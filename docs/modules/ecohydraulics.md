# Ecohydraulics

What the design is worth ecologically. Three independent analyses; all of them need a
prepared condition, and habitat area additionally needs a flow duration curve from
{doc}`../getstarted/index`.

## Habitat Area (SHArC)

{mod}`riverarchitect.sharc` - the **Ecohydraulics ▸ Habitat Area (SHArC)** tab.

Turns 2D hydrodynamic results into a map of how good the habitat is for a given fish species
and lifestage, and then into a single number a project can be judged on.

1. **Habitat suitability curves** come from `Fish.xlsx`: for each species and lifestage, a
   piecewise-linear curve mapping flow depth, velocity, substrate size or cover radius onto a
   suitability index between 0 and 1.
2. **Hydraulic HSI rasters** apply those curves to the depth and velocity rasters of a
   discharge, giving `dsi` and `vsi`.
3. **Composite HSI** (`cHSI`) combines them by geometric mean or product, optionally with a
   cover HSI, and is masked to the wetted area.
4. **Usable area** at a discharge is the area where `cHSI` exceeds a threshold (0.4 by
   default), optionally weighted by the mean `cHSI` there.
5. **SHArea** integrates usable area over the flow duration curve, so habitat that only
   exists at a rare discharge counts for little.

$$
\text{SHArea} = \sum_i \frac{E_i - E_{i-1}}{100}\,A_i
$$

with $E_i$ the cumulative per-cent exceedance of discharge $i$ and $A_i$ its usable area.
That reproduces the `=(E5-E4)/100*F5` column of the original `CONDITION_sharea_template.xlsx`
exactly.

```{admonition} Read the mean cHSI, not only the area
:class: tip

Usable area is not monotonic in discharge. A high flow can inundate a large area of channel
margin shallowly enough to clear the threshold even though the reach as a whole is less
suitable. Area and quality are different questions; SHArea is the one that weighs them
together.
```

### Cover

Depth and velocity say whether a fish *can* be somewhere. **Cover** says whether it is safe
to be there - a fry in open water at the right depth and velocity is still a meal. Pass
`cover=True` to {meth}`riverarchitect.sharc.SHArC.run`, or call
{func}`riverarchitect.sharc.cover_hsi` directly.

| Cover type | Source | How it is applied |
|---|---|---|
| `substrate` | the grain size raster | mapped through its suitability curve, like depth or velocity |
| `cobbles` | grain size 0.064 - 0.256 m | presence, spread over the curve's radius |
| `boulders` | grain size above 0.256 m | presence, spread over the curve's radius |
| `plants` | `plants.tif` beside the condition | presence, spread over the curve's radius |
| `wood` | `wood.tif` beside the condition | presence, spread over the curve's radius |

A cover element shelters everything within its **radius**, taken from the first x value of
its curve in `Fish.xlsx`, and those cells take the curve's suitability. The result is the
cell-wise **maximum** across the types present: the best shelter available at a cell is what
counts, not the sum of every kind of it. Cover is cropped to water the lifestage can reach -
shelter a fish cannot get to shelters nothing.

With cover, the composite is the cube root of `dsi * vsi * cover` rather than the square root
of `dsi * vsi`.

```{admonition} Where the radius came from
:class: note

The original produced it by converting the cover raster to points, running
`SpatialJoin_analysis(..., match_option="CLOSEST", search_radius=r)` against a point per
cell, and converting back. That is a Euclidean distance transform written the only way
`arcpy` allowed; here it is {func}`riverarchitect.raster.within_radius`, which also handles
anisotropic cells correctly.
```

### Species and lifestages

The workbook defines Chinook Salmon, Rainbow / Steelhead Trout, Lamprey, Green Sturgeon and
a generic "All Aquatic" block, each with its own lifestages, seasons, curves and swimming
thresholds. Lifestage *labels are read from the workbook* rather than assumed, because they
vary by species - offset 3 is "fry" for salmon but "ammocoetes" for lamprey.

Names are matched **ignoring case and spacing**, so `"Chinook salmon"` and the workbook's
`"Chinook Salmon"` both work. In the original, and in early versions of this port, the
capitalisation of a caller's argument decided whether the analysis ran at all.

To add or edit a species, edit the packaged `Fish.xlsx` - see the *Edit Fish template* page
below.

### Relation to the original

