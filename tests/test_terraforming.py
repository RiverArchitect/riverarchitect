"""Tests for threshold-based terraforming.

The rule is arithmetic - lower the ground by exactly the excess depth to the water table -
so a synthetic bench with known elevations has an exactly known answer.
"""

import numpy as np
import pytest

from riverarchitect import config, raster
from riverarchitect.terraforming import DEFAULT_D2W_MAX, Terraforming, planting_depth_limit


def make_profile(width=4, height=2, cell=1.0):
    from affine import Affine
    return {"driver": "GTiff", "height": height, "width": width, "count": 1,
            "dtype": "float32", "crs": "EPSG:32633",
            "transform": Affine(cell, 0.0, 0.0, 0.0, -cell, height * cell)}


@pytest.fixture
def bench(tmp_path, monkeypatch):
    """A bench whose depth to the water table rises from 2 to 20 ft across four cells."""
    directory = tmp_path / "01_Conditions" / "bench"
    directory.mkdir(parents=True)
    profile = make_profile()

    # Two identical rows: the volume integration needs a triangle, which one row cannot
    # make, and the second row changes no per-cell arithmetic.
    raster.write(str(directory / "dem.tif"),
                 np.tile([100.0, 105.0, 110.0, 120.0], (2, 1)), profile)
    raster.write(str(directory / "d2w.tif"),
                 np.tile([2.0, 5.0, 10.0, 20.0], (2, 1)), profile)
    raster.write(str(directory / "h001000.tif"),
                 np.tile([1.0, 0.0, 0.0, 0.0], (2, 1)), profile)
    raster.write(str(directory / "u001000.tif"),
                 np.tile([1.0, 0.0, 0.0, 0.0], (2, 1)), profile)

    actions = tmp_path / "actions"
    actions.mkdir()
    # the feature is planned everywhere
    raster.write(str(actions / "best_wil.tif"), np.ones((2, 4)), profile)

    monkeypatch.setenv("RIVERARCHITECT_HOME", str(tmp_path))
    config.set_project_home(str(tmp_path))
    yield tmp_path, actions
    config.set_project_home(None)


# ---------------------------------------------------------------- depth limit

def test_planting_depth_limit_is_the_most_demanding_species():
    """The terrain has to suit the fussiest planting planned, not the easiest."""
    from riverarchitect.lifespan import FEATURES

    limit = planting_depth_limit()
    plantings = [f.d2w_max for f in FEATURES.values()
                 if f.group == "Vegetation plantings" and f.d2w_max is not None]
    assert limit == pytest.approx(min(plantings))
    assert limit == pytest.approx(7.0)


def test_a_selection_without_a_depth_limit_falls_back():
    from riverarchitect.lifespan import FEATURES

    assert FEATURES["wood"].d2w_max is None
    assert planting_depth_limit(feature_ids=["wood"]) == pytest.approx(DEFAULT_D2W_MAX)


# ------------------------------------------------------------------- lowering

def test_only_cells_above_the_limit_are_lowered(bench):
    home, actions = bench
    analysis = Terraforming("bench", str(actions), unit="us", d2w_max=7.0)
    result = analysis.run(output_dir=str(home / "out"))

    dem, _profile = raster.read(result["dem_raster"])
    # d2w 2 and 5 are within reach: untouched. 10 and 20 are lowered by 3 and 13.
    assert list(dem[0]) == pytest.approx([100.0, 105.0, 107.0, 107.0])
    assert result["modified_cells"] == 4          # two lowered cells in each of two rows
    assert result["cut_volume"] == pytest.approx(2 * (3.0 + 13.0))
    assert result["max_cut"] == pytest.approx(13.0)


def test_a_lowered_cell_lands_exactly_at_the_limit(bench):
    """Not deeper: the point is to reach the water table, not to dig a pond."""
    home, actions = bench
    analysis = Terraforming("bench", str(actions), unit="us", d2w_max=7.0)
    result = analysis.run(output_dir=str(home / "out"))

    d2w, _profile = raster.read(result["d2w_raster"])
    assert d2w[0][2] == pytest.approx(7.0)
    assert d2w[0][3] == pytest.approx(7.0)
    # cells that were already within reach keep their original depth
    assert d2w[0][0] == pytest.approx(2.0)


