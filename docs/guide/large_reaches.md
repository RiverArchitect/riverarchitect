# Large reaches

A river of a few kilometres fits in memory many times over. A river of a few hundred does not: a 400 km reach mapped at 1 to 2 m spans a **bounding box** of tens of billions of cells, and a single float raster of that box needs more than 100 GiB before any analysis has started. No amount of installed memory solves that, and most of those cells are NoData anyway, since the river covers perhaps one percent of its bounding box.

River Architect therefore processes such rasters **block by block**. Nothing has to be switched on and nothing about the workflow changes: every analysis checks whether its rasters would fit in memory and, if they would not, runs the same computation on one block at a time. The log says when that happens:

```text
   >> 221184 x 173568 cells exceed the memory budget - processing block by block
      * cHSI at Q = 750: 2862 block(s) of 4096x4096 cells on 4 thread(s)
```

## What stays the same

**The results.** A block-wise run gives the same rasters, cell for cell, and the same areas as an in-memory run. Operations that look at neighbouring cells (cover radius, mineral cover fraction, terrain slope) read a margin of extra cells around each block. Operations that reach across the whole reach are stitched across block seams: pool connectivity and the main channel in *Stranding Risk*, the escape-route search with a velocity criterion, and the polygon layers. The test suite holds every module to that on the sample reach, with blocks small enough that every seam cuts through the channel. Only means and volumes, which are summed in a different order, can differ in the last few digits.

**The inputs and outputs.** The same files, names and summary tables. Output GeoTIFFs are tiled and, where needed, BigTIFF, with overviews so that QGIS draws them quickly.

## What is different

**Empty blocks are skipped.** A block in which every input is NoData is neither computed nor written, and the output files are sparse, so the empty part of the bounding box costs almost no time and no disk space. For a long river this is where most of the time is saved.

**Extrapolated water surfaces stop at the terrain.** *Get Started* extrapolates the water surface (`wle.tif`) and the detrended DEM from the wetted cells. In memory the surface covers the whole grid; block by block it covers only blocks that hold at least one DEM cell, since a surface far from any terrain serves no analysis. Every product derived from it (`h_interp.tif`, `d2w.tif`) is unaffected.

**Very large samples are thinned.** The water surface and detrended DEM are interpolated from wetted cells. If even that sample of points would not fit in memory, every n-th cell is used instead and the log says so. On any reach where the sample fits, the result is exactly the in-memory one.

**Some functions return a path instead of an array.** {func}`~riverarchitect.preprocessing.detrended_dem`, {func}`~riverarchitect.preprocessing.water_level_elevation`, {func}`~riverarchitect.preprocessing.interpolated_depth`, {func}`~riverarchitect.preprocessing.depth_to_water_table` and {func}`~riverarchitect.preprocessing.morphological_units` return the array they computed. For a grid too large to hold they work block by block whenever they are given an `output_path`, and return that path instead of an array; without one they raise an error saying so. {class}`~riverarchitect.volume_assessment.VolumeAssessment` offers its difference raster only through `run(output_dir=...)` on such grids, and {meth}`StrandingRisk.escape_routes <riverarchitect.stranding.StrandingRisk.escape_routes>` and {meth}`~riverarchitect.stranding.StrandingRisk.main_channel`, which return whole arrays, remain in-memory methods: `run()` does not use them on large grids.

## Settings

The defaults suit most machines. They can be changed through environment variables, set before the program starts, or from Python:

| Setting | Environment variable | Default | Meaning |
|---|---|---|---|
| {func}`config.set_memory_budget() <riverarchitect.config.set_memory_budget>` | `RIVERARCHITECT_MAX_MEMORY` | half of the installed memory | how much an analysis may plan to hold at once, e.g. `16G` |
| {data}`config.TILING <riverarchitect.config.TILING>` | `RIVERARCHITECT_TILING` | `auto` | `auto` decides per run, `always` and `never` force the choice |
| {data}`config.BLOCK_SIZE <riverarchitect.config.BLOCK_SIZE>` | `RIVERARCHITECT_BLOCK_SIZE` | `4096` | block edge in cells; shrunk automatically when blocks would not fit |
| {data}`config.WORKERS <riverarchitect.config.WORKERS>` | `RIVERARCHITECT_WORKERS` | up to 4 | blocks processed in parallel |

On Windows, set a variable for one session in the *Anaconda Prompt* before starting the program:

```bat
set RIVERARCHITECT_MAX_MEMORY=24G
riverarchitect
```

From Python:

```python
from riverarchitect import config

config.set_memory_budget("24G")
config.WORKERS = 8
```

More workers are faster but hold more blocks at once. Blocks are sized so that all workers together stay within the budget.

## Preparing large inputs

**Use compressed, tiled GeoTIFFs with a NoData value.** A block is read without touching the rest of the file only when the file itself is tiled, and empty blocks are recognised without decoding them only when the file is compressed and declares its NoData value: the tile index then shows which tiles are empty. Other rasters work too, but every block of them is read and checked, which on a long reach costs most of the run time. Convert them once with GDAL, which ships with the environment:

```bash
gdal_translate -co TILED=YES -co COMPRESS=DEFLATE -co PREDICTOR=3 -co BIGTIFF=IF_SAFER in.tif out.tif
```

**Give every raster of a condition the same grid.** Rasters on differing grids are resampled block by block, which is correct but slower than reading an aligned file. **Get Started ▸ align every raster onto one grid** does this once, block by block as well.

**Keep the NoData value consistent.** `riverarchitect-reconcile-nodata` rewrites a condition to one NoData value and streams large rasters rather than reading them whole.

## Splitting a reach

Splitting a long reach into sub-reaches, for instance with `gdal_translate -projwin`, is no longer necessary, and it has a cost: connectivity does not cross the cut lines, so *Stranding Risk* would count pools cut off by a sub-reach boundary that are in fact connected. Split only where the reaches are genuinely independent.
