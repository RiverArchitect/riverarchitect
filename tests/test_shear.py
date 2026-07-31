"""Analytical tests for the regime-aware Shields stress.

Every expected value is computed in closed form from the published resistance laws, never
recorded from the implementation's own output.
"""

import math

import numpy as np
import pytest

from riverarchitect import shear


def keulegan_theta(u, h, dmean, gravity=9.81):
    """Closed-form theta84 in the pure Keulegan regime, from first principles."""
    d84 = 2.2 * dmean
    chi = h / (2.0 * d84)
    ustar = u / (5.75 * math.log10(12.2 * chi))
    return ustar ** 2 / (gravity * (shear.RHO_RATIO - 1.0) * d84)


def rickenmann_recking_theta(u, h, dmean, gravity=9.81):
    """Closed-form theta84 in the pure Rickenmann-Recking regime."""
    d84 = 2.2 * dmean
    x = h / d84
    ratio = 4.416 * x ** 1.904 * (1.0 + (x / 1.283) ** 1.618) ** -1.083
    return (u / ratio) ** 2 / (gravity * (shear.RHO_RATIO - 1.0) * d84)


# --------------------------------------------------------------------- pure regimes


def test_deep_water_reproduces_keulegan():
    # dmean = 0.01 m -> d84 = 0.022, ks = 0.044; h = 2.2 m -> h/ks = 50 >= 20.
    u, h, dmean = 1.5, 2.2, 0.01
    result = shear.calculate_taux(np.array([u]), np.array([h]),
                                  shear.d84_of(np.array([dmean])))
    assert result.regime[0] == 3
    assert result.theta84[0] == pytest.approx(keulegan_theta(u, h, dmean), rel=1e-12)
    assert result.h_over_ks[0] == pytest.approx(50.0)


def test_deep_water_ustar2_matches_legacy_expression():
    # In the deep-water limit ustar2 must equal the original arcpy expression
    # Square(u / (5.75 * Log10(12.2 * h / (2 * 2.2 * dmean)))) exactly.
    u, h, dmean = 2.0, 3.0, 0.01
    legacy = (u / (5.75 * math.log10(12.2 * h / (2 * 2.2 * dmean)))) ** 2
    result = shear.calculate_taux(np.array([u]), np.array([h]),
                                  shear.d84_of(np.array([dmean])))
    assert result.regime[0] == 3
    assert result.ustar2[0] == pytest.approx(legacy, rel=1e-12)


def test_shallow_water_reproduces_rickenmann_recking():
    # dmean = 0.05 m -> d84 = 0.11, ks = 0.22; h = 0.5 m -> h/ks = 2.27 <= 7.
    u, h, dmean = 0.8, 0.5, 0.05
    result = shear.calculate_taux(np.array([u]), np.array([h]),
                                  shear.d84_of(np.array([dmean])))
    assert result.regime[0] == 1
    assert result.theta84[0] == pytest.approx(rickenmann_recking_theta(u, h, dmean),
                                              rel=1e-12)


def test_us_customary_gravity_scales_theta():
    # theta is dimensionless: same numbers in ft with g in ft/s**2 divide by g_us/g_si.
    u, h, dmean = 1.5, 2.2, 0.01
    si = shear.calculate_taux(np.array([u]), np.array([h]),
                              shear.d84_of(np.array([dmean])), gravity=9.81)
    us = shear.calculate_taux(np.array([u]), np.array([h]),
                              shear.d84_of(np.array([dmean])), gravity=32.174)
    assert us.theta84[0] == pytest.approx(si.theta84[0] * 9.81 / 32.174, rel=1e-12)
    assert us.ustar2[0] == si.ustar2[0]


# ------------------------------------------------------------------------- blending


def test_blend_is_continuous_at_both_limits():
    dmean = 0.05
    ks = shear.KS_FACTOR * shear.D84_FACTOR * dmean
    u = 1.0
    eps = 1e-9
    for chi_limit, closed_form in ((shear.LOW_LIMIT, rickenmann_recking_theta),
                                   (shear.HIGH_LIMIT, keulegan_theta)):
        h = chi_limit * ks
        inside = shear.calculate_taux(np.array([u]), np.array([h * (1 + eps)]),
                                      shear.d84_of(np.array([dmean])))
        assert inside.theta84[0] == pytest.approx(closed_form(u, h, dmean), rel=1e-6)


