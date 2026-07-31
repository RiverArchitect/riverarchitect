"""Regime-aware dimensionless bed shear stress (Shields stress).

Replaces the Keulegan-only expression of the original River Architect
(``LifespanDesign/cLifespanDesignAnalysis.analyse_taux``)::

    ustar2 = Square(u / (5.75 * Log10(12.2 * h / (2 * 2.2 * dmean))))
    taux = ustar2 / ((s - 1) * g * dmean)

That expression assumes the Keulegan-Einstein logarithmic resistance law everywhere,
including shallow coarse-bed cells where the roughness layer occupies most of the water
column. There the argument of the logarithm approaches one, the computed shear velocity
blows up, and the resulting Shields stress is meaningless - shallow riffle margins are
exactly where lifespan and recruitment analyses look. This module therefore:

* uses the Rickenmann-Recking (2011) coarse-bed resistance relation at low relative
  submergence (``h/ks <= 7``),
* uses the Keulegan-Einstein relation where the flow is deep (``h/ks >= 20``),
* blends the shear coefficient ``Cf = (u*/U)**2`` smoothly between the two limits, so
  there is no artificial seam in the output where the closure switches,
* references the Shields stress to ``D84`` (``theta84 = ustar2 / (g * (s - 1) * D84)``),
  consistent with Schwindt et al. (2019), rather than to the mean grain size,
* masks NoData, dry cells, negative velocities and nonpositive grain sizes, and reports
  a per-cell regime code so users can see which closure applied where.

``ks = 2 * D84`` and ``D84 = 2.2 * dmean`` reproduce the roughness height of the original
expression (``2 * 2.2 * dmean``); with those defaults the deep-water limit of this module
is exactly the legacy ``ustar2``, and ``theta84`` is the legacy value divided by 2.2.

The blend is a transparent engineering interpolation between two published resistance
equations; the blend itself is not a separately calibrated law. Pass a very large
``high_limit`` to use Rickenmann-Recking over the whole range instead.

This module is pure numpy: no arcpy, no GDAL, testable anywhere. NoData travels as
``numpy.nan``, as everywhere in this package; invalid cells come back as NaN with regime
code 0.
"""

from typing import NamedTuple

import numpy as np

__all__ = ["G_SI", "RHO_RATIO", "D84_FACTOR", "KS_FACTOR", "LOW_LIMIT", "HIGH_LIMIT",
           "REGIME_LABELS", "ShearResult", "gravity_of", "rickenmann_recking_velocity_ratio",
           "keulegan_velocity_ratio", "smoothstep_weight", "d84_of", "calculate_taux",
           "regime_summary"]

#: Gravitational acceleration in m/s^2.
G_SI = 9.81

#: Relative grain density (ratio of sediment and water density).
RHO_RATIO = 2.68

#: Default multiplier estimating ``D84`` from a mean grain size raster.
D84_FACTOR = 2.2

#: Equivalent roughness height as a multiple of ``D84`` (``ks = KS_FACTOR * D84``).
KS_FACTOR = 2.0

#: Pure Rickenmann-Recking at or below this relative submergence ``h/ks``.
LOW_LIMIT = 7.0

#: Pure Keulegan-Einstein at or above this relative submergence ``h/ks``.
HIGH_LIMIT = 20.0

#: Meaning of the codes in :attr:`ShearResult.regime`.
REGIME_LABELS = {0: "invalid", 1: "Rickenmann-Recking", 2: "blended",
                 3: "Keulegan-Einstein"}


class ShearResult(NamedTuple):
    """What :func:`calculate_taux` returns, cell by cell.

    Attributes:
        ustar2 (numpy.ndarray): squared shear velocity ``u***2`` [length**2/time**2].
        theta84 (numpy.ndarray): dimensionless Shields stress referenced to ``D84``.
        h_over_ks (numpy.ndarray): relative submergence ``h/ks``.
        regime (numpy.ndarray): uint8 code per :data:`REGIME_LABELS`; 0 where invalid.
    """

    ustar2: np.ndarray
    theta84: np.ndarray
    h_over_ks: np.ndarray
    regime: np.ndarray


