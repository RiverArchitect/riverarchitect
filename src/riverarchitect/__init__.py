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
:mod:`riverarchitect.mapping`
    QGIS print layouts and multi-page PDF map series.
:mod:`riverarchitect.config`
    Paths, units and the canonical NoData value.
:mod:`riverarchitect.tools`
    Command-line maintenance tools.

The graphical interface lives in :mod:`riverarchitect.gui` and is started with the
``riverarchitect`` console script, or with ``python -m riverarchitect``.
"""

__version__ = "1.0.0"
__author__ = "River Architect Development Team"
__license__ = "BSD-3-Clause"

from . import config  # noqa: F401

__all__ = ["config", "raster", "volume", "volume_assessment", "mapping", "tools",
           "__version__"]


def __getattr__(name):
    """Import the heavier submodules lazily.

    Keeps ``import riverarchitect`` cheap and, more importantly, keeps it working when an
    optional dependency (QGIS, pykrige, rasterstats) is missing: only the module that needs
    it fails, and only when it is actually used.
    """
    if name in ("raster", "volume", "volume_assessment", "mapping", "tools"):
        import importlib
        module = importlib.import_module("." + name, __name__)
        globals()[name] = module
        return module
    raise AttributeError("module %r has no attribute %r" % (__name__, name))
