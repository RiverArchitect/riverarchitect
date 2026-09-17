# The worked example: the whole chain on the sample reach

This page runs **every** module in order on the sample data: prepare the condition, map feature lifespans, pick the best feature per cell, terraform the ground those features need, then the three ecohydraulic analyses. Every number below was produced by the code on this page.

The same walkthrough is built into the interface. Open **Help ▸ Live Guide: Example** and it steps through these stages beside the window, sets the project directory to the sample data for you, and brings the relevant tab to the front as you go. It can also play itself, jump to any step by name, and resume where you left it. The guide and this page are the same content: {mod}`riverarchitect.guide` holds it as data that both front ends render.

The numbered sections here are the guide's steps 1 to 14; the guide's step 0 is the introduction you are reading.

```{admonition} How this differs from the tutorial
:class: note

{doc}`tutorial` builds two analyses **out of raster primitives**, to show what the modules do underneath. This page uses the modules themselves and covers the whole chain instead. Read the tutorial to understand the mechanics; read this one to run a project.
```

## Before you start

```bash
git clone https://github.com/RiverArchitect/riverarchitect.git
cd riverarchitect
export RIVERARCHITECT_HOME="$PWD/sample-data"
```

The reach, `2100_sample`, is a real gravel-cobble reach in a Mediterranean climate: 359 x 173 cells at 3 ft resolution, in **U.S. customary units**, with a DEM, mean grain size, a DEM of difference and 60 pairs of modelled depth and velocity rasters between 300 and 88053 cfs.

Set the units to U.S. customary first: the program starts in SI, and every analysis below stops with a `UnitMismatchError` if the selected units disagree with the CRS of these rasters (EPSG:6418, in U.S. survey feet). In Python, pass `unit="us"` to each call. See {ref}`the unit warning in Get Started <units-warning>`.

```python
from riverarchitect import config
config.set_project_home("sample-data")
```

```{admonition} Two rasters in this condition are bad, and that is useful
:class: warning

`u000550.tif` tops out at 1.4 ft/s where its neighbours at 500 and 600 cfs reach 4.5 ft/s. `h088053.tif` peaks at 6.8 ft where 42200 cfs reaches 22 ft - a low-flow result wearing a flood's file name. Both are byte-for-byte what upstream publishes, and they are left in place deliberately: real conditions contain rasters like these, nothing in the software can detect them for you, and spotting them in a result table is part of the work. Their effect is called out at each step below.
```

## 1. Set up the project

Everything below runs on the bundled sample data, so that every number can be checked. This is the part you repeat on your own reach: turning 2D model output into a project River Architect can read.

A project is a directory with four sub-directories, and every path resolves against it:

```text
<project>/
├── 00_Flows/<condition>/       flow duration curves and daily flow records
├── 01_Conditions/<condition>/  the input rasters and input_definitions.inp
├── 02_Maps/                    QGIS projects and exported PDFs
└── Output/<module>/<condition>/  every analysis result
```

Point the program at it with **Project ▸ Set project directory**, with `RIVERARCHITECT_HOME`, or with {func}`riverarchitect.config.set_project_home`. A *condition* is one state of the river - existing, or planned - and the whole chain runs per condition.

Inside a condition, names carry meaning. Each modelled discharge is a pair, `h<Q>.tif` for water depth and `u<Q>.tif` for depth-averaged velocity, with the discharge zero-padded to six digits: `h000750.tif` and `u000750.tif` are 750 cfs. A discharge with only one of the two is skipped by every hydraulic module. Alongside them go `dem.tif`, a mean or median grain size raster, and optionally a DEM of difference for the scour and fill criteria.

`input_definitions.inp` decides how much of the analysis you get. It maps each modelled discharge to a flood return period, and lifespan mapping uses only the discharges that carry one - here, 17 of the 60 rasters on disk. **Get Started ▸ Build ▸ `input_definitions.inp`** writes a starting file from the discharges it finds; the return periods are yours to fill in from a flood frequency analysis.

```{admonition} Reconcile NoData before anything else
:class: tip

NoData arrives from third-party models as `-9999`, `-3.4e38`, `3.4e38` or a plain `0`, sometimes varying within one dataset, and a `0` meant as NoData reads as a real depth of zero. **Tools ▸ Reconcile NoData in a condition** rewrites a folder to one sentinel, preserving the mask exactly. Run it once, on import.
```

