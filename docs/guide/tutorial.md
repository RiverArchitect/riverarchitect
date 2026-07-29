# Tutorial: lifespan mapping and fish stranding

This walkthrough runs two complete analyses on a real reach: a **lifespan and design map**
for angular boulders, and a **fish stranding risk** assessment over a receding hydrograph.
Both use the public sample data, and every number printed below was produced by the code on
this page.

````{admonition} Two ways to run these
:class: tip

Both analyses are packaged modules with a tab in the interface -
{mod}`riverarchitect.lifespan` and {mod}`riverarchitect.stranding` - so in practice you would
click *Lifespan and design* and *Ecohydraulics* in the GUI, or call three lines of Python:

```python
from riverarchitect.lifespan import LifespanDesign
from riverarchitect.stranding import StrandingRisk

LifespanDesign("2100_sample").run(["rocks"])
StrandingRisk.for_fish("2100_sample", "Chinook salmon", "fry").run()
```

This page takes the long way round instead, building both analyses out of the raster
primitives. That is worth reading once: it shows exactly what the modules do, which
assumptions they make, and where you would change them for a river that behaves differently.
The physical background is in {doc}`../wiki/LifespanDesign`,
{doc}`../wiki/LifespanDesign-parameters` and {doc}`../wiki/StrandingRisk`.
````

The scripts on this page are in `examples/`, ready to run:

```bash
mamba run -n ra-env python examples/lifespan_rocks.py
mamba run -n ra-env python examples/stranding_risk.py
```

## The data

The data ships with the repository in `sample-data/`; there is nothing to download.

```bash
git clone https://github.com/RiverArchitect/riverarchitect.git
cd riverarchitect
```

It is a gravel-cobble reach in a Mediterranean climate, 359 x 173 cells at 3 ft
resolution, in **US customary units** (feet, cubic feet per second). Under
`sample-data/01_Conditions/2100_sample/`:

| File | What it is |
|---|---|
| `dem.tif`, `dem_detrend.tif` | elevation and detrended elevation |
| `dmean.tif` | mean grain size, ft |
| `d2w.tif` | depth to the water table, ft |
| `scour.tif`, `fill.tif` | DEM of difference, ft, on a **5 ft** grid |
| `h000300.tif` … `h088053.tif` | flow depth at 60 discharges, ft |
| `u000300.tif` … `u088053.tif` | flow velocity at the same discharges, ft/s |
| `input_definitions.inp` | which rasters belong to the condition, and the flood return period of each discharge |

The scripts resolve their paths through {func}`riverarchitect.config.project_home`: the
`RIVERARCHITECT_HOME` environment variable if set, otherwise the working directory, and
otherwise the bundled `sample-data/`. So they run from anywhere in a clone, and pointing
`RIVERARCHITECT_HOME` at your own project directory switches them to your data.

```{warning}
`scour.tif` is on a 5 ft grid; the depth, velocity and grain-size rasters are on a 3 ft
grid. They cannot be combined without an explicit {func}`riverarchitect.raster.align`. This
is not a quirk of the sample data - it is what real conditions look like, and it is why
alignment is explicit in this package rather than implicit as it was in `arcpy.env.extent`.
```

## Part 1: lifespan and design mapping

### The idea

A restoration feature survives until a flood mobilises it. For angular boulders placed on
the bed, "mobilised" means the flow can move a grain of the boulder's size. So: compute, at
each modelled discharge, the largest grain the flow can still move; compare that against the
grain size actually present; and the **lowest** flood return period at which the flow wins is
the feature's expected lifespan in years.

The critical grain size follows from Manning's equation and a Shields criterion:

$$
D_{cr} = \frac{(u \cdot n)^2}{(s - 1)\ \tau_{*,cr}\ h^{1/3}\ \mathit{SF}}
$$

with $u$ flow velocity, $h$ flow depth, $n$ Manning's roughness, $s = 2.68$ the relative
grain density, $\tau_{*,cr}$ the critical dimensionless bed shear stress and $\mathit{SF}$ a
safety factor. The default threshold values for angular boulders are $\tau_{*,cr} = 0.047$
and $\mathit{SF} = 1.3$.

### Setup

The return periods and their discharges come from `input_definitions.inp`:

