#!/usr/bin/python
"""Design tables for self-sustaining pool-riffle sequences.

A pool-riffle sequence maintains itself when the flow **reverses**: at low flow the riffle
is the faster of the two, but as discharge rises the pool accelerates past it, scouring
itself out and depositing on the riffle. Without that reversal the pool fills in and the
sequence disappears within a few floods. Caamano et al. (2009) give the geometric condition
for it in a trapezoidal channel, and this module sizes a sequence that satisfies it.

The calculation is one-dimensional and cross-section-averaged: it takes a channel, not a
raster, and it produces numbers a designer puts on a drawing. That is why it sits beside
the raster analyses rather than inside them. Its natural companion is **River Builder**
(:mod:`riverarchitect.riverbuilder`), which generates the valley these dimensions go into,
and the side-channel guidance in the feature catalogue.

What it computes
----------------
1. The **reversal discharge** - the flow that just mobilises the bed, from the Shields
   criterion applied to the normal channel.
2. The **pool spacing**, as a multiple of bankfull width, after Thompson (2013).
3. The **pool and riffle base widths** that produce a target residual pool depth at the
   reversal discharge, found by widening the riffle and narrowing the pool in step until
   the depth is reached, subject to the Caamano criterion.

Everything is computed in SI internally. ``unit="us"`` converts lengths and discharges at
the boundary; Manning's ``n`` is quoted as the same number in both systems by convention,
so it is never converted.

This module is pure Python and numpy: no rasters, no I/O, no optional dependencies.

Where this differs from the 1.x design script
---------------------------------------------
The reversal discharge, the reversal depth, the pool spacing and the residual pool depth
all reproduce ``Tools/morphology_designer.py`` exactly. The **pool and riffle widths do
not**, and it is worth knowing why before comparing a new table against an old one.

The original adjusted the pool bank slope inside a branch guarded by
``if caamano_ratio > 1``, printing *"Caamano criterion NOT fulfilled"* - but a ratio above
one is the criterion being *satisfied*, so the adjustment fired in exactly the case it was
meant to rescue and its message was inverted. On the shipped sample channel it steepened
the pool bank once, from 1:2.58 to 1:2.48, which is why that run reports a 15.65 m pool
against the 14.88 m here. Both reach the same residual depth and both satisfy the
criterion; they are two points on the same design curve, at different pool bank slopes.

Under this construction the criterion holds from the first increment anyway, so nothing
needs steering towards it - see :func:`design_pool_riffle`.

Two smaller corrections: the expansion-loss angle is now in the degrees that Hager's
formula expects, where the original passed a dimensionless width gradient through
``radians()`` before taking its arctangent and drove the term to about a hundred-thousandth
of its intended value; and the pool spacing is the mean of the Thompson factors rather than
the mean of ten million unseeded lognormal draws constructed to have exactly that mean.
"""

import logging
import math
from typing import NamedTuple

from . import config
from .shear import G_SI, RHO_RATIO

__all__ = ["TAUX_CR", "THOMPSON_FACTORS", "PoolRiffleDesign", "REPORT_FIELDS",
           "roughness_strickler", "roughness_meyer_peter_mueller",
           "roughness_rickenmann_recking",
           "manning_discharge", "normal_depth", "base_width",
           "critical_depth_for_transport", "discharge_for_transport",
           "pool_spacing", "pool_spacing_bounds", "design_pool_riffle", "format_design"]

logger = logging.getLogger("riverarchitect")

#: Default critical dimensionless bed shear stress (Shields parameter) for incipient motion.
TAUX_CR = 0.047

#: Pool-to-pool spacing as a multiple of bankfull width, after Thompson (2013). The first
#: entry is the midpoint of a reported 2.50-3.76 range; the rest are single reported values.
THOMPSON_FACTORS = ((2.50 + 3.76) / 2, 3.25, 5.4, 6.51, 6.7)

