"""Raster operations for River Architect, built on rasterio, GDAL, numpy and scipy.

This module is the open-source replacement for the ``arcpy`` / Spatial Analyst raster
algebra that the original River Architect was written against. Every function here has a
named arcpy counterpart, documented in :doc:`/guide/arcpy_migration`.

Two conventions run through the whole module and matter more than any individual function:

**NoData is always ``numpy.nan`` in memory.**
    Rasters are read with the declared NoData mask applied and converted to ``float64``.
    Never compare cell values against a sentinel such as ``-999``; third-party inputs carry
    ``-3.4e38``, ``3.4e38``, ``0`` or ``-9999`` interchangeably. On write, the canonical
    value :data:`riverarchitect.config.NODATA` is stamped back in.

**Alignment is explicit.**
    arcpy silently reconciled operands of differing extent through ``arcpy.env.extent`` and
    ``arcpy.env.snapRaster``. numpy does not: it either raises on a shape mismatch or, worse,
    broadcasts into a spatially meaningless result. Use :func:`align` before combining any
    two rasters that do not provably share a grid.

Example
-------
Compute a water surface elevation from a DEM and a depth raster whose extents differ::

    from riverarchitect import raster

    dem, dem_prof = raster.read("dem.tif")
    h, h_prof = raster.read("h000098_750.tif")
    h = raster.align(h, h_prof, dem_prof)          # onto the DEM grid
    wse = raster.con(h > 0, dem + h)               # false branch becomes NoData
    raster.write("wse.tif", wse, dem_prof)
"""

import glob
import os

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.features import rasterize as _rasterize
from rasterio.features import shapes as _shapes
from rasterio.mask import mask as _mask
from rasterio.warp import reproject
from scipy import ndimage
from scipy.spatial import cKDTree

from . import config

__all__ = [
    "read", "write", "profile_of", "cell_size", "align", "resample",
    "con", "is_null", "set_null", "cell_statistics", "reclassify",
    "polygonize", "rasterize", "extract_by_mask", "raster_to_points",
    "idw", "nearest_neighbour", "kriging",
    "label_regions", "disconnected_mask", "within_radius",
    "zonal_statistics", "tabulate_area", "slope",
    "list_rasters",
]


# --------------------------------------------------------------------------- I/O

def read(path, band=1):
    """Read a raster into a float array with NoData as ``numpy.nan``.

    Replaces ``arcpy.Raster(path)`` and ``arcpy.RasterToNumPyArray``.

    Args:
        path (str): path to a GDAL-readable raster.
        band (int): 1-based band index.

    Returns:
        tuple: ``(numpy.ndarray, dict)`` - the array and the rasterio profile.
    """
    with rasterio.open(path) as src:
        array = src.read(band, masked=True).astype("float64")
        prof = src.profile.copy()
    return np.ma.filled(array, np.nan), prof


def profile_of(path):
    """Return the rasterio profile of ``path`` without reading pixel data."""
    with rasterio.open(path) as src:
        return src.profile.copy()


def write(path, array, prof, dtype="float32", nodata=None, compress="lzw"):
    """Write ``array`` to ``path``, stamping in the canonical NoData value.

    Replaces ``arcpy.Raster.save()`` and ``arcpy.NumPyArrayToRaster``.

    Args:
        path (str): output path (GeoTIFF).
        array (numpy.ndarray): 2-D array; ``numpy.nan`` marks NoData.
        prof (dict): rasterio profile supplying the grid and CRS.
        dtype (str): output data type.
        nodata (float): NoData value; defaults to :data:`config.NODATA`.
        compress (str): GeoTIFF compression.

    Returns:
        str: ``path``.
    """
    nodata = config.NODATA if nodata is None else nodata
    out = prof.copy()
    out.update(dtype=dtype, nodata=nodata, count=1, compress=compress)
    out.pop("photometric", None)
    filled = np.where(np.isfinite(array), array, nodata).astype(dtype)
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with rasterio.open(path, "w", **out) as dst:
        dst.write(filled, 1)
    return path


