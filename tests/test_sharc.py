"""Tests for habitat suitability and Seasonal Habitat Area.

The curve interpolation and the SHArea integration both have closed forms, so these assert
against hand-computed answers rather than against recorded output.
"""

import numpy as np
import pytest

from riverarchitect import config, raster
from riverarchitect.sharc import (COMBINE_METHODS, FishDatabase, SHArC, apply_curve,
                                  default_fish_database, read_flow_duration)


def make_profile(width=4, height=1, cell=1.0):
    from affine import Affine
    return {"driver": "GTiff", "height": height, "width": width, "count": 1,
            "dtype": "float32", "crs": "EPSG:32633",
            "transform": Affine(cell, 0.0, 0.0, 0.0, -cell, height * cell)}


# --------------------------------------------------------------------- curve maths

def test_apply_curve_interpolates_linearly_between_points():
    curve = (np.array([0.0, 1.0, 2.0]), np.array([0.0, 1.0, 0.0]))
    got = apply_curve(np.array([[0.0, 0.5, 1.0, 1.5, 2.0]]), curve)
    assert got[0].tolist() == pytest.approx([0.0, 0.5, 1.0, 0.5, 0.0])


def test_apply_curve_holds_the_first_value_below_the_curve():
    """Below the first point the suitability is held, as the original's first Con did."""
    curve = (np.array([1.0, 2.0]), np.array([0.8, 0.2]))
    got = apply_curve(np.array([[0.0, 0.5]]), curve)
    assert got[0].tolist() == pytest.approx([0.8, 0.8])


def test_apply_curve_drops_to_zero_above_the_curve():
    """Above the last point the habitat is unsuitable, not maximally suitable.

    Clamping there would invent habitat at the highest discharges, which is the one place
    the interpolation must not be symmetric.
    """
    curve = (np.array([1.0, 2.0]), np.array([0.8, 0.6]))
    got = apply_curve(np.array([[2.0, 2.001, 50.0]]), curve)
    assert got[0][0] == pytest.approx(0.6)
    assert got[0][1] == pytest.approx(0.0)
    assert got[0][2] == pytest.approx(0.0)


def test_apply_curve_preserves_nodata():
    curve = (np.array([0.0, 1.0]), np.array([0.0, 1.0]))
    got = apply_curve(np.array([[0.5, np.nan]]), curve)
    assert got[0][0] == pytest.approx(0.5)
    assert np.isnan(got[0][1])


def test_apply_curve_sorts_unordered_curve_points():
    ordered = apply_curve(np.array([[0.5]]), (np.array([0.0, 1.0]), np.array([0.0, 1.0])))
    shuffled = apply_curve(np.array([[0.5]]), (np.array([1.0, 0.0]), np.array([1.0, 0.0])))
    assert ordered[0][0] == pytest.approx(shuffled[0][0])


def nested_con_raster_calc(ras, curve_data):
    """``cHSI.HHSI.nested_con_raster_calc`` of River Architect 1.x, transcribed.

    One ``Con`` per half-open curve segment, else 0, summed with
    ``CellStatistics(..., "SUM", "DATA")``. Exactly one segment can match a cell, so the sum
    is that segment's interpolated value. Kept here to compare against, because this is the
    behaviour :func:`apply_curve` claims to reproduce.
    """
    x_values, y_values = curve_data
    stack = [np.where(np.isfinite(ras), 0.0, np.nan)]           # ras * 0
    i_par_prev, i_hsi_prev = 0.0, float(y_values[0])
    for index, i_par in enumerate(x_values):
        i_par, i_hsi = float(i_par), float(y_values[index])
        with np.errstate(invalid="ignore", divide="ignore"):
            interpolated = i_hsi_prev + (ras - i_par_prev) / (i_par - i_par_prev) \
                * (i_hsi - i_hsi_prev)
            segment = np.where((ras >= i_par_prev) & (ras < i_par), interpolated, 0.0)
        stack.append(np.where(np.isfinite(ras), segment, np.nan))
        i_hsi_prev, i_par_prev = i_hsi, i_par
    return raster.cell_statistics(stack, "SUM")


