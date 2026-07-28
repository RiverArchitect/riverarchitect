"""Fish stranding risk over a receding hydrograph on the ``2100_sample`` condition.

Run it from anywhere in a clone; it falls back to the bundled ``sample-data/``::

    mamba run -n ra-env python examples/stranding_risk.py

Writes ``sample-data/Output/StrandingRisk/2100_sample/``: one raster per discharge,
a ``Q_disconnect.tif`` recording the discharge at which each cell becomes a trap, and a
GeoPackage of the individual pools at the worst discharge.

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
OUT = os.path.join(config.dir_output("StrandingRisk"), "2100_sample")

# Discharges (cfs) of the recession, highest first.
DISCHARGES = [1500, 1400, 1300, 1200, 1100, 1000, 900, 800, 700, 600, 500, 400, 300]

# Minimum swimming depth (ft). Chinook salmon fry: 0.2; juvenile: 0.3. This is the single
# most influential parameter in the analysis - report it with the result.
H_MIN = 0.2

# Discharge to polygonise into individual pools.
POOL_Q = 700


def main():
    os.makedirs(OUT, exist_ok=True)

    # The highest discharge defines the reference grid.
    _, prof = raster.read(os.path.join(CONDITION, "h%06d.tif" % DISCHARGES[0]))
    dx, dy = raster.cell_size(prof)
    cell_area = dx * dy

    per_q = []
    print("%8s %8s %12s %12s %8s" % ("Q", "pools", "wetted", "stranded", "%"))
    for q in DISCHARGES:
        depth, dprof = raster.read(os.path.join(CONDITION, "h%06d.tif" % q))
        depth = raster.align(depth, dprof, prof)
        # nan_to_num keeps NoData out of the comparison instead of propagating it.
        wet = np.nan_to_num(depth) > H_MIN

        # connectivity=4 matches arcpy.sa.RegionGroup: cells touching only at a corner
        # are not one pool.
        mask, n_pools = raster.disconnected_mask(wet, connectivity=4)
        per_q.append(raster.con(mask, float(q)))

        wetted = wet.sum() * cell_area
        stranded = mask.sum() * cell_area
        print("%8d %8d %12.0f %12.0f %8.2f"
              % (q, n_pools, wetted, stranded, 100.0 * stranded / wetted))

        raster.write(os.path.join(OUT, "disconnected_%06d.tif" % q),
                     raster.con(mask, 1.0), prof)

    # Highest discharge at which each cell was disconnected: the flow at which that spot
    # becomes a trap as the hydrograph recedes.
    q_disconnect = raster.cell_statistics(per_q, "MAXIMUM")
    raster.write(os.path.join(OUT, "Q_disconnect.tif"), q_disconnect, prof)

    total = np.isfinite(q_disconnect).sum() * cell_area
    print("\ntotal area disconnected at some point: %.0f sqft (%.2f ac)"
          % (total, total / 43560.0))

    # Individual pools, for a map or a field sheet.
    depth, dprof = raster.read(os.path.join(CONDITION, "h%06d.tif" % POOL_Q))
    depth = raster.align(depth, dprof, prof)
    mask, _ = raster.disconnected_mask(np.nan_to_num(depth) > H_MIN, connectivity=4)

    pools = raster.polygonize(mask.astype("int32"), prof, mask=mask)
    pools["area"] = pools.geometry.area
    pools = pools.sort_values("area", ascending=False)
    pools.to_file(os.path.join(OUT, "pools_%06d.gpkg" % POOL_Q), driver="GPKG")
    print("\npool areas at %d cfs (sqft):" % POOL_Q)
    print(pools["area"].round(0).to_string(index=False))


if __name__ == "__main__":
    main()