def cell_size(prof):
    """Return ``(dx, dy)`` in map units.

    Replaces ``GetRasterProperties_management(ras, "CELLSIZEX")``, which returned a
    *localised string* and so broke arithmetic on systems using a comma decimal separator.
    """
    transform = prof["transform"]
    return abs(transform.a), abs(transform.e)


def list_rasters(directory, pattern="*.tif"):
    """Sorted list of raster paths in ``directory``. Replaces ``arcpy.ListRasters()``."""
    return sorted(glob.glob(os.path.join(directory, pattern)))


# --------------------------------------------------------------------- alignment

def align(array, src_prof, ref_prof, resampling=Resampling.nearest):
    """Resample ``array`` onto the grid described by ``ref_prof``.

    This is the explicit form of ``arcpy.env.extent`` + ``env.snapRaster`` + ``env.cellSize``.
    Use ``Resampling.nearest`` (the default, and arcpy's default) for anything categorical or
    where original cell values must survive; ``Resampling.bilinear`` only for genuinely
    continuous resampling.

    Args:
        array (numpy.ndarray): source array with ``numpy.nan`` NoData.
        src_prof (dict): profile describing ``array``.
        ref_prof (dict): profile describing the target grid.
        resampling (rasterio.enums.Resampling): resampling method.

    Returns:
        numpy.ndarray: array on the reference grid, NoData as ``numpy.nan``.
    """
    dst = np.full((ref_prof["height"], ref_prof["width"]), np.nan, dtype="float64")
    reproject(source=np.ascontiguousarray(array),
              destination=dst,
              src_transform=src_prof["transform"], src_crs=src_prof["crs"],
              dst_transform=ref_prof["transform"], dst_crs=ref_prof["crs"],
              src_nodata=np.nan, dst_nodata=np.nan,
              resampling=resampling)
    return dst


def resample(path, factor, resampling=Resampling.bilinear):
    """Read ``path`` at a coarser or finer resolution.

    Replaces ``arcpy.Resample_management``. ``factor`` > 1 coarsens.
    """
    with rasterio.open(path) as src:
        height = max(1, int(src.height / factor))
        width = max(1, int(src.width / factor))
        array = src.read(1, out_shape=(1, height, width), resampling=resampling,
                         masked=True).astype("float64")
        prof = src.profile.copy()
        prof.update(height=height, width=width,
                    transform=src.transform * src.transform.scale(src.width / width,
                                                                  src.height / height))
    return np.ma.filled(array, np.nan), prof


# ------------------------------------------------------------------- map algebra

def con(condition, true_value, false_value=np.nan):
    """Conditional evaluation. Replaces ``arcpy.sa.Con``.

    Note the default: the two-argument form of arcpy's ``Con`` yields **NoData**, not zero,
    where the condition is false. Passing ``false_value=0`` instead is a common and
    hard-to-spot source of wetted-area artefacts.
    """
    return np.where(condition, true_value, false_value)


def is_null(array):
    """Replaces ``arcpy.sa.IsNull``."""
    return ~np.isfinite(array)


def set_null(condition, array):
    """Replaces ``arcpy.sa.SetNull``: sets cells to NoData where ``condition`` holds."""
    return np.where(condition, np.nan, array)