```python
import os
import numpy as np
from riverarchitect import config, raster

CONDITION = os.path.join(config.dir_conditions(), "2100_sample")
OUT = os.path.join(config.dir_output("LifespanDesign"), "2100_sample")

LIFESPANS = [1.0, 1.08, 1.13, 1.19, 1.3, 1.4, 1.84, 2.0, 3.27,
             5.0, 6.53, 10.0, 15.0, 20.0, 30.0, 40.0, 50.0]
DISCHARGES = [7250, 7750, 8250, 8750, 9250, 9750, 10000, 12000, 16000,
              20000, 21100, 24000, 28000, 30000, 34000, 42200, 88053]

TAU_CR = 0.047          # (-) critical dimensionless bed shear stress
SF = 1.3                # (-) safety factor
S = 2.68                # (-) relative grain density
N = 0.0473934 / 1.49    # (s/ft^1/3) Manning's n; 1.49 converts from SI

os.makedirs(OUT, exist_ok=True)


def critical_grain_size(h, u):
    """Grain diameter that just starts to move, in feet."""
    return (u * N) ** 2 / ((S - 1.0) * TAU_CR * h ** (1.0 / 3.0)) / SF


def hydraulics(q, ref_prof):
    """Depth and velocity at discharge q, on the reference grid."""
    h, hp = raster.read(os.path.join(CONDITION, "h%06d.tif" % q))
    u, up = raster.read(os.path.join(CONDITION, "u%06d.tif" % q))
    h = raster.align(h, hp, ref_prof)
    u = raster.align(u, up, ref_prof)
    return np.where(h > 0, h, np.nan), u
```

Note `np.where(h > 0, h, np.nan)`: dry cells must become NoData, not zero, or the $h^{1/3}$
term divides by zero and produces an infinite critical grain size everywhere the bed is dry.

### The lifespan raster

The grain-size raster defines the reference grid; everything else is aligned onto it.

```python
dmean, prof = raster.read(os.path.join(CONDITION, "dmean.tif"))

failure = []
for years, q in zip(LIFESPANS, DISCHARGES):
    h, u = hydraulics(q, prof)
    with np.errstate(invalid="ignore", divide="ignore"):
        d_cr = critical_grain_size(h, u)
    failure.append(raster.con(d_cr >= dmean, years))

lifespan = raster.cell_statistics(failure, "MINIMUM")
raster.write(os.path.join(OUT, "lf_rocks.tif"), lifespan, prof)
```

Three functions are doing the work:

{func}`~riverarchitect.raster.con` with two arguments writes the return period where the grain is mobile and **NoData** everywhere else. Passing `0` for the false branch instead would put a zero-year lifespan on every stable cell and destroy the next step.

{func}`~riverarchitect.raster.cell_statistics` with `"MINIMUM"` then reduces the stack of 17 per-flood rasters to the earliest flood that mobilises each cell. Cells that survive every modelled flood are NoData in all 17 layers and stay NoData - correctly, since their lifespan
is longer than the 50-year event and cannot be quantified from this data.

`align` inside `hydraulics()` is a no-op here, because the depth and velocity rasters happen to share the grain-size grid. It becomes necessary in the next step, and leaving it in costs nothing.

### The design raster

A lifespan map says how long a feature lasts. A design map says how big it has to be. For a 20-year design target, that is the critical grain size at the 20-year flood:

```python
h, u = hydraulics(DISCHARGES[LIFESPANS.index(20.0)], prof)
with np.errstate(invalid="ignore", divide="ignore"):
    design = critical_grain_size(h, u) * 12.0          # ft -> in
design = raster.con(np.isfinite(lifespan), design)
raster.write(os.path.join(OUT, "ds_rocks.tif"), design, prof)
```

The final `con` clips the design raster to the extent of the lifespan raster, so the map only shows dimensions where placing the feature makes sense at all.

### Results

```python
dx, dy = raster.cell_size(prof)
mapped = np.isfinite(lifespan)
print("mapped area  %.0f sqft (%.2f ac)"
      % (mapped.sum() * dx * dy, mapped.sum() * dx * dy / 43560.0))
for years, count in zip(*np.unique(lifespan[mapped], return_counts=True)):
    print("  %6.2f years  %7.0f sqft" % (years, count * dx * dy))
print("stable grain size at the design flow: median %.1f in, max %.1f in"
      % (np.nanmedian(design), np.nanmax(design)))
```

