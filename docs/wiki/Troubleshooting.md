Error messages and Troubleshooting
==================================

***

# Known issues<a name="issues"></a>
We do our very best to program *River Architect* as robust and flexible as possible. *River Architect*'s stepwise development nevertheless led to a few restrictions in its freedom of use, which are caused by a couple of hard-code sequences. The following limitations because of hard-coding are known and will be fixed in future versions:

 - <a href="SHArC">SHArC</a>: Physical Habitats / fish lifestages must be named either `spawning, fry, ammocoetes, juvenile, adult, hydrologic year, season, depth > x, ` or `velocity > x`. The [lifestage names](SHArC#hefish) are currently hard-coded in the `Fish` class (`RiverArchitect/.site_packages/riverpy/cFish.py`) dictionary `self.ls_col_add = {"spawning": 1, "fry": 3, "ammocoetes": 3, "juvenile": 5, "adult": 7, "hydrologic year": 1, "season": 3, "depth > x": 5, "velocity > x": 7}`. This dictionary can be changed for using other lifestage names and we are working on an improvement in later versions. *Note: This dictionary defines the relative column numbers that is added to the column where a fish name is defined.*
 - **ArcGIS Pro 2.4** `Exception Error: (arcpy) - expected 1 arguments, got 2` <br/>
   The latest version of *ArcGIS Pro 2.4* may cause problems when *RiverArchitect* calls the conda environment. <br/> Remedy (1): Use `"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"` instead of `"%PROGRAMFILES%\ArcGIS\Pro\bin\Python\Scripts\propy"` in the `RiverArchitect/Start_River_Architect.bat` ([see context in the installation instructions](Installation#started)). <br/> Remedy (2): In *ArcGIS Pro*, go to *Settings* (bottom left), then *Python*, click on *Manage Environments* and *Clone Default*. Check the clone (`arcgispro-py3-clone`) and close *ArcGIS Pro*.
- **Maximum data size (*River Architect*'s Lifespan & Design mapping hangs without prompting any message)**: *River Architect*'s data processing competence depends on the available Random-Access Memory (RAM). As a general rule, the maximum amount of data should be smaller than the available RAM. The size of processed data can be approximated as:<br/>RAM >= *Single Raster size* · *Number of features* · *Number of parameters per feature* · *Number of discharges*<br/>The data size limit applies to lifespan mapping only, where *River Architect* loads nearby all available data in the `01_Conditions/CONDITION/` folder for each selected feature to run [`arcpy.sa.CellStatistics`](https://pro.arcgis.com/en/pro-app/tool-reference/spatial-analyst/cell-statistics.htm). To avoid issues, consider the following rules of thumb:
	 * Limit the project area to reasonable extents (single Raster size <= 350 MB). 
	 * Limit the number of discharges to less than 10 (set relevant discharges defined in rows 4, 11, and 12 of [*input files*](Signposts#inpfile) to less than 10); manual modification of automatically generated input files may be required (rows 4, 11, and 12 of `01_Conditions/CONDITION/input_definitions.inp`).
	 * Analyze only one feature at a time rather than feature groups (such as "Plantings"). In this case, the single Raster size may be up to 1 GB.
- **Grain size raster name coherence**: The `LifespanDesign` module will read grain size raster names from `01_Conditions/CONDITION/input_definitions.inp`. However, the `Ecohydraulics` module absolutely requires that a grain size raster in SI units is named `dmean.tif` (units: meters) and a grain size raster in U.S. customary units must be named `dmean_ft.tif` (units: feet).
- **PDF maps export of lifespan** maps fails under some circumstances ([read more in the error message](#pdfexp)).



# How to trace Error and Warning messages<a name="howto"></a>
If *River Architect* encounters problems, the code writes *WARNING* and *ERROR* messages to the *Python* command line and to the same logfile where all other computation progress information is logged. The *WARNING* and *ERROR* messages provide information on the error cause and this Wiki contains all possible *WARNING* and *ERROR* messages of *River Architect*.

Thus, for troubleshooting, press the `CTRL` + `F` key, enter (part of) the *WARNING* or *ERROR* message that occurred, and press enter. *Causes* and *Remedies* are provided for every *WARNING* and *ERROR* message. Do not include specific parameters, file names, or expressions in parentheses or brackets.

Otherwise, the *WARNING* and *ERROR* messages are listed in alphabetic order (starting with **E**rror messages, then **E**xceptionalError message, then **W**arning messages ...).


# Error and Warning message generation

Most errors occur when the wrong python interpreter is used or when Rasters or layouts have bad formats or when the information stated in the [input files](Signposts#inpfile) is erroneous.
The *River Architect* writes process errors and descriptions to logfiles. When the GUI encounters problems, it directly provides causes and remedies in pop-up infoboxes. The common error and warning messages, which can be particularly raised by the package (alphabetical order) are listed in the following with detailed descriptions of causes and remedies. Most error messages are written to the logfiles, but some exception errors are only printed to the terminal because they occur before logging could even be started. Such non-logged `ExceptionErrors` are listed at the bottom of the Error messages.
Some non-identifiable errors raised by the `arcpy` package disappear after rebooting the system.

***

Error messages
==============

 - **`arcpy ERROR 130051: Input feature class is not registered as versioned.`**
    - *Cause:*   `arcpy` failed to register datasets, which basically means that the dataset does not exist. Moreover, this arbitrary error may occur if, for example, multiple [subsets of a *Condition*](Signposts#sub-condition) were created without closing *River Architect* between each creation.
    - *Remedy:*
        + Make sure that the dataset exists (read error message information).
        + [GetStarted](Signposts): When creating *Condition*s, ensure to restart River Architect after every single creation of a *Condition* or *Condition* subset. This issue is related to `arcpy`, which will not [register datasets](https://pro.arcgis.com/en/pro-app/help/data/geodatabases/overview/a-quick-tour-of-registering-and-unregistering-data-as-versioned.htm) unless *River Architect* is completely closed. We are developing work-arounds.
        + <a href="ProjectMaker">ProjectMaker</a>: Ensure that the project polygon and the selected habitat condition (from <a href="SHArC">SHArC</a>) overlap (otherwise, the intersecting dataset is empty).

- **`ERROR 000641: Too few records for analysis.`**
    - *Cause:*   This  `arcpy` error message occurs here when `arcpy.CalculateGeometryAttributes_management` tries to compute the area of an empty shapefile.
    - *Remedy:*  If this error occurs within the calculation of SHArea (Seasonal Habitat Area) calculations, it may be ignored because some discharges do not provide any usable habitat area for a target fish species within a defined project area. Otherwise, traceback files and check the shapefile consistency.

- **`ERROR 999998: Unexpected Error.`** This is an operating system error and it can indicate different error conditions (i.e., the real reasons may have various error sources). Some of the most probable causes are:

    - *Cause:*   Usage of the wrong python interpreter
    - *Remedy:*
        + Make sure to use the correct *Python* environment ([see installation guide](Installation#install-and-get-started))
        + Make sure that all input Rasters are in *GeoTIFF* format and well placed in the folder `RiverArchitect/01_Conditions/CONDITION/`.
        + Rebooting the system can help in some cases.

- **`ERROR: .cache folder in use.`**
    - *Cause:*   The content in the cache folder is blocked by another software and the output is probably affected.
    - *Remedy:*  Close the software that blocks `.cache`, including `explorer.exe`, other instances of `python` or *ArcGIS* and rerun the code. Also re-logging may be required if the folder cannot be unlocked.

- **`ERROR: .cache folder will be removed by package controls.`**
    - *Cause:*   `arcpy` could not clean up the `.cache` folder and the task is passed to *Python*'s`os` package. The content in the cache folder is blocked by another process and the output is probably affected.
    - *Remedy:*  Close the software that blocks `.cache`, including `explorer.exe`, other instances of *Python* or *ArcGIS* and rerun the code. Also re-logging may be required if the folder cannot be unlocked.

 - **`ERROR: (arcpy) in *PAR*.`**
    - *Cause:*   Similar to`ExceptionERROR: (arcpy) ...`. The error is raised by the `analysis_...`, `design_...` and other functions when `arcpy` Raster calculations could not be performed. Missing Rasters, bad Raster assignments, errors in input geodata files, or bad Raster calculation expressions are possible reasons. The error can also occur when the `SpatialAnalyst` license is not available.
    - *Remedy:*  See `ExceptionERROR: (arcpy) ...`


 - **`ERROR: Analysis stopped ([...] failed).`**
    - *Cause:*   Raised by `analysis(...)` function in `LifespanDesign/feature_analysis.py` when it encountered an error.
    - *Remedy:*  Trace back the error message in brackets. If a results Raster could not be saved, it means that the analyzed feature has no application, i.e., the results Raster is empty, and therefore, it cannot be saved.

 - **`ERROR: Area calculation failed.`**
    - *Cause:*   Raised by `calculate_sha(self)` of [*SHArC*][6]'s `CHSI()` class in `SHArC/cHSI.py` when it could not calculate the usable habitat area (see [SHArea Methods](SHArC#herunaua)).
    - *Remedy:*
        + Ensure that the SHArea threshold has a meaningful value between 0.0 and 1.0 ([SHArC Intro](SHArC)).
        + Ensure that neither the directory `SHArC/.cache/` nor the directory `SHArC/SHArea/` or their contents are in use by other program.
        + Review the input settings according to the [SHArC Quick GUIde](SHArC#hegui).
        + Follow up earlier error messages.

 - **`ERROR: Bad assignment of x/y values in the coordinate input file.`**
    - *Cause:*   Raised by the `coordinates_read(self)` function of the `Info()` class in either `LifespanDesign/cRead InpLifespan.py` or `MaxLifespan/cReadActionInput.py` when `mapping.inp` has bad assignments of *x*-*y* coordinates.
    - *Remedy:*  Ensure that the coordinate definitions in `mapping.inp` (`LifespanDesign/.templates/` or `MaxLifespan/.templates/`) correspond to the definitions in [*LifespanDesign* Output maps](LifespanDesign#outmaps).

 - **`ERROR: Bad call of map centre coordinates. Creating squared-x layouts.`**
    - *Cause:*   Raised by `get_map_extent(self, direction)` function of the `Info()` class in either `LifespanDesign/cReadInpLifespan.py` or `MaxLifespan/cReadActionInput.py` when `mapping.inp` has bad assignments of *x*-*y* coordinates.
    - *Remedy:*
        + [*LifespanDesign*][3]: Ensure that the file `mapping.inp` exists in the directory `LifespanDesign/.templates/` corresponding to the definitions in [*LifespanDesign* Output maps](LifespanDesign#outmaps).
        + [*MaxLifespan*][4]: Ensure that the file `mapping.inp` exists in the directory `MaxLifespan/.templates/` corresponding to the definitions in [*LifespanDesign* Output maps](LifespanDesign#outmaps).
        + General: Replace `mapping.inp` with the original file and re-apply modifications strictly following [*LifespanDesign* Output maps](LifespanDesign#outmaps).

 - **`ERROR: Bad mapping input file.`**
    - *Cause:*   Raised by either`get_map_extent(self, direction)`,`coordinates_read(self)` or`get_map_scale(self)` function of the `Info()` class in either `LifespanDesign/cReadInpLifespan.py` or `MaxLifespan/cReadActionInput.py` when `mapping.inp` has wrong formats or it is missing.
    - *Remedy:*  See `ERROR: Bad call of map centre coordinates [...]`.
    
 - **`ERROR: MU calculation failed.`**
    - *Cause:*   Error raised by the `MU` class (`GetStarted/cMorphUnits.py`) when the defined flow depth and/or velocity Rasters are not usable.
    - *Remedy:*
        + Ensure that no other program uses the selected in flow depth and velocity Rasters, and *Condition* folder.
        + Manually / visually verify the consistency of the provided input Rasters (*Float* - type).
        + See also next error message (*Baseflow MU update failed.*)
    
 - **`ERROR: MU update failed.`**
    - *Cause:*   Error raised by the `MU` class (`GetStarted/cMorphUnits.py`) when processing the provided flow depth and/or velocity Rasters lead to non-meaningful results.
    - *Remedy:*
        + Ensure that the flow depth and velocity Rasters have consistent units.
        + ISSUE: The current code uses U.S. customary units for MU delineation according to [Wyrick and Pasternack (2014)](https://www.sciencedirect.com/science/article/pii/S0169555X14000099). If required, manual changes of the delineation functions can be made in `GetStarted/cMorphUnits.py` (`calculate_mu_baseflow` function approximately from line 75 onward). We are working on improving the Morphological Unit generator.

 - **`ERROR: Boundary shapefile in arcpy.PolygonToRaster[...].`**
    - *Cause:*   Raised the SHArC module's `make_boundary_ras(self, shapefile)` function (`cHSI.py`) when it could not convert a provided shapefile defining calculation boundaries to a Raster and load it as `arcpy.Raster(.../SHArC/HSI/CONDITION/bound_ras)`.
    - *Remedy:*  Verify that a the selected boundary shapefile ([SHArC computation boundaries](SHArC#hebound)) has a valid rectangle and an `Id` field value of `1` for that rectangle.

 - **`ERROR: Boundary shapefile provided but [...].`**
    - *Cause:*   Raised the SHArC module's`make_chsi(self, fish, boundary_shp)` function (`cHSI.py`) when the "To Raster" conversion of the provided shapefile defining calculation boundaries failed.
    - *Remedy:*  See `ERROR: Boundary shapefile in arcpy.PolygonToRaster[...]`.

 - **`ERROR: Calculation of cell statistics failed.`**
    - *Cause:*   Raised by `identify_best_features(self)` of [*MaxLifespan*][4]'s `ArcpyContainer()` class in `MaxLifespan/cActionAssessment.py` when `arcpy.sa.CellStatistics()` could not be executed.
    - *Remedy:*
        + The latest feature added to the internal best lifespan Raster may contain inconsistent data. Manually load the last feature Raster (the logfile tells the feature name) into *ArcGIS Pro* and trace back the error. If needed, re-run lifespan/design Raster Maker.
        + In the case that the error occurs already with the first feature added, the [*MaxLifespan*][4]'s `zero` Raster may be corrupted. The remedy described for the error message `ExceptionERROR: Unable to create ZERO Raster. Manual intervention required* can be used to manually re-create the `zero` Raster.

 - **`ERROR: Calculation of volume from RASTER failed.`**
    - *Cause:*   The `volume_computation(self)` function of the `VolumeAssessment()` class in `VolumeAssessment/cVolumeAssessment.py` raises this error when the command `arcpy.SurfaceVolume_3d(RASTER, "", "ABOVE", 0.0, 1.0)` failed.
    - *Remedy:*
        + Ensure that an *ArcGIS* `3D` extension license is available.
        + Ensure that the modified DEM Rasters contain valid data and are not used in any other application.

 - **`ERROR: Cannot find FEAT max. lifespan Raster.`**
    - *Cause:*   The automated terrain modification with grading and/or widen features uses max. lifespan Rasters (maps) to identify relevant areas. If The `get_action_Raster(self, feature_name)` function of the `ModifyTerrain()` class in `ModifyTerrain/cModifyTerrain.py` cannot find max. lifespan Rasters in the defined max. lifespan Raster directory (default: `MaxLifespan/Output/Rasters/CONDITION/`), it raises this error message.
    - *Remedy:*  Ensure that grading and/or widen max. lifespan Rasters exist in the defined input folder (default `MaxLifespan/Output/Rasters/CONDITION/`) and that the names of the Rasters contain the feature shortname (i.e., `grade` and/or `widen`).

 - **`ERROR: Cannot find flow depth Raster.`**
    - *Cause:*   Raised by `make_chsi(self, fish, boundary_shp)` of the [*SHArC*][6]'s `CHSI()` class in `SHArC/cHSI.py` when it could associate a flow depth Raster based on the name of a habitat suitability index (HSI) Raster name.
    - *Remedy:*
        + Ensure that the flow depth Raster names in `RiverArchitect/01_Conditions/CONDITION/` strictly comply with the naming conventions described in the [Conditions / Input Rasters section](Signposts#conditions).
        + Ensure that the HSI Rasters are stored in `.../SHArC/HSI/CONDITION/`, with the correct Raster names including information about the discharge (see the [SHArC output section](SHArC#heoutput)).

 - **`ERROR: Cannot load modified DEM.`**
    - *Cause:*   The volume difference calculation and mapping of a (CAD-) modified DEM Rasters failed because the `__init__(self, ...)` function of the `VolumeAssessment()` class in `VolumeAssessment/cVolumeAssessment.py` cannot access the Raster.
    - *Remedy:*  Ensure that the selected (CAD-) modified DEM Raster exists and that it is not opened in any other program (close *ArcGIS Pro* / *QGIS*).

 - **`ERROR: Cannot load original DEM.`**
    - *Cause:*   The volume difference calculation and mapping of the selected DEM Rasters failed because the `__init__(self, ...)` function of the `VolumeAssessment()` class in `VolumeAssessment/cVolumeAssessment.py` cannot access the Raster.
    - *Remedy:*  Ensure that the selected DEM Raster exists and that it is not opened in any other program (close *ArcGIS Pro* / *QGIS*).
    
- **`ERROR: Cannot open project: DIR/module_name.aprx.`**
    - *Cause:*   Mapping of `module_name` raises this error message when the stated project file (*.aprx*) cannot be opened.
    - *Remedy:*  Ensure that the stated is not opened in any other program (*ArcGIS Pro Desktop*) and that the stated project file exists.

- **`ERROR: Could not access Fish.xlsx (...).`**
    - *Cause:*   The `get_hsi_curve(self, species, lifestage, par)` function of the `Fish()` class (`.site_packages/riverpy/cFish.py`) or the `main()` function in `s40_compare_wua.py` raise this error message when it cannot access `Fish.xlsx` or copy read values from the `/SHArC/SHArea/`condition` directory.
    - *Remedy:*  Ensure that neither `.site_packages/templates/Fish.xlsx` nor any file in `/SHArC/SHArea/`condition*` is used by another program.

 - **`ERROR: Could not add cover HSI.`**
    - *Cause:*   The `make_chsi(self, fish)` function of the `CHSI()` class (`HabitatEvluation/cHSI.py`) raises this error message when it failed to add cover HSI Rasters.
    - *Remedy:*  Manually verify cover HSI Rasters in `SHArC/HSI/` and recompile cover HSI Rasters if needed (see [CoverHSI](SHArC#hemakecovhsi)).
		
	
 - **`ERROR: Could not append PDF page XX to map assembly.`**
    - *Cause:*   The `make_pdf_maps(self, ...)` function of the `Mapper()` class (`.site_packages/riverpy/cMapper.py`) raises this error when it failed to map the current page (extent).
    - *Remedy:*
	    + <a href="LifespanDesign">LifespanDesign</a> / <a href="MaxLifespan">Max Lifespan</a>: Ensure that the definitions in [`LifespanDesign/.templates/mapping.inp`](Signposts#inpfile) are correct.
	    + <a href="VolumeAssessment">VolumeAssessment</a>: Verify the definitions in the [reach coordinates workbook](RiverReaches) and also refer to error message `ERROR: Could not create new project`.
	    + General: Ensure that no other program accesses the `LifespanDesign/.cache/`, `MaxLifespan/.cache/`, `MaxLifespan/Output/`, `VolumeAssessment/Output/`, or `02_Maps/*` directories or their contents (close *ArcGIS Pro*).

 - **`ERROR: Could not calculate CellStatistics (Raster comparison).`**
    - *Cause:*   Raised by `compare_raster_set(self, ...)` function of the `arcpyAnalysis()` class in `LifespanDesign/cLifespanDesignAnalysis.py` when the provided it failed to combine the lifespan according to the provided input Rasters (hydraulic or scour fill or morphological units).
    - *Remedy:*  Manually open the input Rasters and ensure that they comply with the requirements stated in the [Conditions / Input Rasters section](Signposts#conditions).

 - **`ERROR: Could not calculate stable grain size Raster for ... .`**
    - *Cause:*   Error raised by the `ProjectMaker/s30_terrain_stabilization/`'s `main()` function when it cannot calculate the stable grain size for a user-defined minimum (critical) lifespan and *Condition*.
    - *Remedy:*  Open `RiverArchitect/logfile.log` and verify that the stated source data exist and are not empty (if necessary, open geofiles in *ArcGIS Pro* and verify contents).
    
- **`ERROR: Could not create new project (...)`**
    - *Cause:*   A module cannot find a project for mapping when it tries to open `aprx_origin = arcpy.mp.ArcGISProject(self.ref_lyt_dir + "module_name.aprx")` or when it tries to save a copy of the source project (`aprx_origin.saveACopy(self.output_mxd_dir + "module_name.aprx")`).
    - *Remedy:*  Ensure that the source project `aprx_origin` exists (quoted in ERROR-message brackets) and that the target directory (`to:`) can be accessed (writing rights / close *ArcGIS Pro*). If the source project is missing, re-download it from the [source code][sourcecode].

 - **`ERROR: Could not create Raster of the project area.`**
    - *Cause:*   Raised by `set_project_area(self)` of *ProjectMakers*'s `SHArC()` class in `ProjectMaker/cSHArC.py` or the `main()` function in `ProjectMaker/s20_plantings_delineation.py`) when it failed to convert the project area shapefile to a Raster, which it needs for limiting spatial calculations to the project extent.
    - *Remedy:*
        + Ensure that the project was correctly delineated ([Project Area Polygon preparation](ProjectMaker#pminp2)).
        + If the Error message occurred within the terrain stabilization process, either restart the Project creation while properly implementing the [Project Area Polygon preparation](ProjectMaker#pminp2) OR manually create a project area Raster (save as `ProjectMaker/ProjectName_vXX/Geodata/Rasters/ProjectArea.tif`, where in-values=`Int(1)` and out-values=`NoData`).
    
- **`ERROR: Could not create sub-condition folder: ... .`**
    - *Cause:*   Raised by `make_sub_condition(...)` (`GetStarted/fSubCondition`) when the defined sub-*Condition* name is invalid.
    - *Remedy:*  Ensure that the target sub-*Condition* folder is not in use by any other program and that there are no invalid characters for folder names (such as `$` or `?!`).

 - **`ERROR: Could not crop RASTER.`**
    - *Cause:*   The `make_sub_condition(...)` (`GetStarted/fSubCondition.py`) function raises this error message when it failed cropping the Raster with the spatial analyst operation `Con(~IsNull(boundary_ras), Float(source_Raster))`.
    - *Remedy:*  Verify the consistency of the Rasters in the source condition and make sure that no other program is using data from the source condition or the new sub-*Condition* folder.

 - **`ERROR: Could not crop Raster to defined flow depth.`**
    - *Cause:*   The `crop_input_Raster(self, fish_species, fish_lifestage, depth_Raster_path)` function of the `CovHSI(HHSI)` class (`HabitatEvluation/cHSI.py`) raises this error message when it failed cropping the Raster with the spatial analyst operation `Con((Float(h_Raster) >= h_min), cover_type_Raster)`.
    - *Remedy:*  Ensure that the provided flow depth file (selected in the GUI) contains valid data and that `Fish.xlsx` contains a minimum flow depth value for the selected fish species and lifestage.

 - **`ERROR: Could not export PDF page no. XX`**
    - *Cause:*   The `make_pdf_maps(self, ...)` function of the `Mapper()` class (`.site_packages/riverpy/cMapper.py`) raises this error when `LifespanDesign/.templates/mapping.inp` or `MaxLifespan/.templates/mapping.inp` contain invalid xy-coordinates (format).
    - *Remedy:*  Ensure the definitions in [`LifespanDesign/.templates/mapping.inp` and `MaxLifespan/.templates/mapping.inp`](Signposts#inpfile) are correct.

 - **`ERROR: Could not find / access input Rasters.`**
    - *Cause:*   Error raised by the `D2W` class (`GetStarted/cDepth2Groundwater.py`) or the `DET` class (`GetStarted/cDetrendedDEM.py`) or the `MU` class (`GetStarted/cMorphUnits.py`) when the defined DEM, flow depth, or velocity *GeoTIFF*s are not usable.
    - *Remedy:*
        + Ensure that no other program uses the selected in DEM/flow depth Raster and *Condition* folder.
        + Manually / visually verify the consistency of the provided input Rasters.
        + Avoid running `d2w.tif`, `mu.tif` and `det.tif` creation simultaneously and for multiple conditions (the *.cache* folders are locked by individual instantiations).

 - **`ERROR: Could not find max. lifespan Rasters.`**
    - *Cause:*   Error raised by the `main()` function in `ProjectMaker/s20_plantings_delineation.py`) when the defined directory of max. lifespan Rasters contains invalid or corrupted Raster data.
    - *Remedy:*
        + Ensure the correct usage of variables and input definitions ([ProjectMaker Quick GUIde](ProjectMaker#pmquick)).
        + Ensure that max. lifespan Rasters were generated without errors; if necessary, visually control the consistency of max. lifespan Rasters in `.../MaxLifespan/Output/Rasters/CONDITION_reach_lyr20_plants/` and `.../MaxLifespan/Products/Rasters/CONDITION_reach_lyr20_plants/` or ...`nature-based engineering` (cf. [Project Maker vegetation plantings and supporting nature-based engineering features](ProjectMaker#pmplants)).

 - **`ERROR: Could not find any worksheet.`**
    - *Cause:*   Error raised by the `open_wb(self)` function of the `Read()` class in `RiverArchitect/.site_packages/riverpy/cInputOutput.py` or the `MakeFlowTable` class (`RiverArchitect/.site_packages/riverpy/cMakeTable.py`) when the concerned workbook contains errors.
    - *Remedy:*
        + Ensure the correct usage of `.site_packages/templates/Fish.xlsx` ([SHArC Fish section](SHArC#hefish)).
        + Ensure the correct adaptation of `ProjectMaker/.../Project_assessment_vii.xlsx` ([ProjectMaker's Cost quantity workbook](ProjectMaker#pmcq)).
        + Open `SHArC/SHArea/CONDITION_sharea_FILI.xlsx`, verify the data contents and make sure that the file is not opened in any other program.

 - **`ERROR: Could not find hydraulic Rasters for CONDITION.`**
    - *Cause:*   Error raised by the `ProjectMaker/s30_terrain_stabilization/`'s `main()` function when it cannot find hydraulic Rasters for the selected lifespan-design condition.
    - *Remedy:*  Ensure that the hydraulic Rasters used for generating Lifespan and Design Rasters are available in *RiverArchitect*/`01_Conditions/CONDITION/` (also: close all other programs that potentially use these Rasters).

 - **`ERROR: Could not find Lifespan Raster (...).`**
    - *Cause:*   Error raised by the `ProjectMaker/s30_terrain_stabilization/`'s `main()` function when it cannot find lifespan Rasters.
    - *Remedy:*  Go to the <a href="Lifespan/Design">LifespanDesign</a> tab for the selected *Condition*. Create lifespan maps for the `Grains / Boulders` feature ( creates `lf_grains.tif`). Terrain stabilization absolutely requires `Grains / Boulders` (`lf_grains.tif`), and optionally requires `Streamwood` (`lf_wood.tif`) and `Nature-based engineering features (other)` (`lf_bio.tif`).

 - **`ERROR: Could not find sheet "extents" in computation_extents.xlsx.`**
    - *Cause:*   Error raised by the `get_reach_coordinates(self, internal_reach_id)` function of the `Read()` class in `RiverArchitect/.site_packages/riverpy/cReachManager.py`) when the `extents` sheet in the reach coordinate workbook (`ModifyTerrain/.templates/computation_extents.xlsx`) could not be read.
    - *Remedy:*  Ensure the correct setup of `ModifyTerrain/.templates/computation_extents.xlsx` ([reach preparation within the *ModifyTerrain* module](RiverReaches)).

 - **`ERROR: Could not find the cover input geofile [...]`**
    - *Cause:*   Error raised by the `__init__(self, ...)` function of the `CovHSI(HHSI)` class in `SHArC/cHSI.py`) when the input cover geofile could not be read or is missing.
    - *Remedy:*  Ensure that a geofile (Raster or shapefile) exists in the specified `CONDITION` folder for the specified cover type (checkbox activated in the GUI). The `Help` button in the GUI provides more information on required geofiles and the [SHArC Working Principles](SHArC-working-principles#heprin).

 - **`ERROR: Could not interpolate exceedance probability of Q =  [...]`**
    - *Cause:*   Raised by `interpolate_flow_exceedance(self, Q_value)` of the `FlowAssessment()` class in `.site_packages/riverpy/cFlows.py` when the flow duration curve contains invalid data.
    - *Remedy:*  Ensure the correct setup of the used flow duration curve in `00_Flows/CONDITION/flow_duration ... .xlsx`. The file structure must correspond to that of the provided template `flow_duration_template.xlsx` and all discharge values need to be positive floats. Review the [HHSI input preparation](SHArC#hemakehsi) for details.
    
 - **`ERROR: Could not load ... .`**
    - *Cause:*   Raised by several functions, when they cannot find a user-defined or built-in template file.
    - *Remedy:*  Ensure that the stated file exists, can be opened (is not corrupted) and no other program uses the stated file.
    
 - **`ERROR: Could not load boundary Raster: ... .`**
    - *Cause:*   Raised by `make_sub_condition(...)` (`GetStarted/fSubCondition`) when the defined boundary Raster contains invalid data.
    - *Remedy:*  Ensure that the spatial boundary was correctly delineated (similar as described in [Project Area Polygon preparation](ProjectMaker#pminp2)) and converted to an Integer Raster: On-values have to be Integer 1 and Off-values have to be Integer 0. The sub-*Condition* creation only considers Pixels with On-values (Integer 1).
    
 - **`ERROR: Could not load existing Raster of the project area.`**
    - *Cause:*   Raised by `set_project_area(self)` of *ProjectMakers*'s `SHArC()` class in `ProjectMaker/cSHArC.py` when it found a Raster that delineates the project area, but this Raster is corrupted. The function requires the shapefile to Raster conversion to limit applicable Rasters to the project extent range, which is done with Raster calculator operations.
    - *Remedy:*
        + Ensure that the project was correctly delineated ([Project Area Polygon preparation](ProjectMaker#pminp2)).
        + Manually inspect the project delineation Raster.

 - **`ERROR: Could not load newly created Raster of the project area.`**
    - *Cause:*   Raised by `set_project_area(self)` of the *<a href="ProjectMaker">ProjectMaker</a>*'s `SHArC()` class in `ProjectMaker/cSHArC.py` when the converted the project area shapefile is corrupted.
    - *Remedy:*  Ensure that the project was correctly delineated ([Project Area Polygon preparation](ProjectMaker#pminp2)).

 - **`ERROR: Could not open workbook (...).`**
    - *Cause:*   Error raised by the `__init__(self)` function of the `Read()` class in `riverpy/cInputOutput.py` or the `write_flow_duration2xlsx(self, ...)` function of the `SeasonalFlowProcessor()` class (`riverpy/cFlows.py`) when the concerned workbook contains errors or cannot be opened for other reasons.
    - *Remedy:* 
	    +  <a href="ProjectMaker">ProjectMaker</a>: Ensure the correct usage of the concerned workbook ([*ProjectMaker* Wiki][7]).
	    +  Flow generator: Ensure that the template workbook in the parentheses is not opened in any other program and that the template workbook was not modified.

 - **`ERROR: Could not perform spatial radius operations [...].`**
    - *Cause:*   The `spatial_join_analysis(self, rater, curve_data)` function of the `CovHSI(HHSI)` class (`SHArC/cHSI.py`) raises this error message when one or several spatial calculations failed, including `arcpy.RasterToPoint_conversion[...]`, `arcpy.SpatialJoin_analysis[...]` and / or  `arcpy.PointToRaster_conversion[...]`.
    - *Remedy:*  Ensure that the cover input files and habitat suitability (curve) parameters are properly defined according to [CoverHSI](SHArC#hemakecovhsi).

 - **`ERROR: Could not process flow series.`**
    - *Cause:*   Error raised by the `build_flow_duration_data(self.)` (`SeasonalFlowProcessor()` in `RiverArchitect/.site_packages/riverpy/cFlows.py`) when it could not read the provided flow series data file.
    - *Remedy:*  Ensure that the format of the provided flow series workbook corresponds to the provided example data file (`00_Flows/InputFlowSeries/flow_series_example_data.xlsx`).
	
 - **`ERROR: Could not process information from [...].`**
    - *Cause:*   The `main()` function in `ProjectMaker/s40_compare_wua.py` raises this error message when it could not calculate the annually usable habitat area for a condition or (set of) discharge(s).
    - *Remedy:*  Ensure that the variable (parameters) are properly defined according to [ProjectMaker Quick GUIde](ProjectMaker#pmquick) and that the [*SHArC*][6] module contains the required information.
    
 - **`ERROR: Could not read flow duration curve data.`**
    - *Cause:*   Raised by `get_flow_data(self, ...)` of the `FlowAssessment()` class in `.site_packages/riverpy/cFlows.py` when the flow duration curve contains invalid data.
    - *Remedy:*
        + Used within `SHArC`: Ensure that a flow duration curve for all selected *Physical Habitats* and the select hydraulic *Condition* was generated. The flow duration curves are typically saved as `00_Flows/CONDITION/flow_duration_FILI.xlsx`, where `FILI` is a placeholder of the first two letters of the selected species and lifestage (*Physical Habitat*), respectively. For example for *Chinook Salmon - Juvenile*, `FILI` becomes `chju`, or for *All Aquatic - hydrologic year*, `FILI` becomes `alhy`.
        + Ensure that the provided discharge series contains valid data formats as indicated in the example workbook (`00_Flows/InputFlowSeries/flow_series_example_data.xlsx`).

 - **`ERROR: Could not read parameter type [...] from Fish.xlsx.`**
    - *Cause:*   The `get_hsi_curve(self, species, lifestage, par)` function of the `Fish()` class (`.site_packages/riverpy/cFish.py`) and the `SeasonalFlowProcessor` class (`riverpy/cFlows.py`) raise this error message when it cannot read a habitat suitability curve from `Fish.xlsx`.
    - *Remedy:*
        + Ensure that `.site_packages/templates/Fish.xlsx` is not opened in any other program.
        + Ensure that a habitat suitability curve is defined in `Fish.xlsx` for the considered hydraulic or cover parameter according to [SHArC Fish section](SHArC#hefish).
        + Ensure that the lifestages defined in `.site_packages/templates/Fish.xlsx` are  part of the following dictionary: `self.ls_col_add = {"spawning": 1, "fry": 3, "ammocoetes": 3, "juvenile": 5, "adult": 7, "hydrologic year": 1, "season": 3, "depth > x": 5, "velocity > x": 7, "rearing": 7}`. **All lifestages must be defined in `self.ls_col_add`, as relative column number to the 0-column of every Fish species.** For example, for adding a `"rearing"` lifestage for `Chinook salmon` (one of the default species), `"rearing"` must replace `"adult"`, which is in the relative 7th (8-1 for the 0-column) of the Chinook salmon species. If lifestages were otherwise modified, either consider using one of the lifestages defined in the dictionary or modify the dictionary (`self.ls_col_add`) in the `Fish` class (`.site_packages/riverpy/cFish.py`).
	
- **`ERROR: Could not read source file.`**
    - *Cause:*   The `Read` class (`RiverArchitect/.site_packages/riverpy/cInputOutput.py`) or `make_sub_condition` (`GetStarted/fSubCondition`) raise this error when the data from the provided workbook or Raster, respectively, cannot be processed.
    - *Remedy:*
        + `riverpy`: Ensure that the provided workbook respects the input requirements described in the instructions of the applied module.
        + `GetStarted/fSubCondition`: Verify the consistency of the Rasters in the source condition and make sure that no other program is using data from the source condition.

- **`ERROR: Could not read source project (...)`**
    - *Cause:*   A module cannot find a project for mapping when it tries to open `aprx_origin = arcpy.mp.ArcGISProject(self.ref_lyt_dir + "module_name.aprx")`.
    - *Remedy:*  Ensure that the source project `aprx_origin` exists (quoted in ERROR-message brackets) and not opened in any other application (e.g., close *ArcGIS Pro*). If the source (origin) project is missing, re-download it from the [source code][sourcecode].

 - **`ERROR: Could not retrieve reach coordinates.`**
    - *Cause:*   The automated terrain modification with grading and/or widen features in the `modification_manager(self, feat_id)` function of the `ModifyTerrain()` class (`ModifyTerrain/cModifyTerrain.py`) or the `make_volume_diff_rasters(self)` function of the `VolumeAssessment()` class (`VolumeAssessment/cVolumeAssessment.py`) raise this error when the reach extents defined in `ModifyTerrain/.templates/computation_extents.xlsx` are not readable. In particular, the command `self.reader.get_reach_coordinates(self.reaches.dict_id_int_id[self.current_reach_id])` caused the error.
    - *Remedy:*
        + Follow the instructions in [reach preparation within the *ModifyTerrain* module](RiverReaches) for correct reach definitions.
	    + If the [*ModifyTerrain*][5] module is externally loaded, ensure the correct definition of features and feature shortnames (see the [alternative run options for the *ModifyTerrain* module](ModifyTerrain#mtaltrun)).

 - **`ERROR: Could not run SHArea analysis.`**
    - *Cause:*   The `main()` function in `ProjectMaker/s40_compare_wua.py` raises this error message when it could not calculate SHArea.
    - *Remedy:*  Traceback warning and other error messages. Ensure the correct definition of parameters, creation of required geodata, and file naming ([*ProjectMaker* Wiki][7]))

 - **`ERROR: Could not save best lifespan Raster.`**
    - *Cause:*   Raised by `identify_best_features(self)` of [*MaxLifespan*][4]'s `ArcpyContainer()` class in `MaxLifespan/cActionAssessment.py` when the calculated internal best lifespan Raster is corrupted.
    - *Remedy:*
        + Check prior WARNING and ERROR messages.
	    + Ensure that neither the directory `MaxLifespan/.cache/` nor the directory `MaxLifespan/Output/` or their contents are in use by other programs.

 - **`ERROR: Could not save CSI Raster associated with ...`**
    - *Cause:*   Raised by `make_chsi_hydraulic(self, fish)` of [*SHArC*][6]'s `CHSI()` class in `SHArC/cHSI.py` when the calculated cHSI Raster is empty or corrupted.
    - *Remedy:*
        + Ensure that neither the directory `SHArC/.cache/` nor the directory `SHArC/SHArea/` or their contents are used by another program.
        + Review the input settings according to [SHArC Quick GUIde](SHArC#hegui).

 - **`ERROR: Could not save cover / H HSI [...] Raster ...`**
    - *Cause:*   Raised by `make_hhsi(self, fish_applied)` of [*SHArC*][6]'s `HHSI()` class in `SHArC/cHSI.py` when the calculated HHSI Raster is empty or corrupted.
    - *Remedy:*
        + Ensure that no other software uses data from neither the `SHArC/` nor the `RiverArchitect/01_Conditions/` directories.
        + Review the input flow velocity and depth Rasters according to the [Conditions / Input Rasters section](Signposts#conditions).

 - **`ERROR: Could not save RASTER .`**
    - *Cause:*   Raised by `save_tif(self, ...)` of [*GetStarted*][11]'s `ConditionCreator()` class in `GetStarted/cConditionCreator.py` or `make_sub_condition` (`GetStarted/fSubCondition.py`) when a Raster file could not be saved to a New or Sub *Condition*, respectively.
    - *Remedy:*
        + Ensure that no other program uses the new `RiverArchitect/01_Conditions/` directory.
        + Visually verify the consistency of provided input Rasters.
	
 - **`ERROR: Could not save WORKBOOK.`**
    - *Cause:*   The `main()` function in `ProjectMaker/s40_compare_wua.py` or the `write_flow_duration2xlsx(self, ...)` function of the `SeasonalFlowProcessor()` class (`riverpy/cFlows.py`) raise this error message when they could not save the `WORKBOOK`.
    - *Remedy:*  Ensure that the target workbook can be overwritten, has valid contents, and is not opened by another program. Traceback earlier warning and error messages.

 - **`ERROR: Could not save SHArea-CHSI Raster.`**
    - *Cause:*   Raised by `calculate_sha(self)` of [*SHArC*][6]'s `CHSI()` class in `SHArC/cHSI.py` when the calculated cHSI Raster is empty or corrupted.
    - *Remedy:*
        + Ensure that the SHArea threshold has a meaningful value between 0.0 and 1.0 ([SHArC Intro](SHArC)).
        + Ensure that neither the directory `SHArC/.cache/` nor the directory `SHArC/SHArea/` or their contents are in use by other programs.
        + Review the input settings according to [SHArC Quick GUIde](SHArC#hegui).

 - **`ERROR: Could not set arcpy environment (permissions and licenses?).`**
    - *Cause:*   A script using `arcpy` and/or `arcpy.sa` could not set up the work environment.
    - *Remedy:*  Either the wrong *Python* interpreter was used or `arcpy` and/or a *Spatial Analyst* extension are not available. [Read more on setting up the Python environment.](https://github.com/RiverArchitect/RA_wiki/Installation#started)
	
 - **`ERROR: Could not transfer net SHArea gain.`**
    - *Cause:*   The `main()` function in `ProjectMaker/s40_compare_wua.py` raises this error message when it could not copy the calculated SHArea from `SHArea_evaluation_unit.xlsx` to **`REACH_stn_costs_vii.xlsx`**.
    - *Remedy:*  Open `SHArea_evaluation_template_unit.xlsx` and verify the calculated values. Traceback potential error sources in the CHSI Rasters `/SHArC/` folder and other error messages.
	
 - **`ERROR: Could not transfer SHArea data for [FISH].`**
    - *Cause:*   The `main()` function in `ProjectMaker/s40_compare_wua.py` raises this error message when it could not retrieve SHArea data from the `/SHArC/SHArea/` module to  `SHArea_evaluation_UNIT.xlsx`.
    - *Remedy:*  Open `SHArea_evaluation_TEMPLATE_UNIT.xlsx` and verify the calculated values. Traceback potential error sources in the CHSI Rasters `/SHArC/` folder and other error messages.

 - **`ERROR: Could not write flow data set.`**
    - *Cause:*   Error raised by the `write_flow_duration2xlsx(self, ...)` function of the `SeasonalFlowProcessor()` class (`riverpy/cFlows.py`) when it could not write flow duration data set to `RiverArchitect/00_Flows/CONDITION/flow_duration_FILI.xlsx`.
    - *Remedy:*  Close all applications that may use `00_Flows/CONDITION/flow_duration_FILI.xlsx` and traceback earlier warning and error messages.
	
 - **`ERROR: Could not write flow duration curve data (...).`**
    - *Cause:*   Error raised by the `make_flow_duration(self, ...)` or `make_condition_flow_duration(self, ...)` functions (`SeasonalFlowProcessor()` in `RiverArchitect/.site_packages/riverpy/cFlows.py`) when it could not write flow duration curve data to `RiverArchitect/00_Flows/CONDITION/flow_duration_FILI.xlsx`.
    - *Remedy:*  Close all applications that may use `00_Flows/CONDITION/flow_duration_FILI.xlsx`.
    
 - **`ERROR: Could not write value to CELL [...]`**
    - *Cause:*   Error raised by the `save_close_wb(self, ...)` (`Write()` in `RiverArchitect/.site_packages/riverpy/cInputOutput.py`) or `write_data_cell(self, column, row, value)` (`MakeTable` in `.site_packages/riverpy/cMakeTable.py`) when it cannot write a value to `RiverArchitect/SHArC/SHArea/`condition_FILI.xlsx`.
    - *Remedy:*  Close all applications that may use `RiverArchitect/SHArC/SHArea/CONDITION_FILI.xlsx`. Detailed information on [*SHArC*][6] workbook outputs are available in the [HHSI input preparation](SHArC#hemakehsi) section.

 - **`ERROR: Could not write SHArea data for [FISH].`**
    - *Cause:*   The `main()` function in `ProjectMaker/s40_compare_wua.py` raises this error message when it could not write the calculated SHArea to when it cannot write a value to `SHArea_evaluation_template_unit.xlsx`.
    - *Remedy:*  Ensure that the workbook is not opened by another program and/or visually verify that the concerned `CHSI* Rasters contain valid values.

 - **`ERROR: Cover Raster calculation (check input data).`**
    - *Cause:*   Raised by `call_analysis(self, curve_data)` of [*SHArC*][6]'s`CovHSI(HHSI)` class in `SHArC/cHSI.py` when the cover HSI Raster calculation failed.
    - *Remedy:*   Ensure that the input geofiles (Raster or shapefile) are correctly set up according to [CoverHSI](SHArC#hemakecovhsi).
	
 - **`ERROR: Extent is not FLOAT. Substituting to extent = 7000.00.`**
    - *Cause:*   Raised by the `save_design(self, name)` or`save_lifespan(self, name)` functions of the `ArcPyAnalysis` class in `LifespanDesign/cLifespanDesignAnalysis.py` when the output folder for Rasters (the folder directory is stated in the logfile) contains Rasters of the same name which cannot be deleted.
    - *Remedy:*  Ensure that no other program uses the Raster output folder and consider moving existing files in that folder to `LifespanDesign/Products/Rasters/CONDITION`.

 - **`ERROR: Existing files are locked. Consider deleting [...] file structure.`**
    - *Cause:*   Raised by the `get_map_extent(self, direction)` function of the `Info()` class in either `LifespanDesign/cReadInpLifespan.py` or `MaxLifespan/cReadActionInput.py` when `mapping.inp` has bad assignments of *x*-*y* coordinates (not a number).
    - *Remedy:*  See `ERROR: Bad call of map centre coordinates ... *

 - **`ERROR: Failed checking *PAR* of *FEATURE*.`**
    - *Cause:*   Special case of **`ERROR: Function analysis`**, which may occur after code modifications.
    - *Remedy:*
        + Make sure that the `self.parameter_list`s of features ([Code Extension / Extend Features within the *LifespanDesign* module](LifespanDesign-code)) has valid entries that also occur in `analysis_call(*args)` (`LifespanDesign/feature_analysis.py`).
	    + Make sure that valid function names exist in `LifespanDesign/cLifespanDesignAnalysis.py` ([Add analysis within the *LifespanDesign* module](LifespanDesign-code#addana)).

 - **`ERROR: Failed to access [...].`**
    - *Cause:*   Error raised by the `open_wb(self, ...)` function of the `Read()` (or the inheriting `Write()`)class in `RiverArchitect/.site_packages/riverpy/cInputOutput.py` or the `MakeFlowTable` class in `RiverArchitect/.site_packages/riverpy/cMakeTable.py`) when a workbook could not be opened.
    - *Remedy:*
        + Ensure that the listed workbook is not opened in any other program and that the workbook is correctly installed according to the module descriptions.
        + Used within `SHArC`:
		   * Ensure that a flow duration curve for all selected *Physical Habitats* and the select hydraulic *Condition* was generated. The flow duration curves are typically saved as `00_Flows/CONDITION/flow_duration_FILI.xlsx`, where `FILI` is a placeholder of the first two letters of the selected species and lifestage (*Physical Habitat*), respectively. For example for *Chinook Salmon - Juvenile*, `FILI` becomes `chju`, or for *All Aquatic - hydrologic year*, `FILI` becomes `alhy`.
		   * If the module is executed repeatedly for the same condition and fish species-lifestage, and the workbook (`SHArC/SHArea/CONDITION_sharea_FILI.xlsx`) has been manually deleted, restore it by clicking on the `Make HSI Raster (...)` dropdown menu > Select  "Hydraulic" or "Cover" options to open the popup window > Select a *Condition* > Wait until the green button `View discharge dependency workbook` becomes active > `RETURN to MAIN WINDOW` and repeat habitat raster, raster combination and/or *SHArea* analysis.
		   * Open `SHArC/SHArea/CONDITION_sharea_FILI.xlsx`, verify the data contents and make sure that the file is not opened in any other program.

 - **`ERROR: Failed to access computation_extents.xlsx.`**
    - *Cause:*   Error raised by the `get_reach_coordinates(self, internal_reach_id)` function of the `Read()` class in `RiverArchitect/.site_packages/riverpy/cReachManager.py`) when the reach coordinate spreadsheet (`ModifyTerrain/.templates/computation_extents.xlsx`) could not be read.
    - *Remedy:*  Ensure the correct setup of `ModifyTerrain/.templates/computation_extents.xlsx` ([reach preparation within the *ModifyTerrain* module](RiverReaches)).

 - **`ERROR: Failed to access / Failed to load [...]`**
    - *Cause:*   (1) Error raised by the `open_wb(self)` and `make_condition_xlsx(self, fish_sn)` functions of the `MakeTable()` class in `.site_packages/riverpy/cMakeTable.py`) when the template workbook contains errors.<br/>
                 (2) Error raised by the *GetStarted* module's `ConditionCreator` (`cConditionCreator.py`).
    - *Remedy:*
        + Ensure the correct usage of `.site_packages/templates/Fish.xlsx` ([SHArC Fish section](SHArC#hefish)) and the completeness of `SHArC/.templates/Q_sharea_template_si.xlsx` and `SHArC/.templates/Q_sharea_template_us.xlsx`. If either template workbook is corrupted or does not exist, re-install missing files.
        + *GetStarted:* Ensure that the provided Raster exists.

 - **`ERROR: Failed to access WORKBOOK.`**
    - *Cause:*   Error raised by the `write_volumes(self, ...)` function of the `Writer()` class in `RiverArchitect/.site_packages/riverpy/cReachManager.py`) or the `__init__(..)` function of the `Read()` class in `RiverArchitect/.site_packages/riverpy/cInputOutput.py` when The `WORKBOOK` is inaccessible or locked by another program.
    - *Remedy:*  Ensure that the concerned workbook exists and no other program uses the workbook.

 - **`ERROR: Failed to add Raster.`**
    - *Cause:*   Raised by `read_hyd_Rasters(self)` of [*SHArC*][6]'s `HHSI()` class in `SHArC/cHSI.py` when is could not find hydraulic input Rasters.
    - *Remedy:*
        + Ensure that no other software uses data from neither the `SHArC/` nor the `RiverArchitect/01_Conditions/` directories.
        + Review the input flow velocity and depth Rasters according to the [Conditions / Input Rasters section](Signposts#conditions).

 - **`ERROR: Failed to create WORKBOOK.`**
 	- *Cause:*   Error raised by the `write_volumes(self, ...)` function of the `Writer()` class in `.site_packages/riverpy/cReachManager.py`) when the `template` it could not add new sheets in `VolumeAssessment/Output/CONDITION_volumes.xlsx` or write to copies of `VolumeAssessment/templates/volume_template.xlsx`.
    - *Remedy:*  Traceback earlier error messages, ensure that no other program locked `VolumeAssessment/Output/CONDITION_volumes.xlsx` and ensure that `VolumeAssessment/templates/volume_template.xlsx` was not deleted.

 - **`ERROR: Failed to open Fish.xlsx. Ensure that the workbook is not open.`**
    - *Cause:*   Raised by the `edit_xlsx(self)` function of the `Fish()` class in `.site_packages/riverpy/cFish.py` when  `.site_packages/templates/Fish.xlsx` is opened by another program or non-existent.
    - *Remedy:*  Ensure that the file `.site_packages/templates/Fish.xlsx` exists and close any software that may use the workbook.
    
 - **`ERROR: Failed to load [...].`**
    - *Cause:*   Raised by the `make_condition_xlsx(self, ...)` function of the `MakeTable()` class in `.site_packages/riverpy/cMakeTable.py` when it could not copy a template workbook for creating fish-lifestage-specific flow tables (copy of `empty.xlsx`).
    - *Remedy:*  Ensure that all template files in `SHArC/.templates/` exist as provided with the installation files (in particular: `empty.xlsx`, `CONDITION_sharea_template_si.xlsx`, `CONDITION_sharea_template_us.xlsx`, and `flow_duration_template.xlsx`).

 - **`ERROR: Failed to read coordinates from computation_extents.xlsx (return 0).`**
    - *Cause:*   Error raised by the `get_reach_coordinates(self, internal_rach_id)` function of the `Read()` class in `.site_packages/riverpy/cReachManager.py`) when the reach coordinate spreadsheet (`ModifyTerrain/.templates/computation_extents.xlsx`) contains invalid data.
    - *Remedy:*  Ensure correct setup of `ModifyTerrain/.templates/computation_extents.xlsx` ([reach preparation within the *ModifyTerrain* module](RiverReaches)).

 - **`ERROR: Failed to read maximum depth to water value for [...].`**
    - *Cause:*   Error raised by the `lower_dem_for_plants* function of the `ModifyTerrain` class in `ModifyTerrain/cModifyTerrain.py`) when the threshold workbook (`LifespanDesign/.templates/thresh old_values.xlsx`) is not accessible or does not contain values for *Depth to water table (min) / max*  contains invalid data.
    - *Remedy:*  Ensure the correct setup of `LifespanDesign/.templates/threshold_values.xlsx` ([Modify Threshold Values within the *LifespanDesign* module](LifespanDesign#modthresh)). Note that *ModifyTerrain* starts reading depth to water table values column by column, until it meets a non-numeric value.

 - **`ERROR: Failed to save PDF map assembly.`**<a name="pdfexp"></a>
    - *Cause:*   The `make_pdf_maps(self, ...)` function of the `Mapper()` class (`.site_packages/riverpy/cMapper.py`) raises this error when the map assembly is corrupted.
    - *Remedy:* 
        + PDF map export of Lifespan maps has troubles at the moment. We recommend to open the automatically created project `RiverArchitect/02_Maps/CONDITION/maps_CONDITION_lyrXY.aprx` and to export PDF maps in *ArcGIS Pro*: (1) Go to desired layout tab; (2) Ensure map layout fits desired export; (3) Go to the `Share` ribbon and click on the green arrow `Layout` (export layout). 
        + Ensure that no other program accesses the `LifespanDesign/.cache/`, `MaxLifespan/.cache/`, `ModifyTerrain/.cache/`, `LifespanDesign/Output/`, `MaxLifespan/Output/`, or `ModifyTerrain/Output/` directories or their contents (close *ArcGIS Pro* and verify read/write rights for `RiverArchitect/02_Maps/CONDITION/`).

 - **`ERROR: Failed to save WORKBOOK.`**
    - *Cause:*   Raised by `calculate_sha(self)` of [*SHArC*][6]'s `CHSI()` class in `SHArC/cHSI.py` when it could not save `CONDITION_FILI.xlsx`.
    - *Remedy:*  Ensure that no other software uses `SHArC/SHArea/CONDITION_FILI.xlsx`.

 - **`ERROR: Failed to set reach extents -- output is corrupted.`**
    - *Cause:*   The automated terrain modification with grading and/or widen features in the `lower_dem_for_plants(self, feat_id, extents)` function of the `ModifyTerrain()` class (`ModifyTerrain/cModifyTerrain.py`) or the creation of volume difference Rasters in the `make_volume_diff_rasters(self)` function of the `VolumeAssessment()` class (`VolumeAssessment/cVolumeAssessment.py`) raise this error when the reach extents defined in `ModifyTerrain/.templates/computation_extents.xlsx` are not readable.
    - *Remedy:*  Follow the instructions in [reach preparation within the *ModifyTerrain* module](RiverReaches) for correct reach definitions.


 - **`ERROR: FEAT SHORTNAME contains non-valid data or is empty.`**
    - *Cause:*   Raised by `get_design_data(self)` in `MaxLifespan/cActionAssessment.py` when the  feature `shortname` Raster is empty or the `shortname* itself does not match the code conventions.
    - *Remedy:* 
        + If code was modified: Review code modifications and ensure to define feature `shortname`s as listed in the [River Design and Restoration Features pages](River-design-features#featoverview). If a new feature was added, it also needs to be appended in the container lists (`self.id_list, self.threshold_cols, self.name_list`) of the `Feature()` class in `.site_packages/riverpy/cDefinit ions.py`. A new feature also requires modifications of the `RiverArchitect/LifespanDesign/.templates/threshold_values.xlsx` spreadsheet ([Modify Threshold Values within the *LifespanDesign* module](LifespanDesign#modthresh)), in line with the column state in the `self.threshold_cols* list of the `Feature()` class.
        + Check consistency of suspected lifespan/design Rasters, the correctness of lifespan/design input directory definitions ([MaxLifespan Quick GUIde](MaxLifespan#actquick)) and if needed re-run lifespan/design Raster Maker.
    
- **`ERROR: Flow series analysis failed.`**
    - *Cause:*   The `make_flow_duration(self, ...)` function in `riverpy/cFlows.py` (`SeasonalFlowAssessment` class) raises this error message when executing the `self.build_flow_duration_data(self)` function failed.
    - *Remedy:*  The provided flow series workbook may be erroneous. Ensure that the workbook follows the formats provided in `00_Flows7InputFlowSeries/flow_series_example_data.xlsx` and follow up previous warning and error messages.

 - **`ERROR: Incoherent data in RAS (Raster comparison).`**
    - *Cause:*   Raised by `compare_Raster_set(self, ...)` function of the `ArcPyAnalysis()` class in `LifespanDesign/cLifespanDesignAnalysis.py` when the provided input Raster `RAS` (hydraulic or scour fill or morphological units) are invalid.
    - *Remedy:*
        + Manually open the concerned `RAS` Raster and ensure that it complies with the requirements for input Rasters stated in the [Conditions / Input Rasters section](Signposts#conditions).
        + Verify that the Rasters defined in `01_Conditions/CONDITION/input_definitions.inp` (lines 8 to 18) correspond to the GRID Raster names in the select conditions folder in `01_Conditions/`.
	
 - **`ERROR: Input file not available.`**
    - *Cause:*   Raised by `get_line_entries(self, line_no)` function of the `Info()` class in `LifespanDesign/cRead InpLifespan.py` when it cannot access input files.
    - *Remedy:*
        + Ensure that the file `01_Conditions/CONDITION/input_definitions.inp` exists in the directory `LifespanDesign/.templates/` corresponding to the definitions in the [Input definitions files of the *LifespanDesign* module](Signposts#inpfile).
	    + Ensure that the file `mapping.inp` exists in the directory `LifespanDesign/.templates/` corresponding to the definitions in [*LifespanDesign* Output maps](LifespanDesign#outmaps).
	    + In the case of doubts: Replace `01_Conditions/CONDITION/input_definitions.inp` and `mapping.inp` with the original files and re-apply modifications strictly following the [Conditions / Input Rasters section](Signposts#conditions).
	
 - **`ERROR: Input Rasters contain invalid data.`**
    - *Cause:*   Error raised by the `D2W` class (`GetStarted/cDepth2Groundwater.py`) or the `DET` class (`GetStarted/cDetrendedDEM.py`) when the defined DEM or flow depth *GeoTIFF* are not usable.
    - *Remedy:*
        + Ensure that no other program uses the selected in DEM/flow depth Raster and *Condition* folder.
        + Manually / visually verify the consistency of the provided DEM / flow depth Rasters.
        + Avoid running both routines simultaneously and for multiple *Conditions* (there is only one *.cache* folder that is locked by every process call).

 - **`ERROR: Insufficient data. Check Raster consistency and add more flows(?).`**
    - *Cause:*   The `compare_Raster_set(self, Raster_set, threshold)` function in `LifespanDesign/cLifespanDesignAnalysis.py` raises this error when insufficient hydraulic Rasters are provided or when the provided hydraulic Rasters have inconsistent data.
    - *Remedy:*
        + Make sure to provide at least two pairs of hydraulic (`u` and `h`) Rasters that correspond to two different discharges (one `u` and one `h` Raster per discharge).
        + As a rule of thumb: the more hydraulic Rasters provided, the better are the lifespan maps.
        + Verify Raster and corresponding lifespan definitions in `01_Conditions/CONDITION/input_definitions.inp` ([Input definitions files of the *LifespanDesign* module](Signposts#inpfile)).

 - **`ERROR: Invalid cell assignment for discharge / Rasters.`**
    - *Cause:*   Error raised by the `make_condition_xlsx(self, fish_sn)` function of the `MakeTable()` class in `.site_packages/riverpy/cMakeTable.py`) when it cannot write discharge values to `RiverArchitect/SHArC/SHArea/CONDITION_FILI.xlsx`.
    - *Remedy:*  Ensure that the flow duration curve is well defined (see the [HHSI input preparation](SHArC#hemakehsi)) and that `RiverArchitect/SHArC/SHArea/CONDITION_FILI.xlsx` is not used by any other application.
    - 
	
 - **`ERROR: Invalid date and / or flow ranges in discharge series.`**
    - *Cause:*   Error raised by the `make_flow_season_data(self, ...)` function (`SeasonalFlowProcessor` class in `.site_packages/riverpy/cFlows.py`) when the data provided in the flow series workbook cannot be interpreted.
    - *Remedy:*  Ensure that the provided flow series workbook corresponds to the formats defined in the example data set (`00_Flows/InputFlowSeries/flow_series_example_data.xlsx`). In particular, the date and discharge columns and start rows are hard-coded (we will work on the issue in future ...) and need to correspond those in the sample data set.
    
 - **`ERROR: Invalid date assignment (Fish.xlsx).`**
    - *Cause:*   Error raised by the `get_season_dates(self, ...)` function of the `Fish()` class in `.site_packages/riverpy/cFish.py` ot the `build_flow_duration_data(self)` function (`SeasonalFlowProcessor` class in `.site_packages/riverpy/cFlows.py`) when either function cannot read the dates defined in `.site_packages/templates/Fish.xlsx`.
    - *Remedy:*  Ensure that the date assignment in `.site_packages/templates/Fish.xlsx` corresponds to template conditions.

 - **`ERROR: Invalid feature ID.`**
    - *Cause:*   Error raised by the `__init__(self, ...)` function of the `ThresholdDirector()` class in `/LifespanDesign/cThresholdDirector.py`, when the feature IDs (shortnames) in `/LifespanDesign/.templates/threshold_values.xlsx` are incorrectly defined.
    - *Remedy:*
        + Ensure correct definitions in `/LifespanDesign/.templates/threshold_values.xlsx` ([Modify Threshold Values within the *LifespanDesign* module](LifespanDesign#modthresh)).
        + Consider replacing corrupted threshold workbooks with the original file.

 - **`ERROR: Invalid file name or data.`**
    - *Cause:*   Error raised by the `save_close_wb(self, *args)` function of the `MakeTable()` or `Write()` class in `.site_packages/riverpy/cMakeTable.py`) or `RiverArchitect/.site_packages/riverpy/cInputOutput.py`), respectively, when it cannot save a workbook (typically `RiverArchitect/SHArC/SHArea/CONDITION_FILI.xlsx` or a copy of the [cost master workbook](https://github.com/RiverArchitect/RA_wiki/ProjectMaker#pmcq)).
    - *Remedy:*
        + [*SHArC*][6]: Close all applications that may use `CONDITION_FILI.xlsx` and ensure that its template exists. Detailed information on [*SHArC*][6] workbook outputs are available in the [HHSI input preparation](SHArC#hemakehsi).
        + [*ProjectMaker*][7]:  Close all applications that may use the cost master workbook (`REACH_stn_costs_VERSION.xlsx`) and ensure that it exists. Detailed information is available in [ProjectMaker Cost quantity section](ProjectMaker#pmcq).

 - **`ERROR: Invalid interpolation data type (type(Q flowdur) ==  ...)`**
    - *Cause:*   Raised by `interpolate_flow_exceedance(self, Q_value)` of [*SHArC*][6]'s `FlowAssessment()` class in `SHArC/cFlows.py` when the flow duration curve contains invalid data.
    - *Remedy:*  Ensure the correct setup of the used flow duration curve in `SHArC/FlowDurationCurves/`. The file structure must correspond to that of the provided template `flow_duration_template.xlsx`. Review the [HHSI input preparation](SHArC#hemakehsi) for details.

 - **`ERROR: Invalid x-y coordinates in extent source [mapping.inp / reaches].`**
    - *Cause:*   The `make_pdf_maps(self, ...)` function of the `Mapper` class in `.site_packages/riverpy/cMapper.py` raises this error when either the `LifespanDesign/.templates/mapping.inp`, `MaxLifespan/.templates/mapping.inp`, or `ModifyTerrain/.templates/computation_extents.xlsx` contains invalid map definitions (extents).
    - *Remedy:*  Ensure that the extent definitions in [`LifespanDesign/.templates/mapping.inp`](Signposts#inpfile) and/or [`ModifyTerrain/.templates/computation_extents.xlsx`](RiverReaches) are valid numeric values according to the module descriptions.


 - **`ERROR: Invalid keyword for feature type.`**
    - *Cause:*   The `Manager` class in `MaxLifespan/cFeatureActions.py` raises this error when it received a `feature_type` argument that is not `"terraforming"`, `"plantings"`, `"nature-based engineering"`, or `"maintenance"`. The error may occur either after code modifications or when`geo_file_maker(condition, feature_type, *args)` in `MaxLifespan/action_planner.py` was executed as standalone or imported as a package in an external application.
    - *Remedy:*
        + Ensure that code extensions comply with coding conventions and instructions in the [MaxLifespan module code modification possibilities](MaxLifespan#actcode). 
        + Ensure that external calls of `geo_file_maker(condition, feature_type, *args)` contain an acceptable  `feature_type` (i.e., `feature_type=` either  `"terraforming"`, `"plantings"`, `"nature-based engineering"`, or `"maintenance"`).

- **`ERROR: Invalid reference map for [...] (skipping).`**
    - *Cause:*   Error raised by mapping routines when the reference map is not present in the mapping project template or the *Condition* project file (*.aprx*).
    - *Remedy:*  Verify that the project file contains all [default layouts and maps](Mapping#lyts) (layout and map names should be identic).

 - **`ERROR: Invalid volume name.`**
    - *Cause:*   Error raised by the `write_volumes(self, ...)` function of the `Writer()` class in `.site_packages/riverpy/cReachManager.py`, when the `template` sheet in the output (or template) workbook (`VolumeAssessment/Output/CONDITION_volumes.xlsx` or `VolumeAssessment/.templates/volume_template.xlsx`) are inaccessible.
    - *Remedy:*  Ensure that `VolumeAssessment/Output/CONDITION_volumes.xlsx` or `VolumeAssessment/.templates/volume_template.xlsx` are not opened in any other program.

 - **`ERROR: Lifespan data fetch failed.`**
    - *Cause:*   The `get_lifespan_data(self)` or`get_design_data(self)` function of the `ArcpyContainer` class in `MaxLifespan/cActionAssessment.py` raise this error when it could not retrieve lifespan or design maps from the defined lifespan/design input directory.
    - *Remedy:*
        + Check lifespan/design folder definitions (review [MaxLifespan Quick GUIde](MaxLifespan#actquick)).
        + Ensure that lifespan and/or design Rasters are in the defined folder.

 - **`ERROR: Mapping could not assign xy-values. Undefined zoom.`**
    - *Cause:*   Error raised by the `zoom2map(self, xy)` functions of the `Mapper()` class (`.site_packages/riverpy/cMapper.py`) when it receives a bad format of *x*-*y* values.
    - *Remedy:*
	    + [*LifespanDesign*][3] or [*MaxLifespan*][4]: Ensure the correct format of [`mapping.inp`](Signposts#inpfile) is correct.
        + [*ModifyTerrain*][5]: Ensure correct setup of `ModifyTerrain/.templates/computation_extents.xlsx` ([reach preparation within the *ModifyTerrain* module](RiverReaches)).
        + For more settings, review the [Mapping wiki](Mapping#modify-map-extents).

 - **`ERROR: Mapping failed.`**
    - *Cause:*   The `make_pdf_maps(self, ...)` function of the `Mapper()` class (`.site_packages/riverpy/cMapper.py`) raises this error when it could not create `PDF` maps. 
    - *Remedy:* Ensure that all layouts ([see module-specific layout names](Mapping#standard-layouts)) are consistently defined in `RiverArchitect/02_Maps/templates/river_template.aprx` and/or `RiverArchitect/02_Maps/CONDITION/map_CONDITION_design.aprx`. Note that modifying layout and/or layer names may cause this error. Therefore, the template layer and layout names must not be changed. Read more about modifications of the smybology, legend, map extents, or code modifications in the <a href="Mapping">Mapping</a> wiki.

 - **`ERROR: Map layout preparation failed.`**
    - *Cause:*   The `prepare_layout(self, ...)` function of the `Mapper()` class (`.site_packages/riverpy/cMapper.py`) raises this error when it encounters problems with either the provided Rasters or the layouts in the *ArcGIS* project file (`.aprx`).
    - *Remedy:*
        + [*LifespanDesign*][3]: If a layout was modified ([see default list](Mapping#standard-layouts)), ensure that links to databases and datasets are correct.
        + [*MaxLifespan*][4]: Ensure that all relevant layouts ([see default list](Mapping#standard-layouts)) are contained in the *ArcGIS* project file (see [mapping descriptions](Mapping#about-mapping-with-river-architect)). If needed, add new layouts after code modifications (the [MaxLifespan module code modification possibilities](MaxLifespan#actcode)).
	    + <a href="VolumeAssessment">VolumeAssessment</a>: Ensure that all relevant layouts ([see default list](VolumeAssessment#vamap)) are contained in the *ArcGIS* project file (see [mapping descriptions](Mapping#about-mapping-with-river-architect)).


 - **`ERROR: Missing (or wrong format of) Raster input definitions.`**
    - *Cause:*   Raised by `get_line_entries(self, line_no)` function of the `Info()` class in `LifespanDesign/cReadInpLifespan.py` when  `01_Conditions/CONDITION/input_definitions.inp` is corrupted.
    - *Remedy:*  Ensure that the file `01_Conditions/CONDITION/input_definitions.inp` exists in the directory `LifespanDesign/.templates/` corresponding to the definitions in the [input definitions files](Signposts#inpfile). In case of doubts: Replace `01_Conditions/CONDITION/input_definitions.inp` with the original file and re-apply modifications strictly following the [Conditions / Input Rasters section](Signposts#conditions).

 - **`ERROR: Multiple openings of Fish.xlsx. Close all office apps ...`**
    - *Cause:*   Raised by the `assign_fish_names(self)` function of the `Fish()` class in `.site_packages/riverpy/cFish.py` when  `.site_packages/templates/Fish.xlsx` is opened by another program or non-existent.
    - *Remedy:*  Ensure that the file `.site_packages/templates/Fish.xlsx` exists and close any software that may use the workbook.

 - **`ERROR: No HSI assigned for parameter type ...`**
    - *Cause:*   Raised by the `get_hsi_curve(self, species, lifestage, par)` function of the `Fish()` class in `SHArC/cFish.py` when `.site_packages/templates/Fish.xlsx` it expected a habitat suitability curve for `par*, but it could not find values..
    - *Remedy:*  Ensure that the file `.site_packages/templates/Fish.xlsx` has valid contents according to [SHArC Fish section](SHArC#hefish).

- **`ERROR: No project/layout available (...).`**
    - *Cause:*   Error raised by mapping routines when map making without project file (*.aprx*) is invoked.
    - *Remedy:*  Verify that the project file contains all [default layouts](Mapping#lyts).

- **`ERROR: No reference layout found for [...] (skipping).`**
    - *Cause:*   Error raised by mapping routines when the geofile to be mapped is not associated with any layout in the template or *Condition* project file (*.aprx*).
    - *Remedy:*  Verify that the project file contains all [default layouts](Mapping#lyts).

- **`ERROR: No reference map found for [...] (skipping).`**
    - *Cause:*   Error raised by mapping routines when the geofile to be mapped is not associated with any map in the template or *Condition* project file (*.aprx*).
    - *Remedy:*  Verify that the project file contains all [default layouts](Mapping#lyts) (the layout and map names should be identic).

 - **`ERROR: *PAR* - Raster copy to Output/Rasters folder failed.`**
    - *Cause:*   The `.cache` folder does not exist or does not contain GRID Rasters or the output folder is not accessible. This error is likely to occur when other errors occurred previously. 
    - *Remedy:* 
        + Follow troubleshooting of other error messages and re-run.
        + Avoid modifications of any folder in the code directory while the program is running, in particular, `.cache`, `01_Conditions/`, `LifespanDesign/Output/Rasters/` and `02_Maps/CONDITION/`.

 - **`ERROR: Raster copy to Output folder failed.`**
    - *Cause:*   The `save_Rasters(self)` function of the `ModifyTerrain()` class in `ModifyTerrain/cModifyTerrain.py` raises this error when saving a terrain difference or new DEM Raster failed.
    - *Remedy:*  Refer to the error `ERROR: Raster could not be saved.` message.

 - **`ERROR: Raster could not be saved.`**
    - *Cause:*   The `save_rasters(self)` function of the `ModifyTerrain()` (`ModifyTerrain/cModifyTerrain.py`) or the `VolumeAssessment` class  (`VolumeAssessment/cVolumeAssessment.py`) raise this error when a terrain differences or new DEM Raster is corrupted.
    - *Remedy:*  Potential reasons for corrupted Rasters are:
        + The computed volume difference or new DEM Raster is empty or contains `NoData` pixels only. The design parameters or Raster of the concerned feature need to be reviewed.
        + The `ModifyTerrain/.cache/` folder is locked by another program. Close potential applications, and if necessary, reboot the system.
        + If `ModifyTerrain/.cache/` was not empty before the module execution, error may occur. Manually delete `ModifyTerrain/.cache/` if it still exists after a run task.
        + The directory `ModifyTerrain/Output/Rasters/CONDITION/` or `VolumeAssessment/Output/PSEUDO_CONDITION/` was deleted or it is locked by another program. Ensure that the directory exists and no other program uses `ModifyTerrain/Output/Rasters/CONDITION/` or `VolumeAssessment/Output/PSEUDO_CONDITION/` or their contents.

 - **`ERROR: Scale is not INT. Substituting scale: 2000.`**
    - *Cause:*   Raised by `get_map_scale(self)` function of the `Info()` class in either `LifespanDesign/cReadInpLifespan.py` or `MaxLifespan/cReadActionInput.py` when it cannot interpret the value assigned to the map scale.
    - *Remedy:*  Ensure that the file `mapping.inp` (in `LifespanDesign/.templates/` or `MaxLifespan /.templates/`) has a correct assignment of the map scale according to the descriptions in [*LifespanDesign* Output maps](LifespanDesign#outmaps).

 - **`ERROR: Shapefile conversion failed.`**
    - *Cause:*   Raised by `calculate_sha(self)` of [*SHArC*][6]'s `CHSI()` class in `SHArC/cHSI.py` when it could not convert the CHSI Raster to a shapefile.
    - *Remedy:*
        + Ensure that the SHArea threshold has a meaningful value between 0.0 and 1.0 ([SHArC Intro](SHArC)).
        + Ensure that neither the directory `SHArC/.cache/` nor the directory `SHArC/SHArea/` or their contents are in use by other programs.
        + Review the input settings according to [SHArC Quick GUIde](SHArC#hegui).
        + Follow up earlier error messages.

 - **`ERROR: TEMPLATE sheet does not exist.`**
    - *Cause:*   Error raised by the `make_condition_xlsx(self, fish_sn)` of the `MakeTable()` class in `.site_packages/riverpy/cMakeTable.py`) when the `template` sheet in the output (template) workbooks  `SHArC/.templates/CONDITION_sharea_template_[...].xlsx`) are corrupted.
    - *Remedy:* Ensure that `SHArC/.templates/CONDITION_sharea_template_[...].xlsx` contains the `summary` sheet and that `SHArC/.templates/empty.xlsx` is available; re-install the templates if necessary.

 - **`ERROR: The provided boundary file (%s) is invalid.`**
    - *Cause:*   Raised the [GetStarted](Signposts#getstarted) module's sub-condition creator function (`make_sub_condition` in `RiverArchitect/GetStarted/fSubCondition.py`), when the defined shapefile or Raster contains invalid data.
    - *Remedy:*  Ensure that the provided shapefile or Raster fullfils the requirements explained in the [GetStarted - Create Sub-Condition](Signposts#sub-condition) section.
    
 - **`ERROR: The Raster name is not coherent with the name conventions. Name correction needed.`**
    - *Cause:*   Error raised by the `MakeFlowTable` class (`riverpy/cMakeTable.py`) when a Raster was wrongly identified as being a flow depth Raster because of a violation of file name conventions.
    - *Remedy:* Ensure that all file names in the `01_Conditions/CONDITION/` folder follow the [file name conventions](Signposts#terms). If the *Condition* folder contains other files than flow depth and velocity *GeoTiff*s starting with the letter `h` or `u`, rename these files or remove them from the *Condition* folder.
    
 - **`ERROR: The selected folder does not contain any depth/velocity Raster containing the defined string.`**
    - *Cause:*   Error raised by the `ConditionCreator` class (`GetStarted/cConditionCreator.py`) when the defined folder does not contain any valid depth or velocity Raster.
    - *Remedy:*
        + Ensure that no other program uses the selected folder.
        + Manually / visually verify the selected folder and provided settings for creating the *Condition*.

 - **`ERROR: The source discharge file contains non-detectable formats (...).`**
    - *Cause:* The date format provided in the hydraulic habitat suitability index flow duration curve preparation file contains invalid date formats.
    - *Remedy:* Ensure that the select flow series file corresponds to the [file requirements](SHArC#input-hhsi). Use the provided example data file (`RiverArchitect/SHArC/FlowDurationCurves/flow_series_example_data.xlsx`) as template workbook for preparing flow series. The flow series workbook must be an `.xlsx` file and the dates must be contained in col. `A`, starting from row `3`. The default format is `DD-MMM-YY` (e.g., 14-June-88 for June 14<sup>th</sup>, 1988).

 - **`ERROR: u/h/hyd--Raster analysis does not accept ras_*name* Raster.`**
    - *Cause:*   Internal programming error: A parameter module called a Raster which does not match the batch processing hierarchy.
    - *Remedy:*  Move new model downward in the processing hierarchy and avoid calling an u/h/hyd--Raster with the optional argument `Raster_info`.

 - **`ERROR: Volume value assignment failed.`**
    - *Cause:*   Error raised by the `write_volumes(self, ...)` function of the `Writer()` class in `.site_packages/riverpy/cReachManager.py`) when it received invalid volume data.
    - *Remedy:*  Ensure that no other program uses `VolumeAssessment/Output/CONDITION_volume.xlsx` and traceback earlier errors (modified DEM Rasters may be corrupted).

 - **`ERROR: Writing failed.`**
    - *Cause:*   Error raised by the `write_volumes(self, ...)` function of the `Writer()` class in `.site_packages/riverpy/cReachManager.py`) when the `template` it could not add new sheets in `VolumeAssessment/Output/CONDITION_volumes.xlsx` or write to copies of `VolumeAssessment/templates/volume_template.xlsx`.
    - *Remedy:*  See error message `ERROR: Failed to create WORKBOOK`.

 - **`ERROR: Wrong format of lifespan list (.inp)`**
    - *Cause:*   Raised by `lifespan_read(self)` (in `LifespanDesign/cReadInpLifespan.py`) when the lifespan list in `01_Conditions/CONDITION/input_definitions.inp` has a wrong format or is empty.
    - *Remedy:*  Ensure that the file `01_Conditions/CONDITION/input_definitions.inp` (in `LifespanDesign/.templates/`) contains a lifespan list (return periods list) with not more than six comma-separated entries according to the definitions in the [Input definitions files of the *LifespanDesign* module](Signposts#inpfile).

 - **`ExceptionERROR: (arcpy) [...].`**
    - *Cause:*   The error is raised if any `arcpy` application of any module encountered problems; e.g., the `analysis_...` and `design_...` functions in `LifespanDesign/cLifespanDesignAnalysis.py` raise this error when Raster calculations could not be performed. Missing Rasters, bad Raster assignments or bad Raster calculation expressions are possible reasons. The error can also occur when the `SpatialAnalyst` license is not available.
    - *Remedy:*
        + Make sure that a `SpatialAnalyst` license is available.
        + Trace back previous error and warning messages.
        + Verify Raster calculation expressions in concerned`analysis_...` and `design_...` functions  (`LifespanDesign/cLifespanDesignAnalysis.py`).
        + Verify Raster definitions in concerned`analysis_...` and `design_...` functions (`LifespanDesign/cLifespanDesignAnalysis.py`).
        + Verify Raster definitions of used parameters (`cParameters.py` and input files `*.inp` according to the [Conditions / Input Rasters section](Signposts#conditions)).
        + If further system errors are stated, trace back error messages.

 - **`ExceptionERROR: Cannot find package files [...].`**
    - *Cause:*   The program cannot retrieve the listed internal files.
    - *Remedy:*  Check the installation of the package and its file structure according to the [Requirements stated in the *Introduction and Installation*](Installation#req).

 - **`ExceptionERROR: Cannot open reference (condition) ...`**
    - *Cause:*   Raised by the `ModifyTerrain()` class (`__init__(self,condition, feature_type, *args)`) in `ModifyTerrain/cModifyTerrain.py` when it cannot find a *...* Raster in `01_Conditions/CONDITION/` (or other user-defined input directory), where *...* is either a `dem.tif` or a `wt_depth_base.tif` Raster. A `wt_depth_base.tif` Raster is required for automated terrain modification after grading and/or widen features. 
    - *Remedy:*  Ensure that the missing Raster (`dem` or a `wt_depth_base`) exists in `01_Conditions/CONDITION/`, or if applies, the user-defined input directory. If no `wt_depth_base.tif` Raster is available, the terrain modification of grading and/or widen features cannot be automated. In this case, consider adding a new DEM automation function (explained in the [Add Routine section in the *ModifyTerrain* module](ModifyTerrain#addmtmod)) or modifying the DEM manually.

 - **`ExceptionERROR: Could not find base Raster for assigning lifespans.`**
    - *Cause:*   Raised by [*MaxLifespan*][4]'s `ArcpyContainer()` class (`__init__(self,condition, feature_type, *args)`) in `MaxLifespan/cActionAssessment.py` when it cannot find its zero Raster template in `MaxLifespan/.templates/Rasters/zeros.tif`.
    - *Remedy:*  Follow the instructions for the error message `ExceptionERROR: Unable to create ZERO Raster. Manual intervention required:...` to manually create the `MaxLifespan/.templates/Rasters/zeros.tif` Raster.

 - **`ExceptionERROR: Missing fundamental packages (required: ...).`**
    - *Cause:*   The listed (required) packages are not available.
    - *Remedy:*  Check installation of required packages and code structure files according to the [Requirements stated in the *Introduction and Installation*](Installation#req).

 - **`ExceptionERROR: Unable to create ZERO Raster. Manual intervention required`**
    - *Cause:*   [*MaxLifespan*][4] failed to create a zero Raster covering the computation area.
    - *Remedy:*  The Raster creation needs to be manually made in *ArcGIS Pro*'s Python interpreter (the external interpreter could not do the job and only the cuckoo from California knows why). Thus, manually create the zeros Raster as follows:
	  + Launch *ArcGIS Pro* and its implemented Python window (`Geoprocessing` dropdown menu: `Python`).
	  + Enter the following sequences (replace `REPLACE_...` according to the local environment):<br/>
		`import os`<br/>
		`from arcpy.sa import *`<br/>
		`zero_ras_str = os.getcwd() + ".templates\Rasters\zeros.tif"`<br/>
		`condition = "REPLACE_CONDITION"`<br/>
		`base_dem = arcpy.Raster("REPLACE_PATHRiverArchitectLifespanDesignInput" + condition + "dem.tif")<br/>
		`arcpy.gp.overwriteOutput = True`<br/>
		`arcpy.env.extent = base_dem.extent`<br/>
		`arcpy.env.workspace = "D:\PythonRiver\Architect\LifespanDesign\Input\" + condition + ""`<br/>
		`zero_ras = Con(IsNull(base_dem), 0, 0)`<br/>
		`zero_ras.save(zero_ras_str)`
		
	  + Close *ArcGIS Pro*

 - **`ExecuteERROR: (arcpy) [...].`**
    - *Cause:*   Similar to`ExceptionERROR: (arcpy) ...`. The error is raised by `arcpy` applications of all modules; e.g., by the `analysis_...` and `design_...` functions in `LifespanDesign/cLifespanDesignAnalysis.py` or when Raster calculations could not be performed. Missing Rasters, bad Raster assignments or bad Raster calculation expressions are possible reasons. The error can also occur when the `SpatialAnalyst` license is not available.
    - *Remedy:*  See `ExceptionERROR: (arcpy) [...]`

 - **`Internal Error: ... .`**
    - *Cause:*  Internal Error messages are raised when the code communicates erroneous data between class functions.
    - *Remedy:* 
        + If the code was modified, revise or revert changes.
        + If Internal Errors occur that are not known issues as stated in other error messages, please provide us with feedback (use the [bug report template](https://github.com/riverarchitect/program/blob/master/.github/ISSUE_TEMPLATE/bug_report.md) or send us an email: river.architect.program [at] gmail.com)

- **`OSError: ....`**
    - *Cause:*   `arcpy` raises this error for various reasons; in particular, if code was modified or the code environment is not set up properly.
    - *Remedy:*  Check the correct installation of *River Architect* and input files (refer to the <a href="Installation">Installation</a>  and <a href="Signposts">Signposts</a> pages and use the [correct Python environment](Installation#install-and-get-started)). Make sure that no other program uses files required by *River Architect*.

- **`WindowsError: [Error 32] The process cannot access the file because ...`**
    - *Cause:*   Files in the `.cache` folder or the `Output` folder are used by another program.
    - *Remedy:*
        + Make sure that *ArcGIS Pro* is not running.
        + Make sure that no other code copy (*Python*) uses these folders.

***

Warning messages
================

 - **`WARNING: .cache folder will be removed by package controls.`**
    - *Cause:*   Raised by `clear_cache(self)` of [*SHArC*][6]'s `CHSI()` class in `SHArC/cHSI.py` when it could not clear and remove the `.cache/` folder.
    - *Remedy:*  Ensure that no other software uses the temporary Rasters stored in `SHArC/.cache/`, and if necessary, delete the folder manually after quitting the module.
    
 - **`WARNING: ### is not a number.`**
    - *Cause:*   Functions raise this warning message when a `float`-number type was expected, but another, non-convertible format was provided.
    - *Remedy:*  Verify if the results are consistent. If problems occur, make sure that the provided input data contain numbers or valid `nan` formats (`NoData` for Rasters and empty cells for workbooks) only.


 - **`WARNING: Bad value ( ... ).`**
    - *Cause:*   Raised by `calculate_sha(self)` of [*SHArC*][6]'s `CHSI()` class in `SHArC/cHSI.py` when a CHSI polygon contains an invalid value.
    - *Remedy:*  Review cHSI Rasters `SHArC/CHSI/CONDITION/`.

 - **`WARNING: Cannot identify reaches.`**
    - *Cause:*   Raised by `VolumeAssessment().__init__(...)` in `VolumeAssessment/cVolumeAssessment.py` when the provided reach names are inconsistent with those listed in `ModifyTerrain/.templates/computation_extents.xlsx`.
    - *Remedy:*  Ensure that `ModifyTerrain/.templates/computation_extents.xlsx` does not contain more than eight reaches (i.e., only cells `B6:C13` contain reach names and identifiers, also see [reach preparation within the *ModifyTerrain* module](RiverReaches)).

 - **`WARNING: Cannot load ...\LifespanRasterSymbology.lyrx. `**
    - *Cause:*   Raised by `prepare_layout(...)` of the `Mapper()` (`.site_packages/riverpy/cMapper.py`) when it cannot load `/RiverArchitect/02_Maps/templates/symbology/LifespanRasterSymbology.lyrx`.
    - *Remedy:*  Ensure that `/RiverArchitect/02_Maps/templates/symbology/LifespanRasterSymbology.lyrx` exists and that the layer file is not broken (e.g., by opening the file in *ArcGIS Pro*).
    
 - **`WARNING: Cannot zoom to defined extent.`**
    - *Cause:*   Raised by the `zoom2map(...)` function of the `Mapper()` class (`.site_packages/riverpy/cMapper.py`) when it cannot interpret the provided coordinates.
    - *Remedy:*
	    + All modules: Ensure that the [`mapping.inp`](Signposts#inpfile) and the [`reach definitions`](RiverReaches) files contain valid data.
    	+ <a href="LifespanDesign">LifespanDesign</a>: Ensure that either a correct background Raster dataset was defined prior to mapping.


 - **`WARNING: computation_extents.xls contains too many reach names.`**
    - *Cause:*   Raised by `Read().get_reach_info(self, type)` in `.site_packages/riverpy/cReachManager.py` when `ModifyTerrain/.templates/computation_extents.xlsx` contains more than eight reach names in columns `B` and/or `C`.
    - *Remedy:*  Ensure that `ModifyTerrain/.templates/computation_extents.xlsx` does not contain more than eight reaches (i.e., only cells `B6:C13* contain reach names and identifiers, also see [reach preparation within the *ModifyTerrain* module](RiverReaches)).
	
 - **`WARNING: Conversion to polygon failed (FEAT).`**
    - *Cause:*   Raised by `identify_best_features(self)` in `MaxLifespan/cActionAssessment.py` when the `arcpy.RasterToPolygon_conversion(FEAT Raster)` failed (e.g., because of an empty `FEAT` Raster).
    - *Remedy:*  An empty `FEAT` Raster of best lifespans occurs when the feature has no spatial relevance. Consider other terrain modifications or maintenance features to increase the features lifespans and start over planning the feature (set).


 - **`WARNING: Could not access hydraulic Raster extents. Using MAXOF instead.`**
    - *Cause:*   Raised by the `D2W` class (`GetStarted/cDepth2Groundwater.py`) when the defined flow depth *GeoTIFF* has no valid extents.
    - *Remedy:* Manually / visually verify the provided flow depth Raster and make corrections / overwrite it if necessary.

- **`WARNING: Could not clear/remove .cache.`**
    - *Cause:*   All modules may raise this warning message when the content in the `.cache` folder was accessed and locked by another software.
    - *Remedy:*  Make sure that no other software, including *ArcGIS Pro* or `explorer.exe`, uses the `MODULE/.cache` folder.

 - **`WARNING: Could not clean up PDF map temp_pages.`**
    - *Cause:*   The `make_pdf_maps(self, map_name, *args, **kwargs)` functions of the `Mapper()` class (`.site_packages/riverpy/cMapper.py`) creates single `PDF`s of every map image (extents defined in [mapping.inp](Signposts#inpfile) or the [reach coordinates workbook](RiverReaches)). These single-page `PDF`s are finally combined into one `PDF` map assembly and the single-page `PDF`s are deleted afterward. 
    - *Remedy:*  Ensure that no other program is using the `PDF` files in `RiverArchitect/02_Maps/CONDITION/` while mapping is in progress (close *ArcGIS Pro*).

 - **`WARNING: Could not crop lifespan Raster extents to wetted area.`**
    - *Cause:*   Raised by the `ArcPyAnalysis` class (`LifespanDesign/cLifespanDesignAnalysis.py`) when it failed to crop lifespan maps (Rasters) to the extents of the depth Raster associated with the highest discharge analyzed.
    - *Remedy:*
        + Manually / visually verify the provided flow depth Rasters and make corrections / overwrite it if necessary.
        + If cropping the lifespan Raster to the wetted area of the highest discharge is not desired, apply the following Raster calculation to the highest discharge's flow depth Raster to eliminate `NoData` values (otherwise, all `NoData` pixels are excluded from the lifespan Raster):<br/>
        `Con((IsNull(hQQQQQQ) == 1), (IsNull(hQQQQQQ) * 0), Float(hQQQQQQ))`

 - **`WARNING: Could not divide [...] by [...]`**
    - *Cause:*   Raised by `calculate_relative_exceedance(self)` of [*SHArC*][6]'s `FlowAssessment()` class in `SHArC/cFlows.py` when the flow duration curve contains invalid data.
    - *Remedy:*  Ensure the correct setup of the used flow duration curve in `SHArC/FlowDurationCurves/`. The data types and file structure must correspond to that of the provided template `flow_duration _template.xlsx` and all discharge values need to be positive floats. Review the [HHSI input preparation](SHArC#hemakehsi) for details.
	
- **`WARNING: Could not find Lifespan Raster (...).`**
    - *Cause:*   Raised by the `ProjectMaker/s30_terrain_stabilization/`'s  or `ProjectMaker/s21_plantings_stabilization/`'s `main()` function when it cannot find lifespan Rasters.
    - *Remedy:*  Go to the <a href="Lifespan/Design">LifespanDesign</a> tab for the selected *Condition*. Create lifespan maps for the goup layers plantings, nature-based engineering, and connectivity. <a href="Project Maker">ProjectMaker</a> absolutely requires `Grains / Boulders` (`lf_grains.tif`), and optionally requires `Streamwood` (`lf_wood.tif`) and `nature-based engineering (other)` (`lf_bio.tif`).

 - **`WARNING: Could not get flow depth Raster properties. Setting [...]`**
    - *Cause:*   The `crop_input_Raster(self, ...)` function (`SHArC/cHSI.py`) prints this warning message when it cannot read the Raster properties from the defined input flow depth Raster.
    - *Remedy:*  Make sure that the defined flow depth Raster exists in `RiverArchitect/01_Conditions/CONDITION/`.

 - **`WARNING: Could not get minimum flow depth [...]. Setting h min [...]`**
    - *Cause:*   The `crop_input_Raster(self, ...)` function (`SHArC/cHSI.py`) prints this warning message when it could not read the minimum flow depth from `Fish.xlsx`. A default value of 0.1 (ft or m) is used to delineate relevant flow regions.
    - *Remedy:*  Make sure that the defined Fish species / lifestage is assigned a cover value and at least one flow depth value in `Fish.xlsx` according to the definitions in [CoverHSI](SHArC#hemakecovhsi).
    
 - **`WARNING: Could not identify maximum flow in flow duration curve.`**
    - *Cause:*   The `get_flow_duration_data(self, ...)` function (`riverpy/cFlows.py`) prints this warning message when it could not identify a maximum flow for interpolating flow exceedance probabilities.
    - *Remedy:*  Open `00_Flows/CONDITION/flow_duration_fili` and verify that the discharges in the first spreadsheet are correct.

 - **`WARNING:  Could not load /01_Conditions/CONDITION/back.tif - ...`**
    - *Cause:*   The `sect_extent()` function (`LifespanDesign/cLifespanDesignAnalysis.py`) prints this warning message when it could not load the `back.tif` Raster in the `CONDITION` folder. This warning message can only occur when the checkbox `Limit computation extent to background (back.tif) Raster` is activated.
    - *Remedy:*  Make sure that there is a `back.tif` Raster in the `CONDITION` folder. Otherwise, uncheck the checkbox, but using a background Raster `back.tif` is strongly recommended.

 - **`WARNING: Could not reset styles.`**
    - *Cause:*   Raised by `Write().write_volumes(self, ...)` in `.site_packages/riverpy/cReachManager.py` when the `template` sheet in the output (template) workbook (`VolumeAssessment/Output/CONDITION_volumes.xlsx` or `VolumeAssessment/.templates/volume_template.xlsx`) is either locked or not accessible.
    - *Remedy:*  Ensure that no other program uses `VolumeAssessment/Output/CONDITION_volumes.xlsx` or `VolumeAssessment/.templates/volume_template.xlsx` and that both workbooks have not been accidentally deleted.

 - **`WARNING: Could not read project area extents.`**
    - *Cause:*   Raised by `SHArC.get_extents(self, ...)` in `ProjectMaker/cSHArC.py` when the function failed to read the project area extents from the `ProjectArea.shp` shapefile.
    - *Remedy:*  Ensure that the `ProjectArea.shp` shapefile is correctly created (in particular the *Attributes Table*), according to [Project Area Polygon preparation](ProjectMaker#pminp2).

 - **`WARNING: Could not remove .cache folder.`**
    - *Cause:*   Raised by multiple modules, if deleting the temporary `.cacheXXXXXXX` folder failed.
    - *Remedy:*  Ensure that no other program uses the cache folder and delete exiting `.cache` folders in the concerned modules manually.	

 - **`WARNING: Could not set project area extents ().`**
    - *Cause:*   Raised by `SHArC().set_env(self)` in `/ProjectMaker/cSHArC.py` when the function failed to set project area extents.
    - *Remedy:*  Occurs when the CHSI Raster associated with a certain discharge is empty. Ignore this Warning if the CHSI Raster was correctly identified as being empty, otherwise, revise CHSI Raster creation with the [*SHArC*][6] module.		

 - **`WARNING: Design map - Could not assign frequency threshold. [...]`**
    - *Cause:*   Design maps, such as stable grain size, refer to hydraulic data related to a defined return period. If`design_...` functions ) `LifespanDesign/cLifespanDesignAnalysis.py`) cannot identify a particular`threshold_freq` value,`design_...` functions automatically try to use hydraulic data related to the first entry of `lifespans* (`Return periods` entry in `01_Conditions/CONDITION/input_definitions.inp`, see the [Input definitions files of the *LifespanDesign* module](Signposts#inpfile)).
    - *Remedy:*
        + Assign a float value to the concerned feature in the `Mobility frequency threshold` row of the `LifespanDesign/.templates/threshold_values.xlsx` spreadsheet (see also [Modify Threshold Values within the *LifespanDesign* module](LifespanDesign#modthresh)).
	    + Make sure that the defined defined `Mobility frequency threshold* float is consistent with the defined `Return periods` in `01_Conditions/CONDITION/input_definitions.inp` (see the [Input definitions files of the *LifespanDesign* module](Signposts#inpfile)).

 - **`WARNING: Empty design Raster [...]`**
    - *Cause:*   The analyzed feature is not applicable in the defined range.
    - *Remedy:*
        + If the feature is not intended to be applied anyway, ignore the warning message.
        + If the feature is intended to be applied, manual terrain modifications adapting the feature's threshold values may be necessary.

 - **`WARNING: Empty lifespan Raster [...]`**
    - *Cause:*   The analyzed feature is not applicable in the defined range.
    - *Remedy:*
        + If the feature is not intended to be applied anyway, ignore the warning message.
        + If the feature is intended to be applied, manual terrain modifications adapting the feature's threshold values may be necessary.

 - **`WARNING: Failed to align input raster [...].`**
    - *Cause:*   Raised by `ConditionCreator().fix_alignment` in `GetStarted/cConditionCreator.py` when it could not align the stated raster.
    - *Remedy:*  Verify if the stated Raster contains invalid values (exists). Complex filenames that do not comply with the *River Architect* [filename convention](Signposts#terms) may also cause this error. Rename all files with the `Tools/rename_files.py` script (see inline code comments for instructions) to adapt all files to the *River Architect* [filename convention](Signposts#terms) and re-run `Align Rasters` (if required).

 - **`WARNING: Failed to arrange worksheets.`**
    - *Cause:*   Raised by `Write().write_volumes(self, ...)` in `.site_packages/riverpy/cReachManager.py` when it could not bring to the front the latest copy of the `template` sheet in the output (template) workbook (`VolumeAssessment/Output/CONDITION_volumes.xlsx` or `VolumeAssessment/.templates/volume_template.xlsx`), which contains the calculation results.
    - *Remedy:*  Traceback earlier error and warning messages. Ensure that no other program uses `VolumeAssessment/Output/CONDITION_volumes.xlsx` or `VolumeAssessment/.templates/volume_template.xlsx` and that both workbooks have not been accidentally deleted.

 - **`WARNING: Failed to write unit system to worksheet.`**
    - *Cause:*   Raised by `Write().write_volumes(self, ...)` in `.site_packages/riverpy/cReachManager.py` when it could not write volume (numbers) to a copy of the `template` sheet in the output (template) workbook (`VolumeAssessment/Output/CONDITION_volumes.xlsx` or `VolumeAssessment/.templates/volume_template.xlsx`).
    - *Remedy:*  Traceback earlier error and warning messages. Ensure that no other program uses `VolumeAssessment/Output/CONDITION_volumes.xlsx` or `VolumeAssessment/.templates/volume_template.xlsx` and that both workbooks have not been accidentally deleted.
	
 - **`WARNING: Flow_duration[...].xlsx has different lengths of [...]"`**
    - *Cause:*   Raised by `get_flow_data(self, *args)` of [*SHArC*][6]'s `FlowAssessment()` class in `SHArC/cFlows.py` when the flow duration curve contains invalid data.
    - *Remedy:*  Ensure that columns `B` and `C` of the flow duration curve workbook have the same length (in particular the last value/row must be the same) and check for empty cells.

 - **`WARNING: Identification failed (FEAT).`**
    - *Cause:*   Raised by `identify_best_features(self)` in `MaxLifespan/cActionAssessment.py` when the analyzed feature cannot be matched with the internal best lifespan Raster.
    - *Remedy:*  Features with very low lifespan may result in empty Rasters. Consider other terrain modifications or maintenance features to increase the features lifespans and start over planning the feature (set).
    
 - **`WARNING: Invalid curve data (Fish.xlsx): PAR= ... , HSI= ... .`**
    - *Cause:*   Raised by `HHSI().nested_con_raster_calc(self, ...)` in `SHArC/cHSI.py` when the *HSI* curve data provided  in `.site_packages/templates/Fish.xlsx` are non-numeric or otherwise invalid.
    - *Remedy:* 
        + Ensure that *Physical Habitats* in `Fish.xlsx` are correctly defined according to the [definitions](SHArC#hefish).
        + Ensure that the curve data in `Fish.xlsx` are suitable numeric values for linear interpolation.

 - **`WARNING: Invalid feature names for column headers.`**
    - *Cause:*   Raised by `Write().write_volumes(self, ...)` in `.site_packages/riverpy/cReachManager.py` when it could not write feature names to a copy of the `template` sheet in the output (template) workbook (`VolumeAssessment/Output/CONDITION_volumes.xlsx` or `VolumeAssessment/.templates/volume_template.xlsx`).
    - *Remedy:* 
        + Ensure that `ModifyTerrain/.templates/computation_extents.xlsx` contains valid reach descriptions ([reach preparation within the *ModifyTerrain* module](RiverReaches)).
        + Ensure that no other program uses `VolumeAssessment/Output/CONDITION_ volumes.xlsx` or `VolumeAssessment/.templates/volume_template.xlsx` and that both workbooks have not been accidentally deleted.
	
 - **`WARNING: Invalid alignment Raster name ([...]).`**
    - *Cause:*   Raised by `ConditionCreator().fix_alignment(self, ...)` in `GetStarted/cConditionCreator.py` when it could not open the stated raster.
    - *Remedy:*  Complex filenames that do not comply with the *River Architect* [filename convention](Signposts#nameconvention) may also cause this error. Rename all files with the `Tools/rename_files.py` script (see inline code comments for instructions) to adapt all Raster filenames to the *River Architect* [filename convention](Signposts#terms) and re-run `Align Rasters` (if required).

 - **`WARNING: Invalid type assignment -- setting reach names to IDs.`**
    - *Cause:*   Raised by `Read().get_reach_info(self, type)` in `.site_packages/riverpy/cReachManager.py` when The `type` argument is not`full_name* or`Id`. In this case, the [*ModifyTerrain*][5] module uses column `C` in `ModifyTerrain/.templates/computation_extents.xlsx` for reach names and IDs.
    - *Remedy:*  This warning message only occurs if the GUI application was changed or when the [*ModifyTerrain*][5] module is externally called with bad argument order. Review the argument order/assignments in the external call and ensure that The `type* variable is in the `allowed_types = ["full_name", "id"]` list.

 - **`WARNING: Invalid unit_system identifier.`**
    - *Cause:*  Raised by `ModifyTerrain.__init__()` ( `ModifyTerrain/cModifyTerrain.py`) or the `VolumeAssessment.__init__()` ( `VolumeAssessment/cVolumeAssessment.py`) when the unit system identifier is not either `us` or `si`. The program will use the default unit system (*U.S. customary*).
    - *Remedy:*  This warning message only occurs if the GUI application was changed or when the [*ModifyTerrain*][5] module is externally called with bad argument order. Review the argument order/assignments in the external call `var = mt.ModifyTerrain(condition=..., unit_system=..., ...)`.

 - **`WARNING: Merge operation failed (empty shapefiles?).`**
    - *Cause:*   Raised by the `ProjectMaker/s30_terrain_stabilization/`'s `main()` function when the nature-based engineering and Angular Boulder shapefiles for stabilizing the terrain failed.
    - *Remedy:*  One or both stabilization shapefiles (`ProjectMaker/ProjectName/Geodata/Shapefiles/Terrain_stab.shp` or `.../Terrain_boulder_stab.shp`) may be empty. Check source data or consider to change the user-defined requried critical lifespan.

 - **`WARNING: No Lifespan / Design Raster found (...).`**
    - *Cause:*   Raised by the `MaxLifespan`'s `Director` class (`MaxLifespan/cFeatureActions.py`) when it cannot find any valid lifespan or design Raster for a condition.
    - *Remedy:*  Make sure to run the [*LifespanDesign*][3] module for at least one feature within the selected group for a condition. If necessary, verify the contents of lifespan Rasters in `LifespanDesign/Output/Rasters/CONDITION/` (e.g., empty Rasters and Raster names must contain `lf` or `ds` to be recognized).

 - **`WARNING: Non-numeric values in data.`**
    - *Cause:*   Raised by the interpolation functions of the `Interpolator` class (`.site_packages/riverpy/cInterpolator.py`) when the x data points that should get an interpolated y-value are not numeric.
    - *Remedy:*  Check the condition flow duration and/or time duration curve and remove any non-numeric value from the discharge columns.
    
 - **`WARNING: Old logfile is locked [...].`**
    - *Cause:*   Raised by the `logging_start(logfile_name)` function (multiple classes) when the logfiles are locked by another process. The parenthesis `[...]` indicates the concerned run task.
    - *Remedy:*  Ensure that the logfiles of the concerned module are not opened in any other process or program.
	
 - **`WARNING: PlantExisting.shp is corrupted or non-existent.`**
    - *Cause:*   Raised by the `ProjectMaker/s20_plantings_delineation/`'s `main()` function when it could not process the existing plants shapefile.
    - *Remedy:*  Ensure that existing plants (`ProjectMaker/ProjectName/Geodata/Shapefiles/PlantExisting.shp`) is correctly set up [according to the descriptions in the wiki](ProjectMaker#pminp31). However, this raster is not absolutely required.

 - **`WARNING: Substituting user-defined crit. lifespan (...) with ....`**
    - *Cause:*   Error raised by the `ProjectMaker/s30_terrain_stabilization/`'s `main()` function when the user-defined critical lifespan for terrain stabilization does not exaclty correspond to the available hydraulic Rasters defined for the provided *Condition*.
    - *Remedy:*  Ensure to only use lifespans defined for the provided *Condition* ([cf. definition of flow duration periods](Signposts#ana-flows)).

 - **`WARNING: The provided path to Rasters for mapping is invalid. Using templates instead.`**
    - *Cause:*   Raised by the `Mapper()` class in `.site_packages/riverpy/cMapper.py` when it could not process the provided input Raster path.
    - *Remedy:*  If code changes were made, ensure that `Mapper()` received correct `CONDITION` and `map_type` arguments. Otherwise, `Mapper()` will use the template Raster files located in `RiverArchitect/02_Maps/templates/Rasters/`.
	
 - **`WARNING: Volume value assignment failed.`**
    - *Cause:*   Raised by `Write().write_volumes(self, ...)` in `.site_packages/riverpy/cReachManager.py` when it could not write volume (numbers) to a copy of the `template` sheet in the output (template) workbook (`VolumeAssessment/Output/CONDITION_volumes.xlsx` or `VolumeAssessment/.templates/volume_template.xlsx`).
    - *Remedy:*  Traceback earlier error and warning messages. Ensure that no other program uses `VolumeAssessment/Output/CONDITION_volumes.xlsx` or `VolumeAssessment/.templates/volume_template.xlsx` and that both workbooks have not been accidentally deleted.


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
[sourcecode]: https://github.com/riverarchitect/program/archive/master.zip
[wyrick14]: https://www.sciencedirect.com/science/article/pii/S0169555X14000099
