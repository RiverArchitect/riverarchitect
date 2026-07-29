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
