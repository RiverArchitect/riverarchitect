# Software setup

Installing River Architect, what it needs, how its files are organised, and where it writes
its logs. This is section 1 of the original wiki's *Installation*, rewritten for the
open-source release.

```{admonition} What changed since the ArcGIS version
:class: important

River Architect no longer requires **ArcGIS Pro**, an **Esri licence** or the **Spatial
Analyst** extension, and it is no longer Windows-only. Everything the original did with
`arcpy` now runs on **GDAL** through rasterio, with numpy and scipy for the algebra and
geopandas for the vector side. Map production runs on **QGIS** print layouts instead of
ArcGIS layout templates.

The practical consequence for setup: you install a conda environment, not a GIS. The one
exception is the Maps tab, which needs the QGIS Python bindings - see
{doc}`../modules/maps`.
```

```{toctree}
:maxdepth: 2
:caption: In this section

../guide/installation
../guide/installation_detailed
```

```{toctree}
:maxdepth: 1
:caption: Reference

Program file structure, requirements and logfiles (legacy) <../wiki/Installation>
```

## The short version

```bash
git clone https://github.com/RiverArchitect/riverarchitect.git
cd riverarchitect
mamba env create -f environment.yml
mamba activate ra-env
pip install -e ".[all]"
./runRiverArchitectLinux.sh          # runRiverArchitectWin.bat on Windows
```

The launcher opens the interface on the bundled sample data. Open **Help ▸ Live Guide:
Example** and work through {doc}`../guide/example_walkthrough`.

## Requirements at a glance

| | |
|---|---|
| Python | 3.9 or newer; 3.12 in the shipped environment |
| Core | numpy, scipy, rasterio, geopandas, shapely, pyproj, pandas, openpyxl |
| Interface | PySide6, or the PyQt5 that QGIS brings; tkinter is the fallback and is always present |
| Mapping | QGIS 3.x and its Python bindings, in the interpreter QGIS was installed with |
| Optional | pykrige (kriging), rasterstats (zonal statistics), whitebox (terrain), matplotlib |
| Operating system | Linux, macOS, Windows |

None of these needs a licence.

## Where things live

A **project directory** is the root that everything resolves against. Set it with the
`Project` menu, with the `RIVERARCHITECT_HOME` environment variable, or as the first
argument to the launcher.

```text
<project>/
├── 00_Flows/<condition>/       flow duration curves, daily flow records
├── 01_Conditions/<condition>/  the input rasters and input_definitions.inp
├── 02_Maps/                    QGIS projects and exported PDFs
└── Output/<module>/<condition>/  every analysis result
```

The **package** is separate from your data and holds only code and lookup tables
(`Fish.xlsx`, `morphological_units.xlsx`, `recruitment_parameters.xlsx`, QGIS layer styles).
Nothing writes into it.

## Logfiles

Every module logs through the standard library `logging` module, to the logger named
`riverarchitect`. The interface prints that stream to the console it was started from. To
capture it to a file:

```python
import logging
logging.basicConfig(filename="riverarchitect.log", level=logging.INFO)
```

The original wrote fixed `logfile.log` files into each module's own folder. Routing through
`logging` instead means the messages can go wherever a project wants them, and that a module
used as a library does not scatter files.
