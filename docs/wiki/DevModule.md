DEVELOPMENT
===========

***

- [**Principles & Requiremments**](#raprin)
- [**Add a module to River Architect**](#addmod)
  * [Use Python templates](#template)
  * [Bind the new module to the GUI](#bind)
- [Edit the Wiki](DevWiki)
- [Use `git`](DevGit)

***

<a name="raprin"></a>
The development of *River Architect* follows the *Zen of Python*, also known as [PEP20](https://www.python.org/dev/peps/pep-0020/).

```python
	>>> import this
	The Zen of Python, by Tim Peters

	Beautiful is better than ugly.
	Explicit is better than implicit.
	Simple is better than complex.
	Complex is better than complicated.
	Flat is better than nested.
	Sparse is better than dense.
	Readability counts.
	Special cases aren't special enough to break the rules.
	Although practicality beats purity.
	Errors should never pass silently.
	Unless explicitly silenced.
	In the face of ambiguity, refuse the temptation to guess.
	There should be one-- and preferably only one --obvious way to do it.
	Although that way may not be obvious at first unless you're Dutch.
	Now is better than never.
	Although never is often better than *right* now.
	If the implementation is hard to explain, it's a bad idea.
	If the implementation is easy to explain, it may be a good idea.
	Namespaces are one honking great idea -- let's do more of those!
```

The *River Architect Wiki* for developers assumes a basic understanding of *Python3*, object-oriented programming, the *markdown* language and basics in *HTML*. In order to ensure quality, we test and debug new code before pushing it, and we run spell checkers before updating the Wiki (albeit we cannot guarantee that the writing is 100 percent correct, we do our best). 


# Add a module to *River Architect* <a name="addmod"></a>
***
Overview
-	[Use Python templates](#template)
-	[Bind the new module to the GUI](#bind)
- 	[Full folder and file structure](#struc)

***

New modules or code modifications should be pushed to the `program` repository [https://github.com/RiverArchitect/program](https://github.com/RiverArchitect/program) ([read more about using `git`](DevGit)).

*River Architect* has currently five **master** tabs (or modules) and three of them have **slave**-tabs (sub-modules): [Lifespan](LifespanDesign), [Morphology](ModifyTerrain), and [Ecohydraulics](SHArC). The development of a new module or sub-module follows the same standards and varies only in the way how the tab is finally bound in the *River Architect* master GUI. For creating a new (sub) module, do the following:

1. Have a look at *River Architect* ([see folder and file structure](Installation#structure)) and think about the capacities that the new module should have, and how it can be fitted in the existing framework (think twice before adding a new master tab).
1. Clone the template repository: `git clone https://github.com/RiverArchitect/development.git`.
1. Frome the cloned repository, copy the folder `RiverArchitect/development/moduleTEMPLATE/` to `RiverArchitect/moduleTEMPLATE/`.
1. Rename `RiverArchitect/moduleTEMPLATE/` to  `RiverArchitect/NEW_MODULE_NAME/` (obviously, replace `NEW_MODULE_NAME` with the name of the new module).
1. Edit and add the module files `RiverArchitect/NEW_MODULE_NAME/cTEMPLATE.py` and `-- TEMPLATE_gui.py` (see below descriptions of the [module template](#template)).
1. Bind the new module to the *River Architect* master GUI (see below descriptions for [binding a new module to the *River Architect* master GUI](#bind)).


## Working with the module template <a name="template"></a>
***
The *River Architect* [development repository](https://github.com/RiverArchitect/development) provides template file for creating a new module in the `moduleTEMPLATE/` directory:

- 	[`TEMPLATE_gui.py`](#templategui) is a template of the actual GUI that will be shown in the new tab.
-	[`cTEMPLATE.py`](#templateclass) is a template for writing new classes using geospatial analysis with `arcpy.sa`.

Inline comments guide through the scripts and their dependencies. Both scripts load all functions and load most of the required packages from `RiverArchitect/.site_packages/riverpy/fGlobal.py`.

### Using `TEMPLATE_gui.py` <a name="templategui"></a>

The script contains [`tkinter`](https://effbot.org/tkinterbook/) classes to build the tab GUI. The first class is a `PopUpWindow` that may be useful for inquiring complex user input (e.g., calculate a value). A good example of using complex user input within *River Architect* is the [River Builder input file creator](RiverBuilder#cinp). 

```python
class PopUpWindow(object):
    def __init__(self, master):
		... 
```

The most relevant template class here is `class MainGui(sg.RaModuleGui)`, which inherits the tab-slave class `RaModuleGui` from `RiverArchitect/slave_gui.py`. **All tabs must inherit `RiverArchitect/slave_gui.RaModuleGui`**, no matter if this will be a master or a slave tab. As such, all tabs inherit the following class variables (relevant variables only are listed here):

-	`self.condition` is a `STR` of a condition contained in `RiverArchitect/01_Conditions/`
-	`self.features` is a `cDef.FeatureDefinitions()` object resulting from `RiverArchitect/LifespanDesign/.templates/threshold_values.xlsx` ([read more about features](River-design-features))
-	`self.reaches` is a `cDef.ReachDefinitions()` object resulting from `RiverArchitect/ModifyTerrain/.templates/computation_extents.xlsx` ([read more about river reaches](RiverReaches))
-	`self.units` is a `STR` variable, which is either `us` (US customary) or `si` (SI Metric)
-	`self.ww` is an `INT` variable defining the tab window width
-	`self.wh` is an `INT` variable defining the tab window height
-	`self.wx` is an `INT` variable defining the tab window x-position
-	`self.wy` is an `INT` variable defining the tab window y-position
-	`self.xd` is an `INT` variable defining the x-pad (pixel space around `tkinter` objects)
-	`self.yd` is an `INT` variable defining the y-pad (pixel space around `tkinter` objects)

Moreover, the `RaModuleGui` class automatically creates a `"Units"` and a `"Close"` dropdown menu.<br/>

The `MainGui(sg.RaModuleGui)` class header (`__init__()` function) looks like this:

```python
class MainGui(sg.RaModuleGui):
    def __init__(self, from_master):
        sg.RaModuleGui.__init__(self, from_master)
        self.ww = 800  # window width
        self.wh = 840  # window height
        self.title = "TEMPLATE"         # <---------------------- SET MODULE NAME HERE, BUT DO NOT CHANGE CLASS NAME
        self.set_geometry(self.ww, self.wh, self.title)
		# ... tkinter examples
```

We recommend modifying the `__init__()` function of new modules starting with the `self.ww` and `self.wh` variables, which define the tab window width and height in pixels, respectively (try to avoid values larger than 1000 pixels). Most important and **required** edits are:

-	the **file name** (rename `TEMPLATE_gui.py` to something like `new_module_gui.py`), and
-	the window title defined with the `self.title` variable (see above code snippet, where `"TEMPLATE"` should be renamed to something like `"New Module"`).

Below `self.title` variable, the template provides some examples for using `tkinter` objects such as labels, listboxes with scroll bars, buttons, checkbuttons, and drop-down menus. For `tkinter` beginners, we recommend to carefully explore  different `tkinter` objects ([read more](https://effbot.org/tkinterbook/tkinter-index.htm#class-reference)).<br/>

The `MainGui.run_calculation()` function illustrates the implementation of a geospatial calculator class ([see `cTEMPLATE.py`](#templategui)):

```python
    def run_calculation(self):
        """
        Trigger a calculation with cTEMPLATE.TEMPLATE()
        """
        geo_calc_object = cTEMPLATE.TEMPLATE()

        # inquire input raster name
        dir2raster = askopenfilename(initialdir=".", title="Select input GeoTIFF raster",
                                     filetypes=[('GeoTIFF', '*.tif;*.tiff')])
        result = geo_calc_object.use_spatial_analyst_function(dir2raster)
        geo_calc_object.clear_cache()  # remove temporary calculation files

        if not(result == -1):
            showinfo("SUCCESS", "The result raster %s has been created." % result)
        else:
            showinfo("ERROR", "Something went wrong. Check the logfile and River Architect Troubleshooting Wiki.")
```

`geo_calc_object` is a `cTEMPLATE.TEMPLATE()` object that is locally created in the `run_calculation()` function. It has a `use_spatial_analyst_function` that requires an input raster path to apply a (random) *ArcGIS Spatial Analyst* map algebra expression to that input raster. For this purpose, the `MainGui.run_calculation()` function asks the user to define an input raster using `tkinters`'s `askopenfilename()` function (imported from `tkinter.filedialog`). The line `result = geo_calc_object.use_spatial_analyst_function(dir2raster)` passes the selected raster file path (`dir2raster`) to the geospatial calculation function, which returns a string of the output raster if the calculation was successful (otherwise, it returns -1). After the calculation, an info window pops up (`showinfo(WINDOW_NAME, MESSAGE)` imported from `tkinter.messagebox`) and informs about the calculation success.

The `MainGui.set_value()` function illustrates the usage of the above mentioned `PopUpWindow` class (in the same file `TEMPLATE_gui.py`) to modify a value. The usage in the template is somewhat meaningless; a more reasonable value modification can be found in the *Lifespan Design* module where the user can modify the *Manning's n* roughness value ([see applicaton](LifespanDesign#lfinpopt)).

```python
    def set_value(self):
        sub_frame = PopUpWindow(self.master)
        self.master.wait_window(sub_frame.top)
        value = float(sub_frame.value)
        showinfo("INFO", "You entered %s (whatever...)." % str(value))
```

The `MainGui.set_value()` function creates a sub-frame by instantiating a `PopUpWindow` object with `MainGui` as master. While the `PopUpWindow` is open, the main window waits for user input in the `PopUpWindow` (`self.master.wait_window(sub_frame.top)`). After closing the window, the function retrieves the user-defined value with `value = float(sub_frame.value)`. Finally, an info window pops up (`showinfo(WINDOW_NAME, MESSAGE)` imported from `tkinter.messagebox`) and recalls the user-defined value (well, this is trivial here ...).


### Using `cTEMPLATE.py` <a name="templategui"></a>

The `cTEMPLATE.TEMPLATE()` class provides a useful frame for programming geospatial calculations, but none of the template routines is obligatory (in contrast to the [above GUI template](#templategui). For using the template class, make the following adaptations to the code block:

```python
class TEMPLATE:
    def __init__(self, *args, **kwargs):
        """
        ...
        """

        # Create a temporary cache folder for, e.g., geospatial analyses; use self.clear_cache() function to delete
        self.cache = os.path.dirname(__file__) + "\\.cache%s\\" % str(random.randint(10000, 99999))
        chk_dir(self.cache)  # from fGlobal

        # Enable logger
        self.logger = logging.getLogger("logfile")
```

-	rename the class from `TEMPLATE` to something meaningful;
-	modify the input arguments of the `__init__(self, *args, **kwargs)` function.

The `cTEMPLATE.TEMPLATE()` class initiates a `self.logger` variable to write calculation progress to a logfile that is created as `RiverArchitect/logfile.log` when *River Architect* is called from the main GUI. This logefile should be used at every critical step where erroneous user input may yield wrong or no result. For example, if a user selects a raster file without valid data, the code should detect and tell the user about the problem using precise `try`-`except` statements. The `cTEMPLATE.TEMPLATE.use_spatial_analyst_function(input_raster_path)` function provides an example for the implementation of such behavior:
<a name="tryexcept"></a>

```python
	try:
		self.logger.info("  >> loading raster %s ..." % str(input_raster_path))
		in_ras = arcpy.Raster(input_raster_path)
	except:
		# go here if the input_raster_path is invalid and write a USEFUL error message
		self.logger.info("ERROR: Game over ... add this error message to RA_wiki/Troubleshooting")
		return -1	
```

In this exemplary code snippet, the command `self.logger.info("  >> loading raster %s ..." % str(input_raster_path))` writes the raster input path to the console window and to the logfile using `self.logger.info()`. If the next step fails (i.e., `arcpy.Raster()` cannot load the provided `input_raster_path` as raster), the user should be informed. This information is passed recorded in the `except:` statement with `self.logger.info("ERROR: Game over ... add this error message to RA_wiki/Troubleshooting")`, which ends with returning `-1` (exits the function because the raster is necessary for all other steps). It would be better to use more precise exception rules such as `except ValueError:`, but we kept the broad "shotgun" approach with `except:` only because we encountered unexpected exception types using `arcpy`. A better and future way of error message logging in *River Architect* will be to use `self.logger.error()` in the exception statement rather than `self.logger.info()`, which should exclusively be used to log calculation progress. **Important is to add error messages, as well as warning messages, to the [Troubleshooting Wiki](Troubleshooting)** ([read more about extending the Wiki](DevWiki)). Use warning messages when a function can still work even though a variable assignment error occurred such as when an optional, additional raster is missing.

Finally, every class should close with a call function, where only the `TEMPLATE` string should be adapted to the new class name:

```python
    def __call__(self, *args, **kwargs):
        # Object call should return class name, file location and class attributes (dir)
        print("Class Info: <type> = TEMPLATE (%s)" % os.path.dirname(__file__))
        print(dir(self))
```

More features of the template are provided with the inline comments in `cTEMPLATE.py`.

## Binding a new tab (module) to the *River Architect* master GUI <a name="bind"></a>
***

New modules need to be bound to the master GUI, either as master-tab or as slave-tab. Both need to added to the `RiverArchitect/master_gui.py` script in the `RA_gui` class's `__init__()` function.

### Binding a New Module with or without submodules
Assuming a new master tab with the name ***NEW MODULE, optionally with *New Sub Modules***, should to be added, which is located in `RiverArchitect/NewModule/new_module_gui.py` (or submodules in `RiverArchitect/NewSubModule1/new_sub1_gui.py` and  `RiverArchitect/NewSubModule2/new_sub2_gui.py`, respectively), the following variables need to be complemented (**attention: the list order is important** - new modules should only be appended at the end of lists):

-	`self.tab_names = ['Get Started', 'Lifespan', 'Morphology', 'Ecohydraulics', 'Project Maker', 'NEW MODULE']`
-	For adding slave (sub) tabs with names `NEW SUB1` and `NEW SUB2`: 
		+ `self.sub_tab_parents = ['Lifespan', 'Morphology', 'Ecohydraulics', 'NEW MODULE']`
		+ `self.sub_tab_names = [['Lifespan Design', 'Max Lifespan'], ['Modify Terrain', 'Volume Assessment'], ['Habitat Area (SHArC)', 'Stranding Risk'], ['NEW SUB1', 'NEW SUB2', ... and so on]]`
-	`self.tab_dir_names`
		+ No sub tabs: `self.tab_dir_names= ['\\GetStarted\\', ['\\LifespanDesign\\', '\\MaxLifespan\\'], ['\\ModifyTerrain\\', '\\VolumeAssessment\\'], ['\\SHArC\\', '\\StrandingRisk\\'], '\\ProjectMaker\\', '\\NewModule\\']` 
		+ With sub tabs located in `RiverArchitect/NewSubModule1/` and  `RiverArchitect/NewSubModule2/`, respectively: `self.tab_dir_names = ['\\GetStarted\\', ['\\LifespanDesign\\', '\\MaxLifespan\\'], ['\\ModifyTerrain\\', '\\VolumeAssessment\\'], ['\\SHArC\\', '\\StrandingRisk\\'], '\\ProjectMaker\\', ['\\NewSubModule1\\', '\\NewSubModule2\\']]`
-	`self.tab_list`
		+ No sub tabs: `self.tab_list= [GetStarted.welcome_gui.MainGui(self.tab_container), ttk.Notebook(self.tab_container), ttk.Notebook(self.tab_container), ttk.Notebook(self.tab_container), ProjectMaker.project_maker_gui.MainGui(self.tab_container), NewModule.new_module_gui.MainGui(self.tab_container)]`
		+ With sub tabs: `self.tab_list= [GetStarted.welcome_gui.MainGui(self.tab_container), ttk.Notebook(self.tab_container), ttk.Notebook(self.tab_container), ttk.Notebook(self.tab_container), ProjectMaker.project_maker_gui.MainGui(self.tab_container), ttk.Notebook(self.tab_container)]`
- 	With sub tabs: `self.sub_tab_list = [[LifespanDesign.lifespan_design_gui.FaGui(self.tabs['Lifespan']), MaxLifespan.action_gui.ActionGui(self.tabs['Lifespan'])],  [ModifyTerrain.modify_terrain_gui.MainGui(self.tabs['Morphology']),  VolumeAssessment.volume_gui.MainGui(self.tabs['Morphology'])], [SHArC.sharc_gui.MainGui(self.tabs['Ecohydraulics']), StrandingRisk.connect_gui.MainGui(self.tabs['Ecohydraulics'])], [NewSubModule1.new_sub1_gui.MainGui(self.tabs['NEW SUB1']), NewSubModule2.new_sub2_gui.MainGui(self.tabs['NEW SUB2'])]]`


### Binding a New Sub-Module to an existing module

The following list indicates variables to be modified when a new sub-module (slave or sub-tab) is added to an existing module. The example assumes the creation of a sub-tab called `RiverCreator` to the `Morphology` module.

-	Verify that the `Morphology` tab is mentioned in  `self.sub_tab_parents = ['Lifespan', 'Morphology', 'Ecohydraulics', 'NEW MODULE']`
-	Add `RIVER CREATOR` to the second nested list in `self.sub_tab_names = [['Lifespan Design', 'Max Lifespan'], ['Modify Terrain', 'Volume Assessment', 'RIVER CREATOR'], ['Habitat Area (SHArC)', 'Stranding Risk']]`; the second nested list must be chosen because `Morphology` is the second item in `self.sub_tab_parents`
-	Assuming that the new module is located in `RiverArchitect/RiverCreator`, modify `self.tab_dir_names = ['\\GetStarted\\', ['\\LifespanDesign\\', '\\MaxLifespan\\'], ['\\ModifyTerrain\\', '\\VolumeAssessment\\', '\\RiverCreator\\'], ['\\SHArC\\', '\\StrandingRisk\\'], '\\ProjectMaker\\', ['\\NewSubModule1\\', '\\NewSubModule2\\']]`
- 	Withe the asumption that the new *River Creator* GUI is located in `RiverArchitect/RiverCreator/rc_gui.py`, modify `self.sub_tab_list = [[LifespanDesign.lifespan_design_gui.FaGui(self.tabs['Lifespan']), MaxLifespan.action_gui.ActionGui(self.tabs['Lifespan'])], [ModifyTerrain.modify_terrain_gui.MainGui(self.tabs['Morphology']), VolumeAssessment.volume_gui.MainGui(self.tabs['Morphology']),  RiverCreator.rc_gui.MainGui(self.tabs['River Creator'])], [SHArC.sharc_gui.MainGui(self.tabs['Ecohydraulics']), StrandingRisk.connect_gui.MainGui(self.tabs['Ecohydraulics'])]]`


**Please do not forget to [update the wiki](DevWiki) and test new code!**


# Full list of folders and files <a name="struc"></a>

***

This is the full list of files and folders in the `RiverArchitect/program` repository. Please update after adding or deleting files. The file list can be generated (in Windows) with *PowerShell*: Enter `Get-ChildItem -Path D:\path-to-local-copy-of-RiverArchitect\program -Recurse` and copy-paste the comand line output.

```

RiverArchitect\program
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----        7/26/2019  11:38 AM                .github
d-----        7/26/2019  11:39 AM                .site_packages
d-----        7/26/2019  11:39 AM                00_Flows
d-----        7/26/2019  11:39 AM                01_Conditions
d-----        7/26/2019  11:39 AM                02_Maps
d-----       11/22/2019  10:17 AM                StrandingRisk
d-----        7/26/2019  11:39 AM                docs
d-----       11/19/2019  12:40 PM                GetStarted
d-----        7/26/2019  11:39 AM                LifespanDesign
d-----        7/26/2019  11:39 AM                MaxLifespan
d-----        10/2/2019   9:57 AM                ModifyTerrain
d-----        11/5/2019   1:57 PM                ProjectMaker
d-----        10/2/2019   9:57 AM                SHArC
d-----       11/25/2019   1:04 PM                Tools
d-----        7/26/2019  11:39 AM                VolumeAssessment
-a----       11/13/2019   8:47 AM             22 .gitignore
-a----         9/4/2019   5:04 PM           1540 LICENSE
-a----       11/22/2019  10:17 AM           6458 master_gui.py
-a----        7/26/2019  11:39 AM           5856 README.md
-a----        11/4/2019  12:33 PM          11594 slave_gui.py
-a----        7/26/2019  11:39 AM            619 Start_River_Architect.bat


RiverArchitect\program\.github
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----        7/26/2019  11:38 AM                ISSUE_TEMPLATE


RiverArchitect\program\.github\ISSUE_TEMPLATE
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:38 AM            834 bug_report.md
-a----        7/26/2019  11:38 AM            126 custom.md
-a----        7/26/2019  11:38 AM            595 feature_request.md


RiverArchitect\program\.site_packages
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----        7/26/2019  11:39 AM                openpyxl
d-----       11/19/2019  12:40 PM                riverpy
d-----        7/26/2019  11:39 AM                templates
-a----        7/26/2019  11:38 AM             23 info.md


RiverArchitect\program\.site_packages\openpyxl
---- TRUNCATED ---- DEPRECATED MODULE BINDINGS

RiverArchitect\program\.site_packages\riverpy
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM           7131 cDefinitions.py
-a----        7/26/2019  11:39 AM           4141 cFeatures.py
-a----        7/26/2019  11:39 AM           5840 cFish.py
-a----       11/19/2019  12:40 PM          19563 cFlows.py
-a----        7/26/2019  11:39 AM          12334 cInputOutput.py
-a----        7/26/2019  11:39 AM           2550 cInterpolator.py
-a----        7/26/2019  11:39 AM           2470 cLogger.py
-a----        7/26/2019  11:39 AM          10583 cMakeTable.py
-a----       11/18/2019   2:11 PM          23510 cMapper.py
-a----         8/6/2019   8:03 AM           2899 config.py
-a----        7/26/2019  11:39 AM           9290 cReachManager.py
-a----        7/26/2019  11:39 AM           4245 cThresholdDirector.py
-a----        9/17/2019  10:03 AM          21388 fGlobal.py
-a----        7/26/2019  11:39 AM            120 __init__.py


RiverArchitect\program\.site_packages\templates
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM          70862 code_icon.ico
-a----       11/19/2019  11:35 AM            134 credits.txt
-a----        7/26/2019  11:39 AM           6172 empty.xlsx
-a----        7/26/2019  11:39 AM          34208 Fish.xlsx
-a----        7/26/2019  11:39 AM          40751 morphological_units.xlsx
-a----        7/26/2019  11:39 AM            164 oups.txt


RiverArchitect\program\00_Flows
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----        7/26/2019  11:39 AM                InputFlowSeries
d-----       11/21/2019   6:10 PM                templates
-a----        7/26/2019  11:39 AM             38 info.md


RiverArchitect\program\00_Flows\InputFlowSeries
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM         252121 flow_series_example_data.xlsx


RiverArchitect\program\00_Flows\templates
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----       11/21/2019   6:10 PM         188246 disc_freq_template.xlsx
-a----        7/26/2019  11:39 AM         205163 flow_duration_template.xlsx
-a----        7/26/2019  11:39 AM          15163 flow_return_period_template.xlsx


RiverArchitect\program\01_Conditions
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----        7/26/2019  11:39 AM                none
-a----        7/26/2019  11:39 AM       13258925 20XX_sample.zip
-a----        7/26/2019  11:39 AM            208 README.md


RiverArchitect\program\01_Conditions\none
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM            111 info.txt
-a----        7/26/2019  11:39 AM             60 __init__.py


RiverArchitect\program\02_Maps
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----        7/26/2019  11:39 AM                templates


RiverArchitect\program\02_Maps\templates
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----        7/26/2019  11:39 AM                Index
d-----        7/26/2019  11:39 AM                legend
d-----        7/26/2019  11:39 AM                rasters
d-----        7/29/2019   5:48 PM                river_template.gdb
d-----        7/29/2019   5:48 PM                scratch.gdb
d-----        7/26/2019  11:39 AM                symbology
-a----        7/26/2019  11:39 AM         475672 river_template.aprx
-a----        7/26/2019  11:39 AM           4096 river_template.tbx


RiverArchitect\program\02_Maps\templates\Index
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----        7/26/2019  11:39 AM                river_map_template
d-----        7/26/2019  11:39 AM                river_template
d-----        7/26/2019  11:39 AM                Thumbnail


RiverArchitect\program\02_Maps\templates\Index\river_map_template
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM             75 log.txt
-a----        7/26/2019  11:39 AM             20 segments.gen
-a----        7/26/2019  11:39 AM            200 segments_2
-a----        7/26/2019  11:39 AM           1509 _0.cfs


RiverArchitect\program\02_Maps\templates\Index\river_template
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM             71 log.txt
-a----        7/26/2019  11:39 AM             20 segments.gen
-a----        7/26/2019  11:39 AM           2580 segments_12
-a----        7/26/2019  11:39 AM           2075 segments_z
-a----        7/26/2019  11:39 AM            977 _10.cfs
-a----        7/26/2019  11:39 AM           6183 _m.cfs
-a----        7/26/2019  11:39 AM            673 _n.cfs
-a----        7/26/2019  11:39 AM              9 _n_1.del
-a----        7/26/2019  11:39 AM            807 _o.cfs
-a----        7/26/2019  11:39 AM            688 _p.cfs
-a----        7/26/2019  11:39 AM              9 _p_1.del
-a----        7/26/2019  11:39 AM            837 _q.cfs
-a----        7/26/2019  11:39 AM            688 _r.cfs
-a----        7/26/2019  11:39 AM              9 _r_1.del
-a----        7/26/2019  11:39 AM            805 _s.cfs
-a----        7/26/2019  11:39 AM            688 _t.cfs
-a----        7/26/2019  11:39 AM              9 _t_1.del
-a----        7/26/2019  11:39 AM            849 _u.cfs
-a----        7/26/2019  11:39 AM            789 _v.cfs
-a----        7/26/2019  11:39 AM            805 _w.cfs
-a----        7/26/2019  11:39 AM            804 _x.cfs
-a----        7/26/2019  11:39 AM            737 _y.cfs
-a----        7/26/2019  11:39 AM              9 _y_1.del
-a----        7/26/2019  11:39 AM            973 _z.cfs
-a----        7/26/2019  11:39 AM              9 _z_1.del


RiverArchitect\program\02_Maps\templates\Index\Thumbnail
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM              0 indx
-a----        7/26/2019  11:39 AM           4208 layers.jpg
-a----        7/26/2019  11:39 AM           5833 layers12.jpg
-a----        7/26/2019  11:39 AM           5611 layers2.jpg
-a----        7/26/2019  11:39 AM           6006 layers22.jpg
-a----        7/26/2019  11:39 AM           5851 layers32.jpg
-a----        7/26/2019  11:39 AM           4823 layers5.jpg
-a----        7/26/2019  11:39 AM           5789 layers7.jpg
-a----        7/26/2019  11:39 AM           4346 map.jpg


RiverArchitect\program\02_Maps\templates\legend
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM        1120768 legend.ServerStyle
-a----        7/26/2019  11:39 AM        1622016 legend.style


RiverArchitect\program\02_Maps\templates\rasters
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----        7/26/2019  11:39 AM                ds_bio_s0
d-----        7/26/2019  11:39 AM                ds_elj_dwc
d-----        7/26/2019  11:39 AM                ds_finese_d15
d-----        7/26/2019  11:39 AM                ds_finese_d85
d-----        7/26/2019  11:39 AM                ds_sidec
d-----        7/26/2019  11:39 AM                ds_sidech110
d-----        7/26/2019  11:39 AM                ds_sym_d
d-----        7/26/2019  11:39 AM                ds_widen
d-----        7/26/2019  11:39 AM                lf_sym
-a----        7/29/2019   5:48 PM           1400 ds_bio_s0.aux.xml
-a----        7/29/2019   5:48 PM           1383 ds_elj_dwc.aux.xml
-a----        7/29/2019   5:48 PM           1413 ds_finese_d15.aux.xml
-a----        7/29/2019   5:48 PM           1387 ds_finese_d85.aux.xml
-a----        7/29/2019   5:48 PM           1487 ds_sidec.aux.xml
-a----        7/29/2019   5:48 PM           1407 ds_sidech110.aux.xml
-a----        7/29/2019   5:48 PM           2335 ds_sym_D.aux.xml
-a----        7/29/2019   5:48 PM            504 ds_widen.aux.xml
-a----        7/26/2019  11:39 AM        1274552 layout_lf.xml
-a----        7/29/2019   5:48 PM           2316 lf_sym.aux.xml


RiverArchitect\program\02_Maps\templates\rasters\ds_bio_s0
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM             32 dblbnd.adf
-a----        7/26/2019  11:39 AM            308 hdr.adf
-a----        7/26/2019  11:39 AM            358 prj.adf
-a----        7/26/2019  11:39 AM             32 sta.adf
-a----        7/26/2019  11:39 AM          98486 w001001.adf
-a----        7/26/2019  11:39 AM            428 w001001x.adf


RiverArchitect\program\02_Maps\templates\rasters\ds_elj_dwc
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM             32 dblbnd.adf
-a----        7/26/2019  11:39 AM            308 hdr.adf
-a----        7/26/2019  11:39 AM            170 prj.adf
-a----        7/26/2019  11:39 AM             32 sta.adf
-a----        7/26/2019  11:39 AM          49286 w001001.adf
-a----        7/26/2019  11:39 AM            236 w001001x.adf


RiverArchitect\program\02_Maps\templates\rasters\ds_finese_d15
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM             32 dblbnd.adf
-a----        7/26/2019  11:39 AM            308 hdr.adf
-a----        7/26/2019  11:39 AM            170 prj.adf
-a----        7/26/2019  11:39 AM             32 sta.adf
-a----        7/26/2019  11:39 AM          98486 w001001.adf
-a----        7/26/2019  11:39 AM            428 w001001x.adf


RiverArchitect\program\02_Maps\templates\rasters\ds_finese_d85
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM             32 dblbnd.adf
-a----        7/26/2019  11:39 AM            308 hdr.adf
-a----        7/26/2019  11:39 AM            170 prj.adf
-a----        7/26/2019  11:39 AM             32 sta.adf
-a----        7/26/2019  11:39 AM          49286 w001001.adf
-a----        7/26/2019  11:39 AM            236 w001001x.adf


RiverArchitect\program\02_Maps\templates\rasters\ds_sidec
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM             32 dblbnd.adf
-a----        7/26/2019  11:39 AM            308 hdr.adf
-a----        7/29/2019   5:48 PM            358 prj.adf
-a----        7/26/2019  11:39 AM             32 sta.adf
-a----        7/26/2019  11:39 AM              8 vat.adf
-a----        7/26/2019  11:39 AM           1662 w001001.adf
-a----        7/26/2019  11:39 AM            428 w001001x.adf


RiverArchitect\program\02_Maps\templates\rasters\ds_sidech110
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM             32 dblbnd.adf
-a----        7/26/2019  11:39 AM            308 hdr.adf
-a----        7/26/2019  11:39 AM            358 prj.adf
-a----        7/26/2019  11:39 AM             32 sta.adf
-a----        7/26/2019  11:39 AM          49286 w001001.adf
-a----        7/26/2019  11:39 AM            236 w001001x.adf


RiverArchitect\program\02_Maps\templates\rasters\ds_sym_d
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM             32 dblbnd.adf
-a----        7/26/2019  11:39 AM            308 hdr.adf
-a----        7/29/2019   5:48 PM            358 prj.adf
-a----        7/26/2019  11:39 AM             32 sta.adf
-a----        7/26/2019  11:39 AM          32886 w001001.adf
-a----        7/26/2019  11:39 AM            172 w001001x.adf


RiverArchitect\program\02_Maps\templates\rasters\ds_widen
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM             32 dblbnd.adf
-a----        7/26/2019  11:39 AM            308 hdr.adf
-a----        7/26/2019  11:39 AM            358 prj.adf
-a----        7/26/2019  11:39 AM             32 sta.adf
-a----        7/26/2019  11:39 AM              8 vat.adf
-a----        7/26/2019  11:39 AM          98486 w001001.adf
-a----        7/26/2019  11:39 AM            428 w001001x.adf


RiverArchitect\program\02_Maps\templates\rasters\lf_sym
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM             32 dblbnd.adf
-a----        7/26/2019  11:39 AM            308 hdr.adf
-a----        7/29/2019   5:48 PM            358 prj.adf
-a----        7/26/2019  11:39 AM             32 sta.adf
-a----        7/26/2019  11:39 AM          98486 w001001.adf
-a----        7/26/2019  11:39 AM            428 w001001x.adf


RiverArchitect\program\02_Maps\templates\river_template.gdb
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM            110 a00000001.gdbindexes
-a----        7/26/2019  11:39 AM            302 a00000001.gdbtable
-a----        7/26/2019  11:39 AM           5152 a00000001.gdbtablx
-a----        7/26/2019  11:39 AM           4118 a00000001.TablesByName.atx
-a----        7/26/2019  11:39 AM           2055 a00000002.gdbtable
-a----        7/26/2019  11:39 AM           5152 a00000002.gdbtablx
-a----        7/26/2019  11:39 AM             42 a00000003.gdbindexes
-a----        7/26/2019  11:39 AM            525 a00000003.gdbtable
-a----        7/26/2019  11:39 AM           5152 a00000003.gdbtablx
-a----        7/26/2019  11:39 AM           4118 a00000004.CatItemsByPhysicalName.atx
-a----        7/26/2019  11:39 AM           4118 a00000004.CatItemsByType.atx
-a----        7/26/2019  11:39 AM           4118 a00000004.FDO_UUID.atx
-a----        7/26/2019  11:39 AM            310 a00000004.gdbindexes
-a----        7/26/2019  11:39 AM           1712 a00000004.gdbtable
-a----        7/26/2019  11:39 AM           5152 a00000004.gdbtablx
-a----        7/26/2019  11:39 AM           4118 a00000004.spx
-a----        7/26/2019  11:39 AM          12310 a00000005.CatItemTypesByName.atx
-a----        7/26/2019  11:39 AM           4118 a00000005.CatItemTypesByParentTypeID.atx
-a----        7/26/2019  11:39 AM           4118 a00000005.CatItemTypesByUUID.atx
-a----        7/26/2019  11:39 AM            296 a00000005.gdbindexes
-a----        7/26/2019  11:39 AM           2074 a00000005.gdbtable
-a----        7/26/2019  11:39 AM           5152 a00000005.gdbtablx
-a----        7/26/2019  11:39 AM           4118 a00000006.CatRelsByDestinationID.atx
-a----        7/26/2019  11:39 AM           4118 a00000006.CatRelsByOriginID.atx
-a----        7/26/2019  11:39 AM           4118 a00000006.CatRelsByType.atx
-a----        7/26/2019  11:39 AM           4118 a00000006.FDO_UUID.atx
-a----        7/26/2019  11:39 AM            318 a00000006.gdbindexes
-a----        7/26/2019  11:39 AM            190 a00000006.gdbtable
-a----        7/26/2019  11:39 AM             32 a00000006.gdbtablx
-a----        7/26/2019  11:39 AM          12310 a00000007.CatRelTypesByBackwardLabel.atx
-a----        7/26/2019  11:39 AM           4118 a00000007.CatRelTypesByDestItemTypeID.atx
-a----        7/26/2019  11:39 AM          12310 a00000007.CatRelTypesByForwardLabel.atx
-a----        7/26/2019  11:39 AM          12310 a00000007.CatRelTypesByName.atx
-a----        7/26/2019  11:39 AM           4118 a00000007.CatRelTypesByOriginItemTypeID.atx
-a----        7/26/2019  11:39 AM           4118 a00000007.CatRelTypesByUUID.atx
-a----        7/26/2019  11:39 AM            602 a00000007.gdbindexes
-a----        7/26/2019  11:39 AM           3479 a00000007.gdbtable
-a----        7/26/2019  11:39 AM           5152 a00000007.gdbtablx
-a----        7/26/2019  11:39 AM              4 gdb
-a----        7/26/2019  11:39 AM            400 timestamps


RiverArchitect\program\02_Maps\templates\scratch.gdb
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM            110 a00000001.gdbindexes
-a----        7/26/2019  11:39 AM            302 a00000001.gdbtable
-a----        7/26/2019  11:39 AM           5152 a00000001.gdbtablx
-a----        7/26/2019  11:39 AM           4118 a00000001.TablesByName.atx
-a----        7/26/2019  11:39 AM           2055 a00000002.gdbtable
-a----        7/26/2019  11:39 AM           5152 a00000002.gdbtablx
-a----        7/26/2019  11:39 AM             42 a00000003.gdbindexes
-a----        7/26/2019  11:39 AM            525 a00000003.gdbtable
-a----        7/26/2019  11:39 AM           5152 a00000003.gdbtablx
-a----        7/26/2019  11:39 AM           4118 a00000004.CatItemsByPhysicalName.atx
-a----        7/26/2019  11:39 AM           4118 a00000004.CatItemsByType.atx
-a----        7/26/2019  11:39 AM           4118 a00000004.FDO_UUID.atx
-a----        7/26/2019  11:39 AM            310 a00000004.gdbindexes
-a----        7/26/2019  11:39 AM           1712 a00000004.gdbtable
-a----        7/26/2019  11:39 AM           5152 a00000004.gdbtablx
-a----        7/26/2019  11:39 AM           4118 a00000004.spx
-a----        7/26/2019  11:39 AM          12310 a00000005.CatItemTypesByName.atx
-a----        7/26/2019  11:39 AM           4118 a00000005.CatItemTypesByParentTypeID.atx
-a----        7/26/2019  11:39 AM           4118 a00000005.CatItemTypesByUUID.atx
-a----        7/26/2019  11:39 AM            296 a00000005.gdbindexes
-a----        7/26/2019  11:39 AM           2074 a00000005.gdbtable
-a----        7/26/2019  11:39 AM           5152 a00000005.gdbtablx
-a----        7/26/2019  11:39 AM           4118 a00000006.CatRelsByDestinationID.atx
-a----        7/26/2019  11:39 AM           4118 a00000006.CatRelsByOriginID.atx
-a----        7/26/2019  11:39 AM           4118 a00000006.CatRelsByType.atx
-a----        7/26/2019  11:39 AM           4118 a00000006.FDO_UUID.atx
-a----        7/26/2019  11:39 AM            318 a00000006.gdbindexes
-a----        7/26/2019  11:39 AM            190 a00000006.gdbtable
-a----        7/26/2019  11:39 AM             32 a00000006.gdbtablx
-a----        7/26/2019  11:39 AM          12310 a00000007.CatRelTypesByBackwardLabel.atx
-a----        7/26/2019  11:39 AM           4118 a00000007.CatRelTypesByDestItemTypeID.atx
-a----        7/26/2019  11:39 AM          12310 a00000007.CatRelTypesByForwardLabel.atx
-a----        7/26/2019  11:39 AM          12310 a00000007.CatRelTypesByName.atx
-a----        7/26/2019  11:39 AM           4118 a00000007.CatRelTypesByOriginItemTypeID.atx
-a----        7/26/2019  11:39 AM           4118 a00000007.CatRelTypesByUUID.atx
-a----        7/26/2019  11:39 AM            602 a00000007.gdbindexes
-a----        7/26/2019  11:39 AM           3479 a00000007.gdbtable
-a----        7/26/2019  11:39 AM           5152 a00000007.gdbtablx
-a----        7/26/2019  11:39 AM              4 gdb
-a----        7/26/2019  11:39 AM            400 timestamps


RiverArchitect\program\02_Maps\templates\symbology
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM           7666 LifespanRasterSymbology.lyrx


RiverArchitect\program\StrandingRisk
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----        8/20/2019  12:22 PM                .templates
-a----       11/21/2019   6:10 PM          28031 cConnectivityAnalysis.py
-a----       11/22/2019  10:17 AM          16505 cGraph.py
-a----       11/19/2019  12:40 PM          12408 connect_gui.py
-a----       11/19/2019  12:40 PM           4199 cRatingCurves.py
-a----        7/26/2019  11:39 AM             84 __init__.py


RiverArchitect\program\StrandingRisk\.templates
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        8/20/2019  12:22 PM         191729 disconnected_area_template.xlsx


RiverArchitect\program\docs
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM           3358 CODE_OF_CONDUCT.md
-a----        7/26/2019  11:39 AM           7504 CONTRIBUTING.md
-a----        7/26/2019  11:39 AM            802 PULL_REQUEST_TEMPLATE.md


RiverArchitect\program\GetStarted
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----        7/26/2019  11:39 AM                .templates
-a----       11/19/2019  12:40 PM          18968 cConditionCreator.py
-a----        7/26/2019  11:39 AM           7321 cDetrendedDEM.py
-a----        7/26/2019  11:39 AM           4387 cMakeInp.py
-a----        7/26/2019  11:39 AM           8722 cMorphUnits.py
-a----        8/20/2019  12:22 PM          19556 cWaterLevel.py
-a----        7/26/2019  11:39 AM           3542 fSubCondition.py
-a----       10/30/2019   4:27 PM           4851 popup_align_rasters.py
-a----        11/4/2019  10:43 AM          10762 popup_analyze_q.py
-a----       10/30/2019   4:27 PM          18197 popup_create_c.py
-a----        9/17/2019  10:19 AM           7493 popup_create_c_sub.py
-a----        7/26/2019  11:39 AM           4329 popup_make_inp.py
-a----        9/17/2019  10:19 AM          13449 popup_populate_c.py
-a----       10/30/2019   4:27 PM           6226 welcome_gui.py
-a----        7/26/2019  11:39 AM             80 __init__.py


RiverArchitect\program\GetStarted\.templates
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM         143253 welcome.gif


RiverArchitect\program\LifespanDesign
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----       11/25/2019   6:43 PM                .templates
d-----        7/26/2019  11:39 AM                Output
-a----       10/24/2019   2:47 PM          53673 cLifespanDesignAnalysis.py
-a----       10/29/2019   6:17 PM          10816 cParameters.py
-a----        7/26/2019  11:39 AM           5776 cReadInpLifespan.py
-a----       10/23/2019   3:48 PM          16584 feature_analysis.py
-a----       11/25/2019   4:10 PM          21688 lifespan_design_gui.py
-a----        7/26/2019  11:39 AM            113 __init__.py


RiverArchitect\program\LifespanDesign\.templates
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM            703 mapping.inp
-a----        7/26/2019  11:39 AM            773 mapping_full.inp
-a----        7/26/2019  11:39 AM          11323 prepare_map_coordinates.xlsx
-a----       11/25/2019   4:10 PM          23190 threshold_values.xlsx


RiverArchitect\program\LifespanDesign\Output
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----        7/26/2019  11:39 AM                Rasters


RiverArchitect\program\LifespanDesign\Output\Rasters
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM             58 __init__.py


RiverArchitect\program\MaxLifespan
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----        7/26/2019  11:39 AM                .templates
d-----        7/26/2019  11:39 AM                Output
-a----       11/25/2019   4:11 PM          14301 action_gui.py
-a----        7/26/2019  11:39 AM           2934 action_planner.py
-a----        7/26/2019  10:50 AM          11193 cActionAssessment.py
-a----        7/26/2019  11:39 AM           3558 cFeatureActions.py
-a----        7/26/2019  11:39 AM            102 __init__.py


RiverArchitect\program\MaxLifespan\.templates
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----        7/26/2019  11:39 AM                rasters
-a----        7/26/2019  11:39 AM            704 mapping.inp
-a----        7/26/2019  11:39 AM          11323 prepare_map_coordinates.xlsx


RiverArchitect\program\MaxLifespan\.templates\rasters
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM             91 zeros.tfw
-a----        7/26/2019  11:39 AM           9445 zeros.tif
-a----        7/26/2019  11:39 AM            364 zeros.tif.aux.xml


RiverArchitect\program\MaxLifespan\Output
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----        7/26/2019  11:39 AM                Rasters


RiverArchitect\program\MaxLifespan\Output\Rasters
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM             62 __init__.py


RiverArchitect\program\ModifyTerrain
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----        7/26/2019  11:39 AM                .templates
d-----        7/26/2019  11:39 AM                Output
d-----        7/26/2019  11:39 AM                RiverBuilder
-a----        7/26/2019  10:39 AM          12435 cModifyTerrain.py
-a----        7/26/2019  11:39 AM           1941 cRiverBuilder.py
-a----        7/26/2019  11:39 AM          12125 cRiverBuilderConstruct.py
-a----         8/6/2019   8:03 AM          13861 modify_terrain_gui.py
-a----        7/26/2019  11:39 AM           3777 riverbuilder_input_example.txt
-a----        9/17/2019  10:27 AM          15650 sub_gui_rb.py
-a----        7/26/2019  11:39 AM             87 __init__.py


RiverArchitect\program\ModifyTerrain\.templates
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM         382805 chnl_xs_parameters.gif
-a----        7/26/2019  11:39 AM          10681 computation_extents.xlsx
-a----        7/26/2019  11:39 AM        1024000 determine_extents.mxd
-a----        7/26/2019  11:39 AM            593 determine_extents.xml
-a----        7/26/2019  11:39 AM            704 mapping.inp
-a----        7/26/2019  11:39 AM          11323 prepare_map_coordinates.xlsx


RiverArchitect\program\ModifyTerrain\Output
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----        7/26/2019  11:39 AM                Grade
d-----        7/26/2019  11:39 AM                RiverBuilder
d-----        7/26/2019  11:39 AM                Widen


RiverArchitect\program\ModifyTerrain\Output\Grade
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM             62 __init__.py


RiverArchitect\program\ModifyTerrain\Output\RiverBuilder
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM             62 __init__.py


RiverArchitect\program\ModifyTerrain\Output\Widen
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM             62 __init__.py


RiverArchitect\program\ModifyTerrain\RiverBuilder
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----        7/26/2019  11:39 AM                messages
-a----        7/26/2019  11:39 AM          45428 riverbuilder.r
-a----        7/26/2019  11:39 AM           3117 RiverBuilderRenderer.py


RiverArchitect\program\ModifyTerrain\RiverBuilder\messages
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM            537 chnl_xs_pts.txt
-a----        7/26/2019  11:39 AM            391 d50.txt
-a----        7/26/2019  11:39 AM            730 datum.txt
-a----        7/26/2019  11:39 AM             81 dy.txt
-a----        7/26/2019  11:39 AM            292 floodplain_outer_height.txt
-a----        7/26/2019  11:39 AM            270 h_bf.txt
-a----        7/26/2019  11:39 AM            381 length.txt
-a----        7/26/2019  11:39 AM            935 sub_curvature.txt
-a----        7/26/2019  11:39 AM            285 sub_floodplain_l.txt
-a----        7/26/2019  11:39 AM            150 sub_floodplain_r.txt
-a----        7/26/2019  11:39 AM            568 sub_meander.txt
-a----        7/26/2019  11:39 AM            149 sub_thalweg.txt
-a----        7/26/2019  11:39 AM            667 sub_w_bf.txt
-a----        7/26/2019  11:39 AM            204 s_valley.txt
-a----        7/26/2019  11:39 AM            572 taux.txt
-a----        7/26/2019  11:39 AM            300 terrace_outer_height.txt
-a----        7/26/2019  11:39 AM           1391 user_functions.txt
-a----        7/26/2019  11:39 AM            150 w_bf.txt
-a----        7/26/2019  11:39 AM            431 w_bf_min.txt
-a----        7/26/2019  11:39 AM            343 w_boundary.txt
-a----        7/26/2019  11:39 AM            831 w_floodplain.txt
-a----        7/26/2019  11:39 AM            419 w_terrace.txt
-a----        7/26/2019  11:39 AM            585 xs_shape.txt
-a----        7/26/2019  11:39 AM            553 x_res.txt


RiverArchitect\program\ProjectMaker
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----        7/29/2019   5:48 PM                .templates
-a----        10/2/2019   9:57 AM          10092 cSHArC.py
-a----        7/26/2019  11:39 AM           4245 fFunctions.py
-a----       11/25/2019   4:13 PM          34810 project_maker_gui.py
-a----       11/19/2019   9:32 AM          11784 s20_plantings_delineation.py
-a----       11/19/2019   9:43 AM           8778 s21_plantings_stabilization.py
-a----       10/24/2019   2:19 PM          11928 s30_terrain_stabilization.py
-a----       11/12/2019   2:21 PM           8488 s40_compare_sharea.py
-a----        7/26/2019  11:39 AM            217 __init__.py


RiverArchitect\program\ProjectMaker\.templates
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----       11/25/2019   4:08 PM                Project_vii_TEMPLATE
-a----        7/26/2019  11:39 AM              5 area_dummy.cpg
-a----        7/26/2019  11:39 AM            118 area_dummy.dbf
-a----        7/26/2019  11:39 AM            132 area_dummy.sbn
-a----        7/26/2019  11:39 AM            116 area_dummy.sbx
-a----        7/26/2019  11:39 AM            220 area_dummy.shp
-a----        7/26/2019  11:39 AM            108 area_dummy.shx


RiverArchitect\program\ProjectMaker\.templates\Project_vii_TEMPLATE
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----       11/19/2019  10:27 AM                Geodata
d-----        7/26/2019  11:39 AM                Index
d-----       10/30/2019   5:57 PM                ProjectMaps.gdb
d-----       11/19/2019   9:41 AM                Quantities
-a----        11/7/2019   5:51 PM         203109 ProjectMaps.aprx
-a----        4/26/2019   9:43 AM           4096 ProjectMaps.tbx
-a----       11/25/2019   4:07 PM          35894 Project_assessment_vii.xlsx


RiverArchitect\program\ProjectMaker\.templates\Project_vii_TEMPLATE\Geodata
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----       11/19/2019   9:12 AM                Rasters
d-----       11/19/2019   9:12 AM                Shapefiles
-a----        7/26/2019  11:39 AM          20814 SHArea_evaluation_template_si.xlsx
-a----        7/26/2019  11:39 AM          20797 SHArea_evaluation_template_us.xlsx


RiverArchitect\program\ProjectMaker\.templates\Project_vii_TEMPLATE\Geodata\Rasters
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----       11/19/2019   9:12 AM             10 __init__.py


RiverArchitect\program\ProjectMaker\.templates\Project_vii_TEMPLATE\Geodata\Shapefiles
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----       11/19/2019   9:12 AM             10 __init__.py


RiverArchitect\program\ProjectMaker\.templates\Project_vii_TEMPLATE\Index
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----        11/5/2019   1:57 PM                ProjectMaps
d-----        7/26/2019  11:39 AM                Thumbnail


RiverArchitect\program\ProjectMaker\.templates\Project_vii_TEMPLATE\Index\ProjectMaps
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        4/26/2019  10:18 AM             20 segments.gen
-a----        4/26/2019  10:18 AM           1067 segments_9
-a----        4/26/2019   9:43 AM           1122 _1.cfs
-a----        4/26/2019   9:43 AM            633 _2.cfs
-a----        4/26/2019  10:17 AM            669 _3.cfs
-a----        4/26/2019  10:18 AM              9 _3_1.del
-a----        4/26/2019  10:17 AM            812 _4.cfs
-a----        4/26/2019  10:18 AM            708 _5.cfs
-a----        4/26/2019  10:18 AM              9 _5_1.del
-a----        4/26/2019  10:18 AM            806 _6.cfs


RiverArchitect\program\ProjectMaker\.templates\Project_vii_TEMPLATE\Index\Thumbnail
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        4/26/2019  10:17 AM              0 indx
-a----        4/26/2019  10:18 AM           1827 layers.jpg


RiverArchitect\program\ProjectMaker\.templates\Project_vii_TEMPLATE\ProjectMaps.gdb
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        4/26/2019   9:43 AM            110 a00000001.gdbindexes
-a----       10/25/2019   8:54 AM            338 a00000001.gdbtable
-a----       10/25/2019   8:54 AM           5152 a00000001.gdbtablx
-a----       10/25/2019   8:54 AM           4118 a00000001.TablesByName.atx
-a----        4/26/2019   9:43 AM           2055 a00000002.gdbtable
-a----        4/26/2019   9:43 AM           5152 a00000002.gdbtablx
-a----        4/26/2019   9:43 AM             42 a00000003.gdbindexes
-a----        4/26/2019   9:43 AM            525 a00000003.gdbtable
-a----        4/26/2019   9:43 AM           5152 a00000003.gdbtablx
-a----       10/25/2019   8:54 AM           4118 a00000004.CatItemsByPhysicalName.atx
-a----       10/25/2019   8:54 AM           4118 a00000004.CatItemsByType.atx
-a----       10/25/2019   8:54 AM           4118 a00000004.FDO_UUID.atx
-a----       10/25/2019   8:54 AM           8536 a00000004.freelist
-a----        4/26/2019   9:43 AM            310 a00000004.gdbindexes
-a----       10/25/2019   8:54 AM          24787 a00000004.gdbtable
-a----       10/25/2019   8:54 AM           5152 a00000004.gdbtablx
-a----       10/25/2019   8:54 AM           4118 a00000004.spx
-a----        4/26/2019   9:43 AM          12310 a00000005.CatItemTypesByName.atx
-a----        4/26/2019   9:43 AM           4118 a00000005.CatItemTypesByParentTypeID.atx
-a----        4/26/2019   9:43 AM           4118 a00000005.CatItemTypesByUUID.atx
-a----        4/26/2019   9:43 AM            296 a00000005.gdbindexes
-a----        4/26/2019   9:43 AM           2074 a00000005.gdbtable
-a----        4/26/2019   9:43 AM           5152 a00000005.gdbtablx
-a----       10/25/2019   8:54 AM           4118 a00000006.CatRelsByDestinationID.atx
-a----       10/25/2019   8:54 AM           4118 a00000006.CatRelsByOriginID.atx
-a----       10/25/2019   8:54 AM           4118 a00000006.CatRelsByType.atx
-a----       10/25/2019   8:54 AM           4118 a00000006.FDO_UUID.atx
-a----        4/26/2019   9:43 AM            318 a00000006.gdbindexes
-a----       10/25/2019   8:54 AM            263 a00000006.gdbtable
-a----       10/25/2019   8:54 AM           5152 a00000006.gdbtablx
-a----        4/26/2019   9:43 AM          12310 a00000007.CatRelTypesByBackwardLabel.atx
-a----        4/26/2019   9:43 AM           4118 a00000007.CatRelTypesByDestItemTypeID.atx
-a----        4/26/2019   9:43 AM          12310 a00000007.CatRelTypesByForwardLabel.atx
-a----        4/26/2019   9:43 AM          12310 a00000007.CatRelTypesByName.atx
-a----        4/26/2019   9:43 AM           4118 a00000007.CatRelTypesByOriginItemTypeID.atx
-a----        4/26/2019   9:43 AM           4118 a00000007.CatRelTypesByUUID.atx
-a----        4/26/2019   9:43 AM            602 a00000007.gdbindexes
-a----        4/26/2019   9:43 AM           3479 a00000007.gdbtable
-a----        4/26/2019   9:43 AM           5152 a00000007.gdbtablx
-a----       10/25/2019   8:54 AM             66 a00000009.gdbindexes
-a----       10/25/2019   8:54 AM            168 a00000009.gdbtable
-a----       10/25/2019   8:54 AM           5152 a00000009.gdbtablx
-a----        4/26/2019   9:43 AM              4 gdb
-a----       10/25/2019   8:54 AM            400 timestamps


RiverArchitect\program\ProjectMaker\.templates\Project_vii_TEMPLATE\Quantities
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----       11/19/2019   9:12 AM             10 __init__.py


RiverArchitect\program\SHArC
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----        7/26/2019  11:39 AM                .templates
d-----        7/26/2019  11:39 AM                CHSI
d-----        7/26/2019  11:39 AM                HSI
d-----        7/26/2019  11:39 AM                SHArea
-a----       11/21/2019   6:14 PM          38809 cHSI.py
-a----       10/22/2019   2:31 PM          32273 sharc_gui.py
-a----        7/26/2019  11:12 AM          17490 sub_gui_covhsi.py
-a----       10/30/2019   5:10 PM           9689 sub_gui_hhsi.py
-a----        7/26/2019  11:39 AM            122 __init__.py


RiverArchitect\program\SHArC\.templates
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM         242416 CONDITION_QvsA_template_si.xlsx
-a----        7/26/2019  11:39 AM         242653 CONDITION_QvsA_template_us.xlsx
-a----        7/26/2019  11:39 AM          17940 CONDITION_sharea_template_si.xlsx
-a----        7/26/2019  11:39 AM          17923 CONDITION_sharea_template_us.xlsx
-a----        7/26/2019  11:39 AM           6172 empty.xlsx


RiverArchitect\program\SHArC\CHSI
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM             62 __init__.py


RiverArchitect\program\SHArC\HSI
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM             62 __init__.py


RiverArchitect\program\SHArC\SHArea
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM             62 __init__.py


RiverArchitect\program\Tools
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----        7/26/2019  11:39 AM                .templates
-a----       11/25/2019   1:05 PM           6547 cHydraulic.py
-a----        7/26/2019  11:39 AM           8790 cInputOutput.py
-a----       11/25/2019   1:05 PM           6126 cPoolRiffle.py
-a----       11/25/2019   1:05 PM           8129 fTools.py
-a----       11/25/2019   1:05 PM           3112 make_annual_flow_duration.py
-a----       11/25/2019   1:05 PM           1687 make_annual_peak.py
-a----        7/26/2019  11:39 AM           1554 morphology_designer.py
-a----       10/30/2019  12:49 PM           1218 rename_files.py
-a----        7/26/2019  11:39 AM            137 run_make_annual_flow_duration.bat
-a----        7/26/2019  11:39 AM            132 run_make_d2w.bat
-a----        7/26/2019  11:39 AM            124 run_make_det.bat
-a----        7/26/2019  11:39 AM            124 run_make_det_gen.bat
-a----        7/26/2019  11:39 AM            126 run_make_mu.bat
-a----        7/26/2019  11:39 AM            147 run_morphology_designer.bat


RiverArchitect\program\Tools\.templates
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM          11618 annual_peak_template.xlsx
-a----        7/26/2019  11:39 AM          20867 flow_duration_template.xlsx
-a----        7/26/2019  11:39 AM          11763 input.xlsx
-a----        7/26/2019  11:39 AM          13784 output.xlsx


RiverArchitect\program\VolumeAssessment
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----        7/26/2019  11:39 AM                .templates
d-----        7/26/2019  11:39 AM                Output
-a----       11/21/2019   6:07 PM          10217 cVolumeAssessment.py
-a----        7/26/2019  11:35 AM           7013 volume_gui.py
-a----        7/26/2019  11:39 AM             79 __init__.py


RiverArchitect\program\VolumeAssessment\.templates
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM          10125 volumes_template.xlsx


RiverArchitect\program\VolumeAssessment\Output
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        7/26/2019  11:39 AM             62 __init__.py

```






