# Troubleshooting and error message handling

Section 6 of the original wiki. What is known to be limited, how to diagnose a problem, and
what the messages mean.

```{admonition} The legacy error list is about arcpy, and no longer applies
:class: important

The original's troubleshooting page is 13 000 words, and most of it decodes `arcpy`
`ExecuteError` codes, Spatial Analyst licence failures and `.aprx` template problems. **None
of those can occur in this release** - there is no `arcpy`, no licence and no `.aprx`. The
page is preserved at the bottom for anyone still running 1.x, and for the analysis background
in it, but start here.
```

## Known issues

**Lifestage names were hard-coded, and no longer are.** The original required lifestages to
be named `spawning`, `fry`, `ammocoetes`, `juvenile`, `adult`, `hydrologic year`, `season`,
`depth > x` or `velocity > x`, because `cFish.ls_col_add` mapped each name to a fixed column
offset. {class}`riverarchitect.sharc.FishDatabase` reads the labels *from the workbook* at
the four possible offsets instead, so a species may name its lifestages whatever it likes.

**Two rasters in the bundled sample condition are inconsistent with their file names.**
`u000550.tif` peaks at 1.4 ft/s where its neighbours at 500 and 600 cfs reach 4.5, and
`h088053.tif` peaks at 6.8 ft where 42200 cfs reaches 22. Both are byte-for-byte what
upstream publishes and are kept deliberately - see `sample-data/README.md`. Expect one odd
row in any per-discharge table on that reach.

**Not ported.** The pool-riffle morphology designer ({doc}`tools`) and the velocity
criterion of Stranding Risk. Both are documented where they belong rather than failing
silently. Every analysis module of the ArcGIS version is otherwise present.

**River Builder's regime relation can produce an absurd depth.** ``H = 165*D50*tau_cr/S`` is
inversely proportional to slope, so a gentle valley with a coarse bed gives a bankfull depth
greater than the channel is wide. That is the original's formula reproduced faithfully; the
tab reports it instead of building the valley silently, and the answer is to give the
bankfull depth explicitly.

**Project Maker leaves some quantities empty.** A rate priced per yard of bank, per culvert
or per bridge does not follow from a mapped area, so it is not guessed. The log names what
could not be derived; enter those directly.

**"QGIS is not available" although QGIS is installed.** The bindings are installed for the
*system* interpreter and River Architect may be running in a conda environment. It searches
for them and adds them itself; when that fails the Maps tab names the directory it rejected
and why. See {doc}`modules/maps`. Never work around it with
`PYTHONPATH=/usr/lib/python3/dist-packages` - that silently downgrades numpy, pandas and
scipy for every other module.

## How to troubleshoot

**1. Read the log.** Every module logs through the `riverarchitect` logger, and the
interface prints it to the console it was started from. Start the launcher from a terminal
and keep it visible - most "nothing happened" reports are a message in that stream saying a
criterion was skipped.

```python
import logging
logging.basicConfig(level=logging.INFO)
```

**2. Check the condition before the analysis.** In order:

```python
from riverarchitect.condition import Condition

c = Condition("2100_sample")
print(c.return_periods)                       # empty? lifespan mapping has no axis
print(len(c.depth_rasters), len(c.all_depth_rasters()))
for name in (c.dem_raster, c.d2w_raster, c.detrended_raster, c.grain_raster, c.mu_raster):
    print(name, c.exists(name))               # False means that criterion is skipped
```

**3. Plot maximum depth and velocity against discharge.** Ten seconds of this finds a
mislabelled or corrupt hydraulic raster, which nothing in the software can detect for you.

**4. Reduce it.** Run one feature, one discharge, one species. The modules take explicit
arguments precisely so a problem can be isolated.

**5. Check the units.** A unit mismatch never raises. If every threshold seems to bite in the
wrong place by a factor near 3.28, this is why.

## Error messages

| Message | What it means | What to do |
|---|---|---|
| `no such condition folder: ...` | the condition name does not match a folder under `01_Conditions/` | check the project directory in the status bar |
| `condition <x> has no usable raster to define the grid` | no grain, DEM or depth raster was found | the condition is empty or misnamed; see the naming conventions |
| `condition <x> has no d2w raster` (Terraforming) | `d2w.tif` is missing | run **Get Started ▸ water surface, depth and depth to water table** |
| `no lf_*.tif rasters in <dir>` | Max Lifespan was pointed at a folder with no lifespan maps | run Lifespan Design first |
| `no feature action rasters in <dir>` | Terraforming was pointed at a folder with no `best_*.tif` | run Max Lifespan first |
| `no such species in Fish.xlsx: <x>` | the species is not in the workbook | the message lists the available names; matching ignores case and spacing |
| `no depth rasters found for condition <x>` | the discharges requested have no `h<Q>.tif` | check the six-digit zero-padded naming |
| `no discharge has both a depth and a velocity raster` | `h<Q>.tif` and `u<Q>.tif` do not pair up | every depth raster needs a velocity raster at the same discharge |
| `no flow in the record falls inside the season given` | the flow record does not cover that lifestage's season | use a longer record, or a lifestage whose season it covers |
| `a Gumbel fit needs at least 10 annual peaks` | too short a record for a return period estimate | use a longer record, or supply return periods from a formal analysis |
| `the flow record has too few days in the <year> recession period` | the record does not cover that season | choose a year the record covers |
| `no cell falls into any morphological unit` | depth and velocity are in different units from the threshold table | check the unit system |
| `DLL load failed while importing ...` (Windows) | the QGIS bindings were found but their Qt/GDAL/PROJ libraries were not | set `QGIS_PREFIX_PATH`, or start from an OSGeo4W shell |

## Warning messages

These do not stop an analysis. They are the ones worth reading anyway, because each means a
result is narrower than you may assume.

| Message | What it means |
|---|---|
| `<feature>: no code for morphological unit(s) ...` | those units are not in the morphological unit table, so they are not part of the criterion. The original swallowed this in a bare `except` and dropped the whole criterion without a word |
| `no morphological-unit code table - skipping the MU criterion` | neither a condition-local nor the packaged table could be read |
| `no discharge reaches the <n>-year design flood for <feature>` | no design map is written, because the condition models nothing that rare |
| `no flow duration workbook for <code> - SHArea not computed` | usable areas are still reported, but there is nothing to integrate them over |
| `could not polygonise <feature>` | the rasters were written; only the GeoPackage failed, usually a missing vector driver |
| `no flow record in the bed preparation period` | recruitment scores bed preparation as zero everywhere |
| `nothing is wetted at the target discharge` | stranding falls back to the largest region at each discharge separately |
| `no wetted cell in <raster> - cannot locate a thalweg` | the reference discharge is dry; choose a higher one |
| `QGIS (qgis.core) is not available - mapping is disabled` | every analysis still works; only the Maps tab is off. The message names what was searched and what to install |
| `QGIS bindings found in <dir> and added to sys.path` | not a problem: discovery worked, and the directory went to the *end* of the path so your own packages keep priority |

## Getting help

Report a problem at
<https://github.com/RiverArchitect/riverarchitect/issues>, with the log output, the
`input_definitions.inp`, and the output of the condition check above.

## Legacy page

```{toctree}
:maxdepth: 1

Error messages and troubleshooting for River Architect 1.x (legacy) <wiki/Troubleshooting>
```
