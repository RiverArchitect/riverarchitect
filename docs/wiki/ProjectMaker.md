Project Maker 
=============

***

- [Introduction to the Project Maker module](#pmintro)
- [Quick GUIde to a project assessment](#pmquick)
  * [Prerequisites](#pmprereq)
  * [Main window set-up and run](#pmgui)
  * [Input: Variables and automatically generated files](#pminp1)
  * [Input: Project Area Polygon shapefile](#pminp2)
  * [Input: Delineate Plantings shapefile](#pminp3)
- [Cost quantity assessment and the cost master workbook](#pmcq)
  * [Terraforming](#pmterraf)
  * [Vegetation plantings and supporting features](#pmplants)
  * [Terrain stabilization](#pmter)
  * [Nature-based engineering features (other)](#pmbio2)
  * [Other civil engineering works](#pmciv)
  * [Other costs and remarks](#pmcadd)
- [Mapping of construction elements](#pmmaps)
- [Ecological benefit assessment (Calculate SHArea)](#pmSHArea)
  * [Additional input and requirements](#pmadd)
  * [Run SHArea calculation](#pmrunSHArea)
  * [Output](#pmout)

***

# Introduction to the Project Maker module<a name="pmintro"></a>

The *ProjectMaker* module guides through the half-automated assessment of cost-relevant quantities and ecological project benefits. A "restoration plan" or project proposal for a restoration plan herein designates an isolated restoration measure that can be delineated with an own `ProjectArea.shp` shapefile. *version*s of a restoration plan may refer to [terraforming](River-design-features#featoverview) options or other planning [*Condition*s](Signposts#new-condition). A project proposal is prepared for (preliminarily) *version*s of a restoration plan including relevant [nature-based engineering features](River-design-features#bioeng) (i.e., [vegetation plantings](River-design-features#plants), stabilizing features such as the placement of [angular boulders](River-design-features#rocks), and [*anchored* streamwood](River-design-features#elj)) and it evaluates cost-relevant quantities. A project cost table uses the cost-relevant quantities for a preliminary cost estimate. The habitat utility in terms of net gain in **S**easonal **H**abitat **Area** ([**SHArea**](SHArC#herunSHArea)) for target fish species determines the project return in *"US\$ per \[acre or m<sup>2</sup>\] of newly created SHArea"*. This Wiki page is organized as follows:

 - [ProjectMaker GUI usage](#pmquick)
 - [Generate a project plan and run a cost-quantity assessment](#pmcq)
 - [Map final designs](#pmmaps)
 - [Calculate gain in SHArea](#pmSHArea)


# Quick GUIde to a project assessment<a name="pmquick"></a>

***

## Prerequisites<a name="pmprereq"></a>


***
> Ensure that the following steps were executed in order to generate the required geodata for creating a project proposal:
> 
> -   If terraforming applies:
>     -   The *SiteName* restoration terraforming plan was verified with 2D hydrodynamic modeling
>     -   The *River Architect*'s [*VolumeAssessment*](VolumeAssessment) module was applied to calculate excavation / fill volumes.
> -   The [*LifespanDesign*][3] and [*MaxLifespan*][4] modules were executed for [plantings](River-design-features#plants) and [other nature-based engineering features](River-design-features#bioeng). Thus, the following directories should exist and contain plantings and other nature-based engineering feature rasters:
>     -   [Plantings](River-design-features#plants):
>         +  `RiverArchitect/LifespanDesign/Output/Rasters/CONDITION_lyr20/`
>         +  `RiverArchitect/MaxLifespan/Output/Rasters/CONDITION_lyr20/`
>     -   [Other nature-based engineering features](River-design-features#bioeng):
>         + `RiverArchitect/LifespanDesign/Output/Rasters/CONDITION_lyr20/`
>         + `RiverArchitect/MaxLifespan/Output/Rasters/CONDITION_lyr20/`
> -   The [*SHArC*][6] module was applied to the pre-project (initial) condition and the "with implementation" ("as-built") condition.
> 
***

## Main window set-up and run<a name="pmgui"></a>

The below figures shows the *ProjectMaker* GUI at startup.

![guipm](https://github.com/RiverArchitect/Media/raw/master/images/gui_start_pm.PNG)

The creation of a cost-benefit assessment requires the step-wise definition of variables and calculation beginning at the top of the GUI and moving forward to the bottom. The following sections provide details regarding input requirements and calculations of every step.

## Input: Variables and automatically generated files<a name="pminp1"></a>

The assessment uses the following parameters and formats, which can be entered in the GUI:

-   *Project version* (or *vii*) is a "*v*" + 2-digits (*ii*) version number (string), for example, `v10` (other 3-digit strings are also allowed)

-   *Project name* is a string (e.g., of a particular site) written in *CamelCase*, for example, `RavineConfluence`

Click on the `VALIDATE VARIABLES` button to verify that the variables entered are correct. A successful validation creates a copy of the template project structure (`RiverArchitect/ProjectMaker/.templates/Project_vii_TEMPLATE/`), which is typically saved as `RiverArchitect/ProjectMaker/ProjectName_vii/`. The *variable validation*  opens an info-box, a project assessment workbook (`.xlsx`), and a mapping project (`.aprx` in *ArcGIS Pro*) that invites to create project-specific files. The required actions include:

-   WORKBOOK (`ProjectName/ProjectName_assessment_version.xlsx`)<br/>
    The workbook contains a spreadsheet named *costs*, where unit costs and quantities are evaluated. The *from\_geodata* sheet will contain quantities such as area (in square meters or acres) of vegetation planting types. The numbers in the *from\_geodata* tab are generated by a subset of codes that use geodata, which require manual actions as described in the next steps. After running the cost-quantity assessment, verify that the cells containing automatically calculated costs in the *costs* sheet link to the correct cells in the *from\_geodata* sheet.

-   MAPPING (`ProjectName/ProjectMaps.aprx`)<br/>
    The copy of *ProjectMaker*'s template project structure contains an *ArcGIS Pro* project file (`ProjectName/ProjectMaps.aprx`) with predefined layouts and layers that may require updates to site-specific geofiles (shapefiles and rasters). Project-specific geofiles (shapefiles and rasters) need to be created as described in the following sections.

## Input: Project Area Polygon shapefile<a name="pminp2"></a>

To determine cost-relevant quantities for a site-related restoration plan, a manual delineation of the project site is necessary (e.g., by using the template layouts provided in `ProjectName/ProjectMaps.aprx`).

1.  Create a new polygon-shapefile in `ProjectName/Geodata/Shapefiles/` ([read more on arcgis.com](https://pro.arcgis.com/en/pro-app/help/editing/create-polygon-features.htm)), name it `ProjectArea`, and select the project *Coordinate System* (`Current Map`). Click on `Run`.

2.  Remove the newly created layer from layout's *Contents* tab, double-click on the existing `Project area` layer -> `Layer Properties` opens up -> go to the `Source` tab -> click on `Set Data Source ...` -> Select the newly created `/Shapefiles/ProjectArea.shp` file -> click `OK`.

3.  In the layout's `Contents` tab, right-click on the `ProjectArea` layer, then `Attribute Table`. In the `Attribute Table`, click on the top-left *Field:* `Add` button. Name the field `AreaCode`, select a `Text` in the *Data Type* column and `50` in the *Length* column. Click below the new field to and add another field (*Click here to add a new field* label) with the following properties: *Field Name* = `gridcode`, *Data Type* = `Short` data type, *Number Format* = `Numeric`, *Precision* = 0, and *Scale* = 0 field named `gridcode`. Go to *ArcGIS Pro*'s *Fields* ribbon (top of the window) and click `Save`. Close the *Fields: Project area (...)* tab (the one where the fields were previously added).

4.  Delineate project area
	1.  Optional: Import modified terrain to visualize boundaries of terraforming.
	1.  In *ArcGIS Pro*'s *Edit* ribbon (top of the window), click on `Create` (ensure that the `ProjectArea` layer is selected in the *Contents* tab) > A *Create Features* opens.
	1.  In the *Create Features* tab, click (highlight) on `ProjectArea`, then on `Polygon`.
	1.  Draw a polygon around the designated project area (finish with the `F2`-key).
	1.  Go to the `Attribute Table` tab and type *`Restoration zone`* in the `AreaCode` field and *`1`* in the `gridcode` field.
	1.  `Save` edits.

## Input: Plantings shapefiles <a name="pminp3"></a>

*Project Maker* will place plants only where it makes sense and removes existing plants where necessary. An overlay of the above-created project area polygon over recent satellite image shows, where existing plants intersect with projected actions and where these plants may need to be cleared (removed). A *PlantExisting.shp* shapefile with polygons delineating these intersects needs to be created and drawn as follows in the `ProjectName/ProjectMaps.aprx`-file:

1.  In the Catalog tab, open the folder tree `ProjectName/Geodata/Shapefiles/` (double click on the folder to make it appear in the lower box).

2.  Create a new polygon-shapefile in `ProjectName/Geodata/Shapefiles/` ([read more on arcgis.com](https://pro.arcgis.com/en/pro-app/help/editing/create-polygon-features.htm)), name it `PlantExisting`, and select the project *Coordinate System* (`Current Map`). Click on `Run`.

3.  Remove the newly created layer from layout's *Contents* tab, double-click on the existing `Existing plants (all)` layer -> `Layer Properties` opens up -> go to the `Source` tab -> click on `Set Data Source ...` -> Select the newly created `.../Shapefiles/PlantExisting.shp` file -> click `OK`.

4.   In the layout's `Contents` tab, right-click on the `PlantExisting` layer, then `Attribute Table`. In the `Attribute Table`, click on the top-left *Field:* `Add` button. Name the field `ActionType`, select a `Text` in the *Data Type* column and `50` in the *Length* column. Click below the new field to and add another field (*Click here to add a new field* label) with the following properties: *Field Name* = `gridcode`, *Data Type* = `Short` data type, *Number Format* = `Numeric`, *Precision* = 0, and *Scale* = 0 field named `gridcode`. Go to *ArcGIS Pro*'s *Fields* ribbon (top of the window) and click `Save`. Close the *Fields: Project area (...)* tab (the one where the fields were previously added).

5.  Delineate existing plantings area:
	1.  Ensure that a valid background image is linked to the `background` layer (`Properties` -> `Source` tab).
    2.  In *ArcGIS Pro*'s *Edit* ribbon (top of the window), click on `Create` (ensure that the `PlantExisting` layer is selected in the *Contents* tab) > A *Create Features* opens.
    3.  In the *Create Features* tab, click (highlight) on `PlantExisting`, then on `Polygon`.
    4.  Draw polygons around existing plantings that are visible in the background (satellite image) project area, within the zone where the modified DEM rasters indicate terrain modification (finish polygons with the `F2`-key).<br/>        
    5.  Go to the `Attribute Table` tab and type `Existing` (*text*) in the `ActionType` field and `1` (*short integer*) in the `gridcode` field.
    6.  Once all visible plantings within the project area are delineated, save the edits.

Terraforming may require clearing of existing vegetation in the project area. In this case, use the above created *PlantExisting.shp* as template to delineate plants to remove (to be cleared): <a name="pminp31"></a>

1.  In the Catalog tab, open the folder tree `ProjectName/Geodata/Shapefiles/` (double click on the folder to make it appear in the lower box).

2.  Make a copy of a new polygon-shapefile in `ProjectName/Geodata/Shapefiles/PlantExisting.shp` and name it `PlantClearing.shp` in the same folder.

3.  In the map *Contents* tab, double-click on the existing `Clearing of Shrubs` layer -> `Layer Properties` opens up -> go to the `Source` tab -> click on `Set Data Source ...` -> Select the newly created `.../Shapefiles/PlantClearing.shp` file -> click `OK`.

4.  Delineate existing plantings to be removed (clearing):
	1.  In the layout's `Contents` tab, right-click on the `PlantClearing` layer, then `Attribute Table`.
    2.  Highlight all polygons of existing plants that do not need to be removed. Press `Delete` to remove these plant polygons from the clearing list. <br/>
        *When highliting existing plantings for clearing, remember that in river restoration and habitat enhancement projects "clearing" should limit to the absolutely required minimum. That means: Delete as many polygons of existing plants as possble from `PlantClearing.shp`.*
    3.  Once all non-clearing plants are removed, save the edits.
	
5. *Project Maker* will not place any plant where existing plants are, even though when these are highlighted in the the `PlantClearing` shapefile. Therefore, consider to remove the polygons contained in `PlantClearing.shp` from `PlantExisting.shp`.

Save and close `ProjectName/ProjectMaps.aprx`.
**Note: Both `PlantExisting` and `PlantClearing` shapefiles are not mandatory for running *Project Maker*, but recommended.**

***

# Cost quantity assessment and the cost master workbook<a name="pmcq"></a>

The `ProjectName_assessment_vii.xlsx` is subsequently referred to as the **cost master workbook**. The workbook is automatically generated as a template-copy and it contains two `cost ...` tabs. **Important:** As a function of the unit system (U.S. Customary or SI metric), **only keep the relevant cost worksheet and delete the other one** (see below figure). **Rename the retained costs tab to `costs`**.

![pmdeltab](https://github.com/RiverArchitect/Media/raw/master/images/deltab.PNG)

The prices contained in the cost master workbook are in US\$ and may be adapted to fit local construction costs. The following sections describe steps and requirements for the assessment of cost-relevant quantities with the cost master workbook.

## Terraforming<a name="pmterraf"></a>

The [*VolumeAssessment*](VolumeAssessment) module evaluated terrain excavation and fill volumes. [*VolumeAssessment*](VolumeAssessment#workbook-spreadsheets) created workbooks featuring terraforming volumes in cubic meters/yards in the directory `RiverArchitect/VolumeAssessment/Output/PSEUDO_CONDITION_volumes.xlsx`. Optionally, these workbooks can be copied to a `PSEUDO_CONDITION_volumes.xlsx` workbook in the project folder.<br/>
Recall: *`PSEUDO_CONDITION_volumes.xlsx`* has to tabs: (1) *excavate\_YYYYMMDDHHhMM* and (2) *fill\_YYYYMMDDHHhMM*. Copy the terraforming volumes from either of these two spreadsheets to the cost master workbook's (`ProjectName_assessment_vii`) *terraforming\_volumes* spreadsheet (cells are highlighted, only values).<br/>
The template's unit costs of US\$ 23.00 per cubic yard (or EUR 23.00 per m<sup>3</sup>) include short transport distances (\< 1 km) and material storage. It is hypothesized that the smaller value (i.e., either the *excavate* or the *fill* volume) is incorporated in the costs of the higher value because the smaller volume can be reused on-site. The costs for terraforming are evaluated in cell *G8* of the *cost()* tab of *CONDITION*\_volumes.xlsx, based on the excavate and fill volumes that need to be copied to the *terraforming\_volumes* tab of *CONDITION*\_volumes.xlsx. The following formula applies (*vol* refers to the *terraforming\_volumes* spreadsheet):

*costs!G8 = costs!D8 · max(vol!C5, vol!C6)*


## Vegetation plantings and supporting features<a name="pmplants"></a>

Before the most reasonable vegetation plantings are implemented into the project plan, the [LifespanDesign][3] and  [*MaxLifespan*][4] modules need to be run based on anew 2D simulations made with the terraformed DEM. The resulting (maximum) lifespan rasters need to be available in the directories `RiverArchitect/LifespanDesign/Output/Rasters/CONDITION_lyr20/` and `RiverArchitect/MaxLifespan/Output/Rasters/CONDITION_lyr20/`.

**Define critical lifespans**<a name="pmactm"></a>
Before plantings can be placed, *River Architect* wants to know the critical threshold for lifespans that a plant species needs have to be applicable (2.5 may be a reasonable estimate here). For example, if the field *Do not plant where expected lifespans are less than* = `2.5`, *River Architect* will only place plantings with an expected lifespan of 2.5 years or more.
In addition, *River Architect* requires the definition of a critical lifespan of vegetation plantings, which require additional nature-based engineering support. For example, if the field *Stabilize plants where expected lifespans are less than* = `10.0`, *River Architect* will add supporting nature-based engineering features where the best performing plant species lifespan is less than 10.0 years.
Note that the second value needs to be higher than the first value to reasonable results.

**Place plantings**
The GUI's *Place best vegetation plantings* button launches a python function that picks up these maximum lifespan rasters, limits there extents to the *ProjectDelineation* Polygon and evaluates relevant quantities for construction purposes. Read the logfile carefully and ensure that no error or warning messages occurred. If error messages occurred, check the geodata sources and error messages, ensure that the costs master file (`ProjectName_assessment_vii.xlsx`) is closed and traceback error messages. Re-run *Delineate Plantings* and traceback error messages until no error messages occur anymore.<br/>
After a successful run, *Delineate plantings* has written vegetation plantings areas to the cost master workbook's *from\_geodata* spreadsheet. The *costs* spreadsheet automatically evaluates plantings in the *Vegetation plantings* frame. Nevertheless, double-check assigned cell links to the *from\_geodata* spreadsheet and close the cost master workbook. *Delineate plantings* saves the cropped maximum lifespan rasters and shapefiles with area summaries in the `/Rasters/` and `/Shapefiles/` subfolders. If the cell links in the automatically opened cost master workbook's *costs* spreadsheet are correct, save and close the workbook.
**Note: *Project Maker* places best plants in alphabetic order.** In the case of the pre-defined plant species, that means, first a pixel is tested for its suitability for *Box Elder*, then for *Cottonwood*, then *White Alder*, and then *Willow*s. If a pixel already got assigned a plant species, it will not be tested again for other plant species. For example, if a pixel got assigned *Box Elder*, it will not be considered for all other plant species.

**Stabilize plantings<a name="pmbio1"></a>**
Even though the vegetation plantings maximum lifespan maps identify the optimum [plant species](River-design-features#plants) according to the highest lifespans, the projected vegetation plantings may be associated with low lifespans. Therefore, supporting (stabilizing) features such as engineered log jams (here: single anchored logs or root wads) may be required. The GUI's `Stabilize plantings` button launches a python function that adds [stabilizing nature-based engineering features](River-design-features#bioeng) such as anchored wood logs to planting areas associated with the user-defined *minimum plantings lifespan*. The *Stabilize plantings* function uses the following priorities of stabilizing features:

1.  [Large wood logs](River-design-features#elj) (diameters defined in `RiverArchitect/LifespanDesign/.templates/`*threshold\_values.xlsx*) if their lifespan is higher than the *Critical  plantings lifespan*.

2.  [Engineered (anchored) wood logs](River-design-features#elj), where maximum lifespan maps indicate convenient applicability.

3.  [Vegetative nature-based engineering features](River-design-features#bioeng) (pre-defined in cost master workbook: brush layers; alternatively, fascines or geotextile can be linked from *costs!F30:F33* to *from\_geodata!C16\*...*, where the depth to the water table does not exceed the threshold values defined in `RiverArchitect/LifespanDesign/.templates/`*threshold\_values.xlsx*.

4.  [Mineralic nature-based engineering features (rock paving)](River-design-features#rocks), where the depth to the water table is insufficient for vegetative stabilization and where the terrain is steeper than the threshold values defined in `RiverArchitect/LifespanDesign/.templates/`*threshold\_values.xlsx*.

5.  [Angular boulders](River-design-features#rocks) where high dimensionless bed shear stress predictions prohibit the utilization of any above feature.

*Place best vegetation plantings* writes construction-relevant numbers for vegetation planting stabilization to the cost master workbook's *from\_geodata* spreadsheet. The *costs* spreadsheet automatically evaluates stabilizing feature quantities in the *nature-based engineering (stabilization)* and *nature-based engineering (other)* frames. Nevertheless, check the assigned cell links to the *from\_geodata* spreadsheet and adapt feature types if required. Moreover, *Stabilize plantings* creates a shapefile called (*Plant\_stab.shp*) in `ProjectName/Geodata/Shapefiles/`. **Check the cell links in the automatically opened cost master workbook's *costs* spreadsheet** (cell links to the *from\_geodata* spreadsheet). Finally, save and close the workbook.

## Stabilize terrain<a name="pmter"></a>

The `Terrain Stabilization` frame enables the identification of areas that require additional support with nature-based engineering features to yield a target lifespan that can be defined in the field *Critical lifespan*. For example, if new terraforms are intended to persist at least 20 years, set *Critical lifespan*=20.
A click on the `Stabilize terrain` button launches the calculations, where nature-based engineering features are placed in the same hierarchical order as before. Besides, the terrain stabilization calculates a [stable grain size Raster](River-design-features#rocks) for the provided *Critical lifespan*. The control variables of *&tau;<sub>\*,cr</sub>* (default 0.047) and [Manning\'s *n*][manningsn] can be defined by clicking on the `Set stability drivers` button. To learn more about the stable grain size computation, please refer to the [parameter calculation](LifespanDesign#inpras) and [stable grain size Raster creation](River-design-features#rocks).

The `Terrain Stabilization` produces writes relevant surfaces to the *from\_geodata* spreadsheet in costs master file (`ProjectName_assessment_vii.xlsx`) and produces the following geofiles:

 - Raster with stable grain (boulder) sizes `ProjectMaker/ProjectName_vii/Geodata/Rasters/terrain_boulder_stab.tif`
 - Shapefile with relevant [nature-based engineering features](River-design-features#bioeng) (see above definitions) `ProjectMaker/ProjectName_vii/Geodata/Shapefiles/Terrain_stab.shp`

**Check the cell links in the automatically opened cost master workbook's *costs* spreadsheet** (cell links to the *from\_geodata* spreadsheet). Finally, save and close the workbook.

## Manual placement of nature-based engineering features<a name="pmbio2"></a>

Additional habitat can be created with [cover features](SHArC#hemakecovhsi) (i.e., engineered logs jams or root wads) at locations that result from an expert assessment. To implement cover features, open `ProjectName/Geodata/ProjectName/ProjectMaps.aprx` to do the following:

1.  Create a new polygon-shapefile in `ProjectName/Geodata/Shapefiles/` and name it `StreamWood`.

2.  Remove the newly created `StreamWood` layer from layout's *Table of Contents*, double-click on the existing `ELJs (Cover habitat)` layer -> `Layer Properties` opens up -> go to the *Source* tab ->  click on *Set Data Source*... -> Select the newly created `ProjectName/Geodata/Shapefiles/StreamWood.shp` file -> click `OK`.

3.  `Start editing` the *`ELJs (Cover habitat)`* layer.

4.  Draw engineered log jams and root wads as 10 ft x 10 ft (3.1 m x 3.1 m) rectangles.<br/>
    ***Design hints**:*<br/>
    *[Engineered log jams](River-design-features#elj) and root wads must not be placed in side channels or anabranched sections of the rivers. However, these features can add "cover" habitat in backwater zones or reconnected ponds.*<br/>
    *A save premise is to keep a distance of at least 100 ft (or approximately 30 m) between individual log jams or root wads. To respect the distances, draw a circle with a diameter of 2·100 ft (or approximately 2·30 m) and place single engineered log jams in the middle of the circles.*

5.  Save the edits and stop editing.

6.  Write the number of drawn streamwood elements to the cost master workbook's (`ProjectName_assessment_vii`) *costs* spreadsheet (*nature-based engineering* frame).

## Other civil engineering works<a name="pmciv"></a>

Site access, terrain acquisition or culverts may be required and contribute to the project costs. Satellite images and GIS measurement tools help to identify the required length of new roads or roads that need to be developed.<br/>
The length of new roads can be evaluated (e.g., by drawing paths transferring the path length in yd' \[length yard\] or m' \[length meter\] to the cost master workbook's (`ProjectName_assessment_vii`) *costs* spreadsheet; cf. *Civil engineering \& other* frame). For later revision, export the drawn paths to a newly created folder (e.g., `ProjectName/Geodata/Shapefiles/`) as polyline shapefile or *\*.kmz* file.<br/>
The resulting costs need to be manually entered in the costs master workbook's (`ProjectName_assessment_vii`) *costs* spreadsheet (Civil engineering \& other frame).

## Markups, permitting, and other costs<a name="pmcadd"></a>

The final project costs include site mobilization and demobilization as well as unexpected costs. Moreover, permitting, markups (such as overhead, profit, and insurance) and engineering fees are added as percentages of costs for construction works at the bottom of the cost master workbook's (`ProjectName_assessment_vii`) *costs* spreadsheet. The total costs for the project proposal are summarized at the top of the *costs* spreadsheet (cell *G2*).

***

**Please note:**
 - **There is no warranty for the calculated costs ([see disclaimer](Disclaimer)).**
 - **All workbook-internal cell links must be verified manually, in particular, the `cost(UNITS)` tab.**

***

# Mapping of construction elements<a name="pmmaps"></a>

Open `ProjectName/ProjectMaps.aprx` and go to the `Catalog` tab (typically on the right). Click on `> Layouts` and double-click on `ProjectName_assessment_vii`. In the layout's *Contents* tab (typically on the left), select `Layers Map Frame` and double-click on every layer to define the correct dataset source files (`Source` tab) that result from the above-described cost assessment. *Note: Layer groups do not have a `Source` tab*. Relevant shapefiles are stored in `ProjectName/Geodata/Shapefiles/` and relevant rasters are stored in `ProjectName/Geodata/Rasters/`. Export the map (*ArcGIS Pro*s `Catalog` -> right-click on `Layouts/ProjectName_assessment_vii` -> select `Export to File...` ) to the project folder and name it `ProjectName_assessment_[...].pdf` (proposition for consistent file naming).

***

# Ecological benefit asessment (Calculate SHArea)<a name="pmSHArea"></a>

The project costs are vetted against the net gain in annually usable habitat area for target fish species. The GUI's *Calculate Net **S**easonal **H**abitat **Area*** routine calculates usable habitat from rasters that indicate where the composite Habitat Suitability Index (*cHSI*) is higher than a selected threshold value.

## Additional input and requirements<a name="pmadd"></a>

Every *cHSI* raster refers to a steady discharge within a flow duration curve. The expected flow exceedance duration per discharge bin multiplied with the usable habitat area is summed up to the [SHArea](SHArC#herunSHArea). The comparison of the existing (pre-project) and the "with implementation" (post-project) habitat suitability requires the following:

-   Both situations (pre- and post-project) were simulated in the 2D hydrodynamic model.
-   Flow duration curves for the project site were established:
    -   A workbook template for flow duration curves is available in `RiverArchitect/SHArC/FlowDurationCurves/flow_duration_templates.xlsx`
    -   The [`GetStarted`](GetStarted) tab contains the `Analyze Flow` tool for producing the required format for SHArea calculation in `00_Flows/CONDITION/`. 
-   The *River Architect*'s [*SHArC*][6] module was executed for both situations (pre- and post-project) to obtain [*cHSI* rasters](SHArC#herunchsi).
-   Example:
    -   The pre-project terrain DEM dates from 2008 and terrain modifications were performed based on the 2008 DEM in a reach called `rea`.
    -   Both DEMs, original and modified correspond to pre- and post-project conditions, respectively.
    -   Both DEMs were simulated in the 2D hydrodynamic model with discharges of 100, 200, 500, 1000, 2000, and 5000 cfs (or m<sup>3</sup>/s).
    -   The corresponding modelling results (flow depth and velocity) were stored in the directories `RiverArchitect/01_Conditions/CONDITION/` and `RiverArchitect/01_Conditions/CONDITION_rea_lyr10/`, respectively. The string `lyr10` refers to terraforming according to the code naming conventions.
    -   The *River Architect*'s [*SHArC*][6] module applied to both situations with a *cHSI* threshold value of, for example, &theta; = 0.5. This threshold value means that all pixels with a *cHSI* value lower than 0.5 were considered as being non-habitat and the [*SHArC*][6] module excludes these pixels from the *cHSI* rasters. Thus, the [*SHArC*][6] module produced *cHSI* rasters that are stored in:
        -   `RiverArchitect/SHArC/SHArea/Rasters/CONDITION/` (existing / pre-project)
        -   `RiverArchitect/SHArC/SHArea/Rasters/CONDITION_rea_lyr10/` (with implementation / post-project)
    -   The [*SHArC*][6] module associated (relative) discharge duration and usable habitat areas with the rasters. For example, if the target fish species was Chinook salmon, juvenile lifestage (naming convention `chju`), the [*SHArC*][6] module wrote the usable habitat area and discharge duration to the following workbook: `RiverArchitect/SHArC/SHArea/CONDITION_chju.xlsx`

## Run SHArea calculation<a name="pmrunSHArea"></a>

When the above requirements are fulfilled, the *Project Proposal* GUI can assess the difference in usable habitat area between both situations (pre- and post-project, i.e., the net gain in SHArea). For starting the calculation, define the above-described input data and confirm the calculation:

-   Select a [fish species](SHArC#hefish) corresponding to the one analyzed with the [*SHArC*][6] module (e.g., *Chinook salmon*, *juvenile*). The `Select fish` button turns green after selecting a target *fish species* + *lifestage*.
-   Select an initial condition (pre-project) and confirm the selection (button turns green after selection).
-   Select a condition after terraforming (with implementation / post-project) and confirm the selection (button turns green after selection.
-   Click on the *Calculate Net gain in SHArea* button to start the assessment.

The program will run in the background and prompts the calculation progress in the console window.

After running the program, discharge-specific usable habitat area was written to a spreadsheet located in `ProjectName/Geodata/SHArea_evaluation_UNIT.xlsx` (see output section below).

***

## Output<a name="pmiout"></a>

After a successful run, a copy of the **cost master workbook** with the file name extension corresponding to the target fish automatically opens. For example, if the target fish was Chinook salmon - juvenile, the copy of the workbook is ...`/ProjectName_assessment_vii_chju.xlsx`.

Moreover, the particular **usable areas associated with the available discharges were written** to `/Geodata/SHArea_evaluation_chju.xlsx`.

The discharge-related **shapefiles** with polygons of usable habitat area were saved as: `ProjectName/Geodata/Rasters/CONDITION/no_cover/NUM_SHArea_eval.shp`. `NUM` is an automated prefix added by the SHArea evaluation routine. The association of the `NUM` shapefile with the corresponding discharge was logged to `ProjectName/Geodata/logfile_40.log`.

The cells *G3* and *I2/3* in `ProjectName_assessment_vii_FILI.xlsx` state the net gain in SHArea and the project return in units of US\$ per acre (or m<sup>2</sup> per EUR or any other currency defined) net gain in SHArea (comparison of pre-and post-project condition), respectively.


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

[manningsn]: https://en.wikipedia.org/wiki/Manning_formula#Manning_coefficient_of_roughness
