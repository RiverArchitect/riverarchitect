"""Tests for the pool-riffle designer.

The hydraulics are checked against closed-form answers wherever the maths allows one - a
rectangular channel has an analytic Manning discharge, the Shields criterion is one line of
algebra, and the pool spacing is a mean. What cannot be done analytically is checked for
the property that matters instead: that the design reaches its target, satisfies the
velocity-reversal criterion, and is self-consistent when read back through the hydraulics
it came from.

The reversal discharge, reversal depth, pool spacing and residual depth are also pinned to
the values the 1.x design script produced on its own sample channel. The pool and riffle
widths deliberately are not - see the module docstring.
"""

import math

import pytest

from riverarchitect import config
from riverarchitect.poolriffle import (
    MAX_POOL_RIFFLE_SLOPE, THOMPSON_FACTORS, base_width, critical_depth_for_transport,
    design_pool_riffle, discharge_for_transport, format_design, manning_discharge,
    normal_depth, pool_spacing, pool_spacing_bounds, roughness_meyer_peter_mueller,
    roughness_rickenmann_recking, roughness_strickler)

#: The channel the 1.x driver script shipped: Upper Gilt Edge Bar, in SI.
SAMPLE = dict(d50=0.0914, slope=0.004, base_width=24.0, target_residual_depth=0.915,
              bank_slope=2.58)


# ------------------------------------------------------------------ trapezoid hydraulics

def test_manning_discharge_of_a_rectangle_is_the_closed_form():
    """With m = 0 the trapezoid is a rectangle and Manning has an exact answer."""
    h, w, n, s = 2.0, 10.0, 0.03, 0.001
    area = w * h
    perimeter = w + 2 * h
    expected = area * (area / perimeter) ** (2 / 3) * math.sqrt(s) / n
    assert manning_discharge(h, 0.0, n, w, s) == pytest.approx(expected, rel=1e-12)


def test_discharge_grows_with_depth_width_and_slope():
    """Monotonicity is what makes the bracketing solver safe; assert it rather than assume."""
    base = manning_discharge(1.5, 2.0, 0.03, 10.0, 0.002)
    assert manning_discharge(1.6, 2.0, 0.03, 10.0, 0.002) > base
    assert manning_discharge(1.5, 2.0, 0.03, 11.0, 0.002) > base
    assert manning_discharge(1.5, 2.0, 0.03, 10.0, 0.003) > base
    assert manning_discharge(1.5, 2.0, 0.02, 10.0, 0.002) > base      # smoother = faster


@pytest.mark.parametrize("bank_slope", [0.0, 1.0, 2.58, 5.0])
@pytest.mark.parametrize("width", [3.0, 24.0, 120.0])
def test_normal_depth_inverts_manning_discharge(bank_slope, width):
    """normal_depth and manning_discharge must be inverses, on any trapezoid."""
    n, s, q = 0.032, 0.004, 90.0
    depth = normal_depth(q, bank_slope, n, width, s)
    assert manning_discharge(depth, bank_slope, n, width, s) == pytest.approx(q, rel=1e-6)


def test_base_width_inverts_manning_discharge():
    """The same round trip, solving for width instead of depth."""
    n, s, q, h, m = 0.032, 0.004, 90.0, 1.8, 2.58
    width = base_width(q, h, m, n, s)
    assert manning_discharge(h, m, n, width, s) == pytest.approx(q, rel=1e-6)


def test_the_solver_reports_an_impossible_target_rather_than_looping():
    """A discharge no depth can carry has no bracket; that must raise, not spin."""
    with pytest.raises(ValueError):
        normal_depth(float("inf"), 2.0, 0.03, 10.0, 0.001)


# ------------------------------------------------------------------- Shields criterion

def test_critical_depth_is_the_shields_criterion_rearranged():
    """h_cr = taux_cr (s-1) D50 / S, exactly."""
    d50, slope, taux, s = 0.05, 0.005, 0.047, 2.68
    assert critical_depth_for_transport(d50, slope, taux, s) == pytest.approx(
        taux * (s - 1) * d50 / slope, rel=1e-12)


def test_critical_depth_falls_as_the_channel_steepens():
    """A steeper bed mobilises the same grain at a shallower depth."""
    shallow = critical_depth_for_transport(0.05, 0.01)
    steep_enough = critical_depth_for_transport(0.05, 0.001)
    assert shallow < steep_enough


