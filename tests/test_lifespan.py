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


def theta84_closed_form(u, h=2.0, dmean=0.05, gravity=9.81):
    """The regime-aware Shields stress of :mod:`riverarchitect.shear`, written out longhand.

    Kept as an independent transcription of the closure rather than a call into it, so a
    change in ``shear`` has to be a deliberate one to keep these tests passing.
    """
    import math

    d84 = 2.2 * dmean
    chi = h / (2.0 * d84)
    x = h / d84
    rr = 4.416 * x ** 1.904 * (1.0 + (x / 1.283) ** 1.618) ** -1.083
    keu = 5.75 * math.log10(12.2 * chi)
    t = min(max((chi - 7.0) / 13.0, 0.0), 1.0)
    w = t * t * (3.0 - 2.0 * t)
    cf = (1.0 - w) / rr ** 2 + w / keu ** 2
    return u ** 2 * cf / (gravity * 1.68 * d84)


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


def test_both_depth_key_spellings_are_read(tmp_path):
    """"Water depth" is what this package writes; "Flow depth" is what 1.x wrote.

    Every condition in existence carries the 1.x spelling - the bundled sample among them -
    so dropping it would make them all unreadable.
    """
    for key in ("Water depth (h)", "Flow depth (h)", "WATER DEPTH", "flow depth"):
        path = tmp_path / "defs.inp"
        path.write_text("%s = h000100.tif, h000200.tif #[LIST]\n" % key, encoding="utf-8")
        values = parse_input_definitions(str(path))
        assert values["depth_rasters"] == ["h000100.tif", "h000200.tif"], key


def test_written_input_definitions_use_the_corrected_term(tmp_path):
    """A file this package writes says "water depth", and reads back the same either way."""
    from riverarchitect import preprocessing as pre

    profile = make_profile(width=2, height=1)
    for discharge in (100, 200):
        raster.write(str(tmp_path / ("h%06d.tif" % discharge)), np.ones((1, 2)), profile)
        raster.write(str(tmp_path / ("u%06d.tif" % discharge)), np.ones((1, 2)), profile)

    path = pre.write_input_definitions(tmp_path)
    text = open(path, encoding="utf-8").read()
    assert "Water depth (h)" in text
    assert "Flow depth" not in text
    assert parse_input_definitions(path)["depth_rasters"] == ["h000100.tif", "h000200.tif"]


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
    analysis = LifespanDesign("synthetic", unit="si")
    analysis._set_reference()
    grain = analysis._read("dmean")

    tau_cr = 0.047
    expected = None
    for period, velocity in zip([2.0, 5.0, 10.0, 25.0], [1.0, 2.0, 4.0, 8.0]):
        if theta84_closed_form(velocity) >= tau_cr:
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


# --------------------------------------------------------------- vegetation plantings

#: The three plant species the wiki documents thresholds for, minus Box Elder, which shares
#: Cottonwood's criteria. Each exercises a different combination of the hierarchy: Cottonwood
#: depth and velocity, Willow depth and bed shear stress, White Alder bed shear stress alone.
PLANTS = ("cot", "wil", "whi")


def test_plant_thresholds_are_the_workbook_ones():
    """The three keep the criteria ``threshold_values.xlsx`` gave them in 1.x.

    The lengths stay in U.S. customary feet: the original multiplied them by ``ft2m`` on
    read and divided by it again when analysing, so the workbook value is what applies.
    See *Threshold units are a round trip* in ``docs/guide/arcpy_migration.md``.
    """
    cottonwood, willow, alder = (FEATURES[fid] for fid in PLANTS)
    assert (cottonwood.h_max, cottonwood.u_max, cottonwood.tau_cr) == (2.1, 3, None)
    assert (willow.h_max, willow.u_max, willow.tau_cr) == (2.1, None, 0.1)
    assert (alder.h_max, alder.u_max, alder.tau_cr) == (None, None, 0.06)
    for feature in (cottonwood, willow, alder):
        assert (feature.d2w_min, feature.d2w_max) == (1, 7)
        assert feature.group == "Vegetation plantings"
        # the wiki, on plantings: "No design maps are created because the lifespan maps
        # already contain all relevant information."
        assert feature.lifespan_mapping and not feature.design_mapping


