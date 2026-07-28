# River Architect

**Analyse and design fluvial ecosystems.**

River Architect supports river engineers and ecologists in planning habitat-enhancing river
design features: their expected lifespans, their required dimensions, where they belong in
the terrain, and what they are worth ecologically.

This is the open-source release. The geoprocessing runs on GDAL, rasterio, numpy and scipy,
and map production runs on QGIS print layouts, so **no Esri software or licence is
required** and the package runs on Linux, macOS and Windows.

The method is documented in an
[open-access, peer-reviewed paper](https://doi.org/10.1016/j.softx.2020.100438)
(*SoftwareX*, 2020).

```{admonition} Migrating from the ArcGIS version?
:class: tip

Start with {doc}`guide/arcpy_migration`. It maps every arcpy operation the original used
onto its open-source equivalent and, more importantly, documents the two semantic
differences that silently produce wrong results if you port code naively: implicit extent
alignment, and what a two-argument `Con()` does on its false branch.
```

## Getting started

```{toctree}
:maxdepth: 2
:caption: User guide

guide/installation
guide/installation_detailed
guide/gui
guide/tutorial
guide/quickstart
guide/volumes
guide/qgis_mapping
guide/arcpy_migration
```

New here? {doc}`guide/installation` takes a few minutes, then {doc}`guide/tutorial` runs a
lifespan map and a fish stranding assessment end to end on the sample data that ships with
the repository. {doc}`guide/gui` covers the graphical interface.

## What it does

**Lifespan and design mapping** predicts how long a restoration feature will survive as a
function of terrain change, morphology and 2D hydrodynamic results, and what dimensions it
needs to be stable (for example the minimum size of angular boulders that will not mobilise
in a flood).

**Terraforming and volumes** compares pre- and post-project digital elevation models to
quantify the earth movement a design requires. Volumes are integrated under the
triangulated surface, so quantities remain comparable with the original software.

**Ecohydraulics** evaluates habitat suitability over a range of discharges, and identifies
wetted areas that become disconnected as flows recede, which is where fish strand.

**Mapping** renders results into publication-quality PDF map series through QGIS print
layouts, with multi-page reach series driven by a QGIS atlas.

## API

```{toctree}
:maxdepth: 2
:caption: API reference

api/index
```

## Legacy user guide

The pages below are the original River Architect wiki, preserved for reference. They
describe the modules of the ArcGIS-based version; the analysis concepts, parameters and
design-feature definitions remain accurate and are the best available background on the
method, but installation instructions and code examples in them refer to the old software.

```{toctree}
:maxdepth: 1
:caption: Concepts and legacy modules

wiki/Signposts
wiki/River-design-features
wiki/RiverReaches
wiki/LifespanDesign
wiki/LifespanDesign-parameters
wiki/LifespanDesign-code
wiki/MaxLifespan
wiki/ModifyTerrain
wiki/RiverBuilder
wiki/VolumeAssessment
wiki/SHArC
wiki/SHArC-working-principles
wiki/StrandingRisk
wiki/RSR
wiki/ProjectMaker
wiki/Mapping
wiki/Tools
wiki/aqua-modification
wiki/Troubleshooting
wiki/FAQ
```

```{toctree}
:maxdepth: 1
:caption: Development

wiki/DevModule
wiki/DevGit
wiki/DevWiki
wiki/Dev2do
wiki/Installation
```

```{toctree}
:maxdepth: 1
:caption: About

wiki/Acknowledgment
wiki/Disclaimer
wiki/main_page
```

## Citing

> Schwindt, S., Larrieu, K., Pasternack, G.B., Rabone, G. (2020). River Architect.
> *SoftwareX* 11, 100438. <https://doi.org/10.1016/j.softx.2020.100438>

## Indices

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`
