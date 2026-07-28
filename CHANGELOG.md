# Changelog

All notable changes to River Architect are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project follows
[semantic versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-07-28

The open-source release. River Architect no longer requires Esri software: the
geoprocessing runs on GDAL, rasterio, numpy and scipy, and map production runs on QGIS print
layouts. It runs on Linux, macOS and Windows.

This is a rewrite rather than a port, so **it is not backwards compatible with 1.x**. See
*Removed* and *Migrating* below.

### Added

**Analysis modules**

- `riverarchitect.raster` - the open-source replacement for arcpy's raster algebra: I/O,
  alignment, `con`/`is_null`/`set_null`, `cell_statistics`, `reclassify`,
  polygonize/rasterize, IDW/kriging/nearest-neighbour interpolation, connected-component
  labelling and zonal statistics.
- `riverarchitect.condition` - reads a condition folder and its `input_definitions.inp`.
- `riverarchitect.preprocessing` (was *GetStarted*) - detrended DEM, water surface
  interpolation with the depth and depth-to-water-table rasters derived from it,
  morphological unit classification, `input_definitions.inp` writer, condition alignment.
- `riverarchitect.lifespan` (was *LifespanDesign*) - lifespan and design mapping for 21
  restoration features.
- `riverarchitect.maxlifespan` (was *MaxLifespan*) - best-feature assessment across several
  lifespan maps.
- `riverarchitect.volume` and `riverarchitect.volume_assessment` (was *VolumeAssessment*) -
  triangulated-surface volume integration and DEM differencing.
- `riverarchitect.sharc` (was *SHArC*) - habitat suitability indices from `Fish.xlsx`
  curves, composite HSI, and Seasonal Habitat Area integrated over the flow duration curve.
- `riverarchitect.stranding` (was *StrandingRisk*) - fish stranding risk from wetted areas
  that disconnect as a hydrograph recedes.
- `riverarchitect.recruitment` (was *RiparianRecruitment*) - the Recruitment Box Model:
  bed preparation, recession-rate desiccation, prolonged inundation and scour.
- `riverarchitect.mapping` - QGIS print layouts and multi-page PDF map series through a
  QGIS atlas.

**Interface**

- A Qt front end (PySide6, or the PyQt5 that ships with QGIS) is now the default, with the
  tkinter interface kept as an automatic fallback so the GUI always opens. Force one with
  `RIVERARCHITECT_GUI=qt|tk`.
- Tabs are grouped as in 1.x: Get Started, Lifespan, Morphology, Ecohydraulics, Maps.
- `runRiverArchitectLinux.sh` and `runRiverArchitectWin.bat` locate a working interpreter
  themselves and open the bundled sample data when given no argument.

**Data and tooling**

- `sample-data/` - a real gravel-cobble reach ships with the repository; no separate
  download. Recompressed losslessly on import, 60 MB to 9 MB.
- `riverarchitect-reconcile-nodata` - normalises inconsistent NoData sentinels in a
  condition, preserving the mask exactly.
- `riverarchitect-lyrx2qml` - converts ArcGIS layer symbology to QGIS styles.
- Documentation on Read the Docs, including the legacy wiki preserved for the analysis
  background.

### Changed

- **NoData is `numpy.nan` in memory.** Read through `raster.read()`, which applies the
  declared mask. `config.NODATA` (-999.0) is what the package *writes*, never what it tests
  against.
- **Raster alignment is explicit.** `arcpy.env.extent` silently reconciled operands of
  differing extent; numpy does not. Call `raster.align()` before combining rasters that do
  not provably share a grid.
- Feature threshold values moved from `threshold_values.xlsx` into `lifespan.FEATURES` as
  Python, so they are diffable in review. `lifespan.load_threshold_workbook()` still reads a
  project's customised workbook.
- Habitat suitability curves are interpolated with `numpy.interp` rather than a chain of
  per-segment `Con()` rasters. The end behaviour is unchanged and deliberately asymmetric:
  the first suitability is held below the curve, but a value above the curve scores zero.
- Selecting a GUI tab no longer changes the process working directory, resizes the window,
  or rebuilds the menu bar.

### Removed

- **arcpy, and with it the ArcGIS Pro and Spatial Analyst licence requirement.** No module
  imports arcpy; there is no Esri dependency anywhere in the package.
- The Windows-only assumption. Paths are built with `os.path` rather than hard-coded `\\`.
- *LifespanAnalysis*, *ModifyTerrain*/*RiverBuilder* and *ProjectMaker* have no equivalent
  yet. Their analysis logic is documented in the legacy wiki, and `raster.py` provides the
  primitives each of them needs.

### Migrating from 1.x

- Read `docs/guide/arcpy_migration.md` first. It records every arcpy call site of the
  original, its verified open-source equivalent, and the defects found during migration.
- Two differences silently produce wrong results if code is ported naively: implicit extent
  alignment, and what a two-argument `Con()` does on its false branch.
- Conditions carry over unchanged. `input_definitions.inp` is read in the original format,
  and `threshold_values.xlsx`, `Fish.xlsx` and `morphological_units.xlsx` are still
  supported.
- Outputs are written as GeoTIFF and GeoPackage instead of Esri grids and shapefiles.

## [1.0.0] - 2019

The ArcGIS release, built on `arcpy` and requiring ArcGIS Pro with a Spatial Analyst
licence on Windows. Described in the accompanying paper:

> Schwindt, S., Larrieu, K., Pasternack, G.B., Rabone, G. (2020). River Architect.
> *SoftwareX* 11, 100438. <https://doi.org/10.1016/j.softx.2020.100438>

[2.0.0]: https://github.com/RiverArchitect/riverarchitect/releases/tag/v2.0.0
[1.0.0]: https://github.com/RiverArchitect/riverarchitect/releases/tag/v1.0.0