def test_cottonwood_fails_at_the_first_flood_exceeding_depth_or_velocity(project):
    """Depth stays at 2.0 below the 2.1 threshold; velocity first passes 3.0 at the third
    discharge, whose return period is 10 years."""
    analysis = LifespanDesign("synthetic", unit="si")
    analysis._set_reference()
    grain = analysis._read("dmean")

    depth_only = analysis._hydraulic_lifespan(Feature("t", "t", h_max=2.1), grain)
    assert not np.isfinite(depth_only).any(), "the depth criterion must not fire here"

    # A criterion that never fails must leave the answer to the ones that do, because
    # arcpy's CellStatistics(..., "DATA") ignores NoData rather than propagating it.
    assert np.all(analysis._hydraulic_lifespan(FEATURES["cot"], grain) == 10.0)


@pytest.mark.parametrize("fid, expected", [("wil", 25.0), ("whi", 10.0)])
def test_shields_stress_plants_fail_at_the_closed_form_flood(project, fid, expected):
    """Willow's tau_cr of 0.1 survives one flood longer than White Alder's 0.06."""
    analysis = LifespanDesign("synthetic", unit="si")
    analysis._set_reference()
    grain = analysis._read("dmean")

    tau_cr = FEATURES[fid].tau_cr
    by_hand = next(period for period, velocity
                   in zip([2.0, 5.0, 10.0, 25.0], [1.0, 2.0, 4.0, 8.0])
                   if theta84_closed_form(velocity) >= tau_cr)
    assert by_hand == expected
    assert np.all(analysis._hydraulic_lifespan(FEATURES[fid], grain) == expected)


def test_plant_maps_are_cut_to_the_water_table_band(project, tmp_path):
    """d2w is 3 ft on the left half and 30 ft on the right, and the band is 1 to 7 ft."""
    analysis = LifespanDesign("synthetic", unit="si")
    output = tmp_path / "plants"
    results = analysis.run(list(PLANTS), output_dir=str(output))

    assert not analysis.error
    assert [entry["feature"] for entry in results] == list(PLANTS)
    for fid in PLANTS:
        array, _profile = raster.read(str(output / ("lf_%s.tif" % fid)))
        assert np.isfinite(array[:, :5]).all()
        assert not np.isfinite(array[:, 5:]).any()
        # two-argument con: outside the band is NoData, never a zero-year lifespan
        assert not np.any(array[np.isfinite(array)] == 0.0)
        assert not (output / ("ds_%s.tif" % fid)).is_file()


def test_max_lifespan_over_the_three_plants(project, tmp_path):
    """Willow wins the whole band, and a fourth feature in the folder stays out of it."""
    analysis = LifespanDesign("synthetic", unit="si")
    output = tmp_path / "plants"
    analysis.run(list(PLANTS), output_dir=str(output))
    raster.write(str(output / "lf_rocks.tif"), np.full((8, 10), 99.0), make_profile())

    assessment = MaxLifespan(str(output), features=list(PLANTS), unit="si")
    assert assessment.feature_ids == sorted(PLANTS)
    result = assessment.run(output_dir=str(tmp_path / "max"), write_polygons=False)
    assert not assessment.error

    best, _profile = raster.read(result["max_lifespan_raster"])
    assert np.all(best[:, :5] == 25.0)          # willow, and not the 99 of lf_rocks
    assert not np.isfinite(best[:, 5:]).any()

    shares = {entry["feature"]: entry["share"] for entry in result["features"]}
    assert shares["wil"] == pytest.approx(100.0)
    assert shares["cot"] == pytest.approx(0.0)
    assert shares["whi"] == pytest.approx(0.0)


@pytest.fixture
def sample_home():
    """The bundled ``2100_sample`` reach as the project home, or skip."""
    from riverarchitect import guide

    if guide.sample_data_dir() is None:
        pytest.skip("not running from a source clone")
    original = config.project_home()
    try:
        yield guide.activate_sample_data()
    finally:
        config.set_project_home(original)


