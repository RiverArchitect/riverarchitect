# River Architect

**Analyse and design fluvial ecosystems.**

River Architect supports river engineers and ecologists in planning habitat-enhancing river
design features: their expected lifespans, their required dimensions, where they belong in
the terrain, and what they are worth ecologically.

This is the open-source release. The geoprocessing runs on **GDAL** (through rasterio, numpy
and scipy) and map production runs on **QGIS** print layouts, so **no Esri software or
licence is required** and the package runs on Linux, macOS and Windows. Everywhere the
original documentation says *arcpy*, this one says GDAL.

The method is documented in an
[open-access, peer-reviewed paper](https://doi.org/10.1016/j.softx.2020.100438)
(*SoftwareX*, 2020).

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

{doc}`guide/arcpy_migration` maps every arcpy operation the original used onto its
open-source equivalent, and documents the semantic differences that silently produce wrong
results if you port code naively: implicit extent alignment, what a two-argument `Con()`
does on its false branch, and the fidelity gaps found by running the whole chain.
```

## Contents

```{toctree}
:maxdepth: 2
:caption: Software setup

setup/index
```

```{toctree}
:maxdepth: 2
:caption: Usage (Quick Start)

usage/index
```

```{toctree}
:maxdepth: 2
:caption: Get started

getstarted/index
```

```{toctree}
:maxdepth: 2
:caption: Modules

modules/index
```

```{toctree}
:maxdepth: 2
:caption: Tools

tools
```

```{toctree}
:maxdepth: 1
:caption: FAQ

faq
```

```{toctree}
:maxdepth: 2
:caption: Troubleshooting

troubleshooting
```

```{toctree}
:maxdepth: 2
:caption: Development

development/index
```

```{toctree}
:maxdepth: 1
:caption: About

license
wiki/Acknowledgment
wiki/Disclaimer
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
