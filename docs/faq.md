# FAQ

Section 5 of the original wiki, brought up to date. For anything not answered here, see
{doc}`troubleshooting`.

**What is a *condition*?**
: A planning state: one folder under `01_Conditions/` holding the terrain, sediment and
  hydraulic rasters for a single situation. Conventionally a four-digit year followed by a
  label - `2100_sample`, `2008_existing`, `2008_with_project`. Every analysis runs against a
  condition, and comparing two conditions is how a project is evaluated. See
  {doc}`getstarted/index`.

**Do I need ArcGIS, an Esri licence or Spatial Analyst?**
: No. That is the point of this release. The geoprocessing runs on GDAL through rasterio,
  with numpy and scipy for the algebra. Nothing in the analysis chain needs a licence, and it
  runs on Linux, macOS and Windows.

**Do I need QGIS?**
: Only for the Maps tab. Every analysis module works without it, and the tab degrades
  gracefully with a message rather than failing. See {doc}`modules/maps`.

**How do I change map styles?**
: Layer styles are QGIS `.qml` files in the package's `templates/symbology/`. Edit them in
  QGIS and save over the file, or point the Maps tab at your own. `riverarchitect-lyrx2qml`
  converts an existing ArcGIS Pro `.lyrx`.

**Why is my lifespan map empty, or much smaller than I expected?**
: Almost always a missing input rather than a bug. A criterion whose raster the condition
  does not have is **skipped**, not failed - so a feature keyed to depth-to-water-table maps
  nothing useful without `d2w.tif`. Run {doc}`getstarted/index` first. Second most common:
  the feature is restricted to morphological units that your `mu.tif` does not contain.

**Why are cells with a long lifespan NoData instead of a large number?**
: Because their lifespan is longer than the largest modelled flood and cannot be quantified
  from the data. Writing a number there would be inventing one. Model a larger discharge if
  you need to resolve them.

**Several features report exactly the same mapped area. Is that a bug?**
: No. Features can differ in their hydraulic thresholds and still share a spatial mask - at
  the largest floods every cell inside a shared depth-to-water-table band fails eventually,
  so the mapped *extent* is identical even though the lifespans within it are not.

**The Max Lifespan shares add up to more than 100%.**
: Ties are kept rather than broken: a cell where two features both reach the maximum lifespan
  appears in both layers. That is deliberate - it tells you the choice is yours.

**Why can I not compute SHArea?**
: SHArea needs a flow duration curve for that species and lifestage, in
  `00_Flows/<condition>/flow_duration_<code>.xlsx`. Build one from a daily flow record with
  **Get Started ▸ analyze flows** ({mod}`riverarchitect.flows`).

**Which discharges does an analysis use?**
: Lifespan mapping uses only the discharges listed in `input_definitions.inp`, because only
  those carry a flood return period. The ecohydraulic modules scan the condition folder and
  use every `h<Q>.tif` on disk. On the sample reach that is 17 against 60.

**Do I have to convert my rasters when I switch the unit system?**
: No - and the switch does not convert them either. The Units menu *states* what your data
  already is. A mismatch does not raise an error anywhere; it silently applies the wrong
  thresholds.

**Can I use the modules without the interface?**
: Yes. Every tab is a thin front end over an ordinary Python module. See
  {doc}`guide/quickstart` and the {doc}`API reference <api/index>`.

**Is everything from the ArcGIS version here now?**
: Every analysis module is, including River Builder ({doc}`modules/morphology`) and Project
  Maker ({doc}`modules/projectmaker`), which were the last two. What remains unported is the
  pool-riffle morphology designer ({doc}`tools`), which never depended on arcpy, and the
  velocity criterion of Stranding Risk ({doc}`modules/ecohydraulics`). Both are called out
  where they belong.

## Legacy page

```{toctree}
:maxdepth: 1

Frequently asked questions (legacy) <wiki/FAQ>
```
