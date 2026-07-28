"""Project-wide configuration: paths, units and the canonical NoData value.

Paths are resolved with :mod:`os.path` so that the same constants work on Windows and
POSIX. The original River Architect hard-coded ``"\\\\"`` separators throughout, which is
one of the reasons it could only run on Windows.

Data directories are resolved relative to a *project root*, which is by default the current
working directory. Point :envvar:`RIVERARCHITECT_HOME` at a directory to override it, or
call :func:`set_project_home` at runtime.
"""

import os

__all__ = ["NODATA", "FT2AC", "FT2M", "CFS2CMS", "UNITS",
           "package_dir", "templates_dir", "symbology_dir",
           "project_home", "set_project_home",
           "dir_conditions", "dir_flows", "dir_maps", "dir_output",
           "area_unit", "unit_labels"]

#: Canonical NoData value for every raster River Architect writes.
#:
#: Never test cell values against this constant directly. Go through the declared NoData
#: mask instead (``rasterio.open(...).read(masked=True)``), because third-party inputs carry
#: ``-3.4e38``, ``3.4e38``, ``0`` or ``-9999`` interchangeably. Use
#: :mod:`riverarchitect.tools.reconcile_nodata` to normalise an input condition.
NODATA = -999.0

#: Square feet to acres.
FT2AC = 1.0 / 43560.0
#: Feet to metres.
FT2M = 0.3048
#: Cubic feet per second to cubic metres per second.
CFS2CMS = 0.0283168466

#: Supported unit systems.
UNITS = ("us", "si")

_PROJECT_HOME = None


def package_dir():
    """Directory of the installed :mod:`riverarchitect` package."""
    return os.path.dirname(os.path.abspath(__file__))


def templates_dir():
    """Directory holding packaged templates (layer styles, workbooks)."""
    return os.path.join(package_dir(), "templates")


def symbology_dir():
    """Directory holding packaged QGIS layer styles (``.qml``)."""
    return os.path.join(templates_dir(), "symbology")


def project_home():
    """Root directory of the user's project data.

    Resolution order: an explicit :func:`set_project_home`, then the
    :envvar:`RIVERARCHITECT_HOME` environment variable, then the current working directory.
    """
    if _PROJECT_HOME:
        return _PROJECT_HOME
    return os.path.abspath(os.environ.get("RIVERARCHITECT_HOME", os.getcwd()))


def set_project_home(path):
    """Set the project root that the ``dir_*`` helpers resolve against."""
    global _PROJECT_HOME
    _PROJECT_HOME = os.path.abspath(path) if path else None
    return project_home()


def dir_conditions():
    """Directory holding input conditions (one sub-folder per condition)."""
    return os.path.join(project_home(), "01_Conditions")


def dir_flows():
    """Directory holding flow series and duration workbooks."""
    return os.path.join(project_home(), "00_Flows")


def dir_maps():
    """Directory holding map output (QGIS projects and PDFs)."""
    return os.path.join(project_home(), "02_Maps")


def dir_output(module=""):
    """Output directory, optionally for a named module."""
    return os.path.join(project_home(), "Output", module) if module \
        else os.path.join(project_home(), "Output")


def area_unit(unit="us"):
    """Area unit label for a unit system: ``'sqft'`` or ``'sqm'``."""
    return "sqft" if str(unit).lower() == "us" else "sqm"


def unit_labels(unit="us"):
    """Discharge, depth, velocity, length and volume labels for a unit system.

    Returns:
        dict: keys ``q``, ``h``, ``u``, ``length``, ``volume``, ``area``.
    """
    if str(unit).lower() == "us":
        return {"q": "cfs", "h": "ft", "u": "ft/s", "length": "ft",
                "volume": "cubic yard", "area": "sqft"}
    return {"q": "cms", "h": "m", "u": "m/s", "length": "m",
            "volume": "cubic meter", "area": "sqm"}
