# River Architect

**Analyse and design fluvial ecosystems.**

[![Documentation](https://readthedocs.org/projects/riverarchitect/badge/?version=latest)](https://riverarchitect.readthedocs.io/en/latest/)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)

River Architect supports river engineers and ecologists in planning habitat-enhancing river
design features: their expected lifespans, the dimensions they need to be stable, where they
belong in the terrain, and what they are worth ecologically.

This is the **open-source release**. The geoprocessing runs on GDAL, rasterio, numpy and
scipy; map production runs on QGIS print layouts. **No Esri software or licence is
required**, and the package runs on Linux, macOS and Windows.

The method is documented in an
[open-access, peer-reviewed paper](https://doi.org/10.1016/j.softx.2020.100438)
(*SoftwareX*, 2020).

---

## Installation

```bash
mamba create -n ra-env -c conda-forge python=3.12 \
    gdal rasterio geopandas shapely pyproj numpy scipy pandas \
    openpyxl matplotlib pykrige rasterstats whitebox
mamba activate ra-env
pip install riverarchitect
```

The geospatial stack installs far more reliably through conda-forge than through pip, because
GDAL and its bindings come as prebuilt binaries. Plain `pip install "riverarchitect[all]"`
works too where wheels are available.

Map production additionally needs QGIS with its Python bindings, which cannot come from PyPI:

```bash
sudo apt install qgis python3-qgis          # Debian / Ubuntu
python -c "from qgis.core import Qgis; print(Qgis.QGIS_VERSION)"
```

Everything except the mapping module works without QGIS. Full instructions, including the
project directory layout, are in the
[installation guide](https://riverarchitect.readthedocs.io/en/latest/guide/installation.html).

## Usage

Launch the graphical interface:

```bash
riverarchitect                    # or: python -m riverarchitect
riverarchitect /path/to/project   # start with a project directory
```

Or use the modules directly:

```python
from riverarchitect import raster

dem, dem_profile = raster.read("01_Conditions/2100_sample/dem.tif")
depth, depth_profile = raster.read("01_Conditions/2100_sample/h001000.tif")

# Rasters of differing extent must be aligned explicitly - the silent
# alternative is a spatially meaningless result.
depth = raster.align(depth, depth_profile, dem_profile)

# Water surface elevation where the bed is wet; the false branch is NoData, not zero.
wse = raster.con(depth > 0, dem + depth)
raster.write("wse.tif", wse, dem_profile)
```

Earthworks quantities between a pre- and post-project DEM:

```python
from riverarchitect.volume_assessment import VolumeAssessment

result = VolumeAssessment("dem.tif", "dem_modified.tif", unit="us").run()
print(result["fill_volume"], result["excavation_volume"], result["volume_unit"])
```

Fish stranding risk from disconnected wetted areas:

```python
import numpy as np
from riverarchitect import raster

depth, profile = raster.read("01_Conditions/2100_sample/h000300.tif")
mask, n_pools = raster.disconnected_mask(np.nan_to_num(depth) > 0)
dx, dy = raster.cell_size(profile)
print(f"{n_pools} pools, {mask.sum() * dx * dy:.0f} sqft stranded")
```

More in the [quickstart](https://riverarchitect.readthedocs.io/en/latest/guide/quickstart.html).

## What's in the box

| Module | Purpose |
|---|---|
| `riverarchitect.raster` | Raster I/O, alignment, map algebra, interpolation (IDW, kriging, nearest neighbour), connectivity, zonal statistics |
| `riverarchitect.volume` | Triangulated-surface volume integration |
| `riverarchitect.volume_assessment` | Earthworks quantities from a pair of DEMs |
| `riverarchitect.mapping` | QGIS print layouts and multi-page PDF map series |
| `riverarchitect.config` | Paths, units, canonical NoData value |
| `riverarchitect.gui` | Tkinter interface |
| `riverarchitect.tools` | `reconcile_nodata`, `lyrx2qml` command-line tools |

## Migrating from the ArcGIS version

The original River Architect was built on `arcpy` and required ArcGIS Pro with a Spatial
Analyst licence. If you are porting scripts, read
[Migrating from arcpy](https://riverarchitect.readthedocs.io/en/latest/guide/arcpy_migration.html)
first. Two differences silently produce wrong results if code is ported naively:

- **`arcpy.env.extent` did implicit alignment.** numpy does not. Use `raster.align()`.
- **Two-argument `Con()` yields NoData on the false branch**, not zero.

Two migration tools ship with the package:

```bash
# normalise inconsistent NoData sentinels in a condition (the mask is preserved exactly)
python -m riverarchitect.tools.reconcile_nodata 01_Conditions/my_condition --dry-run

# convert ArcGIS layer symbology (.lyrx, which is CIM JSON) to a QGIS style (.qml)
python -m riverarchitect.tools.lyrx2qml LifespanRasterSymbology.lyrx
```

## Documentation

<https://riverarchitect.readthedocs.io/>

The legacy wiki is preserved under *Concepts and legacy modules*. Its analysis concepts,
parameters and design-feature definitions remain the best available background on the
method; its installation instructions and code examples refer to the ArcGIS version.

## Development

```bash
git clone https://github.com/RiverArchitect/riverarchitect.git
cd riverarchitect
mamba env create -f environment.yml
mamba activate ra-env
pip install -e ".[all,test,docs]"

pytest                                          # test suite
python -m sphinx -b html docs docs/_build/html  # documentation
```

Sample data for a gravel-cobble river is in the
[SampleData repository](https://github.com/RiverArchitect/SampleData).

Contributions are welcome. Please open an issue before starting on a major change.

## Citing

> Schwindt, S., Larrieu, K., Pasternack, G.B., Rabone, G. (2020).
> River Architect. *SoftwareX* 11, 100438.
> <https://doi.org/10.1016/j.softx.2020.100438>

## Acknowledgment

Developed in the [Pasternack Lab](http://pasternack.ucdavis.edu/) at the University of
California, Davis, Department of Land, Air and Water Resources, with funding from the
[Yuba Water Agency](https://www.yubawater.org/) (Awards #201016094 and #10446) and the
[USDA National Institute of Food and Agriculture](https://nifa.usda.gov/)
(Hatch project CA-D-LAW-7034-H).

## License

BSD 3-Clause. See [LICENSE](LICENSE).