def test_apply_curve_reproduces_the_arcpy_nested_con_chain():
    """numpy.interp against the Con-per-segment chain, over the whole curve and beyond it."""
    curve = (np.array([0.25, 0.8, 2.4, 5.0, 7.9]), np.array([0.0, 1.0, 1.0, 0.4, 0.0]))
    values = np.array([np.linspace(0.0, 9.0, 181)])

    mine = apply_curve(values, curve)
    theirs = nested_con_raster_calc(values, curve)
    assert np.allclose(mine, theirs, atol=1e-12)

    # and the two ends the chain is easy to get wrong
    assert mine[0][0] == pytest.approx(0.0)          # held below the first point
    assert mine[0][-1] == pytest.approx(0.0)         # zero beyond the last


def test_the_endpoint_convention_only_differs_where_the_curve_does_not_end_at_zero():
    """arcpy's segments are half-open, so a cell exactly on the last x got 0 there.

    numpy.interp returns the last suitability instead. The difference is invisible for every
    curve that ends at zero suitability - which is what the next test pins down for the
    packaged ones - so this records where it would show.
    """
    curve = (np.array([1.0, 2.0]), np.array([0.8, 0.6]))
    values = np.array([[2.0]])
    assert apply_curve(values, curve)[0][0] == pytest.approx(0.6)
    assert nested_con_raster_calc(values, curve)[0][0] == pytest.approx(0.0)


def test_curves_that_do_not_end_at_zero_end_beyond_any_real_depth():
    """Which is why the endpoint convention above cannot change a packaged result.

    A curve ending at zero suitability makes the difference invisible. The packaged ones that
    do not - Steelhead adults, Lamprey, Green Sturgeon, All Aquatic - end at 30 ft or more,
    a cap point meant to hold the suitability out to infinity rather than a value a depth
    raster is ever exactly equal to. Listed rather than waved at, so an edited workbook has
    to come back through here.
    """
    pytest.importorskip("openpyxl")
    fish = FishDatabase()

    open_ended = {}
    for species, lifestage in fish.pairs():
        for parameter in ("h", "u"):
            curve = fish.curve(species, lifestage, parameter)
            if curve is not None and curve[1][-1] != 0.0:
                open_ended[(species, lifestage, parameter)] = float(curve[0][-1])

    assert all(last_x >= 30.0 for last_x in open_ended.values()), open_ended
    # every Chinook curve ends at zero, so no Chinook result can differ at all
    assert not any(species == "Chinook Salmon" for species, _stage, _p in open_ended)


# ------------------------------------------------------------------ fish database

def test_packaged_fish_database_exists():
    import os
    assert os.path.isfile(default_fish_database())


def test_fish_database_reads_species_and_lifestages():
    database = FishDatabase()
    assert "Chinook Salmon" in database.species
    assert "juvenile" in database.lifestages("Chinook Salmon")


def test_lifestage_labels_come_from_the_workbook_not_a_fixed_list():
    """Offset 3 is 'fry' for salmon but 'ammocoetes' for lamprey."""
    database = FishDatabase()
    assert "fry" in database.lifestages("Chinook Salmon")
    assert "ammocoetes" in database.lifestages("Lamprey")
    assert "fry" not in database.lifestages("Lamprey")


def test_shortname_matches_the_original_file_naming():
    assert FishDatabase.shortname("Chinook Salmon", "spawning") == "chsp"
    assert FishDatabase.shortname("Chinook Salmon", "juvenile") == "chju"


