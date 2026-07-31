"""River Architect: analyse and design fluvial ecosystems.

An open-source toolkit for river engineers and ecologists. This package is the
licence-free rewrite of the original ArcGIS-based River Architect: the geoprocessing runs on
GDAL/rasterio/numpy/scipy and map production runs on QGIS print layouts, so nothing here
requires Esri software.

Modules
-------
:mod:`riverarchitect.raster`
    Raster I/O, alignment, map algebra, interpolation, connectivity and zonal statistics.
:mod:`riverarchitect.volume`
    Triangulated-surface volume integration.
:mod:`riverarchitect.volume_assessment`
    Earthworks quantities from a pair of DEMs.
:mod:`riverarchitect.condition`
    Reading a condition folder and its ``input_definitions.inp``.
:mod:`riverarchitect.shear`
    Regime-aware dimensionless bed shear stress (Shields stress).
:mod:`riverarchitect.lifespan`
    Lifespan and design mapping for restoration features.
:mod:`riverarchitect.maxlifespan`
    Best-feature assessment across several lifespan maps.
:mod:`riverarchitect.stranding`
    Fish stranding risk from disconnecting wetted areas.
:mod:`riverarchitect.sharc`
    Habitat suitability indices and Seasonal Habitat Area.
:mod:`riverarchitect.preprocessing`
    Preparing a condition: detrended DEM, water levels, morphological units.
:mod:`riverarchitect.recruitment`
    Riparian seedling recruitment potential.
:mod:`riverarchitect.terraforming`
    Threshold-based grading and widening of a DEM for planting.
:mod:`riverarchitect.riverbuilder`
    Synthetic river valleys from a handful of design parameters.
:mod:`riverarchitect.projectmaker`
    Construction cost against the gain in seasonal habitat area.
:mod:`riverarchitect.flows`
    Seasonal flow duration curves, annual peaks and flood return periods.
:mod:`riverarchitect.mapping`
    QGIS print layouts and multi-page PDF map series.
:mod:`riverarchitect.config`
    Paths, units and the canonical NoData value.
:mod:`riverarchitect.guide`
    The Live Guide: the sample-data walkthrough both front ends render.
:mod:`riverarchitect.tools`
    Command-line maintenance tools.

The graphical interface lives in :mod:`riverarchitect.gui` and is started with the
``riverarchitect`` console script, or with ``python -m riverarchitect``.
"""

__version__ = "2.2.0"
__author__ = "River Architect Development Team"
__license__ = "BSD-3-Clause"

from . import config  # noqa: F401

__all__ = ["config", "guide", "condition", "raster", "shear", "volume",
           "volume_assessment", "lifespan", "maxlifespan", "terraforming",
           "riverbuilder", "stranding", "sharc", "preprocessing", "recruitment",
           "flows", "projectmaker", "mapping", "tools", "__version__"]


def __getattr__(name):
    """Import the heavier submodules lazily.

    Keeps ``import riverarchitect`` cheap and, more importantly, keeps it working when an
    optional dependency (QGIS, pykrige, rasterstats) is missing: only the module that needs
    it fails, and only when it is actually used.
    """
    if name in ("raster", "shear", "volume", "volume_assessment", "condition", "lifespan",
                "maxlifespan", "terraforming", "riverbuilder", "stranding", "sharc",
                "preprocessing", "recruitment", "flows", "projectmaker", "mapping",
                "guide", "tools"):
        import importlib
        module = importlib.import_module("." + name, __name__)
        globals()[name] = module
        return module
    raise AttributeError("module %r has no attribute %r" % (__name__, name))
