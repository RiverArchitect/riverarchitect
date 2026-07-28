"""Fish stranding risk from wetted areas that disconnect as a hydrograph recedes.

The open-source replacement for the ArcGIS ``StrandingRisk`` module. As discharge falls the
wetted area shrinks and breaks apart; pools that lose their connection to the main channel
trap fish. That is a connected-component problem: threshold the depth raster at the minimum
swimming depth of the species and lifestage in question, label the wetted regions, and every
region except the one still joined to the main channel is a stranding risk.

Outputs
-------
* one ``disconnected_<Q>.tif`` per discharge;
* ``Q_disconnect.tif`` - the highest discharge at which each cell was disconnected, i.e. the
  flow at which that spot becomes a trap as the hydrograph recedes;
* a polygon layer of the individual pools at the worst discharge;
* a per-discharge table of wetted area, stranded area and pool count.

Relation to the original
------------------------
The original built a least-cost "escape route" raster per discharge and called a cell
disconnected when no route reached the low-flow polygon. With the depth threshold applied
first, that reduces to the connectivity rule implemented here and in
:func:`riverarchitect.raster.disconnected_mask`: keep the largest wetted region, everything
else is stranded. The velocity criterion of the original (a fish cannot swim upstream faster
than ``u_max``) is not applied; see :attr:`StrandingRisk.velocity_limited` for the flag that
records this.
"""

import logging
import os

import numpy as np

from . import config, raster
from .condition import Condition

__all__ = ["TRAVEL_THRESHOLDS", "StrandingRisk"]

logger = logging.getLogger("riverarchitect")

#: Minimum swimming depth and maximum swimming speed per species and lifestage, in U.S.
#: customary units, reproducing the defaults of the original ``Fish.xlsx``.
TRAVEL_THRESHOLDS = {
    ("Chinook salmon", "fry"): {"h_min": 0.2, "u_max": 1.9},
    ("Chinook salmon", "juvenile"): {"h_min": 0.3, "u_max": 1.9},
    ("Chinook salmon", "adult"): {"h_min": 0.9, "u_max": 11.0},
}


