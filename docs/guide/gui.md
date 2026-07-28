# The graphical interface

River Architect ships a desktop interface with one tab per module. It is a front end over
the same functions the scripts in {doc}`tutorial` call, so anything the interface does can
also be done from Python, and vice versa.

## Starting it

::::{tab-set}

:::{tab-item} Linux / macOS
:sync: linux

```bash
./runRiverArchitectLinux.sh                  # bundled sample data
./runRiverArchitectLinux.sh /data/my_project # your own project directory
```

The launcher finds an interpreter itself: an explicit `RA_PYTHON`, then a conda or mamba
environment named `ra-env`, then whatever environment is active, then `python3` on the
`PATH`. It checks that numpy and rasterio import before opening a window, so a broken
install produces a readable message instead of a traceback.
:::

:::{tab-item} Windows
:sync: windows

```powershell
runRiverArchitectWin.bat
runRiverArchitectWin.bat D:\my_project
```

Double-clicking the `.bat` file works too. It looks for an `ra-env` environment under the
usual Miniforge, Mambaforge, Miniconda and Anaconda locations before falling back to the
`python.exe` on the `PATH`.

This replaces the ArcGIS-era launcher, which called ArcGIS Pro's `propy.bat` and failed
without a Spatial Analyst licence.
:::

:::{tab-item} Installed package
:sync: installed

```bash
riverarchitect                     # console script
python -m riverarchitect           # equivalent
riverarchitect sample-data         # start with a project directory
```
:::

::::

With no argument, the launchers open the `sample-data/` directory bundled with the
repository, so a fresh clone starts with something to look at.

## Two front ends

```{list-table}
:header-rows: 1
:widths: 12 30 58

* - Backend
  - Requires
  - Notes
* - **Qt**
  - PySide6, or the PyQt5 that comes with QGIS
  - The default. Native widgets, correct HiDPI scaling, a real menu bar and a status bar.
* - **tkinter**
  - nothing beyond the standard library
  - The fallback, so the interface always opens. Functionally equivalent, plainer.
```

The choice is automatic: Qt when a binding is importable, tkinter otherwise. Force one with

```bash
RIVERARCHITECT_GUI=tk riverarchitect
```

which is mainly useful when a Qt install is misbehaving. In code:

```python
from riverarchitect.gui import available_backends, select_backend

print(available_backends())     # e.g. ['qt', 'tk']
print(select_backend())         # 'qt'
```

```{admonition} Why not just tkinter?
:class: note

tkinter is in the standard library and needs no dependency, which is exactly why it is kept
as the fallback. What it does not give you is a native look on any platform, HiDPI scaling,
or layout that survives a font-size change - and River Architect is used on projector
screens and on 4K laptops. Qt handles all three, and the project already links Qt through
QGIS for map production, so it adds no new class of dependency.

PySide6 is the Qt binding used because it is LGPL, installs from PyPI and conda-forge on
every supported platform, and is the binding the Qt Company maintains.
```

## The QGIS interpreter

The Mapping tab needs the QGIS Python bindings, which are compiled against the interpreter
QGIS was installed with - normally the system Python, not a conda environment. Started from
`ra-env`, the Mapping tab greys itself out and explains what is missing; every other tab
works normally.

To get a working Mapping tab, start with the interpreter that owns the bindings:

```bash
RA_PYTHON=/usr/bin/python3 ./runRiverArchitectLinux.sh
```

```powershell
set RA_PYTHON=C:\OSGeo4W\bin\python.exe
runRiverArchitectWin.bat
```

That interpreter has PyQt5 rather than PySide6, and the interface runs on it unchanged - the
Qt front end supports both bindings for exactly this reason. See {doc}`qgis_mapping`.

```{admonition} The trade runs both ways
:class: warning

A QGIS interpreter usually has no rasterio, just as a conda environment has no QGIS. So each
interpreter gives you one half:

| Started with | Analysis tabs | Mapping tab |
|---|---|---|
| `ra-env` | enabled | disabled, explains why |
| the QGIS interpreter | disabled, explains why | enabled |

A disabled tab says what is missing rather than failing when you click *Compute*, and the
launchers warn at startup. To get both at once, install rasterio into the QGIS interpreter -
but the usual and lower-risk arrangement is to run the analysis in `ra-env`, write GeoTIFFs,
and then point the Mapping tab at them from the QGIS interpreter.
```

## Tabs

The top-level tabs group the modules the way the ArcGIS version did, and three of them open
onto sub-tabs:

```text
Get Started
Lifespan        -> Lifespan Design | Max Lifespan
Morphology      -> Volume Assessment
Ecohydraulics   -> Habitat Area (SHArC) | Stranding Risk | Riparian Seedling Recruitment
Maps
```

**Get Started** prepares a condition. Nothing here is an analysis in its own right; it
produces the derived rasters the others read - a detrended DEM, an interpolated water
surface and the depth and depth-to-water-table rasters that follow from it, a morphological
unit classification, the `input_definitions.inp`, and a one-off alignment of every raster
onto a single grid. Start here with a condition that only has a DEM and 2D model output.