def test_cells_outside_the_feature_are_untouched(bench):
    home, actions = bench
    profile = make_profile()
    # plan the feature on the first two cells only, which are already within reach
    raster.write(str(actions / "best_wil.tif"),
                 np.tile([1.0, 1.0, np.nan, np.nan], (2, 1)), profile)

    analysis = Terraforming("bench", str(actions), unit="us", d2w_max=7.0)
    result = analysis.run(output_dir=str(home / "out"), write_rasters=False)
    assert result["modified_cells"] == 0
    assert result["cut_volume"] == pytest.approx(0.0)


def test_the_cut_raster_is_nodata_where_nothing_was_dug(bench):
    """Two-argument con: an untouched cell is NoData, not a zero cut."""
    home, actions = bench
    result = Terraforming("bench", str(actions), unit="us", d2w_max=7.0) \
        .run(output_dir=str(home / "out"))
    cut, _profile = raster.read(result["cut_raster"])
    assert np.isnan(cut[0][0]) and np.isnan(cut[0][1])
    assert cut[0][2] == pytest.approx(3.0)


def test_features_are_applied_in_sequence_on_the_terrain_the_last_one_left(bench):
    """Lowering the ground lowers its depth to water, so the second feature sees the first."""
    home, actions = bench
    profile = make_profile()
    raster.write(str(actions / "best_a.tif"), np.ones((2, 4)), profile)
    raster.write(str(actions / "best_b.tif"), np.ones((2, 4)), profile)
    (actions / "best_wil.tif").unlink()

    analysis = Terraforming("bench", str(actions), unit="us", d2w_max=7.0,
                            features=["a", "b"])
    result = analysis.run(output_dir=str(home / "out"), write_rasters=False)

    first, second = result["per_feature"]
    assert first["feature"] == "a" and first["cells"] == 4
    # b finds nothing left to do, because a already brought every cell to the limit
    assert second["feature"] == "b" and second["cells"] == 0
    assert result["cut_volume"] == pytest.approx(32.0)


def test_the_result_feeds_a_volume_assessment(bench):
    """Terraforming only ever cuts, and the DoD is exactly the cut it reports.

    The two totals are *not* the same number and should not be asserted equal: the cut
    volume is a cell-wise sum over whole cells, while
    :class:`riverarchitect.volume_assessment.VolumeAssessment` integrates under the
    triangulated surface through the cell *centres*, which covers only the area between
    them. On a 4x2 test grid that is a third of the area; on a real reach the edge effect is
    negligible and the two agree within a few per cent.
    """
    from riverarchitect.volume_assessment import VolumeAssessment

    home, actions = bench
    result = Terraforming("bench", str(actions), unit="si", d2w_max=7.0) \
        .run(output_dir=str(home / "out"))

    original = str(home / "01_Conditions" / "bench" / "dem.tif")
    assessment = VolumeAssessment(original, result["dem_raster"], unit="si",
                                  level_of_detection=0.0)
    volumes = assessment.volumes()
    # Lowering the ground can never place fill.
    assert volumes["fill_volume"] == pytest.approx(0.0)
    assert volumes["excavation_volume"] > 0.0

    # The DoD is the negated cut, cell for cell, wherever anything was dug.
    difference, _profile = assessment.difference()
    cut, _profile = raster.read(result["cut_raster"])
    dug = np.isfinite(cut)
    assert np.allclose(difference[dug], -cut[dug])
    assert np.all(np.nan_to_num(difference) <= 0.0)


# --------------------------------------------------------------------- errors

def test_a_missing_action_directory_is_reported(bench):
    home, _actions = bench
    with pytest.raises(FileNotFoundError, match="no such directory"):
        Terraforming("bench", str(home / "nowhere"))


def test_an_empty_action_directory_says_what_to_do(bench):
    home, _actions = bench
    empty = home / "empty"
    empty.mkdir()
    with pytest.raises(FileNotFoundError, match="Run Max Lifespan first"):
        Terraforming("bench", str(empty))


def test_a_condition_without_a_water_table_is_refused(tmp_path, monkeypatch):
    directory = tmp_path / "01_Conditions" / "bare"
    directory.mkdir(parents=True)
    profile = make_profile(width=2, height=2)
    raster.write(str(directory / "dem.tif"), np.ones((2, 2)), profile)
    actions = tmp_path / "actions"
    actions.mkdir()
    raster.write(str(actions / "best_wil.tif"), np.ones((2, 2)), profile)

    monkeypatch.setenv("RIVERARCHITECT_HOME", str(tmp_path))
    config.set_project_home(str(tmp_path))
    try:
        with pytest.raises(FileNotFoundError, match="depth to water table"):
            Terraforming("bare", str(actions))
    finally:
        config.set_project_home(None)