#: Channel slope above which a pool-riffle morphology is not the expected bed form.
MAX_POOL_RIFFLE_SLOPE = 0.02


class PoolRiffleDesign(NamedTuple):
    """One pool-riffle design, in the unit system it was asked for.

    Attributes:
        pool_width (float): pool base width.
        riffle_width (float): riffle base width.
        residual_depth (float): residual pool depth ``D_z``, pool bed to riffle crest.
        pool_depth (float): flow depth over the pool at the reversal discharge.
        riffle_depth (float): flow depth over the riffle at the reversal discharge.
        normal_depth (float): flow depth in the unmodified normal channel at that discharge.
        pool_spacing (float): pool-to-pool spacing.
        pool_riffle_spacing (float): pool-to-riffle spacing, half the above.
        pool_bank_slope (float): pool bank slope ``m`` as ``1:m``.
        riffle_bank_slope (float): riffle bank slope ``m``.
        reversal_discharge (float): the flow that just mobilises the bed.
        bankfull_width (float): top width of the normal channel at that flow.
        mean_velocity (float): cross-section-averaged velocity over the pool.
        caamano_satisfied (bool): whether the velocity-reversal criterion holds.
        converged (bool): whether the target residual depth was reached.
        iterations (int): how many width increments were tried.
        unit (str): ``"us"`` or ``"si"``.
    """

    pool_width: float
    riffle_width: float
    residual_depth: float
    pool_depth: float
    riffle_depth: float
    normal_depth: float
    pool_spacing: float
    pool_riffle_spacing: float
    pool_bank_slope: float
    riffle_bank_slope: float
    reversal_discharge: float
    bankfull_width: float
    mean_velocity: float
    caamano_satisfied: bool
    converged: bool
    iterations: int
    unit: str


# ------------------------------------------------------------------ roughness estimates

def roughness_strickler(d50):
    """Manning's ``n`` after Strickler (1923).

    Args:
        d50 (float): median grain size in metres.

    Returns:
        float: Manning's n in s/m^(1/3).
    """
    return d50 ** (1.0 / 6.0) / 21.1


def roughness_meyer_peter_mueller(d90):
    """Manning's ``n`` after Meyer-Peter and Mueller (1948).

    Valid in fully turbulent flow only.

    Args:
        d90 (float): 90th-percentile grain size in metres. ``d90 = 2.75 * d50`` is the
            substitution the original design script used when only a median was known.

    Returns:
        float: Manning's n in s/m^(1/3).
    """
    return d90 ** (1.0 / 6.0) / 26.0


def roughness_rickenmann_recking(depth, d84):
    """Manning's ``n`` from the variable-power resistance law of Rickenmann and Recking (2011).

    Unlike the other two this one depends on the flow, because at low relative submergence
    resistance is not a property of the grain size alone. Use ``d84 = 2.2 * d50`` when only
    a median is available - the same substitution :mod:`riverarchitect.shear` makes.

    Args:
        depth (float): flow depth in metres.
        d84 (float): 84th-percentile grain size in metres.

    Returns:
        float: Manning's n in s/m^(1/3).
    """
    x = depth / d84
    sqrt_8_over_f = 4.416 * x ** 1.904 * (1.0 + (x / 1.283) ** 1.618) ** -1.083
    return depth ** (1.0 / 6.0) / sqrt_8_over_f


# ------------------------------------------------------------------ trapezoidal hydraulics

def _area(depth, bank_slope, base_width):
    return depth * (base_width + bank_slope * depth)


def _perimeter(depth, bank_slope, base_width):
    return base_width + 2.0 * depth * math.sqrt(1.0 + bank_slope ** 2)


