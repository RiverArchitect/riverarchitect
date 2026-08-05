"""The **Tools** menu, declared once for both front ends.

Every utility that ships as a console script also has to be reachable without a terminal,
and the two interfaces have to offer the same set. Declaring the menu here rather than in
each ``main.py`` makes that a single edit and lets a test assert the two agree, the way
``TAB_GROUPS`` is already asserted.

Each entry names a method that the main window must implement. The handler opens a small
wizard over the tool's own module - the same code path the console script takes, so the
two cannot disagree about what the tool does.
"""

import os

__all__ = ["TOOLS", "format_taux", "handler_names", "unit_name"]

#: One entry per tool: ``(menu label, main-window method, module it drives)``.
#: The module string is what the parity test checks against the console scripts.
TOOLS = (
    ("Reconcile NoData in a condition ...", "run_reconcile_nodata",
     "riverarchitect.tools.reconcile_nodata"),
    ("Bed shear stress ...", "run_taux",
     "riverarchitect.tools.taux"),
    ("Pool-riffle designer ...", "run_pool_riffle",
     "riverarchitect.tools.pool_riffle"),
    ("Convert ArcGIS .lyrx to QGIS .qml ...", "run_lyrx2qml",
     "riverarchitect.tools.lyrx2qml"),
)


def handler_names():
    """The method names a main window has to provide to build the menu."""
    return tuple(handler for _label, handler, _module in TOOLS)


def unit_name(unit):
    """Spelled-out name of a unit system, for a sentence rather than an axis label."""
    return "U.S. customary units" if str(unit).lower() == "us" else "SI units"


def format_taux(written):
    """Render what :func:`riverarchitect.tools.taux.compute` returned as a report.

    Shared by both front ends so the wizards agree with each other and with what the
    console script prints.
    """
    summary = written.get("_summary", {})
    # "invalid" is every dry or NoData cell, and on a real reach that is most of the
    # raster. Sharing it out against the wetted cells is the useful number, so it is
    # reported on its own line rather than folded into the denominator.
    invalid = summary.get("invalid", 0)
    wetted = sum(count for label, count in summary.items() if label != "invalid")

    lines = []
    if summary:
        lines.append("Resistance regime, share of the %d wetted cells:" % wetted)
        for label, count in summary.items():
            if label == "invalid":
                continue
            share = 100.0 * count / wetted if wetted else 0.0
            lines.append("  %-22s %9d  %5.1f %%" % (label, count, share))
        lines.append("  %-22s %9d  (dry or NoData)" % ("not evaluated", invalid))
        lines.append("")

    paths = [path for key, path in sorted(written.items()) if not key.startswith("_")]
    lines.append("Wrote:")
    lines += ["  %s" % path for path in paths]
    if paths:
        lines += ["", "Output folder: %s" % os.path.dirname(os.path.abspath(paths[0]))]
    return "\n".join(lines)
