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
git clone https://github.com/RiverArchitect/riverarchitect.git
cd riverarchitect
mamba env create -f environment.yml
mamba activate ra-env
pip install -e ".[all]"
```

The geospatial stack installs far more reliably through conda-forge than through pip, because
GDAL and its bindings come as prebuilt binaries. `mamba` comes with
[Miniforge](https://conda-forge.org/download/). River Architect is not on PyPI yet, so
install from a clone as above.

Map production additionally needs QGIS with its Python bindings, which cannot come from PyPI:

```bash
sudo apt install qgis python3-qgis          # Debian / Ubuntu
python -c "from qgis.core import Qgis; print(Qgis.QGIS_VERSION)"
```

Everything except the mapping module works without QGIS. Per-platform instructions are in the
[quick installation guide](https://riverarchitect.readthedocs.io/en/latest/guide/installation.html);
the dependency background, project directory layout and troubleshooting are in the
[detailed one](https://riverarchitect.readthedocs.io/en/latest/guide/installation_detailed.html).

## Usage

Launch the graphical interface:

```bash
./runRiverArchitectLinux.sh       # Linux and macOS
runRiverArchitectWin.bat          # Windows
```

The launchers find the environment themselves and, with no argument, open the sample data
bundled in `sample-data/`. From an activated environment:

```bash
riverarchitect                    # or: python -m riverarchitect
riverarchitect /path/to/project   # start with a project directory
```

The interface renders with Qt (PySide6, or the PyQt5 that comes with QGIS) and falls back to
tkinter when no Qt binding is installed, so it always opens. See the
[interface guide](https://riverarchitect.readthedocs.io/en/latest/guide/gui.html).

Or use the modules directly:

```python
from riverarchitect import raster

dem, dem_profile = raster.read("sample-data/01_Conditions/2100_sample/dem.tif")
depth, depth_profile = raster.read("sample-data/01_Conditions/2100_sample/h001000.tif")

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

depth, profile = raster.read("sample-data/01_Conditions/2100_sample/h000300.tif")
mask, n_pools = raster.disconnected_mask(np.nan_to_num(depth) > 0)
dx, dy = raster.cell_size(profile)
print(f"{n_pools} pools, {mask.sum() * dx * dy:.0f} sqft stranded")
```

### Try it on real data

A real gravel-cobble reach ships in [`sample-data/`](sample-data) - 60 discharges of depth
and velocity, a DEM, grain sizes and a DEM of difference - so there is nothing to download.
The [tutorial](https://riverarchitect.readthedocs.io/en/latest/guide/tutorial.html) runs a
lifespan and design map for angular boulders and a fish stranding assessment over a receding
hydrograph on it. Both scripts are in `examples/` and need no arguments:

```bash
mamba run -n ra-env python examples/lifespan_rocks.py
mamba run -n ra-env python examples/stranding_risk.py
```

More building blocks in the
[quickstart](https://riverarchitect.readthedocs.io/en/latest/guide/quickstart.html).

## What's in the box

| Module | Purpose |
|---|---|
| `riverarchitect.raster` | Raster I/O, alignment, map algebra, interpolation (IDW, kriging, nearest neighbour), connectivity, zonal statistics |
| `riverarchitect.volume` | Triangulated-surface volume integration |
| `riverarchitect.volume_assessment` | Earthworks quantities from a pair of DEMs |
| `riverarchitect.mapping` | QGIS print layouts and multi-page PDF map series |
| `riverarchitect.config` | Paths, units, canonical NoData value |
| `riverarchitect.gui` | Desktop interface: Qt front end with a tkinter fallback |
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
python -m riverarchitect.tools.reconcile_nodata sample-data/01_Conditions/2100_sample --dry-run

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

Sample data lives in [`sample-data/`](sample-data); it is vendored from the
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