def manning_discharge(depth, bank_slope, roughness, base_width, slope):
    """Discharge through a trapezoid by the Gauckler-Manning-Strickler formula.

    Args:
        depth (float): flow depth in metres.
        bank_slope (float): bank slope ``m`` as ``1:m`` (horizontal per vertical).
        roughness (float): Manning's n in s/m^(1/3).
        base_width (float): channel base width in metres.
        slope (float): channel bed slope, dimensionless.

    Returns:
        float: discharge in m^3/s.
    """
    area = _area(depth, bank_slope, base_width)
    perimeter = _perimeter(depth, bank_slope, base_width)
    return area ** (5.0 / 3.0) * math.sqrt(slope) / (roughness * perimeter ** (2.0 / 3.0))


def _solve_increasing(function, target, upper_guess, tolerance=1e-9, max_iterations=200):
    """Invert a strictly increasing positive function by bracketing and bisection.

    Newton-Raphson is what the original design script used, from an initial guess of
    ``1 / base_width`` - a quantity with the wrong dimensions, which diverged on wide
    shallow channels and reported "no convergence" after a thousand iterations. Discharge
    is strictly increasing in depth and in width, so a bracket always exists and bisection
    always finds it. It is slower per step and cannot fail.

    Args:
        function (callable): strictly increasing, ``function(0) <= 0`` in effect.
        target (float): the value to reach.
        upper_guess (float): a starting guess for the upper bracket; doubled until it
            overshoots.

    Returns:
        float: the argument at which ``function`` equals ``target``.

    Raises:
        ValueError: when no bracket can be found, which means the inputs are unphysical.
    """
    low = 0.0
    high = max(float(upper_guess), 1e-6)
    for _ in range(max_iterations):
        if function(high) >= target:
            break
        high *= 2.0
    else:
        raise ValueError("no bracket for the target value %g - check the inputs" % target)

    for _ in range(max_iterations):
        middle = 0.5 * (low + high)
        if function(middle) < target:
            low = middle
        else:
            high = middle
        if high - low < tolerance * max(1.0, high):
            break
    return 0.5 * (low + high)


def normal_depth(discharge, bank_slope, roughness, base_width, slope):
    """Normal (uniform-flow) depth of a trapezoid carrying ``discharge``.

    Args:
        discharge (float): discharge in m^3/s.
        bank_slope (float): bank slope ``m`` as ``1:m``.
        roughness (float): Manning's n in s/m^(1/3).
        base_width (float): base width in metres.
        slope (float): bed slope, dimensionless.

    Returns:
        float: flow depth in metres.
    """
    return _solve_increasing(
        lambda h: manning_discharge(h, bank_slope, roughness, base_width, slope),
        discharge, upper_guess=max(base_width, 1.0))


def base_width(discharge, depth, bank_slope, roughness, slope):
    """Base width a trapezoid needs to carry ``discharge`` at ``depth``.

    The inverse question to :func:`normal_depth`, for when the target is a flow depth
    rather than a channel.

    Args:
        discharge (float): discharge in m^3/s.
        depth (float): target flow depth in metres.
        bank_slope (float): bank slope ``m`` as ``1:m``.
        roughness (float): Manning's n in s/m^(1/3).
        slope (float): bed slope, dimensionless.

    Returns:
        float: base width in metres.
    """
    return _solve_increasing(
        lambda w: manning_discharge(depth, bank_slope, roughness, w, slope),
        discharge, upper_guess=max(10.0 * depth, 1.0))


def critical_depth_for_transport(d50, slope, taux_cr=TAUX_CR, rho_ratio=RHO_RATIO):
    """Flow depth at which the bed just starts to move.

    From the Shields criterion with the wide-channel approximation ``tau_b = rho g h S``:

    .. math:: h_{cr} = \\frac{\\tau_{*,cr}\\,(s-1)\\,D_{50}}{S_0}

    Args:
        d50 (float): median grain size in metres.
        slope (float): bed slope, dimensionless.
        taux_cr (float): critical Shields parameter.
        rho_ratio (float): relative grain density.

    Returns:
        float: critical depth in metres.
    """
    return taux_cr * (rho_ratio - 1.0) * d50 / slope


