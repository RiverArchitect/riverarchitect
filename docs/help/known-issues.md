# Known issues

Things that are known to be wrong, missing or surprising. Each is documented here rather than left to be discovered.

**Two rasters in the bundled sample condition are inconsistent with their file names.** `u000550.tif` peaks at 1.4 ft/s where its neighbours at 500 and 600 cfs reach 4.5, and `h088053.tif` peaks at 6.8 ft where 42200 cfs reaches 22. Both are byte-for-byte what upstream publishes and are kept deliberately - see `sample-data/README.md`. Expect one odd row in any per-discharge table on that reach.

**River Builder's regime relation can produce an absurd depth.** `H = 165*D50*tau_cr/S` is inversely proportional to slope, so a gentle valley with a coarse bed gives a bankfull depth greater than the channel is wide. The tab reports this instead of building the valley silently, and the answer is to give the bankfull depth explicitly.

**Project Maker leaves some quantities empty.** A rate priced per yard of bank, per culvert or per bridge does not follow from a mapped area, so it is not guessed. The log names what could not be derived; enter those directly.

**The stranding-risk velocity criterion needs a velocity *field*, not a speed.** Conditions ship `u<Q>.tif`, which is a magnitude, and a one-way passability rule needs direction. Without `ux<Q>.tif` and `uy<Q>.tif` the criterion is skipped, and {attr}`riverarchitect.stranding.StrandingRisk.velocity_limited` reports `False` so a result can state which analysis it is. See {doc}`../modules/ecohydraulics`.

**"QGIS is not available" although QGIS is installed.** The bindings are compiled extension modules and load only in the Python minor version they were built for, which is usually the system interpreter rather than the conda environment. The Maps tab names the directory it rejected and the version it needs. See {doc}`../modules/maps`. Never work around it with `PYTHONPATH=/usr/lib/python3/dist-packages` - that silently downgrades numpy, pandas and scipy for every other module.

## How to troubleshoot

**1. Read the log.** Every module logs through the `riverarchitect` logger, and the interface prints it to the console it was started from. Start the launcher from a terminal and keep it visible - most "nothing happened" reports are a message in that stream saying a criterion was skipped.

```python
import logging
logging.basicConfig(level=logging.INFO)
```

**2. Check the condition before the analysis.** One line prints what the folder provides, what it lacks, and the raster naming the discovery expects:

```python
from riverarchitect.condition import Condition

print(Condition("2100_sample").describe())
```

For a closer look:

```python
c = Condition("2100_sample")
print(c.validate())                           # problems as a list, empty when usable
print(c.return_periods)                       # empty? lifespan mapping has no axis
print(len(c.depth_rasters), len(c.all_depth_rasters()))
for name in (c.dem_raster, c.d2w_raster, c.detrended_raster, c.grain_raster, c.mu_raster):
    print(name, c.exists(name))               # False means that criterion is skipped
```

Two hydraulic raster naming forms are accepted: plain integers (`h000550.tif` models 550 cfs or m³/s) and a decimal form that writes the discharge as `%010.3f` with `_` as the decimal separator, so `h000001_060.tif` models 1.06.

**3. Plot maximum depth and velocity against discharge.** Ten seconds of this finds a mislabelled or corrupt hydraulic raster, which nothing in the software can detect for you.

**4. Reduce it.** Run one feature, one discharge, one species. The modules take explicit arguments precisely so a problem can be isolated.

**5. Check the units.** A unit mismatch never raises. If every threshold seems to bite in the wrong place by a factor near 3.28, this is why.

## Error messages

| Message | What it means | What to do |
|---|---|---|
| `no such condition folder: ...` | the condition name does not match a folder under `01_Conditions/` | check the project directory in the status bar |
| `condition <x> has no usable raster to define the grid` | no grain, DEM or depth raster was found | the condition is empty or misnamed; see the naming conventions |
| `condition <x> has no d2w raster` (Terraforming) | `d2w.tif` is missing | run **Get Started ▸ water surface, depth and depth to water table** |
| `no lf_*.tif rasters in <dir>` | Max Lifespan was pointed at a folder with no lifespan maps | run Lifespan Design first |
| `no feature action rasters in <dir>` | Terraforming was pointed at a folder with no `best_*.tif` | run Max Lifespan first |
| `no such species in Fish.xlsx: <x>` | the species is not in the workbook | the message lists the available names; matching ignores case and spacing |
| `no depth rasters found for condition <x>` | the discharges requested have no `h<Q>.tif` | check the naming: `h000550.tif`, or `h000001_060.tif` for a decimal discharge |
| `the dimensionless bed shear stress is NoData everywhere` | the grain raster does not overlap the hydraulics, or holds something other than grain diameters | check `dmean.tif` units and extent; the `regime<Q>.tif` diagnostic maps show where the closure was valid |
| `no discharge has both a depth and a velocity raster` | `h<Q>.tif` and `u<Q>.tif` do not pair up | every depth raster needs a velocity raster at the same discharge |
| `no flow in the record falls inside the season given` | the flow record does not cover that lifestage's season | use a longer record, or a lifestage whose season it covers |
| `a Gumbel fit needs at least 10 annual peaks` | too short a record for a return period estimate | use a longer record, or supply return periods from a formal analysis |
| `the flow record has too few days in the <year> recession period` | the record does not cover that season | choose a year the record covers |
| `no cell falls into any morphological unit` | depth and velocity are in different units from the threshold table | check the unit system |
| `DLL load failed while importing ...` (Windows) | the QGIS bindings were found but their Qt, GDAL and PROJ libraries were not | set `QGIS_PREFIX_PATH`, or start from an OSGeo4W shell |

## Warning messages

These do not stop an analysis. They are the ones worth reading anyway, because each means a result is narrower than you may assume.

| Message | What it means |
|---|---|
| `<feature>: no code for morphological unit(s) ...` | those units are not in the morphological unit table, so they are not part of the criterion |
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

Report a problem at <https://github.com/RiverArchitect/riverarchitect/issues>, with the log output, the `input_definitions.inp`, and the output of the condition check above.
