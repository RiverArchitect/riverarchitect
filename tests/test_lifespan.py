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
    # v1's write_Q_str form: '%010.3f' with '.' replaced by '_'.
    assert Condition.discharge_of("h000001_060.tif") == 1.06
    assert Condition.discharge_of("u000293_000.tif") == 293.0
    assert Condition.discharge_of("wse000025_400.tif") == 25.4


def test_discharge_token_round_trips():
    from riverarchitect.condition import discharge_label, discharge_token

    assert discharge_token(550) == "000550"
    assert discharge_token(1.06) == "000001_060"
    assert discharge_token(293.0) == "000293"
    assert Condition.discharge_of("h%s.tif" % discharge_token(1.06)) == 1.06
    assert Condition.discharge_of("h%s.tif" % discharge_token(550)) == 550.0
    assert discharge_label(550.0) == "550"
    assert discharge_label(1.06) == "1.06"


def test_decimal_discharge_condition_is_discovered(tmp_path):
    """A v1-style condition folder with underscore-decimal names and no .inp file."""
    directory = tmp_path / "rsrm_style"
    directory.mkdir()
    profile = make_profile()
    shape = (profile["height"], profile["width"])
    for token in ("000001_060", "000003_890", "000025_400"):
        raster.write(str(directory / ("h%s.tif" % token)), np.full(shape, 1.0), profile)
        raster.write(str(directory / ("u%s.tif" % token)), np.full(shape, 1.0), profile)
    raster.write(str(directory / "dmean.tif"), np.full(shape, 0.001), profile)

    condition = Condition("rsrm_style", directory=str(directory))
    assert condition.discharges == [1.06, 3.89, 25.4]
    assert condition.all_depth_rasters() == ["h000001_060.tif", "h000003_890.tif",
                                             "h000025_400.tif"]
    assert condition.depth_raster_for(3.89) == "h000003_890.tif"
    assert condition.velocity_raster_for(99.0) is None
    pairs = list(condition.hydraulic_pairs())
    assert [period for period, _h, _u in pairs] == [1.06, 3.89, 25.4]


def test_condition_describe_reports_what_is_there_and_what_is_wrong(tmp_path):
    """A folder with unpaired rasters and no .inp yields an actionable report."""
    directory = tmp_path / "broken"
    directory.mkdir()
    profile = make_profile()
    shape = (profile["height"], profile["width"])
    raster.write(str(directory / "h000001_060.tif"), np.ones(shape), profile)
    # deliberately: no matching u raster, no dem, no dmean, no .inp

    condition = Condition("broken", directory=str(directory))
    problems = condition.validate()
    assert any("input_definitions.inp is missing" in p for p in problems)
    assert any("No velocity raster" in p for p in problems)
    assert any("1.06 has a depth raster but no velocity raster" in p for p in problems)
    assert any("DEM" in p for p in problems)
    assert any("grain size" in p for p in problems)

    report = condition.describe()
    assert "depth rasters: 1" in report
    assert "velocity rasters: none" in report
    assert "Problems:" in report


def test_condition_validate_is_quiet_on_a_complete_condition(project):
    condition = Condition("synthetic")
    assert condition.validate() == []
    assert "Problems:" not in condition.describe()


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


def test_taux_failure_period_matches_the_closed_form(project):
    """A pure tau_cr feature (no safety factor) fails at an analytically known flood.

    The fixture has depth 2.0 and dmean 0.05 everywhere, so h/ks = 2.0/0.22 = 9.09: the
    blended regime. theta84 rises with the squared velocity ramp, and the first discharge
    whose closed-form theta84 crosses tau_cr is the expected failure period everywhere.
    """
    import math

    analysis = LifespanDesign("synthetic", unit="si")
    analysis._set_reference()
    grain = analysis._read("dmean")

    def theta84_of(u, h=2.0, dmean=0.05):
        d84 = 2.2 * dmean
        chi = h / (2.0 * d84)
        x = h / d84
        rr = 4.416 * x ** 1.904 * (1.0 + (x / 1.283) ** 1.618) ** -1.083
        keu = 5.75 * math.log10(12.2 * chi)
        t = min(max((chi - 7.0) / 13.0, 0.0), 1.0)
        w = t * t * (3.0 - 2.0 * t)
        cf = (1.0 - w) / rr ** 2 + w / keu ** 2
        return u ** 2 * cf / (9.81 * 1.68 * d84)

    tau_cr = 0.047
    expected = None
    for period, velocity in zip([2.0, 5.0, 10.0, 25.0], [1.0, 2.0, 4.0, 8.0]):
        if theta84_of(velocity) >= tau_cr:
            expected = period
            break
    assert expected is not None  # the fixture must exercise the criterion

    lifespan = analysis._hydraulic_lifespan(Feature("t", "test", tau_cr=tau_cr), grain)
    assert np.all(lifespan == expected)


def test_run_feature_writes_the_shear_rasters(project, tmp_path):
    """Every taux run leaves ts/tb/hks/regime beside the lifespan maps, named as
    preprocessing.bed_shear_stress names them in the condition folder."""
    import rasterio

    analysis = LifespanDesign("synthetic", unit="si")
    output = tmp_path / "out"
    analysis.features = {"t": Feature("t", "test", tau_cr=0.047)}
    result = analysis.run(["t"], output_dir=str(output))
    assert result
    for token in ("001000", "002000", "003000", "004000"):
        for prefix in ("ts", "tb", "hks"):
            assert (output / ("%s%s.tif" % (prefix, token))).is_file()
        regime_path = output / ("regime%s.tif" % token)
        assert regime_path.is_file()
        with rasterio.open(str(regime_path)) as src:
            assert src.dtypes[0] == "uint8"
            assert src.nodata == 0
            # depth 2.0 and dmean 0.05 everywhere -> h/ks = 9.09: all cells blended
            assert set(np.unique(src.read(1))) == {2}


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