```text
mapped area  65943 sqft (1.51 ac)
    1.00 years     9144 sqft
    1.08 years      594 sqft
    1.13 years      135 sqft
    1.19 years      243 sqft
    1.30 years       63 sqft
    1.40 years      171 sqft
    1.84 years     4599 sqft
    2.00 years     2034 sqft
    3.27 years     3006 sqft
    5.00 years     2502 sqft
    6.53 years      252 sqft
   10.00 years     1584 sqft
   15.00 years     6480 sqft
   20.00 years     2862 sqft
   30.00 years     9405 sqft
   40.00 years    22869 sqft
stable grain size at the design flow: median 3.7 in, max 7.1 in
```

Read that as a design statement: over 1.5 acres of this reach, boulders are mobile at some modeled flood. About 9100 sqft go at the annual flood and are not worth treating with placed rock; the 22900 sqft that survive to 40 years are where the feature pays for itself. Achieving a 20-year lifespan requires a median 3.7 in boulder, and up to 7.1 in in the fastest cells.

### Refinement: restrict to where the bed actually moves

Angular boulders are a response to scour, so the original method restricts the lifespan map to cells whose observed scour exceeds a threshold - 3 ft in the default threshold workbook. This is the step that needs the alignment, since `scour.tif` is on the 5 ft grid:

```python
scour, scour_prof = raster.read(os.path.join(CONDITION, "scour.tif"))
scour = raster.align(scour, scour_prof, prof)
restricted = raster.con(scour >= 3.0, lifespan)
print("after the 3 ft scour restriction: %.0f sqft"
      % (np.isfinite(restricted).sum() * dx * dy))
```

```text
after the 3 ft scour restriction: 18 sqft
```

Two cells. That is a real result, not a bug: on this reach the DEM of difference reaches 3 ft of scour in barely 1% of its cells, and those cells hardly overlap the mobile-grain area. The lesson is that the default threshold workbook is calibrated for a different river, and the topographic-change threshold is the first value to revisit for a new site. At 2 ft the restricted area is 1845 sqft; at 1 ft it is 6075 sqft.

## Part 2: fish stranding risk

### The idea

As a hydrograph recedes, the wetted area shrinks and breaks apart. Pools that lose their connection to the main channel trap fish. That is a connected-component problem: threshold the depth raster at the minimum swimming depth, label the wetted regions, and everything except the largest one is disconnected.

{func}`~riverarchitect.raster.disconnected_mask` is exactly this rule.

### Setup

The travel thresholds come from the fish database of the original software. For Chinook salmon fry the minimum swimming depth is 0.2 ft.

```python
import os
import numpy as np
from riverarchitect import config, raster

CONDITION = os.path.join(config.dir_conditions(), "2100_sample")
OUT = os.path.join(config.dir_output("StrandingRisk"), "2100_sample")

DISCHARGES = [1500, 1400, 1300, 1200, 1100, 1000, 900, 800, 700, 600, 500, 400, 300]
H_MIN = 0.2   # ft, minimum swimming depth, Chinook salmon fry

os.makedirs(OUT, exist_ok=True)

_, prof = raster.read(os.path.join(CONDITION, "h%06d.tif" % DISCHARGES[0]))
dx, dy = raster.cell_size(prof)
cell_area = dx * dy
```

### Walking the recession

```python
per_q = []
print("%8s %8s %12s %12s %8s" % ("Q", "pools", "wetted", "stranded", "%"))
for q in DISCHARGES:
    depth, dprof = raster.read(os.path.join(CONDITION, "h%06d.tif" % q))
    depth = raster.align(depth, dprof, prof)
    wet = np.nan_to_num(depth) > H_MIN

    mask, n_pools = raster.disconnected_mask(wet, connectivity=4)
    per_q.append(raster.con(mask, float(q)))

    wetted = wet.sum() * cell_area
    stranded = mask.sum() * cell_area
    print("%8d %8d %12.0f %12.0f %8.2f"
          % (q, n_pools, wetted, stranded, 100.0 * stranded / wetted))

    raster.write(os.path.join(OUT, "disconnected_%06d.tif" % q),
                 raster.con(mask, 1.0), prof)
```

`np.nan_to_num(depth) > H_MIN` turns NoData into `False` rather than letting the comparison propagate NaN. `connectivity=4` matches `arcpy.sa.RegionGroup`'s default: cells touching only at a corner are *not* one pool.

```text
       Q    pools       wetted     stranded        %
    1500        1       113319            9     0.01
    1400        1       111663            9     0.01
    1300        1       110205            9     0.01
    1200        1       108306            9     0.01
    1100        1       106380           18     0.02
    1000        2       104292           27     0.03
     900        1       102195           18     0.02
     800        1        99369           72     0.07
     700        3        96381          747     0.78
     600        6        92529          576     0.62
     500        8        89415          171     0.19
     400        5        85698           72     0.08
     300        1        81369            9     0.01
```

