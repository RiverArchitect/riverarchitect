"""Earthworks quantities from a pair of DEMs.

Compares an original (pre-project) and a modified (post-project) digital elevation model and
reports the fill and excavation volumes required to get from one to the other, together with
the affected areas.

This is the open-source port of the former ``VolumeAssessment`` module. Beyond dropping
arcpy and the 3D Analyst licence it changes two things of substance:

* Volumes are integrated under the **triangulated** surface (:mod:`riverarchitect.volume`)
  rather than parsed out of a geoprocessing message string.
* The two DEMs are **explicitly aligned** onto a common grid. The original relied on
  ``arcpy.env.extent`` to reconcile differing extents silently, which is the single most
  likely source of quietly wrong numbers when the modified DEM covers a different footprint.

Example
-------
::

    from riverarchitect.volume_assessment import VolumeAssessment

    va = VolumeAssessment("dem.tif", "dem_modified.tif", unit="us")
    result = va.run(output_dir="Output/volumes")
    print(result["fill_volume"], result["excavation_volume"])
"""

import logging
import os

import numpy as np

from . import config, raster, volume

__all__ = ["VolumeAssessment"]

#: Cubic feet to cubic yards.
FT3_TO_CY = 1.0 / 27.0


class VolumeAssessment:
    """Compare two DEMs and quantify the earthworks between them.

    Args:
        original_dem (str): path to the pre-project DEM.
        modified_dem (str): path to the post-project DEM.
        unit (str): ``"us"`` (feet, reported in cubic yards) or ``"si"`` (metres, cubic
            metres).
        level_of_detection (float): elevation changes with a magnitude below this threshold
            are treated as survey noise and ignored. Defaults to 0.99 ft for ``"us"`` and
            0.3 m for ``"si"``, matching the original module.
    """

    def __init__(self, original_dem, modified_dem, unit="us", level_of_detection=None):
        self.logger = logging.getLogger("riverarchitect")
        self.original_dem = original_dem
        self.modified_dem = modified_dem

        if str(unit).lower() not in config.UNITS:
            self.logger.warning("Invalid unit %r - falling back to 'us'.", unit)
            unit = "us"
        self.unit = str(unit).lower()
        self.labels = config.unit_labels(self.unit)

        if self.unit == "us":
            self.volume_factor = FT3_TO_CY
            self.level_of_detection = 0.99 if level_of_detection is None else level_of_detection
        else:
            self.volume_factor = 1.0
            self.level_of_detection = 0.30 if level_of_detection is None else level_of_detection

        self.dod = None          # DEM of Difference, modified - original
        self.profile = None

    # ------------------------------------------------------------------ analysis

    def difference(self):
        """Compute the DEM of Difference (modified minus original) on a common grid.

        Returns:
            tuple: ``(dod, profile)``. Positive values are fill, negative are excavation.
        """
        original, original_profile = raster.read(self.original_dem)
        modified, modified_profile = raster.read(self.modified_dem)

        same_grid = (original.shape == modified.shape and
                     original_profile["transform"] == modified_profile["transform"])
        if not same_grid:
            self.logger.info("DEM extents differ - aligning the modified DEM onto the "
                             "original grid (%s -> %s).", modified.shape, original.shape)
            modified = raster.align(modified, modified_profile, original_profile)

        dod = modified - original

        # Suppress changes below the level of detection.
        dod = np.where(np.abs(dod) < self.level_of_detection, 0.0, dod)
        dod = np.where(np.isfinite(original) & np.isfinite(modified), dod, np.nan)

        self.dod = dod
        self.profile = original_profile
        return dod, original_profile

    def volumes(self):
        """Fill and excavation volumes from the DEM of Difference.

        Returns:
            dict: volumes in the reporting unit plus the planimetric and draped areas.
        """
        if self.dod is None:
            self.difference()

        dx, dy = raster.cell_size(self.profile)

        fill = volume.surface_volume(self.dod, dx, dy, plane=0.0, reference="ABOVE")
        cut = volume.surface_volume(self.dod, dx, dy, plane=0.0, reference="BELOW")

        return {
            "fill_volume": fill["volume"] * self.volume_factor,
            "excavation_volume": cut["volume"] * self.volume_factor,
            "net_volume": (fill["volume"] - cut["volume"]) * self.volume_factor,
            "fill_area": fill["area_2d"],
            "excavation_area": cut["area_2d"],
            "fill_area_3d": fill["area_3d"],
            "excavation_area_3d": cut["area_3d"],
            "volume_unit": self.labels["volume"],
            "area_unit": self.labels["area"],
            "level_of_detection": self.level_of_detection,
        }

    # -------------------------------------------------------------------- output

    def write_rasters(self, output_dir):
        """Write the DoD plus separate fill and excavation rasters.

        Returns:
            dict: ``{name: path}`` of the rasters written.
        """
        os.makedirs(output_dir, exist_ok=True)
        if self.dod is None:
            self.difference()

        fill = raster.con(self.dod > 0, self.dod)
        cut = raster.con(self.dod < 0, self.dod)

        written = {
            "dod": raster.write(os.path.join(output_dir, "dod.tif"), self.dod, self.profile),
            "fill": raster.write(os.path.join(output_dir, "fill.tif"), fill, self.profile),
            "excavation": raster.write(os.path.join(output_dir, "excavation.tif"), cut,
                                       self.profile),
        }
        for name, path in written.items():
            self.logger.info("Wrote %s raster: %s", name, path)
        return written

    def run(self, output_dir=None):
        """Run the full assessment: difference, volumes and (optionally) output rasters.

        Args:
            output_dir (str): if given, DoD/fill/excavation rasters are written there.

        Returns:
            dict: the :meth:`volumes` result, plus ``rasters`` when ``output_dir`` was given.
        """
        self.logger.info("Volume assessment: %s -> %s",
                         os.path.basename(self.original_dem),
                         os.path.basename(self.modified_dem))
        self.difference()
        result = self.volumes()

        self.logger.info("  fill        : %12.2f %s over %.1f %s",
                         result["fill_volume"], result["volume_unit"],
                         result["fill_area"], result["area_unit"])
        self.logger.info("  excavation  : %12.2f %s over %.1f %s",
                         result["excavation_volume"], result["volume_unit"],
                         result["excavation_area"], result["area_unit"])
        self.logger.info("  net         : %12.2f %s",
                         result["net_volume"], result["volume_unit"])

        if output_dir:
            result["rasters"] = self.write_rasters(output_dir)
        return result
