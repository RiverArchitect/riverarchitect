Get Started and Signposts
=========================

***

- [Get Started and Create Conditions](#getstarted)
  +  [Create New Condition](#new-condition)
  +  [Populate New Condition](#pop-condition)
  +  [Analyze Flow](#ana-flows)
  +  [Make a Subset Condition](#sub-condition)
  +  [Make Input Files (.inp)](#inpfile)
  +  [Align Input Rasters](#align-inputs)
- [Geofile name conventions](Signposts#terms)
- [Input file preparation](Signposts#inputs)

***

# Get Started<a name="getstarted"></a><a name="conditions"></a>

*River Architect*'s first tab invites the user for the creation of *Conditions*.

![ragui](https://github.com/RiverArchitect/Media/raw/master/images/gui_start.PNG)

A *Condition* is a folder filled with Rasters that represent a temporal snapshot (situation) of a river. *Conditions* are stored in `RiverArchitect/01_Conditions/`. For example, if the goal is to assess feature lifespans based on the situation in the year 2008, the condition folder name may be `2008` and the corresponding folder is `RiverArchitect/01_Conditions/2008/`.
The *Condition* name may NOT include any SPACE character and good practice is that the first 4 characters represent a 4-digit year.
All other modules build on the data provided in `RiverArchitect/01_Conditions/` and the modules create output folders beginning with the defined *Condition* name and ending with specifiers such as [feature layer](River-design-features), [reach](ModifyTerrain#mtsetreaches), or fish ([see bottom of HHSI output descriptions](SHArC#hemakehsi)) information.

The *Get Started*-tab buttons invite the user to create conditions from scratch, populate (new) conditions, and make spatial subsets. Every button opens up a new window with the following options:

- Create New *Condition*: Create a new *Condition* from scratch
- Populate *Condition*: Add Morphological Unit, Depth to water table, and Detrended DEM Rasters to an existing (or newly created) *Condition*
- Create a spatial subset of a *Condition*: Define a boundary Raster that delineates a spatial frame for creating a subset of an existing *Condition* (useful for comparing project alternatives at different sites).

## Create New Condition<a name="new-condition"></a>
The creation of a new *Condition* requires that a 2D hydrodynamic model was previously run to obtain spatially explicit flow depth and velocity data. Moreover, grain size data (spatially explicit )and a digital terrain elevation model need to be available.
A new popup window inquires following inputs for generating a new *Condition* from scratch:

- A name for the new *Condition*
- A folder containing flow velocity Rasters (preferably use *GeoTFF* `.tif` Rasters) corresponding to multiple discharges ([read more on discharge definitions](#inputs)). A *Raster string* may be defined to select only Rasters that contain certain letters in their name from the defined folder (e.g., enter `u`).
- A folder containing flow depth Rasters (preferably use *GeoTFF* `.tif` Rasters) corresponding to multiple discharges ([read more on discharge definitions](#inputs)).  A *Raster string* may be defined to select only Rasters that contain certain letters in their name from the defined folder (e.g., enter `h`).
- A *DEM* (Digital Elevation Model) or *DTM* (Digital Terrain elevation Model) of the terrain covered by the flow depth and velocity Rasters.
- A *Grain Size* Raster (U.S. customary: in feet or SI metric: in meters).
- An optional folder containing velocity angle Rasters (preferably use *GeoTFF* `.tif` Rasters) corresponding to multiple discharges ([read more on discharge definitions](#inputs)). Note that velocity angles are defined in degrees from North, i.e. North=0, East=90, West=-90, South=180/-180. A *Raster string* may be defined to select only Rasters that contain certain letters in their name from the defined folder (e.g., enter `va`).
- An optional *Scour* Raster (U.S. customary: in feet or SI metric: in meters) containing annual scour rates, which may result from terrain change detection analyses ([Pasternack and Wyrick 2017](http://dx.doi.org/10.1002/esp.4064)) or hydro-morphodynamic modeling (tricky).
- An optional *Fill* Raster (U.S. customary: in feet or SI metric: in meters) containing annual fill rates, which may result from terrain change detection analyses ([Pasternack and Wyrick 2017](http://dx.doi.org/10.1002/esp.4064)) or hydro-morphodynamic modeling (tricky).
- A background Raster, which can optionally be used to [Align Input Rasters](#align-inputs).

*Note that the optional inputs are highly recommended to make the subsequent analyses robust.*

Once the input is defined, clicking on the `CREATE CONDITION` button will create the new *Condition* as `RiverArchitect/01_Conditions/`*NEW\_CONDITION* with the following contents:<a name="nameconvention"></a>

- `back.tif` is a background Raster that may be used for limiting lifespan analyses (<a href="LifespanDesign">LifespanDesign</a>) extents and all subsequent analyses. Moreover, the background Raster enables consistent mapping.

- `dem.tif` is a DEM Raster indirectly required by the <a href="LifespanDesign">LifespanDesign</a>, <a href="ModifyTerrain">Modify Terrain</a>, <a href="StrandingRisk">Stranding Risk</a>, <a href="ProjectMaker">ProjectMaker</a> and <a href="MaxLifespan">Max Lifespan</a> modules.

- `dmean.tif` is a grain size Raster indirectly required by the <a href="LifespanDesign">LifespanDesign</a>, <a href="SHArC">SHArC</a>, <a href="StrandingRisk">Stranding Risk</a>, <a href="ProjectMaker">ProjectMaker</a> and <a href="MaxLifespan">Max Lifespan</a> modules.

- `fill.tif` is topographic change Raster indicating annual sediment deposition rates, which are required by the <a href="LifespanDesign">LifespanDesign</a>, and indirectly, the <a href="MaxLifespan">Max Lifespan</a> and <a href="ProjectMaker">ProjectMaker</a> modules.

- `hQQQQQQ.tif` are flow depth rasters required by the <a href="LifespanDesign">LifespanDesign</a>, <a href="SHArC">SHArC</a>, <a href="StrandingRisk">Stranding Risk</a>, and (indirectly) the <a href="ProjectMaker">ProjectMaker</a> and <a href="MaxLifespan">Max Lifespan</a> modules. [Read more about file name conventions.](#terms)

- `uQQQQQQ.tif` are flow velocity rasters required by the <a href="LifespanDesign">LifespanDesign</a>, <a href="SHArC">SHArC</a>, <a href="StrandingRisk">Stranding Risk</a>, and (indirectly) the <a href="ProjectMaker">ProjectMaker</a> and <a href="MaxLifespan">Max Lifespan</a> modules. [Read more about file name conventions.](#terms)

- `scour.tif` is topographic change Raster indicating annual terrain erosion rates, which are required by the <a href="LifespanDesign">LifespanDesign</a>, and indirectly, the <a href="MaxLifespan">Max Lifespan</a> and <a href="ProjectMaker">ProjectMaker</a> modules.

- `vaQQQQQQ.tif` is flow velocity direction rasters required by the [Stranding Risk](StrandingRisk) module. [Read more about file name conventions.](#terms)

The flow depth and velocity Rasters may require manual renaming to adapt to these Raster name conventions. A [*River Architect Tools* script](Tools#renamefiles) facilitates renaming multiple file names. Subsequently, populating the created *Condition* is strongly recommended

## Populate Condition<a name="pop-condition"></a>
***
*Condition* - wise Morphological Unit, Depth to water table, and Detrended DEM Rasters add consistency to the analyses of all modules. The `Populate Condition` popup window invites the user to define a *Condition* to be populated, and subsequently to create the following Rasters:

- Morphological Unit, 
- Depth to water table, and 
- Detrended DEM.


### Make Morphological Unit Rasters<a name="mu"></a>
***
Instream morphological unit Rasters according to [Wyrick and Pasternack (2014)][wyrick14] enable the correct allocation of [river design features](River-design-features) as defined in the [thresholds workbook](LifespanDesign#modthresh). For this purpose, the following inputs are needed:

 -  A flow velocity raster (use [baseflow](https://en.wikipedia.org/wiki/Baseflow) in line with [scientific literature][wyrick14]);
 -  A flow depth raster (use [baseflow](https://en.wikipedia.org/wiki/Baseflow) in line with [scientific literature][wyrick14]).

The delineation of morphological units as a function of flow depth and velocity can be modified in the `morphological_units.xlsx` workbook (`RiverArchitect/.site_packages/templates/` folder). A click on the `Populate Condition` GUI's `View/change MU definitions` opens this workbook.

![ramus](https://github.com/RiverArchitect/Media/raw/master/images/mu_xlsx.PNG)

For making changes in the workbook, choose either one of the pre-defined river classes (`Mountain river` with large roughness elements, `gravel-cobble` bed, or `cobble-boulder` bed) or select `User Defined` from the drop-down menu in cell `E2`. If `User Defined` is selected, morphological units can be defined as a function of upper and lower limits of flow velocity and depth in cells `N6:Q22` (instream) and/or `N24:Q43` (floodplain). Morphological unit names can be modified in cells `M6:M22` (instream) and/or `M24:M43` (floodplain). Please note:

- Do not modify anything outside the green frames, in particular, do not make changes within the red frame (cells `B3:J44` and the `.templates` sheet).
- Use **metric units only**; for the conversion of metric units for their application to Rasters in U.S. customary units, select `Units: U.S. customary` (default) from the `Populate Condition` window. The currently selected unit system is shown at the bottom of the `Populate Condition` window.
- Instream and floodplain units are currently equally applied (future versions of *River Architect* aim at a more precise approach to delineate floodplain morphological units).
- The maximum length of morphological units names (`M6:M22` and/or `M24:M43`) is 50 characters per cell.
- *River Architect* calculates a Raster for each morphological unit defined using the following `arcpy.sa` expression: `Con(h > 0, Con(((u >= u_lower) & (u < u_upper) & (h >= h_lower) & (h < h_upper)), mu_id))`. The final Raster is created by the superimposition of all applicable morphological raster and using the maximum `mu_id` value (pre-defined in column `E`). with `arcpy.sa` cell statistics: `CellStatistics(mu_id_raster_list, "MAXIMUM", "DATA")`.
- The results are
	+ the morphological unit's `ID` Raster saved as `RiverArchitect/01_Conditions/CONDITION/mu.tif`; and
	+ the morphological unit's name Raster (uses an intermediated Raster to point conversion) saved as `RiverArchitect/01_Conditions/CONDITION/mu_str.tif`.


### Make Depth to Water Table Rasters<a name="d2w"></a>
***
The depth to the water table is primarily required for identifying relevant regions for target indigenous [plant species](https://github.com/RiverArchitect/RA_wiki/River-design-features#plants). For this purpose, the following input Rasters are required.

 -  A terrain DEM (or DTM) is automatically assigned from the selected *Condition* folder.
 -  A low-level flow depth Raster (in arid regions) based on the assumption that the groundwater table in the vicinity of the river corresponds to at least this water level, which marks the moment of highest water stress for plants.

RiverArchitect estimates the depth to water table by interpolating the given low flow water surface across the DEM extent. There are three options for the interpolation method used to calculate this surface:

- `IDW`: Inverse distance weighted interpolation. Each null cell in the low flow depth raster is assigned a weighted average of its 12 nearest neighbors. Each weight is inversely proportional to the second power of the distance between the interpolated cell and its neighbor. Thus, the closest neighbors to an interpolated cell receive the largest weights.
- `Kriging`: Ordinary Kriging interpolation. This method also uses a weighted average of the 12 nearest neighbors, but weights are calculated using a semi-variogram, which describes the variance of the input data set as a function of the distance between points. A spherical functional form is also assumed for the fitted semi-variogram. Kriging is the most accurate interpolation method if certain assumptions are met regarding normality and stationarity of error terms. However, it is also the most computationally expensive method.
- `Nearest Neighbor`: The simplest method, which sets the water surface elevation of each null cell to that of the nearest neighboring cell.

All interpolated rasters are saved with a corresponding `.info.txt` file which records the interpolation method and input rasters used in its creation. 

### Make Detrended DEM Rasters<a name="det"></a>
***
Automation of [grading](River-design-features#grading) or the relevance of [widening and berm setbacks](River-design-features#berms) build on the relative elevation of the terrain over the river water surface elevation. For this purpose, the following input Rasters are required.

 -  A terrain DEM (or DTM) is automatically assigned from the selected *Condition* folder.
 -  A flow depth Raster (in arid regions) marks the level for relative elevations. Designers may have different reasons for choosing the relevant flow depth Raster (low flows for habitat enhancement or high flows for flood protection), and therefore, no recommendation is made here.
 
Please note that step-like artifacts may occur in the detrended DEM. The steps result from variations in the Thalweg elevation of the DEM that attenuate with the selection of flow depth Rasters of higher discharges. Users can decide to select a low-flow depth Raster to be on the safe side for delineating vegetation plantings or a high-flow depth Raster to reduce step-like artifacts in the detrended DEM.

## Create a spatial subset of a Condition<a name="sub-condition"></a>
***
The creation of a spatial subset of a *Condition* requires a Boundary shapefile or Raster (if this is a GRID Raster, select the corresponding .aux.xml file). The boundary file needs to contain On-values (Integer 1) and Off-values (Integer 0) values only as specified in the [Project Area Polygon preparation](ProjectMaker#pminp2).

If a shapefile is selected:

 - River Architect automatically uses the `gridcode` Field in the Shapefile\'s Attribute Table.
 - If the `gridcode` Field cannot be found, the third Field or the `FID` Field is used. (in that order). Note that the enforced usage of the `FID` Field may cause errors later on.
 - Ensure that the `gridcode` / third Field contains On-Off Integers only, where 0=Outside and 1=Inside boundary. 
 - **Restart River Architect to create multiple subsets.** This issue is related to `arcpy`, which will not release the new datasets unless *River Architect* is closed ([otherwise there will be an error message referring to registering datasets](https://pro.arcgis.com/en/pro-app/help/data/geodatabases/overview/a-quick-tour-of-registering-and-unregistering-data-as-versioned.htm)) We are developing workarounds.

If a Raster is selected:
 - Ensure that the Raster contains On-Off Integers only, where 0=Outside and 1=Inside boundary.

The boundary files are of particular interest within the <a href="ProjectMaker">ProjectMaker</a> and <a href="SHArC">SHArC</a> modules.

## Analyze Flows<a name="ana-flows"></a>
The sustainability (lifespan) and ecohydraulic analyses require hydraulic data related to discharges (flows) and the return period. The *Analyze Discharge* pop-up window guides through the creation of flow-metadata files that link hydraulic Raster names with flows and return periods for a *Condition*. *Analyze Discharge* looks for flow depth and velocity Rasters in a selected *Condition*, extracts the flow quantity, and creates a template workbook in the *Condition* folder. For this purpose, hydraulic (flow depth and velocity) Rasters must be named according to the [Geofile name convetions](#terms) (i.e., flow depth Rasters = "hQQQQQQ.tif" and flow velocity Rasters = "uQQQQQQ.tif").

![raq](https://github.com/RiverArchitect/Media/raw/master/images/gui_start_flows.PNG)

Start with selecting a *Condition* from the upper listbox and click the `Analyze` button. This creates a workbook called `RiverArchitect/01_Conditions/flow_definitions.xlsx`, which automatically opens up and asks for the definitions of flow return periods in years. Frequent flows with a return period of one year or less should be assigned `1.0` (column `C`).

![raq](https://github.com/RiverArchitect/Media/raw/master/images/def_return_periods.PNG)

Flow duration curves are required for ecohydraulic analyses and can be generated for specific [Physical Habitats preferred by target fish species-lifestages](SHArC#hefish).
Select at least one *Fish Species - Lifestage* from the lower listbox and use the `Add` button (to add multiple *Fish Species - Lifestage*s, select-add one-by-one). A click on the `Modify Source` button opens the `Fish.xlsx` workbook that contains *Fish Species - Lifestage* definitions. At this point, on particular fish names and seasons start/end dates may be modified. Modifications of *Lifestages* should be avoided. For more details, refer to the [SHArC Wiki pages](SHArC#hefish).
Before a *Fish Species - Lifestage* flow duration curve can be generated, ensure to `Select input Flow Series` (workbook) with the following characteristics:

- The file ending must be `.xlsx`
- Column `A` must contain dates, where 
	+ row `1` is the header (i.e., `A1 = "Date"`), 
	+ row `2` indicates the date units (i.e., `A2 = "(DD-MM-YY)"`), and 
	+ date series must be entered from row `3` onward (i.e., dates in the format `A3 = 5-Sep-03` or `A4 = 9/5/2003`).
- Column `B` must contain mean daily flows, where 
	+ row `1` is the header (i.e., `B1 = "Mean daily"`), 
	+ row `2` indicates the date units (i.e., `B2 = "(CFS)"` or `B2 = "(CMS)"), and 
	+ mean daily flows must be entered from row `3` onward (i.e., dates in the format `B3 = 59.3` or `B4 = 79`).
- For later application, store the flow series workbook in `RiverArchitect/00_Flows/InputFlowSeries/` (default folder where *River Architect* looks for flow series).

An example workbook is provided with `RiverArchitect/00_Flows/InputFlowSeries/flow_series_example_data.xlsx`. 

Click on `Make flow duration curve(s)` (plural applies if multiple *Fish Species - Lifestage*s are selected) to generate an Physical Habitat workbook for target *Fish Species - Lifestage*s. The workbook containing the last *Fish Species - Lifestage* flow duration curve in the selected list will open up automatically when the flow duration curve generation finishes without error messages. All generated workbooks will be saved as `RiverArchitect/00_Flows/CONDITION/flow_duration_FILI.xlsx`, where `FILI` denotes the first two letters of the selected fish species and lifestage. The workbooks contain two tabs that link all observed mean daily flows from the target *Fish Species - Lifestage*'s season (tab 1) with the available 2D model data (tab 2). The result is a flow duration curve that provides a measure of how well the 2D model data may represent the relevant discharges for a *Fish Species - Lifestage*.

![raq](https://github.com/RiverArchitect/Media/raw/master/images/RA_flow_dur.PNG)



## Generate Input File(s) (.inp) <a name="inpfile"></a>
***
Lifespan mapping uses input files (.inp) to identify relevant Rasters and (flood) return periods. Given that `Analyze Flow` was previously executed for a *Condition*, an input file can be generated with the `Make Input File` tool.

The resulting `input_definitions.inp` is stored in the directory `RiverArchitect/01_Conditions/CONDITION/`. `input_definitions.inp` contains information about lifespan duration and Raster names, which link to Rasters containing spatial information as described in the [Parameters](LifespanDesign-parameters) Wiki page. The order of definitions and lines must not be changed to ensure the proper functioning of the module. Enter or change the information in the corresponding lines, only between the "=" and the "*\#*" signs (the input routines uses these signs as start and end identifiers for relevant information). Verify that every `input_definitions.inp` created contains the following definitions (line by line):

|Line No.| [Par.](LifespanDesign-parameters) | Description|
|:-------|:-------------|:-----------|
| Lines 1-3 | None |Do not change|
| Line  4 | Return periods | Comma-separated list of flood discharge return periods corresponding to the hydraulic rasters; i.e., the first entry after ``='' corresponds to the return period of the first velocity and flow depth raster (Lines 11 and 12, respectively)|
| Lines 5-7 | None |Do not change|
| Line  8 | *CHSI* | One raster name of spatial composite Habitat Suitability Indexes |
| Line  9 | *DoD*  | Comma-separated list of two (first = scour, second = fill) DEM of Differences rasters; if one raster is missing, replace it by double quotation marks, for example scour is missing: `... = "", fill # ...`|
| Line 10 | `det`  | One raster name defining the detrended DEM raster|
| Line 11 | `u`	| Comma-separated list defining flow velocity rasters corresponding to discharge return periods (Line4); replace missing rasters by double quotation marks, for example, when `u` rasters of a return period list of five entries are not available for entries 2 and 4, `... = u001000, "", u003000, "", u005000 # ...`. However, ensure that at least two `u` rasters are defined. The `00Q000` identifier relates to the underlying discharge in thousand cfs or m<sup>3</sup>/s (see [Geofile name conventions](#terms)).|
| Line 12 | `h`	| Comma-separated list defining flow depth rasters corresponding to discharge return periods (Line 4); replace missing rasters by double quotation marks, for example, when `h` rasters of a return period list of six entries are not available for entries 2, 3 and 5, type `... = h001000, "", "", h004000, "", h006000 # ...`. Ensure that at least two `h` rasters are defined. The `00Q000` identifier relates to the underlying discharge in thousand cfs or m<sup>3</sup>/s (see [Geofile name conventions](#terms)).|
| Line 13 | Grain size| One raster name defining the raster containing mean grain diameters (typically `dmean`; pay attention to raster units: use feet for U.S. customary and m for S.I.)|
| Line 14 | `mu`  | One raster name delineating morphological units according to the definitions in Sec. \ref{sec:par}|
| Line 15 | `d2w` | One raster name defining the depth to water table|
| Line 16 | `dem` | One raster name defining the digital elevation model|
| Line 17 | `sidech` | One raster name delineating appropriate sites for side channels|
| Line 18 | `wild` | One raster name for the spatial confinement of the feature analysis of 0/nodata (= off) and 1 (= on) values for any purpose (wildcard raster)|

The <a href="LifespanDesign">LifespanDesign</a> module produces results based on the available information only, where any raster name can be substituted with double quotation marks. However, this lack of information reduces the accuracy of final lifespan and design maps. No results are produced for a feature where the information is insufficient for the analysis. The required information for every feature corresponds to the definitions in the input file.

## Map extent input definition files <a name="inmaps"></a>
The file `RiverArchitect/LifespanDesign/.templates/mapping.inp` defines map center points, extents (*dx* and *dy* in ft or m) and scales (scale has no effect currently).<br/>
The extent of the map determines the map scale, where the corresponding *dx* and *dy* values define the map width and height in ft or m, respectively. The layout templates (in the project file `RiverArchitect/02_Maps/templates/river_template.aprx`) define the paper size, which is by default "ANSI E landscape" (width = 44 inches, height = 34 inches).<br/>
The map focus is defined page-wise in `mapping.inp` from Line 8 onward. Existing pages can be removed by simply deleting the line. Additional pages can be added by inserting or appending a new line below Line 8, which needs to begin with the keyword "`Page`" and *x* and *y* need to be stated in brackets, separated by a comma without any white space.<br/>
Good practice for changing the map layouts starts with importing the `determine_extents.mxd` layout from `RiverArchitect/ModifyTerrain/templates/` into a map project (`.aprx`). Zoom to new focus point using, for example, using *ArcGIS Pro*'s `Go To XY` function or freehand to any convenient extent. Use *ArcGIS* `Info` cursor and click in the center of the reticule to obtain the current center point. Write new center point coordinates for the desired page number in `mapping.inp`.<br/>
For retrieving the extent, in *ArcGIS* Desktop, go to the `View` menu, click on `Data Frame Properties...` and go to the `Data Frame` tab. In the `Extent` box, click on the scroll-down menu and choose `Fixed Extent`. Subtracting the `Right` value from the `Left` value defines *dx* (Line 3 in `mapping.inp`) and subtracting the `Top` value from the `Bottom` value defines *dy* (Line 4 in `mapping.inp`).<br/>
The function uses these definitions for zooming to each point defined below Line 8 in `mapping.inp`, cropping the map to the defined extents and exporting each page to a `pdf` map bundle containing as many pages as there are defined in `mapping.inp`.<br/>
The program uses the reference coordinate system and projection defined in the `.aprx` file's map layout templates or in `mapping.inp`.


## Align Input Rasters<a name="align-inputs"></a>
***
In order to ensure robustness and accuracy of analyses, it is important that input rasters share a common alignment, cell size, and coordinate system. Input rasters can be aligned in the following ways:
- During creation of a new [Condition](#new-condition), align input rasters by using a background raster and selecting the "Use to align input rasters" checkbox.
- For an existing condition, the tool from the GetStarted menu allows selection of an alignment raster.

The alignment routine reprojects and/or resamples the input raster data to match the following attributes from the input alignment raster:
- ArcGIS SpatialRefernce (i.e. reference coordinate system)
- lower left corner of raster, modulo cell size
- cell size

Caution should be taken when using the built-in alignment routine, as input data may have already been resampled (e.g. from a mesh, TIN, or point features) and repeated resampling of data may create artifacts in the resultant data. Additionally, other routines in River Architect assume that water surface elevation can be calculated by summation of the DEM and depth rasters, which may not hold true if these data have been subject to different resampling schemes.

# Geofile (Raster) conventions<a name="terms"></a>
***
The input Rasters need to be in **GeoTIFF** (*.tif*) format, notably, a `raster_name.tif` file. _Note that River Architect is designed to also handle Esri's GRID format, but the primary raster file type should be GeoTIFF_. Depth Raster names must start with `h` and velocity Raster names must start with `u`, followed by a six-digit discharge `QQQQQQ`, which is independent of the unit system. For example, a flow depth Raster associated with a discharge of 55 m³/s needs to be called `h000055.tif` and a velocity Raster associated with a discharge of 11000 m³/s needs to be called `u011000.tif`. Likewise, a flow depth Raster associated with a discharge of 55 cfs needs to be called `h000055.tif`. The Raster names ignore discharge value digits after the decimal point. Moreover, every flow depth Raster requires a matching velocity Raster and vice versa (e.g., `h000055.tif` requires a Raster called `u000055.tif`).<br/>
**Note: `back.tif` may be used to limit calculation extents.**


# Manual input data preparation<a name="inputs"></a>
***
Relevant Raster names for calculation are defined in an input file ([`.inp`](#inpfile)) of the [*LifespanDesign*][3] module (input section see for details and definitions). Please note that *.inp* files for lifespan mapping are different from the input (*.txt*) files required for [River Builder](RiverBuilder).
Sample data representing a patch of a Californian gravel-cobble bed river in 2100 can be downloaded [here](https://github.com/RiverArchitect/SampleData/archive/master.zip). The input file of the sample case is located in `01_Conditions/2100_sample/input_definitions.inp` file. The sample case includes a set of Rasters for flow scenarios corresponding to return periods of < 1.0 (ignored in the input file), 1.0,  ... , 2.0, 5.0, 10.0, 15.0, 20.0, 30.0, 40.0, and 50.0 years, as well as a couple of annual discharges for habitat assessments. The according flows are defined in `01_Conditions/2100_sample/flow_definitions.xlsx`, with pre-compiled flow duration curves for whetted area (`alhy`), Chinook salmon juveniles (`chju`), fry (`chfr`), and spawning (`chju`) lifestages that are stored in `00_Flows/2100_sample/flow_duration_FILI.xlsx` (see above [flow definitions](#ana-flows)).

The below listed Rasters are available in GeoTIFF format in `01_Conditions/2100_sample/` for the sample case `condition` = `2100_sample`. *Italic font* indicates *optional* Rasters, which are, however, recommended to use because they significantly increase the pertinence of lifespan maps; Rasters written in **`CAPITALIZED ROUGE FONT`** font are **`required`** for *River Architect* to work. The Raster names correspond to the above-described naming conventions.

| **PARAMETER** | (UNITS) |
|---------------|:--------|
| **`FLOW VELOCITY`** | **`(in fps or m/s)`** |
| u000300    | lowest     |
| u000350    | ...     |
| u......    | ...                        |
| u088053    | highest                    |
| **`FLOW DEPTH`**       | **`(in ft or m)`** |
| h000300      | lowest   |
| h000350      | ...   |
| h......      | ...                      |
| h088053      | highest                  |
| `Topographic change` | `(in ft or m)` |
| dodfill    |average annual deposition height  |
| dodscour   |average annual scour depths       |
| **`Depth to water table`** | **`(in ft or m)`** |
| d2w          | referring to a baseflow of 15 m³/s (530 cfs) |
| `Background`                    | `(black and white)` |
| back | here: determines <a href="LifespanDesign">LifespanDesign</a>'s calculation extents |
| **`MORPHOLOGICAL UNITS`**  | **`Float / Int`** |
| mu         | generated with *Populate Condition* (Get Started) |
| **`D mean`**     | **`(in ft or m)`** |
| dmean\_ft or dmean | mean valley grain size        |
| `DEM`                | `(in ft a.s.l.)` |
| dem        | *Digital Elevation Model*      |
| **`DEM DETRENDED`**         | **`(in ft or m)`** |
| dem\_detrend | generated with *Populate Condition*|
| `Side channel`                     | `(0/nodata=off and 1=on)` |
| sidech     | *Side channel delineation*     |
| `Wildcard`   | `(0/nodata=off and 1=on)` |
| wild         | On/ off values for any purpose to confine analyses |

More Rasters indicating morphological units (e.g., [Wyrick and Pasternack 2014][wyrick14]) or topographic change (e.g., [Carley et al. 2012][carley12]) as well as a detrended digital elevation model (DEM), surface grain size estimate and a depth to water table Raster are (optionally) required.

Some parameters, such as the dimensionless bed shear stress or the mobile grain size, can be directly computed from the flow velocity, depth, and present grain size. Additional input Rasters could be used for every parameter to shorten calculation duration, but this approach required large storage capacity on the hard disk and it is less flexible regarding computation methods. Therefore, the *River Architect* uses its own routines for calculating parameters such as the dimensionless bed shear stress or mobile grain sizes.

`NoData` handling: *River Architect* does not consider pixels with `NoData` values and has routines to handle `NoData` during the calculation. 



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
[carley12]: https://www.sciencedirect.com/science/article/pii/S0169555X12003819
[wyrick14]: https://www.sciencedirect.com/science/article/pii/S0169555X14000099
