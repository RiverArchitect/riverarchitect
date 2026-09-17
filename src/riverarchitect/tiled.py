"""Block-wise raster processing for reaches too large to hold in memory.

Every analysis module reads its rasters whole, which is the right thing for a reach of a few
kilometres and impossible for a few hundred: a 400 km river mapped at 1 to 2 m spans a
bounding box of tens of billions of cells, more than 100 GiB for a *single* float raster,
although the river itself covers perhaps one percent of it. This module lets the same
analyses run on such rasters by processing them in blocks, and it is what the modules
switch to on their own when :func:`enabled` says a run would not fit in
:func:`riverarchitect.config.memory_budget`.

Three properties make it safe to use as a drop-in:

**The result does not depend on the block layout.** Per-cell algebra is exact in any
partition. Neighbourhood operations read a *halo* of extra cells around each block and
crop it off again. Operations that reach across the whole raster - connected components
(:func:`label_components`), least-cost distance (:func:`least_cost_distance`) and
vectorisation (:func:`polygonize`) - are stitched across block seams so that they give the
answer the whole raster would. ``tests/test_tiled.py`` holds each of them to that with
deliberately awkward block sizes.

**Empty blocks cost almost nothing.** A block whose inputs are all NoData is skipped and
never written; output GeoTIFFs are sparse, so the unwritten blocks take no disk space either.
For a river corridor inside its bounding box this is where most of the time is saved.

**No new dependency.** Only rasterio, numpy and scipy, which the in-memory path needs
anyway. Blocks run on a thread pool, since GDAL and numpy release the GIL.

Example
-------
Map a per-cell expression over a raster of any size::

    from riverarchitect import raster, tiled

    reference = raster.profile_of("h000750.tif")
    with tiled.Writer("wet.tif", reference) as out:
        def work(block):
            depth = tiled.read("h000750.tif", reference, block.outer)
            out.write(block, block.crop(raster.con(depth > 0.1, 1.0)))
        tiled.map_blocks(work, reference)

Settings: :data:`riverarchitect.config.TILING`, :data:`~riverarchitect.config.BLOCK_SIZE`,
:data:`~riverarchitect.config.WORKERS` and :func:`~riverarchitect.config.set_memory_budget`.
"""

import concurrent.futures
import hashlib
import logging
import math
import os
import threading
import warnings

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.errors import NotGeoreferencedWarning
from rasterio.transform import Affine
from rasterio.warp import reproject, transform_bounds
from rasterio.windows import Window
from rasterio.windows import bounds as window_bounds
from rasterio.windows import transform as window_transform
from scipy import ndimage

from . import config

__all__ = ["enabled", "block_shape", "Block", "blocks", "map_blocks", "read", "Writer",
           "has_data", "Summary", "ValueCounts", "nanmean", "label_components", "Components",
           "least_cost_distance", "polygonize"]

logger = logging.getLogger("riverarchitect")

# rasterio wraps each array handed to `reproject` or `shapes` in an in-memory dataset that
# has no transform for an instant, and hides the warning that causes with `catch_warnings` -
# which is process-wide, so with several threads at work the warning escapes now and then.
# The transform is set before the dataset is used (tests/test_tiled.py checks every result),
# so only that warning, and only from those two modules, is silenced.
if isinstance(NotGeoreferencedWarning, type):     # not under the docs build's mocks
    warnings.filterwarnings("ignore", message="Dataset has no geotransform",
                            category=NotGeoreferencedWarning,
                            module=r"rasterio\.(warp|features)")

#: Cells read beyond a reprojected block on every side, so that nearest-neighbour lookups at
#: the block edge find the source cell they would find in the whole raster.
_REPROJECT_PAD = 2
#: Smallest block :func:`block_shape` shrinks to when memory is tight.
_MIN_BLOCK = 256


# ----------------------------------------------------------------------- policy

def enabled(profile, layers=1):
    """Whether a run over ``profile`` should be processed block by block.

    Args:
        profile (dict): the grid of the run.
        layers (int): how many float rasters of that grid the in-memory path holds at once.

    Returns:
        bool: True when :data:`config.TILING <riverarchitect.config.TILING>` is
        ``"always"``, or is ``"auto"`` and ``layers`` float64 grids exceed the memory budget.
    """
    mode = str(config.TILING).lower()
    if mode == "always":
        return True
    if mode == "never":
        return False
    need = int(profile["height"]) * int(profile["width"]) * 8 * max(1, int(layers))
    return need > config.memory_budget()


def _workers():
    return max(1, int(config.WORKERS or min(4, os.cpu_count() or 1)))


