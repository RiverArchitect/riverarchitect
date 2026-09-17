"""Threshold-based terrain modification: grading and widening for planting.

The open-source replacement for the threshold-value part of the ArcGIS ``ModifyTerrain``
module (``cModifyTerrain.lower_dem_for_plants``).

The problem it solves
---------------------
A lifespan map says a willow would survive at a cell *if* the water table were within reach
of its roots. Where the ground stands too high above the water table it will not, and the
answer is to lower the ground - grading, or widening the channel into a berm. This computes
the resulting terrain: where a feature is planned and the depth to the water table exceeds
what the feature tolerates, the DEM is lowered by exactly the excess, so that the cell ends
up at the deepest tolerable depth to water and no lower.

.. math::

    z' = \\begin{cases}
        z - (d_{2w} - d_{2w,\\max}) & \\text{where the feature applies and } d_{2w} > d_{2w,\\max} \\\\
        z & \\text{elsewhere}
    \\end{cases}

Features are applied in sequence, and each works on the terrain the previous one left. That
is what the original did, and it matters: lowering the ground also lowers its depth to the
water table, so the second feature must see the first one's excavation rather than the
original DEM.

Pair the result with :mod:`riverarchitect.volume_assessment` to get the earthwork quantity.

Relation to the original
------------------------
The whole of ``lower_dem_for_plants`` reduces to one nested ``Con``, wrapped in a hundred
lines of extent juggling, a cache folder and a four-deep ``try`` ladder that read the
tolerated depth to water from up to four planting features. The ladder is
:func:`planting_depth_limit` here, and it takes the **minimum** of the tolerances, as the
original did - the terrain has to suit the most demanding species planned, not the least.

What is *not* here is ``RiverBuilder``, the synthetic-valley generator that shares the
original's ModifyTerrain tab. It is a separate program with its own input format and is not
part of this package; see the ``River Builder`` page of the legacy wiki.
"""

import logging
import os

import numpy as np

from . import config, raster, tiled, units
from .condition import Condition

__all__ = ["Terraforming", "planting_depth_limit", "DEFAULT_D2W_MAX"]

logger = logging.getLogger("riverarchitect")

#: Depth to the water table used when no planting feature declares one, in feet. The
#: original's fallback, reached through the last ``except`` of its ladder.
DEFAULT_D2W_MAX = 10.0


def planting_depth_limit(features=None, feature_ids=None):
    """Deepest water table the planned plantings can still reach, in the condition's units.

    Args:
        features (dict): feature id -> :class:`riverarchitect.lifespan.Feature`. Defaults to
            :data:`riverarchitect.lifespan.FEATURES`.
        feature_ids (iterable): restrict to these features. Defaults to every feature in the
            *Vegetation plantings* group.

    Returns:
        float: the smallest ``d2w_max`` among them, or :data:`DEFAULT_D2W_MAX` when none of
        them declares one.
    """
    from .lifespan import FEATURES

    features = features or FEATURES
    if feature_ids:
        chosen = [features[fid] for fid in feature_ids if fid in features]
    else:
        chosen = [feature for feature in features.values()
                  if feature.group == "Vegetation plantings"]

    limits = [feature.d2w_max for feature in chosen if feature.d2w_max is not None]
    if not limits:
        logger.info("      * no planting feature declares a depth to water table - using "
                    "the default of %s", DEFAULT_D2W_MAX)
        return DEFAULT_D2W_MAX
    return float(min(limits))


