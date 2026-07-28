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

from . import config, raster

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
                try:
                    polygons = raster.polygonize(wins.astype("int32"), reference, mask=wins)
                    polygons["feature"] = fid
                    polygons["area"] = polygons.geometry.area
                    vector_path = os.path.join(output_dir, "best_%s.gpkg" % fid)
                    polygons.to_file(vector_path, driver="GPKG")
                    entry["polygons"] = vector_path
                except Exception as exc:  # a missing driver must not lose the rasters
                    self.logger.info("      * could not polygonise %s (%s)", fid, exc)
                    self.error = True

            summary.append(entry)

        summary.sort(key=lambda entry: entry["area"], reverse=True)
        return {
            "max_lifespan_raster": max_path,
            "output_dir": output_dir,
            "total_mapped_area": total_mapped,
            "area_unit": config.area_unit(self.unit),
            "features": summary,
        }
