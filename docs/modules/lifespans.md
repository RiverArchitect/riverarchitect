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

### Dimensionless bed shear stress (`taux`)

River Architect keeps the historical name `taux` for the **Shields parameter**.  It is not
a dimensional stress and it is not the $x$-component of a stress tensor.  For the reference
grain fraction $D_{84}$,

$$
\theta_{84} \equiv \mathtt{taux}
  = \frac{u_*^2}{g(s-1)D_{84}},
\qquad
\tau_b = \rho_w u_*^2,
$$

where $u_*$ is shear velocity, $g$ is gravitational acceleration, $s=\rho_s/\rho_w$,
and $\tau_b$ is dimensional bed shear stress.  The hydraulic-model raster supplies the
depth-averaged speed $U$, not $u_*$, so a flow-resistance relation is needed to recover
$u_*^2$ cell by cell.

Define

$$
k_s=2D_{84}, \qquad \chi=\frac{h}{k_s}, \qquad x=\frac{h}{D_{84}}=2\chi.
$$

The current calculation changes resistance law with relative submergence:

| Relative submergence | Resistance relation | Interpretation |
|---|---|---|
| $\chi \le 7$ | Rickenmann--Recking | protruding grains and large-scale roughness strongly affect the depth-averaged flow |
| $7 < \chi < 20$ | smooth blend | avoids a numerical seam between resistance laws |
| $\chi \ge 20$ | Keulegan--Einstein | well-submerged, fully rough logarithmic resistance |

The high-submergence branch is

$$
C_K \equiv \frac{U}{u_*}
 = 5.75\log_{10}(12.2\chi).
$$

This is the relation represented by the original ArcPy expression
`Square(u / (5.75 * Log10(12.2 * h / (2 * D84))))`.  It contains **one** base-10
logarithm.  It is a depth-integrated resistance law derived from a logarithmic wall profile;
it does not require two logarithmic layers in the water column, and it does not assert that
the instantaneous velocity profile is logarithmic from the grain crests to the free surface.

For lower submergence, River Architect uses the field relation of Rickenmann and Recking
(2011):

$$
C_{RR} \equiv \frac{U}{u_*}
 = 4.416x^{1.904}
   \left[1+\left(\frac{x}{1.283}\right)^{1.618}\right]^{-1.083}.
$$

Within the transition interval, let

$$
t=\frac{\chi-7}{20-7}, \qquad w=t^2(3-2t),
$$

and blend the **stress coefficient**, not the velocity ratio:

$$
C_f = \left(\frac{u_*}{U}\right)^2
    = \frac{1-w}{C_{RR}^2}+\frac{w}{C_K^2}.
$$

Outside that interval, $C_f=C_{RR}^{-2}$ below it and $C_f=C_K^{-2}$ above it.  The
reported quantities are then

$$
u_*^2=U^2C_f, \qquad
\tau_b=\rho_wU^2C_f, \qquad
\mathtt{taux}=\frac{U^2C_f}{g(s-1)D_{84}}.
$$

```{admonition} What the switch does and does not diagnose
:class: important

The values 7 and 20 are River Architect's engineering transition bounds, not universal
phase boundaries.  Published field comparisons show that the unmodified Keulegan relation
can disagree substantially with gravel-bed observations at low relative depth; the precise
range also depends on bed structure, form drag, slope and how $k_s$ is defined.  The
Rickenmann--Recking branch is therefore used where a grain-only log law is least defensible,
and the interval is blended so a one-cell change in depth does not create a jump in stress.

This switch assumes turbulent, hydraulically rough gravel/cobble flow.  Check the roughness
Reynolds number $k_s^+=u_*k_s/\nu$: if viscosity still affects the resistance, use a
smooth/transitionally rough resistance law or, preferably, bed shear exported by the
hydraulic model.  The switch also cannot separate grain stress from bar, step, bank,
vegetation or large-wood form drag.
```

```{admonition} Relative submergence is not the shallow-water assumption
:class: note

$h/k_s$ compares water depth with bed roughness.  Saint-Venant or depth-averaged modelling
instead requires depth to be small relative to the horizontal length scale and vertical
accelerations to remain modest.  A wide river can satisfy the depth-averaged approximation
while having low $h/k_s$.  Conversely, a locally deep pool can contain strong three-
dimensional secondary flow.  River Architect uses local depth $h\approx R$ as a wide-channel
approximation to hydraulic radius; for narrow or sidewall-dominated channels, calculate the
appropriate hydraulic radius or use modelled bed shear.
```

```{admonition} The grain percentile must be consistent
:class: warning

Use a measured $D_{84}$ raster when possible.  The fallback $D_{84}\approx2.2D_{50}$ was
the median relation in the Rickenmann--Recking field data and is only justified when the
input represents $D_{50}$.  A file called `dmean.tif` is not automatically $D_{50}$;
record what statistic it contains.  Compare $\theta_{84}$ with a critical Shields value
defined for the same reference fraction, or apply an explicit hiding/exposure correction.
```

Primary sources: [Keulegan (1938)](https://nvlpubs.nist.gov/nistpubs/jres/21/jresv21n6p707_A1b.pdf),
[Einstein (1950)](https://books.google.com/books?id=ah_n36gVE2gC), and
[Rickenmann and Recking (2011)](https://doi.org/10.1029/2010WR009793).

#### Where it lives, and what it writes

{func}`riverarchitect.shear.calculate_taux` is the single implementation; both
{meth}`riverarchitect.lifespan.LifespanDesign.shields_stress` and
{meth}`riverarchitect.recruitment.RecruitmentPotential.shields_stress` call it, so the two
modules cannot drift apart. It is pure numpy and takes plain arrays, so it can be used
directly on any aligned depth, velocity and $D_{84}$ rasters.

Every run writes two diagnostic rasters per discharge beside its maps:

| Raster | Content |
|---|---|
| `hks<Q>.tif` | relative submergence $\chi=h/k_s$ |
| `regime<Q>.tif` | 0 invalid, 1 Rickenmann--Recking, 2 blended, 3 Keulegan--Einstein |

Read `regime<Q>.tif` before trusting a stress map. On the bundled sample reach about 95 % of
wet cells are regime 1, meaning the original program's single logarithmic law was applied
almost everywhere outside its range of validity.

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
