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
│   └── flow_duration_*.xlsx     flow duration curves per species and lifestage
└── 01_Conditions/2100_sample/
    ├── dem.tif                  digital elevation model, ft
    ├── dem_detrend.tif          detrended DEM, ft
    ├── dmean.tif                mean grain size, ft
    ├── d2w.tif                  depth to the water table, ft
    ├── scour.tif, fill.tif      DEM of difference, ft, on a 5 ft grid
    ├── wle.tif                  water level elevation, ft
    ├── mu.tif, mu_str.tif       morphological units
    ├── back.tif, boundary.tif   background and analysis boundary
    ├── h000300.tif … h088053.tif   flow depth at 60 discharges, ft
    ├── u000300.tif … u088053.tif   flow velocity at the same discharges, ft/s
    ├── flow_definitions.xlsx    discharge definitions
    └── input_definitions.inp    raster names and the return period of each discharge
```

The six-digit number in a hydraulic raster name is the discharge in cfs: `h001000.tif` is
flow depth at 1000 cfs.

Grids are **not** uniform. Depth, velocity, grain size and the DEM are on a 3 ft grid;
`scour.tif` and `fill.tif` are on a 5 ft grid, and `back.tif` on a 3.28 ft grid. Combining
them requires an explicit `raster.align()` - that is deliberate, and it is what real
conditions look like.

## Provenance

The rasters are byte-for-byte the same data as upstream. They were recompressed on import
(DEFLATE with the floating-point predictor, from largely uncompressed GeoTIFFs) to bring the
directory from 60 MB to 9 MB. Cell values, NoData masks, geotransforms and CRS were verified
identical for all 131 rasters after conversion.

## Licence

See the upstream repository. The data is provided for demonstration and testing.
