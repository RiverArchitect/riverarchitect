# Ecohydraulics

What the design is worth ecologically. Three independent analyses; all of them need a prepared condition, and habitat area additionally needs a flow duration curve from {doc}`../getstarted/index`.

## Habitat Area (SHArC)

{mod}`riverarchitect.sharc` - the **Ecohydraulics ▸ Habitat Area (SHArC)** tab.

Turns 2D hydrodynamic results into a map of how good the habitat is for a given fish species and lifestage, and then into a single number a project can be judged on.

1. **Habitat suitability curves** come from `Fish.xlsx`: for each species and lifestage, a piecewise-linear curve mapping water depth, velocity, substrate size or cover radius onto a suitability index between 0 and 1.
2. **Hydraulic HSI rasters** apply those curves to the depth and velocity rasters of a discharge, giving `dsi` and `vsi`.
3. **Composite HSI** (`cHSI`) combines them by geometric mean or product, optionally with a cover HSI, and is masked to the wetted area.
4. **Usable area** at a discharge is the area where `cHSI` exceeds a threshold (0.4 by default), optionally weighted by the mean `cHSI` there.
5. **SHArea** integrates usable area over the flow duration curve, so habitat that only exists at a rare discharge counts for little.

$$
\text{SHArea} = \sum_i \frac{E_i - E_{i-1}}{100}\,A_i
$$

with $E_i$ the cumulative per-cent exceedance of discharge $i$ and $A_i$ its usable area.

```{admonition} Read the mean cHSI, not only the area
:class: tip

Usable area is not monotonic in discharge. A high flow can inundate a large area of channel margin shallowly enough to clear the threshold even though the reach as a whole is less suitable. Area and quality are different questions; SHArea is the one that weighs them together.
```

### Cover

Depth and velocity say whether a fish *can* be somewhere. **Cover** says whether it is safe to be there - a fry in open water at the right depth and velocity is still a meal. Pass `cover=True` to {meth}`riverarchitect.sharc.SHArC.run`, or call {func}`riverarchitect.sharc.cover_hsi` directly.

| Cover type | Source | How it is applied |
|---|---|---|
| `substrate` | the grain size raster | mapped through its suitability curve, like depth or velocity |
| `cobbles` | grain size 0.064 - 0.256 m | presence, spread over the curve's radius |
| `boulders` | grain size above 0.256 m | presence, spread over the curve's radius |
| `plants` | `plants.tif` beside the condition | presence, spread over the curve's radius |
| `wood` | `wood.tif` beside the condition | presence, spread over the curve's radius |

A cover element shelters everything within its **radius**, taken from the first x value of its curve in `Fish.xlsx` and applied with {func}`riverarchitect.raster.within_radius`, and those cells take the curve's suitability. The result is the cell-wise **maximum** across the types present: the best shelter available at a cell is what counts, not the sum of every kind of it. Cover is cropped to water the lifestage can reach - shelter a fish cannot get to shelters nothing.

With cover, the composite is the cube root of `dsi * vsi * cover` rather than the square root of `dsi * vsi`.

```{admonition} Mineral cover can also be read as an areal fraction
:class: note

`Fish.xlsx` heads both cover blocks `Rad.`, which is why cobbles and boulders are applied by radius like plants and streamwood. They can equally be read as areal fractions - *the share of the neighbourhood that is boulder* - which is how the method has also been described:

```python
SHArC("2100_sample", unit="us", mineral_rule="fraction")   # or cover_window=2
```

The fraction is measured over a 3x3 window by default ({data}`riverarchitect.sharc.COVER_WINDOW`, computed with {func}`riverarchitect.raster.focal_fraction`) and the window size is a parameter rather than a constant. See {data}`riverarchitect.sharc.MINERAL_COVER_RULES`.

Worth knowing before choosing. The mineral values the workbook holds are 0.1 for cobbles and 1.0 for boulders, which as radii are smaller than a cell on any real grid - so under the default a mineral cover element shelters only itself, with no spreading at all. As fractions the same numbers ask for 10 % and 100 % of the neighbourhood. On the sample reach, Chinook juvenile SHArea with cover is 55 331 sqft by radius against 53 723 sqft by fraction, and boulders drop out of the fraction result entirely: their value asks for a neighbourhood that is *wholly* boulder, and a gravel-cobble reach has none.
```

