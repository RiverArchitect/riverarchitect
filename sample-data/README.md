# Sample data

A real gravel-cobble reach in a Mediterranean climate, used by the
[tutorial](../docs/guide/tutorial.md) and the scripts in [`examples/`](../examples).
**All datasets are in U.S. customary units** (feet, feet per second, cubic feet per second).

Originally published as <https://github.com/RiverArchitect/SampleData> and vendored here so
that the examples run straight out of a clone, with no second download.

## Using it

The directory is a complete River Architect *project home*. Point the package at it:

```bash
export RIVERARCHITECT_HOME=/path/to/riverarchitect/sample-data
```

```python
from riverarchitect import config
config.set_project_home("sample-data")
```

or launch the graphical interface with it:

```bash
riverarchitect sample-data
```

## Contents

```text
sample-data/
├── 00_Flows/2100_sample/
│   ├── flow_duration_*.xlsx     flow duration curves per species and lifestage
│   ├── flow_series_2020.csv     a daily flow record, for RiparianRecruitment
│   └── make_flow_series.py      the script that generates it
└── 01_Conditions/2100_sample/
    ├── dem.tif                  digital elevation model, ft
    ├── dem_detrend.tif          detrended DEM, ft
    ├── dmean.tif                mean grain size, ft
    ├── d2w.tif                  depth to the water table, ft
    ├── scour.tif, fill.tif      DEM of difference, ft, on a 5 ft grid
    ├── wle.tif                  water level elevation, ft
    ├── mu.tif, mu_str.tif       morphological units
    ├── back.tif, boundary.tif   background and analysis boundary
    ├── h000300.tif … h088053.tif   water depth at 60 discharges, ft
    ├── u000300.tif … u088053.tif   flow velocity at the same discharges, ft/s
    ├── flow_definitions.xlsx    discharge definitions
    └── input_definitions.inp    raster names and the return period of each discharge
```

The six-digit number in a hydraulic raster name is the discharge in cfs: `h001000.tif` is
water depth at 1000 cfs.

Grids are **not** uniform. Depth, velocity, grain size and the DEM are on a 3 ft grid;
`scour.tif` and `fill.tif` are on a 5 ft grid, and `back.tif` on a 3.28 ft grid. Combining
them requires an explicit `raster.align()` - that is deliberate, and it is what real
conditions look like.

## Two rasters are bad, and they are left that way

`u000550.tif` tops out at **1.4 ft/s** where its neighbours at 500 and 600 cfs reach 4.5 ft/s
(mean over wetted cells: 0.61, against 1.93 and 2.08). `h088053.tif` peaks at **6.8 ft** where
42200 cfs reaches 22.0 ft, and wets 11 322 cells against 39 648 - it is a low-flow result
wearing a flood's file name, and `u088053.tif` matches it.

Both are byte-for-byte what upstream publishes; neither was introduced here. They are kept
because they are instructive: nothing in the software can detect them for you, and they show
up in exactly the way a bad raster shows up in a real project - as one row of a result table
that does not fit the others. SHArC reports a collapsed usable area at 550 cfs; lifespan
mapping never reaches a 50-year lifespan from a hydraulic criterion, because the discharge
that carries that return period is the broken one.

`docs/guide/example_walkthrough.md` points at both where they surface.

## The daily flow record is synthetic

`00_Flows/2100_sample/flow_series_2020.csv` does not come from upstream. The condition ships
flow *duration* curves but no dated record, and the recruitment box model needs one, because
bed preparation, recession and scour are about *when* flows happened rather than which flows
are possible.

`make_flow_series.py` beside it builds one water year whose flow duration matches the
condition's own `Q data` sheet: the **discharges are the reach's own** and only their ordering
in time is invented - a Mediterranean year with a wet winter, three storms, a spring freshet
and a long summer recession, 730 to 61 093 cfs, median 1 720. Regenerate it with

```bash
python sample-data/00_Flows/2100_sample/make_flow_series.py \
    sample-data/00_Flows/2100_sample/flow_series_2020.csv
```

Treat recruitment results on this condition as a demonstration of the method, not as a
finding about the reach.

## Provenance

The rasters are byte-for-byte the same data as upstream. They were recompressed on import
(DEFLATE with the floating-point predictor, from largely uncompressed GeoTIFFs) to bring the
directory from 60 MB to 9 MB. Cell values, NoData masks, geotransforms and CRS were verified
identical for all 131 rasters after conversion.

## Licence

See the upstream repository. The data is provided for demonstration and testing.