def discharge_for_transport(d50, slope, bank_slope, roughness, width,
                            taux_cr=TAUX_CR, rho_ratio=RHO_RATIO):
    """Discharge that just mobilises the bed, and the depth at which it does.

    This is the **reversal discharge**: the design flow of a self-maintaining sequence,
    because a sequence that never moves its bed never rebuilds itself.

    Args:
        d50 (float): median grain size in metres.
        slope (float): bed slope, dimensionless.
        bank_slope (float): bank slope ``m`` as ``1:m``.
        roughness (float): Manning's n in s/m^(1/3).
        width (float): base width in metres.

    Returns:
        tuple: ``(discharge, depth)`` in m^3/s and metres.
    """
    depth = critical_depth_for_transport(d50, slope, taux_cr, rho_ratio)
    return manning_discharge(depth, bank_slope, roughness, width, slope), depth


# ------------------------------------------------------------------------- pool spacing

def pool_spacing(bankfull_width, factors=THOMPSON_FACTORS):
    """Expected pool-to-pool spacing, after Thompson (2013).

    Reported spacings scatter log-normally about a few multiples of bankfull width. The
    expected value of that distribution is the mean of the reported factors, so this is a
    multiplication.

    The original design script arrived at the same number by fitting a lognormal to the
    factors, drawing ten million samples and averaging them - which is the mean of the
    distribution it was constructed to have, computed the slow way, and differently on
    every run because the draw was unseeded. Use :func:`pool_spacing_bounds` when the
    spread is what you actually want.

    Args:
        bankfull_width (float): top width of the channel at bankfull flow.
        factors (tuple): spacing as multiples of bankfull width.

    Returns:
        float: pool-to-pool spacing, in the unit of ``bankfull_width``.
    """
    return bankfull_width * sum(factors) / len(factors)


def pool_spacing_bounds(bankfull_width, factors=THOMPSON_FACTORS):
    """The reported range of pool-to-pool spacings, not just its expectation.

    A single spacing implies a confidence the literature does not support. This returns the
    smallest and largest reported multiples, which is the honest thing to put on a drawing
    alongside the design value.

    Args:
        bankfull_width (float): top width of the channel at bankfull flow.
        factors (tuple): spacing as multiples of bankfull width.

    Returns:
        tuple: ``(minimum, maximum)`` spacing, in the unit of ``bankfull_width``.
    """
    return bankfull_width * min(factors), bankfull_width * max(factors)


# ------------------------------------------------------------------------- the designer

def _expansion_loss(pool_width, riffle_width, length, gravity, velocity):
    """Head loss through the expansion from pool to riffle, after Hager (2010).

    .. math:: \\zeta_{ex} = \\left(\\frac{\\theta}{90} + \\sin 2\\theta\\right)
              \\left(1 - \\frac{B_p}{B_r}\\right)^2

    with the expansion angle :math:`\\theta` in degrees. The original script passed a
    dimensionless width gradient through ``radians()`` before taking its arctangent and
    then treated the radian result as degrees, which drove the whole term to about
    :math:`10^{-5}` of its intended value - the correction was present but inert. It is
    small either way on a realistic expansion; it is computed correctly here so that it is
    small for the right reason.

    Returns:
        float: the head loss, as a length.
    """
    if riffle_width <= 0 or riffle_width <= pool_width or length <= 0:
        return 0.0
    theta = math.degrees(math.atan((riffle_width - pool_width) / length))
    zeta = (theta / 90.0 + math.sin(math.radians(2.0 * theta))) \
        * (1.0 - pool_width / riffle_width) ** 2
    return velocity ** 2 / (2.0 * gravity) * zeta