def block_shape(layers=1):
    """``(rows, cols)`` of one block.

    :data:`config.BLOCK_SIZE <riverarchitect.config.BLOCK_SIZE>`, shrunk when ``layers``
    float64 blocks per worker thread would not fit in the memory budget.
    """
    size = config.BLOCK_SIZE
    rows, cols = (size, size) if np.isscalar(size) else size
    rows, cols = int(rows), int(cols)
    per_cell = 8 * max(1, int(layers)) * _workers()
    fit = int(math.sqrt(config.memory_budget() / per_cell))
    if fit < max(rows, cols):
        fit = max(_MIN_BLOCK, fit // _MIN_BLOCK * _MIN_BLOCK)
        rows, cols = min(rows, fit), min(cols, fit)
    return rows, cols


# ----------------------------------------------------------------------- blocks

class Block:
    """One block of a grid.

    Attributes:
        index (tuple): ``(i, j)`` position in the block layout.
        window (rasterio.windows.Window): the cells this block is responsible for.
        outer (rasterio.windows.Window): ``window`` grown by the halo, clipped to the grid.
            Read inputs over this.
        inner (tuple): slices selecting ``window`` from an array shaped like ``outer``.
        profile (dict): the grid profile restricted to ``outer``.
    """

    __slots__ = ("index", "window", "outer", "inner", "profile")

    def __init__(self, index, window, outer, profile):
        self.index = index
        self.window = window
        self.outer = outer
        row = int(window.row_off - outer.row_off)
        col = int(window.col_off - outer.col_off)
        self.inner = (slice(row, row + int(window.height)),
                      slice(col, col + int(window.width)))
        self.profile = dict(profile, height=int(outer.height), width=int(outer.width),
                            transform=window_transform(outer, profile["transform"]))

    @property
    def shape(self):
        """Shape of arrays over :attr:`outer`."""
        return int(self.outer.height), int(self.outer.width)

    def crop(self, array):
        """The part of an :attr:`outer`-shaped array that belongs to :attr:`window`."""
        return array[self.inner]

    def __repr__(self):
        return "Block(%s, rows %d+%d, cols %d+%d)" % (
            self.index, self.window.row_off, self.window.height,
            self.window.col_off, self.window.width)


def _halo(halo):
    """``(top, bottom, left, right)`` from an int or a 4-tuple."""
    if np.isscalar(halo):
        halo = int(halo)
        return halo, halo, halo, halo
    return tuple(int(h) for h in halo)


def layout(profile, layers=1):
    """``(rows, cols, n_rows, n_cols)`` of the block layout over ``profile``."""
    rows, cols = block_shape(layers)
    height, width = int(profile["height"]), int(profile["width"])
    return rows, cols, -(-height // rows), -(-width // cols)


def blocks(profile, halo=0, layers=1):
    """Every block of ``profile``, row by row.

    Args:
        profile (dict): the grid.
        halo (int or tuple): extra cells to read around each block, or
            ``(top, bottom, left, right)``.
        layers (int): passed to :func:`block_shape`.

    Returns:
        list: :class:`Block` objects.
    """
    shape = layout(profile, layers)
    return [_block(profile, shape, i, j, halo)
            for i in range(shape[2]) for j in range(shape[3])]


def _block(profile, shape, i, j, halo=0):
    """Block ``(i, j)`` of the layout ``shape``, as :func:`layout` returns it."""
    top, bottom, left, right = _halo(halo)
    height, width = int(profile["height"]), int(profile["width"])
    rows, cols = shape[0], shape[1]
    row0, col0 = i * rows, j * cols
    row1, col1 = min(height, row0 + rows), min(width, col0 + cols)
    outer_row0, outer_row1 = max(0, row0 - top), min(height, row1 + bottom)
    outer_col0, outer_col1 = max(0, col0 - left), min(width, col1 + right)
    return Block((i, j), Window(col0, row0, col1 - col0, row1 - row0),
                 Window(outer_col0, outer_row0, outer_col1 - outer_col0,
                        outer_row1 - outer_row0),
                 profile)


_GDAL_CACHE = [None]


def _limit_gdal_cache():
    """Keep GDAL's block cache within the memory budget.

    GDAL caches decompressed blocks up to 5 % of the installed memory by default, which on
    a large machine is far more than a block-wise run means to hold.
    """
    limit = max(64 * 1024 ** 2, config.memory_budget() // 8)
    if _GDAL_CACHE[0] != limit:
        try:
            from rasterio._env import set_gdal_config
            set_gdal_config("GDAL_CACHEMAX", int(limit))
        except (ImportError, TypeError, ValueError):
            pass
        _GDAL_CACHE[0] = limit


def map_blocks(func, profile, halo=0, layers=1, workers=None, label=None, items=None,
               needs=None):
    """Call ``func(block)`` for every block, on a thread pool.

    Args:
        func (callable): does the work for one :class:`Block` and returns anything.
        profile (dict): the grid.
        halo (int or tuple): see :func:`blocks`.
        layers (int): see :func:`block_shape`.
        workers (int): threads; :data:`config.WORKERS <riverarchitect.config.WORKERS>` by
            default.
        label (str): what to call the work in progress messages.
        items (list): blocks to process instead of all of them.
        needs (list): raster paths ``func`` needs data from. A block where none of them
            holds any, across ``block.outer``, is not passed to ``func`` and yields
            ``None`` - so ``func`` must give nothing for such a block anyway. See
            :func:`has_data`.

    Returns:
        list: the return values, in block order.
    """
    _limit_gdal_cache()
    items = blocks(profile, halo, layers) if items is None else list(items)
    needs = [path for path in (needs or []) if isinstance(path, str)]
    workers = workers or _workers()
    total = len(items)
    if label and total > 1:
        logger.info("      * %s: %d block(s) of %s cells on %d thread(s)", label, total,
                    "x".join(str(n) for n in block_shape(layers)), min(workers, total))
    step = max(1, total // 10)
    done = [0]
    lock = threading.Lock()

    def run(block):
        if needs and not any(has_data(path, profile, block.outer) for path in needs):
            result = None
        else:
            result = func(block)
        with lock:
            done[0] += 1
            if label and total > 1 and (done[0] % step == 0) and done[0] < total:
                logger.info("        %s: %d/%d blocks", label, done[0], total)
        return result

    if workers <= 1 or total <= 1:
        return [run(block) for block in items]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(run, items))


# -------------------------------------------------------------------------- I/O

def _same_grid(src, profile):
    return (src.crs == profile["crs"]
            and src.transform.almost_equals(profile["transform"], precision=1e-9))


def read(source, profile, window, resampling=Resampling.nearest):
    """Read part of a raster onto part of a reference grid.

    The block-wise counterpart of :func:`riverarchitect.raster.read` followed by
    :func:`riverarchitect.raster.align`: the result equals the corresponding slice of the
    whole aligned raster.

    Args:
        source (str or tuple): a raster path, or an in-memory ``(array, profile)`` pair.
        profile (dict): the reference grid.
        window (rasterio.windows.Window): the part of the reference grid to fill.
        resampling (rasterio.enums.Resampling): as for ``align``.

    Returns:
        numpy.ndarray: float64, NoData as ``numpy.nan``.
    """
    height, width = int(window.height), int(window.width)
    out = np.full((height, width), np.nan)
    if isinstance(source, tuple):
        return _read_array(source[0], source[1], profile, window, out, resampling)
    if not has_data(source, profile, window):
        return out
    with rasterio.open(source) as src:
        if _same_grid(src, profile):
            row0, col0 = int(window.row_off), int(window.col_off)
            r0, r1 = max(row0, 0), min(row0 + height, src.height)
            c0, c1 = max(col0, 0), min(col0 + width, src.width)
            if r1 > r0 and c1 > c0:
                data = src.read(1, window=Window(c0, r0, c1 - c0, r1 - r0), masked=True)
                out[r0 - row0:r1 - row0, c0 - col0:c1 - col0] = np.ma.filled(
                    data.astype("float64"), np.nan)
            return out

        src_window = _source_window(src.transform, src.crs, src.height, src.width,
                                    profile, window)
        if src_window is None:
            return out
        data = np.ma.filled(src.read(1, window=src_window, masked=True).astype("float64"),
                            np.nan)
        reproject(source=data, destination=out,
                  src_transform=src.window_transform(src_window), src_crs=src.crs,
                  dst_transform=window_transform(window, profile["transform"]),
                  dst_crs=profile["crs"], src_nodata=np.nan, dst_nodata=np.nan,
                  resampling=resampling)
    return out


def _read_array(array, src_profile, profile, window, out, resampling):
    if (src_profile["crs"] == profile["crs"]
            and Affine(*src_profile["transform"][:6]).almost_equals(
                profile["transform"], precision=1e-9)):
        row0, col0 = int(window.row_off), int(window.col_off)
        r0, r1 = max(row0, 0), min(row0 + out.shape[0], array.shape[0])
        c0, c1 = max(col0, 0), min(col0 + out.shape[1], array.shape[1])
        if r1 > r0 and c1 > c0:
            out[r0 - row0:r1 - row0, c0 - col0:c1 - col0] = array[r0:r1, c0:c1]
        return out
    src_window = _source_window(src_profile["transform"], src_profile["crs"],
                                array.shape[0], array.shape[1], profile, window)
    if src_window is None:
        return out
    rows, cols = src_window.toslices()
    reproject(source=np.ascontiguousarray(array[rows, cols], dtype="float64"),
              destination=out,
              src_transform=window_transform(src_window, src_profile["transform"]),
              src_crs=src_profile["crs"],
              dst_transform=window_transform(window, profile["transform"]),
              dst_crs=profile["crs"], src_nodata=np.nan, dst_nodata=np.nan,
              resampling=resampling)
    return out


def _source_window(src_transform, src_crs, src_height, src_width, profile, window):
    """The source cells covering ``window`` of ``profile``, padded, or None."""
    left, bottom, right, top = window_bounds(window, profile["transform"])
    if src_crs != profile["crs"]:
        left, bottom, right, top = transform_bounds(profile["crs"], src_crs,
                                                    left, bottom, right, top,
                                                    densify_pts=21)
    inverse = ~src_transform
    corners = [inverse * (x, y) for x in (left, right) for y in (bottom, top)]
    cols = [c for c, _ in corners]
    rows = [r for _, r in corners]
    c0 = max(0, int(math.floor(min(cols))) - _REPROJECT_PAD)
    c1 = min(int(src_width), int(math.ceil(max(cols))) + _REPROJECT_PAD)
    r0 = max(0, int(math.floor(min(rows))) - _REPROJECT_PAD)
    r1 = min(int(src_height), int(math.ceil(max(rows))) + _REPROJECT_PAD)
    if c1 <= c0 or r1 <= r0:
        return None
    return Window(c0, r0, c1 - c0, r1 - r0)


class _Coverage:
    """Which tiles of a GeoTIFF can hold data, read from the file's tile index alone.

    A tile is known to be empty when it was never written (a sparse file) or when its
    compressed bytes are identical to those of a tile of the same shape that has been
    decoded and found to be all NoData. Compression is deterministic, so identical bytes
    are identical cells; anything else counts as data. Files this cannot be decided for -
    other formats, uncompressed or mask-band GeoTIFFs, rasters without a NoData value -
    report every tile as data.
    """

    #: Most tile bytes hashed per file before giving up on the file.
    MAX_HASHED = 2 * 1024 ** 3

    def __init__(self, path):
        self.tiles = None
        try:
            self._scan(path)
        except Exception as exc:                  # never let an optimisation fail a run
            logger.debug("no tile coverage for %s (%s)", path, exc)
            self.tiles = None

    def _scan(self, path):
        from rasterio.enums import MaskFlags

        with rasterio.open(path) as src:
            self.crs, self.transform = src.crs, src.transform
            self.height, self.width = src.height, src.width
            if (src.driver != "GTiff" or src.nodata is None
                    or src.mask_flag_enums[0] != [MaskFlags.nodata]
                    or not src.compression):
                return
            rows, cols = src.block_shapes[0]
            height, width = src.height, src.width
            n_rows, n_cols = -(-height // rows), -(-width // cols)
            sizes = np.full((n_rows, n_cols), -1, dtype=np.int64)
            offsets = np.zeros((n_rows, n_cols), dtype=np.int64)
            for i in range(n_rows):
                for j in range(n_cols):
                    size = src.get_tag_item("BLOCK_SIZE_%d_%d" % (j, i), "TIFF", 1)
                    if size is not None and int(size) > 0:
                        sizes[i, j] = int(size)
                        offsets[i, j] = int(src.get_tag_item(
                            "BLOCK_OFFSET_%d_%d" % (j, i), "TIFF", 1))

            written = sizes >= 0
            tiles = written.copy()
            values, counts = np.unique(sizes[written], return_counts=True)
            # An empty tile compresses to the same few bytes wherever it is, so only sizes
            # shared by several tiles are worth hashing.
            candidates = values[counts > 1]
            candidates = candidates[np.cumsum(candidates * counts[counts > 1])
                                    <= self.MAX_HASHED]
            verdicts = {}
            with open(path, "rb") as handle:
                for i, j in zip(*np.nonzero(np.isin(sizes, candidates))):
                    handle.seek(int(offsets[i, j]))
                    shape = (min(rows, height - i * rows), min(cols, width - j * cols))
                    key = (shape, hashlib.blake2b(handle.read(int(sizes[i, j])),
                                                  digest_size=16).digest())
                    if key not in verdicts:
                        window = Window(j * cols, i * rows, shape[1], shape[0])
                        verdicts[key] = bool(np.ma.count(
                            src.read(1, window=window, masked=True)))
                    tiles[i, j] = verdicts[key]
        self.tiles = tiles
        self.rows, self.cols = rows, cols

    def any(self, window):
        """Whether any tile touching ``window`` (of the file's own grid) may hold data."""
        if self.tiles is None:
            return True
        i0 = max(0, int(window.row_off) // self.rows)
        j0 = max(0, int(window.col_off) // self.cols)
        i1 = int(math.ceil((window.row_off + window.height) / self.rows))
        j1 = int(math.ceil((window.col_off + window.width) / self.cols))
        return bool(self.tiles[i0:i1, j0:j1].any())


_COVERAGE = {}
_COVERAGE_LOCK = threading.Lock()


def _coverage(path):
    stat = os.stat(path)
    key = (os.path.abspath(path), stat.st_mtime_ns, stat.st_size)
    with _COVERAGE_LOCK:
        entry = _COVERAGE.get(key)
        if entry is None:
            if len(_COVERAGE) >= 512:                # scratch rasters come and go
                del _COVERAGE[next(iter(_COVERAGE))]
            entry = _COVERAGE[key] = [threading.Lock(), None]
    with entry[0]:
        if entry[1] is None:
            entry[1] = _Coverage(path)
    return entry[1]


def has_data(source, profile, window):
    """Whether a raster may hold data within ``window`` of the grid ``profile``.

    ``False`` is certain: :func:`read` would return nothing but NoData. ``True`` means the
    tiles could not be ruled out. Decided from the GeoTIFF tile index, without decoding
    tiles that are known to be empty, which is what makes the empty part of a long reach's
    bounding box nearly free.

    Args:
        source (str or tuple): a raster path; an ``(array, profile)`` pair always may.
        profile (dict): the reference grid.
        window (rasterio.windows.Window): part of it.
    """
    if not isinstance(source, str):
        return True
    coverage = _coverage(source)
    if coverage.tiles is None:
        return True
    if _same_grid(coverage, profile):
        return coverage.any(window)
    src_window = _source_window(coverage.transform, coverage.crs, coverage.height,
                                coverage.width, profile, window)
    return src_window is not None and coverage.any(src_window)


class Writer:
    """A GeoTIFF written block by block.

    The block-wise counterpart of :func:`riverarchitect.raster.write`: same NoData
    stamping, but the file is tiled, may exceed 4 GiB (BigTIFF), and blocks that are never
    written - because they hold nothing - stay sparse and read back as NoData. Overviews
    are built on close so that large results stay responsive in QGIS.

    Use as a context manager. :meth:`write` is thread-safe.

    Args:
        path (str): output GeoTIFF.
        profile (dict): the grid.
        dtype (str): output data type.
        nodata (float): NoData value; :data:`config.NODATA
            <riverarchitect.config.NODATA>` by default.
        compress (str): GeoTIFF compression.
        overviews (bool): build overviews on close.
        options: further GeoTIFF creation options, e.g. ``predictor=3``.
    """

    def __init__(self, path, profile, dtype="float32", nodata=None, compress="lzw",
                 overviews=True, **options):
        self.path = path
        self.dtype = dtype
        self.nodata = config.NODATA if nodata is None else nodata
        self.overviews = overviews
        out = dict(profile)
        out.update(driver="GTiff", dtype=dtype, nodata=self.nodata, count=1,
                   compress=compress, tiled=True, blockxsize=512, blockysize=512,
                   BIGTIFF="IF_SAFER", SPARSE_OK="TRUE")
        out.update(options)
        out.pop("photometric", None)
        directory = os.path.dirname(os.path.abspath(path))
        if directory:
            os.makedirs(directory, exist_ok=True)
        self._lock = threading.Lock()
        self._dst = rasterio.open(path, "w", **out)

    def write(self, block, array):
        """Write ``array`` over ``block.window`` (a :class:`Block` or a ``Window``).

        An array holding nothing but NoData is not written at all.
        """
        from . import raster

        window = block.window if isinstance(block, Block) else block
        array = np.asarray(array)
        if np.issubdtype(array.dtype, np.floating):
            if not np.isfinite(array).any():
                return
        elif not (array != self.nodata).any():
            return
        filled = raster.stamp_nodata(array, self.nodata, self.dtype)
        with self._lock:
            self._dst.write(filled, 1, window=window)

    def close(self):
        """Finish the file, building overviews when asked for."""
        if self._dst.closed:
            return self.path
        if self.overviews:
            factors = []
            size = max(self._dst.height, self._dst.width)
            factor = 2
            while size / factor >= 256:
                factors.append(factor)
                factor *= 2
            if factors:
                self._dst.build_overviews(factors, Resampling.nearest)
        self._dst.close()
        return self.path

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


# -------------------------------------------------------------------- reducers

def nanmean(source, profile, rows=64):
    """Mean of the finite cells of a raster, read a few rows at a time.

    The strips are fixed rather than taken from the block layout, so the value is the same
    to the last bit whether ``source`` is a whole array or a file processed in blocks.

    Args:
        source (str or tuple): a raster path or an ``(array, profile)`` pair.
        profile (dict): the grid to read it on.
        rows (int): rows per strip.

    Returns:
        float: the mean, ``numpy.nan`` when no cell is finite.
    """
    height, width = int(profile["height"]), int(profile["width"])
    total, count = 0.0, 0
    for row in range(0, height, rows):
        part = read(source, profile, Window(0, row, width, min(rows, height - row)))
        finite = np.isfinite(part)
        total += float(part[finite].sum())
        count += int(finite.sum())
    return total / count if count else float("nan")


class Summary:
    """Count, sum, minimum and maximum of the finite values seen, merged across blocks."""

    def __init__(self):
        self.count = 0
        self.total = 0.0
        self.minimum = np.inf
        self.maximum = -np.inf

    @classmethod
    def of(cls, array):
        """Summary of one array."""
        summary = cls()
        values = np.asarray(array, dtype="float64")
        values = values[np.isfinite(values)]
        if values.size:
            summary.count = int(values.size)
            summary.total = float(values.sum())
            summary.minimum = float(values.min())
            summary.maximum = float(values.max())
        return summary

    def add(self, other):
        """Merge another summary into this one and return this one."""
        self.count += other.count
        self.total += other.total
        self.minimum = min(self.minimum, other.minimum)
        self.maximum = max(self.maximum, other.maximum)
        return self

    @classmethod
    def merge(cls, summaries):
        """One summary of many."""
        result = cls()
        for summary in summaries:
            if summary is not None:
                result.add(summary)
        return result

    @property
    def mean(self):
        """Mean, or ``numpy.nan`` when nothing was seen."""
        return self.total / self.count if self.count else float("nan")


class ValueCounts:
    """How often each finite value occurs, merged across blocks.

    Gives the exact median of a raster of few distinct values - lifespans, classes - without
    holding its cells.
    """

    def __init__(self):
        self.counts = {}

    @classmethod
    def of(cls, array):
        """Value counts of one array."""
        result = cls()
        values = np.asarray(array, dtype="float64")
        values, counts = np.unique(values[np.isfinite(values)], return_counts=True)
        result.counts = dict(zip(values.tolist(), counts.tolist()))
        return result

    @classmethod
    def merge(cls, many):
        """One count table of many."""
        result = cls()
        for item in many:
            if item is None:
                continue
            for value, count in item.counts.items():
                result.counts[value] = result.counts.get(value, 0) + count
        return result

    @property
    def size(self):
        """Number of values counted."""
        return int(sum(self.counts.values()))

    def median(self):
        """The median, as :func:`numpy.nanmedian` computes it over the same values."""
        n = self.size
        if not n:
            return float("nan")
        values = sorted(self.counts)
        cumulative = np.cumsum([self.counts[v] for v in values])
        low = values[int(np.searchsorted(cumulative, (n - 1) // 2, side="right"))]
        high = values[int(np.searchsorted(cumulative, n // 2, side="right"))]
        return float(np.mean([low, high]))


# --------------------------------------------------------- connected components

def _structure(connectivity):
    if int(connectivity) == 8:
        return np.ones((3, 3), dtype=int)
    return ndimage.generate_binary_structure(2, 1)


class Components:
    """Connected components of a mask, labelled block by block and merged across seams.

    Built by :func:`label_components`. Component ids are dense, ``0`` to
    :attr:`count` - 1, and ordered like the labels of :func:`scipy.ndimage.label` on the
    whole raster: by the first cell of each component in row-major order.

    Attributes:
        count (int): number of components.
        sizes (numpy.ndarray): cells per component.
        touching (numpy.ndarray): boolean, per component, whether it overlaps the target
            mask given to :func:`label_components`.
        path (str): the raster of block-local labels behind :meth:`ids`.
    """

    def __init__(self, profile, layers, path, offsets, component, count, sizes, touching):
        self.profile = profile
        self.layers = layers
        self.path = path
        self._offsets = offsets
        self._component = component
        self.count = int(count)
        self.sizes = sizes
        self.touching = touching

    def largest(self):
        """Id of the largest component, the first one on a tie; ``None`` when empty."""
        if not self.count:
            return None
        return int(np.argmax(self.sizes))

    def ids(self, window):
        """Component id of every cell of a window, -1 outside every component.

        Args:
            window: a :class:`Block`, whose ``window`` is taken, or any
                ``rasterio.windows.Window`` of the grid - a block's ``outer`` one, say.
        """
        window = window.window if isinstance(window, Block) else window
        ids = np.full((int(window.height), int(window.width)), -1, dtype=np.int64)
        shape = layout(self.profile, self.layers)
        rows, cols = shape[0], shape[1]
        for i in range(int(window.row_off) // rows,
                       (int(window.row_off + window.height) - 1) // rows + 1):
            for j in range(int(window.col_off) // cols,
                           (int(window.col_off + window.width) - 1) // cols + 1):
                self._paste(ids, window, _block(self.profile, shape, i, j))
        return ids

    def _paste(self, ids, window, block):
        """Write the component ids of ``block`` that fall into ``window`` into ``ids``."""
        overlap = _intersection(block.window, window)
        if overlap is None or block.index not in self._offsets:
            return
        local = np.nan_to_num(read(self.path, self.profile, overlap), nan=0.0) \
            .astype(np.int64)
        found = local > 0
        part = np.full(local.shape, -1, dtype=np.int64)
        part[found] = self._component[local[found] + self._offsets[block.index]]
        rows = slice(int(overlap.row_off - window.row_off),
                     int(overlap.row_off - window.row_off + overlap.height))
        cols = slice(int(overlap.col_off - window.col_off),
                     int(overlap.col_off - window.col_off + overlap.width))
        ids[rows, cols] = part

    def remove(self):
        """Delete the label raster."""
        try:
            os.remove(self.path)
        except OSError:
            pass


def _intersection(a, b):
    row0, col0 = max(a.row_off, b.row_off), max(a.col_off, b.col_off)
    row1 = min(a.row_off + a.height, b.row_off + b.height)
    col1 = min(a.col_off + a.width, b.col_off + b.width)
    if row1 <= row0 or col1 <= col0:
        return None
    return Window(col0, row0, col1 - col0, row1 - row0)


def label_components(mask_fn, profile, path, connectivity=4, layers=1, needs=None):
    """Connected components of a mask too large to hold, stitched across block seams.

    The block-wise counterpart of :func:`riverarchitect.raster.label_regions`. Each block
    is labelled on its own; labels that meet across a seam - including diagonally, with
    ``connectivity=8`` - are then merged into one component through a graph of the labels,
    which is small, rather than of the cells.

    Args:
        mask_fn (callable): ``mask_fn(block)`` returns ``(mask, target)`` over
            ``block.window``: the boolean mask to label, and a boolean mask whose overlap
            with each component is recorded in :attr:`Components.touching` (or ``None``).
        profile (dict): the grid.
        path (str): where to keep the block-local labels. Removed by
            :meth:`Components.remove`.
        connectivity (int): 4 or 8.
        layers (int): see :func:`block_shape`.
        needs (list): see :func:`map_blocks`.

    Returns:
        Components
    """
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components

    structure = _structure(connectivity)
    width = int(profile["width"])

    with Writer(path, profile, dtype="int32", nodata=0, overviews=False) as out:
        def work(block):
            mask, target = mask_fn(block)
            labels, count = ndimage.label(np.asarray(mask, dtype=bool), structure=structure)
            if not count:
                return None
            out.write(block, labels.astype("int32"))
            flat = labels.ravel()
            sizes = np.bincount(flat, minlength=count + 1)[1:]
            # First cell of each label in row-major order: scipy numbers labels by it.
            present, first = np.unique(flat, return_index=True)
            keep = present > 0
            rows, cols = np.divmod(first[keep], labels.shape[1])
            first_key = (rows + int(block.window.row_off)) * width \
                + cols + int(block.window.col_off)
            touching = np.zeros(count, dtype=bool)
            if target is not None:
                hit = np.unique(labels[np.asarray(target, dtype=bool) & (labels > 0)])
                touching[hit - 1] = True
            edges = (labels[0, :].copy(), labels[-1, :].copy(),
                     labels[:, 0].copy(), labels[:, -1].copy())
            return count, sizes, first_key, touching, edges

        results = map_blocks(work, profile, layers=layers, label="labelling", needs=needs)

    items = blocks(profile, layers=layers)
    rows_per, cols_per, n_rows, n_cols = layout(profile, layers)
    offsets, total = {}, 0
    sizes, first_keys, touching = [np.zeros(1, dtype=np.int64)], \
        [np.array([-1], dtype=np.int64)], [np.zeros(1, dtype=bool)]
    for block, result in zip(items, results):
        if result is None:
            continue
        offsets[block.index] = total
        count, block_sizes, block_first, block_touching, _edges = result
        sizes.append(block_sizes)
        first_keys.append(block_first)
        touching.append(block_touching)
        total += count
    sizes = np.concatenate(sizes)
    first_keys = np.concatenate(first_keys)
    touching = np.concatenate(touching)

    by_index = {block.index: (block, result) for block, result in zip(items, results)}

    def edge(i, j, which, length):
        """Globally numbered edge of block (i, j), zeros where it has none."""
        block, result = by_index[(i, j)]
        if result is None:
            return np.zeros(length, dtype=np.int64)
        values = result[4][which].astype(np.int64)
        return np.where(values > 0, values + offsets[block.index], 0)

    pairs_a, pairs_b = [], []

    def link(first, second):
        shifts = (0, -1, 1) if int(connectivity) == 8 else (0,)
        for shift in shifts:
            a = first[max(0, shift):len(first) + min(0, shift)]
            b = second[max(0, -shift):len(second) + min(0, -shift)]
            both = (a > 0) & (b > 0)
            if both.any():
                pairs_a.append(a[both])
                pairs_b.append(b[both])

    for i in range(n_rows - 1):
        above = np.concatenate([edge(i, j, 1, by_index[(i, j)][0].window.width)
                                for j in range(n_cols)])
        below = np.concatenate([edge(i + 1, j, 0, by_index[(i + 1, j)][0].window.width)
                                for j in range(n_cols)])
        link(above, below)
    for j in range(n_cols - 1):
        left = np.concatenate([edge(i, j, 3, by_index[(i, j)][0].window.height)
                               for i in range(n_rows)])
        right = np.concatenate([edge(i, j + 1, 2, by_index[(i, j + 1)][0].window.height)
                                for i in range(n_rows)])
        link(left, right)

    n = total + 1
    if pairs_a:
        a, b = np.concatenate(pairs_a), np.concatenate(pairs_b)
        graph = coo_matrix((np.ones(a.size, dtype=np.int8), (a, b)), shape=(n, n))
        _count, merged = connected_components(graph, directed=False)
    else:
        merged = np.arange(n)

    # Renumber merged components by their first cell, which is the order scipy would have
    # numbered them in on the whole raster. Label 0 is the background, not a component.
    first = np.full(merged.max() + 1, np.iinfo(np.int64).max, dtype=np.int64)
    np.minimum.at(first, merged[1:], first_keys[1:])
    used = np.unique(merged[1:])
    order = used[np.argsort(first[used], kind="stable")]
    rank = np.full(merged.max() + 1, -1, dtype=np.int64)
    rank[order] = np.arange(order.size)
    component = rank[merged]
    component[0] = -1

    count = int(order.size)
    component_sizes = np.bincount(component[1:], weights=sizes[1:], minlength=count) \
        .astype(np.int64) if count else np.zeros(0, dtype=np.int64)
    component_touching = np.zeros(count, dtype=bool)
    if count:
        np.logical_or.at(component_touching, component[1:], touching[1:])
    return Components(profile, layers, path, offsets, component, count, component_sizes,
                      component_touching)


# ----------------------------------------------------------- least-cost distance

def least_cost_distance(inputs_fn, profile, path, dx=1.0, dy=1.0, connectivity=8,
                        towards_sources=False, layers=1, max_sweeps=None, needs=None):
    """Least-cost distance over a raster too large to hold, written to ``path``.

    The block-wise counterpart of :func:`riverarchitect.raster.least_cost_distance`, and
    exactly equal to it. Each block is solved with Dijkstra's algorithm on its own cells
    plus a one-cell ring of its neighbours' cells, which enter the search at the cost their
    own block last found for them. Blocks whose edge costs improve pass that on to their
    neighbours, and the sweep repeats until nothing changes. Costs only ever decrease, so
    this terminates; along a river, where the mainstem runs through nearly every block,
    it takes few sweeps.

    Args:
        inputs_fn (callable): ``inputs_fn(block)`` for a block with a one-cell halo returns
            ``(passable, sources, allowed)`` over ``block.outer``, as
            :func:`~riverarchitect.raster.least_cost_distance` takes them.
        profile (dict): the grid.
        path (str): output GeoTIFF.
        dx, dy, connectivity, towards_sources: as for the in-memory function.
        layers (int): see :func:`block_shape`.
        max_sweeps (int): stop after this many sweeps, with a warning. Unlimited by default.
        needs (list): rasters without which a block has no passable cell; see
            :func:`map_blocks`.

    Returns:
        str: ``path``.
    """
    from . import raster

    items = {block.index: block for block in blocks(profile, halo=1, layers=layers)}
    edges = {}
    dirty = set(items)
    sweep = 0
    with Writer(path, profile, dtype="float64") as out:
        while dirty:
            sweep += 1
            if max_sweeps is not None and sweep > max_sweeps:
                logger.warning("      * least-cost distance stopped after %d sweeps with "
                               "%d block(s) still changing", max_sweeps, len(dirty))
                break
            snapshot = dict(edges)

            def work(block):
                passable, sources, allowed = inputs_fn(block)
                passable = np.asarray(passable, dtype=bool)
                if not passable.any():
                    return block.index, None
                seed = _ring_cost(block, items, snapshot)
                cost = raster.least_cost_distance(
                    passable, sources, dx, dy, connectivity=connectivity, allowed=allowed,
                    towards_sources=towards_sources, seed_cost=seed)
                inner = block.crop(cost)
                previous = snapshot.get(block.index)
                current = (inner[0, :].copy(), inner[-1, :].copy(),
                           inner[:, 0].copy(), inner[:, -1].copy())
                changed = previous is None or not all(
                    np.array_equal(p, c, equal_nan=True) for p, c in zip(previous, current))
                out.write(block, inner)
                return block.index, (current, changed)

            results = map_blocks(work, profile, items=[items[k] for k in sorted(dirty)],
                                 label="least-cost sweep %d" % sweep if sweep > 1
                                 else "least-cost distance", needs=needs)
            dirty = set()
            for index, result in (r for r in results if r is not None):
                if result is None:
                    continue
                current, changed = result
                edges[index] = current
                if changed:
                    i, j = index
                    dirty.update(k for k in ((i + di, j + dj) for di in (-1, 0, 1)
                                             for dj in (-1, 0, 1) if di or dj)
                                 if k in items)
    if sweep > 1:
        logger.info("      * least-cost distance settled after %d sweep(s)", sweep)
    return path


def _ring_cost(block, items, edges):
    """Costs the neighbours of ``block`` know for its halo cells, NaN elsewhere."""
    seed = np.full(block.shape, np.nan)
    orow, ocol = int(block.outer.row_off), int(block.outer.col_off)
    oheight, owidth = block.shape
    i, j = block.index
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if not (di or dj) or (i + di, j + dj) not in edges:
                continue
            neighbour = items[(i + di, j + dj)].window
            top, bottom, left, right = edges[(i + di, j + dj)]
            nrow, ncol = int(neighbour.row_off), int(neighbour.col_off)
            nheight, nwidth = int(neighbour.height), int(neighbour.width)
            if di:
                # A row of the neighbour: its bottom row above us, its top row below.
                row = nrow + nheight - 1 if di < 0 else nrow
                values = bottom if di < 0 else top
                c0, c1 = max(ncol, ocol), min(ncol + nwidth, ocol + owidth)
                if c1 > c0 and orow <= row < orow + oheight:
                    seed[row - orow, c0 - ocol:c1 - ocol] = values[c0 - ncol:c1 - ncol]
            else:
                col = ncol + nwidth - 1 if dj < 0 else ncol
                values = right if dj < 0 else left
                r0, r1 = max(nrow, orow), min(nrow + nheight, orow + oheight)
                if r1 > r0 and ocol <= col < ocol + owidth:
                    seed[r0 - orow:r1 - orow, col - ocol] = values[r0 - nrow:r1 - nrow]
    seed[block.inner] = np.nan
    return seed


# ------------------------------------------------------------------ polygonize

def polygonize(value_fn, profile, layers=1, needs=None):
    """Vectorise a raster too large to hold, merging polygons cut by block seams.

    The block-wise counterpart of :func:`riverarchitect.raster.polygonize` with its default
    4-connectivity. Blocks are vectorised in cell coordinates, where seams are exact
    integers, so the pieces of a polygon cut by a seam join without slivers; the merged
    result is then placed on the map with the grid transform.

    Args:
        value_fn (callable): ``value_fn(block)`` returns ``(values, mask)`` over
            ``block.window`` as ``polygonize`` takes them, or ``None`` for nothing.
        profile (dict): the grid.
        layers (int): see :func:`block_shape`.
        needs (list): see :func:`map_blocks`.

    Returns:
        geopandas.GeoDataFrame: with a ``gridcode`` column.
    """
    import geopandas as gpd
    import shapely
    import shapely.affinity
    from shapely.geometry import shape

    from rasterio.features import shapes as _shapes

    def work(block):
        result = value_fn(block)
        if result is None:
            return []
        values, mask = result
        mask = np.asarray(mask, dtype=bool)
        if not mask.any():
            return []
        values = np.nan_to_num(values, nan=0).astype("int32")
        # A translation by whole cells, never the identity: rasterio warns about that one.
        offset = Affine(1.0, 0.0, float(block.window.col_off) - 0.5, 0.0, 1.0,
                        float(block.window.row_off) - 0.5)
        return [(shapely.affinity.translate(shape(geom), 0.5, 0.5), int(value))
                for geom, value in _shapes(values, mask=mask, transform=offset)]

    records = [record for part in map_blocks(work, profile, layers=layers,
                                             label="vectorising", needs=needs)
               if part for record in part]
    rows, cols, n_rows, n_cols = layout(profile, layers)
    geometries = [g for g, _ in records]
    codes = np.array([v for _, v in records], dtype=np.int64)

    if geometries and (n_rows > 1 or n_cols > 1):
        bounds = shapely.bounds(np.array(geometries, dtype=object))
        seam_rows = np.arange(1, n_rows) * rows
        seam_cols = np.arange(1, n_cols) * cols
        on_seam = (np.isin(bounds[:, 0], seam_cols) | np.isin(bounds[:, 2], seam_cols)
                   | np.isin(bounds[:, 1], seam_rows) | np.isin(bounds[:, 3], seam_rows))
        kept = [(g, c) for g, c, s in zip(geometries, codes, on_seam) if not s]
        for code in np.unique(codes[on_seam]):
            pieces = [g for g, c, s in zip(geometries, codes, on_seam) if s and c == code]
            merged = shapely.union_all(pieces)
            kept.extend((part, int(code)) for part in shapely.get_parts(merged))
        # Row-major by the top-left corner, so the order does not depend on the layout.
        kept.sort(key=lambda item: (shapely.bounds(item[0])[1], shapely.bounds(item[0])[0]))
        geometries = [g for g, _ in kept]
        codes = np.array([c for _, c in kept], dtype=np.int64)

    t = profile["transform"]
    matrix = [t.a, t.b, t.d, t.e, t.c, t.f]
    placed = [shapely.affinity.affine_transform(g, matrix) for g in geometries]
    return gpd.GeoDataFrame({"gridcode": [int(c) for c in codes]}, geometry=placed,
                            crs=profile["crs"])