def gravity_of(unit):
    """Gravitational acceleration in the length unit of ``unit``.

    Args:
        unit (str): ``"us"`` (ft/s^2) or ``"si"`` (m/s^2).

    Returns:
        float: the value to pass as ``gravity`` to :func:`calculate_taux`.
    """
    from . import config

    return G_SI / config.FT2M if str(unit).lower() == "us" else G_SI


def rickenmann_recking_velocity_ratio(relative_depth):
    """``U/u*`` from Rickenmann and Recking (2011), for coarse shallow beds.

    Args:
        relative_depth (numpy.ndarray): ``h / D84``.

    Returns:
        numpy.ndarray: ``U/u* = 4.416 * x**1.904 * (1 + (x / 1.283)**1.618)**-1.083``.
    """
    x = np.asarray(relative_depth, dtype=np.float64)
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        return (4.416 * np.power(x, 1.904)
                * np.power(1.0 + np.power(x / 1.283, 1.618), -1.083))


def keulegan_velocity_ratio(relative_submergence):
    """``U/u*`` from the Keulegan-Einstein fully rough logarithmic law.

    Args:
        relative_submergence (numpy.ndarray): ``h / ks``.

    Returns:
        numpy.ndarray: ``U/u* = 5.75 * log10(12.2 * h/ks)``.
    """
    chi = np.asarray(relative_submergence, dtype=np.float64)
    with np.errstate(divide="ignore", invalid="ignore"):
        return 5.75 * np.log10(12.2 * chi)


