"""Tests for the riparian recruitment box model.

The four objectives are scored on fixed thresholds, so a synthetic flow record with a known
peak and a known recession rate has a known answer.
"""

import datetime as dt

import numpy as np
import pytest

from riverarchitect import config, raster
from riverarchitect.recruitment import (RecruitmentParameters, RecruitmentPotential,
                                        read_flow_series)


def make_profile(width=4, height=1, cell=1.0):
    from affine import Affine
    return {"driver": "GTiff", "height": height, "width": width, "count": 1,
            "dtype": "float32", "crs": "EPSG:32633",
            "transform": Affine(cell, 0.0, 0.0, 0.0, -cell, height * cell)}


@pytest.fixture
def floodplain(tmp_path, monkeypatch):
    """A bench rising away from a channel, with two modelled discharges."""
    directory = tmp_path / "01_Conditions" / "bench"
    directory.mkdir(parents=True)
    profile = make_profile(width=4, height=1)

    # ground rises from 100.0 at the channel to 103.0 on the bench
    raster.write(str(directory / "dem.tif"), np.array([[100.0, 101.0, 102.0, 103.0]]),
                 profile)
    raster.write(str(directory / "dmean.tif"), np.full((1, 4), 0.01), profile)

    # low flow wets the channel to 100.5; high flow to 102.5
    raster.write(str(directory / "h000100.tif"), np.array([[0.5, 0.0, 0.0, 0.0]]), profile)
    raster.write(str(directory / "u000100.tif"), np.full((1, 4), 0.3), profile)
    raster.write(str(directory / "h005000.tif"), np.array([[2.5, 1.5, 0.5, 0.0]]), profile)
    raster.write(str(directory / "u005000.tif"), np.full((1, 4), 3.0), profile)

    monkeypatch.setenv("RIVERARCHITECT_HOME", str(tmp_path))
    config.set_project_home(str(tmp_path))
    yield tmp_path
    config.set_project_home(None)


def season(year=2020, winter_peak=5000.0, summer=100.0):
    """A year of daily flows: a winter peak, then a steady summer baseflow."""
    series = {}
    day = dt.date(year - 1, 10, 1)
    while day <= dt.date(year, 9, 30):
        series[day] = winter_peak if day.month in (1, 2) else summer
        day += dt.timedelta(days=1)
    return series


# ------------------------------------------------------------------- parameters

def test_default_parameters_match_the_template():
    parameters = RecruitmentParameters()
    assert parameters.tau_cr_full == pytest.approx(0.047)
    assert parameters.tau_cr_partial == pytest.approx(0.03)
    assert parameters.recession_stress == pytest.approx(2.5)
    assert parameters.recession_lethal == pytest.approx(5.0)
    assert parameters.inundation_stress == 14
    assert parameters.inundation_lethal == 28


def test_parameters_load_from_the_packaged_workbook():
    parameters = RecruitmentParameters.from_workbook()
    assert "Cottonwood" in parameters.species
    assert parameters.seed_start == (5, 2)
    assert parameters.baseflow_start == (9, 15)
    assert parameters.tau_cr_full == pytest.approx(0.047)


def test_date_in_builds_a_date_for_the_analysis_year():
    parameters = RecruitmentParameters()
    assert parameters.date_in(2021, (5, 2)) == dt.date(2021, 5, 2)


# ------------------------------------------------------------------ flow record

def test_read_flow_series_from_csv(tmp_path):
    path = tmp_path / "flows.csv"
    path.write_text("date,mean daily\n2020-01-01,500\n2020-01-02,600\n", encoding="utf-8")
    series = read_flow_series(str(path))
    assert series == {dt.date(2020, 1, 1): 500.0, dt.date(2020, 1, 2): 600.0}


def test_read_flow_series_skips_unparseable_rows(tmp_path):
    path = tmp_path / "flows.csv"
    path.write_text("date,q\n2020-01-01,500\nnot-a-date,600\n2020-01-03,\n", encoding="utf-8")
    assert list(read_flow_series(str(path))) == [dt.date(2020, 1, 1)]