def test_plant_lifespan_maps_on_the_sample_reach(sample_home, tmp_path):
    """The areas quoted in ``docs/guide/example_walkthrough.md``, on the real reach.

    Cottonwood and Willow map the same *extent* - at the largest floods every cell of the
    shared 1 to 7 ft water table band passes their 2.1 ft depth threshold - while White
    Alder, limited by bed shear stress alone, maps a small part of it. The lifespans inside
    those extents differ, which is why the medians are asserted as well.
    """
    output = tmp_path / "lifespan"
    analysis = LifespanDesign("2100_sample", unit="us")
    results = {entry["feature"]: entry
               for entry in analysis.run(list(PLANTS), output_dir=str(output))}
    assert not analysis.error

    assert results["cot"]["area"] == pytest.approx(124542.0)
    assert results["wil"]["area"] == pytest.approx(124542.0)
    assert results["whi"]["area"] == pytest.approx(16200.0)
    assert results["cot"]["median_lifespan"] == pytest.approx(1.13)
    assert results["wil"]["median_lifespan"] == pytest.approx(1.19)

    condition = Condition("2100_sample")
    d2w, d2w_profile = raster.read(condition.path(condition.d2w_raster))
    for fid, span in (("cot", (1.0, 5.0)), ("wil", (1.0, 5.0)), ("whi", (1.0, 50.0))):
        assert results[fid]["area_unit"] == "sqft"
        assert (results[fid]["min_lifespan"], results[fid]["max_lifespan"]) == \
            pytest.approx(span)

        array, profile = raster.read(str(output / ("lf_%s.tif" % fid)))
        mapped = np.isfinite(array)
        # every value is one of the modelled return periods, never interpolated between two
        for value in np.unique(array[mapped]):
            assert min(abs(value - period) for period in condition.return_periods) < 1e-4
        # and every mapped cell sits inside the water table band
        band = raster.align(d2w, d2w_profile, profile)
        assert np.all((band[mapped] >= 1.0) & (band[mapped] <= 7.0))


def test_max_lifespan_of_the_plants_on_the_sample_reach(sample_home, tmp_path):
    """One maximum-lifespan raster out of the three plant maps, ties kept."""
    pytest.importorskip("geopandas")

    output = tmp_path / "lifespan"
    LifespanDesign("2100_sample", unit="us").run(list(PLANTS), output_dir=str(output))

    assessment = MaxLifespan(str(output), features=list(PLANTS), unit="us")
    result = assessment.run(output_dir=str(tmp_path / "max"))
    assert not assessment.error

    best, _profile = raster.read(result["max_lifespan_raster"])
    expected = raster.cell_statistics(
        [raster.read(str(output / ("lf_%s.tif" % fid)))[0] for fid in PLANTS], "MAXIMUM")
    finite = np.isfinite(expected)
    assert np.array_equal(np.isfinite(best), finite)
    assert np.allclose(best[finite], expected[finite])

    # the union of the three extents, which here is Cottonwood's and Willow's
    assert result["total_mapped_area"] == pytest.approx(124542.0)

    winners = np.zeros(best.shape, dtype=int)
    for entry in result["features"]:
        mask, _mask_profile = raster.read(entry["raster"])
        winners += np.isfinite(mask).astype(int)
        if entry["area"]:
            assert os.path.isfile(entry["polygons"])
    assert np.all(winners[finite] >= 1)                 # nothing mapped goes unclaimed
    assert not np.any(winners[~finite])                 # and nothing wins outside the map
    # Ties are kept rather than broken, so the shares add up to more than a hundred.
    assert np.any(winners > 1)
    assert sum(entry["share"] for entry in result["features"]) > 100.0


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


# ------------------------------------ stranding risk on the sample reach, vs Dijkstra

