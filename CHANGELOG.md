# Changelog

All notable changes to River Architect are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project follows
[semantic versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.0] - 2026-07-31

**Corrected bed shear stress, and conditions from River Architect 1.x are readable again.**
The dimensionless bed shear stress the original computed with a single logarithmic
resistance law is replaced by a regime-aware one, which changes every result that depends on
it. Separately, conditions whose hydraulic rasters use 1.x's decimal discharge naming were
invisible to the whole package; they now work. The interface gains an application icon.

### Changed

- **The dimensionless bed shear stress is now regime-aware, and referenced to `D84`.**
  The original's single Keulegan-Einstein expression assumed one logarithmic resistance law
  at every relative submergence; on the bundled sample reach about 95 % of wet cells sit at
  `h/ks < 7`, where that law does not hold and the computed stress diverges as the argument
  of the logarithm approaches one. `riverarchitect.shear.calculate_taux` now uses
  Rickenmann-Recking (2011) below `h/ks = 7`, Keulegan-Einstein above 20, and a smooth
  stress-coefficient blend between them, with the Shields stress referenced to
  `D84 = 2.2 * dmean` rather than to the mean grain size. **Every taux-dependent result
  moves**: `lifespan.FEATURES` and the recruitment parameters keep their critical values
  numerically and are now read as `theta84` thresholds. On the sample reach `Generic`
  planting rose from 23 166 to 44 775 sqft and full recruitment potential from 17 361 to
  31 977 sqft. `docs/guide/arcpy_migration.md` records the reasoning.
- **The legacy wiki pages say so.** `docs/wiki/LifespanDesign.md` and `docs/wiki/RSR.md`
  still carry the ArcPy 1.x equations verbatim, as the rest of `docs/wiki/` does, but each
  now opens with a note that the shipped calculation differs and links to the current
  equations. They document the historical method, not the current one.
- **The documentation navigation is one tree.** The eight captioned `toctree` blocks on the
  landing page collapsed into a single one, with `collapse_navigation` on so only the current
  branch expands. License, acknowledgments and disclaimer moved behind a new `docs/about.md`
  rather than sitting loose at the root.

### Added

- `riverarchitect.shear` - the single implementation of the Shields stress, pure numpy and
  usable on any aligned rasters. `lifespan` and `recruitment` both call it, so the two
  cannot drift apart.
- **The bed shear stress is written out, not just used.** Four rasters per discharge:
  `ts<Q>.tif` (the dimensionless Shields stress the thresholds are compared against),
  `tb<Q>.tif` (`u*^2`), `hks<Q>.tif` (relative submergence) and `regime<Q>.tif`
  (0 invalid, 1 Rickenmann-Recking, 2 blended, 3 Keulegan-Einstein), so both the stress and
  the closure used to reach it are visible rather than implicit. Lifespan Design and
  Riparian Recruitment write them into their output folder for the discharges they used.
- `preprocessing.bed_shear_stress`, reachable as the Get Started product **dimensionless
  bed shear stress (taux)**, writes the same four into the **condition folder** for every
  modelled discharge - the counterpart of 1.x's `LifespanDesign/helper.py`, which wrote
  `ts/` and `tb/` subfolders there. They go beside `h<Q>.tif` and `u<Q>.tif` instead, since
  a subfolder per quantity split one discharge's rasters across three places. `tb` keeps
  the 1.x prefix but is documented as what 1.x actually stored there: `u*^2`, not the
  `rho_w u*^2` its name claims. Nothing reads these back - both analyses recompute the
  stress - so a stale or hand-edited `ts<Q>.tif` cannot quietly change a result.
- **"Water depth" replaces "flow depth" throughout.** Depth is a property of the water
  column, not of the flow, so the term the ArcGIS version used was wrong. The
  documentation, the docstrings and the interface now say water depth, and
  `write_input_definitions` writes `Water depth (h) = ...` into new
  `input_definitions.inp` files. **Existing conditions keep working**: the parser reads
  both spellings, and 1.x is unaffected because it reads that file by line position rather
  than by key. Two strings deliberately keep the old wording because they are literal
  identifiers of the ArcGIS version rather than prose - the `Flow depth` row label in
  `threshold_values.xlsx`, which 1.x matches exactly, and the `WARNING: Could not get
  minimum flow depth` message quoted on the troubleshooting page.
- `Condition.describe()` and `Condition.validate()` - what a condition folder provides, what
  it lacks, and the raster naming discovery expects. Analyses that cannot start now embed
  that report in the error instead of only saying what was missing.
- `riverarchitect-taux` - the Shields stress calculation as a command-line tool, for one set
  of rasters outside a condition folder (`python -m riverarchitect.tools.taux`).
