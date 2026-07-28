"""Tests for lifespan, max-lifespan and stranding analysis.

The synthetic fixtures give **analytically known** answers rather than recording whatever
the code currently produces, which is the property the volume tests already hold: a channel
whose velocity is uniform per discharge makes the failure return period exactly predictable.
"""

import os

import numpy as np
import pytest

from riverarchitect import config, raster
from riverarchitect.condition import Condition, parse_input_definitions
from riverarchitect.lifespan import FEATURES, Feature, LifespanDesign, feature_groups
from riverarchitect.maxlifespan import MaxLifespan
from riverarchitect.stranding import StrandingRisk

PROFILE_KEYS = ("driver", "height", "width", "count", "dtype", "crs", "transform")


def make_profile(width=10, height=8, cell=1.0):
    from affine import Affine
    return {"driver": "GTiff", "height": height, "width": width, "count": 1,
            "dtype": "float32", "crs": "EPSG:32633",
            "transform": Affine(cell, 0.0, 0.0, 0.0, -cell, height * cell)}


@pytest.fixture
def condition_dir(tmp_path):
    """A synthetic condition: 4 discharges, uniform depth and a velocity ramp."""
    directory = tmp_path / "01_Conditions" / "synthetic"
    directory.mkdir(parents=True)
    profile = make_profile()
    shape = (profile["height"], profile["width"])

    # Velocity rises with discharge; depth is constant. With Manning's n and tau_cr fixed,
    # the critical grain size therefore rises monotonically with discharge, so the flood at
    # which a given grain becomes mobile is known in advance.
    discharges = [1000, 2000, 3000, 4000]
    velocities = [1.0, 2.0, 4.0, 8.0]
    for discharge, velocity in zip(discharges, velocities):
        raster.write(str(directory / ("h%06d.tif" % discharge)),
                     np.full(shape, 2.0), profile)
        raster.write(str(directory / ("u%06d.tif" % discharge)),
                     np.full(shape, velocity), profile)

    raster.write(str(directory / "dmean.tif"), np.full(shape, 0.05), profile)
    raster.write(str(directory / "dem.tif"), np.zeros(shape), profile)

    # depth to water table: left half shallow, right half deep
    d2w = np.zeros(shape)
    d2w[:, : shape[1] // 2] = 3.0
    d2w[:, shape[1] // 2:] = 30.0
    raster.write(str(directory / "d2w.tif"), d2w, profile)

    (directory / "input_definitions.inp").write_text(
        "Return periods = 2.0, 5.0, 10.0, 25.0 #[LIST]\n"
        "Flow depth (h) = h001000.tif, h002000.tif, h003000.tif, h004000.tif #[LIST]\n"
        "Flow velocity (u) = u001000.tif, u002000.tif, u003000.tif, u004000.tif #[LIST]\n"
        "Grain sizes (D mean) = dmean #[STRING]\n"
        "Depth to groundwater table (d2w) = d2w #[STRING]\n"
        "DEM = dem #[STRING]\n", encoding="utf-8")
    return directory


@pytest.fixture
def project(tmp_path, condition_dir, monkeypatch):
    monkeypatch.setenv("RIVERARCHITECT_HOME", str(tmp_path))
    config.set_project_home(str(tmp_path))
    yield tmp_path
    config.set_project_home(None)


# ------------------------------------------------------------------------ condition

def test_input_definitions_are_parsed(condition_dir):
    values = parse_input_definitions(str(condition_dir / "input_definitions.inp"))
    assert values["return_periods"] == [2.0, 5.0, 10.0, 25.0]
    assert len(values["depth_rasters"]) == 4
    assert values["grain_raster"] == "dmean"
    # "DEM = dem" must not be swallowed by "Depth to groundwater table"
    assert values["dem_raster"] == "dem"


def test_comments_and_blank_lines_are_ignored(tmp_path):
    path = tmp_path / "defs.inp"
    path.write_text("# a comment line\n\nReturn periods = 1.0, 2.0 #[LIST] trailing\n",
                    encoding="utf-8")
    assert parse_input_definitions(str(path))["return_periods"] == [1.0, 2.0]


def test_discharge_is_read_from_the_file_name():
    assert Condition.discharge_of("h001000.tif") == 1000.0
    assert Condition.discharge_of("u088053.tif") == 88053.0
    assert Condition.discharge_of("dem.tif") is None


def test_condition_pairs_depth_with_velocity(project):
    condition = Condition("synthetic")
    pairs = list(condition.hydraulic_pairs())
    assert [period for period, _h, _u in pairs] == [2.0, 5.0, 10.0, 25.0]
    assert condition.max_lifespan == 25.0


def test_all_depth_rasters_scans_disk_not_just_the_inp(project, condition_dir):
    """The .inp lists flood discharges; a recession analysis needs everything on disk."""
    profile = make_profile()
    raster.write(str(condition_dir / "h000500.tif"),
                 np.full((profile["height"], profile["width"]), 1.0), profile)
    condition = Condition("synthetic")
    assert len(condition.depth_rasters) == 4          # from the .inp
    assert len(condition.all_depth_rasters()) == 5    # from disk


# ------------------------------------------------------------------------- lifespan

def test_critical_grain_size_matches_the_closed_form(project):
    analysis = LifespanDesign("synthetic", unit="si")
    depth = np.array([[2.0]])
    velocity = np.array([[4.0]])
    tau_cr, sf, n, s = 0.047, 1.3, analysis.n, 2.68
    expected = (4.0 * n) ** 2 / ((s - 1.0) * tau_cr * 2.0 ** (1.0 / 3.0)) / sf
    got = analysis.critical_grain_size(depth, velocity, tau_cr, sf)
    assert got[0, 0] == pytest.approx(expected)


def test_lifespan_is_the_first_flood_that_mobilises_the_grain(project, tmp_path):
    """Velocity doubles with each discharge, so the failure flood is predictable."""
    analysis = LifespanDesign("synthetic", unit="si")
    analysis._set_reference()
    grain = analysis._read("dmean")

    feature = Feature("t", "test", tau_cr=0.047, safety_factor=1.3)
    lifespan = analysis._hydraulic_lifespan(feature, grain)

    # Work out by hand which discharge first moves a 0.05 m grain.
    expected = None
    for period, velocity in zip([2.0, 5.0, 10.0, 25.0], [1.0, 2.0, 4.0, 8.0]):
        d_cr = analysis.critical_grain_size(np.array([[2.0]]), np.array([[velocity]]),
                                            0.047, 1.3)[0, 0]
        if d_cr >= 0.05:
            expected = period
            break
    assert np.all(lifespan == expected) if expected else np.all(~np.isfinite(lifespan))


def test_cells_surviving_every_flood_stay_nodata(project):
    """An indestructible feature must be NoData, not zero: its lifespan is unquantified."""
    analysis = LifespanDesign("synthetic", unit="si")
    analysis._set_reference()
    grain = analysis._read("dmean")
    feature = Feature("t", "test", tau_cr=1e9)          # never mobile
    lifespan = analysis._hydraulic_lifespan(feature, grain)
    # An all-NoData array, not None: the criterion *did* apply, it simply never failed.
    # None means something different - that no criterion applied at all - and run_feature
    # branches on that distinction.
    assert lifespan is not None
    assert not np.isfinite(lifespan).any()


def test_no_applicable_criterion_returns_none(project):
    """A feature with no thresholds at all yields None, so run_feature can skip it."""
    analysis = LifespanDesign("synthetic", unit="si")
    analysis._set_reference()
    assert analysis._hydraulic_lifespan(Feature("t", "test"), None) is None


def test_feature_without_any_criteria_is_skipped(project, tmp_path):
    analysis = LifespanDesign("synthetic", unit="si")
    analysis.features = {"t": Feature("t", "test")}
    assert analysis.run_feature("t", str(tmp_path / "out")) is None


def test_depth_to_water_table_masks_the_result(project):
    """The right half has d2w = 30, outside the 1..7 range, so it must drop out."""
    analysis = LifespanDesign("synthetic", unit="si")
    analysis._set_reference()
    feature = Feature("t", "test", d2w_min=1, d2w_max=7)
    mask = analysis._spatial_mask(feature, None)
    assert mask[:, :5].all()
    assert not mask[:, 5:].any()


def test_run_feature_writes_a_lifespan_raster(project, tmp_path):
    analysis = LifespanDesign("synthetic", unit="si")
    output = tmp_path / "out"
    result = analysis.run_feature(FEATURES["rocks"], str(output))
    assert result is not None
    assert os.path.isfile(result["lifespan_raster"])
    array, _profile = raster.read(result["lifespan_raster"])
    finite = array[np.isfinite(array)]
    assert set(finite.tolist()) <= {2.0, 5.0, 10.0, 25.0}


def test_unknown_feature_is_reported_not_raised(project, tmp_path):
    analysis = LifespanDesign("synthetic", unit="si")
    assert analysis.run(["no_such_feature"], output_dir=str(tmp_path / "out")) == []
    assert analysis.error is True


def test_default_features_are_grouped(project):
    groups = feature_groups()
    assert "Terraforming" in groups
    assert any(feature.fid == "rocks" for group in groups.values() for feature in group)


# --------------------------------------------------------------------- maxlifespan

def test_max_lifespan_picks_the_longest_lived_feature(tmp_path):
    profile = make_profile(width=4, height=1)
    directory = tmp_path / "lf"
    directory.mkdir()
    # feature a wins the first two cells, b the last two
    raster.write(str(directory / "lf_a.tif"), np.array([[10.0, 20.0, 5.0, 5.0]]), profile)
    raster.write(str(directory / "lf_b.tif"), np.array([[1.0, 2.0, 30.0, 40.0]]), profile)

    result = MaxLifespan(str(directory), unit="si").run(output_dir=str(tmp_path / "out"),
                                                        write_polygons=False)
    best, _profile = raster.read(result["max_lifespan_raster"])
    assert list(best[0]) == [10.0, 20.0, 30.0, 40.0]

    areas = {entry["feature"]: entry["area"] for entry in result["features"]}
    assert areas["a"] == pytest.approx(2.0)      # two 1x1 cells
    assert areas["b"] == pytest.approx(2.0)


def test_ties_are_kept_for_both_features(tmp_path):
    profile = make_profile(width=2, height=1)
    directory = tmp_path / "lf"
    directory.mkdir()
    raster.write(str(directory / "lf_a.tif"), np.array([[10.0, 10.0]]), profile)
    raster.write(str(directory / "lf_b.tif"), np.array([[10.0, 1.0]]), profile)

    result = MaxLifespan(str(directory), unit="si").run(output_dir=str(tmp_path / "out"),
                                                        write_polygons=False)
    areas = {entry["feature"]: entry["area"] for entry in result["features"]}
    assert areas["a"] == pytest.approx(2.0)
    assert areas["b"] == pytest.approx(1.0)      # wins only the tied cell


def test_max_lifespan_needs_lifespan_rasters(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(FileNotFoundError):
        MaxLifespan(str(empty))


# ----------------------------------------------------------------------- stranding

@pytest.fixture
def recession(tmp_path, monkeypatch):
    """A channel that splits into two pools as discharge drops."""
    directory = tmp_path / "01_Conditions" / "recede"
    directory.mkdir(parents=True)
    profile = make_profile(width=9, height=1)

    # 2000: continuous. 1000: a dry cell in the middle detaches a 2-cell pool.
    raster.write(str(directory / "h002000.tif"),
                 np.array([[1.0] * 9]), profile)
    raster.write(str(directory / "h001000.tif"),
                 np.array([[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0]]), profile)

    monkeypatch.setenv("RIVERARCHITECT_HOME", str(tmp_path))
    config.set_project_home(str(tmp_path))
    yield directory
    config.set_project_home(None)


def test_stranding_finds_the_detached_pool(recession, tmp_path):
    analysis = StrandingRisk("recede", discharges=[2000, 1000], h_min=0.5, unit="si")
    result = analysis.run(output_dir=str(tmp_path / "out"))

    high, low = result["per_discharge"]
    assert high["discharge"] == 2000 and high["pools"] == 0
    assert high["stranded_area"] == pytest.approx(0.0)

    # the 2-cell fragment on the right is smaller than the 6-cell mainstem
    assert low["discharge"] == 1000 and low["pools"] == 1
    assert low["stranded_area"] == pytest.approx(2.0)
    assert result["worst_discharge"] == 1000


def test_q_disconnect_records_the_highest_disconnecting_discharge(recession, tmp_path):
    analysis = StrandingRisk("recede", discharges=[2000, 1000], h_min=0.5, unit="si")
    result = analysis.run(output_dir=str(tmp_path / "out"))
    array, _profile = raster.read(result["q_disconnect_raster"])
    assert np.nanmax(array) == pytest.approx(1000.0)
    assert np.isfinite(array).sum() == 2


def test_depth_threshold_changes_what_counts_as_wetted(recession, tmp_path):
    """h_min above the actual depth leaves nothing wetted, so nothing is stranded."""
    analysis = StrandingRisk("recede", discharges=[1000], h_min=5.0, unit="si")
    result = analysis.run(output_dir=str(tmp_path / "out"), write_rasters=False)
    assert result["per_discharge"][0]["wetted_area"] == pytest.approx(0.0)


def test_for_fish_uses_the_travel_thresholds(recession):
    analysis = StrandingRisk.for_fish("recede", "Chinook salmon", "juvenile",
                                      discharges=[2000, 1000])
    assert analysis.h_min == pytest.approx(0.3)
    with pytest.raises(KeyError):
        StrandingRisk.for_fish("recede", "Trout", "fry")