## 2. Prepare the condition

Nothing later works without this. Lifespan mapping reads `d2w.tif` and `dem_detrend.tif`; the morphological-unit criteria read `mu.tif`. A missing input does not raise - the criterion that needed it is simply dropped, and the map that comes out looks like an answer.

Use **750 cfs** as the reference discharge: an in-channel low flow, which is what a detrended DEM and a water surface should be keyed to.

```python
from riverarchitect import preprocessing

for product in ("detrended", "water", "mu"):
    for line in preprocessing.build_product("2100_sample", product, discharge=750,
                                            unit="us"):
        print(line)

# The flow analysis needs the daily record instead of a reference discharge.
for line in preprocessing.build_product(
        "2100_sample", "flows", unit="us",
        flow_series="sample-data/00_Flows/2100_sample/flow_series_2020.csv"):
    print(line)
```

| Product | Writes | What it is |
|---|---|---|
| `detrended` | `dem_detrend.tif` | elevation above the local thalweg, so elevations are comparable along the reach |
| `water` | `wle.tif`, `h_interp.tif`, `d2w.tif` | a water surface extrapolated from the wetted area, and the depth and depth-to-groundwater rasters derived from it |
| `mu` | `mu.tif` | pools, riffles, runs and the rest, classified from depth and velocity |
| `flows` | `00_Flows/2100_sample/flow_duration_<code>.xlsx` | one seasonal flow duration curve per species and lifestage, from `flow_series_2020.csv` |

```{admonition} Building a product overwrites the condition's copy
:class: warning

With no output directory, `build_product` writes into the **condition folder** - so rebuilding `dem_detrend.tif`, `d2w.tif` or `mu.tif` replaces the one that shipped with it. That is deliberate and matches the original: the products *are* part of the condition, and the modules read them from there.

It does mean the sample condition is no longer pristine after a run, and that a later comparison against the shipped rasters compares them with themselves. Two ways round it:

* pass an output directory (`output_dir=...`, or **Output directory** in the tab) and build into a scratch folder, which is what the comparison figures on this page were produced with; or
* work on a copy of `sample-data/`, which is what the Live Guide's *Use the sample data* button does not do - it points at the directory in place.

`git checkout sample-data/` restores it in a clone.
```

The condition already ships `dem_detrend.tif`, `d2w.tif` and `mu.tif`, so you can check what you built against them:

```text
dem_detrend.tif   r = 0.994   mean offset +0.25 ft
d2w.tif           r = 0.999   mean offset +0.26 ft
```

The constant offset is the different reference discharge, not an error.

Eight morphological units can be delineated hydraulically on this reach: chute, fast and slow glide, pool, riffle, riffle transition, run and slackwater. The packaged table holds another twenty floodplain units - floodplain, terrace, levee, pond and so on - which carry a code but no depth or velocity range because they are not delineated hydraulically. `mu.tif` therefore never contains them, but the lifespan feature thresholds name them, so their codes are kept.

## 3. Lifespan and design mapping

For each feature, per cell: how many years is it expected to survive here? Each modelled discharge carries a flood return period from `input_definitions.inp`, and for every criterion the feature has a threshold for, the analysis finds the lowest return period at which the threshold is exceeded. Cells that survive every modelled flood stay NoData - their lifespan is longer than the largest modelled event and cannot be quantified from the data.

```python
from riverarchitect.lifespan import LifespanDesign

results = LifespanDesign("2100_sample", unit="us").run()
```

| Feature | Mapped area (sqft) | Lifespan range (yr) |
|---|---:|---|
| Streamwood (`wood`) | 332 532 | 1.0 - 40.0 |
| Box Elder, Cottonwood, Willow, and their established forms | 124 542 each | 1.0 - 5.0 |
| Other nature-based eng. (`bio`) | 74 574 | 50.0 |
| Generic planting (`Generic`, `Generic_est`) | 44 775 each | 1.0 - 50.0 |
| White Alder (`whi`, `Whi_est`) | 16 200 each | 1.0 - 50.0 |
| Side channels (`sidech`) | 11 817 | 1.0 - 50.0 |
| Gravel: In (`gravin`) | 5 490 | 1.0 - 50.0 |
| Backwater (`backwt`) | 2 295 | 1.0 |
| Grading (`grade`) | 279 | 1.13 - 20.0 |
| Angular boulders (`rocks`) | 18 | 40.0 |
| Gravel: Out (`gravou`), fine sediment (`fines`) | 0 | - |

