"""Tests for the synthetic valley generator.

The geometry is closed-form, so most of these assert against the formula rather than against
recorded output: a straight valley has sinuosity 1, a symmetric U is symmetric, the channel
slope is the valley slope over the sinuosity, and the regime depth is the Shields relation.
"""

import math

import numpy as np
import pytest

from riverarchitect.riverbuilder import (CROSS_SECTIONS, RiverBuilder, RiverBuilderInput,
                                         UserFunction)


def straight(**overrides):
    """A straight reach with an explicit depth - the simplest case with a known answer."""
    parameters = dict(name="test", length=100.0, x_resolution=100, xs_points=11,
                      valley_slope=0.01, bankfull_width=10.0, bankfull_width_min=5.0,
                      bankfull_depth=2.0, d50=0.01, datum=0.0)
    parameters.update(overrides)
    return RiverBuilderInput(**parameters)


# ------------------------------------------------------------------- user functions

def test_sin_and_cos_are_evaluated_against_the_radian_station():
    radians = np.array([0.0, np.pi / 2, np.pi])
    metres = np.zeros(3)
    index = np.arange(3)
    assert np.allclose(UserFunction("SIN", [2, 1, 0])(radians, metres, index),
                       2 * np.sin(radians))
    assert np.allclose(UserFunction("COS", [2, 1, 0])(radians, metres, index),
                       2 * np.cos(radians))


def test_line_is_evaluated_against_the_station_in_length_units():
    """LINE is the one form that works in metres, not radians."""
    metres = np.array([0.0, 10.0, 20.0])
    result = UserFunction("LINE", [0.5, 3.0])(np.zeros(3), metres, np.arange(3))
    assert np.allclose(result, 0.5 * metres + 3.0)


def test_a_phase_shift_may_be_written_in_terms_of_pi():
    function = UserFunction.parse("SIN(1, 1, PI/2)")
    assert function.arguments[2] == pytest.approx(math.pi / 2)
    assert np.allclose(function(np.zeros(1), np.zeros(1), np.zeros(1)), 1.0)


def test_sin_sq_is_parsed_before_sin():
    """Longest name first, or SIN_SQ is read as SIN and the square is lost."""
    assert UserFunction.parse("SIN_SQ(1, 1, 0)").kind == "SIN_SQ"


def test_perlin_noise_is_bounded_and_reproducible():
    index = np.arange(200.0)
    rng = np.random.default_rng(3)
    a = UserFunction("PERL", [2.0, 20.0])(index, index, index, noise=rng)
    b = UserFunction("PERL", [2.0, 20.0])(index, index, index,
                                          noise=np.random.default_rng(3))
    assert np.abs(a).max() <= 2.0
    assert np.allclose(a, b)


def test_an_unknown_function_is_refused():
    with pytest.raises(ValueError, match="unknown function"):
        UserFunction.parse("WOBBLE(1, 2, 3)")


# -------------------------------------------------------------------- the geometry

def test_a_straight_valley_has_sinuosity_one():
    geometry = RiverBuilder(straight()).build()
    assert geometry["sinuosity"] == pytest.approx(1.0, rel=1e-6)
    assert np.allclose(geometry["centreline"], 0.0)


def test_a_meander_makes_the_channel_longer_than_the_valley():
    geometry = RiverBuilder(straight(meander=[UserFunction("SIN", [10, 2, 0])])).build()
    assert geometry["sinuosity"] > 1.0
    assert geometry["arc_length"][-1] > geometry["x"][-1]


def test_channel_slope_is_the_valley_slope_over_the_sinuosity():
    """The channel falls the same height over a longer path, so it is gentler."""
    geometry = RiverBuilder(straight(meander=[UserFunction("SIN", [10, 2, 0])])).build()
    assert geometry["channel_slope"] == pytest.approx(0.01 / geometry["sinuosity"],
                                                      rel=1e-6)


def test_the_regime_relation_sets_the_depth_when_none_is_given():
    builder = RiverBuilder(straight(bankfull_depth=0.0, d50=0.001, tau_cr=0.047))
    geometry = builder.build()
    expected = 165.0 * 0.001 * 0.047 / geometry["channel_slope"]
    assert geometry["depth"] == pytest.approx(expected)


def test_an_implausible_regime_depth_is_reported():
    """Deeper than the channel is wide is not a river; the original said nothing."""
    builder = RiverBuilder(straight(bankfull_depth=0.0, d50=0.1, valley_slope=0.0001))
    builder.build()
    assert builder.error


def test_bankfull_width_follows_its_function_and_respects_the_minimum():
    geometry = RiverBuilder(straight(
        width_function=[UserFunction("SIN", [0.9, 2, 0])],
        bankfull_width=10.0, bankfull_width_min=6.0)).build()
    assert geometry["bankfull_width"].max() <= 10.0 * 1.9 + 1e-9
    assert geometry["bankfull_width"].min() >= 6.0


# ---------------------------------------------------------------- cross-sections

def test_the_symmetric_section_is_symmetric_and_deepest_in_the_middle():
    geometry = RiverBuilder(straight(xs_shape="SU", xs_points=11)).build()
    section = geometry["xs_z"][0]
    assert np.allclose(section, section[::-1])
    assert section.argmin() == len(section) // 2
    # the edges sit at the bank top, the middle a bankfull depth below it
    assert section[0] == pytest.approx(geometry["top_of_bank"][0])
    assert section.min() == pytest.approx(geometry["top_of_bank"][0]
                                          - geometry["bankfull_depth"][0])


