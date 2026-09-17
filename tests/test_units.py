"""Unit systems and coordinate reference systems must agree, and never silently."""

import inspect
import logging

import numpy as np
import pytest
from affine import Affine

from riverarchitect import config, raster, tiled, units
from riverarchitect.units import UnitMismatchError

METRE = "EPSG:32633"
METRE_OTHER_ZONE = "EPSG:32632"
US_FOOT = "EPSG:2226"
DEGREES = "EPSG:4326"


def make_profile(crs, width=6, height=4, cell=1.0, x0=500000.0, y0=4000000.0):
    return {"driver": "GTiff", "height": height, "width": width, "count": 1,
            "dtype": "float32", "crs": crs,
            "transform": Affine(cell, 0.0, x0, 0.0, -cell, y0)}


def write(path, crs, value=1.0, **kwargs):
    profile = make_profile(crs, **kwargs)
    raster.write(str(path), np.full((profile["height"], profile["width"]), value), profile)
    return str(path)


@pytest.fixture
def condition(tmp_path, monkeypatch):
    """A minimal condition in metres, and a way to add rasters to it."""
    directory = tmp_path / "01_Conditions" / "reach"
    directory.mkdir(parents=True)
    monkeypatch.setenv("RIVERARCHITECT_HOME", str(tmp_path))
    config.set_project_home(str(tmp_path))

    def add(name, crs=METRE):
        return write(directory / name, crs)

    for name in ("dem.tif", "dmean.tif", "h000010.tif", "u000010.tif"):
        add(name)
    yield directory, add
    config.set_project_home(None)


# ------------------------------------------------------------------- recognising units

@pytest.mark.parametrize("crs, expected", [
    (METRE, "si"), ("EPSG:3857", "si"), (US_FOOT, "us"), ("EPSG:6418", "us"),
    ("EPSG:2263", "us"), (None, None),
])
def test_the_crs_linear_unit_names_the_unit_system(crs, expected):
    assert units.crs_unit_system(crs) == expected


def test_an_international_foot_crs_is_us_customary():
    # NAD83 / Oregon GIC Lambert (ft), in international feet
    assert units.crs_unit_system("EPSG:2992") == "us"


def test_a_geographic_crs_is_refused():
    with pytest.raises(UnitMismatchError, match="degrees"):
        units.crs_unit_system(DEGREES)


def test_an_unknown_unit_system_is_refused_rather_than_guessed():
    assert units.check_unit(" SI ") == "si"
    with pytest.raises(ValueError, match="furlongs"):
        units.check_unit("furlongs")


# ------------------------------------------------------------------- defaults are SI

def test_every_analysis_defaults_to_si():
    from riverarchitect import (flows, lifespan, maxlifespan, preprocessing, projectmaker,
                                recruitment, sharc, stranding, terraforming,
                                volume_assessment)

    callables = [lifespan.LifespanDesign, sharc.SHArC, sharc.cover_hsi,
                 stranding.StrandingRisk, terraforming.Terraforming,
                 recruitment.RecruitmentPotential, maxlifespan.MaxLifespan,
                 flows.FlowSeries, flows.seasonal_flow_duration,
                 preprocessing.MorphologicalUnits, preprocessing.morphological_units,
                 preprocessing.bed_shear_stress, preprocessing.build_product,
                 projectmaker.ProjectMaker, volume_assessment.VolumeAssessment,
                 config.area_unit, config.unit_labels]
    for function in callables:
        default = inspect.signature(function).parameters["unit"].default
        assert default == "si", function.__qualname__
    assert config.unit_labels()["h"] == "m"


# ------------------------------------------------------------ rasters against the unit

def test_a_metric_condition_passes_in_si(condition):
    from riverarchitect.condition import Condition

    assert Condition("reach").check_units("si") == "si"
    assert Condition("reach").unit_system() == "si"


def test_a_metric_condition_is_refused_in_us_units(condition):
    from riverarchitect.condition import Condition

    with pytest.raises(UnitMismatchError, match="set to U.S. customary"):
        Condition("reach").check_units("us")


def test_an_analysis_refuses_the_wrong_unit_system(condition):
    from riverarchitect.stranding import StrandingRisk

    with pytest.raises(UnitMismatchError, match="EPSG:32633"):
        StrandingRisk("reach", unit="us")
    assert StrandingRisk("reach").unit == "si"


def test_the_mismatch_can_be_downgraded_to_a_warning(condition, caplog):
    from riverarchitect.condition import Condition

    with caplog.at_level(logging.WARNING, logger="riverarchitect"):
        assert Condition("reach").check_units("us", strict=False) == "si"
    assert "set to U.S. customary" in caplog.text