def cell_statistics(arrays, statistic="MAXIMUM", ignore_nodata=True):
    """Per-cell statistic across a stack of aligned rasters.

    Replaces ``arcpy.sa.CellStatistics(rasters, statistic, "DATA")``. ``ignore_nodata=True``
    corresponds to ``"DATA"``, which is what every call site in the original code used.

    Args:
        arrays (list): aligned 2-D arrays of identical shape.
        statistic (str): MAXIMUM, MINIMUM, MEAN, SUM, MEDIAN, STD or RANGE.
        ignore_nodata (bool): ignore NoData cells instead of propagating them.

    Returns:
        numpy.ndarray
    """
    stack = np.stack([np.asarray(a, dtype="float64") for a in arrays])
    key = str(statistic).upper()

    if key == "SUM":
        # nansum returns 0 for all-NaN columns; restore NoData there.
        result = np.nansum(stack, axis=0) if ignore_nodata else stack.sum(axis=0)
        if ignore_nodata:
            result = np.where(np.isfinite(stack).any(axis=0), result, np.nan)
        return result

    funcs = {
        "MAXIMUM": (np.nanmax, np.max),
        "MINIMUM": (np.nanmin, np.min),
        "MEAN": (np.nanmean, np.mean),
        "MEDIAN": (np.nanmedian, np.median),
        "STD": (np.nanstd, np.std),
    }
    if key == "RANGE":
        with np.errstate(invalid="ignore"):
            return cell_statistics(arrays, "MAXIMUM") - cell_statistics(arrays, "MINIMUM")
    if key not in funcs:
        raise ValueError("unsupported statistic %r" % statistic)

    func = funcs[key][0 if ignore_nodata else 1]
    with np.errstate(invalid="ignore"):
        # all-NaN slices legitimately produce NaN; arcpy returns NoData there too
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            return func(stack, axis=0)


def reclassify(array, breaks, values, right=True):
    """Map continuous values onto classes. Replaces ``arcpy.sa.Reclassify``/``RemapRange``.

    Args:
        array (numpy.ndarray): input.
        breaks (list): ascending class boundaries.
        values (list): output value per class; ``len(values) == len(breaks) + 1``.
        right (bool): whether intervals are closed on the right.

    Returns:
        numpy.ndarray
    """
    if len(values) != len(breaks) + 1:
        raise ValueError("values must have exactly one more entry than breaks")
    idx = np.digitize(np.nan_to_num(array, nan=-np.inf), breaks, right=right)
    out = np.asarray(values, dtype="float64")[idx]
    return np.where(np.isfinite(array), out, np.nan)


def slope(dem, dx, dy, units="DEGREE"):
    """Surface slope. Replaces ``arcpy.sa.Slope``.

    Returns degrees by default, or percent rise when ``units="PERCENT"``.
    """
    filled = np.where(np.isfinite(dem), dem, np.nanmean(dem))
    grad_y, grad_x = np.gradient(filled, dy, dx)
    rise = np.hypot(grad_x, grad_y)
    result = rise * 100.0 if str(units).upper() == "PERCENT" else np.degrees(np.arctan(rise))
    return np.where(np.isfinite(dem), result, np.nan)


# ------------------------------------------------------- raster <-> vector

def polygonize(array, prof, mask=None, connectivity=4):
    """Vectorise a raster into polygons. Replaces ``arcpy.RasterToPolygon_conversion``.

    Args:
        array (numpy.ndarray): values to vectorise (cast to int32, as arcpy requires).
        prof (dict): rasterio profile supplying transform and CRS.
        mask (numpy.ndarray): optional boolean mask of cells to include.
        connectivity (int): 4 (arcpy's default) or 8.

    Returns:
        geopandas.GeoDataFrame: with a ``gridcode`` column, mirroring arcpy's output field.
    """
    import geopandas as gpd
    from shapely.geometry import shape

    values = np.nan_to_num(array, nan=0).astype("int32")
    if mask is None:
        mask = np.isfinite(array)
    records = [(shape(geom), int(val))
               for geom, val in _shapes(values, mask=mask.astype(bool),
                                        transform=prof["transform"],
                                        connectivity=connectivity)]
    return gpd.GeoDataFrame({"gridcode": [v for _, v in records]},
                            geometry=[g for g, _ in records],
                            crs=prof["crs"])