def test_the_bed_is_never_above_the_bank_top():
    for shape in CROSS_SECTIONS:
        geometry = RiverBuilder(straight(
            xs_shape=shape, trapezoid_base=4,
            curvature=[UserFunction("SIN", [0.01, 2, 0])])).build()
        assert np.all(geometry["xs_z"] <= geometry["top_of_bank"][:, None] + 1e-9), shape


def test_an_even_number_of_section_points_leaves_out_the_centre():
    """So the thalweg is not sampled twice, as in the original."""
    odd = RiverBuilder._cross_section_offsets(11)
    even = RiverBuilder._cross_section_offsets(10)
    assert 0.0 in odd and 0.0 not in even
    assert odd.min() == -1.0 and odd.max() == 1.0


def test_an_unknown_cross_section_is_refused():
    with pytest.raises(ValueError, match="cross-sectional shape"):
        RiverBuilder(straight(xs_shape="ZZ"))


def test_a_minimum_width_above_the_base_width_is_refused():
    with pytest.raises(ValueError, match="minimum bankfull width"):
        RiverBuilder(straight(bankfull_width=5.0, bankfull_width_min=10.0))


# ------------------------------------------------------------------ benches, output

def test_floodplain_and_terrace_add_points_outside_the_channel():
    plain = RiverBuilder(straight()).build()
    benched = RiverBuilder(straight(floodplain_width=20.0, terrace_width=10.0,
                                    floodplain_outer_height=1.0,
                                    terrace_outer_height=2.0)).build()
    assert plain["bench_z"].size == 0
    assert benched["bench_z"].size > 0
    # the terrace sits above the floodplain, which sits above the bank top
    assert benched["bench_z"].max() > benched["top_of_bank"].max()


def test_the_dem_covers_the_valley_and_holds_its_elevations(tmp_path):
    pytest.importorskip("rasterio")
    from riverarchitect import raster

    builder = RiverBuilder(straight(floodplain_width=20.0,
                                    meander=[UserFunction("SIN", [5, 2, 0])]))
    result = builder.run(output_dir=str(tmp_path), cell_size=1.0)

    dem, profile = raster.read(result["dem_raster"])
    assert np.isfinite(dem).any()
    low, high = result["elevation_range"]
    assert low < high
    # every mapped elevation lies between the thalweg and the highest bench
    points = builder.point_cloud()
    assert low >= points[:, 2].min() - 1e-6
    assert high <= points[:, 2].max() + 1e-6


def test_run_writes_the_dem_hillshade_points_and_parameters(tmp_path):
    pytest.importorskip("rasterio")
    import os

    result = RiverBuilder(straight()).run(output_dir=str(tmp_path))
    for key in ("dem_raster", "hillshade_raster", "points_csv", "parameters_file"):
        assert os.path.isfile(result[key]), key


# ------------------------------------------------------------------- the file format

def test_an_input_file_round_trips(tmp_path):
    original = straight(meander=[UserFunction("SIN", [10, 2, 0])],
                        thalweg=[UserFunction("COS", [0.5, 3, 0])],
                        xs_shape="AU", floodplain_width=15.0)
    path = tmp_path / "input.txt"
    original.write(str(path))

    read_back = RiverBuilderInput.read(str(path))
    assert read_back.length == original.length
    assert read_back.xs_shape == "AU"
    assert read_back.floodplain_width == pytest.approx(15.0)
    assert [f.kind for f in read_back.meander] == ["SIN"]
    assert read_back.meander[0].arguments[:3] == pytest.approx([10, 2, 0])
    assert [f.kind for f in read_back.thalweg] == ["COS"]


def test_the_original_parameter_names_are_understood(tmp_path):
    """An existing RiverBuilder input must run unchanged."""
    path = tmp_path / "legacy.txt"
    path.write_text(
        "# a comment\n"
        "SIN1=SIN(0, 1, 0)\n"
        "Datum=65.7\n"
        "Length=350\n"
        "X Resolution=100\n"
        "Channel XS Points=25\n"
        "Valley Slope (Sv)=0.005\n"
        "Bankfull Width (Wbf)=20\n"
        "Bankfull Depth (Hbf, A)=7\n"
        "Median Sediment Size (D50)=0.0965\n"
        "Cross-Sectional Shape=SU\n"
        "Meandering Centerline Function=SIN1\n", encoding="utf-8")

    entry = RiverBuilderInput.read(str(path))
    assert entry.datum == pytest.approx(65.7)
    assert entry.length == pytest.approx(350.0)
    assert entry.xs_points == 25
    assert entry.xs_shape == "SU"
    assert len(entry.meander) == 1
    RiverBuilder(entry).build()          # and it builds


def test_several_functions_on_one_parameter_are_summed(tmp_path):
    path = tmp_path / "sum.txt"
    path.write_text("SIN1=SIN(5, 1, 0)\nSIN2=SIN(3, 4, 0)\n"
                    "Length=100\nX Resolution=50\n"
                    "Meandering Centerline Function=SIN1, SIN2\n", encoding="utf-8")
    entry = RiverBuilderInput.read(str(path))
    assert len(entry.meander) == 2

    geometry = RiverBuilder(entry).build()
    radians = geometry["radians"]
    assert np.allclose(geometry["centreline"],
                       5 * np.sin(radians) + 3 * np.sin(4 * radians))
