"""Tests for the condition preprocessing products.

The fixtures are geometrically simple enough that the right answer is known in advance: a
plane tilted along the channel detrends to exactly zero, and a flat water surface gives a
depth-to-water-table equal to the ground's height above it.
"""

import os

import numpy as np
import pytest

from riverarchitect import config, raster
from riverarchitect import preprocessing as pre
from riverarchitect.condition import parse_input_definitions


def make_profile(width=9, height=5, cell=1.0):
    from affine import Affine
    return {"driver": "GTiff", "height": height, "width": width, "count": 1,
            "dtype": "float32", "crs": "EPSG:32633",
            "transform": Affine(cell, 0.0, 0.0, 0.0, -cell, height * cell)}


@pytest.fixture
def sloping_reach(tmp_path):
    """A bed sloping downstream with a wetted thalweg along the middle row."""
    profile = make_profile(width=9, height=5)
    columns = np.arange(9, dtype="float64")

    # bed drops 0.5 per column downstream, and rises 1.0 per row away from the thalweg
    dem = np.zeros((5, 9))
    for row in range(5):
        dem[row] = 100.0 - 0.5 * columns + abs(row - 2) * 1.0

    depth = np.zeros((5, 9))
    depth[2] = 1.0                       # only the middle row is wet

    dem_path = str(tmp_path / "dem.tif")
    depth_path = str(tmp_path / "h000100.tif")
    raster.write(dem_path, dem, profile)
    raster.write(depth_path, depth, profile)
    return dem_path, depth_path, profile, dem


# ------------------------------------------------------------------- detrended DEM

def test_detrended_dem_is_zero_along_the_thalweg(sloping_reach):
    """The thalweg is its own nearest wetted cell, so it detrends to exactly zero."""
    dem_path, depth_path, _profile, _dem = sloping_reach
    detrended, _out = pre.detrended_dem(dem_path, depth_path)
    assert detrended[2] == pytest.approx(np.zeros(9))


def test_detrended_dem_removes_the_downstream_slope(sloping_reach):
    """Off the thalweg, the value is the height above the nearest thalweg cell.

    Rows 1 and 3 sit exactly 1.0 above the thalweg at the same column, everywhere.
    """
    dem_path, depth_path, _profile, _dem = sloping_reach
    detrended, _out = pre.detrended_dem(dem_path, depth_path)
    assert detrended[1] == pytest.approx(np.ones(9))
    assert detrended[3] == pytest.approx(np.ones(9))
    assert detrended[0] == pytest.approx(np.full(9, 2.0))


def test_detrended_dem_needs_a_wetted_cell(tmp_path, sloping_reach):
    dem_path, _depth_path, profile, _dem = sloping_reach
    dry = str(tmp_path / "dry.tif")
    raster.write(dry, np.zeros((5, 9)), profile)
    with pytest.raises(ValueError, match="thalweg"):
        pre.detrended_dem(dem_path, dry)


def test_unknown_interpolation_method_raises(sloping_reach):
    dem_path, depth_path, _profile, _dem = sloping_reach
    with pytest.raises(ValueError):
        pre.detrended_dem(dem_path, depth_path, method="magic")
    assert "nearest" in pre.INTERPOLATION_METHODS


# --------------------------------------------------------------------- water levels

def test_water_surface_matches_dem_plus_depth_where_wet(sloping_reach):
    dem_path, depth_path, _profile, dem = sloping_reach
    wle, _out = pre.water_level_elevation(dem_path, depth_path)
    assert wle[2] == pytest.approx(dem[2] + 1.0)


def test_depth_to_water_table_is_ground_above_the_water_surface(sloping_reach):
    """Row 1 is 1.0 above the thalweg bed, whose surface is 1.0 above that again."""
    dem_path, depth_path, _profile, _dem = sloping_reach
    d2w, _out = pre.depth_to_water_table(dem_path, depth_path)
    assert d2w[1] == pytest.approx(np.zeros(9))          # 1.0 up, 1.0 of water
    assert d2w[0] == pytest.approx(np.ones(9))
    # under the water surface the value is negative and is kept, not clipped
    assert np.all(d2w[2] < 0)


def test_interpolated_depth_keeps_only_positive_depths(sloping_reach):
    dem_path, depth_path, _profile, _dem = sloping_reach
    depth, _out = pre.interpolated_depth(dem_path, depth_path)
    finite = depth[np.isfinite(depth)]
    assert finite.size
    assert np.all(finite > 0)
    assert np.isnan(depth[0]).all()                      # high ground stays dry