def rasterize(gdf, prof, column="gridcode", fill=0, all_touched=False, dtype="int32"):
    """Burn polygons into a raster grid. Replaces ``arcpy.PolygonToRaster_conversion``."""
    shapes = [(geom, value) for geom, value in zip(gdf.geometry, gdf[column])]
    return _rasterize(shapes,
                      out_shape=(prof["height"], prof["width"]),
                      transform=prof["transform"],
                      fill=fill, all_touched=all_touched, dtype=dtype)


def extract_by_mask(path, geometries, crop=True):
    """Clip a raster to polygon geometries. Replaces ``arcpy.sa.ExtractByMask``."""
    with rasterio.open(path) as src:
        array, transform = _mask(src, geometries, crop=crop, nodata=config.NODATA)
        prof = src.profile.copy()
    prof.update(height=array.shape[1], width=array.shape[2],
                transform=transform, nodata=config.NODATA)
    out = array[0].astype("float64")
    return np.where(out == config.NODATA, np.nan, out), prof


def raster_to_points(array, prof, step=1):
    """Cell centres and values of every valid cell.

    Replaces ``arcpy.RasterToPoint_conversion`` plus the ``arcpy.sa.Sample`` call the original
    code needed to recover full float precision - the values here are exact by construction.

    Args:
        array (numpy.ndarray): source with ``numpy.nan`` NoData.
        prof (dict): rasterio profile.
        step (int): take every ``step``-th valid cell (subsampling for speed).

    Returns:
        tuple: ``(points, values)`` where ``points`` is ``(n, 2)`` of x/y coordinates.
    """
    rows, cols = np.where(np.isfinite(array))
    rows, cols = rows[::step], cols[::step]
    xs, ys = rasterio.transform.xy(prof["transform"], rows, cols)
    return np.column_stack([xs, ys]), array[rows, cols]


def _target_grid(prof):
    rows, cols = np.mgrid[0:prof["height"], 0:prof["width"]]
    xs, ys = rasterio.transform.xy(prof["transform"], rows.ravel(), cols.ravel())
    return np.column_stack([xs, ys])


# ----------------------------------------------------------------- interpolation

def idw(points, values, prof, k=12, power=2.0):
    """Inverse-distance weighted interpolation onto the grid of ``prof``.

    Replaces ``arcpy.Idw_3d(..., search_radius="Variable 12")`` with its default power of 2.

    Args:
        points (numpy.ndarray): ``(n, 2)`` source coordinates.
        values (numpy.ndarray): ``(n,)`` source values.
        prof (dict): profile describing the output grid.
        k (int): number of nearest neighbours.
        power (float): inverse-distance exponent.

    Returns:
        numpy.ndarray: interpolated grid.
    """
    tree = cKDTree(points)
    k = min(int(k), len(points))
    distance, index = tree.query(_target_grid(prof), k=k)
    if k == 1:
        distance, index = distance[:, None], index[:, None]
    distance = np.maximum(distance, 1e-12)
    weight = 1.0 / distance ** float(power)
    grid = (weight * np.asarray(values)[index]).sum(axis=1) / weight.sum(axis=1)
    return grid.reshape(prof["height"], prof["width"])


def nearest_neighbour(points, values, prof):
    """Nearest-neighbour interpolation.

    Matches the original's "Nearest Neighbor" option, which was ``Idw_3d`` with a single
    neighbour. Values are taken straight from the source array rather than through the
    inverse-distance weighting, so the output reproduces input values exactly instead of
    carrying the rounding error of a weight division.
    """
    tree = cKDTree(points)
    _, index = tree.query(_target_grid(prof), k=1)
    return np.asarray(values)[index].reshape(prof["height"], prof["width"])


