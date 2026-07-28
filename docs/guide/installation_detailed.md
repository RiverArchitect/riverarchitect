# Installation in detail

{doc}`installation` is the short version. This page explains what is actually being
installed, why the recommended route looks the way it does, how to lay out a project
directory, and what to do when a step fails.

## Background: why conda and not pip

River Architect is pure Python, but almost everything it does goes through
[GDAL](https://gdal.org/). GDAL is a large C++ library with its own dependency tree
(PROJ, GEOS, and the format drivers for GeoTIFF, NetCDF, HDF and the rest). Three Python
packages bind to it - `rasterio`, `geopandas` via `fiona`/`pyogrio`, and `pyproj` - and all
three must bind to the *same* GDAL build. When they do not, the failure mode is not an
import error but a silent one: mismatched PROJ data directories give you rasters that are
georeferenced into the wrong place.

conda-forge builds the whole stack together against one GDAL, which is why it is the
recommended route. PyPI wheels usually work too, because `rasterio` and `pyogrio` now vendor
their own GDAL copies, but each vendored copy is separate and version skew between them is
your problem to debug.

The other reason is QGIS. It cannot come from PyPI at all, and its Python bindings are
compiled against the *system* Python, so mapping runs in a different interpreter from the
rest of the package. That constraint shapes the whole layout and is covered in
{ref}`qgis-bindings` below.

(detailed-requirements)=

## Requirements

### Runtime

| Package | Version | Needed for | Source |
|---|---|---|---|
| Python | >= 3.9 | everything | conda-forge |
| `numpy` | >= 1.22 | all array work | conda-forge |
| `scipy` | >= 1.8 | interpolation, connected components, filters | conda-forge |
| `rasterio` | >= 1.3 | raster I/O, reprojection, masking | conda-forge |
| `geopandas` | >= 0.12 | vector I/O, polygonize output | conda-forge |
| `shapely` | >= 2.0 | geometry operations | conda-forge |
| `pyproj` | >= 3.4 | coordinate reference systems | conda-forge |
| `pandas` | >= 1.5 | tabular results | conda-forge |
| `openpyxl` | >= 3.0 | reading `.xlsx` flow and threshold workbooks | conda-forge |
| `tkinter` | stdlib | the fallback graphical interface | ships with CPython |

`tkinter` is part of the standard library but some Linux distributions package it
separately. On Debian and Ubuntu it is `python3-tk`; the conda-forge Python includes it.

### Optional extras

| Extra | Package | Enables |
|---|---|---|
| `gui` | `pyside6` | the Qt interface; without it the interface falls back to tkinter |
| `interpolation` | `pykrige` | {func}`riverarchitect.raster.kriging` and its estimation variance |
| `zonal` | `rasterstats` | {func}`riverarchitect.raster.zonal_statistics` |
| `terrain` | `whitebox` | depression filling and flow routing |
| `plotting` | `matplotlib` | figures from the volume assessment |
| `all` | all of the above | |
| `test` | `pytest`, `pytest-cov` | the test suite |
| `docs` | `sphinx`, `myst-parser`, `sphinx-rtd-theme`, `sphinx-copybutton`, `sphinx-design` | building this documentation |

Each optional dependency is imported lazily, inside the function that needs it. A missing
extra therefore breaks exactly one function and nothing else - `riverarchitect.__init__`
resolves submodules through `__getattr__` for the same reason.

### Graphical interface

| Component | Version | Notes |
|---|---|---|
| PySide6 | >= 6.5 | the default front end; from PyPI or conda-forge |
| PyQt5 | 5.15 | the alternative Qt binding, already present in a QGIS interpreter |
| tkinter | stdlib | the fallback, so the interface always opens |

No wheel exists for PySide6 on linux-aarch64, which is why the `gui` extra carries an
environment marker. There, tkinter takes over; a Raspberry Pi still gets a working window.
See {doc}`gui`.

### Mapping

| Component | Version | Notes |
|---|---|---|
| QGIS | >= 3.28 (3.44 is what is tested) | needs the `qgis.core` Python bindings |
| Qt | 5.15 or 6 | comes with QGIS |

## Installation routes

### From a clone (recommended)

```bash
git clone https://github.com/RiverArchitect/riverarchitect.git
cd riverarchitect
mamba env create -f environment.yml
mamba activate ra-env
pip install -e ".[all,test,docs]"
```

`environment.yml` pins Python 3.12 and pulls the whole geospatial stack plus the optional
extras from conda-forge. `pip install -e` then registers the package itself in editable
mode, which is what you want if you intend to modify or contribute to it.

### Into an existing environment

If you already have a working geospatial environment, only the package is missing:

```bash
mamba activate my-env
pip install --no-deps -e /path/to/riverarchitect
```

`--no-deps` stops pip from pulling PyPI copies of packages conda already provides. That
mixture is the single most common way to break a conda geospatial environment.

### Plain pip

```bash
pip install -e ".[all]"
```

This works on Windows and macOS, where `rasterio` and `geopandas` publish wheels with a
vendored GDAL. On Linux it usually works too; if it does not, you need GDAL development
headers (`sudo apt install libgdal-dev` and matching `gdal` version pin), which is precisely
the situation conda avoids.

### Without conda at all

Nothing in the package requires conda. A system Python with distribution packages works:

```bash
sudo apt install python3-rasterio python3-geopandas python3-scipy python3-tk
pip install --user --no-deps -e /path/to/riverarchitect
```

This is also the configuration in which the mapping module works out of the box, because
distribution QGIS binds to that same interpreter.

(qgis-bindings)=

## QGIS and the two-interpreter problem

QGIS bindings are compiled against a specific Python. The QGIS you install through `apt`,
OSGeo4W or Homebrew binds to *that* installation's Python, not to `ra-env`. `import qgis`
from inside a conda environment therefore fails, and no amount of `pip install` fixes it,
because there is no `qgis` package on PyPI to install.

River Architect handles this by keeping QGIS confined to one module. `riverarchitect.mapping`
imports it behind a guard:

```python
from riverarchitect.mapping import QGIS_AVAILABLE
```

`QGIS_AVAILABLE` is `False` when the bindings are absent, the Mapping tab in the GUI explains
what is missing instead of raising, and every other module carries on normally.

The practical arrangement is:

* run analysis in `ra-env`, write results as GeoTIFF and GeoPackage;
* run mapping with the interpreter that owns the QGIS bindings, pointing it at those files.

```bash
# analysis
mamba run -n ra-env python my_analysis.py

# mapping, with the system interpreter
QT_QPA_PLATFORM=offscreen PYTHONPATH=src /usr/bin/python3 my_mapping.py
```

`QT_QPA_PLATFORM=offscreen` is what makes QGIS run without a display, for example over SSH
or in CI. If QGIS is installed somewhere other than `/usr`, tell it where:

```bash
export QGIS_PREFIX_PATH=/opt/qgis
```

See {doc}`qgis_mapping` for the mapping workflow itself.

## Project directory layout

River Architect resolves data paths against a *project home*, not against the package. Set it
in any of these ways, listed in order of precedence:

```python
from riverarchitect import config
config.set_project_home("/data/my_project")     # 1. explicit call
```

```bash
export RIVERARCHITECT_HOME=/data/my_project     # 2. environment variable
riverarchitect /data/my_project                 # 3. argument to the console script
```

With none of them set, the current working directory is used.

The expected layout, which `sample-data/` in the repository already follows:

```text
my_project/
├── 00_Flows/                     flow series and duration workbooks
│   └── 2100_sample/
│       └── flow_duration_chsp.xlsx
├── 01_Conditions/                one sub-folder per condition
│   └── 2100_sample/
│       ├── dem.tif               digital elevation model
│       ├── dem_detrend.tif       detrended DEM
│       ├── dmean.tif             mean grain size
│       ├── d2w.tif               depth to the water table
│       ├── scour.tif, fill.tif   DEM of difference
│       ├── h001000.tif           flow depth at 1000 cfs
│       ├── u001000.tif           flow velocity at 1000 cfs
│       └── input_definitions.inp raster names and return periods
├── 02_Maps/                      QGIS projects and PDF output
└── Output/                       analysis results
```

Discharges are encoded in the file name with six digits, zero-padded: `h001000.tif` is the
depth raster at 1000 cfs. `input_definitions.inp` lists which rasters belong to the condition
and which flood return period each discharge represents; {doc}`tutorial` reads one.

The bundled `sample-data/` directory is a complete example of this layout, and the launchers
open it when no other project directory is given.

## When something goes wrong

**`ImportError: libgdal.so.XX: cannot open shared object file`**
: A pip package and a conda package are binding to different GDAL builds. Reinstall the
  offending package from conda-forge, or recreate the environment and use `--no-deps` for
  the pip step.

**Rasters land in the wrong place, or CRS lookups fail**
: PROJ cannot find its data directory. Check `python -c "import pyproj; print(pyproj.datadir.get_data_dir())"`
  and make sure it points inside the active environment. Unsetting a stale `PROJ_LIB` or
  `GDAL_DATA` from your shell profile usually fixes it.

**`ModuleNotFoundError: No module named 'tkinter'`**
: Install `python3-tk` (Debian/Ubuntu) or use the conda-forge Python, which bundles it.
  Only relevant when PySide6 is also missing; with either one, the interface opens.

**The interface starts but looks dated, with no menu bar styling**
: That is the tkinter fallback. `pip install pyside6` and restart. Check which one is in use
  with `python -c "from riverarchitect.gui import select_backend; print(select_backend())"`.

**`qt.qpa.plugin: Could not load the Qt platform plugin "xcb"`**
: Qt cannot reach a display. Over SSH, enable X forwarding or set
  `QT_QPA_PLATFORM=offscreen` for headless use; on a bare container install
  `libxcb-cursor0`. Falling back with `RIVERARCHITECT_GUI=tk` also works.

**`ModuleNotFoundError: No module named 'qgis'`**
: Expected inside `ra-env`. Run mapping with the interpreter that owns the bindings; see
  {ref}`qgis-bindings`.

**QGIS crashes on a machine with no display**
: Set `QT_QPA_PLATFORM=offscreen`.

**`pip install riverarchitect` cannot find the package**
: It is not published on PyPI. Install from a clone.

**Results contain implausible values such as `-3.4e38` or `-9999`**
: Input rasters declare inconsistent NoData sentinels. Normalise the condition first:
  `python -m riverarchitect.tools.reconcile_nodata 01_Conditions/2100_sample --dry-run`,
  then run it without `--dry-run`. The NoData *mask* is preserved exactly; only the sentinel
  changes.

## Building the documentation locally

```bash
mamba activate ra-env
pip install -e ".[docs]"
python -m sphinx -b html docs docs/_build/html
```

The build is expected to finish with zero warnings. Open `docs/_build/html/index.html`.