def test_stranding_target_is_the_low_flow_mainstem(recession, tmp_path):
    """A fragment cut off at low flow stays cut off even if it grows large later.

    The original defined its target once, from the largest wetted region at the *lowest*
    analysed discharge, and judged every higher discharge against it. Taking the largest
    region at each discharge separately gives a different answer whenever a detached area
    outgrows the channel it is detached from.
    """
    directory = recession
    profile = make_profile(width=9, height=1)
    # At the low flow only the 3-cell channel on the left is wet: that is the mainstem.
    raster.write(str(directory / "h000500.tif"),
                 np.array([[1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]), profile)
    # At 3000 a 5-cell backwater on the right is wet as well, but cell 3 stays dry, so no
    # route joins it to the mainstem. It is larger than the mainstem it is cut off from.
    raster.write(str(directory / "h003000.tif"),
                 np.array([[1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0]]), profile)

    seeded = StrandingRisk("recede", discharges=[3000, 500], h_min=0.5, unit="si")
    assert seeded.target_discharge == 500
    rows = {row["discharge"]: row for row in
            seeded.run(output_dir=str(tmp_path / "seeded"))["per_discharge"]}
    assert rows[3000]["stranded_area"] == pytest.approx(5.0)

    largest = StrandingRisk("recede", discharges=[3000, 500], h_min=0.5, unit="si",
                            target_discharge=False)
    rows = {row["discharge"]: row for row in
            largest.run(output_dir=str(tmp_path / "largest"))["per_discharge"]}
    # Without a target the 5-cell backwater *is* the largest region, so the mainstem is
    # reported as the stranded one instead - the outcome the low-flow target prevents.
    assert rows[3000]["stranded_area"] == pytest.approx(3.0)


def test_stranding_reports_both_percentage_bases(recession, tmp_path):
    analysis = StrandingRisk("recede", discharges=[2000, 1000], h_min=0.5, unit="si")
    result = analysis.run(output_dir=str(tmp_path / "out"), write_rasters=False)
    assert result["max_wetted_area"] == pytest.approx(9.0)
    low = result["per_discharge"][1]
    # 2 of the 8 cells wetted at 1000, but 2 of the 9 wetted at the highest discharge
    assert low["percent_stranded"] == pytest.approx(100.0 * 2 / 8)
    assert low["percent_of_max_wetted"] == pytest.approx(100.0 * 2 / 9)


def test_for_fish_reads_the_packaged_fish_database(recession):
    """Thresholds come from Fish.xlsx, which spells the species "Chinook Salmon"."""
    pytest.importorskip("openpyxl")
    from riverarchitect.stranding import travel_thresholds

    thresholds = travel_thresholds("Chinook Salmon", "fry")
    assert thresholds["h_min"] == pytest.approx(0.2)
    assert thresholds["u_max"] == pytest.approx(1.9)

    analysis = StrandingRisk.for_fish("recede", "Chinook Salmon", "fry",
                                      discharges=[2000, 1000])
    assert analysis.h_min == pytest.approx(0.2)
    assert analysis.u_max == pytest.approx(1.9)
    assert analysis.species == "Chinook Salmon"


def test_travel_thresholds_fall_back_to_the_built_in_table(recession):
    """Chinook adults are in the built-in table but not in the packaged workbook."""
    from riverarchitect.stranding import travel_thresholds

    thresholds = travel_thresholds("Chinook salmon", "adult")
    assert thresholds["h_min"] == pytest.approx(0.9)


def test_morphological_unit_criterion_uses_the_packaged_table(project, tmp_path):
    """Without a workbook beside the condition the criterion used to be dropped silently.

    The original read its codes from the packaged ``morphological_units.xlsx`` too
    (``cParameters.MU.read_mus``), so falling back to it is what the criterion needs to
    apply at all on a condition that ships no table of its own.
    """
    pytest.importorskip("openpyxl")
    analysis = LifespanDesign("synthetic", unit="us")
    codes = analysis._mu_codes()
    assert codes, "no morphological unit codes were found"
    # instream units, delineated by depth and velocity
    assert codes["pool"] == 23
    # floodplain units carry a code but no hydraulic range, and used to be dropped
    assert codes["floodplain"] == 12
    assert codes["terrace"] == 32
    # the threshold table's vocabulary resolves through the alias map
    assert codes["agriplain"] == codes["agricultural plain"]
    assert codes["in-channel bar"] == codes["bar (in-channel)"]
    assert codes["high floodplain"] == codes["floodplain (high)"]


def test_features_carry_the_workbook_morphological_unit_lists():
    """sideca, gravin and gravou lost their MU lists when FEATURES was transcribed."""
    for fid in ("sideca", "gravin", "gravou"):
        feature = FEATURES[fid]
        assert feature.mu_relevant, "%s has no relevant morphological units" % fid
        assert feature.mu_method == 1
    assert "pool" in FEATURES["gravin"].mu_relevant
    assert "floodplain" in FEATURES["gravou"].mu_relevant
    assert "cutbank" in FEATURES["sideca"].mu_relevant
