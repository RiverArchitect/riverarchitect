# Usage quickstart

Please note that the mapping example needs QGIS.

## Reading and combining rasters

The two rules that matter most: NoData is always `numpy.nan` in memory, and rasters of differing extent must be **explicitly aligned** before they are combined.

```python
from riverarchitect import raster

dem, dem_profile = raster.read("sample-data/01_Conditions/2100_sample/dem.tif")
depth, depth_profile = raster.read("sample-data/01_Conditions/2100_sample/h001000.tif")

# The DEM and the depth raster rarely share a grid. arcpy hid this behind env.extent;
# here it is explicit, because the silent alternative is a spatially meaningless result.
depth = raster.align(depth, depth_profile, dem_profile)

# Water surface elevation where the bed is wet. The false branch becomes NoData, not zero.
wse = raster.con(depth > 0, dem + depth)

raster.write("wse.tif", wse, dem_profile)
```

## Wetted area and fish stranding risk

Pools that lose their connection to the main channel as discharge drops are a stranding risk. That is a connected-component problem:

```python
import numpy as np
from riverarchitect import raster

depth, profile = raster.read("sample-data/01_Conditions/2100_sample/h000300.tif")
wet = np.nan_to_num(depth) > 0

mask, n_pools = raster.disconnected_mask(wet, connectivity=4)

dx, dy = raster.cell_size(profile)
print(f"{n_pools} disconnected pools, {mask.sum() * dx * dy:.1f} sqft stranded")
```

Vectorise the result to get per-pool areas:

```python
pools = raster.polygonize(mask.astype("int32"), profile, mask=mask)
pools["area"] = pools.geometry.area
print(pools.sort_values("area", ascending=False).head())
```

## Interpolating a water surface

```python
from riverarchitect import raster

wse, wse_profile = raster.read("sample-data/01_Conditions/2100_sample/wle.tif")
dem, dem_profile = raster.read("sample-data/01_Conditions/2100_sample/dem.tif")

points, values = raster.raster_to_points(wse, wse_profile, step=5)

surface = raster.idw(points, values, dem_profile, k=12, power=2.0)
# or:  raster.nearest_neighbour(points, values, dem_profile)
# or:  raster.kriging(points, values, dem_profile, model="spherical")

depth_to_water = dem - surface
raster.write("d2w.tif", depth_to_water, dem_profile)
```

Kriging can also return the estimation variance, which was not straightforward in the ArcGIS implementation in v1:

```python
surface, variance = raster.kriging(points, values, dem_profile, return_variance=True)
```

## Earthworks quantities

```python
from riverarchitect.volume_assessment import VolumeAssessment

va = VolumeAssessment("dem.tif", "dem_modified.tif", unit="us")
result = va.run(output_dir="sample-data/Output/volumes")

print(f"fill       {result['fill_volume']:.1f} {result['volume_unit']}")
print(f"excavation {result['excavation_volume']:.1f} {result['volume_unit']}")
print(f"net        {result['net_volume']:.1f} {result['volume_unit']}")
```

Volumes are integrated under the triangulated surface through the cell centres, not summed as vertical prisms. See {doc}`volumes` for why that distinction is not cosmetic.

## Producing maps

```python
from riverarchitect.mapping import Mapper

mapper = Mapper("2100_sample", "lf", "sample-data/Output/LifespanDesign/2100_sample",
                "02_Maps/2100_sample")
mapper.prepare_layout(True)
```

For a multi-page reach series, set the page centres before exporting:

```python
mapper = Mapper("2100_sample", "lf", raster_dir, output_dir)
mapper.prepare_layout(False, map_items=["lf_wood.tif"])

extent = mapper.raster_extent
width = extent.width() / 3.0
mapper.xy_center_points = [[extent.xMinimum() + (i + 0.5) * width, extent.center().y()]
                           for i in range(3)]
mapper.dx, mapper.dy = width, extent.height()
mapper.make_pdf_maps("lf_wood_series")
```

This writes a single three-page PDF through a QGIS atlas, alongside a `.qgz` project you can open and refine in QGIS.

## Normalising input NoData

Conditions assembled from different preprocessing chains carry inconsistent NoData values. Reconcile a condition folder before analysis:

```bash
python -m riverarchitect.tools.reconcile_nodata sample-data/01_Conditions/2100_sample --dry-run
python -m riverarchitect.tools.reconcile_nodata sample-data/01_Conditions/2100_sample
```

The NoData *mask* is preserved exactly; only the sentinel changes.
