"""River Builder: synthetic river valleys from a handful of parameters.

The open-source replacement for the *River Builder* half of the ArcGIS ``ModifyTerrain``
module. The other half - threshold-based grading and widening of an existing DEM - is
:mod:`riverarchitect.terraforming`; this one starts from nothing and *invents* a valley.

Why invent a valley
-------------------
A restoration design needs a target, and a reach that has been channelised for a century no
longer contains one. River Builder generates a reach with the geometry a natural one would
have - a meandering centreline, a thalweg that rises and falls, bankfull width that varies
along it, floodplain and terrace benches - from parameters an engineer can defend: valley
slope, bankfull width and depth, median grain size, and a critical Shields stress. The
result is a DEM you can run a 2D model over and compare against the existing one.

The construction
----------------
1. A **centreline** along the valley, displaced sideways by the *meandering* function. Its
   arc length ``s`` and the sinuosity follow from that displacement.
2. **Bankfull width** at each station, from the width function about the base width, floored
   at the minimum width.
3. **Curvature**, from the curvature function - and, for an asymmetric cross-section, the
   analytical curvature of the sine that defines it.
4. **Channel slope** by least squares of curvature against arc length, plus valley slope
   over sinuosity. When the bankfull depth is not given it follows from it:
   ``H = 165 * D50 * tau_cr / S`` - a regime relation, so depth is not a free parameter.
5. **Thalweg and bank tops** at each station, and a **cross-section** between them: a
   symmetric U, an asymmetric U leaning into the bend, or a trapezoid.
6. **Floodplain and terrace** benches either side, offset by their own functions.
7. The points are triangulated onto a regular grid, clipped to the valley boundary, and
   written as a GeoTIFF.

Relation to the original
------------------------
The original called an R script (``riverbuilder.r``, 1189 lines) through ``rpy2``, wrote a
point cloud to CSV, and rebuilt it as a TIN and a raster with ``arcpy`` 3D Analyst - so it
needed R, rpy2, ArcGIS *and* a 3D Analyst licence. The geometry is reproduced here in numpy
and the interpolation is :class:`scipy.interpolate.LinearNDInterpolator`, which is what a TIN
is. Nothing else is required.

The parameter file format is unchanged, so an existing RiverBuilder input runs as it is.
"""

import logging
import math
import os
import re

import numpy as np

from . import config, raster

__all__ = ["RiverBuilder", "RiverBuilderInput", "UserFunction", "PARAMETERS",
           "CROSS_SECTIONS", "FUNCTION_TYPES", "DEFAULTS"]

logger = logging.getLogger("riverarchitect")

#: The function forms a sub-reach variability parameter may take, longest name first so that
#: ``SIN_SQ`` is not matched as ``SIN``.
FUNCTION_TYPES = ("SIN_SQ", "SIN", "COS", "LINE", "PERL")

#: Cross-sectional shapes: symmetric U, asymmetric U, trapezoid.
CROSS_SECTIONS = ("SU", "AU", "TZ")

#: Parameter name in the input file -> attribute name. The file format is the original's, so
#: an existing RiverBuilder input runs unchanged.
PARAMETERS = {
    "Datum": "datum",
    "Length": "length",
    "X Resolution": "x_resolution",
    "Channel XS Points": "xs_points",
    "Valley Slope (Sv)": "valley_slope",
    "Critical Shields Stress (t*50)": "tau_cr",
    "Bankfull Width (Wbf)": "bankfull_width",
    "Bankfull Width Minimum": "bankfull_width_min",
    "Bankfull Depth (Hbf, A)": "bankfull_depth",
    "Median Sediment Size (D50)": "d50",
    "Floodplain Width": "floodplain_width",
    "Outer Floodplain Edge Height": "floodplain_outer_height",
    "Terrace Width": "terrace_width",
    "Outer Terrace Edge Height": "terrace_outer_height",
    "Boundary Width": "boundary_width",
    "Cross-Sectional Shape": "xs_shape",
    "Meandering Centerline Function": "meander",
    "Centerline Curvature Function": "curvature",
    "Bankfull Width Function": "width_function",
    "Thalweg Elevation Function": "thalweg",
    "Left Floodplain Function": "left_floodplain",
    "Right Floodplain Function": "right_floodplain",
    "Trapezoidal Base": "trapezoid_base",
}

