"""Lifespan and design map for angular boulders on the ``2100_sample`` condition.

Run it from anywhere in a clone; it falls back to the bundled ``sample-data/``::

    mamba run -n ra-env python examples/lifespan_rocks.py

Writes ``sample-data/Output/LifespanDesign/2100_sample/{lf,ds}_rocks.tif``. Point it at your
own data by setting ``RIVERARCHITECT_HOME``.

The walkthrough for this script, including the expected output, is in
``docs/guide/tutorial.md``.
"""

import os

import numpy as np

from riverarchitect import config, raster


def use_bundled_sample_data():
    """Fall back to the sample data in the repository when no project home is set.

    Paths resolve against :func:`riverarchitect.config.project_home`: RIVERARCHITECT_HOME if
    it is set, otherwise the working directory. When that holds no conditions, use the
    ``sample-data/`` directory of this clone, so the example runs from anywhere.
    """
    if os.path.isdir(config.dir_conditions()):
        return
    bundled = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sample-data")
    if os.path.isdir(os.path.join(bundled, "01_Conditions")):
        config.set_project_home(bundled)


use_bundled_sample_data()

CONDITION = os.path.join(config.dir_conditions(), "2100_sample")
OUT = os.path.join(config.dir_output("LifespanDesign"), "2100_sample")

# Return periods (years) and the discharges (cfs) they belong to, from
# 01_Conditions/2100_sample/input_definitions.inp.
LIFESPANS = [1.0, 1.08, 1.13, 1.19, 1.3, 1.4, 1.84, 2.0, 3.27,
             5.0, 6.53, 10.0, 15.0, 20.0, 30.0, 40.0, 50.0]
DISCHARGES = [7250, 7750, 8250, 8750, 9250, 9750, 10000, 12000, 16000,
              20000, 21100, 24000, 28000, 30000, 34000, 42200, 88053]

# Threshold values for the "angular boulders" feature.
TAU_CR = 0.047          # (-) critical dimensionless bed shear stress
SF = 1.3                # (-) safety factor
DESIGN_LIFESPAN = 20.0  # (years) target lifespan for the design map
SCOUR_MIN = 3.0         # (ft) topographic change below which the feature is irrelevant

S = 2.68                # (-) relative grain density
N = 0.0473934 / 1.49    # (s/ft^1/3) Manning's n; 1.49 converts from SI


def critical_grain_size(h, u):
    """Grain diameter that just starts to move, in feet."""
    return (u * N) ** 2 / ((S - 1.0) * TAU_CR * h ** (1.0 / 3.0)) / SF


def hydraulics(q, ref_prof):
    """Depth and velocity at discharge ``q``, aligned onto ``ref_prof``.

    Dry cells become NoData rather than zero, otherwise the ``h ** (1/3)`` term divides by
    zero and reports an infinite critical grain size across the whole dry bed.
    """
    h, hp = raster.read(os.path.join(CONDITION, "h%06d.tif" % q))
    u, up = raster.read(os.path.join(CONDITION, "u%06d.tif" % q))
    h = raster.align(h, hp, ref_prof)
    u = raster.align(u, up, ref_prof)
    return np.where(h > 0, h, np.nan), u


def main():
    os.makedirs(OUT, exist_ok=True)

    # The grain-size raster defines the reference grid.
    dmean, prof = raster.read(os.path.join(CONDITION, "dmean.tif"))

    # One raster per flood, holding its return period where the grain is mobile and NoData
    # where it is not. The cell-wise minimum is then the earliest flood that mobilises the
    # cell, which is the feature's lifespan there.
    failure = []
    for years, q in zip(LIFESPANS, DISCHARGES):
        h, u = hydraulics(q, prof)
        with np.errstate(invalid="ignore", divide="ignore"):
            d_cr = critical_grain_size(h, u)
        failure.append(raster.con(d_cr >= dmean, years))

    lifespan = raster.cell_statistics(failure, "MINIMUM")
    raster.write(os.path.join(OUT, "lf_rocks.tif"), lifespan, prof)

    # Design map: the grain size that is stable at the design flood, clipped to the
    # extent of the lifespan map.
    h, u = hydraulics(DISCHARGES[LIFESPANS.index(DESIGN_LIFESPAN)], prof)
    with np.errstate(invalid="ignore", divide="ignore"):
        design = critical_grain_size(h, u) * 12.0          # ft -> in
    design = raster.con(np.isfinite(lifespan), design)
    raster.write(os.path.join(OUT, "ds_rocks.tif"), design, prof)

    dx, dy = raster.cell_size(prof)
    mapped = np.isfinite(lifespan)
    print("mapped area  %.0f sqft (%.2f ac)"
          % (mapped.sum() * dx * dy, mapped.sum() * dx * dy / 43560.0))
    for years, count in zip(*np.unique(lifespan[mapped], return_counts=True)):
        print("  %6.2f years  %7.0f sqft" % (years, count * dx * dy))
    print("stable grain size at the design flow: median %.1f in, max %.1f in"
          % (np.nanmedian(design), np.nanmax(design)))

    # Optional: angular boulders are a response to scour, so restrict the map to cells
    # where the bed actually moves. scour.tif is on a 5 ft grid, hence the align().
    scour, scour_prof = raster.read(os.path.join(CONDITION, "scour.tif"))
    scour = raster.align(scour, scour_prof, prof)
    restricted = raster.con(scour >= SCOUR_MIN, lifespan)
    print("after the %.1f ft scour restriction: %.0f sqft"
          % (SCOUR_MIN, np.isfinite(restricted).sum() * dx * dy))


if __name__ == "__main__":
    main()