def kriging(points, values, prof, model="spherical", nlags=12, n_closest=12,
            return_variance=False):
    """Ordinary kriging onto the grid of ``prof``.

    Replaces ``arcpy.sa.Kriging(..., KrigingModelOrdinary("Spherical", ...))``.

    Unlike arcpy, the estimation variance is returned on request. The original code had the
    variance raster commented out because of an arcpy limitation; here it is free.

    Kriging cost grows steeply with the number of source points. ``n_closest`` keeps the
    solve local, which is the equivalent of arcpy's ``search_radius="Variable 12"``.

    Args:
        points (numpy.ndarray): ``(n, 2)`` source coordinates.
        values (numpy.ndarray): ``(n,)`` source values.
        prof (dict): profile describing the output grid.
        model (str): variogram model - spherical, exponential, gaussian, linear or power.
        nlags (int): number of variogram lag bins.
        n_closest (int): neighbours used per estimate.
        return_variance (bool): also return the estimation variance grid.

    Returns:
        numpy.ndarray or tuple: the grid, or ``(grid, variance)``.
    """
    from pykrige.ok import OrdinaryKriging

    ok = OrdinaryKriging(points[:, 0], points[:, 1], values,
                         variogram_model=model, nlags=int(nlags),
                         enable_plotting=False, coordinates_type="euclidean")
    target = _target_grid(prof)
    estimate, variance = ok.execute("points", target[:, 0], target[:, 1],
                                    n_closest_points=int(n_closest), backend="loop")
    grid = np.asarray(estimate).reshape(prof["height"], prof["width"])
    if return_variance:
        return grid, np.asarray(variance).reshape(prof["height"], prof["width"])
    return grid


# ------------------------------------------------------------------ connectivity

def label_regions(binary, connectivity=4):
    """Label connected components. Replaces ``arcpy.sa.RegionGroup``.

    Args:
        binary (numpy.ndarray): boolean or 0/1 array.
        connectivity (int): 4 (arcpy's default) or 8.

    Returns:
        tuple: ``(labels, count)``.
    """
    if connectivity == 8:
        structure = np.ones((3, 3), dtype=int)
    else:
        structure = ndimage.generate_binary_structure(2, 1)
    return ndimage.label(np.asarray(binary).astype(bool), structure=structure)


def within_radius(mask, radius, dx=1.0, dy=1.0):
    """Cells lying within ``radius`` of any True cell of ``mask``.

    Replaces the original's *spatial join* round trip: raster to points, then
    ``SpatialJoin_analysis(..., match_option="CLOSEST", search_radius=r)``, then points back
    to raster. That produced exactly this - the set of cells with a source cell inside the
    radius - and SHArC used it to spread a cover element's influence over the area it
    shelters.

    Args:
        mask (numpy.ndarray): boolean source cells.
        radius (float): influence radius in map units.
        dx, dy (float): cell size, from :func:`cell_size`.

    Returns:
        numpy.ndarray: boolean mask of the source cells and everything within the radius.
    """
    mask = np.asarray(mask).astype(bool)
    if radius <= 0 or not mask.any():
        return mask
    # A Euclidean distance transform of the *complement* gives, per cell, the distance to
    # the nearest source cell; anisotropic cells are handled by `sampling`.
    distance = ndimage.distance_transform_edt(~mask, sampling=(abs(dy), abs(dx)))
    return distance <= radius


