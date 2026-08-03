# Volumes and earthworks

River Architect reports cut and fill quantities as a project deliverable, so how the volume under a surface is integrated is a substantive choice, not an implementation detail.

## Two ways to integrate, and why they differ

**Cell-prism sum.** Treat every cell as a vertical prism: `volume = sum(z) * cell_area`. Simple, and wrong at the edges. A raster surface is a set of samples at cell *centres*; the prism model implicitly extends each boundary cell by half a cell in every direction, so the result carries an error proportional to the perimeter of the surface.

**Triangulated surface (TIN).** Build a triangulated surface through the cell centres and integrate under it. Every 2x2 block of neighbouring centres forms a quad split into two triangles; over each triangle the elevation varies linearly and the volume against a reference plane has a closed form, with clipping where the surface crosses the plane.

The difference is not small. For a flat surface at z = 5 over an 11x11 grid of 1 m cells:

| Method | Volume | Comment |
|---|---|---|
| TIN | 500.0 m³ | the TIN spans 10 x 10 m, from centre to centre |
| cell-prism sum | 605.0 m³ | 21 % high; counts a half-cell skirt all the way round |

For surfaces that are truncated at their edge, that error does **not** vanish under grid refinement, because the perimeter term scales with the boundary, not the cell size.

{mod}`riverarchitect.volume` uses the triangulated method, which is what surveying and earthworks software reports, so quantities are comparable with a contractor's own figures.

## Usage

```python
import numpy as np
from riverarchitect.volume import surface_volume

z = np.full((11, 11), 5.0)
result = surface_volume(z, dx=1.0, dy=1.0, plane=0.0, reference="ABOVE")

result["volume"]   # 500.0  cubic map units
result["area_2d"]  # 100.0  planimetric area contributing to the volume
result["area_3d"]  # 100.0  draped (true surface) area
```

`reference="BELOW"` integrates the part of the surface below the plane. NoData cells (`numpy.nan`) drop the triangles that touch them, matching arcpy's behaviour of building the TIN only where data exists.

The draped area `area_3d` is genuinely useful for costing surface treatments such as seeding or revetment, where the quantity follows the real surface rather than its map footprint. The original code computed it and threw it away.

## Earthworks between two DEMs

{mod}`riverarchitect.volume_assessment` wraps the above into the usual workflow:

```python
from riverarchitect.volume_assessment import VolumeAssessment

va = VolumeAssessment("dem.tif", "dem_modified.tif", unit="us",
                      level_of_detection=0.99)
result = va.run(output_dir="Output/volumes")
```

Three things it does that are worth knowing about:

**Explicit alignment.** If the two DEMs do not share a grid, the modified DEM is resampled onto the original's grid before differencing, and the fact is logged. The original relied on `arcpy.env.extent` to reconcile this silently, which is the most likely way to get quietly wrong numbers when the post-project survey covers a different footprint.

**Level of detection.** Elevation changes smaller than this threshold are treated as survey noise and zeroed before integration. Defaults to 0.99 ft (`unit="us"`) or 0.30 m (`unit="si"`), matching the original module. Set it from your own survey error analysis; it directly scales the reported quantities.

**Unit handling.** With `unit="us"` inputs are read as feet and volumes reported in cubic yards; with `unit="si"`, metres and cubic metres. The raster's own units are not inspected, so this must match your data.

## Verification

The integration is checked against twelve cases with exact analytical answers: flat and tilted planes, planes crossing the reference (clipping), non-zero reference planes, the `BELOW` direction, anisotropic cells, NoData exclusion and draped area on a 45-degree slope (100·√2). A pyramid whose ridges deliberately do not follow the triangulation converges to the exact volume under refinement (1330.0 → 1332.5 → 1333.125 against an exact 1333.33), which is the expected behaviour: a TIN approximates such a surface rather than reproducing it.

See `tests/test_volume.py` and `tests/test_volume_assessment.py`.