def test_curves_are_monotonic_in_x_and_bounded_in_y():
    database = FishDatabase()
    for species, lifestage in database.pairs():
        for parameter in ("h", "u"):
            curve = database.curve(species, lifestage, parameter)
            if curve is None:
                continue
            x_values, y_values = curve
            assert np.all(np.diff(np.sort(x_values)) >= 0)
            assert y_values.min() >= 0.0 and y_values.max() <= 1.0, (species, lifestage)


def test_unknown_species_or_lifestage_raises():
    database = FishDatabase()
    with pytest.raises(KeyError):
        database.curve("Nessie", "adult", "h")
    with pytest.raises(KeyError):
        database.curve("Chinook Salmon", "larva", "h")


# ----------------------------------------------------------------------- SHArea

def test_sharea_is_a_riemann_sum_over_exceedance():
    """Two discharges at 10% and 30% cumulative exceedance, areas 100 and 200."""
    rows = [{"discharge": 500.0, "usable_area": 100.0},
            {"discharge": 100.0, "usable_area": 200.0}]
    duration = {500.0: 10.0, 100.0: 30.0}
    # 10/100 * 100  +  (30-10)/100 * 200  =  10 + 40 = 50
    assert SHArC.sharea(rows, duration) == pytest.approx(50.0)


def test_sharea_ignores_discharges_absent_from_the_flow_duration():
    rows = [{"discharge": 500.0, "usable_area": 100.0},
            {"discharge": 999.0, "usable_area": 9e9}]
    assert SHArC.sharea(rows, {500.0: 10.0}) == pytest.approx(10.0)


def test_sharea_of_nothing_is_zero():
    assert SHArC.sharea([], {100.0: 50.0}) == pytest.approx(0.0)


def test_rare_discharges_contribute_little():
    """A big habitat that only exists at a rare flow must not dominate."""
    common = SHArC.sharea([{"discharge": 1.0, "usable_area": 100.0}], {1.0: 90.0})
    rare = SHArC.sharea([{"discharge": 2.0, "usable_area": 100.0}], {2.0: 1.0})
    assert common > rare * 50


# ------------------------------------------------------------------- composite HSI

@pytest.fixture
def habitat_condition(tmp_path, monkeypatch):
    """A one-row channel with a depth and velocity ramp at two discharges."""
    directory = tmp_path / "01_Conditions" / "habitat"
    directory.mkdir(parents=True)
    profile = make_profile(width=4, height=1)
    for discharge, depth, velocity in ((1000, 1.0, 0.5), (2000, 3.0, 2.0)):
        raster.write(str(directory / ("h%06d.tif" % discharge)),
                     np.array([[0.0, depth, depth, depth]]), profile)
        raster.write(str(directory / ("u%06d.tif" % discharge)),
                     np.full((1, 4), velocity), profile)
    monkeypatch.setenv("RIVERARCHITECT_HOME", str(tmp_path))
    config.set_project_home(str(tmp_path))
    yield tmp_path
    config.set_project_home(None)


def test_composite_hsi_is_masked_to_the_wetted_area(habitat_condition):
    analysis = SHArC("habitat", unit="si")
    chsi, profile = analysis.composite_hsi("Chinook Salmon", "juvenile", 1000.0)
    # the first cell is dry, so it must be NoData rather than a suitability of zero
    assert np.isnan(chsi[0][0])
    assert np.isfinite(chsi[0][1:]).all()


def test_geometric_mean_and_product_differ_as_expected(habitat_condition):
    geometric = SHArC("habitat", unit="si", combine_method="geometric_mean")
    product = SHArC("habitat", unit="si", combine_method="product")
    a, _profile = geometric.composite_hsi("Chinook Salmon", "juvenile", 1000.0)
    b, _profile = product.composite_hsi("Chinook Salmon", "juvenile", 1000.0)
    wet = np.isfinite(a) & np.isfinite(b) & (b > 0)
    # sqrt(x) >= x for 0 <= x <= 1, so the geometric mean is never the smaller one
    assert np.all(a[wet] >= b[wet] - 1e-12)
    assert np.allclose(a[wet] ** 2, b[wet])