def test_water_products_accept_a_precomputed_surface(sloping_reach):
    dem_path, depth_path, _profile, _dem = sloping_reach
    wle, _out = pre.water_level_elevation(dem_path, depth_path)
    a, _p = pre.depth_to_water_table(dem_path, None, wle=wle)
    b, _p = pre.depth_to_water_table(dem_path, depth_path)
    assert np.allclose(a, b, equal_nan=True)


# --------------------------------------------------------------- morphological units

def test_morphological_unit_table_converts_to_us_units():
    metric = pre.MorphologicalUnits(unit="si")
    customary = pre.MorphologicalUnits(unit="us")
    assert len(metric) == len(customary) > 0
    # 1 m = 3.2808399 ft, the factor the original used
    assert (customary.units["pool"]["h_min"]
            == pytest.approx(metric.units["pool"]["h_min"] * 3.2808399, rel=1e-6))


def test_morphological_units_classify_by_depth_and_velocity(tmp_path):
    """A deep slow cell is a pool; a shallow fast one is a riffle."""
    profile = make_profile(width=2, height=1)
    table = pre.MorphologicalUnits(unit="si")
    depth_path = str(tmp_path / "h.tif")
    velocity_path = str(tmp_path / "u.tif")
    # pool: h >= 1.4, u < 0.6   |   riffle: h < 0.7, u >= 0.6
    raster.write(depth_path, np.array([[2.0, 0.3]]), profile)
    raster.write(velocity_path, np.array([[0.1, 1.0]]), profile)

    mu, _profile, _table = pre.morphological_units(depth_path, velocity_path, table=table)
    assert mu[0][0] == pytest.approx(table.units["pool"]["code"])
    assert mu[0][1] == pytest.approx(table.units["riffle"]["code"])


def test_morphological_units_ignore_dry_cells(tmp_path):
    profile = make_profile(width=2, height=1)
    table = pre.MorphologicalUnits(unit="si")
    depth_path = str(tmp_path / "h.tif")
    velocity_path = str(tmp_path / "u.tif")
    raster.write(depth_path, np.array([[2.0, 0.0]]), profile)
    raster.write(velocity_path, np.array([[0.1, 0.1]]), profile)
    mu, _profile, _table = pre.morphological_units(depth_path, velocity_path, table=table)
    assert np.isnan(mu[0][1])


def test_morphological_units_report_when_nothing_classifies(tmp_path):
    """Wrong units are the usual cause, so say so rather than write an empty raster."""
    profile = make_profile(width=1, height=1)
    depth_path = str(tmp_path / "h.tif")
    velocity_path = str(tmp_path / "u.tif")
    raster.write(depth_path, np.array([[1e6]]), profile)
    raster.write(velocity_path, np.array([[1e6]]), profile)
    with pytest.raises(ValueError, match="units"):
        pre.morphological_units(depth_path, velocity_path,
                                table=pre.MorphologicalUnits(unit="si"))


# ------------------------------------------------------------------ condition setup

def test_write_input_definitions_round_trips(tmp_path):
    profile = make_profile(width=2, height=1)
    for discharge in (100, 500, 2000):
        raster.write(str(tmp_path / ("h%06d.tif" % discharge)), np.ones((1, 2)), profile)
        raster.write(str(tmp_path / ("u%06d.tif" % discharge)), np.ones((1, 2)), profile)

    path = pre.write_input_definitions(tmp_path, return_periods=[1.5, 5.0, 20.0])
    values = parse_input_definitions(path)
    assert values["return_periods"] == [1.5, 5.0, 20.0]
    assert values["depth_rasters"] == ["h000100.tif", "h000500.tif", "h002000.tif"]
    assert values["velocity_rasters"] == ["u000100.tif", "u000500.tif", "u002000.tif"]
    assert values["dem_raster"] == "dem"


def test_write_input_definitions_keeps_decimal_discharge_names(tmp_path):
    profile = make_profile(width=2, height=1)
    for token in ("000001_060", "000293_000"):
        raster.write(str(tmp_path / ("h%s.tif" % token)), np.ones((1, 2)), profile)
        raster.write(str(tmp_path / ("u%s.tif" % token)), np.ones((1, 2)), profile)

    path = pre.write_input_definitions(tmp_path)
    values = parse_input_definitions(path)
    # The names on disk are kept: "h000293_000.tif" parses to 293.0, and regenerating
    # the compact token "h000293.tif" would name a raster that is not there.
    assert values["depth_rasters"] == ["h000001_060.tif", "h000293_000.tif"]
    assert values["velocity_rasters"] == ["u000001_060.tif", "u000293_000.tif"]