Alongside the maps, each discharge leaves four bed-shear rasters: `ts<Q>.tif` (the dimensionless Shields stress the thresholds are compared against), `tb<Q>.tif` (u*²), `hks<Q>.tif` (relative submergence h/k_s) and `regime<Q>.tif` (which closure applied: 1 Rickenmann-Recking, 2 blended, 3 Keulegan-Einstein, 0 invalid). On this reach about 95 % of wet cells fall in regime 1 - see [the migration notes](arcpy_migration.md) for why that matters. To produce the same four for a whole condition without running a lifespan analysis, use **Get Started ▸ dimensionless bed shear stress (taux)**, which writes them into the condition folder beside `h<Q>.tif` and `u<Q>.tif`.

Three of those rows repay a second look.

**Angular boulders map only 18 sqft** because the feature is restricted to cells that scour by 3 ft or more, and this reach barely does. Without that restriction the same criterion maps 66 000 sqft - `examples/lifespan_rocks.py` prints both. The restriction is doing real work, not failing.

**Several features report exactly the same area.** Box Elder, Cottonwood and Willow have different depth and velocity thresholds, but at the largest floods every cell inside their shared depth-to-water-table band of 1 to 7 ft fails eventually. The mapped *extent* is therefore identical; the lifespans within it are not.

**`gravou` and `fines` map nothing.** `gravou` is restricted to floodplain morphological units, and `mu.tif` on this reach contains only instream units, because that is all a depth-and-velocity classification can produce. `fines` needs a grain size below 0.0067 ft and this is a gravel-cobble reach. Both zeros are the data answering the question.

Design maps - the stable grain size at the feature's design flood - are written for `backwt`, `rocks`, `gravin` and `gravou`.

## 4. Your own threshold values

Section 3 ran on the published defaults. This is how to replace them, and it is the difference between a demonstration and a design you can defend.

A threshold is a statement about your model's output. Each feature carries some of `h_max` and `u_max`, the depth and velocity beyond which it fails; `froude_max`; `tau_cr`, the critical dimensionless bed shear stress, compared against the `ts<Q>.tif` rasters of section 2; `d2w_min` and `d2w_max`, the depth-to-water-table band a planting needs; `det_min` and `det_max`, a detrended elevation band; `grain_max`; and `scour_rate` and `fill_rate`, read from the DEM of difference. Every criterion is optional, and one whose threshold is unset - or whose input raster the condition does not have - is skipped. That is why a sparsely defined feature still produces a map, and why a missing `d2w.tif` shrinks the analysis instead of failing it.

In the interface: **Lifespan Design ▸ Save the defaults ...** writes the whole set out, you edit it, and **Threshold values** loads it back. The same round trip in Python:

```python
from riverarchitect.lifespan import (LifespanDesign, load_threshold_workbook,
                                     write_threshold_workbook)

write_threshold_workbook("threshold_values.xlsx")      # one column per feature
features = load_threshold_workbook("threshold_values.xlsx")

analysis = LifespanDesign("2100_sample", unit="us", features=features)
analysis.run(["rocks"], output_dir="Output/LifespanDesign/2100_sample")
```

An unedited round trip must reproduce section 3 exactly - Angular boulders at 18 sqft. That check is worth making: it confirms the file is being read the way you think it is before you start changing numbers.

```{admonition} The workbook's values are used exactly as written
:class: warning

They are U.S. customary and unconverted. Cottonwood really is keyed to a water table 1 to 7 **feet** down, and there is no hidden conversion waiting to fix a metric number typed into the sheet. See *Threshold units are a round trip* in {doc}`arcpy_migration`.
```

The `Morphological units` rows use a different vocabulary from the morphological unit table itself - `agriplain` against `agricultural plain`. The aliases are bridged for you, but a name that appears in neither vocabulary silently matches nothing rather than raising.

## 5. Best feature per cell