def test_the_environment_setting_downgrades_it_too(condition, monkeypatch, caplog):
    from riverarchitect.stranding import StrandingRisk

    monkeypatch.setattr(config, "UNIT_CHECK", "warn")
    with caplog.at_level(logging.WARNING, logger="riverarchitect"):
        assert StrandingRisk("reach", unit="us").unit == "us"
    assert "RIVERARCHITECT_UNIT_CHECK" in caplog.text
    # An explicit argument still wins over the environment.
    with pytest.raises(UnitMismatchError):
        StrandingRisk("reach", unit="us", strict_units=True)


def test_a_condition_mixing_feet_and_metres_is_refused_even_when_lenient(condition):
    from riverarchitect.condition import Condition

    _directory, add = condition
    add("h000020.tif", crs=US_FOOT)
    with pytest.raises(UnitMismatchError, match="mix unit systems"):
        Condition("reach").check_units("si", strict=False)


def test_a_raster_without_a_crs_among_others_is_refused(condition):
    from riverarchitect.condition import Condition

    _directory, add = condition
    add("u000020.tif", crs=None)
    with pytest.raises(UnitMismatchError, match="u000020.tif have no coordinate"):
        Condition("reach").check_units("si")


def test_a_condition_without_any_crs_warns(tmp_path, caplog):
    paths = [write(tmp_path / "a.tif", None), write(tmp_path / "b.tif", None)]
    with caplog.at_level(logging.WARNING, logger="riverarchitect"):
        assert units.check_rasters(paths, "us") is None
    assert "cannot be verified" in caplog.text


def test_a_geographic_condition_is_refused(tmp_path):
    path = write(tmp_path / "a.tif", DEGREES, cell=0.001, x0=15.0, y0=45.0)
    with pytest.raises(UnitMismatchError, match="geographic"):
        units.check_rasters([path], "si")


def test_differing_crs_with_one_unit_warn(tmp_path, caplog):
    paths = [write(tmp_path / "a.tif", METRE), write(tmp_path / "b.tif", METRE_OTHER_ZONE)]
    units._warned_pairs.clear()          # the warning is issued once per pair of CRSs
    with caplog.at_level(logging.WARNING, logger="riverarchitect"):
        assert units.check_rasters(paths, "si") == "si"
    assert "Reprojecting" in caplog.text


def test_the_project_note_names_the_mismatching_condition(condition):
    directory, _add = condition
    assert units.project_unit_note("si") is None
    note = units.project_unit_note("us")
    assert "reach: the rasters are in SI (metric) units" in note


# ------------------------------------------------------------------ combining rasters

def test_align_refuses_feet_onto_metres():
    array = np.ones((4, 6))
    with pytest.raises(UnitMismatchError, match="linear units differ"):
        raster.align(array, make_profile(US_FOOT), make_profile(METRE))


def test_align_refuses_a_missing_crs_on_one_side():
    array = np.ones((4, 6))
    with pytest.raises(UnitMismatchError, match="no CRS"):
        raster.align(array, make_profile(None), make_profile(METRE))


def test_align_refuses_degrees():
    array = np.ones((4, 6))
    with pytest.raises(UnitMismatchError, match="geographic"):
        raster.align(array, make_profile(DEGREES, cell=0.001, x0=15.0, y0=45.0),
                     make_profile(METRE))


def test_align_reprojects_between_metric_crs_with_a_warning(caplog):
    source = make_profile(METRE, width=20, height=20, cell=10.0)
    target = make_profile(METRE, width=20, height=20, cell=10.0)
    array = np.full((20, 20), 3.0)
    assert np.array_equal(raster.align(array, source, target), array)
    units._warned_pairs.clear()
    # The same place in the neighbouring zone: (500000, 4000000) in 33N is about
    # (1040078, 4016715) in 32N. A generous source grid covers the whole target.
    other = make_profile(METRE_OTHER_ZONE, width=60, height=60, cell=10.0, x0=1039900.0,
                         y0=4016900.0)
    with caplog.at_level(logging.WARNING, logger="riverarchitect"):
        result = raster.align(np.full((60, 60), 3.0), other, target)
    assert "Reprojecting" in caplog.text
    assert np.all(result == 3.0)


def test_block_reads_refuse_feet_onto_metres(tmp_path):
    from rasterio.windows import Window

    path = write(tmp_path / "feet.tif", US_FOOT)
    with pytest.raises(UnitMismatchError, match="linear units differ"):
        tiled.read(path, make_profile(METRE), Window(0, 0, 3, 2))
    with pytest.raises(UnitMismatchError, match="linear units differ"):
        tiled.read((np.ones((4, 6)), make_profile(US_FOOT)), make_profile(METRE),
                   Window(0, 0, 3, 2))