def smoothstep_weight(relative_submergence, low_limit=LOW_LIMIT, high_limit=HIGH_LIMIT):
    """Zero-to-one smoothstep weight of the Keulegan closure between two ``h/ks`` limits.

    Args:
        relative_submergence (numpy.ndarray): ``h / ks``.
        low_limit (float): weight is 0 at or below this.
        high_limit (float): weight is 1 at or above this.

    Returns:
        numpy.ndarray: ``t * t * (3 - 2 * t)`` with ``t`` clipped to [0, 1].
    """
    if not 0.0 < low_limit < high_limit:
        raise ValueError("Require 0 < low_limit < high_limit.")
    chi = np.asarray(relative_submergence, dtype=np.float64)
    t = np.clip((chi - low_limit) / (high_limit - low_limit), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def d84_of(grain, grain_kind="dmean", factor=D84_FACTOR):
    """``D84`` estimated from a grain-size raster.

    River Architect condition folders carry a ``dmean`` raster; the analyses need
    ``D84``. The published approximation ``D84 = 2.2 * D50`` is applied to ``dmean``
    for continuity with the original program, but a measured ``d84`` raster is
    preferable wherever one exists.

    Args:
        grain (numpy.ndarray): grain sizes in the condition's length unit.
        grain_kind (str): ``"dmean"``, ``"d50"`` (multiplied by ``factor``) or
            ``"d84"`` (used as is).
        factor (float): multiplier estimating ``D84`` from ``dmean`` or ``D50``.

    Returns:
        numpy.ndarray: the ``D84`` array.
    """
    if factor <= 0.0:
        raise ValueError("D84 conversion factor must be positive.")
    if grain_kind == "d84":
        return np.asarray(grain, dtype=np.float64)
    if grain_kind in ("d50", "dmean"):
        return np.asarray(grain, dtype=np.float64) * factor
    raise ValueError("Unsupported grain kind: %r" % grain_kind)


def calculate_taux(velocity, depth, d84, *, gravity=9.81, density_ratio=RHO_RATIO,
                   ks_factor=KS_FACTOR, low_limit=LOW_LIMIT, high_limit=HIGH_LIMIT):
    """Squared shear velocity, D84 Shields stress, relative submergence and regime.

    All inputs must share one unit system (SI with ``gravity=9.81``, or U.S. customary
    with ``gravity`` in ft/s**2); the Shields stress is dimensionless either way.
    Arrays may contain NaN. Invalid cells (NaN anywhere, ``u < 0``, ``h <= 0``,
    ``d84 <= 0``) come back as NaN with regime code 0.

    Args:
        velocity (numpy.ndarray): depth-averaged flow velocity ``U``.
        depth (numpy.ndarray): flow depth ``h``.
        d84 (numpy.ndarray): ``D84`` grain size; see :func:`d84_of`.
        gravity (float): gravitational acceleration in the rasters' unit system.
        density_ratio (float): sediment-to-water density ratio ``s``.
        ks_factor (float): equivalent roughness multiplier ``ks / D84``.
        low_limit (float): pure Rickenmann-Recking at or below this ``h/ks``.
        high_limit (float): pure Keulegan-Einstein at or above this ``h/ks``.

    Returns:
        ShearResult: ``(ustar2, theta84, h_over_ks, regime)``.
    """
    if gravity <= 0.0:
        raise ValueError("gravity must be positive.")
    if density_ratio <= 1.0:
        raise ValueError("density_ratio must be greater than one.")
    if ks_factor <= 0.0:
        raise ValueError("ks_factor must be positive.")
    if not 0.0 < low_limit < high_limit:
        raise ValueError("Require 0 < low_limit < high_limit.")

    u = np.asarray(velocity, dtype=np.float64)
    h = np.asarray(depth, dtype=np.float64)
    grain = np.asarray(d84, dtype=np.float64)
    u, h, grain = np.broadcast_arrays(u, h, grain)

    valid = (np.isfinite(u) & np.isfinite(h) & np.isfinite(grain)
             & (u >= 0.0) & (h > 0.0) & (grain > 0.0))

    ustar2 = np.full(u.shape, np.nan, dtype=np.float64)
    theta84 = np.full(u.shape, np.nan, dtype=np.float64)
    h_over_ks = np.full(u.shape, np.nan, dtype=np.float64)
    regime = np.zeros(u.shape, dtype=np.uint8)

    if not np.any(valid):
        return ShearResult(ustar2, theta84, h_over_ks, regime)

    x = np.full(u.shape, np.nan, dtype=np.float64)
    chi = np.full(u.shape, np.nan, dtype=np.float64)
    x[valid] = h[valid] / grain[valid]
    chi[valid] = h[valid] / (ks_factor * grain[valid])

    rr_ratio = rickenmann_recking_velocity_ratio(x)

    # Evaluate Keulegan only above the low-submergence limit. Elsewhere the RR value is
    # a safe placeholder that carries zero blend weight.
    keulegan_ratio = rr_ratio.copy()
    use_log = valid & (chi > low_limit)
    keulegan_ratio[use_log] = keulegan_velocity_ratio(chi[use_log])

    weight = smoothstep_weight(chi, low_limit, high_limit)
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        shear_coefficient = ((1.0 - weight) / np.square(rr_ratio)
                             + weight / np.square(keulegan_ratio))
        candidate_ustar2 = np.square(u) * shear_coefficient
        candidate_theta = candidate_ustar2 / (gravity * (density_ratio - 1.0) * grain)

    finite = (valid & np.isfinite(shear_coefficient) & (shear_coefficient >= 0.0)
              & np.isfinite(candidate_ustar2) & np.isfinite(candidate_theta))

    ustar2[finite] = candidate_ustar2[finite]
    theta84[finite] = candidate_theta[finite]
    h_over_ks[finite] = chi[finite]

    regime[finite & (chi <= low_limit)] = 1
    regime[finite & (chi > low_limit) & (chi < high_limit)] = 2
    regime[finite & (chi >= high_limit)] = 3

    return ShearResult(ustar2, theta84, h_over_ks, regime)


def regime_summary(regime):
    """Cell counts per resistance regime, for logging.

    Args:
        regime (numpy.ndarray): the code array of a :class:`ShearResult`.

    Returns:
        dict: ``{label: count}`` in the order of :data:`REGIME_LABELS`.
    """
    counts = np.bincount(np.asarray(regime, dtype=np.uint8).ravel(), minlength=4)
    return {REGIME_LABELS[code]: int(counts[code]) for code in sorted(REGIME_LABELS)}