#: Defaults, reproducing ``cRiverBuilderConstruct.InputFile.get_par_defaults``.
DEFAULTS = {
    "datum": 1.0, "length": 100.0, "x_resolution": 100, "xs_points": 23,
    "valley_slope": 0.001, "tau_cr": 0.047,
    "bankfull_width": 10.0, "bankfull_width_min": 5.0, "bankfull_depth": 0.0,
    "d50": 0.01,
    "floodplain_width": 0.0, "floodplain_outer_height": 0.0,
    "terrace_width": 0.0, "terrace_outer_height": 0.0, "boundary_width": 0.0,
    "xs_shape": "SU", "trapezoid_base": 0,
}

_CALL = re.compile(r"^\s*([A-Z_]+)\s*\((.*)\)\s*$")


def _number(text):
    """A float that may be written in terms of PI, as the input format allows."""
    text = str(text).strip()
    if not text:
        return 0.0
    if "PI" in text.upper():
        # "2*PI", "PI/4", "PI" - a small, closed grammar rather than eval().
        expression = text.upper().replace("PI", repr(math.pi))
        if not re.fullmatch(r"[0-9eE+\-*/.() ]+", expression):
            raise ValueError("cannot read %r as a number" % text)
        return float(eval(expression, {"__builtins__": {}}))  # noqa: S307 - grammar checked
    return float(text)


class UserFunction:
    """One term of a sub-reach variability parameter.

    Args:
        kind (str): one of :data:`FUNCTION_TYPES`.
        arguments (list): the numbers in the call, in the order the format writes them.

    ``SIN``, ``COS`` and ``SIN_SQ`` take amplitude, frequency and phase shift and are
    evaluated against the *radian* station; ``LINE`` takes a slope and an intercept and is
    evaluated against the station in length units; ``PERL`` takes an amplitude and a
    wavelength and produces smooth pseudo-random noise against the station index.
    """

    def __init__(self, kind, arguments):
        kind = str(kind).upper()
        if kind not in FUNCTION_TYPES:
            raise ValueError("unknown function %r; expected one of %s"
                             % (kind, ", ".join(FUNCTION_TYPES)))
        self.kind = kind
        self.arguments = [_number(a) for a in arguments]
        while len(self.arguments) < 3:
            self.arguments.append(0.0)

    @classmethod
    def parse(cls, text):
        """Read ``SIN(0, 1, 0)`` into a :class:`UserFunction`."""
        match = _CALL.match(str(text))
        if not match:
            raise ValueError("cannot read %r as a function call" % text)
        name, arguments = match.group(1), match.group(2)
        for kind in FUNCTION_TYPES:            # longest first, so SIN_SQ wins over SIN
            if name.startswith(kind):
                return cls(kind, [a for a in arguments.split(",") if a.strip()])
        raise ValueError("unknown function %r" % name)

    def __call__(self, radians, metres, index, noise=None):
        """Evaluate along the reach.

        Args:
            radians (numpy.ndarray): station in radians, for the trigonometric forms.
            metres (numpy.ndarray): station in length units, for ``LINE``.
            index (numpy.ndarray): station index, for ``PERL``.
            noise (numpy.random.Generator): source for ``PERL``. Optional.
        """
        a, b, c = self.arguments[:3]
        if self.kind == "SIN":
            return a * np.sin(b * radians + c)
        if self.kind == "COS":
            return a * np.cos(b * radians + c)
        if self.kind == "SIN_SQ":
            return (a * np.sin(b * radians + c)) ** 2 / a if a else np.zeros_like(radians)
        if self.kind == "LINE":
            return a * metres + b
        return self._perlin(index, a, b, noise)

    @staticmethod
    def _perlin(index, amplitude, wavelength, noise=None):
        """Value noise: random values every ``wavelength`` samples, cosine-interpolated.

        The original drew its randoms from a hand-rolled linear congruential generator, so
        a run was not reproducible from anything the user could see. A
        :class:`numpy.random.Generator` is used instead, and
        :class:`RiverBuilder` seeds it, so the same input file gives the same valley.
        """
        index = np.asarray(index, dtype="float64")
        if wavelength <= 0:
            return np.zeros_like(index)
        noise = noise or np.random.default_rng(0)
        knots = noise.random(int(index.max() / wavelength) + 2) - 0.5

        position = index / wavelength
        low = np.floor(position).astype(int)
        fraction = position - low
        # Cosine interpolation, so successive sub-waves join without a kink.
        weight = (1.0 - np.cos(fraction * np.pi)) * 0.5
        return 2.0 * amplitude * (knots[low] * (1.0 - weight) + knots[low + 1] * weight)

    def __repr__(self):
        return "%s(%s)" % (self.kind, ", ".join("%g" % a for a in self.arguments))