- **An application icon.** Both front ends set it (`iconphoto` on tkinter,
  `setWindowIcon` on Qt) from `config.icon_path()`, and the artwork ships inside the package
  as `riverarchitect/assets/icon-v2.png` so an installed copy has it too. On Windows the
  process declares `config.APP_ID` as its AppUserModelID, without which the taskbar groups
  the window under the Python interpreter instead of showing the icon. The previous artwork
  is kept as `docs/img/icon-stale*`.
- **A note on the grain-size statistic** in the Get Started docs: `dmean.tif` is a file name,
  not a promise about which percentile it holds, and the bed-shear calculation's
  `D84 = 2.2 * D50` fallback is only defensible when the input really is `D50`.

### Fixed

- **Conditions using River Architect 1.x decimal discharge names were invisible.**
  `h000001_060.tif` (1.06 m³/s, written by 1.x's `write_Q_str` as `%010.3f` with `_` for the
  decimal point) matched neither the discovery pattern nor the discharge parser, which read
  only the leading digits and would have collided distinct discharges at the same integer.
  Such a condition reported "no paired depth and velocity rasters" however complete it was.
  Both naming forms are now read, sorted numerically, and round-tripped through the new
  `condition.discharge_token`; output file names, `input_definitions.inp` writing and the
  discharge lists in both front ends follow. A raster derived from a discharge keeps the
  spelling of the hydraulic rasters it came from (`Condition.token_for`), so
  `u000293_000.tif` yields `ts000293_000.tif` rather than the canonical `ts000293.tif` -
  both parse back to 293, but only the first keeps a discharge's rasters together in a
  sorted listing.

## [2.2.0] - 2026-07-30

**Feature parity with the ArcGIS original.** River Builder and Project Maker were the last
two modules without an open-source implementation; both are ported here, so every analysis
the 1.x series offered now runs without Esri software, without R, and without a licence. The
interface carries all eleven modules.

### Added

**The last two ArcGIS modules, ported**

- `riverarchitect.riverbuilder` - **River Builder**. Generates a synthetic river valley -
  meandering centreline, varying bankfull width, thalweg, symmetric/asymmetric/trapezoidal
  cross-sections, floodplain and terrace benches - and writes it as a DEM with a hillshade.
  The original called a 1189-line R script through `rpy2` and rebuilt the point cloud as a
  TIN with ArcGIS 3D Analyst; the geometry is numpy here and the TIN is
  `scipy.interpolate.LinearNDInterpolator`, so neither R nor a licence is needed. The
  parameter file format is unchanged, so an existing RiverBuilder input runs as it is, and
  the `PERL` noise is seeded so a run is reproducible - the original's was not.
- `riverarchitect.projectmaker` - **Project Maker**. Prices the works from what the earlier
  modules mapped, compares SHArea between an existing and a with-project condition, and
  reports the cost per unit of habitat gained. The unit rates are the original workbook's,
  held as Python so a change to a rate is reviewable; the four percentage rates compound in
  the order the workbook applied them.
- New **Morphology ▸ River Builder** and **Project Maker** tabs in both front ends. The
  interface now carries all eleven modules.

### Fixed

- Two bugs found while porting River Builder, both in this release's own new code: the
  channel slope dropped the `valley_slope / sinuosity` term, which left a channel that
  barely fell and an absurd regime depth with it; and the arc length started at the first
  step rather than at zero, so a perfectly straight valley reported a sinuosity of 1.01.
- Project Maker no longer derives a quantity for a rate priced per length or per piece from
  a mapped area. Pricing 250 000 logs because a feature covers 250 000 square feet is how a
  cost estimate becomes fiction; those lines are left empty and named in the log instead.

### Documentation

- Section captions are no longer numbered.
- **Development** is one page instead of five. The nested *DEVELOPMENT* page, *Using git*,
  *Edit the Wiki*, *The to-do list for developers* with its *DETAILED PROBLEM DESCRIPTIONS*,
  and the *Full list of folders and files* are removed. *Add a module to River Architect* is
  reconciled into a single flat section and rewritten for this codebase - the legacy version
  documented `master_gui.py`, `moduleTEMPLATE/` and `arcpy.sa`, none of which exist here.
- The **API reference** is now part of *Development* rather than a section of its own.
  `navigation_depth` is raised to 4 so its module pages stay visible in the sidebar.
- **About** drops the legacy *River Architect overview* / *River Architect Wiki* landing page
  and gains a **License** page: the BSD 3-Clause terms in plain language and in full, the
  citation, and the third-party components River Architect builds on.

## [2.1.1] - 2026-07-29

### Fixed