def dijkstra_escape_cost(passable, target, dx, dy):
    """Least-cost distance from every passable cell to the target, by Dijkstra.

    The original built a weighted graph over travel-permissible cells and ran Dijkstra
    outwards from the mainstem, writing the path length into a ``shortest_paths\\`` raster
    and calling a cell disconnected when no finite-cost path reached it. This is that search,
    with 4-neighbour edges weighted by centre-to-centre distance.
    """
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import dijkstra

    rows, cols = passable.shape
    index = -np.ones(passable.shape, dtype=np.int64)
    index[passable] = np.arange(int(passable.sum()))

    src, dst, weight = [], [], []
    for dr, dc, cost in ((0, 1, dx), (1, 0, dy)):
        here = passable[: rows - dr, : cols - dc]
        there = passable[dr:, dc:]
        edge = here & there
        src.append(index[: rows - dr, : cols - dc][edge])
        dst.append(index[dr:, dc:][edge])
        weight.append(np.full(int(edge.sum()), cost))

    n = int(passable.sum())
    graph = coo_matrix((np.concatenate(weight),
                        (np.concatenate(src), np.concatenate(dst))), shape=(n, n)).tocsr()

    cost = np.full(passable.shape, np.nan)
    sources = index[target & passable]
    if sources.size:
        distance = dijkstra(graph, directed=False, indices=sources, min_only=True)
        cost[passable] = np.where(np.isfinite(distance), distance, np.nan)
    return cost


def test_juvenile_chinook_travel_thresholds_come_from_the_workbook(sample_home):
    """0.3 ft minimum swimming depth, and a 1.9 fps limit that is recorded, not applied."""
    pytest.importorskip("openpyxl")

    analysis = StrandingRisk.for_fish("2100_sample", "Chinook salmon", "juvenile")
    assert analysis.h_min == pytest.approx(0.3)
    assert analysis.u_max == pytest.approx(1.9)
    assert analysis.velocity_limited is False
    assert (analysis.species, analysis.lifestage) == ("Chinook salmon", "juvenile")
    # deeper than fry, so a juvenile is stranded by shallower water
    assert analysis.h_min > StrandingRisk.for_fish("2100_sample", "Chinook salmon",
                                                   "fry").h_min


def test_stranding_for_juvenile_chinook_on_the_sample_reach(sample_home, tmp_path):
    """The recession walked at the juvenile's 0.3 ft threshold."""
    pytest.importorskip("openpyxl")

    analysis = StrandingRisk.for_fish("2100_sample", "Chinook salmon", "juvenile")
    assert len(analysis.discharges) == 60
    assert analysis.target_discharge == 300.0        # the lowest, as the original used

    result = analysis.run(output_dir=str(tmp_path / "stranding"))
    assert result["worst_discharge"] == 7250.0
    assert result["worst_stranded_area"] == pytest.approx(1350.0)
    assert result["total_disconnected_area"] == pytest.approx(8172.0)
    assert sum(1 for row in result["per_discharge"] if row["pools"]) == 47
    assert result["velocity_limited"] is False

    # the percentage bases: 42200 cfs is the wettest raster, not the highest discharge
    assert result["max_wetted_area"] == pytest.approx(356625.0)
    worst = next(row for row in result["per_discharge"] if row["discharge"] == 7250.0)
    assert worst["percent_of_max_wetted"] < worst["percent_stranded"]

    assert os.path.isfile(result["q_disconnect_raster"])
    assert os.path.isfile(result["pools_layer"])


def test_the_component_rule_matches_a_dijkstra_escape_route_search(sample_home):
    """The equivalence the port rests on, tested rather than assumed.

    With only the depth criterion applied, a least-cost route to the mainstem exists exactly
    when the cell's wetted region touches it, so Dijkstra and connected-component labelling
    must select the same cells. If that ever stops holding, the module's central shortcut is
    wrong.
    """
    pytest.importorskip("scipy")
    pytest.importorskip("openpyxl")

    analysis = StrandingRisk.for_fish("2100_sample", "Chinook salmon", "juvenile")
    reference = raster.profile_of(analysis._available[analysis.discharges[0]])
    dx, dy = raster.cell_size(reference)
    target = analysis.main_channel(reference)
    assert target is not None and target.any()

    for discharge in (7250.0, 16000.0, 6250.0):
        wet = analysis._wet(discharge, reference)
        by_components, pools = raster.disconnected_mask(wet, connectivity=4, target=target)
        cost = dijkstra_escape_cost(wet, target, dx, dy)
        by_dijkstra = wet & ~np.isfinite(cost)

        assert np.array_equal(by_components, by_dijkstra), discharge
        assert pools > 0                     # the discharge has to exercise the rule
        # and the escape-route raster the original wrote is recoverable from the same search
        assert np.isfinite(cost[target]).all()
        assert np.nanmax(cost) > 0.0

        # the module's own search, which is the code a caller actually reaches
        mine = analysis.escape_routes(discharge, reference)
        assert np.array_equal(np.isfinite(mine), np.isfinite(cost))
        both = np.isfinite(mine)
        assert np.allclose(mine[both], cost[both])


