"""Reading a *condition*: its input rasters and the return periods of its discharges.

A condition is one folder under ``01_Conditions/`` holding the terrain, sediment and
hydraulic rasters for a single planning situation. ``input_definitions.inp`` names which
raster is which and gives the flood return period of each modelled discharge - it is the
metadata every analysis module needs before it can start.

The file format is the original one, so existing conditions are read unchanged::

    Return periods = 1.0, 1.08, 1.13 #[Comma separated LIST] defines lifespans
    Water depth (h) = h007250.tif, h007750.tif #[Comma separated LIST]
    Grain sizes (D mean) = dmean #[STRING]

Everything after ``#`` is a comment, the key is matched case-insensitively on a substring,
and the ``.tif`` extension is optional.

River Architect 1.x wrote ``Flow depth (h)`` for that second key. Both spellings are read,
so no existing condition needs editing; this package writes the hydraulically correct
*water depth*, since "flow depth" names a property of the flow rather than of the water
column it is measured in.
"""

import os
import re

from . import config

__all__ = ["Condition", "parse_input_definitions", "discharge_token", "discharge_label"]

#: Maps a key in ``input_definitions.inp`` onto the attribute it fills. The keys are matched
#: as lower-case substrings, because the original files are inconsistent about wording.
_KEYS = {
    "return periods": "return_periods",
    "water depth": "depth_rasters",
    "flow depth": "depth_rasters",       # what River Architect 1.x wrote; still read
    "flow velocity": "velocity_rasters",
    "grain sizes": "grain_raster",
    "dem of differences": "dod_rasters",
    "detrended dem": "detrended_raster",
    "morphological units": "mu_raster",
    "depth to groundwater": "d2w_raster",
    "side channel": "side_channel_raster",
    "wildcard raster": "wildcard_raster",
    "composite habitat suitability": "chsi_raster",
    "dem": "dem_raster",          # must stay last: "dem" also matches the keys above
}


def parse_input_definitions(path):
    """Parse an ``input_definitions.inp`` file into a plain dict.

    Args:
        path (str): path to the ``.inp`` file.

    Returns:
        dict: attribute name -> value. List-valued keys give lists of strings; ``return
        periods`` gives a list of floats.
    """
    values = {}
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.split("#", 1)[0].strip()
            if not line or "=" not in line:
                continue
            key, _, raw = line.partition("=")
            key = key.strip().lower()
            raw = raw.strip()
            if not raw:
                continue

            # Longest key first, so "detrended dem" is not swallowed by "dem".
            for candidate in sorted(_KEYS, key=len, reverse=True):
                if candidate in key:
                    attribute = _KEYS[candidate]
                    break
            else:
                continue

            items = [item.strip() for item in raw.split(",") if item.strip()]
            if attribute == "return_periods":
                values[attribute] = [float(item) for item in items]
            elif attribute.endswith("_rasters"):
                values[attribute] = items
            else:
                values[attribute] = items[0]
    return values


