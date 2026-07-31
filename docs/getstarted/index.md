# Get started, terminology and signposts

Section 2 of the original wiki. What a *Condition* is, what the file naming conventions
mean, how to prepare the input rasters, and how to analyse a flow record - everything that
has to exist before an analysis can run.

The module is {mod}`riverarchitect.preprocessing` (with {mod}`riverarchitect.flows` for the
flow side), and the **Get Started** tab of the interface.

## Conditions

A **condition** is one folder under `01_Conditions/` holding the terrain, sediment and
hydraulic rasters for a single planning situation: existing state, with-project state, a
design variant. Every analysis runs *against a condition*, and comparing two conditions is
how a project is evaluated.

## Geofile conventions

These are not cosmetic. The modules find rasters by name.

| Name | What it is |
|---|---|
| `dem.tif` | digital elevation model |
| `dem_detrend.tif` | detrended DEM: elevation above the local thalweg |
| `dmean.tif` | mean grain size |
| `d2w.tif` | depth to the groundwater table |
| `mu.tif` | morphological units |
| `wle.tif` | water level elevation |
| `scour.tif`, `fill.tif` | DEM of difference: annual erosion and deposition |
| `h<Q>.tif` | flow depth at discharge `Q` |
| `u<Q>.tif` | flow velocity at the same discharge |
| `ts<Q>.tif` | dimensionless bed shear stress (Shields stress) at that discharge |
| `tb<Q>.tif` | squared shear velocity `u*^2` at that discharge |
| `hks<Q>.tif` | relative submergence `h/ks` at that discharge |
| `regime<Q>.tif` | which bed-resistance law applied: 1 Rickenmann-Recking, 2 blended, 3 Keulegan-Einstein, 0 invalid |

`<Q>` is the discharge as a **six-digit, zero-padded** integer, so 1000 cfs is `h001000.tif`.
That is how {class}`riverarchitect.condition.Condition` recovers the discharge from a file
name, and how depth is paired with velocity. Conditions written by River Architect 1.x
instead spell a fractional discharge with `_` for the decimal point
(`h000001_060.tif` is 1.06); both forms are read, and a derived raster keeps the spelling of
the hydraulic rasters it came from.

The last four are written by **Get Started ▸ dimensionless bed shear stress (taux)** - see
{func}`riverarchitect.preprocessing.bed_shear_stress`. They are outputs, not inputs: nothing
requires them, and Lifespan Design and Riparian Recruitment recompute the stress internally
rather than reading them, so an edited or stale `ts<Q>.tif` cannot silently change an
analysis.

```{admonition} Units are in the data, not in the name
:class: warning

The original distinguished `dmean.tif` from `dmean_ft.tif`. This release does not: a
condition is in one unit system throughout, stated once, and mixing them within a folder is
the error the naming convention was papering over.
```

```{admonition} Record the grain-size statistic
:class: important

The legacy name `dmean.tif` does not prove that a raster contains $D_{50}$, $D_{84}$, or
an arithmetic mean.  That distinction matters in the Lifespan module's
{doc}`dimensionless bed-shear calculation <../modules/lifespans>`: supply measured $D_{84}$
where possible, or use $D_{84}\approx2.2D_{50}$ only when the input is actually $D_{50}$.
Store that interpretation in the condition metadata so a later analysis does not silently
apply the conversion to the wrong statistic.
```

## Input definition files

`input_definitions.inp` names which raster is which, and gives the **flood return period of
each modelled discharge**. It is the metadata every analysis needs before it can start, and
the return periods are what turn a set of discharges into a lifespan axis.

```text
Return periods = 1.0, 1.08, 1.13, 2.0, 5.0, 20.0, 50.0 #[Comma separated LIST]
Flow depth (h) = h007250.tif, h007750.tif, ... #[Comma separated LIST]
Flow velocity (u) = u007250.tif, u007750.tif, ... #[Comma separated LIST]
Grain sizes (D mean) = dmean #[STRING]
Detrended DEM = dem_detrend #[STRING]
Depth to groundwater table (d2w) = d2w #[STRING]
Morphological units (mu) = mu #[STRING]
DEM = dem #[STRING]
DEM of differences = fill, scour #[Comma separated LIST]
```

