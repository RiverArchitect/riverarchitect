"""Riparian seedling recruitment potential: the Recruitment Box Model.

The open-source replacement for the ArcGIS ``RiparianRecruitment`` module. Cottonwood and
willow seedlings establish only where four things happen in the right order over a single
season, and this maps where all four coincide:

============================  =====================================================
Objective                     Question
============================  =====================================================
Bed preparation               did a winter flow mobilise the bed, clearing a seedbed?
Recession rate (desiccation)  did the water table drop slowly enough for roots to follow?
Prolonged inundation          did the seedling stay under water long enough to drown?
Scour                         did a later flow uproot it?
============================  =====================================================

Each is scored 1 (good), 0.5 (stressed) or 0 (fatal), and the recruitment potential is their
**product** - a seedling has to survive every one of them, so a zero anywhere is a zero
overall. That is the model of Braatne et al. (2007) as the original implemented it.

What it needs
-------------
A **daily flow record** for the season in question, which is the input the other modules do
not use: bed preparation, recession and scour are all about *when* flows happened, not just
which flows are possible. Pass it as a two-column table of date and mean daily discharge.

Relation to the original
------------------------
The original tracked recession and inundation by looping day by day over the flow record and
rebuilding an ArcGIS raster per day. The same loop is here, but a day costs one numpy array
operation, and the water surface for a day's discharge is linearly interpolated between the
two bracketing modelled discharges rather than re-interpolated from points each time.
"""

import datetime as dt
import logging
import os

import numpy as np

from . import config, raster, shear
from .condition import Condition, discharge_token
# Reading a daily flow record lives in `flows`; it is re-exported here because this module
# was the first to need one and callers import it from here. One implementation, not two.
from .flows import read_flow_series
from .preprocessing import water_level_elevation

__all__ = ["RecruitmentParameters", "RecruitmentPotential", "read_flow_series"]

logger = logging.getLogger("riverarchitect")

#: Relative grain density, as in :mod:`riverarchitect.shear`.
RHO_RATIO = shear.RHO_RATIO
#: Centimetres per foot and per metre, for the recession-rate thresholds.
CM_PER_FOOT = 30.48
CM_PER_METRE = 100.0


class RecruitmentParameters:
    """Species and threshold values for the recruitment model.

    Defaults reproduce the Fremont Cottonwood template of the original
    ``recruitment_parameters.xlsx``. Dates carry a year that is ignored: only month and day
    matter, and the analysis year is chosen per run.

    Args:
        seed_start, seed_end (date): the seed dispersal window.
        baseflow_start (date): when the recession ends and baseflow begins.
        bed_prep_years (int): how many years back a bed-preparing flow still counts.
        tau_cr_full, tau_cr_partial (float): dimensionless bed shear stress above which the
            bed counts as fully or partially mobilised.
        recession_stress, recession_lethal (float): water table decline in cm/day that
            stresses or kills a seedling.
        inundation_stress, inundation_lethal (int): days of inundation that stress or kill.
        band_lower, band_upper (float): optional elevation band above the baseflow water
            surface, in cm, to restrict recruitment to.
    """

    def __init__(self, species="Fremont Cottonwood",
                 seed_start=(5, 2), seed_end=(6, 20), baseflow_start=(9, 15),
                 bed_prep_years=1, tau_cr_full=0.047, tau_cr_partial=0.03,
                 recession_stress=2.5, recession_lethal=5.0,
                 inundation_stress=14, inundation_lethal=28,
                 band_lower=None, band_upper=None):
        self.species = species
        self.seed_start = seed_start
        self.seed_end = seed_end
        self.baseflow_start = baseflow_start
        self.bed_prep_years = int(bed_prep_years)
        self.tau_cr_full = float(tau_cr_full)
        self.tau_cr_partial = float(tau_cr_partial)
        self.recession_stress = float(recession_stress)
        self.recession_lethal = float(recession_lethal)
        self.inundation_stress = int(inundation_stress)
        self.inundation_lethal = int(inundation_lethal)
        self.band_lower = band_lower
        self.band_upper = band_upper

    @classmethod
    def from_workbook(cls, path=None):
        """Read the parameters from a ``recruitment_parameters.xlsx``."""
        import openpyxl

        path = path or os.path.join(config.templates_dir(), "recruitment_parameters.xlsx")
        sheet = openpyxl.load_workbook(path, data_only=True).active

        def value(row, column=3):
            return sheet.cell(row, column).value

        def as_month_day(row):
            raw = value(row)
            if isinstance(raw, dt.datetime):
                return raw.month, raw.day
            if isinstance(raw, dt.date):
                return raw.month, raw.day
            return None

        def as_float(row):
            raw = value(row)
            try:
                return float(raw)
            except (TypeError, ValueError):
                return None

        kwargs = {"species": value(2) or "unnamed"}
        for row, key in ((5, "seed_start"), (6, "seed_end"), (7, "baseflow_start")):
            parsed = as_month_day(row)
            if parsed:
                kwargs[key] = parsed
        for row, key in ((8, "bed_prep_years"), (12, "tau_cr_full"), (13, "tau_cr_partial"),
                         (15, "recession_stress"), (16, "recession_lethal"),
                         (18, "inundation_stress"), (19, "inundation_lethal"),
                         (21, "band_lower"), (22, "band_upper")):
            parsed = as_float(row)
            if parsed is not None:
                kwargs[key] = parsed
        return cls(**kwargs)

    def date_in(self, year, month_day):
        return dt.date(int(year), int(month_day[0]), int(month_day[1]))

    def __repr__(self):
        return "RecruitmentParameters(%r)" % self.species


