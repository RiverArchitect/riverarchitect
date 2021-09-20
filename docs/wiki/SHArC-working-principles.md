SHArC - Working Principles
==========================

***

- [Introduction to Habitat Suitability evaluation](SHArC#heintro)
- [Quick GUIde to habitat suitability evaluation](SHArC#hequick)
  * [Main window set-up and run](SHArC#main-window-set-up-and-run)
  * [Input: Physical Habitats for Fish](SHArC#hefish)
  * [Input: Combine methods (of habitat suitability Rasters)](SHArC#hecombine)
  * [Input: Define computation boundaries](SHArC#hebound)
  * [Input: HHSI](SHArC#hemakehsi)
  * [Input: Cover HSI](SHArC#hemakecovhsi)
  * [Combine habitat suitability Rasters](SHArC#herunchsi)
  * [Calculate SHArea](SHArC#herunSHArea)
  * [Output and application in river restoration projects](SHArC#heoutput)
  * [Quit module and logfile](SHArC#quit-module-and-logfile)
- **Working principles**
  * [Cover HSI: Substrate](#subshsi)
  * [Cover HSI: Boulder](#bouhsi)
  * [Cover HSI: Cobble](#cobhsi)
  * [Cover HSI: Streamwood](#woohsi)
  * [Cover HSI: Vegetation](#veghsi)
  * [Cover HSI combination methods](#hecombinecov)
  * [Usable habitat area calculation](#hewuamethods)
- [More about Physical Habitats and Modifying `Fish.xlsx`](aqua-modification#hecode)

***

# Working principles<a name="heprin"></a>
***


## Cover HSI: Substrate<a name="subshsi"></a>

A `dmean` Raster is needed in the `RiverArchitect/01_Conditions/CONDITION/` folder. If this box is checked,
a `substrate_hsi` Raster is created in `RiverArchitect/SHArC/HSI/CONDITION/`. The applied Habitat Suitability Curves can be adapted by clicking on the `Edit HSCs` button.

## Cover HSI: Boulder<a name="bouhsi"></a>

A `boulder` shapefile containing polygons with boulder sizes (diameters) needs to be available in `RiverArchitect/SHArC/Cover/CONDITION/`. The polygons need to be manually delineated for the entire region of interest. The module will convert boulder size information into a Raster and retain boulders with a size larger than a threshold value. Areas, where the boulder presence covers more than 30\% of the surface get assigned an HSI value of 0.5. Both the 30\% surface ratio and the associated HSI of 0.5 can be changed for every Physical Habitat for [fish species and lifestages](SHArC#hefish).

## Cover HSI: Cobble<a name="cobhsi"></a>

A `cobble` Raster containing substrate sizes (cobble diameters) needs to be available in `RiverArchitect/SHArC/HSI/CONDITION/`. The module will evaluate the percentage of area that is covered with cobble larger than a threshold value (grain size). Areas, where the percentage area covers more than 30\% of the surface get assigned an HSI value of 0.3. Both the 30\% surface ratio and the associated HSI of 0.3 can be changed for every Physical Habitat for [fish species and lifestages](SHArC#hefish).


## Cover HSI: Streamwood<a name="woohsi"></a>

A `streamwood` shapefile containing polygons with single wood elements needs to be available in `RiverArchitect/SHArC/HSI/CONDITION/`. The module draws polygons with a user-defined radius around the streamwood polygons and
assigns a value of `1` to these polygons. The new polygons are converted into a Raster and an HSI value of 0.3 is assigned to `1`-pixels. The user-defined radius and the associated HSI of 0.3 can be changed for every Physical Habitat for [fish species and lifestages](SHArC#hefish).


## Cover HSI: Vegetation<a name="veghsi"></a>

A `plantings` shapefile containing polygons with single plants needs to be available in `RiverArchitect/SHArC/HSI/CONDITION/`. The module draws polygons with a user-defined radius around the plant polygons and assigns a value of `1` to these polygons. The new polygons are converted into a Raster and an HSI value of 0.3 is assigned to `1`/pixels. The user-defined radius and the associated HSI of 0.3 can be changed for every Physical Habitat for [fish species and lifestages](SHArC#hefish).


## Cover HSI combination methods<a name="hecombinecov"></a>

The cover Rasters are combined by selecting the maximum value of the superposition of applied cover types: `covHSI = arcpy.sa.Float(arcpy.sa.CellStatistics(applied_covers, ”MAXIMUM”, ”DATA”))`, where `applied_covers` is a list of `arcpy.Raster()`s of applied cover types.

## Usable habitat area calculation<a name="hewuamethods"></a>

The usable area is measured by converting *cHSI* Rasters to polygon shapefiles using `arcpy.RasterToPolygon_conversion(cHSI, polygon_shp, ”NO_SIMPLIFY”)`. The area of single polygons is calculated by `arcpy.CalculateGeometryAttributes_management(polygon_shp, geometry_property=[["F_AREA", "AREA"]], area_unit=self.area_unit)`. The polygon areas are summed up in a loop over the polygons (`with arcpy.da.UpdateCursor(polygon_shp, ”F_AREA”)as cursor: for row in cursor: area += float (row[0])`). The `area` variable contains the usable habitat area for every discharge-related *cHSI* Raster and it is eventually written in column `G` of `CONDITION_FILI.xlsx`.
