"""Block-wise processing: every operation must equal its whole-raster counterpart.

Block sizes here are deliberately small and unequal (7 x 11 cells) so that seams cut
through every feature, and the grids are not multiples of them, so the last row and
column of blocks are ragged.
"""

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from riverarchitect import config, raster, tiled

BLOCK = (7, 11)


@pytest.fixture
def small_blocks(monkeypatch):
    """Force block-wise processing with awkward blocks, on two threads."""
    monkeypatch.setattr(config, "TILING", "always")
    monkeypatch.setattr(config, "BLOCK_SIZE", BLOCK)
    monkeypatch.setattr(config, "WORKERS", 2)
    return BLOCK


def _profile(height, width, cell=1.0, x0=500.0, y0=900.0):
    return {"driver": "GTiff", "height": height, "width": width, "count": 1,
            "dtype": "float32", "crs": "EPSG:32610", "nodata": config.NODATA,
            "transform": from_origin(x0, y0, cell, cell)}


def _write(path, array, profile):
    return raster.write(str(path), array, profile)


def _whole(path):
    return raster.read(str(path))[0]


def _run_map(profile, func, path):
    with tiled.Writer(str(path), profile) as out:
        def work(block):
            out.write(block, block.crop(func(block)))
        tiled.map_blocks(work, profile)
    return _whole(path)


def _pools(height=40, width=50, seed=3):
    """A wetted mask with a U-shaped pool that only closes in a later block."""
    rng = np.random.default_rng(seed)
    wet = rng.random((height, width)) > 0.55
    wet[20, :] = True                                   # the main channel
    wet[2:14, 30] = True                                # U: two arms ...
    wet[2:14, 44] = True
    wet[13, 30:45] = True                               # ... joined at the bottom
    wet[1, 29:46] = False
    return wet


# ------------------------------------------------------------------------ policy

def test_enabled_follows_the_budget(monkeypatch):
    profile = _profile(1000, 1000)
    monkeypatch.setattr(config, "TILING", "auto")
    config.set_memory_budget("100M")
    try:
        assert not tiled.enabled(profile, layers=1)            # 8 MB
        assert tiled.enabled(profile, layers=20)               # 160 MB
    finally:
        config.set_memory_budget(None)
    monkeypatch.setattr(config, "TILING", "never")
    assert not tiled.enabled(_profile(10 ** 5, 10 ** 5))
    monkeypatch.setattr(config, "TILING", "always")
    assert tiled.enabled(_profile(2, 2))


def test_memory_budget_parses_units(monkeypatch):
    assert config.set_memory_budget("2G") == 2 * 1024 ** 3
    assert config.set_memory_budget("512MB") == 512 * 1024 ** 2
    assert config.set_memory_budget(1000) == 1000
    config.set_memory_budget(None)
    monkeypatch.setenv("RIVERARCHITECT_MAX_MEMORY", "3GiB")
    assert config.memory_budget() == 3 * 1024 ** 3
    monkeypatch.delenv("RIVERARCHITECT_MAX_MEMORY")
    assert config.memory_budget() > 0


def test_block_shape_shrinks_to_the_budget(monkeypatch):
    monkeypatch.setattr(config, "BLOCK_SIZE", 4096)
    monkeypatch.setattr(config, "WORKERS", 1)
    config.set_memory_budget("64M")
    try:
        rows, cols = tiled.block_shape(layers=10)
        assert rows == cols and rows % 256 == 0
        assert rows * cols * 8 * 10 <= 64 * 1024 ** 2
    finally:
        config.set_memory_budget(None)


def test_blocks_cover_the_grid_once(small_blocks):
    profile = _profile(40, 50)
    covered = np.zeros((40, 50), dtype=int)
    for block in tiled.blocks(profile, halo=2):
        covered[block.window.toslices()] += 1
        assert block.shape[0] >= block.window.height
        assert block.crop(np.zeros(block.shape)).shape == (block.window.height,
                                                            block.window.width)
    assert (covered == 1).all()


# --------------------------------------------------------------------------- I/O

def test_read_same_grid_equals_whole(tmp_path, small_blocks):
    profile = _profile(40, 50)
    data = np.random.default_rng(0).random((40, 50))
    data[5:9, :] = np.nan
    path = _write(tmp_path / "a.tif", data, profile)
    for block in tiled.blocks(profile, halo=3):
        part = tiled.read(path, profile, block.outer)
        np.testing.assert_array_equal(part, _whole(path)[block.outer.toslices()])