# ------------------------------------ escape routes under an arbitrary velocity field

@pytest.fixture
def chute(tmp_path, monkeypatch):
    """A straight channel whose only way out runs through one narrow cell.

    Row 1 is wet from column 0 to 8 at Q = 1000 and only from 0 to 3 at Q = 500, so the
    mainstem is the western half and everything east of column 4 has to pass column 4 to
    reach it. Depth alone never disconnects anything here, which is what makes the fixture
    useful: whatever the velocity criterion strands, it stranded on its own.
    """
    directory = tmp_path / "01_Conditions" / "chute"
    directory.mkdir(parents=True)
    profile = make_profile(width=9, height=3)

    high = np.zeros((3, 9))
    high[1, :] = 1.0
    low = np.zeros((3, 9))
    low[1, :4] = 1.0
    raster.write(str(directory / "h001000.tif"), high, profile)
    raster.write(str(directory / "h000500.tif"), low, profile)

    monkeypatch.setenv("RIVERARCHITECT_HOME", str(tmp_path))
    config.set_project_home(str(tmp_path))
    yield directory, profile
    config.set_project_home(None)


def flow(throat, elsewhere=0.1):
    """An arbitrary velocity field: eastward everywhere, ``throat`` fps in column 4."""
    ux = np.full((3, 9), float(elsewhere))
    ux[:, 4] = float(throat)
    return ux, np.zeros((3, 9))


def stranding_rows(analysis, tmp_path):
    result = analysis.run(output_dir=str(tmp_path / "out"), write_rasters=False)
    return {row["discharge"]: row for row in result["per_discharge"]}, result


def test_depth_alone_connects_the_whole_chute(chute, tmp_path):
    """The baseline the velocity cases are read against."""
    directory, _profile = chute
    analysis = StrandingRisk("chute", discharges=[1000, 500], h_min=0.5, unit="si",
                             u_max=2.0)
    assert analysis.velocity_limited is False        # u_max alone does not apply it
    rows, result = stranding_rows(analysis, tmp_path)
    assert rows[1000]["stranded_area"] == pytest.approx(0.0)
    assert result["u_max"] == pytest.approx(2.0)


def test_a_chute_too_fast_to_climb_strands_everything_behind_it(chute, tmp_path):
    """The velocity criterion, applied through the directed Dijkstra search.

    Column 4 runs east at 5 fps and the fish can swim 2, so the step from column 4 westwards
    to the mainstem is one the fish cannot make. Columns 4 to 8 are wet, connected and
    stranded - which is the case the depth criterion cannot express at all.
    """
    directory, _profile = chute
    field = {1000.0: flow(5.0), 500.0: flow(0.1)}
    analysis = StrandingRisk("chute", discharges=[1000, 500], h_min=0.5, unit="si",
                             u_max=2.0, velocity_field=field)
    assert analysis.velocity_limited is True

    rows, _result = stranding_rows(analysis, tmp_path)
    assert rows[1000]["stranded_area"] == pytest.approx(5.0)      # columns 4 to 8
    assert rows[1000]["pools"] == 1
    assert rows[500]["stranded_area"] == pytest.approx(0.0)       # the mainstem itself