def test_unknown_combine_method_raises(habitat_condition):
    with pytest.raises(ValueError):
        SHArC("habitat", combine_method="average")
    assert "geometric_mean" in COMBINE_METHODS


def test_usable_area_counts_only_cells_above_the_threshold(habitat_condition):
    analysis = SHArC("habitat", unit="si", threshold=0.5)
    profile = make_profile(width=4, height=1)
    chsi = np.array([[np.nan, 0.4, 0.6, 0.9]])
    # two cells of 1 x 1 exceed 0.5
    assert analysis.usable_area(chsi, profile) == pytest.approx(2.0)


def test_weighted_usable_area_scales_by_the_mean_suitability(habitat_condition):
    analysis = SHArC("habitat", unit="si", threshold=0.5)
    profile = make_profile(width=4, height=1)
    chsi = np.array([[np.nan, 0.4, 0.6, 0.8]])
    plain = analysis.usable_area(chsi, profile, weighted=False)
    weighted = analysis.usable_area(chsi, profile, weighted=True)
    assert plain == pytest.approx(2.0)
    assert weighted == pytest.approx(2.0 * 0.7)      # mean of 0.6 and 0.8


def test_run_reports_every_requested_discharge(habitat_condition, tmp_path):
    analysis = SHArC("habitat", unit="si")
    result = analysis.run("Chinook Salmon", "juvenile",
                          output_dir=str(tmp_path / "out"))
    assert [row["discharge"] for row in result["per_discharge"]] == [1000.0, 2000.0]
    assert result["shortname"] == "chju"
    # no flow duration workbook in this synthetic project, so no SHArea
    assert "sharea" not in result


def test_run_rejects_a_condition_without_paired_rasters(tmp_path, monkeypatch):
    directory = tmp_path / "01_Conditions" / "empty"
    directory.mkdir(parents=True)
    profile = make_profile()
    raster.write(str(directory / "h001000.tif"), np.ones((1, 4)), profile)
    monkeypatch.setenv("RIVERARCHITECT_HOME", str(tmp_path))
    config.set_project_home(str(tmp_path))
    try:
        with pytest.raises(ValueError):
            SHArC("empty").run("Chinook Salmon", "juvenile")
    finally:
        config.set_project_home(None)


# -------------------------------------------------- species and lifestage lookup

def test_species_lookup_ignores_case_and_spacing():
    """The workbook writes "Chinook Salmon"; the literature writes "Chinook salmon".

    Matching exactly used to make the caller's capitalisation decide whether the analysis
    ran at all - ``SHArC.run("Chinook salmon", ...)`` raised ``KeyError`` while
    ``StrandingRisk.for_fish`` accepted the same string.
    """
    database = FishDatabase()
    for spelling in ("Chinook Salmon", "Chinook salmon", "chinook salmon",
                     "  CHINOOK   SALMON  "):
        assert database.resolve_species(spelling) == "Chinook Salmon"


def test_lifestage_lookup_ignores_case_and_spacing():
    database = FishDatabase()
    assert database.resolve_lifestage("Chinook salmon", "SPAWNING") == "spawning"
    assert database.resolve_lifestage("chinook salmon", " fry ") == "fry"


def test_curves_resolve_through_either_spelling():
    database = FishDatabase()
    lower = database.curve("Chinook salmon", "spawning", "h")
    upper = database.curve("Chinook Salmon", "spawning", "h")
    assert lower is not None
    assert np.array_equal(lower[0], upper[0])
    assert np.array_equal(lower[1], upper[1])


def test_lookup_failure_names_the_available_options():
    database = FishDatabase()
    with pytest.raises(KeyError) as info:
        database.resolve_species("Nessie")
    assert "Chinook Salmon" in str(info.value)
    with pytest.raises(KeyError) as info:
        database.resolve_lifestage("Chinook Salmon", "larva")
    assert "spawning" in str(info.value)


