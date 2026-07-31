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

#: Modules that genuinely need the geospatial stack. Importing them without it *should*
#: raise ImportError, so the "must import" test skips them in an environment that lacks it -
#: a QGIS interpreter, for instance, has no rasterio.
NEEDS_GEOSPATIAL = {
    "riverarchitect.raster",
    "riverarchitect.volume_assessment",
    "riverarchitect.lifespan",
    "riverarchitect.maxlifespan",
    "riverarchitect.stranding",
}

try:
    import numpy  # noqa: F401
    import rasterio  # noqa: F401
    HAS_GEOSPATIAL = True
except ImportError:
    HAS_GEOSPATIAL = False

MODULES = [
    "riverarchitect",
    "riverarchitect.config",
    "riverarchitect.raster",
    "riverarchitect.volume",
    "riverarchitect.volume_assessment",
    "riverarchitect.condition",
    "riverarchitect.lifespan",
    "riverarchitect.maxlifespan",
    "riverarchitect.stranding",
    "riverarchitect.mapping",
    "riverarchitect.tools",
    "riverarchitect.tools.reconcile_nodata",
    "riverarchitect.tools.lyrx2qml",
    "riverarchitect.tools.taux",
    "riverarchitect.gui",
]


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name):
    if name in NEEDS_GEOSPATIAL and not HAS_GEOSPATIAL:
        pytest.skip("no geospatial stack in this interpreter")
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


def test_taux_tool_writes_the_four_rasters(tmp_path):
    """The CLI wrapper must agree with the module it wraps, regime for regime."""
    import numpy as np
    import rasterio
    from affine import Affine

    from riverarchitect import raster, shear
    from riverarchitect.tools import taux

    profile = {"driver": "GTiff", "height": 1, "width": 3, "count": 1, "dtype": "float32",
               "crs": "EPSG:32633", "transform": Affine(1.0, 0.0, 0.0, 0.0, -1.0, 1.0)}
    # depths chosen to land one cell in each regime for dmean = 0.01 (ks = 0.044 m)
    raster.write(str(tmp_path / "h.tif"), np.array([[0.2, 0.5, 2.2]]), profile)
    raster.write(str(tmp_path / "u.tif"), np.full((1, 3), 1.0), profile)
    raster.write(str(tmp_path / "dmean.tif"), np.full((1, 3), 0.01), profile)

    written = taux.compute(str(tmp_path / "u.tif"), str(tmp_path / "h.tif"),
                           str(tmp_path / "dmean.tif"), str(tmp_path / "out" / "q"),
                           unit="si")
    summary = written.pop("_summary")
    assert set(written) == {"ustar2", "theta84", "h_over_ks", "regime"}
    assert summary == {"invalid": 0, "Rickenmann-Recking": 1, "blended": 1,
                       "Keulegan-Einstein": 1}

    with rasterio.open(written["regime"]) as src:
        assert src.dtypes[0] == "uint8" and src.nodata == 0
        assert src.read(1).tolist() == [[1, 2, 3]]

    theta, _profile = raster.read(written["theta84"])
    expected = shear.calculate_taux(np.full((1, 3), 1.0), np.array([[0.2, 0.5, 2.2]]),
                                    shear.d84_of(np.full((1, 3), 0.01)), gravity=9.81)
    assert np.allclose(theta, expected.theta84, rtol=1e-6)


def test_the_application_icon_ships_inside_the_package():
    """The icon must resolve from the package, not from the repository layout.

    Both front ends load it through ``config.icon_path()`` at start-up. If it lived only in
    ``docs/img/`` - or if ``assets/**/*`` fell out of the wheel's package-data - a source
    checkout would still work while every installed copy raised on launch.
    """
    import os

    from riverarchitect import config

    path = config.icon_path()
    assert os.path.isfile(path), "packaged icon missing: %s" % path
    assert os.path.dirname(path) == os.path.join(config.package_dir(), "assets")


def test_reconcile_nodata_reports_missing_dependencies_from_main():
    """The dependency check belongs in main(), not at import time."""
    from riverarchitect.tools import reconcile_nodata

    assert hasattr(reconcile_nodata, "dependencies_available")
    # The module imports either way; the check simply reports what is actually installed.
    assert reconcile_nodata.dependencies_available() is HAS_GEOSPATIAL
