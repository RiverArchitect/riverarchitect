"""End-to-end earthworks quantities from a pair of DEMs."""

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from riverarchitect import config
from riverarchitect.volume_assessment import VolumeAssessment


def _dem(path, array, cell=1.0, origin=(1000.0, 2000.0)):
    prof = {
        "driver": "GTiff", "height": array.shape[0], "width": array.shape[1], "count": 1,
        "dtype": "float32", "crs": "EPSG:3857", "nodata": config.NODATA,
        "transform": from_origin(origin[0], origin[1], cell, cell),
    }
    with rasterio.open(path, "w", **prof) as dst:
        dst.write(np.where(np.isfinite(array), array, config.NODATA).astype("float32"), 1)
    return str(path)


def test_uniform_fill(tmp_path):
    """Raising an 11x11 grid of 1 m cells by 2 m fills a 10x10 m TIN: 200 m3."""
    original = _dem(tmp_path / "a.tif", np.full((11, 11), 100.0))
    modified = _dem(tmp_path / "b.tif", np.full((11, 11), 102.0))
    result = VolumeAssessment(original, modified, unit="si").run()
    assert result["fill_volume"] == pytest.approx(200.0)
    assert result["excavation_volume"] == pytest.approx(0.0)
    assert result["net_volume"] == pytest.approx(200.0)


def test_uniform_excavation(tmp_path):
    original = _dem(tmp_path / "a.tif", np.full((11, 11), 100.0))
    modified = _dem(tmp_path / "b.tif", np.full((11, 11), 98.0))
    result = VolumeAssessment(original, modified, unit="si").run()
    assert result["excavation_volume"] == pytest.approx(200.0)
    assert result["fill_volume"] == pytest.approx(0.0)
    assert result["net_volume"] == pytest.approx(-200.0)


def test_level_of_detection_suppresses_small_changes(tmp_path):
    original = _dem(tmp_path / "a.tif", np.full((11, 11), 100.0))
    modified = _dem(tmp_path / "b.tif", np.full((11, 11), 100.1))
    result = VolumeAssessment(original, modified, unit="si", level_of_detection=0.3).run()
    assert result["fill_volume"] == pytest.approx(0.0)


def test_us_units_report_cubic_yards(tmp_path):
    """27 cubic feet make one cubic yard."""
    original = _dem(tmp_path / "a.tif", np.full((11, 11), 100.0))
    modified = _dem(tmp_path / "b.tif", np.full((11, 11), 103.0))
    result = VolumeAssessment(original, modified, unit="us", level_of_detection=0.99).run()
    assert result["fill_volume"] == pytest.approx(300.0 / 27.0)
    assert result["volume_unit"] == "cubic yard"


def test_differing_extents_are_aligned(tmp_path):
    """The modified DEM covers a smaller footprint; it must be aligned, not broadcast."""
    original = _dem(tmp_path / "a.tif", np.full((21, 21), 100.0))
    modified = _dem(tmp_path / "b.tif", np.full((11, 11), 102.0))
    assessment = VolumeAssessment(original, modified, unit="si")
    dod, prof = assessment.difference()
    assert dod.shape == (21, 21)
    assert np.isfinite(dod).any()


def test_writes_output_rasters(tmp_path):
    original = _dem(tmp_path / "a.tif", np.full((11, 11), 100.0))
    modified = _dem(tmp_path / "b.tif", np.full((11, 11), 102.0))
    out = tmp_path / "out"
    result = VolumeAssessment(original, modified, unit="si").run(output_dir=str(out))
    for name in ("dod", "fill", "excavation"):
        assert (out / ("%s.tif" % name)).is_file()
    assert "rasters" in result


def test_invalid_unit_falls_back_to_us(tmp_path):
    original = _dem(tmp_path / "a.tif", np.full((5, 5), 100.0))
    modified = _dem(tmp_path / "b.tif", np.full((5, 5), 100.0))
    assert VolumeAssessment(original, modified, unit="furlongs").unit == "us"


def test_nodata_regions_excluded(tmp_path):
    array = np.full((11, 11), 100.0)
    array[0, :] = np.nan
    original = _dem(tmp_path / "a.tif", array)
    modified = _dem(tmp_path / "b.tif", np.full((11, 11), 102.0))
    result = VolumeAssessment(original, modified, unit="si").run()
    # one row of nodes drops out of the TIN: 9 x 10 m instead of 10 x 10 m
    assert result["fill_volume"] == pytest.approx(180.0)
