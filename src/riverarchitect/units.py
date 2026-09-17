"""Unit-system and coordinate-reference checks.

River Architect never converts input data. The unit system (``"si"`` or ``"us"``) *states*
what the rasters of a condition already are, and every threshold, gravity constant and
area label follows from it. A wrong statement does not fail on its own: it applies metric
thresholds to rasters in feet, or the reverse, and yields plausible-looking nonsense.

This module turns that silent failure into an error wherever the data carries evidence,
which is the linear unit of each raster's coordinate reference system (CRS):

* a raster whose CRS is in metres is SI, one in feet or U.S. survey feet is U.S. customary;
* a geographic CRS (degrees) is refused, since cell sizes, slopes and volumes would be in
  degrees;
* rasters that are combined must agree on that unit, and a raster with a CRS is never
  combined with one without;
* rasters in different CRSs with the same unit are reprojected, with a warning.

What cannot be checked is a raster whose *values* are in a different unit from its CRS,
for example depths in feet on a metric grid. Such data must be converted before use.

A disagreement between the stated unit system and the CRS raises
:class:`UnitMismatchError`. Where that is intended (a vertical unit that genuinely differs
from the horizontal one), pass ``strict=False`` or set
:envvar:`RIVERARCHITECT_UNIT_CHECK` to ``warn`` to log a warning instead. Mismatches
*between* rasters always raise.
"""

import logging
import os
import threading
from collections.abc import Mapping

from . import config

__all__ = ["UnitMismatchError", "check_unit", "crs_unit_system", "describe_crs",
           "check_crs_pair", "check_rasters", "infer_unit_system", "project_unit_note"]

logger = logging.getLogger("riverarchitect")

#: Linear unit factors (metres per unit) recognised as U.S. customary: the international
#: foot and the U.S. survey foot.
_FOOT_FACTORS = (0.3048, 1200.0 / 3937.0)

_warned_pairs = set()
_warned_lock = threading.Lock()


class UnitMismatchError(ValueError):
    """The unit system or CRS of the input data is inconsistent."""


def check_unit(unit):
    """Normalise and validate a unit-system name.

    Args:
        unit (str): ``"si"`` or ``"us"``, in any case.

    Returns:
        str: the lower-case unit system.

    Raises:
        ValueError: for anything else. There is deliberately no fallback.
    """
    value = str(unit).strip().lower()
    if value not in config.UNITS:
        raise ValueError("unit must be one of %s, not %r" % (list(config.UNITS), unit))
    return value


def _as_crs(crs):
    if crs is None or crs == "":
        return None
    from rasterio.crs import CRS
    if isinstance(crs, CRS):
        return crs
    return CRS.from_user_input(crs)


def describe_crs(crs):
    """Short human-readable label of a CRS and its linear unit, for messages."""
    crs = _as_crs(crs)
    if crs is None:
        return "no CRS"
    epsg = crs.to_epsg()
    name = "EPSG:%d" % epsg if epsg else (crs.to_string()[:60] or "custom CRS")
    if crs.is_geographic:
        return "%s (geographic, degrees)" % name
    return "%s (%s)" % (name, crs.linear_units)


def crs_unit_system(crs):
    """The unit system a CRS's linear unit implies.

    Args:
        crs: a :class:`rasterio.crs.CRS`, anything it accepts, or ``None``.

    Returns:
        str or None: ``"si"`` for metres, ``"us"`` for feet or U.S. survey feet, ``None``
        when there is no CRS or its unit is neither.

    Raises:
        UnitMismatchError: for a geographic CRS.
    """
    crs = _as_crs(crs)
    if crs is None:
        return None
    if crs.is_geographic:
        raise UnitMismatchError(
            "%s is a geographic coordinate system: cell sizes, slopes and volumes would be in "
            "degrees. Reproject the rasters to a projected CRS in metres or feet."
            % describe_crs(crs))
    try:
        _name, factor = crs.linear_units_factor
    except Exception:  # CRS without a usable linear unit
        return None
    if abs(factor - 1.0) < 1e-9:
        return "si"
    if any(abs(factor - foot) < 1e-7 for foot in _FOOT_FACTORS):
        return "us"
    return None


def check_crs_pair(src_crs, dst_crs):
    """Refuse to combine two rasters whose CRSs are incompatible.

    Called before a raster is reprojected onto another's grid. Raises if exactly one of
    the two has a CRS, if either is geographic, or if their linear units differ; logs a
    warning (once per pair) if they merely differ and will be reprojected.

    Raises:
        UnitMismatchError: when the two cannot be combined safely.
    """
    src, dst = _as_crs(src_crs), _as_crs(dst_crs)
    if src is None and dst is None:
        return
    if src is None or dst is None:
        raise UnitMismatchError(
            "cannot combine a raster in %s with one in %s: assign the missing CRS first"
            % (describe_crs(src), describe_crs(dst)))
    if src == dst:
        return
    src_unit, dst_unit = crs_unit_system(src), crs_unit_system(dst)
    if src_unit != dst_unit or (src_unit is None and src.linear_units != dst.linear_units):
        raise UnitMismatchError(
            "cannot combine a raster in %s with one in %s: their linear units differ, so "
            "their values are almost certainly in different units too. Convert and "
            "reproject the data to one unit system first."
            % (describe_crs(src), describe_crs(dst)))
    key = (src.to_wkt(), dst.to_wkt())
    with _warned_lock:
        if key in _warned_pairs:
            return
        _warned_pairs.add(key)
    logger.warning("Reprojecting a raster from %s onto %s. Both are in %s, but check that "
                   "the rasters really belong together.",
                   describe_crs(src), describe_crs(dst), dst.linear_units)