# ------------------------------------------------------------------ cover HSI

def make_cover_profile(width=9, height=9, cell=1.0):
    from affine import Affine
    return {"driver": "GTiff", "height": height, "width": width, "count": 1,
            "dtype": "float32", "crs": "EPSG:32633",
            "transform": Affine(cell, 0.0, 0.0, 0.0, -cell, height * cell)}


def test_cover_spreads_over_its_radius():
    """A cover element shelters everything within its radius, not only its own cell."""
    from riverarchitect.sharc import cover_hsi

    profile = make_cover_profile()
    plants = np.zeros((9, 9))
    plants[4, 4] = 1.0

    cover, used = cover_hsi("Chinook salmon", "fry", {"plants": plants}, profile, unit="si")
    assert used == ["plants"]
    sheltered = np.isfinite(cover)
    # radius 3 around the centre cell, and nothing in the far corner
    assert sheltered[4, 4] and sheltered[4, 1] and sheltered[1, 4]
    assert not sheltered[0, 0]
    assert cover[4, 4] == pytest.approx(1.0)


def test_cobbles_and_boulders_are_cut_out_of_the_grain_raster():
    """Their diameter ranges come from the original's define_grain_size, in metres."""
    from riverarchitect.sharc import GRAIN_SIZE_LIMITS, cover_hsi

    assert GRAIN_SIZE_LIMITS["cobbles"] == (0.064, 0.256)
    profile = make_cover_profile()
    # one sand cell, one cobble cell, one boulder cell
    grain = np.full((9, 9), 0.001)
    grain[4, 4] = 0.1        # cobble
    grain[0, 0] = 1.0        # boulder

    cover, used = cover_hsi("Chinook salmon", "fry", {"substrate": grain}, profile,
                            unit="si")
    assert "cobbles" in used and "boulders" in used
    assert np.isfinite(cover[4, 4]) and np.isfinite(cover[0, 0])
    # the sand in between is out of reach of both radii (0.1 m and 1.0 m)
    assert not np.isfinite(cover[4, 0])


# ---------------------------------------------------- mineral cover: areal fraction

def test_mineral_cover_is_an_areal_fraction_not_a_radius():
    """The areal-fraction rule for mineral cover, and the reason the radius one is inert.

    *"Areas where the boulder presence covers more than 30 % of the surface get assigned an
    HSI value of 0.5"*. Chinook fry ask for 10 % of cobble, so a single cobble cell carries
    its 3x3 neighbourhood (1/9 = 11 %) but not the ring beyond it. Opt-in: the radius
    reading stays the default.
    """
    from riverarchitect.sharc import cover_hsi

    profile = make_cover_profile()
    grain = np.full((9, 9), 0.001)
    grain[4, 4] = 0.1                      # one cobble cell in a sand bed

    cover, used = cover_hsi("Chinook salmon", "fry", {"substrate": grain}, profile,
                            unit="si", mineral_rule="fraction")
    assert "cobbles" in used
    sheltered = np.isfinite(cover)
    assert sheltered[3:6, 3:6].all()       # the 3x3 window around the cobble
    assert not sheltered[2, 4] and not sheltered[4, 2]
    assert cover[4, 4] == pytest.approx(0.4)

    # the default radius rule reaches only the cobble cell itself, because the workbook's
    # 0.1 is smaller than the cell
    by_radius, _used = cover_hsi("Chinook salmon", "fry", {"substrate": grain}, profile,
                                 unit="si")
    assert np.isfinite(by_radius).sum() == 1


