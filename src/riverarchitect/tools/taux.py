#!/usr/bin/python
""" Dimensionless bed shear stress (Shields stress) from a velocity, depth and grain raster.

Rationale
---------
The analysis modules compute the Shields stress internally, per condition and per discharge.
This tool exposes the same calculation - :func:`riverarchitect.shear.calculate_taux` - for a
single set of rasters, so a stress map can be produced from model output that is not (yet)
organised as a River Architect condition, and so the closure can be checked against measured
data.

It writes four rasters, one per output quantity, prefixed with ``--output-prefix``:

    <prefix>_ustar2.tif      squared shear velocity, in the inputs' unit system
    <prefix>_theta84.tif     Shields stress referenced to D84
    <prefix>_h_over_ks.tif   relative submergence h/ks
    <prefix>_regime.tif      uint8: 0 invalid, 1 Rickenmann-Recking, 2 blended,
                             3 Keulegan-Einstein

Usage
-----
    python -m riverarchitect.tools.taux --velocity u000550.tif --depth h000550.tif \\
        --grains dmean.tif --unit us --output-prefix out/q000550

    # a measured D84 raster is preferable to estimating it from a mean grain size
    python -m riverarchitect.tools.taux --velocity u.tif --depth h.tif --grains d84.tif \\
        --grain-kind d84 --unit si --output-prefix out/run1

Depth and grain size are resampled onto the velocity raster's grid, so the inputs need not
share an extent - but they must share a unit system, and ``--unit`` must name it. Requires
rasterio/GDAL; it does not use arcpy, so it runs on any platform.
"""

import argparse
import os
import sys

try:
    from riverarchitect import config, raster, shear
except ImportError:  # pragma: no cover - exercised only without the geospatial stack
    config = raster = shear = None


def dependencies_available():
    """True when the geospatial stack this tool needs could be imported."""
    return raster is not None


def compute(velocity_path, depth_path, grains_path, output_prefix, grain_kind="dmean",
            unit="si", ks_factor=None, low_limit=None, high_limit=None):
    """Write the four shear rasters and return ``{quantity: path}``.

    Args:
        velocity_path (str): depth-averaged velocity raster; defines the output grid.
        depth_path (str): water depth raster.
        grains_path (str): grain size raster; see ``grain_kind``.
        output_prefix (str): path prefix of the four outputs.
        grain_kind (str): ``"dmean"``, ``"d50"`` or ``"d84"``.
        unit (str): ``"si"`` or ``"us"``, selecting the gravitational acceleration.
        ks_factor, low_limit, high_limit (float): closure parameters; see
            :func:`riverarchitect.shear.calculate_taux`.

    Returns:
        dict: quantity name -> path written.
    """
    kwargs = {}
    if ks_factor is not None:
        kwargs["ks_factor"] = ks_factor
    if low_limit is not None:
        kwargs["low_limit"] = low_limit
    if high_limit is not None:
        kwargs["high_limit"] = high_limit

    velocity, reference = raster.read(velocity_path)
    depth, depth_profile = raster.read(depth_path)
    grain, grain_profile = raster.read(grains_path)
    depth = raster.align(depth, depth_profile, reference)
    grain = raster.align(grain, grain_profile, reference)

    result = shear.calculate_taux(velocity, depth, shear.d84_of(grain, grain_kind),
                                  gravity=shear.gravity_of(unit), **kwargs)

    directory = os.path.dirname(os.path.abspath(output_prefix))
    if directory:
        os.makedirs(directory, exist_ok=True)

    written = {}
    for quantity in ("ustar2", "theta84", "h_over_ks"):
        path = "%s_%s.tif" % (output_prefix, quantity)
        raster.write(path, getattr(result, quantity), reference)
        written[quantity] = path
    path = "%s_regime.tif" % output_prefix
    raster.write(path, result.regime, reference, dtype="uint8", nodata=0)
    written["regime"] = path

    written["_summary"] = shear.regime_summary(result.regime)
    return written


def main():
    parser = argparse.ArgumentParser(
        description="Regime-aware dimensionless bed shear stress from aligned velocity, "
                    "depth and grain-size rasters.")
    parser.add_argument("--velocity", required=True, help="velocity raster; defines the grid")
    parser.add_argument("--depth", required=True, help="water depth raster")
    parser.add_argument("--grains", required=True, help="grain size raster")
    parser.add_argument("--output-prefix", required=True,
                        help="path prefix of the four output rasters")
    parser.add_argument("--grain-kind", choices=("dmean", "d50", "d84"), default="dmean",
                        help="what the grain raster holds; dmean and d50 are multiplied by "
                             "2.2 to estimate D84. A measured d84 is preferable.")
    parser.add_argument("--unit", choices=("si", "us"), default="si",
                        help="unit system of the rasters (selects g)")
    parser.add_argument("--ks-factor", type=float, default=None,
                        help="equivalent roughness ks/D84 (default 2)")
    parser.add_argument("--low-limit", type=float, default=None,
                        help="pure Rickenmann-Recking at or below this h/ks (default 7)")
    parser.add_argument("--high-limit", type=float, default=None,
                        help="pure Keulegan-Einstein at or above this h/ks (default 20)")
    args = parser.parse_args()

    if not dependencies_available():
        print("ERROR: This tool needs numpy and rasterio. Run it in the `ra-env` "
              "environment:\n"
              "       mamba run -n ra-env python -m riverarchitect.tools.taux ...",
              file=sys.stderr)
        return 1

    for label, path in (("velocity", args.velocity), ("depth", args.depth),
                        ("grains", args.grains)):
        if not os.path.isfile(path):
            print("ERROR: no such %s raster: %s" % (label, path), file=sys.stderr)
            return 1

    if args.grain_kind != "d84":
        print("NOTE: estimating D84 = 2.2 * %s. A measured D84 raster is preferable."
              % args.grain_kind, file=sys.stderr)

    try:
        written = compute(args.velocity, args.depth, args.grains, args.output_prefix,
                          grain_kind=args.grain_kind, unit=args.unit,
                          ks_factor=args.ks_factor, low_limit=args.low_limit,
                          high_limit=args.high_limit)
    except (OSError, RuntimeError, ValueError) as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        return 2

    summary = written.pop("_summary")
    print("Resistance regime, cell counts:")
    for label, count in summary.items():
        print("  %-20s %d" % (label, count))
    print("Written:")
    for quantity, path in written.items():
        print("  %-12s %s" % (quantity, path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