@pytest.mark.parametrize("cell, x0, y0", [(1.0, 500.0, 900.0), (0.7, 503.3, 897.9),
                                          (2.0, 490.0, 910.0)])
def test_read_other_grid_equals_align(tmp_path, small_blocks, cell, x0, y0):
    reference = _profile(40, 50)
    source_profile = _profile(int(45 / cell), int(55 / cell), cell, x0, y0)
    data = np.random.default_rng(1).random((source_profile["height"],
                                            source_profile["width"]))
    data[::7, ::5] = np.nan
    path = _write(tmp_path / "b.tif", data, source_profile)
    array, prof = raster.read(path)
    expected = raster.align(array, prof, reference)
    for block in tiled.blocks(reference, halo=1):
        np.testing.assert_array_equal(tiled.read(path, reference, block.outer),
                                      expected[block.outer.toslices()])
        np.testing.assert_array_equal(tiled.read((array, prof), reference, block.outer),
                                      expected[block.outer.toslices()])


def test_writer_is_sparse_and_equals_write(tmp_path, small_blocks):
    profile = _profile(40, 50)
    data = np.full((40, 50), np.nan)
    data[30:33, 3:9] = 4.5
    whole = raster.read(_write(tmp_path / "whole.tif", data, profile))[0]
    part = _run_map(profile, lambda block: tiled.read((data, profile), profile, block.outer),
                    tmp_path / "part.tif")
    np.testing.assert_array_equal(part, whole)
    with rasterio.open(tmp_path / "part.tif") as src:
        assert src.nodata == config.NODATA
        assert src.profile.get("tiled")


# ------------------------------------------------------------------ reducers

def test_summary_and_value_counts_merge_exactly():
    rng = np.random.default_rng(2)
    data = rng.choice([1.0, 2.5, 5.0, 10.0, np.nan], size=(30, 40))
    parts = [data[:13], data[13:14], data[14:]]
    summary = tiled.Summary.merge(tiled.Summary.of(p) for p in parts)
    assert summary.count == np.isfinite(data).sum()
    assert summary.minimum == np.nanmin(data) and summary.maximum == np.nanmax(data)
    assert summary.mean == pytest.approx(np.nanmean(data), rel=1e-12)
    counts = tiled.ValueCounts.merge(tiled.ValueCounts.of(p) for p in parts)
    assert counts.median() == np.nanmedian(data)
    even = tiled.ValueCounts.of(np.array([1.0, 2.0, 5.0, 10.0]))
    assert even.median() == 3.5
    assert np.isnan(tiled.ValueCounts().median())


# --------------------------------------------------------------- neighbourhoods

def test_halo_makes_neighbourhoods_exact(tmp_path, small_blocks):
    profile = _profile(40, 50)
    rng = np.random.default_rng(4)
    mask = rng.random((40, 50)) > 0.93
    dem = rng.random((40, 50)) * 3.0
    dem[:, 17] = np.nan
    fill = float(np.nanmean(dem))

    for window, radius in ((1, 2.5), (3, 4.0)):
        expected_fraction = raster.focal_fraction(mask, window=window)
        expected_radius = raster.within_radius(mask, radius, 1.0, 1.0)
        halo = max(window, int(np.ceil(radius)))
        fraction = np.full(mask.shape, np.nan)
        near = np.zeros(mask.shape, dtype=bool)
        for block in tiled.blocks(profile, halo=halo):
            part = mask[block.outer.toslices()]
            fraction[block.window.toslices()] = block.crop(
                raster.focal_fraction(part, window=window,
                                      valid=np.ones(part.shape, dtype=bool)))
            near[block.window.toslices()] = block.crop(
                raster.within_radius(part, radius, 1.0, 1.0))
        np.testing.assert_array_equal(near, expected_radius)
        np.testing.assert_allclose(fraction, expected_fraction, rtol=0, atol=1e-15)

    expected_slope = raster.slope(dem, 1.0, 1.0)
    slope = np.full(dem.shape, np.nan)
    for block in tiled.blocks(profile, halo=1):
        slope[block.window.toslices()] = block.crop(
            raster.slope(dem[block.outer.toslices()], 1.0, 1.0, fill_value=fill))
    np.testing.assert_array_equal(slope, expected_slope)