class Condition:
    """One condition folder: where its rasters are and what discharges they represent.

    Args:
        name (str): condition folder name, e.g. ``"2100_sample"``.
        directory (str): the folder itself. Defaults to ``01_Conditions/<name>`` under the
            project home.

    Attributes:
        return_periods (list): flood return period in years, one per modelled discharge.
        discharges (list): discharge of each hydraulic raster, parsed from its file name.
    """

    def __init__(self, name, directory=None):
        self.name = str(name)
        self.directory = directory or os.path.join(config.dir_conditions(), self.name)
        if not os.path.isdir(self.directory):
            raise FileNotFoundError("no such condition folder: %s" % self.directory)

        definitions = {}
        self.definitions_file = os.path.join(self.directory, "input_definitions.inp")
        if os.path.isfile(self.definitions_file):
            definitions = parse_input_definitions(self.definitions_file)

        self.return_periods = definitions.get("return_periods", [])
        self.depth_rasters = definitions.get("depth_rasters", [])
        self.velocity_rasters = definitions.get("velocity_rasters", [])
        self.grain_raster = definitions.get("grain_raster", "dmean")
        self.detrended_raster = definitions.get("detrended_raster", "dem_detrend")
        self.d2w_raster = definitions.get("d2w_raster", "d2w")
        self.mu_raster = definitions.get("mu_raster", "mu")
        self.dem_raster = definitions.get("dem_raster", "dem")
        self.dod_rasters = definitions.get("dod_rasters", ["fill", "scour"])

        if not self.depth_rasters:
            # No .inp, or an incomplete one: fall back to whatever is on disk.
            self.depth_rasters = self._discover("h")
            self.velocity_rasters = self._discover("u")

        self.discharges = [self.discharge_of(name) for name in self.depth_rasters]

    # ------------------------------------------------------------------ discovery

    def _discover(self, prefix):
        pattern = re.compile(r"^%s\d+(?:_\d+)?\.tif$" % prefix, re.IGNORECASE)
        matches = [name for name in os.listdir(self.directory) if pattern.match(name)]
        # Numeric order, not lexical: "h000001_060.tif" (1.06) sorts before
        # "h000003_890.tif" (3.89) either way, but mixed naming folders would not.
        return sorted(matches, key=lambda name: (self.discharge_of(name), name))

    def all_depth_rasters(self):
        """Every ``h<discharge>.tif`` present on disk, not just those in the ``.inp``.

        ``input_definitions.inp`` lists the discharges that carry a flood return period,
        which is what lifespan mapping needs. A recession analysis needs the low flows too,
        and in a real condition those are on disk but absent from the ``.inp`` - the sample
        condition has 60 depth rasters and names 17.
        """
        return self._discover("h")

    def all_velocity_rasters(self):
        """Every ``u<discharge>.tif`` present on disk. See :meth:`all_depth_rasters`."""
        return self._discover("u")

    def path(self, name):
        """Absolute path of a raster in this condition, adding ``.tif`` when omitted."""
        if not name:
            return None
        if not os.path.splitext(name)[1]:
            name += ".tif"
        return os.path.join(self.directory, name)

    def exists(self, name):
        """True when the named raster is present in the condition folder."""
        path = self.path(name)
        return bool(path) and os.path.isfile(path)

    @staticmethod
    def discharge_of(raster_name):
        """Discharge encoded in a hydraulic raster name.

        Both naming forms of the original program are read: plain integers
        (``h001000.tif`` -> ``1000.0``) and the underscore-decimal form its
        ``write_Q_str`` produced (``h000001_060.tif`` -> ``1.06``).
        """
        digits = re.search(r"(\d+)(?:_(\d+))?", os.path.basename(str(raster_name)))
        if not digits:
            return None
        if digits.group(2) is not None:
            return float(digits.group(1) + "." + digits.group(2))
        return float(digits.group(1))

    def depth_raster_for(self, discharge):
        """File name of the depth raster modelling ``discharge``, or None."""
        return self._raster_for("h", discharge)

    def velocity_raster_for(self, discharge):
        """File name of the velocity raster modelling ``discharge``, or None."""
        return self._raster_for("u", discharge)

    def _raster_for(self, prefix, discharge):
        for name in self._discover(prefix):
            parsed = self.discharge_of(name)
            if parsed is not None and abs(parsed - float(discharge)) < 1e-6:
                return name
        return None

    def token_for(self, discharge):
        """Discharge token spelled as *this condition's own* file names spell it.

        A raster derived from a discharge should be named after the rasters it came from:
        ``h000293_000.tif`` and ``u000293_000.tif`` yield ``ts000293_000.tif``, not the
        canonical ``ts000293.tif`` that :func:`discharge_token` would produce for 293.0.
        Both parse back to the same discharge, but only the first keeps a discharge's
        rasters together in a sorted file listing.

        Falls back to :func:`discharge_token` when the condition has no depth raster at
        that discharge.
        """
        name = self.depth_raster_for(discharge) or self.velocity_raster_for(discharge)
        if name:
            return re.sub(r"^[a-zA-Z_]+", "", os.path.splitext(name)[0])
        return discharge_token(discharge)

    def hydraulic_pairs(self):
        """Yield ``(return_period, depth_path, velocity_path)`` for each modelled discharge.

        Pairs whose depth or velocity raster is missing from disk are skipped, and a
        condition with no return periods falls back to the discharge itself, so that a
        partially prepared condition still produces something rather than raising.
        """
        periods = self.return_periods or self.discharges
        for index, depth_name in enumerate(self.depth_rasters):
            if index >= len(self.velocity_rasters) or index >= len(periods):
                break
            velocity_name = self.velocity_rasters[index]
            if not (self.exists(depth_name) and self.exists(velocity_name)):
                continue
            yield periods[index], self.path(depth_name), self.path(velocity_name)

    @property
    def max_lifespan(self):
        """Longest return period in the condition; the cap on any lifespan it can support."""
        return max(self.return_periods) if self.return_periods else 50.0

    # ------------------------------------------------------------------ diagnosis

    def validate(self):
        """Problems with how this condition is defined, as a list of sentences.

        Empty when the condition looks usable. This is what error messages embed when an
        analysis cannot start, so each entry states what is wrong *and* what the module
        expected to find.
        """
        problems = []
        depth_names = self.all_depth_rasters()
        velocity_names = self.all_velocity_rasters()

        if not os.path.isfile(self.definitions_file):
            problems.append("input_definitions.inp is missing; rasters are discovered "
                            "from their file names instead.")

        if not depth_names:
            problems.append("No depth raster found. Depth rasters must be named "
                            "h<discharge>.tif, either as integers (h000550.tif = 550) or "
                            "with '_' as the decimal separator (h000001_060.tif = 1.06).")
        if not velocity_names:
            problems.append("No velocity raster found (u<discharge>.tif, named like the "
                            "depth rasters).")

        depth_q = {self.discharge_of(name) for name in depth_names} - {None}
        velocity_q = {self.discharge_of(name) for name in velocity_names} - {None}
        for missing in sorted(depth_q - velocity_q):
            problems.append("Discharge %s has a depth raster but no velocity raster."
                            % discharge_label(missing))
        for missing in sorted(velocity_q - depth_q):
            problems.append("Discharge %s has a velocity raster but no depth raster."
                            % discharge_label(missing))

        for label, name in (("DEM", self.dem_raster), ("grain size", self.grain_raster)):
            if not self.exists(name):
                problems.append("The %s raster %r is not in the folder. Terrain-based "
                                "and bed-stability analyses need it."
                                % (label, os.path.basename(str(self.path(name)))))

        for attribute in ("depth_rasters", "velocity_rasters"):
            for name in getattr(self, attribute):
                if not self.exists(name):
                    problems.append("input_definitions.inp names %r, which is not in "
                                    "the folder." % name)
        return problems

    def describe(self):
        """A short multi-line report of what this condition provides and what it lacks.

        Written to be shown to users verbatim when an analysis cannot start.
        """
        depth_names = self.all_depth_rasters()
        velocity_names = self.all_velocity_rasters()
        lines = ["Condition %r in %s" % (self.name, self.directory),
                 "  input_definitions.inp: %s"
                 % ("parsed" if os.path.isfile(self.definitions_file) else "not found")]

        for label, names in (("depth", depth_names), ("velocity", velocity_names)):
            discharges = sorted({self.discharge_of(name) for name in names} - {None})
            if discharges:
                lines.append("  %s rasters: %d, discharges %s to %s"
                             % (label, len(names), discharge_label(discharges[0]),
                                discharge_label(discharges[-1])))
            else:
                lines.append("  %s rasters: none" % label)

        present = [name for name in (self.dem_raster, self.grain_raster, self.d2w_raster,
                                     self.detrended_raster, self.mu_raster)
                   if self.exists(name)]
        lines.append("  other rasters present: %s" % (", ".join(present) or "none"))

        problems = self.validate()
        if problems:
            lines.append("Problems:")
            lines.extend("  - %s" % problem for problem in problems)
        return "\n".join(lines)

    def __repr__(self):
        return "Condition(%r, %d discharges)" % (self.name, len(self.depth_rasters))


def discharge_token(discharge):
    """File-name token of a discharge, round-tripping through :meth:`Condition.discharge_of`.

    Integral discharges keep the compact form of this package's own outputs
    (``550`` -> ``"000550"``); fractional ones use the original program's
    ``write_Q_str`` form (``1.06`` -> ``"000001_060"``).
    """
    value = float(discharge)
    if value == int(value):
        return "%06d" % int(value)
    return ("%010.3f" % value).replace(".", "_")


def discharge_label(discharge):
    """Human-readable discharge for GUI lists: ``550.0`` -> ``"550"``, ``1.06`` -> ``"1.06"``."""
    return "%g" % float(discharge)