def test_blend_has_no_seam():
    # theta84 as a function of depth must be monotone through the blend zone for this
    # configuration - a hard equation switch would produce a jump.
    dmean = 0.05
    ks = shear.KS_FACTOR * shear.D84_FACTOR * dmean
    h = np.linspace(5.0 * ks, 25.0 * ks, 2001)
    u = np.full_like(h, 1.0)
    result = shear.calculate_taux(u, h, shear.d84_of(np.full_like(h, dmean)))
    theta = result.theta84
    assert np.all(np.isfinite(theta))
    assert np.all(np.diff(theta) < 0)  # deeper water, same velocity -> less stress
    assert set(np.unique(result.regime)) == {1, 2, 3}


def test_smoothstep_weight_endpoints_and_monotonicity():
    chi = np.linspace(0.0, 30.0, 301)
    w = shear.smoothstep_weight(chi)
    assert np.all(w[chi <= shear.LOW_LIMIT] == 0.0)
    assert np.all(w[chi >= shear.HIGH_LIMIT] == 1.0)
    assert np.all(np.diff(w) >= 0.0)
    with pytest.raises(ValueError):
        shear.smoothstep_weight(chi, low_limit=5.0, high_limit=5.0)


def test_blended_cell_matches_hand_computed_mixture():
    # One cell in the middle of the blend zone, checked against the Cf mixture formula.
    dmean = 0.05
    d84 = 2.2 * dmean
    ks = 2.0 * d84
    chi = 13.5
    h = chi * ks
    u = 1.0
    x = h / d84
    rr = 4.416 * x ** 1.904 * (1.0 + (x / 1.283) ** 1.618) ** -1.083
    keu = 5.75 * math.log10(12.2 * chi)
    t = (chi - 7.0) / (20.0 - 7.0)
    w = t * t * (3 - 2 * t)
    cf = (1 - w) / rr ** 2 + w / keu ** 2
    expected = u ** 2 * cf / (9.81 * (shear.RHO_RATIO - 1.0) * d84)
    result = shear.calculate_taux(np.array([u]), np.array([h]),
                                  shear.d84_of(np.array([dmean])))
    assert result.regime[0] == 2
    assert result.theta84[0] == pytest.approx(expected, rel=1e-12)


# ------------------------------------------------------------------------- masking


def test_invalid_inputs_yield_nan_and_regime_zero():
    u = np.array([np.nan, -0.1, 1.0, 1.0, 1.0])
    h = np.array([1.0, 1.0, 0.0, 1.0, 1.0])
    d84 = np.array([0.02, 0.02, 0.02, -0.02, np.nan])
    result = shear.calculate_taux(u, h, d84)
    assert np.all(np.isnan(result.theta84))
    assert np.all(np.isnan(result.ustar2))
    assert np.all(np.isnan(result.h_over_ks))
    assert np.all(result.regime == 0)


def test_all_nan_input_returns_quietly():
    nan = np.full((3, 3), np.nan)
    result = shear.calculate_taux(nan, nan, nan)
    assert np.all(np.isnan(result.theta84))
    assert np.all(result.regime == 0)


def test_zero_velocity_is_valid_and_gives_zero_stress():
    result = shear.calculate_taux(np.array([0.0]), np.array([2.2]),
                                  shear.d84_of(np.array([0.01])))
    assert result.theta84[0] == 0.0
    assert result.regime[0] == 3


# ---------------------------------------------------------------------- parameters


def test_parameter_validation():
    one = np.array([1.0])
    for kwargs in ({"gravity": 0.0}, {"density_ratio": 1.0}, {"ks_factor": 0.0},
                   {"low_limit": 20.0, "high_limit": 7.0}):
        with pytest.raises(ValueError):
            shear.calculate_taux(one, one, one, **kwargs)


def test_d84_of_kinds():
    grain = np.array([0.01])
    assert shear.d84_of(grain, "dmean")[0] == pytest.approx(0.022)
    assert shear.d84_of(grain, "d50")[0] == pytest.approx(0.022)
    assert shear.d84_of(grain, "d84")[0] == pytest.approx(0.01)
    with pytest.raises(ValueError):
        shear.d84_of(grain, "d16")
    with pytest.raises(ValueError):
        shear.d84_of(grain, "dmean", factor=0.0)


def test_regime_summary_counts():
    regime = np.array([0, 1, 1, 2, 3, 3, 3], dtype=np.uint8)
    assert shear.regime_summary(regime) == {"invalid": 1, "Rickenmann-Recking": 2,
                                            "blended": 1, "Keulegan-Einstein": 3}