Which feature belongs here, and how long will it last?

```python
from riverarchitect import config
from riverarchitect.maxlifespan import MaxLifespan
import os

lifespan_dir = os.path.join(config.dir_output("LifespanDesign"), "2100_sample")
summary = MaxLifespan(lifespan_dir, unit="us").run()
```

The cell-wise maximum across the lifespan rasters is `max_lf.tif`, and a feature wins a cell where its own lifespan equals that maximum.

| Feature | Area (sqft) | Share | Max lifespan |
|---|---:|---:|---:|
| `wood` | 253 134 | 74.9% | 40 yr |
| `bio` | 74 574 | 22.1% | 50 yr |
| `Generic`, `Generic_est` | 13 599 each | 4.0% | 50 yr |
| `wil`, `Wil_est` | 12 762 each | 3.8% | 5 yr |
| `cot`, `cot_est` | 10 755 each | 3.2% | 5 yr |
| `box`, `Box_est` | 6 237 each | 1.8% | 3.27 yr |
| `gravin` | 2 538 | 0.8% | 50 yr |
| `whi`, `Whi_est` | 2 286 each | 0.7% | 50 yr |
| `sidech` | 2 097 | 0.6% | 50 yr |
| `backwt` | 1 251 | 0.4% | 1 yr |
| `grade` | 63 | 0.0% | 20 yr |

Total mapped: 337 806 sqft. The shares add to more than 100% because **ties are kept**: a cell where two features both reach the maximum appears in both layers. That is deliberate, and it is what the original did - it tells the planner the choice is theirs. Each winner is also polygonised into a GeoPackage, ready to draw as action areas.

## 6. Terraforming and earthworks

{mod}`riverarchitect.terraforming` asks what the terrain would have to look like for the features of section 5 to work, and {mod}`riverarchitect.volume_assessment` asks what that costs in earth movement.

```python
import os
from riverarchitect import config
from riverarchitect.terraforming import Terraforming
from riverarchitect.volume_assessment import VolumeAssessment

actions = os.path.join(config.dir_output("MaxLifespan"), "2100_sample")
result = Terraforming("2100_sample", actions, unit="us",
                      features=["wil", "cot", "box", "Generic"]).run()

quantities = VolumeAssessment("sample-data/01_Conditions/2100_sample/dem.tif",
                              result["dem_raster"], unit="us").run()
```

| | |
|---|---:|
| Max. depth to water table | 7 ft |
| Cells lowered | 417 |
| Area lowered | 3 753 sqft |
| Excavated volume | 11 744 cubic ft (435 cubic yd) |
| Deepest cut | 9.07 ft |
| Volume Assessment excavation | 416 cubic yd |

The two totals differ by about 5 per cent because Terraforming sums the cut over whole cells while Volume Assessment integrates between cell *centres* and applies a level of detection. Quote the Volume Assessment figure - it is the one a contractor will recognise.

`wil`, `cot` and `box` lower nothing here, and that is correct: their `best_*.tif` masks only cover cells whose depth to the water table is already inside their 1 - 7 ft band. `Generic` has no depth-to-water criterion, so it is planned on ground that does need lowering.

## 7. Habitat suitability and usable area (SHArC)

Habitat suitability curves from `Fish.xlsx` map depth and velocity onto an index between 0 and 1; their geometric mean is the composite habitat suitability index (cHSI), masked to the wetted area. Usable habitat area at a discharge is the area where cHSI exceeds the threshold.

```python
from riverarchitect.sharc import SHArC

result = SHArC("2100_sample", unit="us").run("Chinook salmon", "spawning")
print(result["sharea"])
```

Species and lifestage names are matched case-insensitively, so `"Chinook salmon"` and the workbook's `"Chinook Salmon"` both work.

| Q (cfs) | Usable area (sqft) | Mean cHSI |
|---:|---:|---:|
| 300 | 50 463 | 0.507 |
| 750 | 26 199 | 0.335 |
| 1 000 | 25 218 | 0.306 |
| 4 000 | 16 137 | 0.135 |
| 9 750 | 66 159 | 0.242 |
| 20 000 | 24 129 | 0.093 |
| 42 200 | 11 511 | 0.035 |

