"""Raster operations: round trips, alignment, map algebra and connectivity."""

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from riverarchitect import config, raster


@pytest.fixture
def grid(tmp_path):
    """A 20x30 raster of 1 m cells with a NoData border, written to disk."""
    height, width = 20, 30
    data = np.arange(height * width, dtype="float64").reshape(height, width)
    data[0, :] = np.nan
    path = tmp_path / "grid.tif"
    prof = {
        "driver": "GTiff", "height": height, "width": width, "count": 1,
        "dtype": "float32", "crs": "EPSG:3857", "nodata": config.NODATA,
        "transform": from_origin(1000.0, 2000.0, 1.0, 1.0),
    }
    with rasterio.open(path, "w", **prof) as dst:
        dst.write(np.where(np.isfinite(data), data, config.NODATA).astype("float32"), 1)
    return str(path), data, prof


def test_read_applies_nodata_mask(grid):
    path, expected, _ = grid
    array, prof = raster.read(path)
    assert array.shape == expected.shape
    assert np.isnan(array[0, :]).all()
    assert array[1, 0] == pytest.approx(30.0)
    assert prof["crs"] is not None


def test_write_round_trip(tmp_path, grid):
    path, _, _ = grid
    array, prof = raster.read(path)
    out = raster.write(str(tmp_path / "out.tif"), array, prof)
    back, _ = raster.read(out)
    assert np.allclose(back[np.isfinite(back)], array[np.isfinite(array)])
    assert np.isnan(back[0, :]).all()
    with rasterio.open(out) as src:
        assert src.nodata == config.NODATA


def test_cell_size(grid):
    _, _, prof = grid
    assert raster.cell_size({"transform": prof["transform"]}) == (1.0, 1.0)


def test_align_changes_shape_to_reference(grid):
    path, _, _ = grid
    array, prof = raster.read(path)
    ref = dict(prof)
    ref["height"], ref["width"] = 10, 15
    ref["transform"] = from_origin(1000.0, 2000.0, 2.0, 2.0)
    aligned = raster.align(array, prof, ref)
    assert aligned.shape == (10, 15)
    assert np.isfinite(aligned).any()


def test_con_defaults_to_nodata_on_false_branch():
    array = np.array([[1.0, -1.0], [2.0, -2.0]])
    result = raster.con(array > 0, array)
    assert np.isnan(result[0, 1]) and np.isnan(result[1, 1])
    assert result[0, 0] == 1.0


def test_con_with_explicit_false_value():
    array = np.array([[1.0, -1.0]])
    assert raster.con(array > 0, array, 0)[0, 1] == 0.0


def test_is_null_and_set_null():
    array = np.array([[1.0, np.nan]])
    assert raster.is_null(array).tolist() == [[False, True]]
    assert np.isnan(raster.set_null(array > 0, array)[0, 0])


def test_cell_statistics_ignores_nodata():
    a = np.array([[1.0, np.nan]])
    b = np.array([[3.0, 5.0]])
    assert raster.cell_statistics([a, b], "MAXIMUM").tolist() == [[3.0, 5.0]]
    assert raster.cell_statistics([a, b], "MEAN").tolist() == [[2.0, 5.0]]
    assert raster.cell_statistics([a, b], "SUM").tolist() == [[4.0, 5.0]]


def test_cell_statistics_sum_keeps_all_nodata_as_nodata():
    a = np.array([[np.nan]])
    assert np.isnan(raster.cell_statistics([a, a], "SUM")[0, 0])


def test_reclassify():
    array = np.array([[0.5, 1.5, 7.0, np.nan]])
    result = raster.reclassify(array, breaks=[1.0, 5.0], values=[10, 20, 30])
    assert result[0, 0] == 10 and result[0, 1] == 20 and result[0, 2] == 30
    assert np.isnan(result[0, 3])


def test_polygonize_rasterize_round_trip(grid):
    path, _, _ = grid
    array, prof = raster.read(path)
    binary = (np.nan_to_num(array) > 100).astype("int32")
    gdf = raster.polygonize(binary, prof, mask=binary.astype(bool))
    assert len(gdf) >= 1
    assert gdf.geometry.area.sum() == pytest.approx(binary.sum() * 1.0)
    back = raster.rasterize(gdf, prof)
    assert (back == binary).mean() > 0.99