**Lifespan Design** predicts how many years each restoration feature survives at every
cell, from the flood return periods in the condition's `input_definitions.inp`, and the
dimensions it needs to reach a target lifespan. Tick one or more features; the defaults
reproduce the threshold values of the original `threshold_values.xlsx`. Writes
`lf_<feature>.tif` and, where the feature supports it, `ds_<feature>.tif`. See
{doc}`tutorial` for a worked example and {doc}`../wiki/LifespanDesign` for the physics.

**Max lifespan** answers the planner's question rather than the engineer's: given several
feature lifespan maps, *which* feature belongs here? It reads the lifespan tab's output,
takes the cell-wise maximum, and writes one best-feature mask and polygon layer per feature
plus `max_lf.tif`. Ties are kept rather than broken, so a cell where two features both reach
the maximum appears in both layers - the choice is yours to make on other grounds.

**Morphology (Volumes)** compares a pre-project and a post-project DEM and reports fill,
excavation and net volumes plus the affected areas. The *level of detection* excludes
elevation differences smaller than the survey noise. Volumes are integrated under the
triangulated surface; see {doc}`volumes` for why that matters.

**Habitat Area (SHArC)** applies the habitat suitability curves of a species and lifestage
to the depth and velocity rasters. Each discharge gets a composite suitability raster, the
area above a threshold is the usable habitat at that flow, and integrating those over the
flow duration curve gives the **Seasonal Habitat Area** - the single number a restoration
project is usually judged on. The curves come from the packaged `Fish.xlsx`; the flow
duration workbook is looked up by the four-letter species code, so juvenile Chinook salmon
needs `00_Flows/<condition>/flow_duration_chju.xlsx`.

**Riparian Seedling Recruitment** maps where cottonwood and willow seedlings can establish
and survive their first season. Four objectives are each scored 1, 0.5 or 0 - was the
seedbed prepared by a winter flow, did the water table recede slowly enough, was the
seedling drowned, was it scoured out - and multiplied, so a zero anywhere is a zero overall.
This is the only tab that needs a **daily flow record**: the other modules care which flows
are possible, recruitment cares when they happened.

**Stranding Risk** walks a falling hydrograph and finds the wetted areas that
lose their connection to the main channel, which is where fish strand. Pick a species and
lifestage to set the minimum swimming depth, or type your own. Writes one
`disconnected_<Q>.tif` per discharge, a `Q_disconnect.tif` recording the flow at which each
cell becomes a trap, and a polygon layer of the pools at the worst discharge.

**Mapping** renders a directory of rasters into a PDF map series through QGIS print layouts.

Every tab runs its work on a background thread, so the window stays responsive and shows a
progress indicator while an analysis is going.

```{admonition} The minimum swimming depth is the choice that matters
:class: tip

In the stranding tab, `h_min` moves the result more than anything else, and it is a
biological choice rather than a numerical one. At `h_min = 0` every wet cell counts and much
of the pool count is single cells at the wetted edge - real in the raster, meaningless in
the river. State the value you used alongside any result.
```

## Menus

**Project** sets the project directory - the root that `01_Conditions/`, `00_Flows/`,
`02_Maps/` and `Output/` resolve against. The status bar shows the current one. It can also
be set with `RIVERARCHITECT_HOME` or as an argument to the launcher.

**Units** switches every tab between U.S. customary and SI. It changes the labels and the
default level of detection; it does **not** convert your rasters, which must already be in
the unit system you select.

**Tools** runs `reconcile_nodata` over a condition folder, normalising inconsistent NoData
sentinels. The NoData mask is preserved exactly; only the sentinel changes.

## Not yet in the interface

ModifyTerrain/RiverBuilder and ProjectMaker have no tab yet. Their analysis logic is
described in the legacy wiki pages linked from the documentation index, and `raster.py`
already provides the primitives each of them needs.

## Everything is also a Python API

The tabs are a front end over ordinary modules, so anything the interface does can be
scripted and put under version control:

```python
from riverarchitect import preprocessing
from riverarchitect.lifespan import LifespanDesign
from riverarchitect.maxlifespan import MaxLifespan
from riverarchitect.recruitment import RecruitmentPotential
from riverarchitect.sharc import SHArC
from riverarchitect.stranding import StrandingRisk

preprocessing.build_product("2100_sample", "detrended", discharge=300)
LifespanDesign("2100_sample").run(["rocks", "wood", "cot"])
MaxLifespan("sample-data/Output/LifespanDesign/2100_sample").run()
SHArC("2100_sample").run("Chinook Salmon", "juvenile")
StrandingRisk.for_fish("2100_sample", "Chinook salmon", "fry").run()
RecruitmentPotential("2100_sample", "daily_flows.csv", year=2020).run()
```
