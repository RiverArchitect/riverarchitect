# FAQ

The questions that come up most often. If something has already gone wrong, {doc}`known-issues` lists the error messages and what each one means.

**What is a *condition*?**
: A planning state: one folder under `01_Conditions/` holding the terrain, sediment and hydraulic rasters for a single situation. Conventionally a four-digit year followed by a label - `2100_sample`, `2008_existing`, `2008_with_project`. Every analysis runs against a condition, and comparing two conditions is how a project is evaluated. See {doc}`../getstarted/index`.

**What do I need installed?**
: A conda environment, not a GIS. The geoprocessing runs on GDAL through rasterio, with numpy and scipy for the algebra and geopandas for the vector side. No licence is needed anywhere in the analysis chain, and it runs on Linux, macOS and Windows. See {doc}`../setup/index`.

**Do I need QGIS?**
: Only for the Maps tab. Every analysis module works without it, and the tab degrades gracefully with a message rather than failing. See {doc}`../modules/maps`.

**How do I change map styles?**
: Layer styles are QGIS `.qml` files in the package's `templates/symbology/`. Edit one in QGIS, save it over the file, or point the Maps tab at your own. A whole map can also be styled by hand: put a `river_template.qgz` in `02_Maps/templates/` and the Maps tab starts from that project instead of composing a layout in code, so base layers and house styling survive.

**Why is my lifespan map empty, or much smaller than I expected?**
: Almost always a missing input rather than a bug. A criterion whose raster the condition does not have is **skipped**, not failed, so a feature keyed to depth-to-water-table maps nothing useful without `d2w.tif`. Run {doc}`../getstarted/index` first. Second most common: the feature is restricted to morphological units that your `mu.tif` does not contain.

**Why are cells with a long lifespan NoData instead of a large number?**
: Because their lifespan is longer than the largest modelled flood and cannot be quantified from the data. Writing a number there would be inventing one. Model a larger discharge if you need to resolve them.

**Several features report exactly the same mapped area. Is that a bug?**
: No. Features can differ in their hydraulic thresholds and still share a spatial mask - at the largest floods every cell inside a shared depth-to-water-table band fails eventually, so the mapped *extent* is identical even though the lifespans within it are not.

**The Max Lifespan shares add up to more than 100 %.**
: Ties are kept rather than broken: a cell where two features both reach the maximum lifespan appears in both layers. That is deliberate - it tells you the choice is yours.

**Why can I not compute SHArea?**
: SHArea needs a flow duration curve for that species and lifestage, in `00_Flows/<condition>/flow_duration_<code>.xlsx`. Build one from a daily flow record with **Get Started ▸ analyze flows** ({mod}`riverarchitect.flows`).

**Which discharges does an analysis use?**
: Lifespan mapping uses only the discharges listed in `input_definitions.inp`, because only those carry a flood return period. The ecohydraulic modules scan the condition folder and use every `h<Q>.tif` on disk. On the sample reach that is 17 against 60.

**Do I have to convert my rasters when I switch the unit system?**
: No - and the switch does not convert them either. The Units menu *states* what your data already is. A mismatch does not raise an error anywhere; it silently applies the wrong thresholds.

**How do I add a fish species, or change a habitat suitability curve?**
: Edit the packaged `Fish.xlsx`, or a copy kept with your project. The layout is described under *The Fish workbook* in {doc}`../modules/ecohydraulics`.

**How do I change a feature's survival thresholds?**
: The defaults are Python, in {data}`riverarchitect.lifespan.FEATURES`, so they can be read and diffed. For a project-specific set, keep a `threshold_values.xlsx` with the project and load it with {func}`riverarchitect.lifespan.load_threshold_workbook`. See {doc}`../modules/features`.

**Can I use the modules without the interface?**
: Yes. Every tab is a thin front end over an ordinary Python module. See {doc}`../guide/quickstart` and the {doc}`API reference <../api/index>`.

**How do I design a pool-riffle sequence?**
: **Tools ▸ Pool-riffle designer**, or `riverarchitect-pool-riffle`. It sizes pool and riffle widths that reach a target pool depth at the discharge which just mobilises the bed, and checks that the sequence would actually maintain itself. See {doc}`../tools`.