def test_write_input_definitions_rejects_mismatched_return_periods(tmp_path):
    profile = make_profile(width=2, height=1)
    raster.write(str(tmp_path / "h000100.tif"), np.ones((1, 2)), profile)
    with pytest.raises(ValueError, match="correspond"):
        pre.write_input_definitions(tmp_path, return_periods=[1.0, 2.0])


def test_write_input_definitions_accepts_custom_raster_names(tmp_path):
    profile = make_profile(width=2, height=1)
    raster.write(str(tmp_path / "h000100.tif"), np.ones((1, 2)), profile)
    path = pre.write_input_definitions(tmp_path, grain_raster="d50")
    assert parse_input_definitions(path)["grain_raster"] == "d50"


def test_align_condition_puts_everything_on_one_grid(tmp_path):
    fine = make_profile(width=8, height=4, cell=1.0)
    coarse = make_profile(width=4, height=2, cell=2.0)
    raster.write(str(tmp_path / "dem.tif"), np.ones((4, 8)), fine)
    raster.write(str(tmp_path / "scour.tif"), np.ones((2, 4)), coarse)

    output = tmp_path / "aligned"
    results = pre.align_condition(str(tmp_path), output_dir=str(output))
    assert len(results) == 2

    for name in ("dem.tif", "scour.tif"):
        _array, profile = raster.read(str(output / name))
        assert (profile["width"], profile["height"]) == (8, 4)


def test_align_condition_needs_rasters(tmp_path):
    with pytest.raises(FileNotFoundError):
        pre.align_condition(str(tmp_path))


# --------------------------------------------------------------- shared product list

def test_every_product_has_a_note():
    keys = {key for _label, key in pre.PRODUCTS}
    assert keys == set(pre.PRODUCT_NOTES)


def test_build_product_rejects_an_unknown_key(tmp_path, monkeypatch):
    directory = tmp_path / "01_Conditions" / "c"
    directory.mkdir(parents=True)
    profile = make_profile(width=2, height=1)
    raster.write(str(directory / "dem.tif"), np.ones((1, 2)), profile)
    monkeypatch.setenv("RIVERARCHITECT_HOME", str(tmp_path))
    config.set_project_home(str(tmp_path))
    try:
        with pytest.raises(ValueError, match="unknown product"):
            pre.build_product("c", "nonsense")
    finally:
        config.set_project_home(None)


def test_the_table_keeps_the_floodplain_units_lifespan_needs():
    """Floodplain units carry a code but no depth or velocity range.

    Requiring all four bounds dropped them, and with them every code the lifespan feature
    thresholds actually name - ``mu_relevant`` lists are mostly floodplain units.
    """
    table = pre.MorphologicalUnits(unit="us")
    codes = table.codes()
    assert codes["pool"] == 23                 # instream, hydraulically delineated
    assert codes["floodplain"] == 12           # floodplain, no hydraulic range
    assert codes["terrace"] == 32
    assert np.isnan(table.units["floodplain"]["h_min"])
    assert not np.isnan(table.units["pool"]["h_min"])


def test_only_hydraulically_delineated_units_can_be_classified():
    table = pre.MorphologicalUnits(unit="us")
    classifiable = table.classifiable()
    assert "pool" in classifiable and "floodplain" not in classifiable
    assert len(classifiable) < len(table.units)
    assert all(not np.isnan(entry["h_min"]) for entry in classifiable.values())


def test_aliases_bridge_the_two_naming_vocabularies():
    """The threshold workbook and the MU workbook never agreed on unit names."""
    codes = pre.MorphologicalUnits(unit="us").codes()
    for alias, canonical in pre.MU_ALIASES.items():
        if canonical in codes:
            assert codes[alias] == codes[canonical], alias


def test_build_product_writes_the_inp_into_the_output_directory(tmp_path, monkeypatch):
    """``output_dir`` used to be ignored for the .inp, which overwrote the condition's."""
    directory = tmp_path / "01_Conditions" / "c"
    directory.mkdir(parents=True)
    profile = make_profile(width=2, height=1)
    raster.write(str(directory / "dem.tif"), np.ones((1, 2)), profile)
    raster.write(str(directory / "h001000.tif"), np.ones((1, 2)), profile)
    raster.write(str(directory / "u001000.tif"), np.ones((1, 2)), profile)

    monkeypatch.setenv("RIVERARCHITECT_HOME", str(tmp_path))
    config.set_project_home(str(tmp_path))
    try:
        target = tmp_path / "elsewhere"
        pre.build_product("c", "inp", output_dir=str(target))
        assert (target / "input_definitions.inp").is_file()
        assert not (directory / "input_definitions.inp").exists()
    finally:
        config.set_project_home(None)
