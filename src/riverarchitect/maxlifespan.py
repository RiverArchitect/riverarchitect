"""Best-feature and maximum-lifespan mapping.

The open-source replacement for the ArcGIS ``MaxLifespan`` module. Lifespan mapping answers
"how long does *this* feature last here?". Given the lifespan rasters of several candidate
features, this answers the planner's question instead: **which feature belongs here, and how
long will it last?**

The rule is the one the original used:

* ``max_lf`` is the cell-wise **maximum** across the feature lifespan rasters;
* a feature wins a cell where its own lifespan equals that maximum;
* each winner is written as a mask raster and polygonised, so the result can be drawn as
  action areas on a map.

Ties are kept rather than broken: a cell where two features both reach the maximum appears
in both layers. That is deliberate - it tells the planner the choice is theirs, and it is
what the original did.
"""

import glob
import logging
import os

import numpy as np

from . import config, raster, tiled

__all__ = ["MaxLifespan"]

logger = logging.getLogger("riverarchitect")


class MaxLifespan:
    """Combine per-feature lifespan rasters into a best-feature assessment.

    Args:
        lifespan_dir (str): directory holding ``lf_<feature>.tif`` rasters, normally the
            output of :class:`riverarchitect.lifespan.LifespanDesign`.
        features (list): feature ids to consider. Defaults to every ``lf_*.tif`` present.
        unit (str): ``"us"`` or ``"si"``, for the area unit in the summary.

    Attributes:
        error (bool): True when at least one feature could not be processed.
    """

    def __init__(self, lifespan_dir, features=None, unit="us"):
        self.lifespan_dir = str(lifespan_dir)
        if not os.path.isdir(self.lifespan_dir):
            raise FileNotFoundError("no such directory: %s" % self.lifespan_dir)
        self.unit = str(unit).lower()
        self.logger = logger
        self.error = False

        self.rasters = {}
        for path in sorted(glob.glob(os.path.join(self.lifespan_dir, "lf_*.tif"))):
            fid = os.path.splitext(os.path.basename(path))[0][3:]
            if features is None or fid in features:
                self.rasters[fid] = path
        if not self.rasters:
            raise FileNotFoundError("no lf_*.tif rasters in %s" % self.lifespan_dir)

    @property
    def feature_ids(self):
        """Feature ids that will take part in the assessment."""
        return sorted(self.rasters)

    def run(self, output_dir=None, write_polygons=True):
        """Compute the maximum-lifespan raster and one best-feature mask per feature.

        Returns:
            dict: ``max_lifespan_raster``, ``features`` (per-feature area and share) and the
            paths written.
        """
        output_dir = output_dir or os.path.join(config.dir_output("MaxLifespan"),
                                                os.path.basename(self.lifespan_dir))
        os.makedirs(output_dir, exist_ok=True)

        first = next(iter(self.rasters.values()))
        if tiled.enabled(raster.profile_of(first), 2 * len(self.rasters) + 4):
            return self._run_blockwise(output_dir, write_polygons)

        # The first raster defines the grid; the rest are aligned onto it. The originals
        # relied on arcpy.env.extent = "MAXOF" to reconcile differing extents implicitly.
        reference = None
        arrays = {}
        for fid, path in self.rasters.items():
            array, profile = raster.read(path)
            if reference is None:
                reference = profile
            else:
                array = raster.align(array, profile, reference)
            arrays[fid] = array

        best = raster.cell_statistics(list(arrays.values()), "MAXIMUM")
        max_path = os.path.join(output_dir, "max_lf.tif")
        raster.write(max_path, best, reference)

        dx, dy = raster.cell_size(reference)
        cell_area = dx * dy
        total_mapped = float(np.isfinite(best).sum() * cell_area)

        summary = []
        for fid, array in arrays.items():
            # Compare only where both are data; NaN == NaN is False, which is what we want.
            with np.errstate(invalid="ignore"):
                wins = np.isfinite(array) & np.isfinite(best) & (array == best)
            area = float(wins.sum() * cell_area)

            entry = {
                "feature": fid,
                "area": area,
                "share": (100.0 * area / total_mapped) if total_mapped else 0.0,
            }
            if wins.any():
                entry["max_lifespan"] = float(np.nanmax(array[wins]))

            path = os.path.join(output_dir, "best_%s.tif" % fid)
            raster.write(path, raster.con(wins, 1.0), reference)
            entry["raster"] = path

            if write_polygons and wins.any():
                self._write_polygons(
                    entry, output_dir,
                    lambda: raster.polygonize(wins.astype("int32"), reference, mask=wins))

            summary.append(entry)

        return self._result(summary, max_path, output_dir, total_mapped)

    def _result(self, summary, max_path, output_dir, total_mapped):
        summary.sort(key=lambda entry: entry["area"], reverse=True)
        return {
            "max_lifespan_raster": max_path,
            "output_dir": output_dir,
            "total_mapped_area": total_mapped,
            "area_unit": config.area_unit(self.unit),
            "features": summary,
        }

    def _write_polygons(self, entry, output_dir, polygonize):
        fid = entry["feature"]
        try:
            polygons = polygonize()
            polygons["feature"] = fid
            polygons["area"] = polygons.geometry.area
            vector_path = os.path.join(output_dir, "best_%s.gpkg" % fid)
            polygons.to_file(vector_path, driver="GPKG")
            entry["polygons"] = vector_path
        except Exception as exc:  # a missing driver must not lose the rasters
            self.logger.info("      * could not polygonise %s (%s)", fid, exc)
            self.error = True

    def _run_blockwise(self, output_dir, write_polygons):
        """:meth:`run` for rasters too large to hold, one block at a time."""
        fids = list(self.rasters)
        reference = raster.profile_of(self.rasters[fids[0]])
        layers = 2 * len(fids) + 4
        self.logger.info("   >> %d x %d cells exceed the memory budget - processing block "
                         "by block", reference["height"], reference["width"])
        max_path = os.path.join(output_dir, "max_lf.tif")
        paths = {fid: os.path.join(output_dir, "best_%s.tif" % fid) for fid in fids}
        writers = {fid: tiled.Writer(path, reference) for fid, path in paths.items()}

        def work(block):
            arrays = {fid: tiled.read(self.rasters[fid], reference, block.window)
                      for fid in fids}
            if not any(np.isfinite(a).any() for a in arrays.values()):
                return None
            best = raster.cell_statistics(list(arrays.values()), "MAXIMUM")
            best_out.write(block, best)
            stats = {}
            for fid, array in arrays.items():
                with np.errstate(invalid="ignore"):
                    wins = np.isfinite(array) & np.isfinite(best) & (array == best)
                writers[fid].write(block, raster.con(wins, 1.0))
                stats[fid] = tiled.Summary.of(array[wins])
            return int(np.isfinite(best).sum()), stats

        try:
            with tiled.Writer(max_path, reference) as best_out:
                parts = [p for p in tiled.map_blocks(work, reference, layers=layers,
                                                     label="maximum lifespan",
                                                     needs=list(self.rasters.values()))
                         if p is not None]
        finally:
            for writer in writers.values():
                writer.close()

        dx, dy = raster.cell_size(reference)
        cell_area = dx * dy
        total_mapped = float(sum(count for count, _stats in parts) * cell_area)
        summary = []
        for fid in fids:
            wins = tiled.Summary.merge(stats[fid] for _count, stats in parts)
            area = float(wins.count * cell_area)
            entry = {
                "feature": fid,
                "area": area,
                "share": (100.0 * area / total_mapped) if total_mapped else 0.0,
            }
            if wins.count:
                entry["max_lifespan"] = wins.maximum
            entry["raster"] = paths[fid]
            if write_polygons and wins.count:
                self._write_polygons(entry, output_dir, lambda fid=fid: tiled.polygonize(
                    lambda block: _mask_values(paths[fid], reference, block),
                    reference, layers=layers, needs=[paths[fid]]))
            summary.append(entry)
        return self._result(summary, max_path, output_dir, total_mapped)


def _mask_values(path, reference, block):
    """``(values, mask)`` of the cells a best-feature raster marks, for polygonising."""
    mask = np.isfinite(tiled.read(path, reference, block.window))
    return mask.astype("int32"), mask