def test_missing_hydraulics_error_carries_the_condition_report(tmp_path, monkeypatch):
    """The 'no paired rasters' error must tell the user what the folder holds and what
    naming the discovery expects - the raw message alone stumped real users."""
    directory = tmp_path / "01_Conditions" / "empty"
    directory.mkdir(parents=True)
    profile = make_profile()
    raster.write(str(directory / "dem.tif"), np.ones((1, 4)), profile)
    monkeypatch.setenv("RIVERARCHITECT_HOME", str(tmp_path))
    config.set_project_home(str(tmp_path))
    try:
        with pytest.raises(ValueError) as excinfo:
            RecruitmentPotential("empty", season(2020))
        message = str(excinfo.value)
        assert "No depth raster found" in message
        assert "h000001_060.tif" in message      # the accepted decimal form is spelled out
        assert "input_definitions.inp" in message
    finally:
        config.set_project_home(None)


def test_empty_flow_record_is_rejected(floodplain):
    with pytest.raises(ValueError, match="empty"):
        RecruitmentPotential("bench", {})


def test_year_defaults_to_the_last_in_the_record(floodplain):
    analysis = RecruitmentPotential("bench", season(2020))
    assert analysis.year == 2020


# ------------------------------------------------------------- water surface

def test_wle_interpolates_between_modelled_discharges(floodplain):
    analysis = RecruitmentPotential("bench", season(2020))
    low = analysis.wle_for(100.0)
    high = analysis.wle_for(5000.0)
    middle = analysis.wle_for(2550.0)                 # halfway between 100 and 5000
    assert np.all(middle >= low - 1e-9)
    assert np.all(middle <= high + 1e-9)


def test_wle_clamps_outside_the_modelled_range(floodplain):
    analysis = RecruitmentPotential("bench", season(2020))
    assert np.allclose(analysis.wle_for(1.0), analysis.wle_for(100.0), equal_nan=True)
    assert np.allclose(analysis.wle_for(1e9), analysis.wle_for(5000.0), equal_nan=True)


# --------------------------------------------------------------- bed mobility

def theta84_of(u, h, dmean, gravity=9.81):
    """Closed-form regime-aware theta84, written out from the published laws."""
    import math

    d84 = 2.2 * dmean
    chi = h / (2.0 * d84)
    x = h / d84
    rr = 4.416 * x ** 1.904 * (1.0 + (x / 1.283) ** 1.618) ** -1.083
    if chi <= 7.0:
        ratio2 = rr ** 2
        cf = 1.0 / ratio2
    else:
        keu = 5.75 * math.log10(12.2 * chi)
        t = min((chi - 7.0) / 13.0, 1.0)
        w = t * t * (3.0 - 2.0 * t)
        cf = (1.0 - w) / rr ** 2 + w / keu ** 2
    return u ** 2 * cf / (gravity * 1.68 * d84)


def test_q_mobile_is_the_lowest_mobilising_discharge(floodplain):
    """Velocity rises tenfold at the high flow, so the coarse threshold is met there."""
    analysis = RecruitmentPotential("bench", season(2020))
    mobile = analysis.q_mobile(0.047)
    finite = mobile[np.isfinite(mobile)]
    assert finite.size
    assert set(np.unique(finite)).issubset({100.0, 5000.0})


def test_q_mobile_matches_the_closed_form_cell_by_cell(floodplain):
    """Thresholds chosen from the closed-form theta84 pin every cell's answer exactly."""
    analysis = RecruitmentPotential("bench", season(2020), unit="si")

    # Wet cells: at 100 cfs only cell 0 (h=0.5, u=0.3); at 5000 cfs cells 0-2
    # (h=2.5, 1.5, 0.5 at u=3.0). dmean is 0.01 everywhere.
    theta_low_0 = theta84_of(0.3, 0.5, 0.01)
    theta_high = [theta84_of(3.0, h, 0.01) for h in (2.5, 1.5, 0.5)]
    assert theta_low_0 < min(theta_high)  # the fixture keeps the regimes apart

    # A threshold between the low-flow and every high-flow stress: mobilised at 5000 only.
    between = 0.5 * (theta_low_0 + min(theta_high))
    mobile = analysis.q_mobile(between)
    assert mobile[0, 0] == 5000.0 and mobile[0, 1] == 5000.0 and mobile[0, 2] == 5000.0
    assert not np.isfinite(mobile[0, 3])

    # A threshold below the low-flow stress: cell 0 is already mobile at 100.
    analysis2 = RecruitmentPotential("bench", season(2020), unit="si")
    mobile = analysis2.q_mobile(theta_low_0 * 0.5)
    assert mobile[0, 0] == 100.0
    assert mobile[0, 1] == 5000.0 and mobile[0, 2] == 5000.0
    assert not np.isfinite(mobile[0, 3])