### Species and lifestages

The workbook defines Chinook Salmon, Rainbow / Steelhead Trout, Lamprey, Green Sturgeon and a generic "All Aquatic" block, each with its own lifestages, seasons, curves and swimming thresholds.

Names are matched **ignoring case and spacing**, so `"Chinook salmon"` and the workbook's `"Chinook Salmon"` both work. Go through {meth}`riverarchitect.sharc.FishDatabase.resolve_species` and {meth}`riverarchitect.sharc.FishDatabase.resolve_lifestage` rather than comparing names directly.

### The Fish workbook

{class}`riverarchitect.sharc.FishDatabase` reads `Fish.xlsx`, either the copy packaged with River Architect ({func}`riverarchitect.sharc.default_fish_database`) or one kept with a project and passed explicitly. Its layout is fixed, and worth knowing before editing:

* **Columns.** Each species occupies a block of eight columns starting at column C. Row 2 holds the species name and row 5 the lifestage labels, at offsets 1, 3, 5 and 7 within the block ({data}`riverarchitect.sharc.LIFESTAGE_OFFSETS`). The gaps are deliberate; do not close them up.
* **Rows.** Each curve starts at a fixed row, listed in {data}`riverarchitect.sharc.PARAMETER_ROWS`: velocity at 9, water depth at 38, substrate at 72, cobbles at 81, boulders at 82, plants at 84, streamwood at 85. Row 6 and row 7 give the season's start and end date, and rows 87 and 88 the minimum swimming depth and maximum swimming velocity.

To **add a species**, copy an existing eight-column block to the right of the last one and edit the name, the lifestage labels and the curve values. To **add or change a curve**, edit the values in place; a curve is a list of x values with a suitability below each. To **drop a lifestage**, leave its columns empty rather than deleting them.

Lifestage *labels are read from the workbook* rather than assumed, so a species may name its lifestages whatever suits it: offset 3 is `fry` for salmon and `ammocoetes` for lamprey, and the All Aquatic block uses `hydrological year`, `season`, `depth > x` and `velocity > x`. Only the row and column *positions* are fixed. Inserting or deleting rows shifts the curves out from under `PARAMETER_ROWS`, which is the one edit that will silently produce wrong suitabilities.

{func}`riverarchitect.sharc.apply_curve` interpolates the curve with `numpy.interp`, holding the first suitability below the curve and dropping to **zero** above it. That asymmetry is deliberate: a depth beyond the curve is unsuitable, not maximally suitable, and clamping there would invent habitat at the highest discharges.

## Stranding Risk

{mod}`riverarchitect.stranding` - the **Ecohydraulics ▸ Stranding Risk** tab.

As discharge falls the wetted area shrinks and breaks apart; pools that lose their connection to the main channel trap fish. Threshold each depth raster at the minimum swimming depth of the species and lifestage, then ask of every wetted cell whether a route back to the main channel exists. Where none does, a fish that is there is trapped.

That question is answered by **Dijkstra's algorithm** over the travel-permissible cells, {func}`riverarchitect.raster.least_cost_distance`: cells are vertices, steps between neighbours are edges weighted by the distance between cell centres, and the cheapest route to the mainstem is the escape route. When only the depth criterion applies, a route exists exactly when the wetted region touches the mainstem, so the answer coincides with connected-component labelling ({func}`riverarchitect.raster.disconnected_mask`); that is the faster path and the one taken when no velocity field is supplied. The two are checked against each other on the sample reach in the test suite.

The **main channel is defined once**, as the largest wetted region at the lowest analysed discharge, and every higher discharge is judged against it.

