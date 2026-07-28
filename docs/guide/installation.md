# Installation

River Architect is a Python package. It runs on Linux, macOS and Windows, and needs **no Esri
software**: the geoprocessing runs on GDAL/rasterio/numpy/scipy and map production runs on
QGIS.

```{note}
If you are looking for the original ArcGIS-based River Architect, its installation
instructions live in the [legacy wiki](../wiki/Installation.md). That version required
ArcGIS Pro with a Spatial Analyst licence and only ran on Windows.
```

## Requirements

| Component | Needed for | Notes |
|---|---|---|
| Python >= 3.9 | everything | |
| numpy, scipy, rasterio, geopandas, shapely, pyproj, pandas | analysis | installed automatically |
| QGIS >= 3.28 with Python bindings | the mapping module | not installable from PyPI, see below |
| pykrige | kriging interpolation | optional extra |
| rasterstats | zonal statistics | optional extra |
| whitebox | terrain/hydrology tools | optional extra |

## Conda / mamba (recommended)

The geospatial stack is far easier to install through conda-forge than through pip, because
GDAL and its bindings come as prebuilt binaries.

```bash
mamba create -n ra-env -c conda-forge python=3.12 \
    gdal rasterio geopandas shapely pyproj \
    numpy scipy pandas openpyxl matplotlib \
    pykrige rasterstats whitebox
mamba activate ra-env
pip install riverarchitect
```

Or, from a clone of the repository:

```bash
git clone https://github.com/RiverArchitect/riverarchitect.git
cd riverarchitect
mamba env create -f environment.yml
mamba activate ra-env
pip install -e ".[all]"
```

## pip

```bash
pip install "riverarchitect[all]"
```

On Windows and macOS this pulls prebuilt wheels for rasterio and geopandas. On Linux you may
need GDAL development headers first; the conda route avoids that entirely.

## QGIS for the mapping module

Map production uses QGIS print layouts. QGIS cannot be installed from PyPI, so install it
through your system package manager and check that its Python bindings are importable:

```bash
python -c "from qgis.core import Qgis; print(Qgis.QGIS_VERSION)"
```

Debian/Ubuntu:

```bash
sudo apt install qgis python3-qgis
```

The QGIS bindings are built against the **system** Python, not against a conda environment.
Run the mapping module with the interpreter that owns the bindings. Everything else in River
Architect works in any environment.

If QGIS lives outside `/usr`, point `QGIS_PREFIX_PATH` at it:

```bash
export QGIS_PREFIX_PATH=/opt/qgis
```

Without QGIS, the rest of the package works normally and the Mapping tab explains what is
missing instead of failing.

## Verifying the installation

```bash
python -c "import riverarchitect; print(riverarchitect.__version__)"
pytest --pyargs riverarchitect   # if installed with the [test] extra
```

## Launching the graphical interface

```bash
riverarchitect                    # console script
python -m riverarchitect          # equivalent
riverarchitect /path/to/project   # start with a project directory
```

## Project directory layout

River Architect resolves data paths against a *project directory*. Set it with the
`RIVERARCHITECT_HOME` environment variable, by passing it to the console script, from the
GUI's **Tools > Set project directory**, or in code with
{func}`riverarchitect.config.set_project_home`.

```text
my_project/
├── 00_Flows/          flow series and duration workbooks
├── 01_Conditions/     one sub-folder per condition, holding input rasters
│   └── 2100_sample/
│       ├── dem.tif
│       ├── h001000.tif        flow depth at 1000 cfs
│       └── u001000.tif        flow velocity at 1000 cfs
├── 02_Maps/           QGIS projects and PDF map output
└── Output/            analysis results
```

Sample data for a gravel-cobble river is available from the
[SampleData repository](https://github.com/RiverArchitect/SampleData).