class RiverBuilderInput:
    """The parameters of a synthetic valley, and the file they are read from and written to.

    Every attribute has a default, so a partially specified input still builds. Sub-reach
    variability parameters hold a *list* of :class:`UserFunction`, which are summed.

    Args:
        **overrides: any attribute in :data:`DEFAULTS`, or a variability parameter as a
            list of :class:`UserFunction`.
    """

    #: The variability parameters, and the independent variable each is evaluated against.
    VARIABILITY = ("meander", "curvature", "width_function", "thalweg",
                   "left_floodplain", "right_floodplain")

    def __init__(self, **overrides):
        for key, value in DEFAULTS.items():
            setattr(self, key, value)
        for key in self.VARIABILITY:
            setattr(self, key, [])
        self.name = "RiverBuilder"
        for key, value in overrides.items():
            if not hasattr(self, key):
                raise AttributeError("unknown parameter %r" % key)
            setattr(self, key, value)

    # ------------------------------------------------------------------ file format

    @classmethod
    def read(cls, path):
        """Read a RiverBuilder input file in the original format.

        User functions are defined by name and then referenced::

            SIN1=SIN(0, 1, 0)
            Meandering Centerline Function=SIN1

        A parameter may reference several, separated by commas or spaces; they are summed.
        """
        defined, values = {}, {}
        with open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                line = line.split("#", 1)[0].strip()
                if "=" not in line:
                    continue
                key, _, raw = line.partition("=")
                key, raw = key.strip(), raw.strip()
                if not raw:
                    continue
                if _CALL.match(raw) and key not in PARAMETERS:
                    defined[key] = UserFunction.parse(raw)   # e.g. SIN1=SIN(0, 1, 0)
                else:
                    values[key] = raw

        entry = cls(name=os.path.splitext(os.path.basename(str(path)))[0])
        for label, raw in values.items():
            attribute = PARAMETERS.get(label)
            if attribute is None:
                continue
            if attribute in cls.VARIABILITY:
                terms = []
                for token in re.split(r"[,\s]+", raw):
                    token = token.strip()
                    if not token:
                        continue
                    if token in defined:
                        terms.append(defined[token])
                    elif _CALL.match(token):
                        terms.append(UserFunction.parse(token))
                    else:
                        logger.info("      * %s: no function named %r - ignored",
                                    label, token)
                setattr(entry, attribute, terms)
            elif attribute in ("xs_shape",):
                setattr(entry, attribute, raw.upper())
            elif attribute in ("x_resolution", "xs_points", "trapezoid_base"):
                setattr(entry, attribute, int(float(raw)))
            else:
                setattr(entry, attribute, _number(raw))
        return entry

    def write(self, path):
        """Write the parameters back out in the original format."""
        lines = ["# River Architect - River Builder input", "#"]
        used, names = [], {}
        for attribute in self.VARIABILITY:
            for term in getattr(self, attribute):
                key = repr(term)
                if key not in names:
                    names[key] = "%s%d" % (term.kind, len(used) + 1)
                    used.append((names[key], term))

        for name, term in used:
            lines.append("%s=%s" % (name, term))
        lines.append("#")
        for label, attribute in PARAMETERS.items():
            value = getattr(self, attribute)
            if attribute in self.VARIABILITY:
                value = ", ".join(names[repr(term)] for term in value)
            lines.append("%s=%s" % (label, value))

        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
        return path

    def __repr__(self):
        return "RiverBuilderInput(%r, length=%g, W=%g)" % (self.name, self.length,
                                                           self.bankfull_width)