def design_pool_riffle(d50, slope, base_width, target_residual_depth,
                       bank_slope=2.58, roughness=None, unit="si",
                       taux_cr=TAUX_CR, increment=0.001, max_iterations=100000):
    """Size a self-maintaining pool-riffle sequence.

    Widens the riffle and narrows the pool in equal steps until the residual pool depth
    reaches ``target_residual_depth`` at the reversal discharge, checking the Caamano
    et al. (2009) velocity-reversal criterion

    .. math:: \\frac{B_r}{B_p} - 1 > \\frac{\\Delta z}{h_r}

    at every step. Under this construction - equal cross-sectional area, pool and riffle
    widths moved by the same step - the left side grows faster than the right from the
    first increment, so the criterion holds throughout and is reported rather than steered
    towards. It is still checked at every step and reported as ``caamano_satisfied``,
    because a design that fails it would not maintain itself and must not be presented as
    though it would.

    Args:
        d50 (float): median grain size, in the length unit of ``unit``.
        slope (float): channel bed slope, dimensionless.
        base_width (float): base width of the normal channel, in the length unit.
        target_residual_depth (float): wanted pool depth below the riffle crest. Must be
            positive.
        bank_slope (float): bank slope ``m`` as ``1:m``, for both pool and riffle at the
            start.
        roughness (float): Manning's n in s/m^(1/3). Defaults to
            :func:`roughness_strickler` of ``d50``. The same number applies in both unit
            systems.
        unit (str): ``"us"`` (feet, cfs) or ``"si"`` (metres, m^3/s).
        taux_cr (float): critical Shields parameter for the reversal discharge.
        increment (float): width step in metres. Smaller is more precise and slower.
        max_iterations (int): give up after this many steps.

    Returns:
        PoolRiffleDesign: the design, in the unit system asked for.

    Raises:
        ValueError: for a non-positive target depth, width, grain size or slope.
    """
    unit = str(unit).lower()
    if unit not in config.UNITS:
        raise ValueError("unit must be one of %s, not %r" % (list(config.UNITS), unit))
    if target_residual_depth <= 0:
        raise ValueError("the target residual pool depth must be positive")
    for name, value in (("d50", d50), ("base_width", base_width), ("slope", slope),
                        ("bank_slope", bank_slope)):
        if value <= 0:
            raise ValueError("%s must be positive, got %r" % (name, value))

    # Work in SI throughout; Manning's n is the same number in both systems by convention,
    # so it is the one quantity that is never converted.
    to_si = config.FT2M if unit == "us" else 1.0
    d50_si = d50 * to_si
    width_si = base_width * to_si
    target_si = target_residual_depth * to_si
    roughness = roughness_strickler(d50_si) if roughness is None else float(roughness)

    if slope > MAX_POOL_RIFFLE_SLOPE:
        logger.warning("   >> channel slope %.3f is above %.2f: a pool-riffle sequence is "
                       "not the bed form expected at this slope.",
                       slope, MAX_POOL_RIFFLE_SLOPE)

    reversal_q, reversal_h = discharge_for_transport(
        d50_si, slope, bank_slope, roughness, width_si, taux_cr=taux_cr)
    logger.info("   >> reversal discharge %.3f m3/s at a depth of %.3f m",
                reversal_q, reversal_h)

    bankfull_width = width_si + 2.0 * bank_slope * reversal_h
    spacing = pool_spacing(bankfull_width)
    pool_riffle_spacing = spacing / 2.0

    pool_width = riffle_width = width_si
    pool_bank_slope = riffle_bank_slope = float(bank_slope)
    residual = pool_depth = riffle_depth = velocity = 0.0
    caamano_ok = False
    converged = False
    iterations = 0

    while iterations < max_iterations:
        iterations += 1
        pool_width -= increment
        riffle_width += increment
        if pool_width <= 0:
            logger.warning("   >> the pool closed up before reaching a residual depth of "
                           "%.3f m - the target is not reachable in this channel.",
                           target_si)
            break

        pool_depth = normal_depth(reversal_q, pool_bank_slope, roughness, pool_width, slope)
        pool_area = _area(pool_depth, pool_bank_slope, pool_width)
        velocity = reversal_q / pool_area

        # The riffle carries the same cross-sectional area as the pool, which fixes its
        # depth once its width is chosen: (B_r + m h) h = A_p.
        riffle_depth = (-riffle_width
                        + math.sqrt(riffle_width ** 2 + 4.0 * riffle_bank_slope * pool_area)
                        ) / (2.0 * riffle_bank_slope)

        residual = pool_depth - riffle_depth - _expansion_loss(
            pool_width, riffle_width, pool_riffle_spacing, G_SI, velocity)

        caamano_ok = (riffle_width / pool_width - 1.0) > (residual / riffle_depth) \
            if riffle_depth > 0 else False

        if abs(target_si - residual) / target_si < 1e-3:
            converged = True
            break

    if not converged:
        logger.warning("   >> no pool-riffle geometry reached a residual depth of %.3f m "
                       "after %d steps (reached %.3f m).", target_si, iterations, residual)
    if not caamano_ok:
        logger.warning("   >> the Caamano velocity-reversal criterion is not satisfied: "
                       "this sequence would not maintain itself.")

    from_si = 1.0 / config.FT2M if unit == "us" else 1.0
    q_from_si = 1.0 / config.CFS2CMS if unit == "us" else 1.0
    return PoolRiffleDesign(
        pool_width=pool_width * from_si,
        riffle_width=riffle_width * from_si,
        residual_depth=residual * from_si,
        pool_depth=pool_depth * from_si,
        riffle_depth=riffle_depth * from_si,
        normal_depth=reversal_h * from_si,
        pool_spacing=spacing * from_si,
        pool_riffle_spacing=pool_riffle_spacing * from_si,
        pool_bank_slope=pool_bank_slope,
        riffle_bank_slope=riffle_bank_slope,
        reversal_discharge=reversal_q * q_from_si,
        bankfull_width=bankfull_width * from_si,
        mean_velocity=velocity * from_si,
        caamano_satisfied=caamano_ok,
        converged=converged,
        iterations=iterations,
        unit=unit,
    )


