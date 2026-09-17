"""Preparing a condition: the terrain products every other module depends on.

The open-source replacement for the ArcGIS ``GetStarted`` module. Nothing here is an
analysis in its own right; it produces the derived rasters that lifespan mapping, habitat
suitability and recruitment all read:

* :func:`detrended_dem` - elevation above the local thalweg, which is what makes an
  elevation comparable between the upstream and downstream ends of a reach;
* :func:`water_level_elevation`, :func:`interpolated_depth` and :func:`depth_to_water_table`
  - a continuous water surface extrapolated from the wetted area, and the depth and
  depth-to-groundwater rasters derived from it;
* :func:`morphological_units` - a depth and velocity classification into pools, riffles,
  runs and the rest, after Wyrick and Pasternack (2014);
* :func:`write_input_definitions` - the ``input_definitions.inp`` a condition needs;
* :func:`align_condition` - put every raster of a condition on one grid.

Relation to the original
------------------------
The original did the interpolation steps by converting rasters to point shapefiles, running
``SpatialJoin_analysis`` with ``match_option="CLOSEST"``, and converting back with
``PointToRaster_conversion``. That round trip through vector data was a way to get a
nearest-neighbour interpolation out of arcpy; here it is
:func:`riverarchitect.raster.nearest_neighbour` directly, with
:func:`riverarchitect.raster.idw` and :func:`riverarchitect.raster.kriging` available as
alternatives the original could not offer.
"""

import logging
import os
import re
import threading

import numpy as np

import rasterio
from scipy.spatial import cKDTree

from . import config, raster, shear, tiled

__all__ = ["detrended_dem", "water_level_elevation", "interpolated_depth",
           "depth_to_water_table", "morphological_units", "MorphologicalUnits",
           "bed_shear_stress", "ShearRasterWriters", "write_input_definitions", "align_condition",
           "build_product", "INTERPOLATION_METHODS", "MU_ALIASES", "PRODUCTS"]

logger = logging.getLogger("riverarchitect")

#: Interpolation methods accepted where a surface is extrapolated from wetted cells.
INTERPOLATION_METHODS = ("nearest", "idw", "kriging")


def _interpolate(points, values, profile, method="nearest", window=None, tree=None,
                 **kwargs):
    """Dispatch to the requested interpolator in :mod:`riverarchitect.raster`."""
    if method == "nearest":
        return raster.nearest_neighbour(points, values, profile, window=window, tree=tree)
    if method == "idw":
        return raster.idw(points, values, profile, window=window, tree=tree, **kwargs)
    if method == "kriging":
        return raster.kriging(points, values, profile, window=window, **kwargs)
    raise ValueError("method must be one of %s" % (INTERPOLATION_METHODS,))


#: Bytes per sampled point while a surface is interpolated block by block: coordinates,
#: value and the KD-tree over them.
_BYTES_PER_POINT = 64


def _blockwise(profile, layers, output_path):
    """Whether a preprocessing function runs block by block.

    Only with a file to write to: without one the result is returned as an array, which a
    grid that fits in memory can still be even when block-wise processing is forced.
    """
    if not tiled.enabled(profile, layers):
        return False
    if output_path:
        return True
    forced = str(config.TILING).lower() == "always"
    need = int(profile["height"]) * int(profile["width"]) * 8 * layers
    if forced and need <= config.memory_budget():
        return False
    raise ValueError("%d x %d cells are too large to return in memory - pass output_path"
                     % (profile["height"], profile["width"]))


