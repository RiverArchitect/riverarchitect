# Morphology (Terraforming)

Changing the terrain, and quantifying the change. Three modules: two that produce a terrain
and one that measures the difference between two of them.

```{toctree}
:maxdepth: 1
:caption: In this section

../guide/volumes
Modify Terrain: working principles (legacy) <../wiki/ModifyTerrain>
River Builder: parameters and background (legacy) <../wiki/RiverBuilder>
Volume Assessment: working principles (legacy) <../wiki/VolumeAssessment>
River reach definitions <../wiki/RiverReaches>
```

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

```{admonition} Post-processing is still required
:class: warning

As in the original, a threshold-based terrain modification is a *proposal*, not a
construction drawing. It needs computer-aided design afterwards - edge smoothing, and
translation into real-world construction geometry - before anyone digs.
```

## River Builder

{mod}`riverarchitect.riverbuilder` - the **Morphology ▸ River Builder** tab.

Terraforming modifies a terrain that exists. River Builder **invents one**. A restoration
design needs a target, and a reach channelised for a century no longer contains one; this
generates a valley with the geometry a natural one would have, from parameters an engineer
can defend.

The construction, in order:

1. a **centreline** down the valley, displaced sideways by the meandering function; its arc
   length gives the sinuosity;
2. **bankfull width** at each station, from the width function about the base width, floored
   at the minimum;
3. **curvature**, from the curvature function - plus the analytical curvature of the sine
   itself when the cross-section is asymmetric;
4. **channel slope**, the valley slope divided by the sinuosity plus the trend of curvature
   along the reach. A meandering channel falls the same height over a longer path, so it is
   gentler than the valley;
5. **thalweg and bank tops**, and a **cross-section** between them - a symmetric U, an
   asymmetric U leaning into the bend, or a trapezoid;
6. **floodplain and terrace** benches either side, each with its own offset function;
7. the points are triangulated onto a regular grid, clipped to the valley boundary, and
   written as a GeoTIFF with a hillshade beside it.

$$
H_{bf} = \frac{165 \, D_{50} \, \tau^{*}_{cr}}{S}
$$

is the regime relation that sets the bankfull depth when none is given: the depth at which
the channel just mobilises its own median grain size. It is inversely proportional to slope,
so a gentle valley with a coarse bed produces a depth greater than the channel is wide -
which is not a river. The original produced that silently; here it is reported, and the
answer is to give the depth explicitly.

Sub-reach variability is expressed as functions - `SIN`, `COS`, `SIN_SQ`, `LINE` and `PERL`
(smooth pseudo-random noise) - which are summed where a parameter names several. The
parameter file format is the original's, so an existing RiverBuilder input runs unchanged.

```{admonition} What replaced R and 3D Analyst
:class: note

The original called a 1189-line R script through `rpy2`, wrote a point cloud to CSV, and
rebuilt it as a TIN and a raster with ArcGIS 3D Analyst - so it needed R, rpy2, ArcGIS *and*
a licence. The geometry is numpy here and the interpolation is
{class}`scipy.interpolate.LinearNDInterpolator`, which is what a TIN is; it returns NaN
outside the convex hull, which is the clip to the valley boundary the original did with a
soft-clip polygon.

The `PERL` noise is seeded, so the same input file gives the same valley. The original drew
from a hand-rolled generator seeded off the clock, and no run could be reproduced.
```

The DEM is a starting point, not a construction drawing: run a 2D model over it, build a
condition from the results, and put it through the rest of the chain.

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

Terraforming and Volume Assessment can be limited to a **reach**: a named stretch of river with its own extent, so
that a long project can be planned and reported in pieces. Reach definitions are described
in {doc}`../wiki/RiverReaches`; this release applies extents through the raster mask and the
QGIS layout rather than through the original's reach workbook.

```{eval-rst}
.. seealso::

   :mod:`riverarchitect.terraforming`, :mod:`riverarchitect.riverbuilder`,
   :mod:`riverarchitect.volume_assessment` and :mod:`riverarchitect.volume` in the API
   reference.
```
