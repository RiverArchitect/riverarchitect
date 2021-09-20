Maximum Lifespan Assessment (MaxLifespan)
=========================================

***

- [Introduction to maxium (best) lifespan mapping](#actintro)
- [Quick GUIde to maximum lifespan maps](#actquick)
  * [Main window set-up and run](#actgui)
  * [Alternative run options](#actrun)
  * [Output](#actoutput)
    + [Geofiles](#actoutgeo)
    + [Mapping](#mapping)
  * [Quit module and logfiles](#actquit)
- [Working principle](#actprin)
- [Code modification: Add feature sets for maximum lifespan maps](#actcode)

  ***

# Introduction to maxium (best) lifespan mapping<a name="actintro"></a>

The *MaxLifespan* module serves for the GIS-based prioritization of [river restoration features](River-design-features) based on lifespan and design maps and it creates `raster`s, `shapefiles`, and `pdf`-maps. This Wiki page is structured as follows:

 - [Quick Guide](#actquick) to the application of the GUI with a description of required input (Rasters), alternative run options and output descriptions.
 - [Output and procedures for `pdf`-map generation](#actprin).
 - [Code conventions and extension possibilities](#actcode).

Maximum lifespan mapping uses lifespan maps produced with the [*LifespanDesign*][3] to identify the feature(s) with the highest lifespan for every pixel within the [predefined feature groups](River-design-features). If the maximum pixel lifespan can be obtained by several features, the *MaxLifespan* module overlays polygons indicating the best feature types. For terrain modifications, all relevant features (grading, widening/berm setback, backwater enhancement as well as side channel or side cavity creation) are equally considered. Thus, the planner has to decide and manually manipulate feature polygons which are relevant for the particular project. Regarding toolbox features, the *MaxLifespan* module evaluates plantings against wood (engineered log jams) and angular boulders (rocks) placement to increase habitat suitability and stabilize terrain modifications. The user has to decide, which plantings, wood or angular boulders (rocks) polygons are relevant to keep for the final version. Finally, the *MaxLifespan* module uses complementary feature lifespan and design maps as well as terrain slope analysis to highlight areas where gravel augmentation, the incorporation of fine sediment in the soil and bioengineering features for terrain/slope stabilization are relevant. Also in this last step, the planner needs to decide, which feature polygons to keep. However, if the analysis of complementary features identifies unstable slopes, it is strongly recommended to take action in the concerned areas.

# Quick GUIde to maximum lifespan maps<a name="actquick"></a>

***

## Main window set-up and run<a name="actgui"></a>

The *MaxLifespan* module requires lifespan and design maps (i.e., the prior run of the [*LifespanDesign*][3] module is required). Then, the *MaxLifespan* module can be launched and the following window opens up.

![mlgui](https://raw.githubusercontent.com/sschwindt/RiverArchitect/master/images/gui_start_ap.PNG)

First, the module requires the choice of a feature set from the dropdown menu. Second, a [`CONDITION`](Signposts#conditions) needs to be defined analog to the [*LifespanDesign*][3] module.

By default, the *MaxLifespan* will look up lifespan and design maps which are stored in the folder `RiverArchitect/LifespanDesign/Output/Rasters/CONDITION/`. This input directory can be modified by clicking on the `Change input directory` button. 
The *MaxLifespan* will automatically look for Raster files beginning with "`lf`" or `ds` and containing the shortname of the considered features (see shortname list in the [feature group overview](River-design-features)). Please note that Raster names that do not start with either `lf` or `ds` and/or that do not contain the complete shortname of the considered features are not recognized by *MaxLifespan*. The background image of the maximum lifespan maps also refers to lifespan and design maps and corresponds to the Raster `RiverArchitect/01_Conditions/CONDITION/back.tif`.<br/>
The mapping checkbox provides the optional creation of maps with the creation of geofiles (Rasters and shapefiles). If the checkbox is selected, running the Geofile Maker also includes the successive runs of the Layout Maker and Map Maker. It is recommended to keep this box checked (default) because maximum lifespan mapping is fully automated and the procedure is fast.\
Once all inputs are defined, click on "Run" and "Verify settings" to ensure the consistency of the chosen settings. After successful verification, the selected feature list and the verified condition change to green font.<br/>
Three "Run" options exist in the drop-down menu:

-  `Run: Geofile Maker` prepares the optimum lifespan Raster and associated feature polygons (shapefiles) in the directories `RiverArchitect/MaxLifespan/Output/Rasters/CONDITION/` and `.../Output /Shapefiles/CONDITION/`

-  `Run: Map Maker ` prepares maximum lifespan map assemblies (`pdf`s) in the directory `RiverArchitect/02_Maps/CONDITION/` ([more information on mapping](#actoutmaps)).


## Alternative run options<a name="actrun"></a>

The principal run options of the GUI call the following methods:

1.  Run: Geofile Maker calls `action_planner.geo_file_maker`

1.  Run: Map Maker calls `action_planner.map_maker`

For batch-processing of multiple scenarios, it can be useful to run the `geo_file_maker` function in a standalone script as follows:

1.  Go to *ArcGIS Pro*s Python folder and double-click one of the following:<br/>
    `C:\Program Files\ArcGIS\Pro\bin\Python\scripts\propy.bat` or<br/>
    `C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe`

1.  Enter `import os`

1.  Navigate to script directory using the command `os.chdir("ScriptDirectory")`<br/>
    Example: `os.chdir("D:/Python/RiverArchitect/MaxLifespan/")`

1.  Import the *MaxLifespan* module: `import action_planner as ap`

1.  Launch Geofile Maker: `ap.geo_file_maker(condition , feature type , ∗args)`, where `args[0]` is a boolean value for activating or deactivation of integrated PDF-mapping (default = `False`), `args[1]` is a string that indicates the unit system (either "us" or "si"; default = "us") and `args[2]` can be an alternative input path of lifespan maps than the default directory (see above)<br/>
    Example: ` ap.geo_file_maker(2008, "framework", True, "us", "D:/temp/")`<br/>
    This command calls the Geofile Maker for the condition "2008" for framework features, with activated mapping, U.S. customary units and it sets the Raster input path to `D:/temp/`.
    

## Output<a name="actoutput"></a>
***
### Geofiles<a name="actoutgeo"></a>

The principal output of the module's Geofile Maker is one Raster called `max_lf` (stored in `.../MaxLifespan/Output/Rasters/CONDITION/`) and one shapefile per analyzed feature containing polygons of the feature's best performing areas (stored in `.../MaxLifespan/Output/Shapefiles/CONDITION/`). Moreover, the module produces Rasters with names corresponding to the lifespan/design Raster names and feature shortnames, which essentially contain the same information as the feature shapefiles. These Raster files are side products from the production of the feature shapefiles.

### Mapping<a name="actoutmaps"></a>

The `Map Maker` uses predefined layout templates to overlay

-   a background Raster (`RiverArchitect/01_Conditions/CONDITION/back.tif`),

-   the best lifespan Raster (`/MaxLifespan/Output/Rasters/CONDITION/max_lf.tif`), and

-   shapefiles of best-performing feature areas (`/MaxLifespan/Output/Shapefiles/CONDITION/lf_feat...` or `ds_feat...`).

The module enforces overwriting of existing Raster and shapefiles in the output folder (`/MaxLifespan/Output/`) and it tries to delete any existing content.
Before running `Map Maker`, the layout templates are stored in `RiverArchitect/02_Maps/templates/river_template.aprx` and they are named after the feature set type. The [mapping wiki pages](Mapping#standard-layouts) provide a list of layout names and explain possibilities for modifying the symbology, legend, or map extents. After running `Map Maker`, the map project file and `PDF`s are stored in `RiverArchitect/02_Maps/CONDITION/map_CONDITION_design.aprx`. Anew modifications should be made within this project file (`.aprx`), which is not overwritten, if *River Architect* identifies an existing `CONDITION`-project file.


## Quit module and logfiles<a name="actquit"></a>

The GUI can be closed via the `Close` dropdown menu if no background processes are going on (see terminal messages). The GUI flashes and rings a system bell when it completed a run task. If layout creation and/or mapping were successfully applied, the target folder automatically opens. After execution of either run task, the GUI disables functionalities, which would overwrite the results and it changes button functionality to open logfiles and quit the program. Logfiles are stored in the `RiverArchitect/MaxLifespan/` folder and named `logfile.log`. Logfiles from previous runs are overwritten.

# Working principle<a name="actprin"></a>
***
The Geofile Maker uses the `CellStatistics` (with "Max" argument) command of `arcpy`'s Spatial Analyst toolbox to identify the best lifespans of features. In the case of features where only design Rasters are available (i.e., Raster units are either on/off (1/0) or dimensional indicators, for example, minimum grain sizes), the Geofile Maker converts any non-zero value of the design Raster to 0.8. The value of 0.8 is an arbitrarily chosen identifier with the hypothetical unit of years, where the only importance is that this identifier is larger than zero and smaller than 0.9. Thus, the identifier is smaller than any lifespan value and the `CellStatistics`'s "Max" corresponds to the lifespan value when lifespan Rasters are compared with design Rasters. In other words, the Geofile Maker prioritizes lifespan Rasters over design Rasters. This choice was made because the data quality of lifespan Rasters is better (higher data abundance) than the quality of design Rasters, considering that the data quality is a function of available layers (DEM, morphological unit, grain size, hydraulic Rasters, etc.). Therefore, pixels where no lifespan value but a design value is available to get assigned a value of 0.8. Finally, the 0.8-pixels are converted to the highest defined lifespan (see [*LifespanDesign*][3] module) based on the assumption that if the feature is constructed corresponding to the design criteria, its lifespan will be high. Note the difference: lifespan values are prioritized because of the better data quality and the *max*-years-value of design Raster-only pixels applies to a chain of safe constructive assumptions potentially resulting in high costs.<br/>
Recall that [`Other bioengineering` features](River-design-features#bioeng) can take three values: (1) `max` years, if the terrain slope is greater than defined in the thresholds workbook and the depth to groundwater is lower than defined in the thresholds workbook (cf. [*LifespanDesign*][3]); (2) `1.0` year, if the terrain slope is greater than defined in the thresholds workbook and the depth to groundwater is greater than defined in the thresholds workbook; (3) `NoData`, if the terrain slope is lower than defined in the thresholds workbook. Thus, where maximum lifespan maps indicate a 1.0-year lifespan, bioengineering features that are independent of the depth to the groundwater table are required. Such features typically imply the placement of angular boulders.

***
# Code modification: Add feature sets for maximum lifespan maps<a name="actcode"></a>

The comprehensive *MaxLifespan* module provides flexibility regarding input directories, layout modifications and mapping extents without modifications of the code. However, modifications of the [feature sets (framework, toolbox and complementary)](River-design-features) require code modifications. The relevant python classes are in the file `cFeatureActions.py`, notably  `class FrameworkFeatures(Director)`, `class ToolboxFeatures(Director)` and `class ComplementaryFeatures(Director)`. These classes all inherit from the `Director` class which identifies and assigns lifespan and design Rasters in the input folder. The following code example indicates where single features can be added or removed from feature sets. It is a generalized code sample where ["Framework"](River-design-features#featoverview), ["Plants"](River-design-features#plants), ["Other Bioengineering"](River-design-features#bioeng) and ["Longitudinal connectivity"](River-design-features#featoverview) are replaced with "TYPE". The feature `FullName_i` and `shortname_i` must comply with the [feature terminology](River-design-features#featoverview) because also the *MaxLifespan* module uses the centralized feature identifier class that is stored in `RiverArchitect/ModifyTerrain/cDefinitions.py`.

```python
class TYPEFeatures(Director):
    # This class stores all information about TYPE features
    def __init__(self, condition, *args):
        try:
            ## check if args[0] = alternative input path exists
            Director.__init__(self, condition, args[0])
        except:
            Director.__init__(self, condition)
        self.names = ["FullName_1", "FullName_2", ..., "FullName_n"] #--CHANGE HERE
        self.shortnames = ["shortname_1", "shortname_2", ..., "shortname_n"] #--CHANGE HERE
        self.ds_rasters = self.append_ds_rasters(self.shortnames)
        self.lf_rasters = self.append_lf_rasters(self.shortnames)

```

In addition, the `choose_ref_layout(self, feature_type)` function of the `Mapper` class in `RiverArchitext/.site_packages/riverpy/cMapper.py` needs to be updated:

```python
  def choose_ref_layout(self, map_name):
        # type(map_name) == str
        map_name = str(map_name)
        if "lf" in map_name:
            if not ("mlf" in map_name):
                return "layout_lf"
            else:
                if "bio" in map_name.lower():
                    return "layout_mlf_bioeng"
                if "maint" in map_name.lower():
                    return "layout_mlf_maintenance"
                if "plant" in map_name.lower():
                    return "layout_mlf_plants"
                if "terra" in map_name.lower():
                    return "layout_mlf_terraforming"
    ...

```

Moreover, the `choose_ref_map(self, feature_type)` function of the `Mapper` class in `RiverArchitext/.site_packages/riverpy/cMapper.py` needs to be updated:

```python
  def choose_ref_layout(self, map_name):
        # type(map_name) == str
        map_name = str(map_name)
                if "lf" in map_name:
            if not ("mlf" in map_name):
                return "layer_lf"
            else:
                if "bio" in map_name.lower():
                    return "layer_mlf_bioeng"
                if "maint" in map_name.lower():
                    return "layer_mlf_maintenance"
                if "plant" in map_name.lower():
                    return "layer_mlf_plants"
                if "terra" in map_name.lower():
                    return "layer_mlf_terraforming"
    ...

```

This also requires the creation of the layout and layer in `RiverArchitect/02_Maps/templates/river_template.aprx` and/or `RiverArchitect/02_Maps/CONDITION/map_CONDITION_design.aprx`.

[1]: https://github.com/RiverArchitect/RA_wiki/Installation
[2]: https://github.com/RiverArchitect/RA_wiki/Signposts
[3]: https://github.com/RiverArchitect/RA_wiki/LifespanDesign
[4]: https://github.com/RiverArchitect/RA_wiki/MaxLifespan
[5]: https://github.com/RiverArchitect/RA_wiki/ModifyTerrain
[6]: https://github.com/RiverArchitect/RA_wiki/SHArC
[7]: https://github.com/RiverArchitect/RA_wiki/ProjectMaker
[8]: https://github.com/RiverArchitect/RA_wiki/Tools
[9]: https://github.com/RiverArchitect/RA_wiki/FAQ
[10]: https://github.com/RiverArchitect/RA_wiki/Troubleshooting