- **Two tests failed on Windows.** `test_mapping_discovery` checked the QGIS bindings
  search by comparing prefix templates against literal POSIX paths, but `os.path.normpath`
  rewrites `/` as a backslash on Windows, so `/Applications/QGIS.app/Contents/MacOS` and
  `/opt/qgis3.40` never matched there. The shipped code was correct - nothing looks for
  those paths on Windows - but the sdist carries the test suite, so the released artefact
  failed `pytest` on that platform. Comparisons are now separator-agnostic, and the
  behaviour is verified under emulated Windows path semantics as well as POSIX.

## [2.1.0] - 2026-07-29

The first release to have been **run end to end**. Every module was executed in order on
`sample-data/2100_sample` and compared against River Architect 1.4, which turned up three
capabilities the wiki describes that had no code at all, and six places where the port was
plausible but did not do what the original did. All are closed here. Details for each are in
*Fidelity gaps found by running the whole chain* in `docs/guide/arcpy_migration.md`.

The documentation is restructured to follow the original wiki's table of contents, and both
front ends gained a **Live Guide** that walks through the whole chain on the sample reach
without leaving the program.

> **Results change.** Nothing in the public API was removed or narrowed, so this is a minor
> release and existing code keeps working. **Numbers do change**, because several analyses
> were wrong before:
>
> - lifespan mapping now applies the morphological-unit criterion, which it never did - on
>   the sample reach `backwt` falls from 124 074 to 2 295 sqft and `gravin` from 33 273 to
>   7 515;
> - riparian recruitment counts *consecutive* inundated days rather than their total - full
>   recruitment potential rises from 5 949 to 17 361 sqft;
> - SHArea can be computed at all for the first time, because nothing could previously build
>   the flow duration curve it integrates over.
>
> Re-run any project you intend to compare against, rather than mixing figures from 2.0.0
> and 2.1.0.

### Added

**Modules the wiki describes that had no code**

- `riverarchitect.flows` - **Analyze Flows**. Turns a daily flow record into a *seasonal*
  flow duration curve per species and lifestage (the season comes from `Fish.xlsx`),
  interpolates the exceedance of each modelled discharge onto it, and writes the
  `flow_duration_<code>.xlsx` that SHArC reads. Also annual peak series and a Gumbel
  `return_periods()` for the `input_definitions.inp` line. **SHArea could not be computed at
  all before this**: nothing in the package could produce the curve it integrates over.
  Reachable as **Get Started ▸ analyze flows** in both front ends.
- `riverarchitect.terraforming` - the threshold-based **grading and widening** half of the
  original `ModifyTerrain`. Lowers the DEM where a planned feature sits further above the
  water table than its roots can reach, by exactly the excess, applying features in sequence
  so each sees the previous one's excavation. New **Morphology ▸ Terraforming** tab in both
  front ends; feed its `dem_terraformed.tif` to Volume Assessment.
- `riverarchitect.sharc.cover_hsi` - the **cover** option of SHArC: substrate, cobbles,
  boulders, plants and wood, each sheltering the area within its radius, combined by
  cell-wise maximum. `SHArC.run(cover=True)` uses whatever the condition provides.
- `riverarchitect.raster.within_radius` - the Euclidean distance transform that replaces the
  original's raster-to-points, `SpatialJoin_analysis`, points-to-raster round trip.
- `FishDatabase.season_dates`, `SHArC.cover_layers`, `COVER_TYPES`, `GRAIN_SIZE_LIMITS`.

**Documentation**

- The structure now follows the original wiki's table of contents: **1. Software setup**
  (was "User guide"), **2. Usage (Quick Start)**, **3. Get started and signposts**,
  **4. Modules** (Lifespans, Morphology, Ecohydraulics, Maps, Project Maker), **5. Tools**,
  **6. FAQ**, **7. Troubleshooting** - with GDAL in place of arcpy throughout. New section
  landing pages carry the current content and link the legacy wiki page beneath each topic.
- `docs/troubleshooting.md` and `docs/faq.md` are new and current. The legacy troubleshooting
  page is 13 000 words of `arcpy` error codes that can no longer occur; it is kept for 1.x
  users but is no longer what a reader lands on.

**The Live Guide**

- `riverarchitect.guide` - the **Live Guide**, a nine-step walkthrough of the sample reach
  held as data so both front ends render the same content. Reachable from **Help ▸ Live
  Guide: Example** in the Qt and the tkinter interface; it can point the project directory
  at the sample data and bring the tab each step talks about to the front.
- `docs/guide/example_walkthrough.md` - the same walkthrough on this site, with the numbers
  each step produces.
- `sample-data/00_Flows/2100_sample/flow_series_2020.csv` and the `make_flow_series.py` that
  generates it. The condition ships flow duration curves but no dated record, so riparian
  recruitment could not be run on it at all. The discharges are the reach's own; only their
  ordering in time is synthetic.
