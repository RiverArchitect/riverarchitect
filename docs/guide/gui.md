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

**Morphology (Volumes)** compares a pre-project and a post-project DEM and reports fill,
excavation and net volumes plus the affected areas. The *level of detection* excludes
elevation differences smaller than the survey noise. Volumes are integrated under the
triangulated surface; see {doc}`volumes` for why that matters.

**Mapping** renders a directory of rasters into a PDF map series through QGIS print layouts.

Both run their work on a background thread, so the window stays responsive and shows a
progress indicator while an analysis is going.

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

LifespanDesign, MaxLifespan, SHArC, StrandingRisk, ModifyTerrain and ProjectMaker have no tab
yet. Lifespan mapping and fish stranding can be run as scripts today - {doc}`tutorial` walks
through both, and the scripts are in `examples/`.