def test_discharge_for_transport_agrees_with_its_own_depth():
    """The returned discharge must be the Manning discharge at the returned depth."""
    q, h = discharge_for_transport(0.0914, 0.004, 2.58, 0.032, 24.0)
    assert h == pytest.approx(critical_depth_for_transport(0.0914, 0.004), rel=1e-12)
    assert q == pytest.approx(manning_discharge(h, 2.58, 0.032, 24.0, 0.004), rel=1e-12)


# ---------------------------------------------------------------------- roughness laws

def test_roughness_estimates_are_the_published_formulae():
    assert roughness_strickler(0.0914) == pytest.approx(0.0914 ** (1 / 6) / 21.1)
    assert roughness_meyer_peter_mueller(0.25) == pytest.approx(0.25 ** (1 / 6) / 26.0)


def test_rickenmann_recking_roughness_falls_with_submergence():
    """Deeper flow over the same bed is relatively smoother."""
    d84 = 0.2
    assert roughness_rickenmann_recking(0.5, d84) > roughness_rickenmann_recking(5.0, d84)


# ----------------------------------------------------------------------- pool spacing

def test_pool_spacing_is_the_mean_of_the_thompson_factors():
    """The original drew ten million lognormal samples to compute this multiplication.

    The lognormal was constructed to have exactly this mean, so the Monte Carlo converged
    to it - slowly, and to a different value each run because the draw was unseeded.
    """
    width = 33.31
    expected = width * sum(THOMPSON_FACTORS) / len(THOMPSON_FACTORS)
    assert pool_spacing(width) == pytest.approx(expected, rel=1e-12)


def test_pool_spacing_bounds_bracket_the_expected_value():
    low, high = pool_spacing_bounds(33.31)
    assert low < pool_spacing(33.31) < high
    assert low == pytest.approx(33.31 * min(THOMPSON_FACTORS))
    assert high == pytest.approx(33.31 * max(THOMPSON_FACTORS))


# --------------------------------------------------------------------------- the design

def test_the_design_reaches_its_target_and_reverses():
    design = design_pool_riffle(**SAMPLE)
    assert design.converged
    assert design.caamano_satisfied
    assert design.residual_depth == pytest.approx(SAMPLE["target_residual_depth"], rel=1e-3)


def test_the_reversal_flow_matches_the_1x_design_script():
    """Pinned to what Tools/morphology_designer.py produced on its own sample channel."""
    design = design_pool_riffle(**SAMPLE)
    assert design.reversal_discharge == pytest.approx(135.9732, rel=1e-4)
    assert design.normal_depth == pytest.approx(1.8042, rel=1e-4)
    assert design.pool_spacing == pytest.approx(166.4869, rel=1e-3)
    assert design.pool_riffle_spacing == pytest.approx(design.pool_spacing / 2)


def test_the_pool_is_narrower_and_deeper_than_the_riffle():
    """The whole point of the geometry; if this inverts, the sequence is not a sequence."""
    design = design_pool_riffle(**SAMPLE)
    assert design.pool_width < SAMPLE["base_width"] < design.riffle_width
    assert design.pool_depth > design.riffle_depth
    # widths move in equal and opposite steps, so they straddle the original symmetrically
    assert (design.pool_width + design.riffle_width) == pytest.approx(
        2 * SAMPLE["base_width"], abs=1e-6)


def test_the_pool_carries_the_reversal_discharge_at_its_reported_depth():
    """Read the design back through the hydraulics it came from: it must be consistent."""
    design = design_pool_riffle(**SAMPLE)
    n = roughness_strickler(SAMPLE["d50"])
    assert manning_discharge(design.pool_depth, design.pool_bank_slope, n,
                             design.pool_width, SAMPLE["slope"]) == pytest.approx(
        design.reversal_discharge, rel=1e-3)


def test_the_riffle_carries_the_same_area_as_the_pool():
    """The riffle depth follows from equal cross-sectional area, which fixes the geometry."""
    design = design_pool_riffle(**SAMPLE)
    pool_area = design.pool_depth * (design.pool_width
                                     + design.pool_bank_slope * design.pool_depth)
    riffle_area = design.riffle_depth * (design.riffle_width
                                         + design.riffle_bank_slope * design.riffle_depth)
    assert riffle_area == pytest.approx(pool_area, rel=1e-3)


def test_the_caamano_criterion_is_evaluated_not_assumed():
    """B_r/B_p - 1 > D_z/h_r is what makes the sequence self-maintaining."""
    design = design_pool_riffle(**SAMPLE)
    left = design.riffle_width / design.pool_width - 1.0
    right = design.residual_depth / design.riffle_depth
    assert (left > right) is design.caamano_satisfied
    assert design.caamano_satisfied