class Terraforming:
    """Lower a DEM so that planned features reach the water table.

    Args:
        condition (Condition or str): the condition, or its name. Supplies ``dem.tif`` and
            ``d2w.tif``.
        action_dir (str): directory holding the ``best_<feature>.tif`` masks of
            :class:`riverarchitect.maxlifespan.MaxLifespan`, which say where each feature is
            planned. Any raster whose finite cells mark an area will do.
        unit (str): ``"si"`` (default) or ``"us"``; must match the condition's rasters,
            which is checked against their CRS.
        strict_units (bool): raise when ``unit`` disagrees with the CRS of the rasters
            rather than warn. Defaults to :data:`riverarchitect.config.UNIT_CHECK`.
        d2w_max (float): deepest tolerable depth to the water table. Defaults to
            :func:`planting_depth_limit`.
        features (list): feature ids to apply, in order. Defaults to every mask found,
            alphabetically.

    Attributes:
        error (bool): True when at least one feature could not be applied.
    """

    def __init__(self, condition, action_dir, unit="si", d2w_max=None, features=None,
                 strict_units=None):
        self.condition = condition if isinstance(condition, Condition) \
            else Condition(condition)
        self.action_dir = str(action_dir)
        if not os.path.isdir(self.action_dir):
            raise FileNotFoundError("no such directory: %s" % self.action_dir)
        self.unit = units.check_unit(unit)
        self.condition.check_units(self.unit, strict_units)
        self.d2w_max = float(d2w_max) if d2w_max is not None else planting_depth_limit()
        self.logger = logger
        self.error = False

        self.actions = self._find_actions(features)
        if not self.actions:
            raise FileNotFoundError(
                "no feature action rasters in %s. Run Max Lifespan first, or point "
                "action_dir at a folder of best_<feature>.tif masks." % self.action_dir)

        for name in (self.condition.dem_raster, self.condition.d2w_raster):
            if not self.condition.exists(name):
                raise FileNotFoundError(
                    "condition %r has no %s raster. Terraforming needs a DEM and a depth "
                    "to water table; build them in Get Started first."
                    % (self.condition.name, name))

        self.reference = raster.profile_of(self.condition.path(self.condition.dem_raster))

    # ------------------------------------------------------------------- inputs

    def _find_actions(self, features):
        """``{feature id: path}`` of the action masks to apply, in application order."""
        import glob

        found = {}
        for path in sorted(glob.glob(os.path.join(self.action_dir, "*.tif"))):
            name = os.path.splitext(os.path.basename(path))[0]
            for prefix in ("best_", "lf_", "ds_"):
                if name.startswith(prefix):
                    found[name[len(prefix):]] = path
                    break
            else:
                found[name] = path

        if features is None:
            return found
        # Preserve the caller's order: features are applied in sequence and each sees the
        # terrain the previous one left.
        return {fid: found[fid] for fid in features if fid in found}

    def _read(self, path):
        array, profile = raster.read(path)
        return raster.align(array, profile, self.reference)

    # ---------------------------------------------------------------------- run

    def apply_feature(self, dem, d2w, action):
        """Lower one feature's cells to the deepest tolerable depth to water.

        Args:
            dem (numpy.ndarray): the terrain to modify.
            d2w (numpy.ndarray): depth to the water table on that terrain.
            action (numpy.ndarray): where the feature is planned; finite and above zero.

        Returns:
            numpy.ndarray: the modified terrain.
        """
        with np.errstate(invalid="ignore"):
            planned = np.isfinite(action) & (np.nan_to_num(action) > 0.0)
            too_high = planned & (d2w > self.d2w_max)
            # Lower by exactly the excess, so the cell lands at d2w_max and no deeper.
            return np.where(too_high, dem - (d2w - self.d2w_max), dem)

    def run(self, output_dir=None, write_rasters=True):
        """Apply every feature in turn and report the terrain change.

        Returns:
            dict: ``per_feature`` rows, the total cut volume, and the paths written.
        """
        output_dir = output_dir or os.path.join(
            config.dir_output("Terraforming"), self.condition.name)
        if write_rasters:
            os.makedirs(output_dir, exist_ok=True)

        dx, dy = raster.cell_size(self.reference)
        cell_area = dx * dy
        layers = len(self.actions) + 10
        if tiled.enabled(self.reference, layers):
            return self._run_blockwise(output_dir, write_rasters, cell_area, layers)

        original = self._read(self.condition.path(self.condition.dem_raster))
        original_d2w = self._read(self.condition.path(self.condition.d2w_raster))
        dem = original.copy()
        rows = []

        for fid, path in self.actions.items():
            try:
                action = self._read(path)
            except Exception as exc:      # a corrupt mask must not lose the others
                self.logger.error("   >> %s: could not read %s (%s)", fid, path, exc)
                self.error = True
                continue

            # Lowering the ground lowers its depth to water by the same amount, so each
            # feature sees what the previous one excavated.
            d2w = original_d2w - (original - dem)
            modified = self.apply_feature(dem, d2w, action)

            with np.errstate(invalid="ignore"):
                cut = np.nan_to_num(dem - modified)
            changed = cut > 0.0
            rows.append({
                "feature": fid,
                "cells": int(changed.sum()),
                "area": float(changed.sum() * cell_area),
                "volume": float(cut.sum() * cell_area),
                "max_cut": float(cut.max()) if changed.any() else 0.0,
            })
            self.logger.info("   >> %-12s lowered %d cell(s), %.0f %s excavated",
                             fid, int(changed.sum()), rows[-1]["volume"],
                             "cubic feet" if self.unit == "us" else "cubic metres")
            dem = modified

        with np.errstate(invalid="ignore"):
            total_cut = np.nan_to_num(original - dem)
        changed = total_cut > 0.0

        result = self._summary(rows, int(changed.sum()), float(total_cut.sum()),
                               float(total_cut.max()) if changed.any() else 0.0, cell_area)

        if write_rasters:
            dem_path = os.path.join(output_dir, "dem_terraformed.tif")
            raster.write(dem_path, dem, self.reference)
            result["dem_raster"] = dem_path

            # Two-argument con: cells that were not touched are NoData, not a zero cut.
            cut_path = os.path.join(output_dir, "cut_depth.tif")
            raster.write(cut_path, raster.con(changed, total_cut), self.reference)
            result["cut_raster"] = cut_path

            d2w_path = os.path.join(output_dir, "d2w_terraformed.tif")
            raster.write(d2w_path, original_d2w - total_cut, self.reference)
            result["d2w_raster"] = d2w_path
            result["output_dir"] = output_dir

        return result

    def _summary(self, rows, modified_cells, cut_sum, max_cut, cell_area):
        return {
            "condition": self.condition.name,
            "d2w_max": self.d2w_max,
            "features": list(self.actions),
            "per_feature": rows,
            "modified_cells": modified_cells,
            "modified_area": float(modified_cells * cell_area),
            "cut_volume": float(cut_sum * cell_area),
            "max_cut": max_cut,
            "area_unit": config.area_unit(self.unit),
            "length_unit": config.unit_labels(self.unit)["length"],
        }

    def _run_blockwise(self, output_dir, write_rasters, cell_area, layers):
        """:meth:`run` for a grid too large to hold, one block at a time."""
        reference = self.reference
        self.logger.info("   >> %d x %d cells exceed the memory budget - processing block "
                         "by block", reference["height"], reference["width"])
        dem_path = self.condition.path(self.condition.dem_raster)
        d2w_path = self.condition.path(self.condition.d2w_raster)
        actions = {}
        for fid, path in self.actions.items():
            try:
                raster.profile_of(path)
            except Exception as exc:      # a corrupt mask must not lose the others
                self.logger.error("   >> %s: could not read %s (%s)", fid, path, exc)
                self.error = True
                continue
            actions[fid] = path

        paths = {"dem_raster": os.path.join(output_dir, "dem_terraformed.tif"),
                 "cut_raster": os.path.join(output_dir, "cut_depth.tif"),
                 "d2w_raster": os.path.join(output_dir, "d2w_terraformed.tif")}
        writers = {key: tiled.Writer(path, reference) for key, path in paths.items()} \
            if write_rasters else {}

        def work(block):
            original = tiled.read(dem_path, reference, block.window)
            original_d2w = tiled.read(d2w_path, reference, block.window)
            if not (np.isfinite(original).any() or np.isfinite(original_d2w).any()):
                return None
            dem = original.copy()
            stats = {}
            for fid, path in actions.items():
                d2w = original_d2w - (original - dem)
                modified = self.apply_feature(dem, d2w, tiled.read(path, reference,
                                                                   block.window))
                with np.errstate(invalid="ignore"):
                    cut = np.nan_to_num(dem - modified)
                changed = cut > 0.0
                stats[fid] = (int(changed.sum()), float(cut.sum()),
                              float(cut.max()) if changed.any() else 0.0)
                dem = modified
            with np.errstate(invalid="ignore"):
                total_cut = np.nan_to_num(original - dem)
            changed = total_cut > 0.0
            if writers:
                writers["dem_raster"].write(block, dem)
                writers["cut_raster"].write(block, raster.con(changed, total_cut))
                writers["d2w_raster"].write(block, original_d2w - total_cut)
            return stats, (int(changed.sum()), float(total_cut.sum()),
                           float(total_cut.max()) if changed.any() else 0.0)

        try:
            parts = [p for p in tiled.map_blocks(work, reference, layers=layers,
                                                 label="terraforming",
                                                 needs=[dem_path, d2w_path])
                     if p is not None]
        finally:
            for writer in writers.values():
                writer.close()

        def merge(items):
            items = list(items)
            return (sum(i[0] for i in items), sum(i[1] for i in items),
                    max((i[2] for i in items), default=0.0))

        rows = []
        for fid in actions:
            cells, cut_sum, max_cut = merge(stats[fid] for stats, _total in parts)
            rows.append({"feature": fid, "cells": cells, "area": float(cells * cell_area),
                         "volume": float(cut_sum * cell_area), "max_cut": max_cut})
            self.logger.info("   >> %-12s lowered %d cell(s), %.0f %s excavated",
                             fid, cells, rows[-1]["volume"],
                             "cubic feet" if self.unit == "us" else "cubic metres")
        result = self._summary(rows, *merge(total for _stats, total in parts),
                               cell_area=cell_area)
        if write_rasters:
            result.update(paths)
            result["output_dir"] = output_dir
        return result