def test_raster_to_points_returns_exact_values(grid):
    path, _, _ = grid
    array, prof = raster.read(path)
    points, values = raster.raster_to_points(array, prof)
    assert points.shape[0] == values.shape[0] == int(np.isfinite(array).sum())
    assert np.isfinite(values).all()


def test_idw_is_bounded_by_its_inputs(grid):
    path, _, _ = grid
    array, prof = raster.read(path)
    points, values = raster.raster_to_points(array, prof, step=7)
    result = raster.idw(points, values, prof, k=8)
    assert np.isfinite(result).all()
    assert result.min() >= values.min() - 1e-9
    assert result.max() <= values.max() + 1e-9


def test_nearest_neighbour_reproduces_source_values(grid):
    path, _, _ = grid
    array, prof = raster.read(path)
    points, values = raster.raster_to_points(array, prof, step=5)
    result = raster.nearest_neighbour(points, values, prof)
    assert set(np.unique(result)).issubset(set(np.unique(values)))


def test_label_regions_connectivity():
    binary = np.zeros((10, 10), dtype=int)
    binary[1:4, 1:4] = 1
    binary[6:9, 6:9] = 1
    binary[4, 4] = 1
    _, four = raster.label_regions(binary, connectivity=4)
    _, eight = raster.label_regions(binary, connectivity=8)
    assert four == 3
    assert eight == 2  # the diagonal bridge merges with the first block


def test_disconnected_mask_finds_all_but_largest():
    binary = np.zeros((10, 10), dtype=int)
    binary[1:5, 1:5] = 1      # largest, 16 cells
    binary[8, 8] = 1          # isolated pool
    mask, pools = raster.disconnected_mask(binary)
    assert pools == 1
    assert mask.sum() == 1


def test_disconnected_mask_on_empty_input():
    mask, pools = raster.disconnected_mask(np.zeros((5, 5), dtype=int))
    assert pools == 0 and not mask.any()


def test_tabulate_area(grid):
    path, _, _ = grid
    array, prof = raster.read(path)
    areas = raster.tabulate_area(array, prof, breaks=[100.0, 400.0])
    assert sum(areas.values()) == pytest.approx(int(np.isfinite(array).sum()) * 1.0)


def test_slope_of_flat_surface_is_zero():
    dem = np.full((10, 10), 5.0)
    assert np.allclose(raster.slope(dem, 1.0, 1.0), 0.0)


def test_slope_of_45_degree_ramp():
    dem = np.tile(np.arange(10, dtype="float64"), (10, 1))
    result = raster.slope(dem, 1.0, 1.0)
    assert result[5, 5] == pytest.approx(45.0)


def test_list_rasters(tmp_path, grid):
    path, _, _ = grid
    assert raster.list_rasters(str(tmp_path)) == [path]


def test_within_radius_spreads_from_every_source_cell():
    """Replaces the original's raster-to-points, SpatialJoin, points-to-raster round trip."""
    mask = np.zeros((7, 7), dtype=bool)
    mask[3, 3] = True

    near = raster.within_radius(mask, radius=2.0, dx=1.0, dy=1.0)
    assert near[3, 3] and near[3, 1] and near[1, 3]
    assert not near[3, 0] and not near[0, 0]
    # exactly on the radius counts, as `search_radius` did
    assert near[3, 5]


def test_within_radius_respects_anisotropic_cells():
    mask = np.zeros((5, 5), dtype=bool)
    mask[2, 2] = True
    # 10 map units per column, 1 per row: a radius of 2 reaches two rows but no column
    near = raster.within_radius(mask, radius=2.0, dx=10.0, dy=1.0)
    assert near[0, 2] and near[4, 2]
    assert not near[2, 1] and not near[2, 3]


def test_within_radius_of_nothing_is_nothing():
    mask = np.zeros((4, 4), dtype=bool)
    assert not raster.within_radius(mask, radius=5.0).any()
    # a zero radius keeps only the source cells
    mask[1, 1] = True
    assert raster.within_radius(mask, radius=0.0).sum() == 1