**SHArea: 24 176 sqft** - usable area integrated over the flow duration curve in `00_Flows/2100_sample/flow_duration_chsp.xlsx`, so habitat that only exists at a rare discharge counts for little. That single number is what a project gets judged on.

Read the mean cHSI column, not only the area. Mean cHSI falls cleanly from 0.51 to 0.04 as discharge rises, which is what spawning habitat should do. Usable *area* is not monotonic: it bottoms out near 4000 cfs and climbs to a second peak of 66 000 sqft near 9750 cfs, because at that flow a large area of channel margin is inundated shallowly enough to clear the 0.4 threshold even though the reach as a whole is less suitable. Area and quality are different questions; SHArea is the one that weighs them together.

Two rows are artefacts of the bad rasters: 550 cfs collapses to 5 985 sqft, and 88053 cfs reports 25 614 sqft at a mean cHSI of 0.315 that no 50-year flood would produce.

## 8. Your own habitat suitability criteria

The curves behind section 7 are published ones for a Californian reach. Replace them the way section 4 replaced the lifespan thresholds: **SHArC ▸ Suitability curves** takes a workbook in the `Fish.xlsx` layout, and the Species and Lifestage lists repopulate from it.

```python
from riverarchitect.sharc import SHArC, FishDatabase, default_fish_database

print(default_fish_database())            # the packaged copy, to start from
fish = FishDatabase("my_curves.xlsx")
print(fish.species, fish.lifestages("Chinook Salmon"))

analysis = SHArC("2100_sample", unit="us", fish=fish, threshold=0.4,
                 combine_method="geometric_mean")
result = analysis.run("Chinook Salmon", "spawning")
```

The layout is one block of eight columns per species: the species name on row 2, its lifestages on row 5 at four fixed offsets, the velocity curve from row 9 and the depth curve from row 38, each a pair of columns of parameter value against suitability index. Cover values sit on rows 72 to 85, and the stranding thresholds - minimum swimming depth and maximum sustained velocity - on rows 87 and 88, which is where section 9 reads them from. {doc}`../modules/ecohydraulics` gives the full layout.

Three settings decide what the curves then mean. **Combine method**: the geometric mean of the depth and velocity indices is forgiving of one poor index, the product is harsher and drops faster. The **usable habitat threshold**, 0.4, is the cHSI above which a cell counts as usable at all, and it moves the reported area more than most curve edits will - state it whenever you quote a number. **Weight usable area by the mean suitability** reports quality-weighted area, which is the fairer comparison between two designs.

```{admonition} A curve is unsuitable past its end, not maximally suitable
:class: warning

Between the points you give, the index is interpolated. Below the first point it holds that first suitability; above the last point it drops to **zero**. The last point you enter is therefore a statement about where the habitat stops, not about where the data ran out.
```

One more trap: the flow duration workbooks are found by a four-letter code derived from the species and lifestage, so renaming `Chinook Salmon` in your workbook breaks the link to `flow_duration_chsp.xlsx`. Usable areas keep appearing and SHArea quietly stops being reported.

## 9. Stranding risk

As discharge falls the wetted area shrinks and breaks apart, and pools that lose their connection to the main channel trap fish.

```python
from riverarchitect.stranding import StrandingRisk

result = StrandingRisk.for_fish("2100_sample", "Chinook salmon", "fry", unit="us").run()
```

The minimum swimming depth comes from `Fish.xlsx`: **0.2 ft** for Chinook fry. It is the single most influential parameter in the analysis, so report it alongside any result.

| Q (cfs) | Pools | Stranded (sqft) | % of wetted |
|---:|---:|---:|---:|
| 7 250 | 63 | 2 178 | 1.17% |
| 16 000 | 24 | 1 746 | 0.58% |
| 7 750 | 12 | 1 332 | 0.59% |
| 6 250 | 33 | 1 305 | 0.77% |
| 6 750 | 39 | 1 197 | 0.68% |

56 of the 60 discharges produce at least one disconnected pool, and **12 996 sqft** is disconnected at some point in the recession. `Q_disconnect.tif` records the highest discharge at which each cell was disconnected - the flow at which that spot becomes a trap as the hydrograph recedes - and the pools at the worst discharge are polygonised into a GeoPackage.