def test_a_denser_mineral_patch_shelters_more():
    """The fraction is monotonic in how much of the neighbourhood is covered."""
    from riverarchitect.sharc import cover_hsi

    profile = make_cover_profile()
    sparse = np.full((9, 9), 0.001)
    sparse[4, 4] = 0.1
    dense = np.full((9, 9), 0.001)
    dense[3:6, 3:6] = 0.1                  # a nine-cell cobble patch

    thin, _used = cover_hsi("Chinook salmon", "fry", {"substrate": sparse}, profile,
                            unit="si", mineral_rule="fraction")
    thick, _used = cover_hsi("Chinook salmon", "fry", {"substrate": dense}, profile,
                             unit="si", mineral_rule="fraction")
    assert np.isfinite(thick).sum() > np.isfinite(thin).sum()


def test_the_mineral_window_is_configurable():
    """A wider window spreads the same patch further, and window 0 is the bare presence."""
    from riverarchitect.sharc import cover_hsi

    profile = make_cover_profile()
    grain = np.full((9, 9), 0.001)
    grain[4, 4] = 0.1

    wide, used = cover_hsi("Chinook salmon", "fry", {"substrate": grain}, profile,
                           unit="si", mineral_rule="fraction", window=2)
    # 1/25 = 4 %, below the 10 % Chinook fry ask for, so a wider window dilutes it away and
    # no cover type contributes at all
    assert wide is None and used == []

    dense = np.full((9, 9), 0.001)
    dense[2:7, 2:7] = 0.1                  # 25 cells: the 5x5 window is now full
    wide, _used = cover_hsi("Chinook salmon", "fry", {"substrate": dense}, profile,
                            unit="si", mineral_rule="fraction", window=2)
    assert np.isfinite(wide).sum() > 25


def test_an_unknown_mineral_rule_raises(habitat_condition):
    from riverarchitect.sharc import cover_hsi

    with pytest.raises(ValueError):
        cover_hsi("Chinook salmon", "fry", {}, make_cover_profile(), mineral_rule="nope")
    with pytest.raises(ValueError):
        SHArC("habitat", unit="si", mineral_rule="nope")


def test_the_best_shelter_available_wins():
    """Cell-wise maximum across cover types, as CellStatistics(..., MAXIMUM) did."""
    from riverarchitect.sharc import cover_hsi

    profile = make_cover_profile()
    grain = np.full((9, 9), 0.1)          # cobbles everywhere: suitability 0.40
    plants = np.zeros((9, 9))
    plants[4, 4] = 1.0                    # plants at the centre: suitability 1.00

    cover, used = cover_hsi("Chinook salmon", "fry",
                            {"substrate": grain, "plants": plants}, profile, unit="si")
    assert set(used) >= {"cobbles", "plants"}
    assert cover[4, 4] == pytest.approx(1.0)      # plants beat cobbles here
    assert cover[0, 0] == pytest.approx(0.4)      # only cobbles reach the corner


def test_cover_is_cropped_to_water_the_fish_can_reach():
    """Cover a fish cannot get to shelters nothing - the original's crop_input_raster."""
    from riverarchitect.sharc import cover_hsi

    profile = make_cover_profile()
    plants = np.ones((9, 9))
    # The right-hand columns are outside the modelled area: NoData, not shallow.
    depth = np.full((9, 9), 5.0)
    depth[:, 4:] = np.nan

    cover, _used = cover_hsi("Chinook salmon", "fry", {"plants": plants}, profile,
                             unit="si", depth=depth)
    assert np.isfinite(cover[4, 0])
    assert not np.isfinite(cover[4, 8])


def test_no_cover_layer_gives_no_cover():
    from riverarchitect.sharc import cover_hsi

    cover, used = cover_hsi("Chinook salmon", "fry", {}, make_cover_profile())
    assert cover is None and used == []


def test_cover_lowers_the_composite_where_shelter_is_poor(habitat_condition):
    """cHSI is a geometric mean, so a cover index below 1 can only pull it down."""
    from riverarchitect.sharc import SHArC

    analysis = SHArC("habitat", unit="si")
    discharge = analysis.discharges[0]
    plain, profile = analysis.composite_hsi("Chinook salmon", "fry", discharge)
    poor = np.full(plain.shape, 0.2)
    with_cover, _profile = analysis.composite_hsi("Chinook salmon", "fry", discharge,
                                                  cover=poor)
    finite = np.isfinite(plain) & np.isfinite(with_cover)
    assert finite.any()
    assert np.all(with_cover[finite] <= plain[finite] + 1e-9)