The peak is at 700 cfs: three pools holding 747 sqft, an order of magnitude more stranded area than at any neighbouring flow. Below that the pools multiply but shrink, and by 300 cfs the reach has drained down to a single connected thread again. If you have to pick one ramp rate to manage, 700 cfs is where a reservoir release should slow down.

### Where disconnection happens

Cells are of more use to a designer than a table. Recording the highest discharge at which each cell was disconnected gives one raster that answers "at what flow does this spot become a trap":

```python
q_disconnect = raster.cell_statistics(per_q, "MAXIMUM")
raster.write(os.path.join(OUT, "Q_disconnect.tif"), q_disconnect, prof)

total = np.isfinite(q_disconnect).sum() * cell_area
print("total area disconnected at some point: %.0f sqft (%.2f ac)"
      % (total, total / 43560.0))
```

```text
total area disconnected at some point: 1602 sqft (0.04 ac)
```

### Per-pool geometry

Polygonizing the mask gives one feature per pool, which is what goes into a map or a field sheet:

```python
depth, dprof = raster.read(os.path.join(CONDITION, "h000700.tif"))
depth = raster.align(depth, dprof, prof)
mask, _ = raster.disconnected_mask(np.nan_to_num(depth) > H_MIN, connectivity=4)

pools = raster.polygonize(mask.astype("int32"), prof, mask=mask)
pools["area"] = pools.geometry.area
pools = pools.sort_values("area", ascending=False)
pools.to_file(os.path.join(OUT, "pools_000700.gpkg"), driver="GPKG")
print(pools["area"].round(0).to_string(index=False))
```

```text
729.0
  9.0
  9.0
```

One pool of 729 sqft carries essentially all of the stranding risk at 700 cfs; the other two are single cells. A survey crew only needs to visit one place.

### Sensitivity to the depth threshold

`H_MIN` is the single most influential choice in this analysis, and it is a biological choice, not a numerical one. Over the thirteen discharges above:

| `H_MIN` | Meaning | Pools per discharge |
|---|---|---|
| 0 ft | every wet cell counts | 2 to 12 |
| 0.2 ft | Chinook salmon fry | 1 to 8 |
| 0.3 ft | Chinook salmon juvenile | 0 to 5 |

At `H_MIN = 0` much of the count is single cells at the wetted edge - real in the raster, meaningless in the river. The swimming-depth threshold removes that noise and leaves pools a fish could actually be trapped in. Choose it from the species and lifestage you are assessing, and state it alongside the result.

## What to do with the output

Both parts write GeoTIFFs into `sample-data/Output/`. To turn them into a map series, hand the directory to the mapping module, which locates the QGIS bindings itself; see {doc}`../modules/maps`:

```python
from riverarchitect.mapping import Mapper

mapper = Mapper("2100_sample", "lf",
                "sample-data/Output/LifespanDesign/2100_sample",
                "02_Maps/2100_sample")
mapper.prepare_layout(True)
mapper.make_pdf_maps("lf_rocks")
```

See {doc}`qgis_mapping` for layouts, atlases and symbology.

## The packaged equivalents

Everything above is what {mod}`riverarchitect.lifespan` and {mod}`riverarchitect.stranding` do internally, and both are verified against the numbers on this page. Two further steps are only available as modules:

```python
from riverarchitect.lifespan import LifespanDesign
from riverarchitect.maxlifespan import MaxLifespan

# map several features at once, with the default threshold values
LifespanDesign("2100_sample").run(["rocks", "wood", "cot", "gravin"])

# then ask which of them belongs where
MaxLifespan("sample-data/Output/LifespanDesign/2100_sample").run()
```

{class}`~riverarchitect.maxlifespan.MaxLifespan` takes the cell-wise maximum across the feature lifespan rasters and writes a best-feature mask and polygon layer per feature. It has no equivalent above because it only becomes meaningful once several features have been mapped.

## Next

* {doc}`gui` runs all of this from the graphical interface.
* {doc}`quickstart` covers the remaining primitives: interpolation, zonal statistics,
  reclassification, NoData reconciliation.
* {doc}`volumes` covers earthwork quantities from DEM differencing.
* {doc}`arcpy_migration` maps each arcpy operation used above onto its replacement, and
  records the defects found while migrating.