def test_a_deeper_pool_needs_a_greater_width_contrast():
    shallow = design_pool_riffle(**dict(SAMPLE, target_residual_depth=0.3))
    deep = design_pool_riffle(**dict(SAMPLE, target_residual_depth=1.5))
    assert deep.pool_width < shallow.pool_width
    assert deep.riffle_width > shallow.riffle_width


def test_an_unreachable_target_says_so_instead_of_returning_a_number():
    """A pool deeper than the channel can produce must not look like a design."""
    design = design_pool_riffle(**dict(SAMPLE, target_residual_depth=50.0))
    assert not design.converged
    assert "NOT CONVERGED" in format_design(design)


# --------------------------------------------------------------------------------- units

def test_us_customary_is_the_same_channel_in_different_numbers():
    """Converting the inputs to feet must convert the outputs to feet and nothing else."""
    si = design_pool_riffle(**SAMPLE)
    us = design_pool_riffle(
        d50=SAMPLE["d50"] / config.FT2M, slope=SAMPLE["slope"],
        base_width=SAMPLE["base_width"] / config.FT2M,
        target_residual_depth=SAMPLE["target_residual_depth"] / config.FT2M,
        bank_slope=SAMPLE["bank_slope"],
        roughness=roughness_strickler(SAMPLE["d50"]), unit="us")

    assert us.pool_width * config.FT2M == pytest.approx(si.pool_width, rel=1e-3)
    assert us.riffle_width * config.FT2M == pytest.approx(si.riffle_width, rel=1e-3)
    assert us.residual_depth * config.FT2M == pytest.approx(si.residual_depth, rel=1e-3)
    assert us.reversal_discharge * config.CFS2CMS == pytest.approx(
        si.reversal_discharge, rel=1e-3)
    # dimensionless quantities are not converted
    assert us.pool_bank_slope == pytest.approx(si.pool_bank_slope)


def test_the_unit_travels_with_the_result_and_into_the_report():
    design = design_pool_riffle(**dict(SAMPLE, unit="si"))
    assert design.unit == "si"
    assert " m" in format_design(design)
    assert " ft" not in format_design(design)


# ----------------------------------------------------------------------------- refusals

@pytest.mark.parametrize("bad", [
    dict(target_residual_depth=0.0),
    dict(target_residual_depth=-1.0),
    dict(d50=0.0),
    dict(base_width=-5.0),
    dict(slope=0.0),
])
def test_unphysical_inputs_raise(bad):
    with pytest.raises(ValueError):
        design_pool_riffle(**dict(SAMPLE, **bad))


def test_an_unknown_unit_raises():
    with pytest.raises(ValueError):
        design_pool_riffle(**dict(SAMPLE, unit="imperial"))


def test_a_steep_channel_warns_that_it_is_the_wrong_bed_form(caplog):
    """Pool-riffle sequences do not occur above about 2 %; say so rather than sizing one."""
    with caplog.at_level("WARNING", logger="riverarchitect"):
        design_pool_riffle(**dict(SAMPLE, slope=MAX_POOL_RIFFLE_SLOPE + 0.01,
                                  target_residual_depth=0.2))
    assert "bed form" in caplog.text


# ------------------------------------------------------------------------- command line

def test_the_command_line_runs_every_roughness_estimate(tmp_path, capsys):
    from riverarchitect.tools.pool_riffle import main

    csv_path = tmp_path / "pr.csv"
    assert main(["--d50", "0.0914", "--slope", "0.004", "--width", "24",
                 "--pool-depth", "0.915", "--roughness", "all", "--quiet",
                 "--csv", str(csv_path)]) == 0
    out = capsys.readouterr().out
    for name in ("strickler", "meyer-peter-mueller", "rickenmann-recking"):
        assert name in out
    rows = csv_path.read_text().strip().splitlines()
    assert len(rows) == 4                      # header plus one row per estimate
    assert "reversal_discharge" in rows[0]


def test_the_command_line_accepts_an_explicit_roughness(capsys):
    from riverarchitect.tools.pool_riffle import main

    assert main(["--d50", "0.0914", "--slope", "0.004", "--width", "24",
                 "--pool-depth", "0.915", "--roughness", "0.04", "--quiet"]) == 0
    assert "n = 0.0400" in capsys.readouterr().out