# ------------------------------------------------- the sample reach, end to end

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


def test_sharc_on_the_sample_reach(sample_home):
    """The usable areas and SHArea quoted in ``docs/guide/example_walkthrough.md``.

    Chinook spawning at the default 0.4 threshold, geometric mean, over all 60 discharges of
    the condition and the flow duration curve in ``00_Flows/2100_sample``.
    """
    pytest.importorskip("openpyxl")

    analysis = SHArC("2100_sample", unit="us")
    assert analysis.threshold == pytest.approx(0.4)
    assert analysis.combine_method == "geometric_mean"

    result = analysis.run("Chinook salmon", "spawning", write_rasters=False)
    assert not analysis.error
    assert result["shortname"] == "chsp"
    assert result["sharea"] == pytest.approx(24176.0, abs=1.0)

    areas = {row["discharge"]: row["usable_area"] for row in result["per_discharge"]}
    for discharge, expected in ((300, 50463), (750, 26199), (1000, 25218), (4000, 16137),
                                (9750, 66159), (20000, 24129), (42200, 11511)):
        assert areas[discharge] == pytest.approx(expected, abs=1.0), discharge

    # mean cHSI falls monotonically across the ordinary discharges, which is what spawning
    # habitat should do; usable area does not, and that is the point of SHArea.
    means = {row["discharge"]: row["mean_chsi"] for row in result["per_discharge"]}
    assert means[300] > means[4000] > means[20000] > means[42200]


def test_sharea_on_the_sample_reach_is_the_riemann_sum_of_its_own_rows(sample_home):
    """SHArea is Σ (E_i - E_{i-1}) / 100 · A_i over ascending exceedance, nothing else."""
    pytest.importorskip("openpyxl")
    import os

    analysis = SHArC("2100_sample", unit="us")
    result = analysis.run("Chinook salmon", "juvenile", write_rasters=False)
    assert result["shortname"] == "chju"

    duration = read_flow_duration(os.path.join(config.dir_flows(), "2100_sample",
                                               "flow_duration_chju.xlsx"))
    rows = sorted(result["per_discharge"], key=lambda row: row["discharge"])
    assert all(row["discharge"] in duration for row in rows)

    # Ten of the sixty discharges share an exceedance of 0 % and two share 100 %, so the
    # order among ties decides which one carries the interval. Sorting on exceedance alone
    # keeps them in discharge order, which is the row order the original workbook's
    # =(E5-E4)/100*F5 column ran down. Comparing whole tuples instead would reorder the ties
    # by area and shift SHArea by about a thousand sqft.
    paired = sorted(((duration[row["discharge"]], row["usable_area"]) for row in rows),
                    key=lambda pair: pair[0])

    total, previous = 0.0, 0.0
    for exceedance, area in paired:
        total += (exceedance - previous) / 100.0 * area
        previous = exceedance
    assert result["sharea"] == pytest.approx(total)
    assert result["sharea"] == pytest.approx(42108.0, abs=1.0)


def test_a_stricter_threshold_can_only_shrink_sharea(sample_home):
    """The wiki quotes 0.5 for the ArcGIS default; this package ships 0.4."""
    pytest.importorskip("openpyxl")

    lenient = SHArC("2100_sample", unit="us", threshold=0.4)
    strict = SHArC("2100_sample", unit="us", threshold=0.5)
    a = lenient.run("Chinook salmon", "spawning", write_rasters=False)["sharea"]
    b = strict.run("Chinook salmon", "spawning", write_rasters=False)["sharea"]
    assert b < a
    assert b == pytest.approx(18098.0, abs=1.0)