class RecruitmentPotential:
    """Recruitment box model for one condition and one season.

    Args:
        condition (Condition or str): the condition, or its name.
        flow_series (dict or str): ``{date: discharge}``, or a path to read one from.
        year (int): the season to analyse. Defaults to the last year in the record.
        parameters (RecruitmentParameters): thresholds. Defaults to the template values.
        unit (str): ``"us"`` or ``"si"``; must match the condition's rasters.
        manning_n (float): Manning's n in s/m^(1/3), for the shear stress.
        existing_vegetation (str): optional raster; cells that already carry vegetation are
            excluded from the recruitment area.
        grading_extent (str): optional raster of graded areas, which count as bed-prepared.

    Attributes:
        error (bool): True when a step could not be completed.
    """

    def __init__(self, condition, flow_series, year=None, parameters=None, unit="us",
                 manning_n=0.0473934, existing_vegetation=None, grading_extent=None):
        self.condition = condition if isinstance(condition, Condition) \
            else Condition(condition)
        self.flow_series = read_flow_series(flow_series) \
            if isinstance(flow_series, str) else dict(sorted(flow_series.items()))
        if not self.flow_series:
            raise ValueError("the flow record is empty")

        self.parameters = parameters or RecruitmentParameters()
        self.unit = str(unit).lower()
        self.n = manning_n / 1.49 if self.unit == "us" else manning_n
        self.g = 9.81 / config.FT2M if self.unit == "us" else 9.81
        self.cm_per_length = CM_PER_FOOT if self.unit == "us" else CM_PER_METRE
        self.existing_vegetation = existing_vegetation
        self.grading_extent = grading_extent
        self.logger = logger
        self.error = False

        self.year = int(year) if year else max(self.flow_series).year

        self._depth = {}
        self._velocity = {}
        for name in self.condition.all_depth_rasters():
            discharge = self.condition.discharge_of(name)
            if discharge is not None:
                self._depth[discharge] = self.condition.path(name)
        for name in self.condition.all_velocity_rasters():
            discharge = self.condition.discharge_of(name)
            if discharge is not None:
                self._velocity[discharge] = self.condition.path(name)

        self.discharges = sorted(set(self._depth) & set(self._velocity))
        if not self.discharges:
            raise ValueError("condition %r has no paired depth and velocity rasters.\n\n%s"
                             % (self.condition.name, self.condition.describe()))

        self._reference = raster.profile_of(self._depth[self.discharges[0]])
        self._dem = None
        self._wle_cache = {}
        self._q_mobile_cache = {}              # tau_cr -> q_mobile raster
        self._taux_cache = {}                  # discharge token -> theta84
        self._shear_diagnostics = {}           # discharge token -> (h_over_ks, regime)

    # ------------------------------------------------------------------- terrain

    @property
    def dem(self):
        """The DEM, on the reference grid."""
        if self._dem is None:
            path = self.condition.path(self.condition.dem_raster)
            if not path or not os.path.isfile(path):
                raise FileNotFoundError("condition %r has no DEM" % self.condition.name)
            array, profile = raster.read(path)
            self._dem = raster.align(array, profile, self._reference)
        return self._dem

    def _read(self, name):
        if not name:
            return None
        path = name if os.path.isfile(str(name)) else self.condition.path(name)
        if not path or not os.path.isfile(path):
            return None
        array, profile = raster.read(path)
        return raster.align(array, profile, self._reference)

    def wle_at(self, discharge):
        """Water surface elevation of a modelled discharge, interpolated across the reach."""
        if discharge in self._wle_cache:
            return self._wle_cache[discharge]
        surface, _profile = water_level_elevation(
            self.condition.path(self.condition.dem_raster), self._depth[discharge], step=2)
        self._wle_cache[discharge] = surface
        return surface

    def wle_for(self, discharge):
        """Water surface for any discharge, linearly interpolated between modelled ones.

        A daily flow record contains discharges the 2D model never ran. The original
        interpolated the stage between the bracketing modelled discharges; so does this.
        """
        modelled = self.discharges
        if discharge <= modelled[0]:
            return self.wle_at(modelled[0])
        if discharge >= modelled[-1]:
            return self.wle_at(modelled[-1])

        index = int(np.searchsorted(modelled, discharge))
        low, high = modelled[index - 1], modelled[index]
        if high == low:
            return self.wle_at(low)
        weight = (discharge - low) / (high - low)
        return self.wle_at(low) * (1.0 - weight) + self.wle_at(high) * weight

    # ----------------------------------------------------------- bed mobilisation

    def shields_stress(self, depth, velocity, grain, token=None):
        """Dimensionless bed shear stress ``theta84``, as :mod:`riverarchitect.lifespan`.

        The regime-aware closure of :mod:`riverarchitect.shear` replaces the Keulegan-only
        expression of the original. When ``token`` is given, the relative submergence and
        regime rasters of that discharge are kept for :meth:`run` to write.
        """
        result = shear.calculate_taux(velocity, depth, shear.d84_of(grain),
                                      gravity=self.g)
        if token is not None:
            self._shear_diagnostics[token] = (result.h_over_ks, result.regime)
            self.logger.info("   >> taux %s: %s", token,
                             ", ".join("%s %d" % (label, count) for label, count
                                       in shear.regime_summary(result.regime).items()))
            if not result.regime.any():
                self.logger.warning(
                    "   >> taux %s is NoData everywhere: the grain raster %r "
                    "(values %g to %g) may not share units or extent with the "
                    "hydraulic rasters.", token, self.condition.grain_raster,
                    np.nanmin(grain) if np.isfinite(grain).any() else float("nan"),
                    np.nanmax(grain) if np.isfinite(grain).any() else float("nan"))
        return result.theta84

    def q_mobile(self, tau_cr):
        """Lowest modelled discharge at which each cell's bed becomes mobile.

        NoData where no modelled discharge mobilises the cell, which reads as "never
        prepared" downstream. Memoized: bed preparation and scour both ask for the same
        two thresholds, and each pass runs the shear closure over every discharge.
        """
        if tau_cr in self._q_mobile_cache:
            return self._q_mobile_cache[tau_cr]

        grain = self._read(self.condition.grain_raster)
        if grain is None:
            raise FileNotFoundError("condition %r has no grain size raster"
                                    % self.condition.name)

        per_discharge = []
        for discharge in self.discharges:
            token = discharge_token(discharge)
            taux = self._taux_cache.get(token)
            if taux is None:
                depth, depth_profile = raster.read(self._depth[discharge])
                velocity, velocity_profile = raster.read(self._velocity[discharge])
                depth = raster.align(depth, depth_profile, self._reference)
                velocity = raster.align(velocity, velocity_profile, self._reference)
                depth = np.where(depth > 0, depth, np.nan)
                taux = self.shields_stress(depth, velocity, grain, token=token)
                self._taux_cache[token] = taux
            per_discharge.append(raster.con(taux >= tau_cr, float(discharge)))

        if self._shear_diagnostics and not any(
                regime.any() for _hks, regime in self._shear_diagnostics.values()):
            raise ValueError(
                "the dimensionless bed shear stress is NoData everywhere, at every "
                "discharge. Check that the grain raster %r holds grain diameters in the "
                "condition's length unit and shares the extent of the hydraulic rasters."
                % self.condition.grain_raster)

        result = raster.cell_statistics(per_discharge, "MINIMUM")
        self._q_mobile_cache[tau_cr] = result
        return result

    # --------------------------------------------------------------- crop area

    def crop_area(self):
        """Where recruitment is possible at all.

        Either the elevation band above the baseflow water surface, when the parameters give
        one, or the area between the lowest and highest wetted extent during seed dispersal -
        seeds only land where the water reached.
        """
        seed_start = self.parameters.date_in(self.year, self.parameters.seed_start)
        seed_end = self.parameters.date_in(self.year, self.parameters.seed_end)
        window = {date: q for date, q in self.flow_series.items()
                  if seed_start <= date <= seed_end}
        if not window:
            raise ValueError("the flow record covers no day of the %d seed dispersal window"
                             % self.year)

        if self.parameters.band_lower is not None and self.parameters.band_upper is not None:
            baseflow_date = self.parameters.date_in(self.year, self.parameters.baseflow_start)
            discharge = self.flow_series.get(
                baseflow_date, self.flow_series[min(self.flow_series,
                                                    key=lambda d: abs(d - baseflow_date))])
            above = self.dem - self.wle_for(discharge)
            lower = self.parameters.band_lower / self.cm_per_length
            upper = self.parameters.band_upper / self.cm_per_length
            with np.errstate(invalid="ignore"):
                return (above >= lower) & (above <= upper)

        low_surface = self.wle_for(min(window.values()))
        high_surface = self.wle_for(max(window.values()))
        with np.errstate(invalid="ignore"):
            return (self.dem <= high_surface) & (self.dem >= low_surface)

    # --------------------------------------------------------------- objectives

    def bed_preparation(self, crop):
        """Objective 1: did a flow in the bed preparation period mobilise the seedbed?"""
        end = self.parameters.date_in(self.year, self.parameters.seed_start)
        start = dt.date(self.year - self.parameters.bed_prep_years,
                        *self.parameters.seed_start)
        window = [q for date, q in self.flow_series.items() if start <= date < end]
        if not window:
            self.logger.info("      * no flow record in the bed preparation period")
            self.error = True
            return raster.con(crop, 0.0)
        peak = max(window)
        self.logger.info("   >> bed preparation: peak discharge %.0f", peak)

        full = self.q_mobile(self.parameters.tau_cr_full)
        partial = self.q_mobile(self.parameters.tau_cr_partial)
        with np.errstate(invalid="ignore"):
            score = np.where(np.nan_to_num(full, nan=np.inf) <= peak, 1.0,
                             np.where(np.nan_to_num(partial, nan=np.inf) <= peak, 0.5, 0.0))

        graded = self._read(self.grading_extent)
        if graded is not None:
            # Graded ground has been mechanically prepared, so it counts as fully prepared.
            score = np.where(np.isfinite(graded), 1.0, score)
        return raster.con(crop, score)

    def recession_and_inundation(self, crop):
        """Objectives 2 and 3, tracked in a single pass over the flow record.

        Both need the same day-by-day walk: the recession rate is how fast the water surface
        drops at a cell, and the inundation count is how long it stays under water.

        Three details decide the result, and all three follow the original
        (``cRecruitmentPotential.rec_inund_survival``):

        * a stressful or lethal recession day is only counted where the cell is **dry** that
          day. While a cell is still submerged its seedling is not desiccating, however fast
          the surface is dropping;
        * a cell that goes dry during seed dispersal starts again from there - that is when
          its seed actually landed - so both the counts and the denominator are per cell;
        * the inundation objective uses the longest run of **consecutive** submerged days,
          not their total. Fourteen days under water in one stretch drowns a seedling;
          fourteen days spread over a season does not.

        Returns:
            tuple: ``(desiccation, inundation, mortality)`` rasters, cropped.
        """
        seed_start = self.parameters.date_in(self.year, self.parameters.seed_start)
        seed_end = self.parameters.date_in(self.year, self.parameters.seed_end)
        baseflow = self.parameters.date_in(self.year, self.parameters.baseflow_start)

        days = [date for date in self.flow_series
                if seed_start - dt.timedelta(days=3) <= date <= baseflow]
        if len(days) < 5:
            raise ValueError("the flow record has too few days in the %d recession period"
                             % self.year)

        recession_days = sum(1 for date in days if date >= seed_start)
        if recession_days == 0:
            raise ValueError("no day falls in the %d recession period" % self.year)

        shape = self.dem.shape
        stress_days = np.zeros(shape, dtype="float64")
        lethal_days = np.zeros(shape, dtype="float64")
        # Per-cell denominator, reset when a cell goes dry during seed dispersal.
        tracked_days = np.full(shape, float(recession_days))
        consecutive = np.zeros(shape, dtype="float64")
        longest_inundation = np.zeros(shape, dtype="float64")

        window = []
        dry = None
        elapsed = 0
        for date in days:
            surface = self.wle_for(self.flow_series[date])
            window.append(surface)
            if len(window) > 4:
                window.pop(0)

            with np.errstate(invalid="ignore"):
                submerged = surface > self.dem
            was_dry = np.ones(shape, dtype=bool) if dry is None else dry
            dry = ~submerged

            if date <= seed_end:
                # The seed of a cell settles when the water leaves it, so everything before
                # that is another cell's history, not this one's.
                just_dried = (~was_dry) & dry
                if just_dried.any():
                    tracked_days = np.where(just_dried,
                                            max(recession_days - elapsed, 1), tracked_days)
                    stress_days = np.where(just_dried, 0.0, stress_days)
                    lethal_days = np.where(just_dried, 0.0, lethal_days)
                    longest_inundation = np.where(just_dried, 0.0, longest_inundation)

            if len(window) == 4 and date >= seed_start:
                # Three-day moving average of the daily drop, converted to cm/day. Positive
                # means the water surface is falling.
                drop = (window[0] - window[-1]) / 3.0 * self.cm_per_length
                with np.errstate(invalid="ignore"):
                    stress_days += np.where(
                        dry & (drop >= self.parameters.recession_stress)
                        & (drop < self.parameters.recession_lethal), 1.0, 0.0)
                    lethal_days += np.where(
                        dry & (drop >= self.parameters.recession_lethal), 1.0, 0.0)

            consecutive = np.where(dry, 0.0, consecutive + 1.0)
            longest_inundation = np.maximum(longest_inundation, consecutive)
            if date >= seed_start:
                elapsed += 1

        # Mortality coefficient of Braatne et al. (2007): lethal days weigh three times as
        # much as stressful ones.
        stress_percent = stress_days / tracked_days * 100.0
        lethal_percent = lethal_days / tracked_days * 100.0
        mortality = (lethal_percent * 3.0 + stress_percent) / 3.0

        desiccation = np.where(mortality > 30.0, 0.0,
                               np.where(mortality >= 20.0, 0.5, 1.0))
        # Strictly greater than the lethal count, as the original had it: a cell submerged
        # for exactly the lethal number of days is stressed, not dead.
        inundation = np.where(longest_inundation > self.parameters.inundation_lethal, 0.0,
                              np.where(longest_inundation >= self.parameters.inundation_stress,
                                       0.5, 1.0))

        self.logger.info("   >> recession tracked over %d day(s) of %d; longest inundation "
                         "%d day(s)", recession_days, len(days),
                         int(np.nanmax(longest_inundation)) if longest_inundation.size else 0)
        return (raster.con(crop, desiccation), raster.con(crop, inundation),
                raster.con(crop, mortality))

    def scour_survival(self, crop):
        """Objective 4: did a flow after seed dispersal uproot the seedling?"""
        seed_end = self.parameters.date_in(self.year, self.parameters.seed_end)
        baseflow = self.parameters.date_in(self.year, self.parameters.baseflow_start)
        window = [q for date, q in self.flow_series.items() if seed_end < date <= baseflow]
        if not window:
            self.logger.info("      * no flow record after seed dispersal - assuming no scour")
            return raster.con(crop, 1.0)
        peak = max(window)
        self.logger.info("   >> scour: peak discharge after seed dispersal %.0f", peak)

        full = self.q_mobile(self.parameters.tau_cr_full)
        partial = self.q_mobile(self.parameters.tau_cr_partial)
        with np.errstate(invalid="ignore"):
            score = np.where(np.nan_to_num(full, nan=np.inf) <= peak, 0.0,
                             np.where(np.nan_to_num(partial, nan=np.inf) <= peak, 0.5, 1.0))
        return raster.con(crop, score)

    # ------------------------------------------------------------------------ run

    def run(self, output_dir=None, write_rasters=True):
        """Run all four objectives and combine them.

        Returns:
            dict: the area at each recruitment potential level, the per-objective areas and
            the paths written.
        """
        output_dir = output_dir or os.path.join(
            config.dir_output("RiparianRecruitment"),
            "%s_%d" % (self.condition.name, self.year))
        if write_rasters:
            os.makedirs(output_dir, exist_ok=True)

        self.logger.info("\nRIPARIAN RECRUITMENT - %s, %d", self.parameters.species,
                         self.year)
        crop = self.crop_area()
        vegetation = self._read(self.existing_vegetation)
        if vegetation is not None:
            # Ground already vegetated cannot recruit a new seedling.
            crop = crop & ~np.isfinite(vegetation)
        self.logger.info("   >> recruitment area: %d cell(s)", int(crop.sum()))

        bed = self.bed_preparation(crop)
        desiccation, inundation, mortality = self.recession_and_inundation(crop)
        scour = self.scour_survival(crop)

        with np.errstate(invalid="ignore"):
            potential = bed * desiccation * inundation * scour

        dx, dy = raster.cell_size(self._reference)
        cell_area = dx * dy

        layers = {"bed_preparation": bed, "desiccation_survival": desiccation,
                  "inundation_survival": inundation, "scour_survival": scour,
                  "mortality_coefficient": mortality,
                  "recruitment_potential": potential}
        written = {}
        if write_rasters:
            for name, array in layers.items():
                path = os.path.join(output_dir, "%s.tif" % name)
                raster.write(path, array, self._reference)
                written[name] = path
            # Shear diagnostics: which resistance closure the Shields stress used where.
            for token, (h_over_ks, regime) in self._shear_diagnostics.items():
                path = os.path.join(output_dir, "hks%s.tif" % token)
                raster.write(path, h_over_ks, self._reference)
                written["hks%s" % token] = path
                path = os.path.join(output_dir, "regime%s.tif" % token)
                raster.write(path, regime, self._reference, dtype="uint8", nodata=0)
                written["regime%s" % token] = path

        def area_of(array, low, high=None):
            with np.errstate(invalid="ignore"):
                mask = (array >= low) if high is None else ((array >= low) & (array < high))
            return float((mask & np.isfinite(array)).sum() * cell_area)

        result = {
            "condition": self.condition.name,
            "species": self.parameters.species,
            "year": self.year,
            "area_unit": config.area_unit(self.unit),
            "crop_area": float(crop.sum() * cell_area),
            "recruitment_area": area_of(potential, 1.0),
            "partial_area": area_of(potential, 0.125, 1.0),
            "objectives": {name: area_of(layers[name], 1.0)
                           for name in ("bed_preparation", "desiccation_survival",
                                        "inundation_survival", "scour_survival")},
            "rasters": written,
        }
        if write_rasters:
            result["output_dir"] = output_dir
        self.logger.info("   >> full recruitment potential: %.0f %s",
                         result["recruitment_area"], result["area_unit"])
        return result
