# Lifespans

Two modules, and the feature definitions they share.

## Lifespan Design

{mod}`riverarchitect.lifespan` - the **Lifespan ▸ Lifespan Design** tab.

Answers two questions per cell, for a chosen restoration feature:

**Lifespan** - how many years is this feature expected to survive here? Each modelled
discharge carries a flood return period. For every criterion the feature has a threshold
for, the analysis finds the lowest return period at which that threshold is exceeded, which
is when the feature fails. The lifespan is the cell-wise **minimum** across criteria: the
first flood that breaks it.

Cells that survive every modelled flood stay **NoData**. Their lifespan is longer than the
largest modelled event and cannot be quantified from the data - writing a number there would
be inventing one.

**Design** - how big does the feature have to be to reach a target lifespan? For grain-based
features that is the stable grain size at the design flood, for example the minimum diameter
of angular boulders that will not mobilise in a 20-year event.

### The criteria

*Hydraulic* criteria produce a failure return period each, and their minimum is the
lifespan:

| Criterion | Fails when |
|---|---|
| Flow depth | depth reaches `h_max` |
| Flow velocity | velocity reaches `u_max` |
| Froude number | Froude reaches `froude_max` |
| Grain stability | dimensionless bed shear stress reaches `tau_cr`, or - when a safety factor is set - the flow can mobilise a grain of the size actually present |

*Spatial* criteria are **masks** applied to that result:

| Criterion | Restricts to |
|---|---|
| Depth to water table | `d2w_min` to `d2w_max` |
| Detrended DEM | `det_min` to `det_max` |
| Grain size | at most `grain_max`, for fine-sediment features |
| Terrain slope | at least `terrain_slope` |
| Topographic change | scour or fill at or above the rate - or, for an inverse-relevance feature, below it |
| Morphological units | the units in `mu_relevant`, or everything except `mu_avoid` |

### Threshold values

Defaults live in {data}`riverarchitect.lifespan.FEATURES` as **Python rather than a binary
workbook**, so they are diffable and reviewable. They reproduce the original
`threshold_values.xlsx` exactly.
{func}`riverarchitect.lifespan.load_threshold_workbook` still reads a project's own
customised workbook.

```{admonition} The threshold units are a round trip
:class: warning

The original multiplies every length threshold by `ft2m` when reading the workbook and
divides by it again when applying it, so the two cancel. The values in `FEATURES` are the
workbook's own U.S. customary numbers, **unconverted**. This looks like a missing conversion
and is not one.
```

### Relation to the original

This implements the analysis hierarchy **as the wiki documents it**, not as a line-by-line
transcription of the `arcpy` control flow. The original threaded results through a mutable
`raster_dict` and a chain of `Con()` calls whose behaviour depended on which rasters
happened to exist, and several of its criteria overwrote their own result four times in a
row. Two-argument {func}`riverarchitect.raster.con` is used throughout, so the false branch
is NoData and never zero - passing `0` instead is what creates wetted-area artefacts.

## Max Lifespan

{mod}`riverarchitect.maxlifespan` - the **Lifespan ▸ Max Lifespan** tab.

Lifespan mapping answers "how long does *this* feature last here?". This answers the
planner's question instead: **which feature belongs here, and how long will it last?**

* `max_lf.tif` is the cell-wise **maximum** across the feature lifespan rasters;
* a feature wins a cell where its own lifespan equals that maximum;
* each winner is written as a mask raster and polygonised into a GeoPackage, so the result
  can be drawn as action areas on a map.

**Ties are kept rather than broken.** A cell where two features both reach the maximum
appears in both layers, which is why the reported shares add to more than 100 per cent. That
is deliberate, and it is what the original did: it tells the planner the choice is theirs.

The result feeds {doc}`morphology` - the `best_<feature>.tif` masks are what Terraforming
reads to know where a feature is planned.

## In this section

```{toctree}
:maxdepth: 1

Lifespan and design mapping: introduction and working principles <../wiki/LifespanDesign>
Parameter hypotheses <../wiki/LifespanDesign-parameters>
River design and restoration features <../wiki/River-design-features>
Code extension and modification <../wiki/LifespanDesign-code>
Max Lifespan: working principles <../wiki/MaxLifespan>
```

```{eval-rst}
.. seealso::

   :mod:`riverarchitect.lifespan` and :mod:`riverarchitect.maxlifespan` in the API
   reference.
```