def focal_fraction(mask, window=1, valid=None):
    """Share of each cell's neighbourhood that is True. Replaces focal ``FocalStatistics``.

    ``arcpy.sa.FocalStatistics(raster, NbrRectangle(n, n, "CELL"), "MEAN")`` over a 0/1
    raster, which is how the original measured *"the percentage of area covered with
    cobble"* for its mineral cover types.

    Cells outside ``valid`` - the reach boundary, or anywhere the input is NoData - are left
    out of both the numerator and the denominator, so a cell at the edge of the surveyed area
    is judged against the neighbours it actually has rather than against assumed dry ground.

    Args:
        mask (numpy.ndarray): boolean presence array.
        window (int): neighbourhood radius in **cells**; ``1`` is the 3x3 window.
        valid (numpy.ndarray): cells carrying data. Defaults to all of them.

    Returns:
        numpy.ndarray: fraction between 0 and 1, ``numpy.nan`` where no valid neighbour
        exists.
    """
    mask = np.asarray(mask).astype(bool)
    window = int(window)
    if window < 1:
        return mask.astype("float64")
    valid = np.ones(mask.shape, dtype=bool) if valid is None \
        else np.asarray(valid).astype(bool)

    size = 2 * window + 1
    kernel = np.ones((size, size), dtype="float64")
    present = ndimage.convolve((mask & valid).astype("float64"), kernel, mode="constant",
                               cval=0.0)
    counted = ndimage.convolve(valid.astype("float64"), kernel, mode="constant", cval=0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(counted > 0, present / counted, np.nan)


def least_cost_distance(passable, sources, dx=1.0, dy=1.0, connectivity=8, allowed=None,
                        towards_sources=False):
    """Least-cost distance between ``sources`` and every reachable cell, by Dijkstra.

    Replaces ``arcpy.sa.CostDistance`` and, more to the point, the hand-built weighted
    digraph River Architect 1.x traversed to find fish escape routes: cells are vertices,
    steps between neighbouring passable cells are edges, and the edge weight is the
    centre-to-centre distance. The result is the cost of the cheapest route from the nearest
    source, which is what 1.x wrote into its ``shortest_paths`` rasters.

    ``allowed`` makes the graph **directed**, which is what a velocity criterion needs: a
    fish may drift down a fast chute it cannot swim back up.

    Args:
        passable (numpy.ndarray): boolean mask of cells that can be occupied at all.
        sources (numpy.ndarray): boolean mask of start cells. Cells outside ``passable`` are
            ignored.
        dx, dy (float): cell size in map units, from :func:`cell_size`.
        connectivity (int): 4 for rook steps, 8 to include the diagonals.
        allowed (callable): ``allowed(dr, dc)`` returns a full-grid boolean array that is
            True at ``(r, c)`` where a step **from** ``(r, c)`` **to** ``(r + dr, c + dc)``
            is permitted. Steps in the opposite direction are asked for separately, so a
            one-way edge is expressed by answering True for one and False for the other.
            Without it every step between passable cells is permitted in both directions.
        towards_sources (bool): search the reversed graph, so the result is the cost of
            travelling **to** the nearest source rather than away from it. This is the
            escape-route direction - a fish leaves the pool for the mainstem - and it is why
            1.x traversed its graph outwards from the mainstem. Without a directed
            ``allowed`` the two are identical.

    Returns:
        numpy.ndarray: cost between each cell and the nearest source, ``numpy.nan`` where
        unreachable or impassable. Source cells cost 0.
    """
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import dijkstra

    passable = np.asarray(passable).astype(bool)
    sources = np.asarray(sources).astype(bool) & passable
    cost = np.full(passable.shape, np.nan)
    if not passable.any() or not sources.any():
        return cost

    rows, cols = passable.shape
    index = -np.ones(passable.shape, dtype=np.int64)
    index[passable] = np.arange(int(passable.sum()))

    steps = [(0, 1, abs(dx)), (1, 0, abs(dy))]
    if int(connectivity) == 8:
        diagonal = float(np.hypot(dx, dy))
        steps += [(1, 1, diagonal), (1, -1, diagonal)]

    from_index, to_index, weight = [], [], []
    for dr, dc, step_cost in steps:
        # The overlap of the grid with itself shifted by (dr, dc): `here` holds the cells a
        # step starts from, `there` the cells it lands on.
        row_from, row_to = max(0, -dr), rows - max(0, dr)
        col_from, col_to = max(0, -dc), cols - max(0, dc)
        here = (slice(row_from, row_to), slice(col_from, col_to))
        there = (slice(row_from + dr, row_to + dr), slice(col_from + dc, col_to + dc))

        both = passable[here] & passable[there]
        if not both.any():
            continue
        forward, backward = both, both
        if allowed is not None:
            forward = both & np.asarray(allowed(dr, dc)).astype(bool)[here]
            backward = both & np.asarray(allowed(-dr, -dc)).astype(bool)[there]

        for source_mask, start, end in ((forward, here, there), (backward, there, here)):
            if not source_mask.any():
                continue
            from_index.append(index[start][source_mask])
            to_index.append(index[end][source_mask])
            weight.append(np.full(int(source_mask.sum()), step_cost))

    n = int(passable.sum())
    if not weight:
        cost[sources] = 0.0
        return cost
    graph = coo_matrix((np.concatenate(weight),
                        (np.concatenate(from_index), np.concatenate(to_index))),
                       shape=(n, n))
    # Reversing the edges turns "how far from the mainstem is this cell" into "how far is
    # this cell from reaching the mainstem", which is the question a stranded fish asks.
    graph = (graph.T if towards_sources else graph).tocsr()

    distance = dijkstra(graph, directed=True, indices=index[sources], min_only=True)
    cost[passable] = np.where(np.isfinite(distance), distance, np.nan)
    return cost


def disconnected_mask(binary, connectivity=4, target=None):
    """Boolean mask of every wetted region that does not reach the main channel.

    This is the rule StrandingRisk applies to find pools that have become detached from the
    main wetted area as discharge drops, and therefore represent fish stranding risk.

    Args:
        binary (numpy.ndarray): boolean or 0/1 wetted mask.
        connectivity (int): 4 (arcpy's ``RegionGroup`` default) or 8.
        target (numpy.ndarray): boolean mask of the main channel. A region counts as
            connected when it overlaps it. Without one the **largest** region is taken as
            the main channel, which is what it is at a single discharge but not necessarily
            across a recession - see :class:`riverarchitect.stranding.StrandingRisk`. A
            target that no region overlaps is ignored rather than stranding the whole reach.

    Returns:
        tuple: ``(mask, n_pools)``.
    """
    binary = np.asarray(binary).astype(bool)
    labels, count = label_regions(binary, connectivity)
    if count == 0:
        return np.zeros(binary.shape, dtype=bool), 0

    connected = set()
    if target is not None:
        connected = set(int(label) for label in np.unique(labels[np.asarray(target).astype(bool)])
                        if label > 0)
    if not connected:
        sizes = ndimage.sum(binary, labels, range(1, count + 1))
        connected = {int(np.argmax(sizes)) + 1}

    mask = (labels > 0) & ~np.isin(labels, sorted(connected))
    return mask, int(len(np.unique(labels[mask])))


# ----------------------------------------------------------------------- zonal

def zonal_statistics(zones, raster_path, stats=("count", "mean", "min", "max", "sum"),
                     nodata=None):
    """Statistics of ``raster_path`` within each zone polygon.

    Replaces ``arcpy.sa.ZonalStatisticsAsTable``.

    Pass ``nodata`` explicitly for rasters whose declared NoData is an extreme float such as
    ``3.4e38``; otherwise those cells contaminate the statistics.
    """
    from rasterstats import zonal_stats
    return zonal_stats(zones, raster_path, stats=list(stats), nodata=nodata)


def tabulate_area(array, prof, breaks):
    """Area per class. Replaces ``arcpy.sa.TabulateArea``.

    Returns:
        dict: ``{class_index: area_in_map_units_squared}``.
    """
    dx, dy = cell_size(prof)
    classes = np.digitize(np.nan_to_num(array, nan=-np.inf), breaks)
    classes = np.where(np.isfinite(array), classes, -1)
    unique, counts = np.unique(classes[classes >= 0], return_counts=True)
    return {int(u): float(c) * dx * dy for u, c in zip(unique, counts)}
