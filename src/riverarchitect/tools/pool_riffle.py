#!/usr/bin/python
"""Command-line front end for the pool-riffle designer.

Sizes a self-maintaining pool-riffle sequence from a channel and a target pool depth, and
prints or writes the design table. See :mod:`riverarchitect.poolriffle` for the method.

Usage
-----
::

    riverarchitect-pool-riffle --d50 0.0914 --slope 0.004 --width 24 --pool-depth 0.915
    riverarchitect-pool-riffle --d50 0.3 --slope 0.004 --width 79 --pool-depth 3 --unit us

    # every roughness estimate, written to a CSV
    riverarchitect-pool-riffle --d50 0.0914 --slope 0.004 --width 24 --pool-depth 0.915 \\
        --roughness all --csv pool_riffle.csv

``--roughness all`` reproduces what the 1.x driver script did: run the design once per
roughness estimate, because the answer is sensitive to a number nobody measures directly,
and a designer should see that spread rather than one figure from one closure.
"""

import argparse
import csv
import logging
import sys

from .. import config
from ..poolriffle import (design_pool_riffle, format_design,
                          roughness_meyer_peter_mueller,
                          roughness_rickenmann_recking, roughness_strickler)

#: Roughness estimates the ``all`` option runs, as ``name -> callable(d50_si, depth_si)``.
ROUGHNESS_ESTIMATES = {
    "strickler": lambda d50, depth: roughness_strickler(d50),
    "meyer-peter-mueller": lambda d50, depth: roughness_meyer_peter_mueller(2.75 * d50),
    "rickenmann-recking": lambda d50, depth: roughness_rickenmann_recking(depth, 2.2 * d50),
}


def build_parser():
    parser = argparse.ArgumentParser(
        prog="riverarchitect-pool-riffle",
        description="Design a self-maintaining pool-riffle sequence.")
    parser.add_argument("--d50", type=float, required=True,
                        help="median grain size, in the chosen unit")
    parser.add_argument("--slope", type=float, required=True,
                        help="channel bed slope, dimensionless")
    parser.add_argument("--width", type=float, required=True,
                        help="base width of the normal channel")
    parser.add_argument("--pool-depth", type=float, required=True,
                        help="target residual pool depth, below the riffle crest")
    parser.add_argument("--bank-slope", type=float, default=2.58,
                        help="bank slope m as 1:m (default: 2.58)")
    parser.add_argument("--roughness", default="strickler",
                        help="a Manning's n in s/m^(1/3), one of %s, or 'all' "
                             "(default: strickler)"
                             % ", ".join(sorted(ROUGHNESS_ESTIMATES)))
    parser.add_argument("--unit", default="si", choices=sorted(config.UNITS),
                        help="'si' for metres and m3/s, 'us' for feet and cfs "
                             "(default: si)")
    parser.add_argument("--taux-cr", type=float, default=0.047,
                        help="critical Shields parameter (default: 0.047)")
    parser.add_argument("--csv", help="write the table here instead of only printing it")
    parser.add_argument("--quiet", action="store_true", help="suppress progress messages")
    return parser


def _roughness_values(args):
    """Resolve ``--roughness`` into ``[(label, n), ...]``, in s/m^(1/3)."""
    to_si = config.FT2M if args.unit == "us" else 1.0
    d50_si = args.d50 * to_si
    # Rickenmann-Recking needs a depth; the critical depth for transport is the flow the
    # design is built around, so it is the right one to evaluate the closure at.
    from ..poolriffle import critical_depth_for_transport
    depth_si = critical_depth_for_transport(d50_si, args.slope, args.taux_cr)

    choice = str(args.roughness).lower()
    if choice == "all":
        return [(name, function(d50_si, depth_si))
                for name, function in sorted(ROUGHNESS_ESTIMATES.items())]
    if choice in ROUGHNESS_ESTIMATES:
        return [(choice, ROUGHNESS_ESTIMATES[choice](d50_si, depth_si))]
    try:
        return [("given", float(args.roughness))]
    except ValueError:
        raise SystemExit("--roughness must be a number, 'all', or one of %s"
                         % ", ".join(sorted(ROUGHNESS_ESTIMATES)))


def main(argv=None):
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.WARNING if args.quiet else logging.INFO,
                        format="%(message)s")

    rows = []
    for label, roughness in _roughness_values(args):
        print("\nRoughness %s: n = %.4f s/m^(1/3)" % (label, roughness))
        design = design_pool_riffle(
            d50=args.d50, slope=args.slope, base_width=args.width,
            target_residual_depth=args.pool_depth, bank_slope=args.bank_slope,
            roughness=roughness, unit=args.unit, taux_cr=args.taux_cr)

        print(format_design(design))
        row = {"roughness_name": label, "manning_n": roughness, "unit": args.unit}
        row.update(design._asdict())
        rows.append(row)

    if args.csv:
        with open(args.csv, "w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print("\nWritten: %s" % args.csv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
