# River Architect

**Analyze and design fluvial ecosystems.**

River Architect supports river engineers and ecologists in planning habitat-enhancing river design features: their expected lifespans, their required dimensions, where they belong in the terrain, and what they are worth ecologically.

Geoprocessing runs on **GDAL** (through rasterio, numpy and scipy) and map production runs on **QGIS** print layouts; River Architect runs on Linux, macOS, and Windows.

The methods are documented in:
* [Schwindt, Larrieu, Pasternack, Rabone,  2020. River Architect. SoftwareX 11, 100438. doi: 10.1016/j.softx.2020.100438
](https://doi.org/10.1016/j.softx.2020.100438)
* [Larrieu, Pasternack, Schwindt, 2021. Automated analysis of lateral river connectivity and fish stranding risks-Part 1: Review, theory and algorithm. Ecohydrology 14, e2268. doi: 10.1002/eco.2268](https://doi.org/10.1002/eco.2268)
* [Phillips, Pasternack, Larrieu, 2025. Development and testing of a mechanistic potential niche model of riparian tree seedling recruitment. Ecological Modelling 501, 110986. doi: 10.1016/j.ecolmodel.2024.110986](https://doi.org/10.1016/j.ecolmodel.2024.110986)




## Where to start

| | |
|---|---|
| {doc}`setup/index` | install it, and what it needs |
| {doc}`usage/index` | run it - the worked example, the API in a page, and the interface |
| {doc}`getstarted/index` | prepare a condition: the step everything else depends on |
| {doc}`modules/index` | the analyses themselves |

```{admonition} The interface can walk you through it
:class: tip

**Help ▸ Live Guide: Example** opens a seven-step walkthrough of the sample reach *inside*
the program: it sets the project directory to the sample data, and each step brings the tab
it talks about to the front. The same content is at {doc}`guide/example_walkthrough`.
```

```{admonition} Migrating from the ArcGIS version?
:class: note

{doc}`guide/arcpy_migration` maps every arcpy operation in v1 used onto its open-source equivalent, and documents the semantic differences that silently produce wrong results if you port code naively: implicit extent alignment, what a two-argument `Con()` does on its false branch, and the fidelity gaps found by running the whole chain.
```

## Contents

```{toctree}
:maxdepth: 4

setup/index
usage/index
getstarted/index
modules/index
tools
faq
troubleshooting
development/index
about
```

## What it does

**Lifespan and design mapping** predicts how long a restoration feature will survive as a
function of terrain change, morphology and 2D hydrodynamic results, and what dimensions it
needs to be stable - for example the minimum size of angular boulders that will not mobilise
in a flood. **Max Lifespan** then compares features and reports which one belongs at each
cell.

**Morphology (Terraforming)** lowers the terrain where a planned planting cannot reach the
water table, and compares pre- and post-project elevation models to quantify the earth
movement a design requires. Volumes are integrated under the triangulated surface, so
quantities stay comparable with the original software.

**Ecohydraulics** evaluates habitat suitability over a range of discharges and integrates it
into a single seasonal habitat area, identifies wetted areas that become disconnected as
flows recede - which is where fish strand - and maps where riparian seedlings can establish.

**Mapping** renders results into publication-quality PDF map series through QGIS print
layouts, with multi-page reach series driven by a QGIS atlas.

## Citing

> Schwindt, S., Larrieu, K., Pasternack, G.B., Rabone, G. (2020). River Architect.
> *SoftwareX* 11, 100438. <https://doi.org/10.1016/j.softx.2020.100438>

## Indices

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`
