"""Project-wide configuration: paths, units and the canonical NoData value.

Paths are resolved with :mod:`os.path` so that the same constants work on Windows, macOS and
Linux. No separator is ever written literally: ``os.path.join`` picks the right one, and
nothing translates separators by hand, because a backslash is a legal character in a POSIX
file name and rewriting it corrupts the path.

Data directories are resolved relative to a *project root*, which is by default the current
working directory. Point :envvar:`RIVERARCHITECT_HOME` at a directory to override it, or
call :func:`set_project_home` at runtime.
"""

import os

__all__ = ["NODATA", "FT2AC", "FT2M", "CFS2CMS", "UNITS",
           "package_dir", "templates_dir", "symbology_dir",
           "project_home", "set_project_home", "user_config_dir",
           "dir_conditions", "dir_flows", "dir_maps", "dir_output",
           "area_unit", "unit_labels",
           "UNIT_CHECK", "TILING", "BLOCK_SIZE", "WORKERS", "memory_budget", "set_memory_budget"]

APP_ID = "org.riverarchitect.RiverArchitect"

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

#: Supported unit systems. ``"si"`` is the default everywhere.
UNITS = ("si", "us")

#: What happens when the stated unit system disagrees with the linear unit of the rasters'
#: CRS: ``"strict"`` raises :class:`riverarchitect.units.UnitMismatchError`, ``"warn"`` logs
#: a warning. Read from :envvar:`RIVERARCHITECT_UNIT_CHECK`. Disagreements *between*
#: rasters always raise. See :mod:`riverarchitect.units`.
UNIT_CHECK = os.environ.get("RIVERARCHITECT_UNIT_CHECK", "strict").strip().lower()
if UNIT_CHECK not in ("strict", "warn"):
    import logging
    logging.getLogger("riverarchitect").warning(
        "RIVERARCHITECT_UNIT_CHECK=%r is neither 'strict' nor 'warn' - using 'strict'",
        UNIT_CHECK)
    UNIT_CHECK = "strict"

_PROJECT_HOME = None

#: When analyses process rasters block by block instead of whole: ``"auto"`` switches on
#: when a run would not fit in :func:`memory_budget`, ``"always"`` and ``"never"`` force
#: the choice. Read from :envvar:`RIVERARCHITECT_TILING`. See :mod:`riverarchitect.tiled`.
TILING = os.environ.get("RIVERARCHITECT_TILING", "auto").strip().lower()

#: Edge length in cells of one processing block, or a ``(rows, cols)`` pair. Read from
#: :envvar:`RIVERARCHITECT_BLOCK_SIZE`.
BLOCK_SIZE = int(os.environ.get("RIVERARCHITECT_BLOCK_SIZE", "4096"))

#: Threads processing blocks in parallel; ``None`` picks up to four from the CPU count.
#: Read from :envvar:`RIVERARCHITECT_WORKERS`.
def _workers_from_environment():
    value = os.environ.get("RIVERARCHITECT_WORKERS", "").strip().lower()
    if value in ("", "auto"):
        return None
    try:
        return max(1, int(value))
    except ValueError:
        import logging
        logging.getLogger("riverarchitect").warning(
            "RIVERARCHITECT_WORKERS=%r is not a whole number - using the default", value)
        return None


WORKERS = _workers_from_environment()

_MEMORY_BUDGET = None
_SIZE_SUFFIX = {"k": 1024, "m": 1024 ** 2, "g": 1024 ** 3, "t": 1024 ** 4}


def _parse_bytes(text):
    """``"16G"``, ``"512MB"`` or ``"1000000"`` in bytes."""
    text = str(text).strip().lower().rstrip("ib").rstrip("b")
    if text and text[-1] in _SIZE_SUFFIX:
        return int(float(text[:-1]) * _SIZE_SUFFIX[text[-1]])
    return int(float(text))


def set_memory_budget(budget):
    """Cap the memory an analysis may plan to hold at once.

    Args:
        budget (int or str): bytes, or a string such as ``"16G"``. ``None`` restores the
            default.

    Returns:
        int: the budget now in force, in bytes.
    """
    global _MEMORY_BUDGET
    _MEMORY_BUDGET = None if budget is None else _parse_bytes(budget)
    return memory_budget()


def memory_budget():
    """Bytes an analysis may plan to hold in memory at once.

    Resolution order: :func:`set_memory_budget`, then :envvar:`RIVERARCHITECT_MAX_MEMORY`,
    then half of the physical memory of this machine (4 GiB where that cannot be
    determined). Analyses whose rasters would exceed it are processed block by block.
    """
    if _MEMORY_BUDGET:
        return _MEMORY_BUDGET
    if os.environ.get("RIVERARCHITECT_MAX_MEMORY"):
        return _parse_bytes(os.environ["RIVERARCHITECT_MAX_MEMORY"])
    total = _physical_memory()
    return total // 2 if total else 4 * 1024 ** 3


def _physical_memory():
    """Installed memory in bytes, or ``None``."""
    try:
        if os.name == "nt":
            import ctypes

            class _MemoryStatus(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong),
                            ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong),
                            ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

            status = _MemoryStatus()
            status.dwLength = ctypes.sizeof(_MemoryStatus)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
            return int(status.ullTotalPhys)
        return int(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))
    except (AttributeError, OSError, ValueError):
        return None


def icon_path():
    return os.path.join(package_dir(), "assets", "icon-v2.png")


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


def user_config_dir():
    """Directory for per-user state that does not belong to any project.

    The Live Guide's place in the walkthrough is remembered here rather than under
    :func:`project_home`, because it is a property of the person reading, not of the data
    they happen to be looking at: switching project directories must not lose it, and a
    project directory shared between people must not carry one reader's position to
    another.

    Resolution order: :envvar:`RIVERARCHITECT_CONFIG_HOME`, then the platform convention -
    ``%APPDATA%`` on Windows, ``$XDG_CONFIG_HOME`` or ``~/.config`` elsewhere.

    Returns:
        str: the directory. It is not created; callers that write make it themselves.
    """
    override = os.environ.get("RIVERARCHITECT_CONFIG_HOME")
    if override:
        return os.path.abspath(override)
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"),
                                                         "AppData", "Roaming")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"),
                                                                 ".config")
    return os.path.join(os.path.abspath(base), "riverarchitect")


def area_unit(unit="si"):
    """Area unit label for a unit system: ``'sqft'`` or ``'sqm'``."""
    return "sqft" if str(unit).lower() == "us" else "sqm"


def unit_labels(unit="si"):
    """Discharge, depth, velocity, length and volume labels for a unit system.

    Returns:
        dict: keys ``q``, ``h``, ``u``, ``length``, ``volume``, ``area``.
    """
    if str(unit).lower() == "us":
        return {"q": "cfs", "h": "ft", "u": "ft/s", "length": "ft",
                "volume": "cubic yard", "area": "sqft"}
    return {"q": "cms", "h": "m", "u": "m/s", "length": "m",
            "volume": "cubic meter", "area": "sqm"}