def test_shields_stress_matches_the_closed_form(floodplain):
    analysis = RecruitmentPotential("bench", season(2020), unit="si")
    theta = analysis.shields_stress(np.array([2.5, 0.5]), np.array([3.0, 0.3]),
                                    np.array([0.01, 0.01]))
    assert theta[0] == pytest.approx(theta84_of(3.0, 2.5, 0.01), rel=1e-9)
    assert theta[1] == pytest.approx(theta84_of(0.3, 0.5, 0.01), rel=1e-9)


def test_a_threshold_nothing_reaches_gives_all_nodata(floodplain):
    analysis = RecruitmentPotential("bench", season(2020))
    mobile = analysis.q_mobile(1e9)
    assert not np.isfinite(mobile).any()


# ---------------------------------------------------------------- objectives

def test_scour_survival_is_one_when_no_flow_follows_dispersal(floodplain):
    """Flat summer baseflow cannot mobilise anything, so nothing is uprooted."""
    analysis = RecruitmentPotential("bench", season(2020, winter_peak=5000.0, summer=100.0))
    crop = np.ones(analysis.dem.shape, dtype=bool)
    scour = analysis.scour_survival(crop)
    assert np.nanmax(scour) == pytest.approx(1.0)


def test_bed_preparation_needs_a_flow_in_the_preparation_window(floodplain):
    """A record with no winter peak leaves the bed unprepared."""
    analysis = RecruitmentPotential("bench", season(2020, winter_peak=100.0, summer=100.0))
    crop = np.ones(analysis.dem.shape, dtype=bool)
    bed = analysis.bed_preparation(crop)
    assert np.nanmax(bed) < 1.0


def test_objectives_multiply_so_any_zero_is_fatal(floodplain, tmp_path):
    analysis = RecruitmentPotential("bench", season(2020))
    result = analysis.run(output_dir=str(tmp_path / "out"))
    assert set(result["objectives"]) == {"bed_preparation", "desiccation_survival",
                                         "inundation_survival", "scour_survival"}
    # the combined area can never exceed the most limiting objective
    assert result["recruitment_area"] <= min(result["objectives"].values()) + 1e-9


def test_run_writes_one_raster_per_objective(floodplain, tmp_path):
    import os
    analysis = RecruitmentPotential("bench", season(2020))
    result = analysis.run(output_dir=str(tmp_path / "out"))
    assert "recruitment_potential" in result["rasters"]
    for path in result["rasters"].values():
        assert os.path.isfile(path)


def test_run_writes_the_shear_diagnostics(floodplain, tmp_path):
    """h/ks and regime rasters land beside the objectives, one pair per discharge."""
    import rasterio

    analysis = RecruitmentPotential("bench", season(2020))
    result = analysis.run(output_dir=str(tmp_path / "out"))
    for token in ("000100", "005000"):
        assert "hks%s" % token in result["rasters"]
        assert "regime%s" % token in result["rasters"]
        with rasterio.open(result["rasters"]["regime%s" % token]) as src:
            assert src.dtypes[0] == "uint8"
            assert src.nodata == 0
            codes = src.read(1)
        assert set(np.unique(codes)).issubset({0, 1, 2, 3})
        # the dry bench cell must be invalid, the wet channel cell must not
        assert codes[0, 3] == 0
        assert codes[0, 0] != 0


