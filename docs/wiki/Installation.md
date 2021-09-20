Installation
============

***

- [Install *River Architect*](#git_install_ra)
- [Update *River Architect*](#update_ra)
- [Launch *River Architect*](#launch_ra)
- [Prepare file structure](#structure)
- [Program environment setup and batchfile modification](#raenv)
- [Requirements and dependencies](#req)
- [Logfiles](#logs)

***

<a name="started"></a>

*River Architect* applies on *ArcGIS Pro*'s `arcpy` package and needs to be executed with *ArcGIS Pro*'s conda environment (`C:\Program Files\ArcGIS\Pro\bin\Python\scripts\propy.bat`). The [requirements](#req) section provides more details and installation hints for external packages.
*River Architect* is designed as an external application rather than a python package, but its modules can be imported as packages for external use (see the *Alternative Run* sections in the module Wikis).<br/>

***

## Installation with *Git Bash/GUI*<a name="git_install_ra"></a>
We recommend downloading and updating *River Architect* using [*Git Bash*](https://git-scm.com/downloads) (or Git GUI). Alternatively, *River Architect* can be downloaded as *zip* file. However, updates are tricky when *River Architect* is downloaded as *zip* file.

**Git Bash**<br/>
*GitHub* provides detailed descriptions and standard procedures to work with their repositories ([read more](https://help.github.com/en/articles/cloning-a-repository)). The following "recipe" guides through the first time installation (cloning) of *River Architect*:

1. Open *Git Bash*
2. Type `cd "D:/Target/Directory/"` to change to the target installation directory (recommended: `cd "D:/Python/RiverArchitect/"`). If the directory does not exist, it can be created in the system explorer (right-click in empty space > `New >` > `Folder`).
3. Clone the repository: `git clone https://github.com/RiverArchitect/program`

Done. Close *Git Bash* and start working with *River Architect*.

**Git GUI**<br/>
For using *Git GUI*, open *Git GUI* and choose `Clone Existing Repository`. Enter the *Source Location*: `https://github.com/RiverArchitect/program`, and the *Target Directory*: `D:/Python/RiverArchitect` (or any other directory, but ensure that the directory does not exist). Click `Clone`. Done.

***

## Update with *Git Bash/GUI* (re- pull)<a name="update_ra"></a>
Currently, *Git Bash* (or Git GUI) are the only options to update local copies of *River Architect*. **Before updating *River Architect*, we recommend to save any files and *Conditions* produced with *River Architect* externally (create a save copy).**

**Git Bash**<br/>
Open *Git Bash* and do the following:

1. Go to the local *River Architect* installation directory: `cd "D:/Python/RiverArchitect/program/"` (or wherever *River Architect* was cloned).
2. Check the current status: `git status`
3. Pull changes: `git pull`

Please note that merge errors may occur when changes were made in the local copy of *River Architect*. In this case, *Git Bash* will guide through the manual merge process.
**If you modified template workbooks (`Fish.xlsx` or `threshold_values.xlsx`): Create a [`.gitignore`](https://git-scm.com/docs/gitignore) file** in the `/RiverArchitect/` directory. Open the `.gitignore` file with a text editor and enter the following:

```

/LifespanDesign/.templates/threshold_values.xlsx
/.site_packages/templates/Fish.xlsx

```

Save the `.gitignore` file and close the text editor. Now `git pull` will no longer overwrite `Fish.xlsx` and `threshold_values.xlsx`.


**Git GUI**<br/>
Open *Git Bash* and open `D:/Python/RiverArchitect` from the *Open Recent Repository* list (or wherever *River Architect* is installed). If not listed, click on `Open Existing Repository` and select the *River Architect* installation directory. Then:

1. Click on `Rescan`.
2. Click on the `Remote` drop-down menu > `Fetch from` > `origin`.
3. Click on the `Merge` drop-down menu > `Local Merge`.



***

## Launch *River Architect*<a name="launch_ra"></a>

To start using *River Architect*:
 1. Right-click on `DRIVE:\path\to\...\RiverArchitect\Start_River_Architect.bat` and click on `Edit`.
     - In the `Start_River_Architect.bat`chfile, ensure that the Python path is correctly defined according to the installed version of *ArcGIS*: `call `**EDIT>>`"%PROGRAMFILES%\ArcGIS\Pro\bin\Python\Scripts\propy"`<<**`"%cd%\master_gui.py"`. For more information about running standalone Python scripts in *ArcGIS Pro*'s conda environment, read their [descriptions](https://pro.arcgis.com/en/pro-app/arcpy/get-started/using-conda-with-arcgis-pro.htm).
     - Save and close `Start_River_Architect.bat`.
 1. Double-click on `DRIVE:\path\to\...\RiverArchitect\Start_River_Architect.bat` to start *River Architect*.
 1. Create a [*Condition*](Signposts#getstarted) on the Welcome (*[Get Started](Signposts#getstarted)*) tab.
 1. Analyze and create ecohydraulic paradises for [Physical Habitats prefered by target (fish) species](SHArC#hefish) with sustainable [river design features](River-design-features) using [lifespan maps](https://www.sciencedirect.com/science/article/pii/S2215016119300913?via%3Dihub).<br/>
    *Hint: The **Quick GUIde** sections in the module Wikis provide straight-forward application guidance.*

*River Architect* starts in a GUI that is stored in `master_gui.py`. Alternatively, the modules can be individually launched by double-clicking on the `LAUNCH_Windows_x64.bat` in the module folders (not recommended and may be abandoned in future versions).

![ragui](https://github.com/RiverArchitect/Media/raw/master/images/gui_start.PNG)


# Package structure, requirements and logfiles

***

## File structure<a name="structure"></a>

The main directory (`/RiverArchitect/`) contains the program launcher named `Start_River_Architect.bat` and the *Python3* file `master_gui.py`. The *River Architect* modules are located in sub-folders. The master folder (`/RiverArchitect/`) includes the following files and directories (the full list of all files for developers is available [here](DevModule#struc)):

-   **.sitepackages**
		Contains adapted third-party Python packages and own packages
    -   `openpyxl`
			Contains a modified version of the `openpyxl` package (version 2.5.2) adapted for *River Architect*
    -   `riverpy`	
			Particular python scripts with recurring routines and classes that are used in multiple modules.
        -   `cDefinitions.py` contains inter-module information of reach and feature keywords.
        -   `cFeatures.py` contains river design features classes with pointers to parameters and threshold values.
        -   `cFish.py` contains the class that reads characteristic species and lifestage data from `riverpy/templates/Fish.xlsx`.
        -   `cFlows.py` contains classes for creating flow duration curves and interpolating the annual/seasonal flow durations of 2D-modeled discharges.
        -   `cGravel.py` contains subfeatures of the Gravel augmentation-feature in `cFeatures`.
        -   `cInputOutput.py` contains workbook (`.xlsx`) read and write routines.
        -   `cInterpolator.py` provides routines for interpolating data between exact data points (*x* and *y*).
        -   `cLogger.py` contains the `Logger()` class that specifies the appearance of logging messages.
        -   `cMakeTables.py` make habitat evaluation workbook tables (`.xlsx` format).
        -   `cMapper.py` contains mapping routines (see <a href="Mapping">Mapping</a> Wiki).
        -   `cPlants.py` contains subfeatures of the Plantings-feature in `cFeatures` and the `ModifyTerrain` module.
        -   `cReachManager.py` processes reach information and reach-wise terrain change (volume differences).
        -   `cThresholdDirector.py` provides the `ThresholdDirector()` class for reading threshold values from the "thresholds.xlsx" workbook.
        -   `config.py` contains global parameter definitions and pointers to workbooks.
        -   `fGlobal.py` provides functions that are required in this module and the other modules in several classes.
        -   
    -   `templates`
			contains global template files (content will be enriched in future versions)

-   **00\_Flows** contains templates for [flow (discharge) analyses](Signposts#ana-flows).
    
-   **01\_Conditions** contains `Condition` folders with parameter Rasters. The condition name begins with a 4-digit year number (e.g., `2018`), optionally followed by a 3-characters reach ID (e.g., `xyz`) and a feature layer indicator (e.g., `lyr10` for terraforming [features][2]). The syllables are separated by an underscore. The process of defining of reaches is explained in the [Signposts][2] and the [*ModifyTerrain* Wiki][5].
    
-   **02\_Maps** contains a map `templates` subfolder that is copied by *River Architect*'s modules for processed conditions (e.g., `02_Maps/CONDITION/`) for <a href="Mapping">Mapping</a> of Rasters and Shapefiles. The following templates and folders may be modified:
    -   `symbology`\ contains a standard symbology layer file (`.lyrx`) for partially logarithmic lifespan classification
    -   `river_template.aprx` is the standard *ArcGIS Pro* project file, where developers recommend to adapt background image (layer) connections.

-   **Module (folder): [`RiverArchitect/StrandingRisk`](StrandingRisk)** for [stranding risk analyses of restoration efforts](StrandingRisk).
    - `Output` directory where Stranding Risk module outputs are saved.
    - `connect_gui.py` is a standalone script that creates the graphical user interface (GUI) for running the [Stranding Risk](StrandingRisk) module.
    - `cConnectivityAnalysis.py` provides methods for calculating stranding risk metrics.
    - `cGraph.py` contains graphic representation routines for habitat connectivity analyses.

-   **Module (folder): [`RiverArchitect/GetStarted`](Signposts#getstarted)** prepare input *Conditions* from scratch or existing conditions.
    -   `.cache` folder occurs temporarily when the module is executed.
    -   `.templates` folder should not be modified and contains the welcome screen imagery.
    -   `cConditionCreator.py` contains a managing class for creating and populating *Conditions*.
    -   `cDetrendedDEM.py` provides routines for generating detrended DEM Rasters.
    -   `cMakeInp.py` provides routines for creating input files (*.inp*) for lifespan mapping.
    -   `cMorphUnit.py` provides routines for calculating instream morphological units ([Wyrick and Pasternack 2014][wyrick14]).
    -   `cWaterLevel.py` provides routines for calculating depth to water table Rasters.
    -   `fSubCondition.py` contains routines for creating a spatial subset of an existing *Condition*.
    -   `popup_ ... .py` contain popup window classes guiding through the creation and population of *Conditions*.
    -   `welcome_gui.py` contains the `Get Started` tab source code.

-   **Module (folder): [`RiverArchitect/LifespanDesign`][3]** for [Lifespan and Design analyses of restoration features][3].
    -   `Output` folder with sub-folders for `Rasters` from individual module runs.
    -   `.cache` folder occurs temporarily when the module is executed.
    -   `.templates` folder should not be modified and contains input (`*.inp`) files; if required, the module includes routines for changing the input files.
    -   `cLifespanDesignAnalysis.py` contains a GIS-based functional core for processing `Raster` files.
    -   `cParameters.py` contains the parameter input core with pointers to `Raster`s and `Raster` names.
    -   `cReadInpLifespan.py` contains classes that read input data from `*.inp` files.
    -   `feature_analysis.py` coordinates class and function calls.
    -   `lifespan_design_gui.py` is a standalone script that creates the graphical user interface (GUI) for running the [*LifespanDesign*][3] module.

-   **Module (folder): [`RiverArchitect/MaxLifespan`][4]** for [maximum lifespan assessment of feature groups (concurring features)][4] 
    -   `Output` folder with sub-folders for `Layouts`, `Maps` and `Rasters` from individual module runs.
    -   `.cache` folder occurs temporarily when the module is executed.
    -   `.templates` folder contains additional Rasters, which are required by this module; other Rasters are loaded from `01_Conditions`.
    -   `action_gui.py` is a standalone script that creates the graphical user interface (GUI) for running the *MaxLifespan* module.
    -   `action_planner.py` coordinates class instantiations and function calls.
    -   `cActionAssessment.py` contains the GIS-based functional core that identifies optimum lifespans and associated features by processing lifespan/design `Raster` and `shape` files.
    -   `cFeatureActions.py` contains pointers to [river restoration feature](River-design-features) data in the [*LifespanDesign*][3] module.
    -   `cReadActionInput.py` contains functions for reading `*.inp` files from the `.templates` folder.

-   **Module (folder): [`RiverArchitect/ModifyTerrain`][5]** [performs half-automated terrain modifications][5]
    -   `Input` folder containing optional modified DEMs for volume difference assessment.
    -   `Output` folder with sub-folders `Rasters` from individual module runs.
    -   `RiverBuilder` folder contains original [River Builder](RiverBuilder) code (`riverbuilder.r`) and input files, as well as help messages.
    -   `.cache` folder occurs when the module is executed.
    -   `.templates` folder contains the [reach](RiverReaches)-defining workbook `computation_extents.xlsx`.
    -   `cModifyTerrain.py` contains GIS-based functional core for modifying DEM `Raster`s with threshold values ([grading](River-design-features#grade) and [widening](River-design-features#berms)).
    -   `cRiverBuilder.py` contains routines for launching [River Builder](RiverBuilder).
    -   `cRiverBuilderConstruct.py` contains routines for creating input files for [River Builder](RiverBuilder).
    -   `modify_terrain_gui.py` is a standalone script that creates the graphical user interface (GUI) for running the [*ModifyTerrain*][5] module.
    -   `sub_gui_rb.py` contains the GUI for creating [River Builder](RiverBuilder) input files.


-   **Module (folder): [`RiverArchitect/SHArC`][6]** [creates Habitat Suitability Index Rasters/maps and quantifies annually usable habitat area for target fish species and user-defined ranges of discharges][6].
    -   `CHSI` contains subfolders with composite habitat suitability index Rasters for pre- and post-project `conditions`.
    -   `HSI` contains subfolders with habitat suitability index `Rasters` for pre- and post-project `conditions`.
    -   `SHArea` contains result workbooks with SHArea values for examined `conditions`. The `Rasters` subfolder contains the associated composite habitat suitability Rasters.
    -   `.cache` folder occurs temporarily when the module is executed.
    -   `.templates` folder contains spreadsheet templates for the quantification of annually usable habitat area and the definition of fish species, lifestages, and associated habitat suitability curves.
    -   `cHSI.py` contains classes to calculate composite habitat suitability Rasters, hydraulic habitat suitability Rasters and interpolating the annual flow duration of considered discharges.
    -   `sharc_gui.py` contains the class of this module.
    -   `sub_gui_covhhsi.py` opens a new GUI window to create cover habitat suitability Rasters.
    -   `sub_gui_hhsi.py` opens a new GUI window to create hydraulic habitat suitability Rasters and determine associated annual flow duration.

-   **Module (folder): [`RiverArchitect/ProjectMaker`][7]** applies on results from *MaxLifespan* and *SHArC*, as well as manual inputs to [calculate project cost-benefit metrics][7].
    -   `.cache` folder occurs temporarily when the module is executed.
    -   `.templates` folder contains a template folder tree and template workbooks with unit cost tables, as well as sample application data that illustrate potential results of the module.
    -   `cSHArC.py` applies *SHArC* results, in particular *cHSI* Rasters for calculating [SHArea](SHArC#herunSHArea) in the project area.
    -   `project_maker_gui.py` contains the class of this module.
    -   `s20_plantings_delineation.py` applies [*LifespanDesign*][3] and [*MaxLifespan*][4] for assessing the most suitable vegetation plantings within the project area.
    -   `s21_plantings_stabilization.py` applies [*LifespanDesign*][3] and [*MaxLifespan*][4] outputs as well as user-defined input parameters for mapping nature-based engineering features required to stabilize vulnerable vegetation plantings.
    -   `s30_terrain_stabilization.py` applies [*LifespanDesign*][3] and [*MaxLifespan*][4] outputs to stabilize terraforming features.
    -   `s40_compare_wua.py` applies on [*SHArC*][6] *cHSI* Rasters used in `cSHArC.py` for assessing the annually usable habitat area for a target fish species and lifestage within the project area.
    -   `LAUNCH_Windows_x64.bat` is a batchfile that runs `project_maker_gui.py` on Windows x64.

-   **Module (folder): [`RiverArchitect/VolumeAssessment`](VolumeAssessment)** [calculates excavation / fill volumes of terraforming features.](VolumeAssessment)
    -   `Output` folder for calculation results.
    -   `.cache` folder occurs when the module is executed.
    -   `.templates` folder contains `volume_template.xlsx`.
    -   `cVolumeAssessment.py` contains GIS-based functional core for calculating volumes using an ArcGIS "3D" extension.
    -   `volume_gui.py` is a standalone script that creates the graphical user interface (GUI) for running the [*VolumeAssessment*](VolumeAssessment) module


-   **Folder: [`Tools`][8]** applies on results from [*MaxLifespan*][4] and [*SHArC*][6], as well as manual inputs to calculate project cost-benefit metrics.
    -   `.cache` folder occurs temporarily when the module is executed.
    -   `.templates` folder contains a template workbooks for multiple purposes.
    -   `Products` folder contains results of any script in this folder.
    -   `cHydraulic.py` contains a class with routines for calculating cross-section-averaged flow characteristics.
    -   `cInputOutput.py` contains classes required for reading and writing data, as well as calculation progress logging.
    -   `cPoolRiffle.py` provides routines for designing self-sustaining pool-riffle channels.
    -   `fTools.py` is a set of functions used by other Python applications within this folder.
    -   `make_annual_peak.py` prepares required input data for statistic flow analyses and with the U.S. Army Corps of Engineers' [*HEC-SPP*][hecspp] software.
    -   `make_annual_flow_duration.py` - *deprecated (will be removed)* creates flow duration curves (annual averages) for the assessment of SHArea (deprecated). *A more sophisticated version of this function is integrated in the <a href="SHArC">SHArC</a> module with options to limit flow duration assessments to fish-lifestage seasons.*
    -   `morphology_designer.py` creates design tables for self-sustaining pool-riffle channels (uses `cHydraulic.py` and `cPoolRiffle.py`).
    -   `run_make_….bat` are a batchfiles that run `make_….py` on Windows.
    -   `run_morphology_designer.bat` is a batchfiles that runs `morphology_designer.py`.


## Program environment setup and batchfile modification<a name="raenv"></a>
***
The package is designed for an *ArcGIS Pro*'s Python3 conda environment. Before launching the *River Architect* package for the first time, the batchfiles may require adaptions for the system environment. On **Windows** only (Linux is not yet available because of `arcpy` issues - we are working on it), set the batch file environment as follows:

1.  Right-click on `Start_River_Architect.bat` and choose *Edit* (*with Texteditor*) or *Open with \...* and choose a *Texteditor* software.

2.  Check, and if necessary, replace the path to the good python interpreter:<br/>
		*Default:* `"%PROGRAMFILES%\ArcGIS\Pro\bin\Python\Scripts\propy"`<br/>
		*Note:* Future versions of *River Architect*'s will require `gdal` and `rasterio`. Therefore, developers recommend to create a new conda environment and to install these packages to that new environment:
      - Open "ArcGIS Pro" and click on the *Project* pane in the upper left corner
      - Click on the *Python* tab
      - Click on the *Manage Environments* button and on *Clone default* (or manually copy the default environment) to, for example, `C:\Python\envs\arcgispro-py3-cust`
      - When cloning was successful, restart *ArcGIS Pro* and go back to the *Project* > *Python* tab and click on *Add Packages*
      - Search for, and install `gdal` (`lib-gdal` also works) and `rasterio`
      - For starting *River Architect* from an *IDE*, set the new conda environment as interpreter (e.g., `C:\Python\envs\arcgispro-py3-cust\python.exe`). The new environment may also be used in the batchfiles.
      - The [ArcGIS Pro website](https://pro.arcgis.com/en/pro-app/arcpy/get-started/what-is-conda.htm) provides more information on how to install *Python* packages.

3.  Save `LAUNCH_River_ArchitectWINx64.bat` and close *Texteditor*.

4.  Set default application to open input file type documents ([`*.inp` files](LifespanDesign-input-files)):<br/>
    *Go to folder `...\River Architect\LifespanDesign\.templates\` and right-click on `mapping.inp` to access the menu `Open with ...`. Choose any text editor, such as `Notepad`, `Texteditor` or `Notepad++` and click `OK`*.

There is no standard easy way to import ArcGIS' `arcpy` package in *Python* running on UNIX platforms (Apple or Linux). Future versions of *River Architect* aim at using other packages for geodata processing, which will also run on UNIX platforms (we are currently experimenting with `gdal` and `qgis.core`).\
After editing the batch files, launch *River Architect* by double-clicking on `Start_River_Architect.bat`.

## Requirements and dependencies<a name="req"></a>
***

### Python packages
The execution of *River Architect* requires the following packages, which are part of the standard *ArcGIS Pro* - *Python3* distribution: 
- `arcpy`
- `argparse`
- `glob`
- `logging`
- `openpyxl`
- `os`
- `shutil`
- `subprocess` (not mandatory, also works without this package)
- `tkinter`

Additional packages:
- `rpy2` and the R language: The *[Morphology\ModifyTerrain][5]* module requires [an installation of the R language](https://www.r-project.org/) to automate the production of river topographic data via the [*RiverBuilder*](http://pasternack.ucdavis.edu/research/model-codes/river-builder/) R package. Note: environmental variables `%R_HOME%` and `%R_USER%` must also be properly defined for Python to access the user installation of R.

*River Architect* incorporates a modified version of [`openpyxl`](https://openpyxl.readthedocs.io/en/stable/), but a more proper way is installing `openpyxl` with *ArcGIS Pro*'s [package manager](https://pro.arcgis.com/en/pro-app/arcpy/get-started/what-is-conda.htm). Future versions may additionally require the `gdal` and `rasterio` packages (see [above](#raenv) instructions).\
Furthermore, *River Architect* requires *ArcGIS Pro*'s "Spatial Analyst" and "3D" ([Volume Assessment](VolumeAssessment) only) extensions. Another version of *River Architect* based on open-source geodata processing packages is planned for the future.

Any folder beginning with a "." for example `.cache` or `.idea` must not be modified or assessed by any other program, in particular during the execution of package methods. Files stored in `.templates` folders are directly called by the GUIs if user definitions are admitted. At the end of execution, the applied modules have created their output folders, which are indicated in the command prompt.

### Other software and dependencies
***
A workbook editing software such as *Excel* or [*LibreOffice*][libreoffice] is required for modifications of user-defined databases (`.xlsx` files).

For the visualization of geodata (`.shp` and `.tif` files), and mapping with project files (`.aprx`), an installation of *ArcGIS Pro* is required. Open-source alternatives are [*QGIS* ](https://www.qgis.org/en/site/forusers/download.html) or [SAGA](http://www.saga-gis.org/en/index.html) (*Please note: There are more GIS alternatives out there.*).

## Logfiles<a name="logs"></a>
***
Logfiles `logfile.log` are created in the module directories during every run task. These files contain time-stamped terminal messages of program activities, warnings and error messages. Thus, logfiles enable the user to review process duration and to trace back problems. The handling of potential errors and warning messages are listed in the [Troubleshooting Wiki][10]  with descriptions of problem sources (cause) and solutions (remedy).

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
[11]: https://github.com/RiverArchitect/RA_wiki/VolumeAssessment
[12]: https://github.com/RiverArchitect/RA_wiki/RiverBuilder

[wyrick14]: https://www.sciencedirect.com/science/article/pii/S0169555X14000099
[hecspp]: https://www.hec.usace.army.mil/software/hec-ssp/
[libreoffice]: https://www.libreoffice.org/
