"""Every module must be importable without side effects, even with dependencies missing.

This is not a style rule. Read the Docs builds the documentation in an environment that has
no geospatial stack, and Sphinx imports each module to render its source listing. A module
that calls ``sys.exit()`` when an optional import fails takes the whole documentation build
down with it - which is exactly what happened once, in
``riverarchitect.tools.reconcile_nodata``.

The same applies to test collection, to ``riverarchitect.gui`` probing what is available,
and to anyone who imports the package to check a version number.
"""

import importlib
import pkgutil
import subprocess
import sys

import pytest

import riverarchitect

MODULES = [
    "riverarchitect",
    "riverarchitect.config",
    "riverarchitect.raster",
    "riverarchitect.volume",
    "riverarchitect.volume_assessment",
    "riverarchitect.mapping",
    "riverarchitect.tools",
    "riverarchitect.tools.reconcile_nodata",
    "riverarchitect.tools.lyrx2qml",
    "riverarchitect.gui",
]


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name):
    assert importlib.import_module(name) is not None


def test_every_submodule_is_discoverable():
    """Guard against a package that cannot even be walked."""
    found = {name for _finder, name, _ispkg
             in pkgutil.walk_packages(riverarchitect.__path__, "riverarchitect.")}
    assert "riverarchitect.raster" in found
    assert "riverarchitect.tools.reconcile_nodata" in found


@pytest.mark.parametrize("name", MODULES)
def test_import_without_dependencies_raises_importerror_not_systemexit(name):
    """With the geospatial stack hidden, importing may fail - but only with ImportError.

    That distinction is the whole point. Sphinx's viewcode imports every documented module
    and tolerates an ImportError; a ``sys.exit()`` at module level is a ``SystemExit``, which
    it does not tolerate, and the documentation build dies. The bug is invisible in-process
    whenever the dependency happens to be installed, so this runs out of process with the
    geospatial packages blocked, reproducing the Read the Docs environment.
    """
    code = (
        "import sys\n"
        "blocked = {'numpy', 'scipy', 'rasterio', 'geopandas', 'shapely', 'fiona',\n"
        "           'pyproj', 'osgeo', 'pykrige', 'rasterstats', 'whitebox',\n"
        "           'matplotlib', 'qgis', 'PySide6', 'PyQt5'}\n"
        "class Blocker:\n"
        "    def find_spec(self, name, path=None, target=None):\n"
        "        if name.split('.')[0] in blocked:\n"
        "            raise ImportError(name)\n"
        "        return None\n"
        "sys.meta_path.insert(0, Blocker())\n"
        "try:\n"
        "    import %s\n"
        "except ImportError:\n"
        "    pass          # legitimate: an optional dependency is genuinely absent\n" % name
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, (
        "importing %s without the geospatial stack failed with something other than "
        "ImportError (exit %s). A module must not call sys.exit() at import time.\n"
        "stdout: %s\nstderr: %s"
        % (name, result.returncode, result.stdout, result.stderr))
    assert "SystemExit" not in result.stderr


def test_reconcile_nodata_reports_missing_dependencies_from_main():
    """The dependency check belongs in main(), not at import time."""
    from riverarchitect.tools import reconcile_nodata

    assert hasattr(reconcile_nodata, "dependencies_available")
    assert reconcile_nodata.dependencies_available() is True   # ra-env has them