def _strict(strict):
    if strict is None:
        return config.UNIT_CHECK != "warn"
    return bool(strict)


def _profile(item):
    if isinstance(item, Mapping):
        return "<array>", item
    if isinstance(item, tuple):
        return "<array>", item[1]
    from . import raster
    return str(item), raster.profile_of(item)


def infer_unit_system(sources):
    """The unit system a set of rasters is in, judged by their CRSs.

    Args:
        sources (iterable): raster paths or rasterio profiles.

    Returns:
        str or None: ``"si"``, ``"us"`` or ``None`` if no raster has a recognised unit.

    Raises:
        UnitMismatchError: if the rasters disagree, or one of them is geographic.
    """
    found = {}
    for item in sources:
        name, profile = _profile(item)
        unit = crs_unit_system(profile.get("crs"))
        if unit is not None:
            found.setdefault(unit, name)
    if len(found) > 1:
        raise UnitMismatchError(
            "the rasters mix unit systems: %s is in feet, %s in metres. River Architect "
            "does not convert data; bring every raster to one unit system first."
            % (os.path.basename(found["us"]), os.path.basename(found["si"])))
    return next(iter(found), None)


def check_rasters(sources, unit, strict=None, label="the input rasters"):
    """Check that rasters agree with each other and with the stated unit system.

    Args:
        sources (iterable): raster paths, rasterio profiles or ``(array, profile)`` pairs.
            Missing paths are skipped.
        unit (str): the unit system the analysis will assume.
        strict (bool): raise on a disagreement between ``unit`` and the rasters' CRS
            (default, or :envvar:`RIVERARCHITECT_UNIT_CHECK` ``=strict``) rather than
            log a warning. Disagreements between the rasters always raise.
        label (str): what the rasters are, for messages.

    Returns:
        str or None: the unit system the rasters are in, if it can be told.

    Raises:
        UnitMismatchError: see above.
        ValueError: for an unknown ``unit``.
    """
    unit = check_unit(unit)
    entries = []
    for item in sources:
        if item is None or (isinstance(item, (str, os.PathLike))
                            and not os.path.isfile(item)):
            continue
        entries.append(_profile(item))
    if not entries:
        return None

    crss = [(name, _as_crs(profile.get("crs"))) for name, profile in entries]
    missing = [name for name, crs in crss if crs is None]
    if missing and len(missing) < len(crss):
        raise UnitMismatchError(
            "%s have no coordinate reference system while the others do (%s). Assign the "
            "CRS of the rest to them first."
            % (", ".join(os.path.basename(name) for name in missing[:5]),
               describe_crs(next(crs for _name, crs in crss if crs is not None))))
    if missing:
        logger.warning("%s carry no coordinate reference system, so their unit system "
                       "cannot be verified. Make sure they are in %s units.",
                       label, "SI" if unit == "si" else "U.S. customary")
        return None

    system = infer_unit_system(profile for _name, profile in entries)
    distinct = {}
    for name, crs in crss:
        distinct.setdefault(crs.to_wkt(), (name, crs))
    if len(distinct) > 1:
        (_first, reference), *others = distinct.values()
        for _name, crs in others:
            check_crs_pair(crs, reference)

    if system is not None and system != unit:
        name, crs = next((n, c) for n, c in crss if crs_unit_system(c) == system)
        message = (
            "%s are in %s units (%s is in %s), but the analysis is set to %s. River "
            "Architect does not convert data: choose %s in the Units menu (or pass "
            "unit=%r). If the vertical unit of the data really differs from the CRS, set "
            "RIVERARCHITECT_UNIT_CHECK=warn."
            % (label, _long(system), os.path.basename(name), describe_crs(crs),
               _long(unit), _long(system), system))
        if _strict(strict):
            raise UnitMismatchError(message)
        logger.warning(message)
    elif system is None:
        logger.warning("The CRS of %s (%s) has a linear unit that is neither metres nor "
                       "feet; their unit system cannot be verified.",
                       label, describe_crs(crss[0][1]))
    return system


def project_unit_note(unit, directory=None):
    """A warning about the conditions of a project that do not match ``unit``, or None.

    Used by the interfaces when a project directory is opened, so a unit system that does
    not fit the data shows before anything is run rather than when a run fails.

    Args:
        unit (str): the unit system the interface is set to.
        directory (str): the conditions folder. Defaults to
            :func:`riverarchitect.config.dir_conditions`.

    Returns:
        str or None: one paragraph per problem, or None when there is none.
    """
    from .condition import Condition

    unit = check_unit(unit)
    directory = directory or config.dir_conditions()
    try:
        names = sorted(name for name in os.listdir(directory)
                       if os.path.isdir(os.path.join(directory, name))
                       and not name.startswith("."))
    except OSError:
        return None
    lines = []
    for name in names:
        try:
            system = Condition(name, os.path.join(directory, name)).unit_system()
        except (UnitMismatchError, OSError, ValueError) as exc:
            lines.append("%s: %s" % (name, exc))
            continue
        if system is not None and system != unit:
            lines.append("%s: the rasters are in %s units, but the Units menu is set to %s."
                         % (name, _long(system), _long(unit)))
    if not lines:
        return None
    return ("River Architect does not convert data, and an analysis whose unit system "
            "does not match its rasters will refuse to run.\n\n" + "\n".join(lines))


def _long(unit):
    return "SI (metric)" if unit == "si" else "U.S. customary"