def _surface_blockwise(dem_path, depth_path, output_path, method, step, kind, what,
                       dtype="float32", clip=False):
    """:func:`detrended_dem` or :func:`water_level_elevation` for a grid too large to hold.

    The sample points are gathered in row-major strips, so ``step`` picks exactly the cells
    it picks from the whole array. When even the sample would not fit in the memory budget,
    ``step`` is raised, and that is logged. Blocks without a single DEM cell are left
    NoData: an extrapolated surface far from any terrain serves no analysis. ``clip``
    leaves every cell without terrain NoData, for a surface that is only ever compared
    with the DEM.
    """
    from rasterio.windows import Window

    profile = raster.profile_of(dem_path)
    height, width = int(profile["height"]), int(profile["width"])
    logger.info("   >> %d x %d cells exceed the memory budget - processing block by block",
                height, width)

    def strips(with_dem=True):
        for row in range(0, height, 64):
            window = Window(0, row, width, min(64, height - row))
            if tiled.has_data(depth_path, profile, window):
                dem = tiled.read(dem_path, profile, window) if with_dem else None
                yield window, dem, tiled.read(depth_path, profile, window)

    wet_cells = sum(int((np.nan_to_num(d) > 0.0).sum())
                    for _w, _z, d in strips(with_dem=False))
    affordable = max(1, config.memory_budget() // 2 // _BYTES_PER_POINT)
    if wet_cells // max(1, step) > affordable:
        raised = -(-wet_cells // affordable)
        logger.warning("   >> %d wetted cells do not fit in the memory budget - sampling "
                       "every %d-th instead of every %d-th", wet_cells, raised, step)
        step = raised

    points, values = [], []
    seen = 0
    for window, dem, depth in strips():
        wetted = np.nan_to_num(depth) > 0.0
        sampled = raster.con(wetted, dem + depth if kind == "wle" else dem)
        rows, cols = np.where(np.isfinite(sampled))
        # The ordinal of each finite cell in the whole raster decides whether it is taken.
        take = (seen + np.arange(rows.size)) % step == 0
        seen += rows.size
        rows, cols = rows[take], cols[take]
        xs, ys = rasterio.transform.xy(profile["transform"], rows + int(window.row_off),
                                       cols)
        points.append(np.column_stack([xs, ys]).reshape(-1, 2))
        values.append(sampled[rows, cols])
    points = np.concatenate(points) if points else np.zeros((0, 2))
    values = np.concatenate(values) if values else np.zeros(0)
    if points.size == 0:
        raise ValueError("no wetted cell in %s - cannot %s" % (depth_path, what))
    logger.info("   >> interpolating from %d wetted cells (%s)", len(values), method)
    # One tree for every block; kriging keeps its own search.
    tree = None if method == "kriging" else cKDTree(points)

    def work(block):
        dem = tiled.read(dem_path, profile, block.window)
        if not np.isfinite(dem).any():
            return
        surface = _interpolate(points, values, profile, method=method, window=block.window,
                               tree=tree)
        if kind != "wle":
            surface = dem - surface
        elif clip:
            surface = np.where(np.isfinite(dem), surface, np.nan)
        out.write(block, surface)

    options = {"predictor": 3} if dtype.startswith("float") else {}
    with tiled.Writer(output_path, profile, dtype=dtype, **options) as out:
        tiled.map_blocks(work, profile, label="interpolating", needs=[dem_path])
    return output_path, profile


def _copy_raster(source, target, dtype="float32"):
    """Copy a raster block by block, as :func:`riverarchitect.raster.write` would write it."""
    profile = raster.profile_of(source)
    with tiled.Writer(target, profile, dtype=dtype) as out:
        tiled.map_blocks(lambda block: out.write(
            block, tiled.read(source, profile, block.window)), profile, needs=[source])
    return target


def _as_surface(wle, profile, window=None):
    """A water surface given as an array or a raster path, on ``profile``."""
    if isinstance(wle, str):
        if window is None:
            array, wle_profile = raster.read(wle)
            return raster.align(array, wle_profile, profile)
        return tiled.read(wle, profile, window)
    return wle if window is None else wle[window.toslices()]


def _sample_points(array, profile, step=1):
    """Points and values of the finite cells of an array."""
    points, values = raster.raster_to_points(array, profile, step=step)
    finite = np.isfinite(values)
    return points[finite], values[finite]


# ------------------------------------------------------------------- detrended DEM

def detrended_dem(dem_path, depth_path, output_path=None, method="nearest", step=1):
    """Elevation above the local thalweg.

    A raw DEM cannot be compared along a reach: 3 ft above the bed means something different
    where the bed is 10 ft higher. Detrending removes the downstream slope by subtracting the
    elevation of the nearest wetted cell - the thalweg at the discharge given.

    Args:
        dem_path (str): the digital elevation model.
        depth_path (str): a water depth raster; its wetted cells define the thalweg. Use a
            low, in-channel discharge.
        output_path (str): where to write the result. Optional.
        method (str): ``"nearest"`` (the original's behaviour), ``"idw"`` or ``"kriging"``.
        step (int): sample every n-th thalweg cell. Raise it on very large rasters.

    Returns:
        tuple: ``(detrended, profile)``. On a grid too large to hold, ``detrended`` is
        ``output_path``, which is then required.
    """
    if _blockwise(raster.profile_of(dem_path), 6, output_path):
        return _surface_blockwise(dem_path, depth_path, output_path, method, step,
                                  "thalweg", "locate a thalweg")
    dem, profile = raster.read(dem_path)
    depth, depth_profile = raster.read(depth_path)
    depth = raster.align(depth, depth_profile, profile)

    # Thalweg elevation: the bed where it is wet. con with two arguments, so dry cells are
    # NoData and are not sampled as if they were at elevation zero.
    thalweg = raster.con(np.nan_to_num(depth) > 0.0, dem)
    points, values = _sample_points(thalweg, profile, step=step)
    if points.size == 0:
        raise ValueError("no wetted cell in %s - cannot locate a thalweg" % depth_path)

    logger.info("   >> detrending against %d thalweg cells (%s)", len(values), method)
    surface = _interpolate(points, values, profile, method=method)
    detrended = dem - surface

    if output_path:
        raster.write(output_path, detrended, profile)
    return detrended, profile


# ------------------------------------------------------------------- water levels

def water_level_elevation(dem_path, depth_path, output_path=None, method="nearest",
                          step=1):
    """Extrapolate a continuous water surface from the wetted area.

    In the wetted area the water surface is ``dem + depth``. Outside it there is no
    modelled water surface at all, so it is interpolated - which is what makes a
    depth-to-groundwater raster possible on dry land.

    Returns:
        tuple: ``(wle, profile)``. On a grid too large to hold, ``wle`` is
        ``output_path``, which is then required.
    """
    if _blockwise(raster.profile_of(dem_path), 6, output_path):
        return _surface_blockwise(dem_path, depth_path, output_path, method, step,
                                  "wle", "build a water surface")
    dem, profile = raster.read(dem_path)
    depth, depth_profile = raster.read(depth_path)
    depth = raster.align(depth, depth_profile, profile)

    wetted = np.nan_to_num(depth) > 0.0
    surface = raster.con(wetted, dem + depth)
    points, values = _sample_points(surface, profile, step=step)
    if points.size == 0:
        raise ValueError("no wetted cell in %s - cannot build a water surface" % depth_path)

    logger.info("   >> interpolating the water surface from %d wetted cells (%s)",
                len(values), method)
    wle = _interpolate(points, values, profile, method=method)

    if output_path:
        raster.write(output_path, wle, profile)
    return wle, profile


def interpolated_depth(dem_path, depth_path, output_path=None, wle=None, **kwargs):
    """Water depth extended beyond the modelled wetted area.

    ``wle - dem``, kept where positive. Used where a 2D model covers less than the area an
    analysis needs.

    Args:
        wle: the water surface, as an array or a raster path. Built when not given.

    Returns:
        tuple: ``(depth, profile)``, with ``output_path`` for ``depth`` on a grid too
        large to hold.
    """
    def derive(dem, surface):
        depth = surface - dem
        with np.errstate(invalid="ignore"):
            return raster.con(depth > 0.0, depth)

    return _from_surface(dem_path, depth_path, output_path, wle, derive, kwargs)


def _from_surface(dem_path, depth_path, output_path, wle, derive, kwargs):
    """Shared body of :func:`interpolated_depth` and :func:`depth_to_water_table`."""
    profile = raster.profile_of(dem_path)
    if _blockwise(profile, 4, output_path):
        scratch = None
        if wle is None:
            # A surface of its own, beside the output but never over an existing file.
            import tempfile

            scratch = tempfile.mkdtemp(
                prefix="wle-", dir=os.path.dirname(os.path.abspath(output_path)))
            wle, _profile = water_level_elevation(
                dem_path, depth_path, os.path.join(scratch, "wle.tif"), **kwargs)

        def work(block):
            dem = tiled.read(dem_path, profile, block.window)
            if np.isfinite(dem).any():
                out.write(block, derive(dem, _as_surface(wle, profile, block.window)))

        try:
            with tiled.Writer(output_path, profile) as out:
                tiled.map_blocks(work, profile, layers=4, needs=[dem_path])
        finally:
            if scratch:
                import shutil

                shutil.rmtree(scratch, ignore_errors=True)
        return output_path, profile

    dem, profile = raster.read(dem_path)
    if wle is None:
        wle, profile = water_level_elevation(dem_path, depth_path, **kwargs)
    result = derive(dem, _as_surface(wle, profile))

    if output_path:
        raster.write(output_path, result, profile)
    return result, profile


def depth_to_water_table(dem_path, depth_path, output_path=None, wle=None, **kwargs):
    """Depth from the ground surface down to the water table.

    ``dem - wle``: positive on dry land above the water surface, which is the range
    vegetation-planting features are keyed to. Cells below the water surface are negative,
    and are kept rather than clipped - a planting feature needs to know it is under water.

    Args:
        wle: the water surface, as an array or a raster path. Built when not given.

    Returns:
        tuple: ``(d2w, profile)``, with ``output_path`` for ``d2w`` on a grid too large
        to hold.
    """
    return _from_surface(dem_path, depth_path, output_path, wle,
                         lambda dem, surface: dem - surface, kwargs)


# -------------------------------------------------------------- morphological units

#: Names the lifespan threshold table uses for morphological units that
#: ``morphological_units.xlsx`` spells differently. The two vocabularies were never
#: reconciled in the original, where the mismatch raised a ``KeyError`` inside a bare
#: ``except`` and silently dropped the whole morphological-unit criterion.
MU_ALIASES = {
    "agriplain": "agricultural plain",
    "backswamp": "swamp",
    "in-channel bar": "bar (in-channel)",
    "lateral bar": "bar (lateral)",
    "medial bar": "bar (medial)",
    "point bar": "bar (point)",
    "high floodplain": "floodplain (high)",
    "island high floodplain": "island (permanent)",
    "island-floodplain": "island (flood only)",
    "fast glide": "glide (fast)",
    "slow glide": "glide (slow)",
}


class MorphologicalUnits:
    """Morphological unit names, raster codes and the depth and velocity ranges they span.

    Read from a ``morphological_units.xlsx`` in the original layout: column D the unit name,
    E its raster code, F and G the depth range, H and I the velocity range. The workbook is
    in **SI**, so the thresholds are converted when the condition is in U.S. customary units.

    The floodplain units in the lower half of the workbook carry a name and a code but no
    depth or velocity range, because they are not delineated hydraulically. They are kept
    here with :data:`numpy.nan` bounds: :func:`morphological_units` cannot classify a cell
    into them, but :mod:`riverarchitect.lifespan` needs their codes to apply a feature's
    ``mu_avoid`` and ``mu_relevant`` lists, most of which name exactly those units.

    Args:
        path (str): the workbook. Defaults to the one shipped with the package.
        unit (str): unit system of the rasters the thresholds will be applied to.
    """

    _FIRST_ROW = 6
    _LAST_ROW = 44

    def __init__(self, path=None, unit="us"):
        import warnings

        import openpyxl

        self.path = path or os.path.join(config.templates_dir(), "morphological_units.xlsx")
        if not os.path.isfile(self.path):
            raise FileNotFoundError("no morphological unit table at %s" % self.path)
        self.unit = str(unit).lower()
        # The workbook is metric; 1 m = 1/0.3048 ft, and the same factor applies to m/s.
        self.factor = 1.0 / config.FT2M if self.unit == "us" else 1.0

        self.units = {}
        with warnings.catch_warnings():
            # openpyxl drops the workbook's data-validation extension on read and says so.
            # It does not affect the thresholds, and there is nothing to act on.
            warnings.simplefilter("ignore", UserWarning)
            sheet = openpyxl.load_workbook(self.path, data_only=True).active
        for row in range(self._FIRST_ROW, self._LAST_ROW + 1):
            name = sheet.cell(row, 4).value
            code = sheet.cell(row, 5).value
            if not name or code is None or str(name).strip().lower() in ("none", "mu type"):
                continue
            raw = [sheet.cell(row, column).value for column in (6, 7, 8, 9)]
            try:
                h_min, h_max, u_min, u_max = (float(value) * self.factor for value in raw)
            except (TypeError, ValueError):
                # A floodplain unit: named and coded, but not hydraulically delineated.
                h_min = h_max = u_min = u_max = float("nan")
            self.units[str(name).strip()] = {
                "code": int(code), "h_min": h_min, "h_max": h_max,
                "u_min": u_min, "u_max": u_max,
            }

    def classifiable(self):
        """The units that carry a depth *and* velocity range, so a cell can fall into one."""
        return {name: entry for name, entry in self.units.items()
                if not np.isnan(entry["h_min"])}

    def codes(self):
        """``{unit name: raster code}``, as :mod:`riverarchitect.lifespan` expects it.

        Every name in :data:`MU_ALIASES` is added as a second key for the unit it refers to,
        so a threshold table may use either vocabulary.
        """
        codes = {name.lower(): entry["code"] for name, entry in self.units.items()}
        for alias, canonical in MU_ALIASES.items():
            if canonical in codes and alias not in codes:
                codes[alias] = codes[canonical]
        return codes

    def __len__(self):
        return len(self.units)

    def __repr__(self):
        return "MorphologicalUnits(%d units, unit=%r)" % (len(self.units), self.unit)


def morphological_units(depth_path, velocity_path, output_path=None, table=None,
                        unit="us"):
    """Classify the wetted area into morphological units by depth and velocity.

    After Wyrick and Pasternack (2014). A cell takes the unit whose depth *and* velocity
    range it falls into; where ranges overlap the highest code wins, which is what the
    original's ``CellStatistics(..., "MAXIMUM")`` did.

    Args:
        depth_path (str): water depth raster, usually at baseflow.
        velocity_path (str): flow velocity raster at the same discharge.
        output_path (str): where to write the result. Optional.
        table (MorphologicalUnits): the threshold table. Built by default.
        unit (str): unit system of the rasters.

    Returns:
        tuple: ``(mu, profile, table)``. On a grid too large to hold, ``mu`` is
        ``output_path``, which is then required.
    """
    table = table or MorphologicalUnits(unit=unit)
    units = table.classifiable()
    if _blockwise(raster.profile_of(depth_path), 2 * len(units) + 4, output_path):
        return _morphological_units_blockwise(depth_path, velocity_path, output_path,
                                              table, 2 * len(units) + 4)
    depth, profile = raster.read(depth_path)
    velocity, velocity_profile = raster.read(velocity_path)
    velocity = raster.align(velocity, velocity_profile, profile)

    layers, counts = _classify(depth, velocity, units)
    for name, count in counts.items():
        if count:
            logger.info("   >> %-22s code %-3d %d cell(s)", name, units[name]["code"], count)

    if not layers:
        raise ValueError(_NO_UNIT)

    mu = raster.cell_statistics(layers, "MAXIMUM")
    if output_path:
        raster.write(output_path, mu, profile)
    return mu, profile, table


_NO_UNIT = ("no cell falls into any morphological unit - check the units of the depth and "
            "velocity rasters against the table")


def _classify(depth, velocity, units):
    """Per-unit code layers of the cells each unit claims, and how many it claims."""
    wet = np.nan_to_num(depth) > 0.0
    layers, counts = [], {}
    for name, entry in units.items():
        with np.errstate(invalid="ignore"):
            selected = (wet
                        & (depth >= entry["h_min"]) & (depth < entry["h_max"])
                        & (velocity >= entry["u_min"]) & (velocity < entry["u_max"]))
        counts[name] = int(selected.sum())
        if counts[name]:
            layers.append(raster.con(selected, float(entry["code"])))
    return layers, counts


def _morphological_units_blockwise(depth_path, velocity_path, output_path, table, layers):
    units = table.classifiable()
    profile = raster.profile_of(depth_path)

    def work(block):
        depth = tiled.read(depth_path, profile, block.window)
        if not (np.nan_to_num(depth) > 0.0).any():
            return None
        velocity = tiled.read(velocity_path, profile, block.window)
        classes, counts = _classify(depth, velocity, units)
        if classes:
            out.write(block, raster.cell_statistics(classes, "MAXIMUM"))
        return counts

    with tiled.Writer(output_path, profile) as out:
        parts = [p for p in tiled.map_blocks(work, profile, layers=layers,
                                             label="morphological units",
                                             needs=[depth_path]) if p]
    totals = {name: sum(part[name] for part in parts) for name in units}
    for name, count in totals.items():
        if count:
            logger.info("   >> %-22s code %-3d %d cell(s)", name, units[name]["code"], count)
    if not any(totals.values()):
        os.remove(output_path)
        raise ValueError(_NO_UNIT)
    return output_path, profile, table


# -------------------------------------------------------------- bed shear stress

#: File-name prefixes of the rasters :func:`bed_shear_stress` writes, per quantity.
SHEAR_PREFIXES = {"theta84": "ts", "ustar2": "tb", "h_over_ks": "hks", "regime": "regime"}


def write_shear_rasters(result, profile, output_dir, token):
    """Write one discharge's shear rasters, named ``<prefix><token>.tif``.

    The single writer behind :func:`bed_shear_stress` and the per-discharge output of
    Lifespan Design and Riparian Recruitment, so the four file names mean the same thing
    wherever they appear.

    Args:
        result (shear.ShearResult): what :func:`riverarchitect.shear.calculate_taux` returned.
        profile (dict): the grid to write on.
        output_dir (str): destination folder.
        token (str): the discharge in file-name form; see :meth:`Condition.token_for`.

    Returns:
        dict: quantity name -> path written.
    """
    os.makedirs(output_dir, exist_ok=True)
    written = {}
    for quantity, prefix in SHEAR_PREFIXES.items():
        path = os.path.join(output_dir, "%s%s.tif" % (prefix, token))
        array = getattr(result, quantity)
        if quantity == "regime":
            # uint8 with an explicit 0: the default -999 would wrap into the value range.
            raster.write(path, array, profile, dtype="uint8", nodata=0)
        else:
            raster.write(path, array, profile)
        written[quantity] = path
    return written


class ShearRasterWriters:
    """:func:`write_shear_rasters`, block by block, for any number of discharges.

    Thread-safe. Also keeps the regime counts that :func:`shear.regime_summary` would give
    for the whole grid.

    Args:
        profile (dict): the grid.
        output_dir (str): destination folder, or ``None`` to only count the regimes.
    """

    def __init__(self, profile, output_dir):
        self.profile = profile
        self.output_dir = output_dir
        self._seen = {}
        self._writers = {}
        self._counts = {}
        self._lock = threading.Lock()

    def _writer(self, token, quantity):
        from . import tiled

        key = (token, quantity)
        with self._lock:
            if key not in self._writers:
                os.makedirs(self.output_dir, exist_ok=True)
                path = os.path.join(self.output_dir,
                                    "%s%s.tif" % (SHEAR_PREFIXES[quantity], token))
                if quantity == "regime":
                    self._writers[key] = tiled.Writer(path, self.profile, dtype="uint8",
                                                      nodata=0)
                else:
                    self._writers[key] = tiled.Writer(path, self.profile)
            return self._writers[key]

    def write(self, token, block, result):
        """Write the part of ``result`` (over ``block.outer``) that ``block`` owns."""
        if self.output_dir is not None:
            for quantity in SHEAR_PREFIXES:
                self._writer(token, quantity).write(block,
                                                    block.crop(getattr(result, quantity)))
        counts = np.bincount(block.crop(result.regime).ravel(), minlength=4)
        with self._lock:
            self._seen.setdefault(token, None)
            self._counts[token] = self._counts.get(token, 0) + counts

    def tokens(self):
        """Discharge tokens seen so far, in the order first seen."""
        return list(self._seen)

    def summary(self, token):
        """:func:`shear.regime_summary` of one discharge over the whole grid."""
        counts = np.array(self._counts.get(token, np.zeros(4, dtype=np.int64)))
        cells = int(self.profile["height"]) * int(self.profile["width"])
        counts[0] = cells - int(counts[1:].sum())
        return {shear.REGIME_LABELS[code]: int(counts[code])
                for code in sorted(shear.REGIME_LABELS)}

    def close(self):
        """Finish every file. Returns ``{token: {quantity: path}}``."""
        written = {}
        for (token, quantity), writer in self._writers.items():
            written.setdefault(token, {})[quantity] = writer.close()
        return written


def bed_shear_stress(condition, unit="us", discharges=None, output_dir=None,
                     grain_kind="dmean"):
    """Write the bed shear stress of every modelled discharge into the condition folder.

    The counterpart of the original's ``LifespanDesign/helper.py``, which wrote ``ts<Q>.tif``
    and ``tb<Q>.tif`` into ``01_Conditions/<condition>/ts/`` and ``.../tb/``. Here they go
    beside the hydraulic rasters they derive from, named the same way (``ts000550.tif``
    accompanies ``h000550.tif`` and ``u000550.tif``), because a subfolder per quantity split
    one discharge's rasters across three places.

    Four rasters per discharge, from :func:`riverarchitect.shear.calculate_taux`:

    ==============  ====================================================================
    ``ts<Q>.tif``   dimensionless bed shear stress (Shields stress) referenced to ``D84``
    ``tb<Q>.tif``   squared shear velocity ``u*^2``, in the condition's units
    ``hks<Q>.tif``  relative submergence ``h/ks``
    ``regime<Q>``   which resistance closure applied; see :data:`shear.REGIME_LABELS`
    ==============  ====================================================================

    ``tb`` keeps the original's prefix but **not** its content: 1.x wrote ``u*^2`` into a
    raster named for the dimensional stress ``rho_w u*^2``, having cancelled the density
    again when forming ``ts``. The quantity here is the one 1.x actually stored, under a
    docstring that says so rather than a name that does not.

    Args:
        condition (Condition or str): the condition, or its name.
        unit (str): ``"us"`` or ``"si"``; selects the gravitational acceleration.
        discharges (list): which discharges to compute. Defaults to every one whose depth
            and velocity raster are both on disk.
        output_dir (str): where to write. Defaults to the condition folder.
        grain_kind (str): what the grain raster holds; see
            :func:`riverarchitect.shear.d84_of`.

    Returns:
        list: one dict per discharge, with its ``discharge``, the ``rasters`` written and
        the ``regime`` cell counts.
    """
    from .condition import Condition, discharge_token

    condition = condition if isinstance(condition, Condition) else Condition(condition)
    target = output_dir or condition.directory
    gravity = shear.gravity_of(unit)

    grain_path = condition.path(condition.grain_raster)
    if not grain_path or not os.path.isfile(grain_path):
        raise FileNotFoundError(
            "condition %r has no grain size raster, so no bed shear stress can be "
            "computed.\n\n%s" % (condition.name, condition.describe()))

    if discharges is None:
        depth_q = {condition.discharge_of(name) for name in condition.all_depth_rasters()}
        velocity_q = {condition.discharge_of(name)
                      for name in condition.all_velocity_rasters()}
        discharges = sorted((depth_q & velocity_q) - {None})
    if not discharges:
        raise ValueError("condition %r has no paired depth and velocity rasters.\n\n%s"
                         % (condition.name, condition.describe()))

    reference = raster.profile_of(grain_path)
    if tiled.enabled(reference, 12):
        return _bed_shear_stress_blockwise(condition, discharges, target, gravity,
                                           grain_path, grain_kind, reference)
    grain, reference = raster.read(grain_path)
    d84 = shear.d84_of(grain, grain_kind)

    results = []
    for discharge in discharges:
        depth_name = condition.depth_raster_for(discharge)
        velocity_name = condition.velocity_raster_for(discharge)
        if not (depth_name and velocity_name):
            logger.info("   >> no depth/velocity pair at %s - skipped",
                        discharge_token(discharge))
            continue

        depth, depth_profile = raster.read(condition.path(depth_name))
        velocity, velocity_profile = raster.read(condition.path(velocity_name))
        depth = raster.align(depth, depth_profile, reference)
        velocity = raster.align(velocity, velocity_profile, reference)
        # Dry cells are NoData, never zero: a depth of zero is not a shallow flow.
        depth = np.where(depth > 0, depth, np.nan)

        result = shear.calculate_taux(velocity, depth, d84, gravity=gravity)
        token = condition.token_for(discharge)
        written = write_shear_rasters(result, reference, target, token)

        summary = shear.regime_summary(result.regime)
        logger.info("   >> taux %s: %s", token,
                    ", ".join("%s %d" % item for item in summary.items()))
        results.append({"discharge": discharge, "rasters": written, "regime": summary})

    _check_shear(results, condition)
    return results


def _check_shear(results, condition):
    if results and not any(entry["regime"]["invalid"] < sum(entry["regime"].values())
                           for entry in results):
        raise ValueError(
            "the bed shear stress is NoData everywhere, at every discharge. Check that the "
            "grain raster %r holds grain diameters in the condition's length unit and "
            "shares the extent of the hydraulic rasters." % condition.grain_raster)


def _bed_shear_stress_blockwise(condition, discharges, target, gravity, grain_path,
                                grain_kind, reference):
    from .condition import discharge_token

    logger.info("   >> %d x %d cells exceed the memory budget - processing block by block",
                reference["height"], reference["width"])
    pairs = []
    for discharge in discharges:
        depth_name = condition.depth_raster_for(discharge)
        velocity_name = condition.velocity_raster_for(discharge)
        if not (depth_name and velocity_name):
            logger.info("   >> no depth/velocity pair at %s - skipped",
                        discharge_token(discharge))
            continue
        pairs.append((discharge, condition.token_for(discharge),
                      condition.path(depth_name), condition.path(velocity_name)))

    sink = ShearRasterWriters(reference, target)

    def work(block):
        grain = tiled.read(grain_path, reference, block.window)
        if not np.isfinite(grain).any():
            return
        d84 = shear.d84_of(grain, grain_kind)
        for _discharge, token, depth_path, velocity_path in pairs:
            depth = tiled.read(depth_path, reference, block.window)
            depth = np.where(depth > 0, depth, np.nan)
            if not np.isfinite(depth).any():
                continue
            velocity = tiled.read(velocity_path, reference, block.window)
            sink.write(token, block, shear.calculate_taux(velocity, depth, d84,
                                                          gravity=gravity))

    try:
        tiled.map_blocks(work, reference, layers=12, label="bed shear stress",
                         needs=[grain_path])
    finally:
        written = sink.close()

    results = []
    for discharge, token, _depth, _velocity in pairs:
        # A discharge that wets no cell with a grain size is still reported, and written,
        # as the whole-grid path does.
        rasters = written.get(token)
        if rasters is None:
            rasters = {}
            for quantity, prefix in SHEAR_PREFIXES.items():
                path = os.path.join(target, "%s%s.tif" % (prefix, token))
                if quantity == "regime":
                    tiled.Writer(path, reference, dtype="uint8", nodata=0).close()
                else:
                    tiled.Writer(path, reference).close()
                rasters[quantity] = path
        summary = sink.summary(token)
        logger.info("   >> taux %s: %s", token,
                    ", ".join("%s %d" % item for item in summary.items()))
        results.append({"discharge": discharge, "rasters": rasters, "regime": summary})
    _check_shear(results, condition)
    return results


# ------------------------------------------------------------------ condition setup

def write_input_definitions(condition_dir, return_periods=None, discharges=None,
                            path=None, **rasters):
    """Write the ``input_definitions.inp`` that names a condition's rasters.

    Args:
        condition_dir (str): the condition folder.
        return_periods (list): flood return period per discharge, in years.
        discharges (list): discharges the return periods belong to. Defaults to every
            ``h<Q>.tif`` on disk, ascending.
        path (str): output path. Defaults to ``<condition_dir>/input_definitions.inp``.
        **rasters: override a default raster name, e.g. ``grain_raster="d50"``.

    Returns:
        str: the path written.
    """
    from .condition import Condition

    condition_dir = os.path.abspath(condition_dir)
    path = path or os.path.join(condition_dir, "input_definitions.inp")

    if discharges is None:
        discharges = sorted(
            q for q in (Condition.discharge_of(name) for name in os.listdir(condition_dir)
                        if name.lower().startswith("h") and name.lower().endswith(".tif"))
            if q is not None)

    if return_periods and len(return_periods) != len(discharges):
        raise ValueError("%d return periods for %d discharges - they must correspond"
                         % (len(return_periods), len(discharges)))

    names = {"grain_raster": "dmean", "detrended_raster": "dem_detrend",
             "d2w_raster": "d2w", "mu_raster": "mu", "dem_raster": "dem"}
    names.update({key: value for key, value in rasters.items() if value})

    from .condition import discharge_token

    def hydraulic_name(prefix, discharge):
        # Prefer the file actually on disk: "u000293_000.tif" parses to 293.0 but the
        # token regenerates as "u000293.tif", which would name a raster that isn't there.
        pattern = re.compile(r"^%s\d+(?:_\d+)?\.tif$" % prefix, re.IGNORECASE)
        for name in os.listdir(condition_dir):
            if pattern.match(name) and Condition.discharge_of(name) == float(discharge):
                return name
        return "%s%s.tif" % (prefix, discharge_token(discharge))

    depth = ", ".join(hydraulic_name("h", q) for q in discharges)
    velocity = ", ".join(hydraulic_name("u", q) for q in discharges)
    periods = ", ".join(str(value) for value in (return_periods or []))

    lines = [
        "# RASTER META DATA - ONLY MODIFY VALUES BETWEEN '=' AND '#'",
        "# Written by riverarchitect.preprocessing.write_input_definitions",
        "#" + "-" * 87,
        "Return periods = %s #[Comma separated LIST] defines lifespans" % periods,
        "#",
        "# RASTER NAMES",
        "#" + "-" * 87,
        "Water depth (h) = %s #[Comma separated LIST]" % depth,
        "Flow velocity (u) = %s #[Comma separated LIST]" % velocity,
        "Grain sizes (D mean) = %s #[STRING]" % names["grain_raster"],
        "Detrended DEM = %s #[STRING]" % names["detrended_raster"],
        "Depth to groundwater table (d2w) = %s #[STRING]" % names["d2w_raster"],
        "Morphological units (mu) = %s #[STRING]" % names["mu_raster"],
        "DEM = %s #[STRING]" % names["dem_raster"],
        "DEM of differences = fill, scour #[Comma separated LIST]",
        "",
    ]
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    logger.info("   >> wrote %s (%d discharges)", path, len(discharges))
    return path


def align_condition(condition_dir, reference=None, output_dir=None, pattern="*.tif"):
    """Resample every raster of a condition onto one grid.

    Rasters assembled from different preprocessing chains routinely differ in extent and
    cell size - in the sample condition the DEM of difference is on a 5 ft grid while
    everything else is on 3 ft. Analyses call :func:`riverarchitect.raster.align` per
    operand, so this is a convenience rather than a requirement; it is worth doing once when
    a condition is going to be used repeatedly.

    Args:
        condition_dir (str): the condition folder.
        reference (str): raster whose grid to adopt. Defaults to ``dem.tif``, else the first.
        output_dir (str): where to write. Defaults to writing in place.
        pattern (str): which rasters to align.

    Returns:
        dict: ``{path: "aligned" | "unchanged"}``.
    """
    paths = raster.list_rasters(condition_dir, pattern)
    if not paths:
        raise FileNotFoundError("no rasters matching %s in %s" % (pattern, condition_dir))

    if reference is None:
        preferred = os.path.join(condition_dir, "dem.tif")
        reference = preferred if os.path.isfile(preferred) else paths[0]
    reference_profile = raster.profile_of(reference)
    output_dir = output_dir or condition_dir
    os.makedirs(output_dir, exist_ok=True)

    blockwise = tiled.enabled(reference_profile, 3)
    results = {}
    for path in paths:
        profile = raster.profile_of(path)
        same_grid = (profile["width"] == reference_profile["width"]
                     and profile["height"] == reference_profile["height"]
                     and profile["transform"] == reference_profile["transform"])
        target = os.path.join(output_dir, os.path.basename(path))
        if same_grid and os.path.abspath(target) == os.path.abspath(path):
            results[path] = "unchanged"
            continue
        if blockwise:
            # Written beside the target and moved over it, since the source may be it.
            partial = target + ".partial.tif"
            with tiled.Writer(partial, reference_profile) as out:
                tiled.map_blocks(
                    lambda block, path=path: out.write(
                        block, tiled.read(path, reference_profile, block.window)),
                    reference_profile, needs=[path])
            os.replace(partial, target)
        else:
            array, profile = raster.read(path)
            aligned = array if same_grid \
                else raster.align(array, profile, reference_profile)
            raster.write(target, aligned, reference_profile)
        results[path] = "unchanged" if same_grid else "aligned"
    logger.info("   >> aligned %d of %d raster(s) onto %s",
                sum(1 for value in results.values() if value == "aligned"), len(results),
                os.path.basename(reference))
    return results


#: The products :func:`build_product` can make, as ``(label, key)``. Both front ends render
#: this list, so they cannot drift apart.
PRODUCTS = (
    ("detrended DEM", "detrended"),
    ("water surface, depth and depth to water table", "water"),
    ("morphological units", "mu"),
    ("dimensionless bed shear stress (taux)", "taux"),
    ("analyze flows: seasonal flow duration curves", "flows"),
    ("input_definitions.inp", "inp"),
    ("align every raster onto one grid", "align"),
)

#: One-line explanation of each product, shown in the interface.
PRODUCT_NOTES = {
    "detrended": "Elevation above the local thalweg, so elevations are comparable along "
                 "the reach. Writes dem_detrend.tif.",
    "water": "Extrapolates the water surface from the wetted area, then writes wle.tif, "
             "h_interp.tif and d2w.tif.",
    "mu": "Classifies the wetted area into pools, riffles, runs and the rest from depth "
          "and velocity. Writes mu.tif.",
    "taux": "Bed shear stress at every modelled discharge, from depth, velocity and grain "
            "size. Writes ts<Q>.tif (Shields stress), tb<Q>.tif (u*^2), hks<Q>.tif "
            "(relative submergence) and regime<Q>.tif (which resistance law applied).",
    "flows": "Turns a daily flow record into one seasonal flow duration curve per species "
             "and lifestage, which is what SHArea is integrated over. Needs a flow series "
             "file; writes 00_Flows/<condition>/flow_duration_<code>.xlsx.",
    "inp": "Writes the input_definitions.inp that names the condition's rasters. Add flood "
           "return periods afterwards for lifespan mapping.",
    "align": "Resamples every raster of the condition onto the DEM's grid. Optional - the "
             "analyses align per operand anyway.",
}


def build_product(condition_name, key, discharge=None, method="nearest", unit="us",
                  output_dir=None, flow_series=None):
    """Build one named product for a condition, and report what was written.

    The single entry point both the Qt and the tkinter interface call, so neither has to
    know how a product is assembled and the two cannot drift apart.

    Args:
        condition_name (str): the condition.
        key (str): one of the keys in :data:`PRODUCTS`.
        discharge (float): reference discharge, for the products that need one.
        method (str): interpolation method, see :data:`INTERPOLATION_METHODS`.
        unit (str): unit system of the rasters.
        output_dir (str): where to write. Defaults to the condition folder.
        flow_series (str): path to a daily flow record, for the ``"flows"`` product.

    Returns:
        list: lines describing what was written.
    """
    from .condition import Condition, discharge_token

    condition = Condition(condition_name)
    target = output_dir or condition.directory
    os.makedirs(target, exist_ok=True)
    dem = condition.path(condition.dem_raster)
    depth = None
    if discharge:
        depth_name = condition.depth_raster_for(discharge)
        if depth_name is None:
            raise FileNotFoundError(
                "condition %r has no depth raster for discharge %s (expected a file "
                "named h%s.tif)" % (condition.name, discharge,
                                    discharge_token(discharge)))
        depth = condition.path(depth_name)
    lines = []

    if key == "detrended":
        path = os.path.join(target, "dem_detrend.tif")
        detrended_dem(dem, depth, path, method=method)
        lines.append("wrote %s" % path)
    elif key == "water":
        wle_path = os.path.join(target, "wle.tif")
        scratch = None
        if tiled.enabled(raster.profile_of(dem), 6):
            # The products below are derived from the float64 surface, as in memory; the
            # file the user gets is its float32 copy, rounded as raster.write rounds.
            import shutil
            import tempfile

            scratch = tempfile.mkdtemp(prefix="wle-", dir=target)
            wle, _profile = _surface_blockwise(
                dem, depth, os.path.join(scratch, "wle.tif"), method, 1, "wle",
                "build a water surface", dtype="float64")
            _copy_raster(wle, wle_path)
        else:
            wle, _profile = water_level_elevation(dem, depth, wle_path, method=method)
        try:
            lines.append("wrote %s" % wle_path)
            for maker, filename in ((interpolated_depth, "h_interp.tif"),
                                    (depth_to_water_table, "d2w.tif")):
                path = os.path.join(target, filename)
                maker(dem, depth, path, wle=wle)
                lines.append("wrote %s" % path)
        finally:
            if scratch:
                shutil.rmtree(scratch, ignore_errors=True)
    elif key == "mu":
        velocity = condition.path(condition.velocity_raster_for(discharge))
        path = os.path.join(target, "mu.tif")
        _mu, _profile, table = morphological_units(depth, velocity, path, unit=unit)
        lines.append("wrote %s (%d unit types can be classified hydraulically; the table "
                     "also holds %d floodplain units for lifespan mapping)"
                     % (path, len(table.classifiable()),
                        len(table) - len(table.classifiable())))
    elif key == "taux":
        results = bed_shear_stress(condition, unit=unit, output_dir=output_dir)
        for entry in results:
            counts = entry["regime"]
            token = condition.token_for(entry["discharge"])
            lines.append("wrote ts%s.tif, tb%s.tif, hks%s.tif, regime%s.tif "
                         "(%d cell(s) Rickenmann-Recking, %d blended, %d Keulegan)"
                         % (token, token, token, token,
                            counts["Rickenmann-Recking"], counts["blended"],
                            counts["Keulegan-Einstein"]))
        lines.append("")
        lines.append("%d discharge(s) processed. regime<Q>.tif shows which resistance law "
                     "applied in each cell; read it before trusting a stress map."
                     % len(results))
    elif key == "flows":
        from .flows import seasonal_flow_duration

        if not flow_series:
            raise ValueError("analyzing flows needs a daily flow record: a CSV or workbook "
                             "of dates and mean daily discharge")
        written = seasonal_flow_duration(flow_series, condition.name, unit=unit,
                                         output_dir=output_dir)
        if not written:
            lines.append("no flow duration curve could be built - the record covers none "
                         "of the seasons in Fish.xlsx.")
        for entry in written:
            lines.append("wrote %s (%s %s, %d day(s) in season)"
                         % (entry["path"], entry["species"], entry["lifestage"],
                            entry["days_in_season"]))
    elif key == "inp":
        path = write_input_definitions(
            condition.directory,
            path=os.path.join(target, "input_definitions.inp"))
        lines.append("wrote %s" % path)
        lines.append("")
        lines.append("Return periods are left empty. Fill them in for lifespan mapping:")
        lines.append("one value per discharge, in years.")
    elif key == "align":
        results = align_condition(condition.directory, output_dir=output_dir)
        changed = sum(1 for value in results.values() if value == "aligned")
        lines.append("aligned %d of %d raster(s)" % (changed, len(results)))
    else:
        raise ValueError("unknown product %r" % key)
    return lines