def test_interpolation_by_window_equals_whole(small_blocks):
    profile = _profile(20, 30, cell=0.5)
    rng = np.random.default_rng(5)
    points = np.column_stack([rng.uniform(500, 515, 60), rng.uniform(890, 900, 60)])
    values = rng.random(60)
    for method in (raster.idw, raster.nearest_neighbour):
        whole = method(points, values, profile)
        parts = np.full(whole.shape, np.nan)
        for block in tiled.blocks(profile):
            parts[block.window.toslices()] = method(points, values, profile,
                                                    window=block.window)
        np.testing.assert_array_equal(parts, whole)


# ----------------------------------------------------------- global operations

@pytest.mark.parametrize("connectivity", [4, 8])
def test_components_equal_whole_labelling(tmp_path, small_blocks, connectivity):
    profile = _profile(40, 50)
    wet = _pools()
    target = np.zeros(wet.shape, dtype=bool)
    target[20, :3] = True
    labels, count = raster.label_regions(wet, connectivity)

    components = tiled.label_components(
        lambda block: (wet[block.window.toslices()], target[block.window.toslices()]),
        profile, str(tmp_path / "labels.tif"), connectivity=connectivity)
    assert components.count == count
    ids = np.full(wet.shape, -1)
    for block in tiled.blocks(profile):
        ids[block.window.toslices()] = components.ids(block)
    # Same components, numbered the same way.
    np.testing.assert_array_equal(ids + 1, labels)
    sizes = np.bincount(labels.ravel(), minlength=count + 1)[1:]
    np.testing.assert_array_equal(components.sizes, sizes)
    assert components.largest() == int(np.argmax(sizes))
    touching = np.unique(labels[target & (labels > 0)]) - 1
    assert set(np.flatnonzero(components.touching)) == set(touching)
    components.remove()


def test_components_merge_diagonals_across_block_corners(tmp_path, small_blocks):
    profile = _profile(14, 22)
    wet = np.zeros((14, 22), dtype=bool)
    wet[6, 10] = wet[7, 11] = True           # meet only at the corner of four blocks
    for connectivity, expected in ((4, 2), (8, 1)):
        components = tiled.label_components(
            lambda block: (wet[block.window.toslices()], None),
            profile, str(tmp_path / "corner.tif"), connectivity=connectivity)
        assert components.count == expected
        assert components.count == raster.label_regions(wet, connectivity)[1]
        components.remove()


@pytest.mark.parametrize("directed", [False, True])
def test_least_cost_distance_equals_whole(tmp_path, small_blocks, directed):
    profile = _profile(40, 50, cell=1.0)
    dx, dy = 1.0, 1.5
    passable = _pools()
    passable[25:38, 5] = True                  # a long arm crossing several seams
    passable[37, 5:48] = True
    sources = np.zeros(passable.shape, dtype=bool)
    sources[20, :] = True
    ux = np.random.default_rng(6).normal(size=passable.shape)
    uy = np.random.default_rng(7).normal(size=passable.shape)

    def rule(u, v):
        def allowed(dr, dc):
            east, north = dc * dx, -dr * dy
            return (u * east + v * north) / np.hypot(east, north) >= -0.8
        return allowed

    expected = raster.least_cost_distance(passable, sources, dx, dy, connectivity=8,
                                          allowed=rule(ux, uy) if directed else None,
                                          towards_sources=True)

    def inputs(block):
        rows, cols = block.outer.toslices()
        allowed = rule(ux[rows, cols], uy[rows, cols]) if directed else None
        return passable[rows, cols], sources[rows, cols], allowed

    path = tiled.least_cost_distance(inputs, profile, str(tmp_path / "cost.tif"),
                                     dx, dy, connectivity=8, towards_sources=True)
    result = raster.read(path)[0]
    assert np.isfinite(expected).sum() > 100
    np.testing.assert_array_equal(np.isfinite(result), np.isfinite(expected))
    finite = np.isfinite(expected)
    # Written as float64, so the costs survive the file exactly.
    np.testing.assert_array_equal(result[finite], expected[finite])


