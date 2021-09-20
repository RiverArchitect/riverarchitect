Mapping
=======

***

- [Standard layouts](#lyts)
- [Modify the symbology](#sym)
- [Modify map extents](#extent)
- [Code information](#code)

***

# About Mapping with *River Architect*<a name="prepare"></a>
The `RiverArchitect/02_Maps/` folder contains a template structure that is copied by the <a href="LifespanDesign">LifespanDesign</a>, <a href="MaxLifespan">Max Lifespan</a>, and <a href="ModifyTerrain">Modify Terrain</a> modules to map their geodata outputs. The [[HabitatEvaluation]] module produces geofiles that can be mapped within the map project file of the <a href="ProjectMaker">ProjectMaker</a> module (`RiverArchitect/ProjectMaker/.templates/REACH_stn_vii_TEMPLATE/ProjectMaps.aprx`). This differentiation enables distinguished mapping of river sections and project (versions). This Wiki only treats the automated mapping routines of the results of the <a href="LifespanDesign">LifespanDesign</a>, <a href="MaxLifespan">Max Lifespan</a>, and <a href="ModifyTerrain">Modify Terrain</a> modules. The [ProjectMaker's result mapping](https://github.com/RiverArchitect/RA_wiki/ProjectMaker#mapping-of-construction-elements) is design for a user-specific map modifications and export.

Before running any of the before-mentioned modules for mapping, open `RiverArchitect/02_Maps/templates/river_template.aprx` (*ArcGIS Pro* project file) and correct the background layer image source (adapt to `CONDITION`) by right-clicking on the `background` layer (see figure below), then click on `Properties` > `Source` > `Set Data Source...`. Navigate to the `CONDITION` folder and select the `CONDITION`'s `background.tif` (the background raster file must have the name `background.tif` - mapping will be inconsistent otherwise).


![adaptproject](https://github.com/RiverArchitect/Media/raw/master/images/adapt_proj.PNG)

The standard symbology for lifespan rasters may be modified and it can be restored by right-clicking on a `lifespan` or `Best Lifespans` raster layer > `Symbology`. The *Symbology* opens up and the standard symbology can be restored from the top-right drop-down menu (`import (...)` > nagivate to `RiverArchitect/02_Maps/templates/symbology/` > select `LifespanRasterSymbology.lyrx`).

The project (`.aprx`) files contains a set of pre-defined layouts and layer names and these names must not be changed. Only consider changing the symbology or data sources, because the modules will automatically update the layer connection `database` and `dataset` according to the output data ([read more](https://pro.arcgis.com/en/pro-app/arcpy/mapping/updatingandfixingdatasources.htm)).

## Standard layouts<a name="lyts"></a>

<a href="LifespanDesign">LifespanDesign</a> layouts:

 - `layout_lf` for lifespan mapping
 - `layout_ds_bio` for [bioengineering features](https://github.com/RiverArchitect/RA_wiki/River-design-features#bioeng)
 - `layout_ds_Dcr` for [grain mobility maps](https://github.com/RiverArchitect/RA_wiki/River-design-features#rocks) and [sediment replenishment / gravel augmentation](https://github.com/RiverArchitect/RA_wiki/River-design-features#gravel)
 - `layout_ds_Dw` for [wood](https://github.com/RiverArchitect/RA_wiki/River-design-features#elj) diameter mobility maps
 - `layout_ds_FS_D15` for [fine sediment](https://github.com/RiverArchitect/RA_wiki/River-design-features#finesed)'s mobile *D<sub>15</sub>* sizes
 - `layout_ds_FS_D85` for [fine sediment](https://github.com/RiverArchitect/RA_wiki/River-design-features#finesed)'s mobile *D<sub>85</sub>* sizes
 - `layout_ds_SeS0` for ratios between terrain and (hypothetic) energy slopes ([side channels](https://github.com/RiverArchitect/RA_wiki/River-design-features#sidechnl))
 - `layout_ds_sideca` for [side cavity](https://github.com/RiverArchitect/RA_wiki/River-design-features#sidecav) application site mapping
 - `layout_ds` for [widen](https://github.com/RiverArchitect/RA_wiki/River-design-features#berms) application site mapping
 
<a href="MaxLifespan">Max Lifespan</a> layouts:

 - `layout_mlf_bioeng` for best lifespan maps of the (other) [bioengineering feature group](https://github.com/RiverArchitect/RA_wiki/River-design-features#featoverview)
 - `layout_mlf_maintenance` for best lifespan maps of the [maintenance/longitudinal connectivity feature group](https://github.com/RiverArchitect/RA_wiki/River-design-features#featoverview)
 - `layout_mlf_plants` for best lifespan maps of the [vegetation plantings feature group](https://github.com/RiverArchitect/RA_wiki/River-design-features#plants)
 - `layout_mlf_terraforming` for best lifespan maps of the  [terraforming feature group](https://github.com/RiverArchitect/RA_wiki/River-design-features#featoverview)
 
<a href="ModifyTerrain">Modify Terrain</a> layouts:

 - `volumes_cust_neg` for mapping the terrain differences (excavation terraforming works) of a manually modified DEM
 - `volumes_cust_pos` for mapping the terrain differences (fill terraforming works) of a manually modified DEM
 - `volumes_grade_neg` for mapping the terrain differences of parametrically (threshold-based) floodplain [grading](https://github.com/RiverArchitect/RA_wiki/River-design-features#grading) within the <a href="ModifyTerrain">Modify Terrain</a> module (only excavation `neg` is meaningful)
 - `volumes_widen_neg` for mapping the terrain differences of parametrically (threshold-based) river [widening](https://github.com/RiverArchitect/RA_wiki/River-design-features#berms) within the <a href="ModifyTerrain">Modify Terrain</a> module (only excavation `neg` is meaningful)
 

## Modify the symbology<a name="sym"></a>

For creating maps with a different symbology then the template symbology, proceed as follows:

 1. Run the *module* `Map Maker` function to create a copy of the template map folder, which will be created in `RiverArchitect/02_Maps/CONDITION/`.
 2. Open the automatically created `RiverArchitect/02_Maps/CONDITION/map_CONDITION_design.aprx` and adapt the symbology and legend as needed.
 3. Re-run the *module* `Map Maker` function to re-create (overwrite previous) `.PDF` maps. *Note:* When a *module* detects an existing version of `RiverArchitect/02_Maps/CONDITION/map_CONDITION_design.aprx` for the `CONDITION` that it is applied on, it will NOT OVERWRITE the PROJECT `MAP_CONDITION_DESIGN.APRX` file, but it will "overwrite existing `.PDF` maps."

 
## Modify map extents<a name="extent"></a>

The global map extents are determined by the input rasters to map. The same is true for raster calculations. The application scheme of *River Architect* (<a href="main_page">Home</a> Wiki page) starts with the usage of the <a href="LifespanDesign">LifespanDesign</a> module. Here, the calculation can be limited to the `background.tif` raster. Thus, for changing map extents, adapt the extent of input rasters for the <a href="LifespanDesign">LifespanDesign</a> and <a href="MaxLifespan">Max Lifespan</a> modules. For the <a href="ModifyTerrain">Modify Terrain</a> module adapt the `dem.tif` raster in the input/ [condition](https://github.com/RiverArchitect/RA_wiki/Signposts#conditions) folder, which determines the map extents. Moreover, when applying <a href="ModifyTerrain">Modify Terrain</a>, do not use another [condition](https://github.com/RiverArchitect/RA_wiki/Signposts#conditions) folder for the modified DEM for volume calculation, because it may interfere, for example, with the `dem_detrend.tif` raster. Preferably use a copy or extract the modified condition's `dem.tif` to `ModifyTerrain/Input/DEM/CONDITION/`.

Moreover, each module has an own mapping definition file to enable reach-wise or multiple map creation within one `PDF`. The particular map extent definitions are:

 - <a href="LifespanDesign">LifespanDesign</a>: `RiverArchitect/LifespanDesign/.templates/mapping.inp` ([see definitions](https://github.com/RiverArchitect/RA_wiki/LifespanDesign-input-files#mapping))
 - <a href="MaxLifespan">Max Lifespan</a>: `RiverArchitect/MaxLifespan/.templates/mapping.inp` ([definitions are analogue to the *LifespanDesign* module](https://github.com/RiverArchitect/RA_wiki/LifespanDesign-input-files#mapping))
 - <a href="ModifyTerrain">Modify Terrain</a>: `RiverArchitect/ModifyTerrain/.templates/computation_extents.xlsx` ([see reach definitions](https://github.com/RiverArchitect/RA_wiki/ModifyTerrain#input-set-reaches))


## Code information<a name="code"></a>

Mapping is centralized for the <a href="LifespanDesign">LifespanDesign</a>, <a href="MaxLifespan">Max Lifespan</a>, and <a href="ModifyTerrain">Modify Terrain</a> modules in the `Mapper()` class that is stored in `RiverArchitect/.site_packages/riverpy/cMapper.py`. The layout and layer names are hard-coded (*sorry for that...*) and this is why layer and layout names should not be changed in the project (`.aprx`) files.

 
[1]: https://github.com/RiverArchitect/RA_wiki/Installation
[2]: https://github.com/RiverArchitect/RA_wiki/Signposts
[3]: https://github.com/RiverArchitect/RA_wiki/LifespanDesign
[4]: https://github.com/RiverArchitect/RA_wiki/MaxLifespan
[5]: https://github.com/RiverArchitect/RA_wiki/ModifyTerrain
[6]: https://github.com/RiverArchitect/RA_wiki/HabitatEvaluation
[7]: https://github.com/RiverArchitect/RA_wiki/ProjectMaker
[8]: https://github.com/RiverArchitect/RA_wiki/Tools
[9]: https://github.com/RiverArchitect/RA_wiki/FAQ
[10]: https://github.com/RiverArchitect/RA_wiki/Troubleshooting

[wyrick14]: https://www.sciencedirect.com/science/article/pii/S0169555X14000099
[hecspp]: https://www.hec.usace.army.mil/software/hec-ssp/
[libreoffice]: https://www.libreoffice.org/