#: Fields worth reporting, in reading order, as ``(attribute, label, kind)``. ``kind`` is
#: the unit-label key from :func:`riverarchitect.config.unit_labels`, or ``None`` for a
#: dimensionless quantity.
REPORT_FIELDS = (
    ("reversal_discharge", "reversal discharge", "q"),
    ("normal_depth", "normal depth at reversal", "length"),
    ("bankfull_width", "bankfull width", "length"),
    ("pool_width", "pool base width", "length"),
    ("riffle_width", "riffle base width", "length"),
    ("residual_depth", "residual pool depth", "length"),
    ("pool_depth", "flow depth over pool", "length"),
    ("riffle_depth", "flow depth over riffle", "length"),
    ("pool_spacing", "pool-to-pool spacing", "length"),
    ("pool_riffle_spacing", "pool-to-riffle spacing", "length"),
    ("pool_bank_slope", "pool bank slope 1:m", None),
    ("riffle_bank_slope", "riffle bank slope 1:m", None),
    ("mean_velocity", "mean velocity over pool", "u"),
)


def format_design(design):
    """Render a design as a plain-text table, with its units and its caveats.

    One implementation for the command line and both front ends, so they cannot report a
    design differently. A design that did not converge, or that fails the Caamano
    criterion, says so at the end: those are the two ways this calculation produces numbers
    that look like an answer and are not.

    Args:
        design (PoolRiffleDesign): what :func:`design_pool_riffle` returned.

    Returns:
        str: the table, without a trailing newline.
    """
    labels = config.unit_labels(design.unit)
    lines = []
    for name, title, kind in REPORT_FIELDS:
        value = getattr(design, name)
        suffix = "" if kind is None else " " + labels[kind]
        lines.append("%-26s %10.3f%s" % (title, value, suffix))
    if not design.converged:
        lines.append("")
        lines.append("NOT CONVERGED: the target residual pool depth was not reached.")
    if not design.caamano_satisfied:
        lines.append("")
        lines.append("CAAMANO CRITERION FAILED: this sequence would not maintain itself.")
    return "\n".join(lines)
