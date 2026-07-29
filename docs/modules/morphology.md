# Morphology (Terraforming)

Changing the terrain, and quantifying the change. Two modules, run in that order.

## Terraforming

{mod}`riverarchitect.terraforming` - the **Morphology ▸ Terraforming** tab.

A lifespan map says a willow would survive at a cell *if* the water table were within reach
of its roots. Where the ground stands too high above the water table it will not, and the
answer is to lower the ground: grading, or widening the channel into a berm.

The rule is one line of arithmetic. Where a feature is planned **and** the depth to the
water table exceeds what the feature tolerates, lower the DEM by exactly the excess:

$$
z' = \begin{cases}
    z - (d_{2w} - d_{2w,\max}) & \text{where the feature applies and } d_{2w} > d_{2w,\max} \\
    z & \text{elsewhere}
\end{cases}
$$

So a lowered cell lands *at* the deepest tolerable depth to water and no lower. The point is
to reach the water table, not to dig a pond.

`d2w_max` defaults to the **smallest** `d2w_max` among the vegetation planting features -
the terrain has to suit the most demanding species planned, not the least.
{func}`riverarchitect.terraforming.planting_depth_limit` computes it; on the shipped
thresholds it is 7 ft.

**Features are applied in sequence, and each works on the terrain the previous one left.**
That matters: lowering the ground also lowers its depth to the water table, so the second
feature must see the first one's excavation rather than the original DEM.

### Inputs and outputs

| | |
|---|---|
| Needs | `dem.tif` and `d2w.tif` from the condition, and the `best_<feature>.tif` masks from {doc}`lifespans` |
| Writes | `dem_terraformed.tif`, `cut_depth.tif`, `d2w_terraformed.tif` |

`cut_depth.tif` is NoData where nothing was dug - two-argument `con`, not a zero cut. Feed
`dem_terraformed.tif` to Volume Assessment as the modified DEM.

```{admonition} River Builder is not part of this package
:class: note

The original's ModifyTerrain tab also hosted **River Builder**, a generator of synthetic
river valleys with its own input format and its own publication. It is a separate program
and is not ported here. Its description is preserved in the legacy page below.
```

```{admonition} Post-processing is still required
:class: warning

As in the original, a threshold-based terrain modification is a *proposal*, not a
construction drawing. It needs computer-aided design afterwards - edge smoothing, and
translation into real-world construction geometry - before anyone digs.
```

## Volume Assessment

{mod}`riverarchitect.volume_assessment` - the **Morphology ▸ Volume Assessment** tab.

Compares an original (pre-project) and a modified (post-project) DEM and reports the
earth movement the design requires: fill volume, excavation volume, the net, and the areas
each covers.

Volumes are **integrated under the triangulated surface** through the cell centres, not
summed as vertical prisms, so quantities remain comparable with the original software. The
{doc}`../guide/volumes` page explains why that distinction is not cosmetic and what it costs
you if you get it wrong.

The **level of detection** excludes elevation differences smaller than the survey noise. It
defaults to 0.99 ft (0.30 m). Differences below it are not evidence of terrain change and
should not be billed as earthworks.

```{admonition} The two modules do not report identical totals
:class: note

Terraforming sums the cut over whole cells; Volume Assessment integrates between cell
*centres*, which covers slightly less area at the edges of the raster. On a real reach the
difference is a few per cent. Quote the Volume Assessment figure - it is the one that
matches the original software and the one a contractor will recognise.
```

## River reaches

Both modules can be limited to a **reach**: a named stretch of river with its own extent, so
that a long project can be planned and reported in pieces. Reach definitions are described
in the legacy page below; this release applies extents through the raster mask and the QGIS
layout rather than through the original's reach workbook.

## In this section

```{toctree}
:maxdepth: 1

../guide/volumes
Modify Terrain: working principles (legacy) <../wiki/ModifyTerrain>
River Builder <../wiki/RiverBuilder>
Volume Assessment: working principles (legacy) <../wiki/VolumeAssessment>
River reach definitions <../wiki/RiverReaches>
```

```{eval-rst}
.. seealso::

   :mod:`riverarchitect.terraforming`, :mod:`riverarchitect.volume_assessment` and
   :mod:`riverarchitect.volume` in the API reference.
```