def test_seed_cost_starts_the_search_at_that_cost():
    passable = np.ones((1, 5), dtype=bool)
    sources = np.zeros((1, 5), dtype=bool)
    seed = np.full((1, 5), np.nan)
    seed[0, 0] = 10.0
    cost = raster.least_cost_distance(passable, sources, 1.0, 1.0, connectivity=4,
                                      seed_cost=seed)
    np.testing.assert_array_equal(cost, [[10.0, 11.0, 12.0, 13.0, 14.0]])


def test_polygonize_merges_across_seams(small_blocks):
    import shapely

    profile = _profile(40, 50, cell=0.5)
    wet = _pools()
    values = np.where(wet, 1, 0) + np.where(np.arange(50) > 25, 1, 0)[None, :]
    whole = raster.polygonize(values.astype(float), profile, mask=wet)
    parts = tiled.polygonize(
        lambda block: (values[block.window.toslices()], wet[block.window.toslices()]),
        profile)
    assert len(parts) == len(whole)
    assert sorted(parts.gridcode) == sorted(whole.gridcode)
    for code in np.unique(whole.gridcode):
        a = shapely.union_all(whole.geometry[whole.gridcode == code].values)
        b = shapely.union_all(parts.geometry[parts.gridcode == code].values)
        assert a.symmetric_difference(b).area == pytest.approx(0.0, abs=1e-9)
    assert sorted(np.round(parts.geometry.area, 9)) == sorted(np.round(whole.geometry.area, 9))


# -------------------------------------------------------------- empty blocks

@pytest.mark.parametrize("sparse", [True, False])
def test_has_data_rules_out_only_empty_tiles(tmp_path, small_blocks, sparse):
    """Empty tiles are recognised in sparse and in fully written files, and nothing else."""
    height, width = 1100, 1500
    profile = dict(_profile(height, width), tiled=True, blockxsize=256, blockysize=256,
                   compress="lzw", nodata=-9999.0)
    if sparse:
        profile["SPARSE_OK"] = "TRUE"
    data = np.full((height, width), np.nan)
    data[300, 700] = 1.0                        # one cell in tile (1, 2)
    data[1099, 1499] = 0.0                      # a zero in the last, clipped, tile
    data[600:700, 0:256] = 5.0                  # a constant tile would compress alike ...
    data[612, 17] = np.nan                      # ... unless it differs
    path = str(tmp_path / "coverage.tif")
    with rasterio.open(path, "w", **profile) as dst:
        filled = np.where(np.isfinite(data), data, -9999.0).astype("float32")
        if sparse:
            for i in range(0, height, 256):
                for j in range(0, width, 256):
                    part = data[i:i + 256, j:j + 256]
                    if np.isfinite(part).any():
                        window = rasterio.windows.Window(j, i, part.shape[1], part.shape[0])
                        dst.write(filled[i:i + 256, j:j + 256], 1, window=window)
        else:
            dst.write(filled, 1)

    grid = raster.profile_of(path)
    coverage = tiled._coverage(path)
    assert coverage.tiles is not None
    assert coverage.tiles.sum() == 3
    whole = raster.read(path)[0]
    for top in range(0, height, 97):
        for left in range(0, width, 131):
            window = rasterio.windows.Window(left, top, 131, 97)
            present = np.isfinite(whole[window.toslices()]).any()
            if present:
                assert tiled.has_data(path, grid, window)
            if not tiled.has_data(path, grid, window):
                assert not present
                assert np.isnan(tiled.read(path, grid, window)).all()


def test_needs_skips_blocks_without_data(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "BLOCK_SIZE", 512)          # the Writer's tile size
    profile = _profile(1500, 2000)
    data = np.full((1500, 2000), np.nan)
    data[2, 3] = 1.0
    path = str(tmp_path / "one.tif")
    with tiled.Writer(path, profile) as out:
        out.write(rasterio.windows.Window(0, 0, 2000, 1500), data)
    called = []
    tiled.map_blocks(lambda block: called.append(block.index), profile, needs=[path])
    assert called == [(0, 0)]


@pytest.mark.parametrize("value, expected", [("", None), ("auto", None), (" 3 ", 3),
                                             ("0", 1), ("many", None)])
def test_workers_from_environment(monkeypatch, value, expected):
    monkeypatch.setenv("RIVERARCHITECT_WORKERS", value)
    assert config._workers_from_environment() == expected