- `FishDatabase.resolve_species` and `resolve_lifestage`; `stranding.travel_thresholds`;
  `preprocessing.MU_ALIASES` and `MorphologicalUnits.classifiable`;
  `raster.disconnected_mask(..., target=...)`; `StrandingRisk.target_discharge`,
  `species`, `lifestage` and `u_max`; `percent_of_max_wetted` in the stranding result.
- The `Help` menu now also carries `F1` for the documentation in the Qt front end, and both
  launcher scripts point new users at the Live Guide.

### Fixed

- **`SHArC` could not be run with the species name every other module uses.** `Fish.xlsx`
  spells it `Chinook Salmon` and `stranding.TRAVEL_THRESHOLDS` spelled it `Chinook salmon`,
  and the lookup was case-sensitive, so `SHArC.run("Chinook salmon", ...)` raised
  `KeyError`. Species and lifestage are now matched ignoring case and spacing.
- **The morphological-unit criterion never applied.** `lifespan` looked only for a workbook
  beside the condition and so found no codes; and `MorphologicalUnits` discarded the twenty
  floodplain units, which are the ones the feature thresholds name, because they carry no
  depth or velocity range. The packaged table is now the fallback, floodplain units are
  kept, the two workbooks' differing unit vocabularies are bridged, and a name that does not
  resolve is logged instead of silently dropped.
- **`sideca`, `gravin` and `gravou` lost their morphological-unit lists** when `FEATURES`
  was transcribed from `threshold_values.xlsx`, so they were mapped without their spatial
  restriction.
- **Stranding connectivity was seeded per discharge** rather than from the largest wetted
  region at the lowest analysed discharge, which is the target the original built its
  least-cost escape routes towards.
- **Riparian recruitment counted inundation as total submerged days** rather than the
  longest consecutive run, counted recession stress on submerged cells, and used one scalar
  denominator instead of resetting per cell when a cell goes dry during seed dispersal.
- **`preprocessing.build_product("inp")` ignored `output_dir`** and always overwrote the
  condition's `input_definitions.inp`.
- `stranding.for_fish` now reads the packaged `Fish.xlsx` first, as `cFish` did, rather than
  only its own hard-coded table.
- **"QGIS is not available" although QGIS was installed.** The bindings cannot come from
  PyPI, so a distribution installs them for the *system* interpreter and a conda environment
  never saw them - the message then told the user to install software they already had.
  `riverarchitect.mapping` now searches the standard locations for the platform (Debian and
  Fedora layouts on Linux, the `.app` bundle on macOS, OSGeo4W and the standalone installer
  on Windows, newest first), registers the matching `bin` directories with
  `os.add_dll_directory` on Windows so the Qt/GDAL/PROJ libraries load, and **appends** the
  result to `sys.path`. Overridable with `RIVERARCHITECT_QGIS_PATH` and `QGIS_PREFIX_PATH`.
  New `mapping.qgis_status()` gives both front ends one actionable message.
- `QgisSession.start` hard-coded the prefix `/usr`, which is meaningless on macOS and
  Windows; it now uses the prefix that belongs to the bindings actually loaded.
- `SHArC` cover cropping now excludes NoData depth cells, matching `Con(h >= h_min, cover)`:
  a cell the 2D model never covered is unknown, not shallow.
- Four legacy wiki pages shared the title *Feature lifespan and design assessment*, so the
  navigation showed the same entry four times. They now have distinct titles.
- `toc.not_included` is no longer suppressed in the Sphinx configuration: a page in no
  toctree is a page nobody can reach, and that is how stale documentation accumulates.
- The docs build is back to **zero warnings** locally. `sphinx.ext.viewcode` imported the
  real PySide6, whose shiboken import hook then ran `inspect.getsource` on autodoc's mocked
  numpy and sent `inspect.unwrap` into "wrapper loop when unwrapping numpy", failing every
  later autodoc import. The Qt bindings are now blocked for the docs build, as they already
  are on Read the Docs.
- `read_flow_series` had two copies; `recruitment` now re-exports the one in `flows`.

### Documentation

- `sample-data/README.md` records the two upstream rasters that are inconsistent with their
  file names (`u000550.tif`, `h088053.tif`) and where they surface in results.

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

[2.2.0]: https://github.com/RiverArchitect/riverarchitect/releases/tag/v2.2.0
[2.1.1]: https://github.com/RiverArchitect/riverarchitect/releases/tag/v2.1.1
[2.1.0]: https://github.com/RiverArchitect/riverarchitect/releases/tag/v2.1.0
[2.0.0]: https://github.com/RiverArchitect/riverarchitect/releases/tag/v2.0.0
[1.0.0]: https://github.com/RiverArchitect/riverarchitect/releases/tag/v1.0.0
