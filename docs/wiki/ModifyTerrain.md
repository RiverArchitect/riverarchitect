Modify Terrain (terraforming) 
======================================

***

- [Introduction to the ModifyTerrain module](#mtintro)
- [Quick GUIde to terrain modifications](#mtquick)
- [Threshold value-based terraforming (widening and grading)](#mtdemmod)
  * [Run](#mtrun)
  * [Alternative run options](#mtaltrun)
  * [Output](#mtoutput)
  * [Working principles](#mtprin)
  * [Code modification](#mtcode)
- [River Builder](RiverBuilder)

***

# Introduction<a name="mtintro"></a>

The *ModifyTerrain* module can (re)model existing terrain DEMs based on threshold values or using the [River Builder](RiverBuilder) [R](https://www.r-project.org/) package.
Threshold value-based terraforming uses DEMs of existing rivers and applies either  [widening (berm setback)](https://github.com/RiverArchitect/RA_wiki/River-design-features#berms) or [grading](https://github.com/RiverArchitect/RA_wiki/River-design-features#grading), primarily to enable plant survival (for [phreatophytes](https://en.wikipedia.org/wiki/Phreatophyte)). While the input DEMs are not necessarily required to be part of a *River Architect* [*Condition*](Signposts#conditions), the definition of [*Condition*](Signposts#conditions)s is still required because the module uses maximum lifespan maps and depth to groundwater Rasters to identify candidate pixels for terraforming.

# Quick GUIde to terrain modifications<a name="mtquick"></a>

***

## Main window set-up and run<a name="mtgui"></a>

The GUI start-up takes a couple of seconds because the module updates reach information from a spreadsheet until the following window opens.

![mtgui](https://github.com/RiverArchitect/Media/raw/master/images/gui_start_mt.PNG)

To start with the *ModifyTerrain* module, first a feature set must be chosen from the drop-down menu, which is currently limited to ["Widen"](River-design-features#berms) and ["Grading"](River-design-features#grading). Second, a [*Condition*](Signposts#conditions) needs to be entered, which requires a click on the `Verify` button to update the GUI. This behavior differs from the [*LifespanDesign*][3] and [*MaxLifespan*][4] modules and an ample revision of the *ModifyTerrain* module will align to the lifespan modules in the future.

## Input: Set Reaches<a name="mtsetreaches"></a>
This module enables analysis for specific [river reaches](RiverReaches), which can be renamed and the reach extents can be modified. The module analyzes all reaches which are defined in a spreadsheet stored in
`ModifyTerrain/.templates/computation_extents.xlsx`. For omitting the reach fragmentation, select `IGNORE` from the `Reaches` drop-down menu.

## Input: Set Condition<a name="mtinp"></a>

For terrain modifications, the module requires an input topo (DEM), which it looks up in the `RiverArchitect/LifespanDesign/Input/CONDITION/` directory by default. The input directory can be modified by clicking on the "Change input DEM directory (optional)" button. Note that the input folder needs to contain a *GeoTIFF* DEM Raster with the name `dem`; other Raster names are not recognized and the input `dem` is crucial for any operation of the module.

# Threshold value-based terraforming: Widening and Grading options<a name="mtdemmod"></a>

The ["Widen"](River-design-features#berms) and ["Grading"](River-design-features#grading) features use the maximum required distance to the groundwater table, which is admissible for plantings. These threshold values are defined in the [*LifespanDesign*][3] module's workbook `RiverArchitect/LifespanDesign/Input/.templates/threshold_values.xlsx`. The prior run of the [*MaxLifespan*][4] module is required to enable *ModifyTerrain* reading Rasters containing the keywords `grade` or `widen` from the folder `RiverArchitect/MaxLifespan/Output/Rasters/CONDITION/`. Moreover, a depth to groundwater table Raster (*GeoTIFF* format) with the name [`d2w.tif`](Signposts#make-depth-to-groundwater-rasters) is required in the directory `RiverArchitect/01_Conditions/CONDITION/` (use the [Get Started](Signposts#getstarted)'s [`Populate Condition`](Signposts#pop-condition) function to create a depth to the groundwater Raster).<br/>
The directory of maximum lifespan and depth to groundwater Rasters can be modified by clicking on the `Change feature max. lifespan Raster directory (optional)` button. This directory needs to contain *GeoTIFF*-Rasters, which have the keywords `grade` or `widen` in their filename.

***


## Run<a name="mtrun"></a>

All run options in the `Run` dropdown menu enables the `Threshold-based DEM modification` when `Reaches`, `Features`, and a `CONDITION` were defined.

***

## Alternative run options<a name="mtaltrun"></a>
The *ModifyTerrain* module has no standalone statement and it is recommended to use the GUI for launching the modules routines. If needed, the module can alternatively be imported and used as python package as follows:

1.  Go to *ArcGIS Pro*s Python folder and double-click one of the following:<br/>
    `C:\Program Files\ArcGIS\Pro\bin\Python\scripts\propy.bat` or<br/>
    `C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe`
2.  Enter `import os`
1.  Navigate to Script direction using the command `os.chdir("ScriptDirectory")`<br/>
    Example: `os.chdir("D:/Python/RiverArchitect/ModifyTerrain/")`
4.  Import the module: `import cModifyTerrain as cmt`
1.  Instantiate a *ModifyTerrain* object:<br/>
	`mt = cmt.ModifyTerrain(condition , unit_system, feature_ids , topo_in_dir , feat_in_dir , reach_ids)`<br/>
    `unit_system` must be either "us" or "si"<br/>
    `feature_ids` is a list of [features shortnames](https://github.com/RiverArchitect/RA_wiki/River-design-features#introduction-and-feature-groups)<br/>
    `topo_in_dir` is an input directory for DEM and depth to groundwater table Rasters<br/>
    `feat_in_dir` is an input directory for feature max. lifespan Rasters; for custom DEMs `feat_in_dir` can be a dummy directory<br/>
    `reach_ids` is a list of reach names to limit the analysis
6.  The DEM Modification is launched by calling the *ModifyTerrain* object that outputs the calculation logfile with volume change information: `logfile = mt()`
8.  The analysis is limited to running the Volume Calculator when the *ModifyTerrain* object is called with arguments: `logfile = mt(True, path_to_modified_DEM)`

***

## Raster Output<a name="mtoutput"></a>

The module creates Rasters of modified DEMs and terrain difference Rasters for grading and/or widen features in the directory `ModifyTerrain/Output/Rasters/CONDITION/`). Raster names contain a reach identifier (`r00`, `r01`, \... `r07` corresponding to spreadsheet rows 6--13), part of the [features shortnames](River-design-features#introduction-and-feature-groups). In addition, terrain **d**ifference Raster, `"d"` with either `"neg"` for excavation or `"pos"` for fill.

## Mapping<a name="mtmap"></a>

Please note that automated mapping is currently deactivated for the *ModifyTerrain* module. For mapping graded or widened terrain, use the <a href="VolumeAssessment">VolumeAssessment</a> module and link the *ModifyTerrain* output Rasters to the *ArcGIS Pro* project file `RiverArchitect/02_Maps/CONDITION/map_CONDITION_design.aprx`. The relevant layout names for the *ModifyTerrain* module are:

 - `volumes_grade_neg` for mapping the terrain differences of parametrically (threshold-based) floodplain [grading](https://github.com/RiverArchitect/RA_wiki/River-design-features#grading) within the <a href="ModifyTerrain">Modify Terrain</a> module (only excavation `neg` is meaningful)
 - `volumes_widen_neg` for mapping the terrain differences of parametrically (threshold-based) river [widening](https://github.com/RiverArchitect/RA_wiki/River-design-features#berms) within the <a href="ModifyTerrain">Modify Terrain</a> module (only excavation `neg` is meaningful)

## Working principles<a name="mtprin"></a>

The module can lower the terrain for grading and/or widen features to make relevant areas adequate for plantings. It looks up the maximum possible depth to groundwater for the considered planting types in `RiverArchitect/LifespanDesign/Input/.templates/threshold_values.xlsx`, cells `J6:M6`. The required lowering *dz* results from the minimum depth
to groundwater value of the latter cells:<br/>
`required_d2w = min([plant1.threshold_d2w_up, plant2.threshold_d2w_up, plant3.threshold_d2w_up, plant4.threshold_d2w_up])`<br/>
The `condition` DEM (`act_dem`) is lowered using the `arcpy`'s spatial analyst:<br/>
`new_dem = Con((d2w > required_d2w), Float(act_dem - (d2w - required_d2w)), act_dem)`



## Code modification: Add routines for automated DEM modification<a name="mtcode"></a>

Other routines for the automated generation of modified terrains can be added as follows:

 - Create new function in the `ModifyTerrain` class (file `ModifyTerrain/cModifyTerrain.py`), which contains routines for creating a new DEM, for example:

```python
  def create_new_dem(self, feat_id, extents):
    self.logger.info("") 
    feature_name = self.features.feat_name_dict[feat_id]
    self.logger.info("* *   * *   * * " + feature_name.capitalize() + " * *   * *  * *")
    # set arcpy env
    arcpy.gp.overwriteOutput = True
    arcpy.env.workspace = self.cache
    if not (type(extents) == str):
      try:
        # XMin, YMin, XMax, YMax
        arcpy.env.extent = arcpy.Extent(extents[0], extents[1], extents[2], extents[3])
      except:
        self.logger.info("ERROR: Failed to set reach extents.")
        return (-1)
    else:
      arcpy.env.extent = extents
    # arcpy.CheckOutExtension('Spatial')  # check out license if needed
	
    # get feature maximum lifespan raster (or any other input raster):
    feat_act_ras = self.get_action_raster(feat_id)
    # set NoData values to 0:
    feat_ras_cor = Con(IsNull(feat_act_ras), self.null_ras, feat_act_ras)
    self.logger.info("  >> Calculating DEM after terrain " + feature_name + " ... ")
	
    # assign a dem for modification (see descriptions below)
    if self.raster_info.__len__() > 0 and not ("diff" in self.raster_info):
      # use modified DEM if there was a prior automated modification
      self.logger.info("   ... based on " + str(self.raster_info) + "-DEM  ... ")
      dem = self.raster_dict[self.raster_info]
      ...add other required Rasters
    else:
      # use condition DEM if there was no prior raster modification 
      dem = self.ras_dem
      ...add other required Rasters
	
    # IMPLEMENT FORMULAE HERE
    new_dem = ...some function...
    # calculated difference DEM for volume calculation
    new_dem_diff_neg = ...
    new_dem_diff_pos = ...
	
    # update class dictionaries (communicate modifications)
    self.raster_dict.update({feat_id[0:3] + "_diffneg": new_dem_diff_neg})
    self.raster_dict.update({feat_id[0:3] + "_diffpos": new_dem_diff_pos})
    self.raster_info = feat_id[0:3]
    self.raster_dict.update({self.raster_info: new_dem})
	
    # arcpy.CheckInExtension('Spatial')  # release license if necessary	
```


Note:

     +  The `self , feat_id , extents` arguments are required for the implementation in the call-routine, where is a [features shortnames](River-design-features#introduction-and-feature-groups) `extent` and is an `arcpy.Extent` variable that limits DEM creation to this extent.

     +  `self.logger.info()` sends messages to the logger, which are also printed on the *Python* terminal.

     +  `dem = self.raster_dict[self.raster_info]` uses the latest DEM version; this is the `condition` DEM if no other terrain modification was applied before. Otherwise, for example if "grading" was used for the automated terrain modification before this function is used, `dem = self.raster_dict[self.raster_info]` points to the terrain DEM after grading.

 - Implement the new function in the modification manager:

```python
  def modification_manager(self, feat_id):
    if not(self.reach_delineation):
      extents = "MAXOF"
    else:
      try:
        extents = self.reader.get_reach_coordinates(self.reaches.dict_id_int_id[self.current_reach_id])
      except:
        extents = "MAXOF"
        self.logger.info("ERROR: Reach delineation recognized but not identifiable in input
      # START CHANGES FROM HERE ON
      if ("grad" in feat_id) or ("wide" in feat_id):
        self.lower_dem_for_plants(feat_id, extents)
      if ("feature_shortname" in feat_id):
        self.create_new_dem(feat_id, extents)

```

 - Save edits

 - The adapted code can now be executed using the [alternative run options](#mtaltrun), where `feature_ids = ["shortname of new feature"]`.<br/>
    *Hint:* The new method can also be implemented in the GUI by adding `self.featmenu.add_command(label="New Feature", command=lambda: self.define_feature("new ID")` to `def __init__(...)` of the `FaGui()` class in the file `modify_terrain_gui.py`. This requires adding an `if not(feature_id == "new ID"): ... else: ...` statement in the `self.define_feature` function according to the function environment.

***

# River Builder
[Continue reading on *River Builder*'s own Wiki page](RiverBuilder).

[1]: https://github.com/RiverArchitect/RA_wiki/Installation
[2]: https://github.com/RiverArchitect/RA_wiki/Signposts
[3]: https://github.com/RiverArchitect/RA_wiki/LifespanDesign
[4]: https://github.com/RiverArchitect/RA_wiki/MaxLifespan
[5]: https://github.com/RiverArchitect/RA_wiki/ModifyTerrain
[6]: https://github.com/RiverArchitect/RA_wiki/SHArC
[7]: https://github.com/RiverArchitect/RA_wiki/ProjectMaker
[8]: https://github.com/RiverArchitect/RA_wiki/Tools
[9]: https://github.com/RiverArchitect/RA_wiki/FAQ