The main channel is defined **once**, from the largest wetted region at the lowest analysed discharge, and every higher discharge is judged against it. That is the target the original built its least-cost escape routes towards. Pass `target_discharge=False` to fall back to the largest region at each discharge separately, which differs whenever a detached area outgrows the channel it is detached from.

The stranded percentage is also reported against the largest *measured* wetted extent (`percent_of_max_wetted`), which on this reach is 356 832 sqft at 42200 cfs - not at the highest discharge, because of `h088053.tif`.

```{admonition} The velocity criterion needs flow direction
:class: warning

Escape routes are found with Dijkstra's algorithm, which can also block a route where the flow is faster than the lifestage can swim against. That criterion is directed - fast water can be drifted down but not climbed back up - so it needs the velocity *components*, and this condition ships only the speed `u<Q>.tif`. Pass `velocity_field={Q: (ux, uy)}` to apply it; `StrandingRisk.velocity_limited` reports whether it was. Do not substitute the speed alone: at 7250 cfs only 0.4 % of the mainstem here is slower than a juvenile's 1.9 fps, so an undirected criterion strands the river itself.
```

## 10. Riparian recruitment

Cottonwood and willow seedlings establish only where four things happen in the right order over one season: a winter flow clears a seedbed, the water table then drops slowly enough for roots to follow, the seedling is not drowned, and no later flow uproots it. Each is scored 1, 0.5 or 0, and the recruitment potential is their **product** - a zero anywhere is a zero overall.

This is the one module that needs a **daily flow record**, because bed preparation, recession and scour are about *when* flows happened, not just which flows are possible.

```python
from riverarchitect.recruitment import RecruitmentPotential

result = RecruitmentPotential(
    "2100_sample", "sample-data/00_Flows/2100_sample/flow_series_2020.csv",
    year=2020, unit="us").run()
```

| Layer | Area (sqft) |
|---|---:|
| Crop area (where recruitment is possible at all) | 71 802 |
| Full recruitment potential | 31 977 |
| Partial potential | 5 868 |
| Bed preparation = 1 | 32 292 |
| Desiccation survival = 1 | 71 748 |
| Inundation survival = 1 | 71 451 |
| Scour survival = 1 | 71 739 |

Bed preparation is the limiting objective: it alone accounts for almost all of the difference between the crop area and the recruitment area.

```{admonition} The flow record is synthetic
:class: warning

The sample condition ships flow duration curves but no dated record. `00_Flows/2100_sample/flow_series_2020.csv` is generated by `make_flow_series.py` beside it: the **discharges are the reach's own**, drawn from its flow duration curve, and only their ordering in time is invented - a plausible Mediterranean water year with a wet winter, three storms, a spring freshet and a long summer recession. Treat recruitment results on this condition as a demonstration of the method, not as a finding about the reach.
```

## 11. What the project costs, and what it buys

Everything so far describes a design. **Project Maker** prices it and asks whether it is worth building.

It takes the quantities from the Max Lifespan output of section 5 - the mapped area of each winning feature becomes so many logs, so many acres of planting, so many cubic yards of grading:

```python
from riverarchitect.maxlifespan import MaxLifespan
from riverarchitect.projectmaker import ProjectMaker

summary = MaxLifespan("Output/LifespanDesign/2100_sample").run(write_polygons=False)

maker = ProjectMaker(name="guide", unit="us")
maker.quantities_from_lifespan(summary)
costs = maker.costs()
```

On this reach that gives 405 logs of streamwood, 0.25 acres of Cottonwood and 0.29 of Willow by the pod method, 0.14 acres of Box Elder and 0.05 of White Alder:

| Group | Cost (US$) |
|---|---|
| Stabilising bioengineering | 313 886 |
| Vegetation plantings | 46 939 |
| **Construction works** | **360 825** |
| Site (de-)mobilization, 10 % | 36 083 |
| Unexpected, 10 % | 39 691 |
| Markups (overhead, profit, insurance), 16.5 % | 72 039 |
| Permitting, 35 % | 178 023 |
| **Total** | **686 660** |

The markups compound in that order, which is why permitting at 35 % is the largest single line: it applies to a subtotal that already carries the other three.

