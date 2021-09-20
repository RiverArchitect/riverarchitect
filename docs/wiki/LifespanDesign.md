Feature lifespan and design assessment
======================================

***

- [**Introduction to lifespan and design mapping**](#lfintro)
- [**Quick GUIde to lifespan and design maps**](#lfgui)
  * [Interface and choice of features](#interface-and-choice-of-features)
  * [Input: Condition and preparation of Rasters](#inpras)
  * [Input: Modify threshold values](#modthresh)
  * [Input: Optional arguments](#lfinopt)
  * [Run](#run)
  * [Alternative run options](#lfrun)
  * [Output](#output)
- [Parameter hypotheses](LifespanDesign-parameters)
- [River design and restoration features](River-design-features)
- [Code extension and modification](LifespanDesign-code)

***

# Introduction to lifespan and design mapping <a name="lfintro"></a>

Survival thresholds applied to a sequence of habitat enhancement features can be spatially compared with hydraulic and sediment data as a result of 2D numerical modeling. Modeled discharges (flows) can be associated with flood return periods that determine feature lifespans. The resulting lifespan maps indicate the temporal stability of particular [river design features](River-design-features) and techniques. Areas with particularly low or high lifespans help planners optimize the design and positioning of features. Moreover, discharges related to specific flood return periods enable probabilistic estimates of the longevity of particular features. Following these procedures described by [Schwindt et al. (2019)][schwindt19] ([open access factsheet-version](https://www.sciencedirect.com/science/article/pii/S2215016119300913/pdfft?md5=0609592e5beae22d0fc68adb409129f8&pid=1-s2.0-S2215016119300913-main.pdf)), the *LifespanDesign* module creates `Raster`s, projects (`aprx`), and maps (`pdf`) of the following types:

-   **Lifespan maps** qualitatively indicate areas where features make sense and the associated feature lifetime estimate in years.

-   **Design maps** indicate dimensional requirements for achieving the success of a feature (e.g., the minimum required [log diameter for the stability of wood / LWM](https://github.com/RiverArchitect/RA_wiki/wiki/River-design-features#elj)).

This Wiki page explains the usage of the *LifespanDesign* module and it is structured as follows:

 * A [Quick Guide](#lfgui) to the application of the code using GUI with descriptions of required input Rasters and alternative launch options.
 * [Physical explanations of relevant parameters](LifespanDesign-parameters).
 * [Explanations of hypotheses in the design of river modification and restoration features](River-design-features).
 * [Coding conventions with descriptions of extension possibilities](LifespanDesign-code).


# Quick GUIde to lifespan and design maps<a name="lfgui"></a>

***

## Interface and choice of features

After successful [Installation][1] and the creation of at least one [*Condition*](Signposts#new-condition), lifespan and design maps can be created from the *Lifespan* -> *LifespanDesign* tab.

![lfgui](https://github.com/RiverArchitect/Media/raw/master/images/gui_start_lf.PNG)

To begin with lifespan/design mapping, click on the drop-down menu "Add Features" and select relevant features. Multiple selection is possible and will extend the "Selected features" list. The *LifespanDesign* module enables the selection of the feature groups of ["terraforming" (framework)](River-design-features#featoverview), ["vegetation plantings"](River-design-features#plants), ["other nature-based engineering"](River-design-features#bioeng) and ["connectivity / maintenance"](#featoverview). 

## Input: Condition and preparation of Rasters<a name="inpras"></a>
The names of input Raster files are defined in a proper file format (*.inp*), which can be changed directly from the GUI button "Modify Raster input". The *.inp* files indicate after the `#` if it requires a single Raster name only (`STRING`) or a list of Rasters (min. two Rasters, `LIST`). _The extension **.tif** is not required for in the Raster names._<br/>
The maximum number of hydraulic Rasters is unlimited. The lifespans related to the hydraulic Rasters are also defined in the [separate *.inp* file](Signposts#inpfile). The [Get Started](Signposts#inpfile) module provides routines for setting up input files that must be stored as `RiverArchitect/01_Conditions/CONDITION/input_definitions.inp` for every [*Condition*](Signposts#conditions).<br/>
Modifications of [map extents](Signposts#inpmaps) can be made by clicking on the "Modify map extent" button or (un-)check the `Limit computation extent to background (back.tif) Raster` box.


## Input: The threshold values workbook `threshold_values.xlsx` and calculation hierarchy<a name="modthresh"></a>

The "Modify survival threshold values" button opens the master workbook containing threshold values and survival identifiers (location: `LifespanDesign/.templates/threshold_values.xlsx`).
![thresholds](https://github.com/RiverArchitect/Media/raw/master/images/threshold_values_illu.png)

Any threshold value can be changed or defined for any feature, but the workbook structure may not be modified (i.e., cells, columns or rows may not be shifted, moved or deleted). The unit system (U.S. customary or SI metric) in the threshold values spreadsheet are independent of the GUI settings but they need to be coherent with the input Rasters of the [*Condition*](Signposts#new-condition).

*River Architect* automatically identifies defined threshold values for selected features. Moreover, *River Architect* automatically applies all defined threshold values to the extent of Rasters available within a [*Condition*](Signposts#new-condition). The identification and execution of possible analyses follow a strictly hierarchical order. If an analysis cannot be executed because of missing threshold value definitions or Rasters, *River Architect* automatically proceeds to the hierarchically next lower analysis. The analysis hierarchy is defined in order to first created lifespan maps (if row 24 in `threshold_values.xlsx` is set to *TRUE* for a feature), and second to save design maps (if row 25 in `threshold_values.xlsx` is set to *TRUE* for a feature).
When defining threshold values in `threshold_values.xlsx` carefully study the following **hierarchy** and parameter application of *River Architect* ([read more about **threshold application to features**](River-design-features)):

1. **Dimensional hydraulic parameter** analysis:
   - **Flow depth** starting with the lowest discharge to the highest discharge Raster (`hQQQQQQ_QQQ.tif`). A threshold value for the flow depth above which a feature will fail can be defined in row 12 in `threshold_values.xlsx`.
   - **Bed shear stress**  &tau;<sub>b</sub> calculated as<br/>
	   `ras_tb` = \{\[`uQQQQQQ_QQQ` / (5.75 * Log<sub>10</sub>(12.2 · `hQQQQQQ_QQQ` / (2 · 2.2 · `dmean`)))\]<sup>2</sup>\} <br/>
	   where
   	+ A threshold value for mobility according to the bed shear stress &tau;<sub>\b, cr</sub> can be defined in row 6 of `threshold_values.xlsx` (read more for example in [Lamb et al. 2008](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2007JF000831))
   	+ &rho;<sub>w</sub> = water density (1000 kg / m<sup>3</sup>) 
   	+ `uQQQQQQ_QQQ` (m/s or fps), `hQQQQQQ_QQQ` (m or ft), and `d84` = 2.2 · `dmean` (m or ft) are `arcpy.Raster()`s considering that the grain diameter *D<sub>84</sub>* can be approximated by *D<sub>84</sub>* = 2.2 · *D<sub>50</sub>* ([Rickenmann and Recking 2011](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2010WR009793))
   	+ *g* = gravitational acceleration (9.81 m/s<sup>2</sup>)
   	+ *s* = ratio of sediment grain and water density (2.68)
   	+ Note that the &tau;<sub>b</sub> analysis is **omitted if *SF* is defined**, which enables to run either a &tau;<sub>b</sub> analysis OR a mobile grain analysis.
   - **Flow velocity** starting with the lowest discharge to the highest discharge Raster (`uQQQQQQ_QQQ.tif`). A threshold value for the velocity above which a feature will fail can be defined in row 13 in `threshold_values.xlsx`.

1. **Dimensionless hydraulic parameter** analysis:
   - **Dimensionless bed shear stress**  &tau;<sub>\*</sub> calculated as<br/>
	   `ras_taux` = \{&rho;<sub>w</sub> · \[`uQQQQQQ_QQQ` / (5.75 * Log<sub>10</sub>(12.2 · `hQQQQQQ_QQQ` / (2 · 2.2 · `dmean`)))\]<sup>2</sup>\} / \[&rho;<sub>w</sub> · *g* (*s* - 1) · `dmean`\] <br/>
	   where
   	+ A threshold value for mobility according to the critical dimensionless bed shear stress &tau;<sub>\*, cr</sub> can be defined in row 7 of `threshold_values.xlsx` (read more for example in [Lamb et al. 2008](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2007JF000831))
   	+ &rho;<sub>w</sub> = water density (1000 kg / m<sup>3</sup>) 
   	+ `uQQQQQQ_QQQ` (m/s or fps), `hQQQQQQ_QQQ` (m or ft), and `d84` = 2.2 · `dmean` (m or ft) are `arcpy.Raster()`s considering that the grain diameter *D<sub>84</sub>* can be approximated by *D<sub>84</sub>* = 2.2 · *D<sub>50</sub>* ([Rickenmann and Recking 2011](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2010WR009793))
   	+ *g* = gravitational acceleration (9.81 m/s<sup>2</sup>)
   	+ *s* = ratio of sediment grain and water density (2.68)
   	+ Note that the &tau;<sub>\*</sub> analysis is **omitted if *SF* is defined**, which enables to run either a &tau;<sub>\*</sub> analysis OR a mobile grain analysis.
   - **Froude number** *Fr* as<br/>
	      `ras_Fr` = `uQQQQQQ_QQQ` / (*g* · `hQQQQQQ_QQQ`)<sup>1/2</sup>
   	+ A threshold value for mobility according to the Froude number can be defined in row 13 of `threshold_values.xlsx`
   - **Mobile grains** (bed mobility) `ras_Dcr`, fine sediment `ras_Dcf` size Rasters as:<br/>
	      `ras_Dcx` =  =  *SF* · `uQQQQQQ_QQQ`<sup>2</sup> · *n*<sup>2</sup> / \[(*s* - 1) · `hQQQQQQ_QQQ`<sup>1/3</sup> · &tau;<sub>\*, cr</sub> \]
	      where
   	+ &tau;<sub>\*, cr</sub> is the critical dimensionless bed shear stress (i.e., threshold value) above which sediment is mobile (read more for example in [Lamb et al. 2008](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2007JF000831)). &tau;<sub>\*, cr</sub> can be defined in row 6 of `threshold_values.xlsx`.
   	+ *n* is [Manning\'s *n*][manningsn] in s/m<sup>1/3</sup> (or  s/ft<sup>1/3</sup> - an internal conversion factor of k = 1.49 applies), which can be changed in the *LifespanDesign* GUI
   	+ *SF* is a dimensionless safety factor that can be defined within *threshold_values.xlsx*; the [angular boulders / grains](River-design-features#rocks) threshold definitions indicate the application of a safety factor of 1.3. The Mobile Grain analysis is **omitted if *SF* is not defined**, which enables to run either a &tau;<sub>\*</sub> analysis OR a mobile grain analysis.
   	+ *Note that a Mobile Grain analysis will only work if a safety factor is defined in row 19 of threshold\_values.xlsx.*

1. **Topographic change Rasters** `tcd` are applied to limit lifespan Rasters to regions where the `fill` and `scour` threshold values defined in rows 22 and 23 of `threshold_values.xlsx`, respectively, are exceeded. The "Topographic change: inverse relevance" threshold applies when the feature relevance refers to regions where the scour and fill rates below the specific threshold values are relevant. By default, features such as angular boulders (rocks or riprap) are relevant where the topographic change rate (scour) exceeds the angular boulder's threshold value for scour. However, features such as grading or side cavities, are relevant where the scour or fill rates do not exceed the threshold rates because these areas are presumably disconnected from the river. Thus, "Topographic change: inverse relevance" is `TRUE` for the grading, side cavity, and side channel features.

1. A **Morphological Unit** Raster as produced with the [GetStarted](Signposts#getstarted) module according to [Wyrick and Pasternack 2014][wyrick14] can be used to limit lifespan mapping to morphologically reasonable regions. For example, [grading](River-design-features#grading) of bedrock units is not reasonable and the default `threshold_values.xlsx` excludes `bedrock` in row 16. *River Architect* enables the application of limit morphological units with an exclusive and an inclusive method:
	+ If the exclusive method is chosen (set row 18 in `threshold_values.xlsx` to `0`), *River Architect* will look for morphological units listed in row 16 and it will set pixels with these morphological units to `NoData` in lifespan maps.
	+ If the inclusive method is chosen (set row 18 in `threshold_values.xlsx` to `1`), *River Architect* will look for morphological units listed in row 17 and it will set pixels that are not within these morphological units to `NoData` in lifespan maps.
	+ Morphological units can be entered as a comma-separated list in row 16 and 17 of `threshold_values.xlsx` corresponding to the settings made during the [morphological unit Raster creation](Signposts#mu) (morphological units are defined in `RiverArchitect/.site_packages/templates/morphological_units.xlsx`.

1. **Side channel** delineation work similar to morphological unit delineation and will only be executed if the *Condition* folder contains a Raster called `sidech` (or otherwise named according to the [input file](Signposts#inpfile) in line17). The side channel delineation Raster should only contain Integer values of `1` indicating pixels where a side channel may be drawn. There is no side channel threshold value.

1. The **Depth to the water table** table (see `d2w.tif` Raster creation with the [GetStarted](Signposts#make-depth-to-groundwater-rasters) module) is particularly important for [vegetation plantings](River-design-features#plants) or [grading](River-design-features#grading) (to make terrain suitable for vegetation plantings) features. Threshold values for a lower and an upper limit of the depth to the water table value are defined in row 7 and row 8 of `threshold_values.xlsx`, respectively. *River Architect* will set all areas (pixels) that are not within the value range defined in row 7 and row 8 to `NoData` in lifespan (and design) maps. Leave both rows empty to avoid depth to water table-limited lifespan analyses.

1. The **Detrended DEM** threshold values (see `dem_detrend.tif` Raster creation with the [GetStarted](Signposts#make-detrended-dem-rasters) module) may be important to limit terraforming features, such as [widening/berm setbacks](River-design-features#berms) to economically reasonable ranges. Threshold values for a lower and an upper limit of the detrended DEM are defined in row 9 and row 10 of `threshold_values.xlsx`, respectively. *River Architect* will set all areas (pixels) that are not within the value range defined in row 9 and row 10 to `NoData` in lifespan (and design) maps. Leave both rows empty to avoid detrended DEM-limited lifespan analyses.

1. **Nature-based engineering in terms of [angular boulders](River-design-features#rocks) or [streamwood](River-design-features#elj) are applied to areas (pixels)** where a Frequency threshold (row 15 in `threshold_values.xlsx`) is defined.

1. **Other nature-based engineering** than angular boulders or streamwood is applied where the terrain is steep and as a function of depth-to-groundwater (baseflow level). *River Architect* uses the **Terrain Slope threshold value**s defined in row 20 of `threshold_values.xlsx` to identify areas (pixels) where other nature-based engineering is required. The **Depth to water table** thresholds are used to differentiate between vegetative and mineral nature-based engineering. *River Architect* applies nature-based engineering such as fascines or geotextile between the **(min)** value in row 7 and the **(max)** value in row 8. Regions with at terrain slope above the threshold defined in row 20 and above the maximum Depth to the water table defined in row 8 get mineral nature-based engineering (such as rock paving or riprap) assigned. The differentiation is made because nature-based engineering features may dry out when the water table is too far away (vertically).

1. **Design maps** indicating the stability of grains (sediment) or wood (logs) extracted after the generation of all above-listed lifespan maps (i.e., design mapping is at the bottom of the hierarchy). Thus, design mapping makes sense for features where grain stability is relevant (including [angular boulders](River-design-features#rocks), [backwater zones](River-design-features#backwtr), [grading](River-design-features#grading), [gravel/sediment augmentation](River-design-features#gravel), and [side channel creation](River-design-features#sidechnl)) and for the [streamwood](River-design-features#elj) feature.
   - Set **row 25 to TRUE**
   - For **stable grain size design maps**, make the following definitions for a feature in `threshold_values.xlsx`: 
   	+ critical dimensionless bed shear stress &tau;<sub>\*, cr</sub> in row 6
   	+ frequency threshold in years in row 15 to define the minimum expected lifespan that is required; *River Architect* uses hydraulic parameter rasters (`hQQQQQQ_QQQ` and `uQQQQQQ_QQQ`) corresponding to the return period defined within the [GetStarted](Signposts#ana-flows) module ([read more on the calculation of stable grain sizes](River-design-features#rocks)).
   	+ optional: set a required maximum grain size (e.g., to ensure the filter stability of sand for [increasing the soil capilarity](River-design-features#finesed) for vegetation plantings, the default value for the *Incorporation of fine sediment* feature in column *S* is set to 2.6 cm corresponding to 0.00667 in)
   - For **stable wood log design maps**, make the following definitions for a feature in `threshold_values.xlsx`: 
   	+ flow depth in row 11 (in m or ft)
   	+ Froude number in row 13 (dimensionless)
   	+ frequency threshold in years in row 15 to define the minimum expected lifespan that is required; *River Architect* uses hydraulic parameter rasters (`hQQQQQQ_QQQ` and `uQQQQQQ_QQQ` for the flow depth and Froude number calculation) corresponding to the return period defined within the [GetStarted](Signposts#ana-flows) module ([read more on the calculation of stable wood log sizes](River-design-features#elj)).

More information on threshold values is provided in the [Feature](River-design-features) descriptions with detailed discussions of the identifiers and threshold values.


## Input: Optional arguments<a name="lfinpopt"></a>

The checkbox "Include mapping after Raster preparation" provides the optional automated [mapping of results](#outmaps).<br/>
The checkbox "Apply wildcard Raster to spatially confine analysis" can be checked to use a *Condition*'s `wild.tif` Raster for spatial limitation of the results. This application makes sense for example if the wildcard Raster contains particular land parcels, where the owner wants to foster habitat enhancement.<br/>
The checkbox "Apply habitat matching" provides the option of habitat matching to regions where the habitat suitability index is low (<0.5, see explanations in the [SHArC][6] module.<br/>
Switching between unit systems (U.S. customary or SI - metric) is possible via the drop-down menu "Units"; please note that the unit system needs to be consistent with all input Raster files.<br/>
[Manning\'s *n*][manningsn] (in s/m<sup>1/3</sup>) is used in the grain mobility analysis ([Angular boulder feature descriptions](River-design-features)) to determine shear velocity that acts on grains. The default value is 0.0473934 s/m<sup>1/3</sup> (the GUI only shows the first three decimal places), which corresponds to a global optimum in the sample case (gravel-cobble bed river). Even if the unit system is set to U.S. customary, Manning's *n* is defined in the GUI in SI-metric units (an internal conversion factor of *k* = 1.49 (i.e., *n* / *k* is automatically applied for U.S. customary unit settings). The logfiles (produced during the program execution) will state the applied Manning's *n* value if used.

***

## Run<a name="lfrungui"></a>

Once all inputs are defined, click on "Run" (drop-down menu) and "Verify settings" to ensure the consistency of the settings (the window will freeze for some seconds). After successful verification, the selected options change to green font.<br/>
The "Run" drop-down menu provides the following functions:

-   `Raster Maker` prepares lifespan and design Rasters in the directory `RiverArchitect/LifespanDesign/Output/Rasters/CONDITION/`

-   `Map Maker` prepares project maps and *PDF* assemblies in the directory `RiverArchitect/02_Maps/CONDITION/`;<br/>
	Before running `Map Maker`, ensure that the correct background image (`01_Conditions/CONDITION/back.tif`) is linked in the project template file `RiverArchitect/02_Maps/templates/river_template.aprx`.<br/>
	 	The mapping extents can be modified using the [`mapping.inp` input file](Signposts#inpmap) and the [Mapping](Mapping) Wiki explains how the symbology, layouts, and other extent settings may be modified.

Either "Run" option causes a run confirmation window popping up and clicking "OK" calls the analysis, which will run in the background Python window and it freezes the GUI windows. Running the `Raster Maker` may take 0.1 to 10 hours, depending on the input Raster size, feature set and habitat matching options.<br/>
After the analysis, the GUI unfreezes and a new button invites to read the logfiles with run information, as well as error and warning messages that may have occurred during the analysis.<br/>
Alternatively, the lifespan mapping functions can be imported in other *Python* applications (without the GUI) as described in the following [Alternative Run options](#lfrun).

***

## Alternative run options<a name="lfrun"></a>

The three run options of the GUI call the following methods:

1.  `Raster Maker` calls `feature_analysis.raster_maker` for the preparation of Rasters in the directory `Output/Rasters/CONDITION/`

1.  `Map maker` calls `feature_analysis.map_maker` for the preparation of an *ArcGIS Pro* project (*aprx*) file and maps assembled in `pdf`s in the directory `RiverArchitect/02_Maps/CONDITION/`; by default the layouts stored in `RiverArchitect/02_Maps/CONDITION/` underlie the `pdf` creation but the method also accepts other input directories as an optional argument. *Please note that directories always need to be **absolute**; relative paths will result in errors.*

The alternative run options are relevant for example to batch process several [*Conditions*](Signposts#conditions). The first alternative run option is to import the *LifespanDesign* module in the *ArcGIS Pro*s Python environment as follows:

1.  Prepare input data in `.../01_Conditions/CONDITION/` and adapt the background layer image datasets in `RiverArchitect/02_Maps/templates/river_template.aprx`

1.  Go to *ArcGIS Pro*s Python folder and double-click one of the following:<br/>
    `C:\Program Files\ArcGIS\Pro\bin\Python\scripts\propy.bat` or<br/>
    `C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe`

1.  Enter `import os`

1.  Navigate to the script direction using the command `os.chdir("ScriptDirectory")`<br/>
    Example: `os.chdir("D:/Python/RiverArchitect/LifespanDesign/")`

1.  Import the module: `import feature_analysis as fa`

Once the module is imported three methods are available and their use is intended in the following order:

1.  `fa.raster_maker("condition", ∗args)` for Raster (*GeoTIFF*) creation

1.  `fa.map_maker("condition", ∗args)` for map (`pdf`) creation

The following steps illustrate the application for creating Rasters.

-   Basic execution: `fa.raster_maker("condition")`, for example: `fa.Raster_maker("2008_rrr")`

-   The code is now running (this takes two to four hours) and it will prompt its activities.

-   Alternatively, the analysis can be limited to some features only (count 2 to 60 minutes per feature for input Raster sizes of 5MB and 1GB, respectively). `fa.raster_maker("condition", ∗args)` accepts optional arguments that are `feature_list`, which enables the analysis of any feature listed in the [Features](#features) section. Some examples for particular applications:<br/>
    -> Example 1: `fa.raster_maker("condition", ["Plantings"])` analyzes plantings only.<br/>
    -> Example 2: `fa.raster_maker("condition", ["Plantings", "Boulders/rocks"], True)`analyses plantings and angular boulders (rocks / riprap) only with an optional argument that activates the creation of layouts for plantings and angular boulders (rocks).<br/>
    -> Example 3: `fa.raster_maker("2008_rrr")`analyses all available [features](#features).

-   The complete list of optional arguments of is as follows:<br/>
    *Hint: Respecting the order of optional arguments is crucial to ensure proper application of the desired analysis options.*

    - `args[0] = feature_list` as above described.

    - `args[1] = mapping`, which can be `True` or `False` (default).

    - `args[2] = habitat_analysis`, which can be `True` or `False` (default) for activating or deactivating
        habitat delineation (limitation) of restoration features to zones with low habitat suitability (e.g., `cHSI` = 0.0 to 0.5).

    - `args[3] = habitat_radius` is a `float` number determining in what distance to low habitat suitability zones restoration features should be applied (default = 400.0 m or ft).

    - `args[4] = feature_list` is either `us` (default) or `si`.

    - `args[5] = feature_list`is either `True` or `False` (default).

The code creates a temp folder called `.cache` where it stores temp variables, databases, and Rasters. Avoid accessing `.cache` while the code is running and ensure its (manual) deletion in the case that the code crashed.

`fa.map_maker(∗args, **kwargs)` creates `pdf` map assemblies based on the layout files stored in `RiverArchitect/02_Maps/CONDITION/map_CONDITION_design.aprx` and Rasters prepared with `fa.Raster_maker("condition", ["Featurename"], True)`.  `fa.map_maker(∗args, **kwargs)` accepts an optional argument defining a `CONDITION` and a keyworded argument defining map-able *reach ID*s:

-   Option 1: `fa.map_maker("2018_mod")` uses the map folder `RiverArchitect/02_Maps/2018_mod/` and Rasters stored in `RiverArchitect/Output/Rasters/2018_mod/`

-   Option 2: `fa.map_maker("2018_mod", "rrr")`  uses the map folder `RiverArchitect/02_Maps/2018_mod/`,  Rasters stored in `RiverArchitect/Output/Rasters/2018_mod/`, and limits mapping to the extents related to a reach `"rrr"` with its extents defined in `RiverArchitect/ModifyTerrain/.templates/computation_extents.xlsx` 


The second alternative run option for the *LifespanDesign* module is to run it as a standalone script (`feature_analysis.py`) from the system command line:

1.  Launch terminal (Start -> type `cmd`)

2.  Navigate to the place where *ArcGIS* `python.exe` is stored:<br/>
    For example: `C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\`

3.  Run as script: `python.exe DriveLetter:\...\LifespanDesign\feature_analysis("condition", ["Featurename"])` 

4.  The code asks for a condition, which needs to be typed case-sensitive and without any apostrophes:<br/>
    For example: `Enter the condition (shape: >> XXXX (e.g., >> 2008))>> 2008`

5.  Next, the code asks for a `feature_list`, which is and optional argument (simply hitting enter works though); the feature list must be typed as list (in brackets): `Enter the condition (no mandatory; do not forget brackets − example: >> ["Featurename1", "Featurename2"] >> ["Sidecavity", "Bermsetback"]`

6.  The program is now running (this takes time) and it will prompt when it finished.

Calling the module as `.py` script may cause errors because of differences between path interpretation methods and it is limited to the creation of Rasters only. Therefore, the fastest and most consistent way for using the `feature_analysis` script is to import it as above described.

## Output<a name="output"></a>
***

### Rasters

The output Rasters are either of the types lifespan (`lf_shortname`) or design (`ds_shortname`) and they are created in `.../Output/Rasters/CONDITION/`. The usage of `shortname`s (see the list on the [Features page](River-design-features#featoverview)) is necessary because `arcpy` cannot handle Rasters with names longer than 13 characters when the GRID format is used (even though the standard Raster type is *GeoTIFF*). The analysis automatically shortens too long Raster names based on shortnames and it creates the condition-output directory if it does not yet exist. Existing files in the `Output/Rasters/CONDITION/` folder are overwritten (the code enforces overwriting and tries to delete any existing content  (i.e., ensure that the output folder does not contain any important files).

### Mapping<a name="outmaps"></a>

The module produces an *ArcGIS Pro* project file (`.aprx`) and `.pdf`s in `RiverArchitect/02_Maps/CONDITION/map_CONDITION_design.aprx`. The map extents can be modified in the [`mapping.inp` input file](Signposts#inpmaps). For map modifications, read the [above](#lfrungui) descriptions or the [Mapping](Mapping) Wiki.


### Interpretation

The success of features corresponds to their ecological sustainability and physical stability, which may positively correlate (i.e., high stability corresponds to high ecological sustainability). However, features such as gravel augmentation or grading have an inverse relationship between ecological sustainability and physical stability. For example, frequently mobile gravel injections create valuable habitat but are, by definition, unstable. In such cases, the lifespan maps need to be considered oppositely: Optimum areas for application correspond to regions with low lifespans (see more in [Schwindt et al. 2019][schwindt19]).

### Quit module and logfiles

The GUI can be closed via the `Close` dropdown menu if no background processes are going on (see terminal messages). The GUI flashes and rings a system bell when it completed a run task. If layout creation and/or mapping were successfully applied, the target folder automatically opens. After execution of either run task, the GUI disables functionalities, which would overwrite the results and it changes button functionality to open logfiles and quit the program. Logfiles are stored in the `RiverArchitect/` folder with the name `logfile.log`. Logfiles from previous runs are overwritten.



[1]: https://github.com/RiverArchitect/RA_wiki/wiki/Installation
[2]: https://github.com/RiverArchitect/RA_wiki/wiki/Signposts
[3]: https://github.com/RiverArchitect/RA_wiki/wiki/LifespanDesign
[4]: https://github.com/RiverArchitect/RA_wiki/wiki/MaxLifespan
[5]: https://github.com/RiverArchitect/RA_wiki/wiki/ModifyTerrain
[6]: https://github.com/RiverArchitect/RA_wiki/wiki/SHArC
[7]: https://github.com/RiverArchitect/RA_wiki/wiki/ProjectMaker
[8]: https://github.com/RiverArchitect/RA_wiki/wiki/Tools
[9]: https://github.com/RiverArchitect/RA_wiki/wiki/FAQ
[10]: https://github.com/RiverArchitect/RA_wiki/wiki/Troubleshooting

[bywater15]: http://dx.doi.org/10.1002/2014WR016641
[carley12]: https://www.sciencedirect.com/science/article/pii/S0169555X12003819
[friedman99]: http://dx.doi.org/10.1002/(SICI)1099-1646(199909/10)15:5<463::AID-RRR559>3.0.CO;2-Z
[gaeuman08]: http://odp.trrp.net/DataPort/doc.php?id=346
[glenn15]: https://doi.org/10.1201/b18359
[jablkowski17]: http://www.sciencedirect.com/science/article/pii/S0169555X1730274X
[kui16a]: http://www.sciencedirect.com/science/article/pii/S0378112716300123
[lange05]: https://www.ethz.ch/content/dam/ethz/special-interest/baug/vaw/vaw-dam/documents/das-institut/mitteilungen/2000-2009/188.pdf
[manningsn]: https://en.wikipedia.org/wiki/Manning_formula#Manning_coefficient_of_roughness
[maynord08]: https://ascelibrary.org/doi/10.1061/9780784408148.apb
[ock13]: https://www.jstage.jst.go.jp/article/hrl/7/3/7_54/_article
[pasquale14]: http://dx.doi.org/10.1002/hyp.9993
[pasternack10a]: http://calag.ucanr.edu/archive/?article=ca.v064n02p69
[polzin06]: https://link.springer.com/article/10.1672/0277-5212(2006)26%5B965:EDSSSA%5D2.0.CO;2
[ruiz16b]: https://www.sciencedirect.com/science/article/pii/S0169555X15002019?via%3Dihub
[schwindt19]: https://www.sciencedirect.com/science/article/pii/S0301479718312751
[stromberg93]: http://www.jstor.org/stable/41712765
[usace00]: https://www.publications.usace.army.mil/Portals/76/Publications/EngineerManuals/EM_1110-2-1913.pdf
[vandenderen17]: https://onlinelibrary.wiley.com/doi/full/10.1002/esp.4267
[weber17]: http://www.sciencedirect.com/science/article/pii/S0169555X16309862
[wilcox13]: http://dx.doi.org/10.1002/wrcr.20256
[wyrick14]: https://www.sciencedirect.com/science/article/pii/S0169555X14000099
[wyrick16]: https://onlinelibrary.wiley.com/doi/full/10.1002/esp.3854