class StrandingRisk:
    """Connectivity analysis over a receding hydrograph.

    Args:
        condition (Condition or str): the condition, or its name.
        discharges (list): discharges to walk, highest first. Defaults to every hydraulic
            raster in the condition, sorted descending.
        h_min (float): minimum swimming depth. Below it a cell does not count as wetted.
        unit (str): ``"us"`` or ``"si"``; must match the condition's rasters.
        connectivity (int): 4 (arcpy's ``RegionGroup`` default) or 8.

    Attributes:
        velocity_limited (bool): always False - the velocity criterion of the original is
            not applied. Recorded so a caller can state it alongside a result.
    """

    velocity_limited = False

    def __init__(self, condition, discharges=None, h_min=0.2, unit="us", connectivity=4):
        self.condition = condition if isinstance(condition, Condition) \
            else Condition(condition)
        self.h_min = float(h_min)
        self.unit = str(unit).lower()
        self.connectivity = int(connectivity)
        self.logger = logger
        self.error = False

        # Scan the folder rather than trusting input_definitions.inp: that file lists only
        # the discharges carrying a flood return period, which is what lifespan mapping
        # needs. A recession analysis needs the low flows, and those are on disk but usually
        # not in the .inp.
        available = {}
        for name in self.condition.all_depth_rasters():
            discharge = self.condition.discharge_of(name)
            if discharge is not None:
                available[discharge] = self.condition.path(name)
        self._available = available

        if discharges is None:
            discharges = sorted(available, reverse=True)
        self.discharges = [float(q) for q in discharges if float(q) in available]
        if not self.discharges:
            raise ValueError("no depth rasters found for condition %r"
                             % self.condition.name)

    @classmethod
    def for_fish(cls, condition, species="Chinook salmon", lifestage="fry", **kwargs):
        """Build with the travel thresholds of a species and lifestage."""
        thresholds = TRAVEL_THRESHOLDS.get((species, lifestage))
        if thresholds is None:
            raise KeyError("no travel thresholds for %s %s" % (species, lifestage))
        kwargs.setdefault("h_min", thresholds["h_min"])
        return cls(condition, **kwargs)

    # -------------------------------------------------------------------------- run

    def run(self, output_dir=None, write_rasters=True):
        """Walk the recession and quantify the disconnected area at each discharge.

        Returns:
            dict: ``per_discharge`` (list of row dicts), ``total_disconnected_area``,
            ``worst_discharge``, ``area_unit`` and the paths written.
        """
        output_dir = output_dir or os.path.join(
            config.dir_output("StrandingRisk"), self.condition.name)
        if write_rasters:
            os.makedirs(output_dir, exist_ok=True)

        reference = raster.profile_of(self._available[self.discharges[0]])
        dx, dy = raster.cell_size(reference)
        cell_area = dx * dy

        rows = []
        per_discharge_masks = []
        for discharge in self.discharges:
            depth, profile = raster.read(self._available[discharge])
            depth = raster.align(depth, profile, reference)
            # nan_to_num keeps NoData out of the comparison rather than propagating it.
            wet = np.nan_to_num(depth) > self.h_min

            mask, pools = raster.disconnected_mask(wet, connectivity=self.connectivity)
            per_discharge_masks.append(raster.con(mask, float(discharge)))

            wetted_area = float(wet.sum() * cell_area)
            stranded_area = float(mask.sum() * cell_area)
            rows.append({
                "discharge": discharge,
                "pools": int(pools),
                "wetted_area": wetted_area,
                "stranded_area": stranded_area,
                "percent_stranded": (100.0 * stranded_area / wetted_area)
                                    if wetted_area else 0.0,
            })

            if write_rasters:
                raster.write(os.path.join(output_dir, "disconnected_%06d.tif" % discharge),
                             raster.con(mask, 1.0), reference)

        result = {
            "condition": self.condition.name,
            "h_min": self.h_min,
            "per_discharge": rows,
            "area_unit": config.area_unit(self.unit),
            "discharge_unit": config.unit_labels(self.unit)["q"],
            "velocity_limited": self.velocity_limited,
        }

        q_disconnect = raster.cell_statistics(per_discharge_masks, "MAXIMUM")
        result["total_disconnected_area"] = float(
            np.isfinite(q_disconnect).sum() * cell_area)

        worst = max(rows, key=lambda row: row["stranded_area"]) if rows else None
        result["worst_discharge"] = worst["discharge"] if worst else None
        result["worst_stranded_area"] = worst["stranded_area"] if worst else 0.0

        if write_rasters:
            path = os.path.join(output_dir, "Q_disconnect.tif")
            raster.write(path, q_disconnect, reference)
            result["q_disconnect_raster"] = path
            result["output_dir"] = output_dir
            if worst:
                pools_path = self.write_pools(worst["discharge"], output_dir, reference)
                if pools_path:
                    result["pools_layer"] = pools_path

        return result

    def write_pools(self, discharge, output_dir, reference=None):
        """Polygonise the disconnected pools at one discharge into a GeoPackage."""
        discharge = float(discharge)
        if discharge not in self._available:
            return None
        reference = reference or raster.profile_of(self._available[self.discharges[0]])

        depth, profile = raster.read(self._available[discharge])
        depth = raster.align(depth, profile, reference)
        mask, _pools = raster.disconnected_mask(np.nan_to_num(depth) > self.h_min,
                                                connectivity=self.connectivity)
        if not mask.any():
            return None

        pools = raster.polygonize(mask.astype("int32"), reference, mask=mask)
        pools["area"] = pools.geometry.area
        pools = pools.sort_values("area", ascending=False)
        path = os.path.join(output_dir, "pools_%06d.gpkg" % discharge)
        try:
            pools.to_file(path, driver="GPKG")
        except Exception as exc:  # a missing vector driver must not lose the rasters
            self.logger.info("      * could not write %s (%s)", path, exc)
            return None
        return path