The habitat half of the assessment needs **two** conditions - the existing one, and a with-project one whose depth and velocity rasters come from re-running your 2D model over the terraformed DEM of section 6. The sample data ships only the existing condition, so the numbers above are the bill of quantities alone; `ProjectMaker.run(before=..., after=...)` adds SHArea before and after, the net gain, and the cost per unit area gained. That last figure is the one to compare between designs: a scheme that is cheaper in total and worse per square foot of habitat is not the cheaper scheme.

```{admonition} The unit rates are not yours
:class: warning

They live in {data}`riverarchitect.projectmaker.COST_ITEMS` as Python - diffable and reviewable, and dated and regional. Treat the shipped rates as a worked structure and substitute your own tender prices before quoting anything to anyone.
```

## 12. Maps

The Maps tab draws any of these rasters into a QGIS print layout and exports a PDF; see {doc}`qgis_mapping`. It needs the QGIS Python bindings, which belong to the interpreter QGIS was installed with rather than to a conda environment. Without them the tab still opens and says so.

## 13. The tools around the edges, and the optional outputs

Four things sit outside the chain because they are used before it, beside it, or instead of it.

**Bed shear stress**, twice over. Section 2 built it for a whole condition; **Tools ▸ Bed shear stress** does the same arithmetic on three loose rasters, which is the point - it runs on model output before that output is a condition folder at all, so a questionable hydraulic result is caught on the day it comes out of the model.

```python
from riverarchitect.tools import taux

written = taux.compute("u000750.tif", "h000750.tif", "dmean.tif",
                       "out/q000750", grain_kind="dmean", unit="us")
```

Both paths write four rasters per discharge: `ts` (the dimensionless Shields stress the feature thresholds are compared against), `tb` (u*²), `hks` (relative submergence h/k_s) and `regime`. Open `regime<Q>.tif` before trusting a stress map. It records which resistance law applied in each cell - 1 Rickenmann-Recking, 2 blended, 3 Keulegan-Einstein, 0 invalid - and on this reach about **95 %** of wet cells are regime 1, precisely the range where a single logarithmic law is outside its validity. A stress map computed the old way would have been wrong across most of the reach without saying so.

**Reconcile NoData in a condition**, which section 1 already recommended on import.

**The pool-riffle designer** sizes a pool-riffle sequence from grain size, bed slope, base width, target residual pool depth and bank slope. It is a calculator rather than a mapping module, so it opens as a dialog and recomputes as you type.

**Convert ArcGIS .lyrx to QGIS .qml** brings layer styling over from an ArcGIS project, for the map series of section 12.

Two tabs also sit outside the chain. **Morphology ▸ River Builder** synthesises a valley DEM from channel parameters - reach length, bankfull width and depth, valley slope, D50, floodplain and terrace widths, meander amplitude and a cross-section shape - which is how to try a method with no survey, or build a controlled test case. **Morphology ▸ Volume Assessment**, used in section 6, computes cut and fill between any two DEMs, not only terraformed ones.

## 14. Before trusting this on your own data

**Are the units right?** The chain refuses a unit system that disagrees with the CRS of the rasters, but it cannot tell whether the raster *values* are in the unit of their CRS, nor what unit your discharges and workbooks are in. Check those yourself.

**Is the condition prepared?** A missing `d2w.tif` does not raise; it drops the criterion that needed it.

**Does `input_definitions.inp` carry a return period for every discharge?** Lifespan mapping only uses the discharges that have one - on this reach, 17 of the 60 rasters on disk. The ecohydraulic modules scan the folder instead and use all 60.

**Do the hydraulic rasters make sense against each other?** Plot maximum depth and maximum velocity against discharge before you start. Ten seconds of that would have found both bad rasters in this condition.

### Where to go from there

{doc}`../modules/index` explains what each analysis computes and cites the literature its defaults come from. {doc}`../modules/features` lists every restoration feature and every threshold behind it, which is the reference to keep open while editing the workbook of section 4. {doc}`../help/known-issues` is the honest list of rough edges in this release - read it before concluding something is broken - and {doc}`../help/faq` answers what comes up first.

If you are arriving from River Architect 1.x, read {doc}`arcpy_migration`, and in particular its last section: those are the places where a plausible-looking port did not do what 1.4 did, and they were only found by running this whole chain on this reach.
