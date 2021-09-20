Seasonal Habitat Area Calculator (SHArC)
========================================

***

- [Introduction to Habitat Suitability evaluation](#heintro)
- [Quick GUIde to habitat suitability evaluation](#hequick)
  * [Main window set-up and run](#main-window-set-up-and-run)
  * [Input: Physical Habitats for Fish](#hefish)
  * [Input: Define computation boundaries](#hebound)
  * [Input: HHSI](#hemakehsi)
  * [Input: Cover HSI](#hemakecovhsi)
  * [Input: Combine methods (of habitat suitability Rasters)](#hecombine)
  * [Combine habitat suitability Rasters](#herunchsi)
  * [Calculate SHArea](#herunSHArea)
  * [Output and application in stream restoration projects](#heoutput)
  * [Quit module and logfile](#quit-module-and-logfile)
- [Working principles](SHArC-working-principles#heprin)
  * [Cover HSI: Substrate](SHArC-working-principles#subshsi)
  * [Cover HSI: Boulder](SHArC-working-principles#bouhsi)
  * [Cover HSI: Cobble](SHArC-working-principles#cobhsi)
  * [Cover HSI: Streamwood](SHArC-working-principles#woohsi)
  * [Cover HSI: Vegetation](SHArC-working-principles#veghsi)
  * [Cover HSI combination methods](SHArC-working-principles#hecombinecov)
  * [Usable habitat area calculation](SHArC-working-principles#hewuamethods)
- [More about Physical Habitats and Modifying `Fish.xlsx`](aqua-modification#hecode)

***

# Introduction to Habitat Suitability evaluation<a name="heintro"></a>

The *SHArC* module creates habitat suitability index (*HSI*) Rasters for various fish species and combines multiple HSI Rasters into a composite habitat suitability index Raster (*cHSI* or *CSI*). The habitat suitability index ranges between 0.0 and 1.0, according to [Bovee (1986)][bovee86]. It uses a threshold value for defining valuable habitat, which is initially set to 0.5 (i.e., *HSI* values between 0.0 and 0.5 or `NoData` are considered as *"non-habitat"* and values between 0.5 and 1.0 correspond to valuable habitat). 
A minimum of three normal discharges within a seasonal flow duration curve should be provided (e.g., the *Q<sub>300</sub>*, *Q<sub>200</sub>* and *Q<sub>100</sub>* denote the flows that are exceeded during 300, 200 and 100 days per year, respectively). The module's [*HHSI* (Hydraulic Habitat Suitability Index) Raster generator](#hemakehsi) provides routines to produce seasonal flow duration curves from discharge series. The *SHArC* module uses the resulting seasonal flow exceedance probabilities that are associated with *cHSI* Rasters for summing up the surface where the *cHSI* is larger than the threshold value (of 0.5 by default). This surface corresponds to the [**S**easonal **H**abitat **Area** (**SHArea**)](#herunSHArea) in \[m<sup>2</sup> per season\] or \[acres per season\]. *Note* that **seasonal refers to the Physical Habitat present during a user-defined fish-lifestage period** (see [definitions of Physical Habitats for fish-lifestage](#hefish)). The module writes relevant flows, exceedance properties and the SHArea to `CONDITION`-related spreadsheets in the `SHArC/SHArea/` directory.

*Note that the SHArC module has no own mapping function. `cHSI` Rasters may be mapped with the project assessment templates of the ProjectMaker module.*


# Quick GUIde to habitat suitability evaluation<a name="hequick"></a>

***

## Main window set-up and run<a name="hegui"></a>

The below figure shows the *SHArC* GUI at start-up.

![guihe](https://github.com/RiverArchitect/Media/raw/master/images/gui_start_he.PNG)


To begin a habitat evaluation as a function of *SHArea*, the module first requires a definition of relevant Physical Habitats for target fish species and lifestages that it [reads from a workbook](#hefish).
Second, [hydraulic habitat suitability Rasters](#hemakehsi) and related discharge exceedance probabilities need to be calculated. The latter step creates habitat conditions, which can now be selected. Once a habitat condition is selected, the next step [combines flow depth and velocity habitat suitability Rasters](#herunchsi). Finally, [*SHArea* is computed](#herunSHArea) based on combined habitat suitability Rasters, with or without *cover*.


## Input: Physical Habitat for Fish<a name="hefish"></a>

The `Select Physical Habitat` menu enables the definition of flow depth and velocity-dependent habitat suitability curves, as well as travel thresholds for use in the [Stranding Risk](StrandingRisk) module. The `DEFINE FISH SPECIES` menu entry opens a workbook called `Fish.xlsx`, which is located in `RiverArchitect/.site_packages/templates/`. The `Fish.xlsx` workbook contains the definition of fish species names (rows 2 to 4) and up to four lifestages per species. For every lifestage, a preference season and piece-wise linear habitat suitability curves can be entered. Moreover, the default workbook contains a global definition of aquatic habitat (`All Aquatic`), where a hydrologic year, season, flow depth, and/or velocity lifestage-like definition can be made. These lifestage-like definitions correspond to wetted area that may be considered for an entire hydrologic year, limited to a season, and/or pixels where a minimum flow depth (default: 0.001 m or ft) or velocity (default: 0.001 m/s or fps) is present. The `All Aquatic` habitat suitability curves assign a theoretic habitat suitability index of 1.0 to all wetted pixels (i.e., where the flow depth or velocity is larger than 0.001).

![hefish](https://github.com/RiverArchitect/Media/raw/master/images/RA_HE_fish_xlsx.png)

All definitions made in this workbook need to respect the default workbook structure:

- Season start in row 6 (*DD*-*MMM*, e.g., 15-Mar). *Note that Office programs will automatically add a year, too. Just ignore the year added, because River Architect only reads the month and day.*

- Season end in row 7 (*DD*-*MMM*, e.g., 15-Mar). 

- Flow velocity *u* in row 9 to 36.

- Flow depth *h* in row 38 to 70.

- Substrate (grain size) *D* in row 72 to 79.

- Cover (minerals) in row 81 to 82. `Min` (in *\%*) describes the minimum surface occupation of either `Cobble` or `Boulder` that is required to improve habitat by an HSI value.

- Cover (vegetative) in row 84 to 85. `Rad.` defines the radius around single `Plants` or `Wood` placements, where habitat improves by an HSI value.

- Habitat Suitability Index curves can be found in the scientific literature with the the following keywords: `Habitat Suitability`, `Index`, `Curve`, *`TARGET SPECIES`* (e.g., [here](https://www.science.gov/topicpages/h/habitat+suitability+curves)).

- Fish lifestages must be named either `spawning, fry, ammocoetes, juvenile, adult, hydrologic year, season, depth > x`, `velocity > x`, or `"rearing": 7`. The lifestage names are currently hard-coded in the `Fish` class (`RiverArchitect/.site_packages/riverpy/cFish.py`) dictionary `self.ls_col_add = {"spawning": 1, "fry": 3, "ammocoetes": 3, "juvenile": 5, "adult": 7, "hydrologic year": 1, "season": 3, "depth > x": 5, "velocity > x": 7, "rearing": 7}` (see [known issues](Troubleshooting#issues)). This dictionary can be changed for using other lifestage names and we are working on an improvement in later versions. Note that this dictionary defines the relative column numbers that are added to the column where the fish species name is defined (e.g., for name=*Chinook Salmon*, the start column is "C" and the *spawning*-column is "C+1"="D", while the "fry"-column is "C+3"="F" and so on). For example, for adding a `"rearing"` lifestage for `Chinook salmon` (one of the default species), `"rearing"` must replace `"adult"`, which is in the relative 7th (col."C"+7 = "J" column) of the Chinook salmon species. In fact, the species names are written to merged cells that cover two columns (see below table), but *River Architect* only reads the numeric value from `self.ls_col_add` to access curve data. **Thus, all lifestages must be defined in `self.ls_col_add`, as relative column number to the 0-column of every Fish species.** The following overview table of merged cells shows where to put what lifestage relative to the 0-column (**REMIND other lifestages than these required modifications of `self.ls_col_add` in `RiverArchitect/.site_packages/riverpy/cFish.py`):

|LIFESTAGE | REL. COl. NO. | EXAMPLE FOR CHINOOK SALMON |
|----------|---------------|----------------------------|
| spawning | 1 | C-D |
| fry | 3 | E-F |
| ammocoetes | 3 | E-F |
| juvenile | 5 | G-H |
| adult | 7 | I-J |
| rearing | 7 | I-J |
| hydrologic year | 1 | C-D (example: All Aquatic AI-AJ)|
| season | 3 | E-F (example: All Aquatic AK-AL)|
| depth > x | 5 | G-H (example: All Aquatic AM-AN)|
| velocity > x | 7 | I-J (example: All Aquatic AO-AP)|


The `Season start` and `Season end` dates are important in the flow duration generation for *HHSI* curves. For the consideration of entire hydrological years (or [water years](https://en.wikipedia.org/wiki/Water_year)), define `Season start` as `1-Oct` and `Season end` as `30-Sep` (in the United States and Switzerland, in Germany from `1-Nov` to `31-Oct` according to the definition of an *Abflussjahr* in the [DIN 4049](https://www.din.de/en/getting-involved/standards-committees/naw/standards/wdc-beuth:din21:1987523)). Hydrological/water years are defined based on the assumption that water resources are smallest in fall. Fish seasons are relevant for habitat assessment because fish grows and a lifestage (e.g., juvenile) may not be relevant for the entire year (that means: possibly not use the entire year).

Ensure the application of the correct unit system; the drop-down menu in the `Fish.xlsx` workbook automatically sets the units of flow velocity *u*, flow depth *h*, grain size *D*, and delineation radius *Rad* around polygons. The radius *Rad* describes the *"effect"* perimeter of boulders, plants and/or wood that is drawn around the delineated polygons.

The base scenario provides habitat suitability curves for four sample fish species. More fish species can easily be appended by copy-pasting the template frame (area in thick borders in the `template` sheet) after the last defined fish species. For example, if another fish species is added to the base scenario, cells `C2` to `J85` from the `template` sheet are copied and pasted at cell `AI2` in the `fish` sheet. However, the number of lifestages per fish species and the above-stated rows need
to be respected when entering piece-wise linear habitat suitability functions. The U.S. Forest Service provides [data](http://www.fsl.orst.edu/geowater/FX3/help/SwimData/swimtable.htm) that may help define additional fish species (especially for [Stranding Risk](StrandingRisk) analysis).<br/>
The structure of `Fish.xlsx` must not be modified (inserting or deleting rows or columns) unless the module's source code is also changed (not recommended). If the structure is changed anyway, the module needs to be modified as explained in the [code section](aqua-modification#hecode).<br/>
Note that any relevant species-lifestage needs to have at least one entry for the velocity habitat suitability curve, as the module uses this first data cell in every column to verify if it contains data or not. For example, if a substrate habitat suitability curve is given, but the velocity habitat suitability curve is left blank, the concerned lifestage will not be considered relevant.<br/>
*River Architect* uses the piece-wise linear curves of habitat suitability indices to interpolate the HSI value of Raster pixels. For example, if a velocity Raster's pixel has a value of 0.51 (fps or m/s), the module looks up the HSI values related to the next smaller or equal provided value (e.g., 0.5 fps or m/s) and the next higher value (e.g., 0.6 fps or m/s) and linearly interpolates the habitat suitability index for 0.51 (fps or m/s). Thus, the numeric expression to determine the linear function piece in this example is `if 0.5<= 0.51 < 0.6: interpolate()`. The calculation function is called `nested_con_raster_calc(ras, curve_data)`, which is implemented in the `HHSI()` class (`SHArC/cHSI.py`), where `ras` is a depth or velocity *GeoTIFF* Raster and `curve_data` (type: nested `LIST`) are the linear break points defined in `Fish.xlsx`. The Raster calculation expression is (simplified code snippet): 

```python
__ras__ = [ras * 0]  # initial raster assignment
index = 0
i_par_prev = 0.0
i_hsi_prev = curve_data[1][0]
for i_par in curve_data[0]:
	__ras__.append(Float(Con((Float(ras) >= Float(i_par_prev)) & (Float(ras) < Float(i_par)), ( Float(i_hsi_prev) + ((Float(ras) - Float(i_par_prev)) / (Float(i_par) - Float(i_par_prev)) * Float(curve_data[1][index] - i_hsi_prev))), Float(0.0))))
	i_hsi_prev = curve_data[1][index]
	i_par_prev = i_par
	index += 1
return Float(CellStatistics(__ras__, "SUM", "DATA"))
```


## Input: Define computation boundaries<a name="hebound"></a>

A boundary shapefile (polygon) can be selected to limit the calculation extents and assessment of the Annually Usable habitat Area SHArea. Typically, that shapefile should be stored in `RiverArchitect/01_Conditions/CONDITION/boundary.shp/.tif` (or [`RiverArchitect/ProjectMaker/ProjectName/Geodata/Shapefiles/ProjectArea.shp`](ProjectMaker#pminp2)) and it should contain one valid polygon with an `Id` field value of `1` for that rectangle in the `Attribute table`.

## Input: HHSI<a name="hemakehsi"></a>

Before habitat suitability Rasters can be calculated, at least one fish species/lifestage needs to be selected (multiple selections are possible) because *SHArC* will only use hydraulic Rasters that are relevant to the selected Physical Habitat for a fish-lifestage (see [*Season start* and *Season end* in *Fish.xlsx*](#hefish)).<br/>

With at least one fish species-lifestage selected, HSI Rasters can be generated by clicking on the `Generate HSI Rasters` menu and `Flow depth and velocity HSI`. A new window opens and first asks for a discharge (or flow) duration curve:

![hefish](https://github.com/RiverArchitect/Media/raw/master/images/exp_HE_subgui.PNG)

A flow duration curve for a preferred Physical Habitat of target fish-lifestages can be generated from any discharge series within the [Get Started][2] module, which produces correctly formatted flow duration workbooks in `RiverArchitect/00_Flows/CONDITION/flow_duration_FILI.xlsx`. The flow duration curve generation only considers discharges observed within the seasons defined in [`RiverArchitect/.site_packages/templates/Fish.xlsx`](#hefish). For the consideration of completed hydrology years, define `Season start` as `1-Oct` and `Season end` as `30-Sep` (see above discussion).

In the process of *HHSI* Raster generation, the produced flow duration curves can (must) be used by clicking the `i) Select flow duration curve (.XLSX)` button, which button opens the file explorer in `RiverArchitect/00_Flows/`. 
The flow duration workbook must list discharges in column `A`, starting at row 2 in descending order. The discharges need to be positive float numbers. The associated exceedance durations (`%`) are stated in column `C`.

Second, hydraulic habitat conditions need to be selected. *River Architect* looks up available hydraulic habitat conditions in `RiverArchitect/01_Conditions/`. After highlighting (click) one of the available hydraulic conditions, a click on the `Select` button generates a workbook in `RiverArchitect/SHArC/SHArea/` with the name `CONDITION_FILI.xlsx` for each previously selected fish. The `FILI` string abbreviates the selected fish species and lifestage, where `FI` represents the first two letters of the fish species and `LI` the first two letters of the fish lifestage. Existing workbooks for the same condition and fish are renamed (`old` gets appended to the file name). Older `...old.xlsx` workbooks are overwritten.<br/>
The generated `CONDITION_FILI.xlsx` can be opened by clicking on the `Optional: View discharge dependency file` button. If opened, close this workbook before continuing. Until here, only the columns `B` to `E` should contain values, which constitute the plotted flow duration curve.<br/>
Finally, a click on `Run (generate habitat condition)` launches the calculation of hydraulic habitat suitability index (HHSI) Rasters, which are created in `RiverArchitect/SHArC/HSI/CONDITION/`. The window starts flashing when the calculation finished. For returning to the main window (it partially freezes while the HHSI window is open), click on the `RETURN` button.
The resulting depth-*HSI* Rasters are named `dsi_FILIqqqqqq` and velocity-*HSI* Rasters are named `vsi_FILIqqqqqq`. The `qqqqqq` string refers to the discharge that is derived from the name of flow depth Rasters stored in `RiverArchitect/01_Conditions/CONDITION/`. Please note, that the maximum discharge that can be handled is 999999 cfs or 999999 m<sup>3</sup>/s because of the maximum length of Raster file names (if GRID Rasters are used).

## Input: Cover HSI<a name="hemakecovhsi"></a>

As before, at least one Physical Habitat for fish species/lifestage needs to be selected (multiple selections are possible). The cover HSI Raster generation can be limited to a user-defined flow region by selecting one of the `hQQQQQQ` Raster names in the `2) Define flow region` frame. However, the later combination of the cover HSI Rasters with the HHSI (hydraulic HSI) Rasters will automatically limit the usable habitat area to wetted pixels only. Thus, the most pertinent choice here is selecting `all terrain`. Click on `Confirm selection` to do so.<br/>
Relevant cover types can be selected by checking the according checkboxes, where geofiles are required to be stored in
`RiverArchitect/01_Conditions/CONDITION/` apply the cover types: 

-   Substrate: A `dmean` (S.I. /metric units) or `dmean_ft` (U.S. customary units) Raster is required (see [Signposts](Signposts#input-file-preparation)).

-   Boulders: A `boulders.shp` polygon shapefile is required; the polygons delineating boulders need to have a `Short Integer`-type field called `cover` in the (`Attributes table`) and the `cover` field value of polygons is `1`.

-   Cobbles: A `dmean` (S.I. /metric units) or `dmean_ft` (U.S. customary units) Raster is required (see [Signposts](Signposts#input-file-preparation)). Cobble is defined, where the `dmean...` Raster indicates grain sizes between 0.064 m and 0.256 m.

-   Plants: A `plants.shp` polygon shapefile is required; the polygons delineating plants need to have a `Short Integer`-type field called `cover` in the (`Attributes table`) and the `cover` field value of polygons is `1`.

-   Wood: A `wood.shp` polygon shapefile is required; the polygons delineating woods need to have a `Short Integer`-type field called `cover` in the (`Attributes table`) and the `cover` field value of polygons is `1`.

The geofiles are used with the habitat suitability (curve) definitions in the `Fish.xlsx` workbook (tab `fish`), which is located in `RiverArchitect/.site_packages/templates/`.<br/>
*HINT:* The applicable cover types are limited to the terms "Substrate", "Boulders", "Cobbles", "Plants", and "Wood".
Bridge piers or other structural turbulence objects may constitute other cover types that are not explicitly implemented in the *SHArC* module. However, may cover types can be associated with similar effects as the implemented cover types. Thus, other cover types can be added as polygons in the shapefiles for "Boulders", "Plants", or "Wood" cover types.


## Input: Combine methods (of habitat suitability Rasters)<a name="hecombine"></a>

The module provides the options of either using the geometric mean or the product to combine depth and velocity Rasters (and eventually cover Rasters). The following formulae are implemented to combine a depth HSI Raster *DHSI* with a velocity HSI Raster *VHSI* to a *cHSI* Raster **if no cover applies**:

Geometric mean: *cHSI = (DHSI · VHSI)<sup>1/2</sup>*<br/>
Product: *cHSI = DHSI · VHSI*


**If** a **cover** HSI Raster *covHSI* is used, the following formulae **apply**:

Geometric mean: *cHSI = (DHSI · VHSI · covHSI)<sup>1/3</sup>*<br/>
Product: *cHSI = DHSI · VHSI · covHSI*

The cover HSI Raster *covHSI* represents the maximum pixel values of applied [cover types](#hecombinecov).

***

## Combine habitat suitability Rasters<a name="herunchsi"></a>

Back in the main window, select one available habitat condition (hydraulic either with or without cover) and confirm the selection. The available habitat conditions refer to the conditions created with the [`Make HSI Rasters` routines](#hemakehsi). Confirming the selection activates the `Combine HSI Rasters ...` buttons for launching the combination of HSI Rasters. The [*HSI* Rasters can be combined](#hecombine) either using the geometric mean or as their product by (un-)checking one of the checkboxes above the `Combine HSI Rasters ...` buttons. The default [combine method](#hecombine) is `Geometric mean`.<br/>
Two combination buttons are available: (1) `pure hydraulic` and (2) `hydraulic and cover`. Additional habitat in terms of turbulent eddies created by cobbles, boulders, submerged plants, and streamwood is not well determined by 2D numerical models. **Cover** adds additional habitat as a function of the relative cobble or boulder surface and the proximity of plants or streamwood. This method values artificially placed cobbles, boulders, submerged plants and streamwood in stream restoration projects. *Cover* delineation may require considerable efforts in terms of drawing polygons around stream restoration elements.

*CSI* or *cHSI* Rasters are created in `RiverArchitect/SHArC/CHSI/CONDITION/`.


## Calculate SHArea<a name="herunSHArea"></a>

The `Run Seasonal Habitat Area Caluclator - SHArC` button launches the [calculation of usable SHArea](#herunchsi) based on the combined habitat suitability index (*cHSI*). Usable (habitat) area is defined as the surface where *cHSI* (or *CSI*) pixel values are larger than the `SHArea threshold` *&theta;*. *SHArea* is defined as the sum of usable habitat areas of *cHSI* of relevant discharges multiplied with the relative presence (*p<sub>Qk</sub>*). Relevant discharges occur every year during the Physical Habitat (fish-lifestage) presence season that is defined by the [*Season start* and *Season end* tags in *Fish.xlsx*](#hefish). Thus, *SHArea* as the sum of discharge-related usable habitat area is:

*SHArea = &Sigma;<sub>Qk</sub> \[ &Sigma;<sub>px</sub>(\{if cHSI(<sub>px</sub>) > &theta;\}· A<sub>px</sub>)· p(Q<sub>k</sub>)\]*

where ***<sub>px</sub>*** denotes "pixel" and ***A<sub>px</sub>*** is the size of a pixel in m² (or ft²). By default, this threshold value ***&theta;*** is 0.5 (i.e., the routine sums up the surface of pixels where the *cHSI* is larger than 0.5). The threshold value can be changed by clicking on the `Set SHArea threshold ...` button. The expression ***\{if cHSI(<sub>px</sub>) > &theta;\}*** is **1** if the *cHSI* value of a pixel is higher than *&theta;* and it is **0** if the *cHSI* value of a pixel is smaller than *&theta;*. ***p<sub>Qk</sub>*** denotes the relative seasonal presence of a discretized discharge ***Q<sub>k</sub>*** that is associated with a set of hydraulic Rasters (flow depth and velocity). *River Architect* converts usable habitat area rasters to polygon shapefiles and adds an `AREA` field  to the shapefiles where Polygon areas are calculated using `arcpy.CalculateGeometryAttributes_management(shp_name, geometry_property=[["F_AREA", "AREA"]], area_unit=user_area_unit)`; where `shp_name`is a temporary shapefile and `user_area_unit`is the user-defined unit system (US customary or metric). The resulting discharge-specific area is written to a spreadsheet located in `SHArC/SHArea/CONDITION_sharea_...xlsx`. 
*Note: For specific project, intermediate area calculation results are written to workbooks when SHArea is calculated within the [Project Maker](ProjectMaker#pmrunSHArea) module.*

 The below figure illustrates the *SHArea* integration scheme based on the application of four discharges (1000, 2000, 3000, and 4000 m<sup>3</sup>/s or cfs) of an Physical Habitat for a fish-lifestage season.

![SHAreaint](https://github.com/RiverArchitect/Media/raw/master/images/RA_HE_integration.png)

Launch the *SHArea* calculation by clicking on `Run Seasonal Habitat Area Calculator - SHArC`. The resulting workbooks will be written to `RiverArchitect/SHArC/SHArea/CONDITION_sharea_FILI.xlsx`. The `SHArC` routine fills column `F` in `CONDITION_sharea_FILI.xlsx`, which automatically calculates column `G`: Area per discharge. Thus, the *SHArea* value in cell `J2` is the sum of column `G`. 
*CHSI* Rasters with relevant information for usable (wetted / habitat) area will be stored in `RiverArchitect/SHArC/SHArea/Rasters_CONDITION/`. The Raster statistics correspond to the numbers written to column `F` in `RiverArchitect/SHArC/SHArea/CONDITION_sharea_FILI.xlsx`.

<!--## Use WUA (Weighted Usable Area) Option<a name="hewua"></a>
Included in the SHArea calculation is an option to apply weighting to the usable area. Weighting the surface area of each pixel by the combined habitat suitability index (*cHSI*) results in an index known as the weighted usable area (*WUA*) that was first described in [Bovee (1982)][bovee82]. To calculate the sum of the discharge-related *WUA* of a given site: 

*WUA* = *cHSI<sub>mean</sub>* · &Sigma; A<sub>pixels</sub>

Before clicking on`Run Seasonal Habitat Area Calculator - SHArC`, check the box above to enable the `Use weighted usable area` option to apply weighting to the calculation.  By default, when this option is enabled the cHSI threshold value  *&theta;* will be set to 0.0 (i.e., all cHSI values, including 0.0, are used to weight the area of each pixel).-->

## Q - Area Analysis<a name="heqa"></a>
The time evolution or (interpolated) habitat area associated with a discharge provide insights into the ecological efficiency of a habitat enhancement measures. The *SHArC* module can generate interpolated discharge-usable habitat area curves even for discharges that were not numerically modeled with a 2D hydrodynamic simulation. A click on the `Discharge - Physical Habitat Area Curve` or `Time series - Physical Habitat Area` button generates habitat area graphs as a function of all discharges of a flow duration curve or a discharge time series, respectively.<br/>
For flow duration curves, by default, *SHArC* uses the discharge duration workbook `flow_duration_FILI.xlsx` associated with the habitat *CONDITION* in `RiverArchitect/00_Flows/CONDITION/`. This behavior can be changed by checking the *Use other flow duration curve* box. The resulting *Discharge - Physical Habitat Area Curve* will be produced in `SHArC/SHArea/CONDITION_QvsA_FILI_stats.xlsx` that contains the following diagram:

![hefish](https://github.com/RiverArchitect/Media/raw/master/images/RA_QvsA_stats.png)

The flow time series calculation will ask for a workbook with mean daily discharges, similar to the [Get Started][2] module. The time series workbook must be organized as follows:
- The file ending must be `.xlsx`
- Column `A` must contain dates, where 
	+ row `1` is the header (i.e., `A1 = "Date"`), 
	+ row `2` indicates the date units (i.e., `A2 = "(DD-MM-YY)"`), and 
	+ date series must be entered from row `3` onward (i.e., dates in the format `A3 = 5-Sep-03` or `A4 = 9/5/2003`).
- Column `B` must contain mean daily flows, where 
	+ row `1` is the header (i.e., `B1 = "Mean daily"`), 
	+ row `2` indicates the date units (i.e., `B2 = "(CFS)"` or `B2 = "(CMS)"), and 
	+ mean daily flows must be entered from row `3` onward (i.e., dates in the format `B3 = 59.3` or `B4 = 79`).

The resulting *Time series - Physical Habitat Area* will be produced in `SHArC/SHArea/CONDITION_QvsA_FILI_time.xlsx` that contains the following diagram:

![hefish](https://github.com/RiverArchitect/Media/raw/master/images/RA_QvsA_time.png)

***

## Output and application in riverscape habitat enhancement projects<a name="heoutput"></a>

The `RiverArchitect/SHArC/SHArea/CONDITION_FILI.xlsx` workbook contains the key outputs of this module. The usable habitat area, related to analyzed discharges, in column `G` and their sum (*SHArea*) in cell `J2` are important figures for comparing two situations (`CONDITION`s).<br/>
For example, a relevant question can be "What was the annually usable habitat area for juvenile Chinook salmon in the year 2008 compared with 2014?" Comparing both the SHArea in `2008_sharea_chju.xlsx` and the *SHArea* in `2014_sharea_chju.xlsx` answers the question.<br/>
Another relevant question may be "How much did terraforming increase *SHArea*?". To answer this question, the habitat conditions of a (hydraulic) `CONDITION` need to be evaluated based on 2D hydrodynamic model outputs for multiple discharges within the annual flow duration curve. Then, layer 1 terraforming features (see [Signposts][2] and the [*ModifyTerrain*][5] module) need to be implemented into the DEM of the `CONDITION`. The 2D hydrodynamic model needs to be re-run using the modified DEM and the same set of multiple annual flow duration discharges. Based on the sets of hydraulic Rasters (flow depth and velocity), the *SHArC* module can compute the *SHArea* for both conditions and selected fish species (e.g., *SHArea* of a 2014 DEM for juvenile Chinook salmon is originally calculated in `2014_sharea_chju.xlsx` and the *SHArea* of the modified (terraformed) 2014 DEM will be contained in `2014_lyr10_sharea_chju.xlsx`). Comparing the `J2` cells of both workbooks reveals the net gain in *SHArea*. When multiple restoration variants have to be compared, the net gain in *SHArea* of all variants can be vetted against construction costs to obtain a price in terms of US\$ per m<sup>2</sup> (or acres) gained in *SHArea*.

## Quit module and logfile<a name="hequit"></a>

The best option to quit the module is the `Close` dropdown menu if no background processes are going on (see terminal messages), where also the processing `logfile.log` can (should) be opened and reviewed for any error messages.


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

[bovee86]: https://pubs.er.usgs.gov/publication/70121265
[bovee82]: https://www.arlis.org/docs/vol1/Susitna/1/APA193.pdf
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