`cHSI.nested_con_raster_calc` built one `Con()` raster per curve segment and took their
cell-wise maximum: a piecewise-linear interpolation written the only way `arcpy` map algebra
allowed. Here it is {func}`riverarchitect.sharc.apply_curve`, which is `numpy.interp` with
the same end behaviour - hold the first suitability below the curve, but drop to **zero**
above it. That asymmetry is deliberate: a depth beyond the curve is unsuitable, not maximally
suitable, and clamping there would invent habitat at the highest discharges.

## Stranding Risk

{mod}`riverarchitect.stranding` - the **Ecohydraulics ▸ Stranding Risk** tab.

As discharge falls the wetted area shrinks and breaks apart; pools that lose their connection
to the main channel trap fish. Threshold each depth raster at the minimum swimming depth of
the species and lifestage, label the wetted regions, and every region that does not reach the
main channel is a stranding risk.

The **main channel is defined once**, as the largest wetted region at the lowest analysed
discharge, and every higher discharge is judged against it - the same target the original
built its least-cost escape routes towards.

| Output | |
|---|---|
| `disconnected_<Q>.tif` | one per discharge |
| `Q_disconnect.tif` | the highest discharge at which each cell was disconnected: the flow at which that spot becomes a trap as the hydrograph recedes |
| `pools_<Q>.gpkg` | the individual pools at the worst discharge |
| table | wetted area, stranded area and pool count per discharge |

The minimum swimming depth comes from `Fish.xlsx` (0.2 ft for Chinook fry). **It is the
single most influential parameter in the analysis** - at `h_min = 0` every wet cell counts
and much of the pool count is single cells at the wetted edge, real in the raster and
meaningless in the river. State the value you used alongside any result.

```{admonition} The velocity criterion is not applied
:class: warning

The original also blocked escape routes where the flow was faster than the lifestage could
swim against. This port applies the depth criterion only.
{attr}`riverarchitect.stranding.StrandingRisk.velocity_limited` is `False` to record that,
and `u_max` carries the threshold that would have been used, so a result can state it.
```

## Riparian Seedling Recruitment

{mod}`riverarchitect.recruitment` - the **Ecohydraulics ▸ Riparian Seedling Recruitment**
tab.

Cottonwood and willow seedlings establish only where four things happen in the right order
over a single season, and this maps where all four coincide - the Recruitment Box Model of
Braatne et al. (2007).

| Objective | Question |
|---|---|
| Bed preparation | did a winter flow mobilise the bed, clearing a seedbed? |
| Recession rate (desiccation) | did the water table drop slowly enough for roots to follow? |
| Prolonged inundation | did the seedling stay under water long enough to drown? |
| Scour | did a later flow uproot it? |

Each is scored 1 (good), 0.5 (stressed) or 0 (fatal), and the recruitment potential is their
**product** - a seedling has to survive every one of them, so a zero anywhere is a zero
overall.

This is the one module that needs a **daily flow record**: bed preparation, recession and
scour are about *when* flows happened, not just which flows are possible.

Bed preparation and scour both ask whether the bed was mobile, which is the dimensionless
bed shear stress $\theta_{84}$ of {mod}`riverarchitect.shear` - the same regime-aware
calculation Lifespan Design uses, described under
[dimensionless bed shear stress](lifespans.md#dimensionless-bed-shear-stress-taux). Each run
writes `hks<Q>.tif` and `regime<Q>.tif` per modelled discharge beside its objective rasters,
showing the relative submergence and which resistance closure applied where.

Three details decide the result, and all three follow the original:

* a stressful or lethal recession day is only counted where the cell is **dry** that day -
  a submerged seedling is not desiccating, however fast the surface is dropping;
* a cell that goes dry during seed dispersal starts again from there, because that is when
  its seed actually landed, so both the counts and their denominator are per cell;
* the inundation objective uses the longest run of **consecutive** submerged days, not their
  total. Fourteen days under water in one stretch drowns a seedling; fourteen days spread
  over a season does not.

## In this section

```{toctree}
:maxdepth: 1

SHArC: introduction and quick guide <../wiki/SHArC>
SHArC: working principles <../wiki/SHArC-working-principles>
Edit the Fish (physical habitats) template <../wiki/aqua-modification>
Stranding Risk <../wiki/StrandingRisk>
Riparian Seedling Recruitment <../wiki/RSR>
```

```{eval-rst}
.. seealso::

   :mod:`riverarchitect.sharc`, :mod:`riverarchitect.stranding` and
   :mod:`riverarchitect.recruitment` in the API reference.
```