class RiverBuilder:
    """Build a synthetic river valley from a :class:`RiverBuilderInput`.

    Args:
        parameters (RiverBuilderInput or str): the parameters, or a file to read them from.
        unit (str): ``"us"`` or ``"si"``. The parameter file is metric by convention; this
            only labels the result.
        seed (int): seed for the ``PERL`` noise, so a run is reproducible.

    Attributes:
        error (bool): True when a step could not be completed.
    """

    def __init__(self, parameters, unit="si", seed=0):
        self.parameters = RiverBuilderInput.read(parameters) \
            if isinstance(parameters, str) else parameters
        self.unit = str(unit).lower()
        self.noise = np.random.default_rng(seed)
        self.logger = logger
        self.error = False

        if self.parameters.xs_shape not in CROSS_SECTIONS:
            raise ValueError("cross-sectional shape must be one of %s, not %r"
                             % (", ".join(CROSS_SECTIONS), self.parameters.xs_shape))
        if self.parameters.bankfull_width_min > self.parameters.bankfull_width:
            raise ValueError("the minimum bankfull width exceeds the bankfull width")
        if self.parameters.x_resolution < 2:
            raise ValueError("x_resolution must be at least 2 stations")

        self.geometry = None

    # ------------------------------------------------------------------ evaluation

    def _evaluate(self, terms, radians, metres, index):
        """Sum a variability parameter's terms, or zero when it has none."""
        total = np.zeros_like(metres, dtype="float64")
        for term in terms:
            total = total + term(radians, metres, index, noise=self.noise)
        return total

    # ------------------------------------------------------------------- the valley

    def build(self):
        """Compute the whole geometry.

        Returns:
            dict: the station arrays (``x``, ``centreline``, ``arc_length``,
            ``bankfull_width``, ``curvature``, ``thalweg``, ``top_of_bank``) and the
            cross-section grids (``xs_x``, ``xs_y``, ``xs_z``).
        """
        p = self.parameters
        n = int(p.x_resolution)

        index = np.arange(n, dtype="float64")
        # Station along the valley axis, and the same in radians over one reach length.
        x = index / n * p.length
        radians = index * (p.length / n / p.length) * 2.0 * np.pi

        centreline = self._evaluate(p.meander, radians, x, index)

        # Arc length of the meandering centreline. The first station is the origin, so its
        # step is zero - a straight valley must come out with a sinuosity of exactly 1.
        step = np.hypot(np.diff(x, prepend=x[0]), np.diff(centreline, prepend=centreline[0]))
        arc = np.cumsum(step)
        arc_radians = 2.0 * np.pi * arc / p.length

        # The direction cosines below divide by the step, so the first one borrows the
        # second rather than dividing by zero. That is what the original's duplicated
        # first `dscms` entry was for.
        step_for_direction = step.copy()
        if n > 1:
            step_for_direction[0] = step[1]

        width_factor = self._evaluate(p.width_function, arc_radians, x, index)
        width = width_factor * p.bankfull_width + p.bankfull_width
        width = np.maximum(width, p.bankfull_width_min)

        curvature = self._evaluate(p.curvature, arc_radians, x, index)
        if p.xs_shape == "AU" and p.curvature:
            # The asymmetric section leans into the bend, so it needs the analytical
            # curvature of the sine that defines it, not only its value.
            a, b, c = p.curvature[0].arguments[:3]
            first = a * b * np.cos(b * arc_radians + c)
            second = -a * b * b * np.sin(b * arc_radians + c)
            curvature = curvature + second / (1.0 + first ** 2) ** 1.5

        # Direction cosines of the centreline, for placing cross-section points normal to it.
        with np.errstate(invalid="ignore", divide="ignore"):
            dx = np.diff(x, prepend=x[0]) / step_for_direction
            dy = np.diff(centreline, prepend=centreline[0]) / step_for_direction
        if n > 1:
            dx[0], dy[0] = dx[1], dy[1]
        dx = np.nan_to_num(dx, nan=1.0)
        dy = np.nan_to_num(dy, nan=0.0)

        sinuosity = arc[-1] / x[-1] if x[-1] else 1.0
        channel_slope = self._channel_slope(arc, curvature, sinuosity, p.valley_slope)

        depth = p.bankfull_depth
        if depth <= 0:
            # Regime relation: the depth that just mobilises D50 at the channel slope.
            depth = 165.0 * p.d50 * p.tau_cr / channel_slope if channel_slope else 1.0
            self.logger.info("   >> bankfull depth from D50 and the Shields criterion: "
                             "%.3f", depth)
            if depth > p.bankfull_width:
                # The relation is inversely proportional to slope, so a gentle valley and a
                # coarse bed give a depth greater than the width - which is not a river.
                # The original produced it silently; say so instead.
                self.logger.info(
                    "      * that is deeper than the channel is wide (%.3f). The regime "
                    "relation needs a steep slope or a fine bed; give an explicit bankfull "
                    "depth instead.", p.bankfull_width)
                self.error = True

        thalweg_factor = self._evaluate(p.thalweg, arc_radians, x, index)
        thalweg = depth * (thalweg_factor + depth) + arc * channel_slope + p.datum
        flat = thalweg - (arc - arc[0]) * channel_slope

        top = np.empty(n)
        top[0] = flat.max() + depth
        for i in range(1, n):
            top[i] = top[i - 1] + (arc[i] - arc[i - 1]) * p.valley_slope
        depths = top - thalweg

        offsets = self._cross_section_offsets(p.xs_points)
        normal = offsets[None, :] * width[:, None] / 2.0
        xs_x = x[:, None] - normal * dy[:, None]
        xs_y = centreline[:, None] + normal * dx[:, None]
        xs_z = self._cross_section(offsets, normal, width, depths, top, curvature)

        self.geometry = {
            "x": x, "centreline": centreline, "arc_length": arc,
            "bankfull_width": width, "curvature": curvature,
            "thalweg": thalweg, "top_of_bank": top, "bankfull_depth": depths,
            "channel_slope": channel_slope, "sinuosity": sinuosity,
            "depth": depth,
            "xs_x": xs_x, "xs_y": xs_y, "xs_z": xs_z,
            "dx": dx, "dy": dy, "index": index, "radians": radians,
        }
        self._add_benches()
        return self.geometry

    @staticmethod
    def _channel_slope(arc, curvature, sinuosity, valley_slope):
        """Channel slope: the trend of curvature along the reach, plus the valley component.

        The second term is the one that matters physically. A meandering channel is longer
        than the valley it runs down, so it falls the same height over a greater distance
        and its slope is the valley slope divided by the sinuosity. Dropping it leaves a
        channel that barely falls at all, and - because the regime depth is inversely
        proportional to this slope - an absurd bankfull depth with it.
        """
        n = arc.size
        denominator = n * np.sum(arc ** 2) - np.sum(arc) ** 2
        regression = 0.0
        if denominator != 0:
            regression = (n * np.sum(arc * curvature) - np.sum(arc) * np.sum(curvature)) \
                / denominator
        return float(regression + (valley_slope / sinuosity if sinuosity else valley_slope))

    @staticmethod
    def _cross_section_offsets(xs_points):
        """Normalised offsets from -1 (left bank) to +1 (right bank).

        An even number of points leaves out the centre, as the original did, so the
        thalweg is not double-sampled.
        """
        step = 1.0 / math.floor(xs_points / 2)
        offsets = np.round(np.arange(-1.0, 1.0 + step / 2, step), 5)
        if xs_points % 2 == 0:
            offsets = offsets[offsets != 0.0]
        return offsets

    def _cross_section(self, offsets, normal, width, depths, top, curvature):
        """Bed elevation across the channel, for the chosen shape."""
        shape = self.parameters.xs_shape
        top_column = top[:, None]
        depth_column = depths[:, None]

        if shape == "SU":
            # A symmetric parabola-like U: full depth at the centre, bank top at the edges.
            return top_column - depth_column * np.sqrt(
                np.clip(1.0 - offsets[None, :] ** 2, 0.0, None))

        if shape == "AU":
            # Asymmetric: the deep part shifts to the outside of the bend. b in (0, 1) is
            # where the deepest point sits across the section, and k follows from it.
            peak = np.abs(curvature).max() * 1.2 or 1.0
            b = 0.5 * (1.0 + curvature / peak)
            b = np.clip(b, 1e-6, 1 - 1e-6)
            k = np.where(curvature < 0, -np.log(2) / np.log(b),
                         -np.log(2) / np.log(1 - b))[:, None]
            with np.errstate(invalid="ignore", divide="ignore"):
                fraction = np.clip((width[:, None] / 2 - normal) / width[:, None],
                                   1e-9, 1.0)
                inner = np.where(curvature[:, None] > 0, fraction, 1.0 - fraction) ** k
                return top_column - 4.0 * depth_column * inner * (1.0 - inner)

        # Trapezoid: a flat base of `trapezoid_base` points, with sloped sides to the banks.
        points = offsets.size
        base = int(np.clip(self.parameters.trapezoid_base, 0, points))
        half = points / 2.0
        distance = np.abs(offsets)[None, :]
        edge = base / points if points else 0.0
        with np.errstate(invalid="ignore", divide="ignore"):
            ramp = np.clip((distance - edge) / (1.0 - edge), 0.0, 1.0) if edge < 1 \
                else np.zeros_like(distance)
        return top_column - depth_column * (1.0 - ramp)

    def _add_benches(self):
        """Floodplain and terrace points either side of the channel, when they have width."""
        p = self.parameters
        g = self.geometry
        if p.floodplain_width <= 0 and p.terrace_width <= 0:
            g["bench_x"] = np.empty((g["x"].size, 0))
            g["bench_y"] = np.empty((g["x"].size, 0))
            g["bench_z"] = np.empty((g["x"].size, 0))
            return

        index, x, radians = g["index"], g["x"], g["radians"]
        right_wave = self._evaluate(p.right_floodplain, radians, x, index)
        left_wave = self._evaluate(p.left_floodplain, radians, x, index)

        half = g["bankfull_width"] / 2.0
        top = g["top_of_bank"]
        columns_x, columns_y, columns_z = [], [], []

        def bench(offset, elevation):
            columns_x.append(x - offset * g["dy"])
            columns_y.append(g["centreline"] + offset * g["dx"])
            columns_z.append(elevation)

        if p.floodplain_width > 0:
            toe = half + p.floodplain_width / 2.0
            bench(toe + right_wave, top + p.floodplain_outer_height)
            bench(-(toe + left_wave), top + p.floodplain_outer_height)
        if p.terrace_width > 0:
            crest = half + p.floodplain_width / 2.0 + p.terrace_width / 2.0
            height = top + p.floodplain_outer_height + p.terrace_outer_height
            bench(crest + right_wave, height)
            bench(-(crest + left_wave), height)
        if p.boundary_width > 0:
            edge = (half + p.floodplain_width / 2.0 + p.terrace_width / 2.0
                    + p.boundary_width)
            height = top + p.floodplain_outer_height + p.terrace_outer_height
            bench(edge, height)
            bench(-edge, height)

        g["bench_x"] = np.column_stack(columns_x)
        g["bench_y"] = np.column_stack(columns_y)
        g["bench_z"] = np.column_stack(columns_z)

    # ---------------------------------------------------------------------- output

    def point_cloud(self):
        """Every generated point as ``(x, y, z)`` columns."""
        if self.geometry is None:
            self.build()
        g = self.geometry
        x = np.concatenate([g["xs_x"].ravel(), g["bench_x"].ravel()])
        y = np.concatenate([g["xs_y"].ravel(), g["bench_y"].ravel()])
        z = np.concatenate([g["xs_z"].ravel(), g["bench_z"].ravel()])
        finite = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
        return np.column_stack([x[finite], y[finite], z[finite]])

    def to_raster(self, path=None, cell_size=1.0, crs=None):
        """Triangulate the point cloud onto a regular grid and write a GeoTIFF.

        The original built an ArcGIS TIN and sampled it, which needed a 3D Analyst licence.
        A Delaunay triangulation with linear interpolation is the same surface;
        :class:`scipy.interpolate.LinearNDInterpolator` returns NaN outside the convex hull,
        which is exactly the clip to the valley boundary that the original did with a
        soft-clip polygon.

        Args:
            path (str): where to write. Optional; without it only the array is returned.
            cell_size (float): output resolution in the parameters' length unit.
            crs (str): coordinate reference system to tag the raster with.

        Returns:
            tuple: ``(dem, profile)``.
        """
        from affine import Affine
        from scipy.interpolate import LinearNDInterpolator

        points = self.point_cloud()
        if points.shape[0] < 3:
            raise ValueError("too few points to build a surface")

        x_min, y_min = points[:, 0].min(), points[:, 1].min()
        x_max, y_max = points[:, 0].max(), points[:, 1].max()
        width = max(int(np.ceil((x_max - x_min) / cell_size)) + 1, 2)
        height = max(int(np.ceil((y_max - y_min) / cell_size)) + 1, 2)

        grid_x, grid_y = np.meshgrid(
            x_min + np.arange(width) * cell_size,
            y_max - np.arange(height) * cell_size)
        dem = LinearNDInterpolator(points[:, :2], points[:, 2])(grid_x, grid_y)

        profile = {
            "driver": "GTiff", "height": height, "width": width, "count": 1,
            "dtype": "float32", "crs": crs,
            "transform": Affine(cell_size, 0.0, x_min, 0.0, -cell_size, y_max),
        }
        if path:
            raster.write(path, dem, profile)
            self.logger.info("   >> wrote %s (%d x %d cells at %g)", path, width, height,
                             cell_size)
        return dem, profile

    def run(self, output_dir=None, cell_size=1.0, crs=None, write_points=True):
        """Build the valley and write the DEM, a hillshade and the point cloud.

        Returns:
            dict: the geometry summary and the paths written.
        """
        p = self.parameters
        output_dir = output_dir or os.path.join(config.dir_output("RiverBuilder"), p.name)
        os.makedirs(output_dir, exist_ok=True)

        self.build()
        dem_path = os.path.join(output_dir, "%s_dem.tif" % p.name)
        dem, profile = self.to_raster(dem_path, cell_size=cell_size, crs=crs)

        g = self.geometry
        result = {
            "name": p.name,
            "output_dir": output_dir,
            "dem_raster": dem_path,
            "length": float(p.length),
            "stations": int(p.x_resolution),
            "cross_section": p.xs_shape,
            "sinuosity": float(g["sinuosity"]),
            "channel_slope": float(g["channel_slope"]),
            "bankfull_depth": float(g["depth"]),
            "bankfull_width_mean": float(g["bankfull_width"].mean()),
            "thalweg_drop": float(g["thalweg"].max() - g["thalweg"].min()),
            "elevation_range": (float(np.nanmin(dem)), float(np.nanmax(dem))),
            "cells": int(np.isfinite(dem).sum()),
            "area": float(np.isfinite(dem).sum() * cell_size ** 2),
            "area_unit": config.area_unit(self.unit),
        }

        dx, dy = raster.cell_size(profile)
        hillshade_path = os.path.join(output_dir, "%s_hillshade.tif" % p.name)
        raster.write(hillshade_path, self._hillshade(dem, dx, dy), profile)
        result["hillshade_raster"] = hillshade_path

        if write_points:
            points_path = os.path.join(output_dir, "%s_points.csv" % p.name)
            np.savetxt(points_path, self.point_cloud(), delimiter=",",
                       header="X,Y,Z", comments="", fmt="%.4f")
            result["points_csv"] = points_path

        parameters_path = os.path.join(output_dir, "%s_input.txt" % p.name)
        p.write(parameters_path)
        result["parameters_file"] = parameters_path

        self.logger.info("   >> %s: sinuosity %.3f, channel slope %.5f, depth %.2f",
                         p.name, result["sinuosity"], result["channel_slope"],
                         result["bankfull_depth"])
        return result

    @staticmethod
    def _hillshade(dem, dx, dy, azimuth=315.0, altitude=45.0):
        """Standard hillshade, so the generated terrain can be read at a glance."""
        gy, gx = np.gradient(np.nan_to_num(dem, nan=np.nanmean(dem)), abs(dy), abs(dx))
        slope = np.arctan(np.hypot(gx, gy))
        aspect = np.arctan2(-gx, gy)
        zenith = np.radians(90.0 - altitude)
        azimuth = np.radians(360.0 - azimuth + 90.0)
        shaded = (np.cos(zenith) * np.cos(slope)
                  + np.sin(zenith) * np.sin(slope) * np.cos(azimuth - aspect))
        return np.where(np.isfinite(dem), np.clip(shaded, 0.0, 1.0) * 255.0, np.nan)