| Output | |
|---|---|
| `disconnected_<Q>.tif` | one per discharge |
| `Q_disconnect.tif` | the highest discharge at which each cell was disconnected: the flow at which that spot becomes a trap as the hydrograph recedes |
| `escape_<Q>.tif` | route length back to the mainstem, with `write_escape_routes=True` |
| `pools_<Q>.gpkg` | the individual pools at the worst discharge |
| table | wetted area, stranded area and pool count per discharge |

The minimum swimming depth comes from `Fish.xlsx` (0.2 ft for Chinook fry). **It is the single most influential parameter in the analysis** - at `h_min = 0` every wet cell counts and much of the pool count is single cells at the wetted edge, real in the raster and meaningless in the river. State the value you used alongside any result.

### The velocity criterion

A fish cannot swim upstream against more than `u_max`, so fast water is a one-way door: it can be drifted down but not climbed back up. That makes the escape-route graph **directed**, and a directed graph needs the flow *direction*. Conditions ship `u<Q>.tif`, a speed, so the criterion applies only when the components are supplied as well:

```python
StrandingRisk.for_fish("2100_sample", "Chinook salmon", "juvenile",
                       velocity_field={7250.0: ("ux007250.tif", "uy007250.tif")})
```

`velocity_field` takes a `{discharge: (ux, uy)}` mapping of arrays or paths, or a callable `f(discharge, profile) -> (ux, uy)`. `ux<Q>.tif` and `uy<Q>.tif` beside the condition's hydraulic rasters are picked up automatically. {attr}`riverarchitect.stranding.StrandingRisk.velocity_limited` reports whether the criterion is being applied, so a result can state it either way.

```{admonition} Do not approximate it with the speed alone
:class: warning

Treating a cell as impassable because it is *fast*, without knowing which way, is not a conservative simplification - it is a different analysis. On the sample reach at 7250 cfs only 0.4 % of the low-flow mainstem is slower than a juvenile Chinook's 1.9 fps, and at 16 000 cfs none of it is: the mainstem itself becomes unreachable and almost the whole wetted area reads as stranded. This is why `u_max` on its own does nothing.
```

## Riparian Seedling Recruitment

{mod}`riverarchitect.recruitment` - the **Ecohydraulics ▸ Riparian Seedling Recruitment** tab.

Cottonwood and willow seedlings establish only where four things happen in the right order over a single season, and this maps where all four coincide - the Recruitment Box Model of Braatne et al. (2007).

| Objective | Question |
|---|---|
| Bed preparation | did a winter flow mobilise the bed, clearing a seedbed? |
| Recession rate (desiccation) | did the water table drop slowly enough for roots to follow? |
| Prolonged inundation | did the seedling stay under water long enough to drown? |
| Scour | did a later flow uproot it? |

Each is scored 1 (good), 0.5 (stressed) or 0 (fatal), and the recruitment potential is their **product** - a seedling has to survive every one of them, so a zero anywhere is a zero overall.

This is the one module that needs a **daily flow record**: bed preparation, recession and scour are about *when* flows happened, not just which flows are possible.

Bed preparation and scour both ask whether the bed was mobile, which is the dimensionless bed shear stress $\theta_{84}$ of {mod}`riverarchitect.shear` - the same regime-aware calculation Lifespan Design uses, described under [dimensionless bed shear stress](lifespans.md#dimensionless-bed-shear-stress-taux). Each run writes `hks<Q>.tif` and `regime<Q>.tif` per modelled discharge beside its objective rasters, showing the relative submergence and which resistance closure applied where.

Three details decide the result:

* a stressful or lethal recession day is only counted where the cell is **dry** that day - a submerged seedling is not desiccating, however fast the surface is dropping;
* a cell that goes dry during seed dispersal starts again from there, because that is when its seed actually landed, so both the counts and their denominator are per cell;
* the inundation objective uses the longest run of **consecutive** submerged days, not their total. Fourteen days under water in one stretch drowns a seedling; fourteen days spread over a season does not.

```{eval-rst}
.. seealso::

   :mod:`riverarchitect.sharc`, :mod:`riverarchitect.stranding` and
   :mod:`riverarchitect.recruitment` in the API reference.
```