def test_existing_vegetation_is_excluded(floodplain, tmp_path):
    """Ground that already carries vegetation cannot recruit a new seedling."""
    profile = make_profile(width=4, height=1)
    vegetation = str(tmp_path / "veg.tif")
    raster.write(vegetation, np.array([[1.0, 1.0, np.nan, np.nan]]), profile)

    plain = RecruitmentPotential("bench", season(2020))
    masked = RecruitmentPotential("bench", season(2020), existing_vegetation=vegetation)
    a = plain.run(output_dir=str(tmp_path / "a"))
    b = masked.run(output_dir=str(tmp_path / "b"))
    assert b["crop_area"] <= a["crop_area"]


def test_a_season_outside_the_record_is_rejected(floodplain):
    analysis = RecruitmentPotential("bench", season(2020), year=1990)
    with pytest.raises(ValueError, match="seed dispersal"):
        analysis.crop_area()


# ----------------------------------------------- recession and inundation details

def build(series, floodplain, **kwargs):
    parameters = RecruitmentParameters(**kwargs) if kwargs else None
    return RecruitmentPotential("bench", series, year=2020, parameters=parameters,
                                unit="si")


def test_inundation_counts_the_longest_run_not_the_total(floodplain):
    """Fourteen days under water in one stretch drowns a seedling; scattered days do not.

    The original tracked ``consec_inund_days_max``. Summing every submerged day instead
    condemns a cell that was briefly wet on twenty separate occasions.
    """
    def record(pattern):
        series = {}
        day = dt.date(2019, 10, 1)
        while day <= dt.date(2020, 9, 30):
            series[day] = 100.0
            day += dt.timedelta(days=1)
        for day, discharge in pattern.items():
            series[day] = discharge
        return series

    # 20 submerged days in a single run, and the same 20 spread over 40 days.
    run = {dt.date(2020, 7, 1) + dt.timedelta(days=n): 5000.0 for n in range(20)}
    scattered = {dt.date(2020, 7, 1) + dt.timedelta(days=2 * n): 5000.0
                 for n in range(20)}

    thresholds = {"inundation_stress": 5, "inundation_lethal": 10}
    continuous = build(record(run), floodplain, **thresholds)
    crop = np.ones(continuous.dem.shape, dtype=bool)
    _d, inundation, _m = continuous.recession_and_inundation(crop)

    broken = build(record(scattered), floodplain, **thresholds)
    _d, spread_out, _m = broken.recession_and_inundation(crop)

    # Cells 1 and 2 are the bench: submerged only at 5000 cfs. Twenty days in a row kills
    # them; the same twenty days one at a time does not touch them.
    assert list(inundation[0, 1:3]) == [0.0, 0.0]
    assert list(spread_out[0, 1:3]) == [1.0, 1.0]


def test_recession_days_are_only_counted_where_the_cell_is_dry(floodplain):
    """A submerged seedling is not desiccating, however fast the surface is dropping."""
    series = {}
    day = dt.date(2019, 10, 1)
    while day <= dt.date(2020, 9, 30):
        # a steady, fast drawdown through the whole recession period
        series[day] = 5000.0 if day < dt.date(2020, 6, 21) else 100.0
        day += dt.timedelta(days=1)

    analysis = build(series, floodplain)
    crop = np.ones(analysis.dem.shape, dtype=bool)
    _d, _i, mortality = analysis.recession_and_inundation(crop)
    # the channel cell (index 0) stays under water at 100 cfs, so it accrues no
    # desiccation mortality at all
    assert mortality[0, 0] == pytest.approx(0.0)


def test_inundation_at_exactly_the_lethal_count_is_stressed_not_dead(floodplain):
    """``> lethal`` is fatal, ``>= stress`` is stressful - the original's boundary."""
    series = {}
    day = dt.date(2019, 10, 1)
    while day <= dt.date(2020, 9, 30):
        series[day] = 100.0
        day += dt.timedelta(days=1)
    for n in range(4):
        series[dt.date(2020, 7, 1) + dt.timedelta(days=n)] = 5000.0

    analysis = build(series, floodplain, inundation_stress=2, inundation_lethal=4)
    crop = np.ones(analysis.dem.shape, dtype=bool)
    _d, inundation, _m = analysis.recession_and_inundation(crop)
    # a bench cell submerged for exactly 4 days scores 0.5, not 0
    assert 0.0 not in set(inundation[np.isfinite(inundation)][1:])