The format is the original's, so existing conditions are read unchanged: everything after
`#` is a comment, keys are matched case-insensitively on a substring, and `.tif` is
optional. {func}`riverarchitect.preprocessing.write_input_definitions` writes one.

Only the discharges listed here carry a return period, so **only these are used for lifespan
mapping**. The ecohydraulic modules scan the folder instead and use every `h<Q>.tif` on
disk - on the sample reach that is 60 rasters against the 17 the `.inp` names.

Without a flood frequency analysis to hand, {func}`riverarchitect.flows.return_periods`
fits a Gumbel distribution to an annual maximum series and gives a defensible first estimate.

## Prepare input rasters

The **Get Started** tab builds each of these; so does
{func}`riverarchitect.preprocessing.build_product`.

| Product | Writes | Why it is needed |
|---|---|---|
| Detrended DEM | `dem_detrend.tif` | 3 ft above the bed means something different where the bed is 10 ft higher; detrending removes the downstream slope so elevations are comparable along a reach |
| Water surface | `wle.tif`, `h_interp.tif`, `d2w.tif` | extrapolates a continuous water surface from the wetted area, which is what makes a depth-to-groundwater raster possible on dry land |
| Morphological units | `mu.tif` | classifies the wetted area into pools, riffles, runs and the rest, after Wyrick and Pasternack (2014) |
| Analyze flows | `00_Flows/<condition>/flow_duration_<code>.xlsx` | one seasonal flow duration curve per species and lifestage - what SHArea is integrated over |
| `input_definitions.inp` | the file above | the metadata every module reads |
| Align | rewritten rasters | puts the whole condition on one grid |

Use a low, in-channel discharge as the reference for the detrended DEM and the water
surface.

```{admonition} Building a product overwrites the condition's copy
:class: warning

With no output directory, `build_product` writes into the **condition folder** - so
rebuilding `dem_detrend.tif`, `d2w.tif` or `mu.tif` replaces the one that shipped with it.
That is deliberate and matches the original: the products *are* part of the condition, and
the modules read them from there.

It does mean the sample condition is no longer pristine after a run, and that a later
comparison against the shipped rasters compares them with themselves. Two ways round it:

* pass an output directory (`output_dir=...`, or **Output directory** in the tab) and build
  into a scratch folder, which is what the comparison figures on this page were produced
  with; or
* work on a copy of `sample-data/`, which is what the Live Guide's *Use the sample data*
  button does not do - it points at the directory in place.

`git checkout sample-data/` restores it in a clone.
```

```{admonition} Interpolation: what the original could not offer
:class: note

The original produced its nearest-neighbour surfaces by converting rasters to point
shapefiles, running `SpatialJoin_analysis` with `match_option="CLOSEST"`, and converting
back. That round trip through vector data was the only way to get a nearest-neighbour
interpolation out of `arcpy`. Here it is
{func}`riverarchitect.raster.nearest_neighbour` directly, with
{func}`riverarchitect.raster.idw` and {func}`riverarchitect.raster.kriging` as alternatives -
and kriging can return its estimation variance, which the ArcGIS implementation could not
easily expose.
```

## Analyze flows

{mod}`riverarchitect.flows` turns a daily record of dates and mean daily discharge into:

* a **seasonal flow duration curve** per species and lifestage. Chinook fry occupy the reach
  between 1 February and 15 June, so the flows of the rest of the year say nothing about
  their habitat - the season comes from `Fish.xlsx`, and only the flows inside it count;
* the **exceedance probability of each modelled discharge**, interpolated on that curve,
  written to the `2D data` sheet that {class}`riverarchitect.sharc.SHArC` reads;
* an **annual maximum series** and, optionally, Gumbel return periods for the
  `input_definitions.inp` line above.

Without this step SHArea cannot be computed at all: there is nothing to weigh one discharge
against another with.

## Map extent definition files

Map extents are QGIS print layouts rather than the original's `.inp` extent files. See
{doc}`../modules/maps`.

## Reference

```{toctree}
:maxdepth: 1

Get started, conditions and geofile conventions (legacy) <../wiki/Signposts>
```

```{eval-rst}
.. seealso::

   :mod:`riverarchitect.preprocessing`, :mod:`riverarchitect.flows` and
   :mod:`riverarchitect.condition` in the API reference.
```