def test_the_same_chute_pointing_the_other_way_strands_nothing(chute, tmp_path):
    """Direction is the whole point: a fish can drift down what it cannot climb up.

    An undirected criterion - "the cell is impassable because it is fast" - would strand the
    same five cells either way, which is exactly the approximation that makes the criterion
    useless on real data.
    """
    directory, _profile = chute
    field = {1000.0: flow(-5.0), 500.0: flow(-0.1)}
    analysis = StrandingRisk("chute", discharges=[1000, 500], h_min=0.5, unit="si",
                             u_max=2.0, velocity_field=field)

    rows, _result = stranding_rows(analysis, tmp_path)
    assert rows[1000]["stranded_area"] == pytest.approx(0.0)

    # and the one-way door really is one-way: nothing can travel east through it
    reference = raster.profile_of(str(directory / "h001000.tif"))
    allowed = analysis._travel_rule(1000.0, reference, 1.0, 1.0)
    assert allowed(0, -1)[1, 4]           # westwards, with the flow
    assert not allowed(0, 1)[1, 4]        # eastwards, against 5 fps


def test_escape_routes_measure_the_way_back_to_the_mainstem(chute, tmp_path):
    """The raster the original kept in ``shortest_paths``: route length, not straight-line."""
    directory, _profile = chute
    analysis = StrandingRisk("chute", discharges=[1000, 500], h_min=0.5, unit="si")
    reference = raster.profile_of(str(directory / "h001000.tif"))

    cost = analysis.escape_routes(1000.0, reference)
    assert cost[1, :4].tolist() == pytest.approx([0.0, 0.0, 0.0, 0.0])   # the mainstem
    assert cost[1, 4:].tolist() == pytest.approx([1.0, 2.0, 3.0, 4.0, 5.0])
    assert np.isnan(cost[0]).all()                                        # dry rows

    # with the chute against them, the cells behind it have no route at all
    blocked = StrandingRisk("chute", discharges=[1000, 500], h_min=0.5, unit="si",
                            u_max=2.0, velocity_field={1000.0: flow(5.0)})
    cost = blocked.escape_routes(1000.0, reference)
    assert cost[1, :4].tolist() == pytest.approx([0.0, 0.0, 0.0, 0.0])
    assert np.isnan(cost[1, 4:]).all()


def test_a_velocity_field_can_be_a_callable(chute, tmp_path):
    directory, _profile = chute
    calls = []

    def field(discharge, profile):
        calls.append(discharge)
        return flow(5.0 if discharge > 700 else 0.1)

    analysis = StrandingRisk("chute", discharges=[1000, 500], h_min=0.5, unit="si",
                             u_max=2.0, velocity_field=field)
    rows, _result = stranding_rows(analysis, tmp_path)
    assert rows[1000]["stranded_area"] == pytest.approx(5.0)
    assert set(calls) == {1000.0, 500.0}


def test_velocity_component_rasters_are_found_beside_the_condition(chute, tmp_path):
    """``ux<Q>.tif`` and ``uy<Q>.tif``, the two a 2D model can export."""
    directory, profile = chute
    for discharge, throat in ((1000, 5.0), (500, 0.1)):
        ux, uy = flow(throat)
        raster.write(str(directory / ("ux%06d.tif" % discharge)), ux, profile)
        raster.write(str(directory / ("uy%06d.tif" % discharge)), uy, profile)

    analysis = StrandingRisk("chute", discharges=[1000, 500], h_min=0.5, unit="si",
                             u_max=2.0)
    assert analysis.velocity_limited is True
    rows, result = stranding_rows(analysis, tmp_path)
    assert rows[1000]["stranded_area"] == pytest.approx(5.0)
    assert result["velocity_limited"] is True

    # without a swimming speed there is nothing to apply, components or not
    assert StrandingRisk("chute", discharges=[1000], h_min=0.5,
                         unit="si").velocity_limited is False


def test_escape_route_rasters_are_written_when_asked(chute, tmp_path):
    directory, _profile = chute
    analysis = StrandingRisk("chute", discharges=[1000, 500], h_min=0.5, unit="si")
    output = tmp_path / "routes"
    analysis.run(output_dir=str(output), write_rasters=False, write_escape_routes=True)
    assert (output / "escape_001000.tif").is_file()
    assert (output / "escape_000500.tif").is_file()
    assert not (output / "disconnected_001000.tif").exists()
