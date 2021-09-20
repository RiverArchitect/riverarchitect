Volume Change Assessment
========================

***

- [Introduction](#vaintro)
- [Quick GUIde to terrain assessment](#vaquick)
  * [Main window set-up and run](#vagui)
  * [Reaches](#vasetreaches)
  * [Mapping](#vamap)
  * [Run](#varun)
  * [Output](#vaoutput)
- [Working principle](#vaprin)
- [Code modification: Change sensitivity threshold (lod) for terrain modification detection](#vacode)

***

# Introduction<a name="vaintro"></a>

The *VolumeAssessment* module compares two input DEM Rasters and calculates the volumetric change between both Rasters. The assessment produces workbooks containing reach-wise or project-wise volume differences (excavation and fill), terrain change DEMs, and `pdf`-maps. This chapter explains the module application in the following sections:

 - [Quick Guide](#vaquick) to the application of the GUI with descriptions of input requirements and output descriptions.

 - [Outputs and procedures for pdf-map generation](#vaprin).

 - [Code conventions and extension](#vacode).

Please note that an *ArcGIS Pro* `3D` extension is required for running this module.



# Quick GUIde to Volume Assessment<a name="vaquick"></a>

***

## Main window set-up and run<a name="vagui"></a>

The GUI start-up takes a couple of seconds because the module updates reach information from an external workbook.

![vagui](https://github.com/RiverArchitect/Media/raw/master/images/gui_start_vol.PNG)

To start with the *VolumeAssessment* module, first, select a [reach](RiverReaches). The subdivision of the subsequently selected Rasters can be omitted by select `IGNORE` from the `Reaches` drop-down menu.
Second, select an input DEM Raster (*GeoTIFF*).  Third, select a modified DEM Raster (*GeoTIFF*) that is to be compared with the input DEM Raster.


## Input: Set Reaches<a name="vasetreaches"></a>
For changing [reach definitions](RiverReaches), please refer to the [reach wiki pages](RiverReaches). Keep in mind that changing [reach definitions](RiverReaches) also affects the <a href="LifespanDesign">LifespanDesign</a> and the <a href="ModifyTerrain">Modify Terrain</a> modules.
A particularity of this module is that it enables running analysis for specific river reaches, which can be renamed and the reach extents can be modified. By default, the module analyzes all reaches which are defined in a spreadsheet stored in
`/VolumeAssessment/.templates/computation_extents.xlsx`.

![compextents](https://github.com/RiverArchitect/Media/raw/master/images/computation_extents_illu.jpg)


## Mapping<a name="vamap"></a>

The Run: `Map Maker` uses layout files stored in the *ArcGIS Pro* project file `RiverArchitect/02_Maps/templates/river_template.aprx`. Running `Map Maker` for the first time for a `CONDITION ` will produce a copy of the template project file (`.aprx`) that is stored in `RiverArchitect/02_Maps/CONDITION/map_CONDITION_design.aprx`. Before the running `Map Maker` for the first time for a `CONDITION `, ensure that the background layer points at the good background raster (typically this is `RiverArchitect/01_Conditions/CONDITION/back.tif`) The relevant layout names for the *VolumeAssessment* module are:

 - `volumes_cust_neg` for mapping required excavation (or scour / erosion) of the input DEM to achieve the modified DEM.
 - `volumes_cust_pos` for mapping required fill (or deposition) in the input DEM to achieve the modified DEM.

The *VolumeAssessment* module produces maps with the extents of the input raster by default. Refer to the <a href="Mapping">Mapping</a> wiki for more information on map extents, symbology, and legend modifications.

***

## Run<a name="varun"></a>

The `Run` drop-down menu includes the `Volume Calculator` and the `Map Maker` options. Please note that the `Map Maker` is activated only after the `Volume Calculator` was executed in the current *River Architect* session. Optionally, the bottom checkbox can be activated for automatically running the map creation with the `Volume Calculator`.

***

## Output<a name="vaoutput"></a>

Because the initial state and modified DEM Rasters may be freely selected and not necessarily correspond to a *River Architect* [*Condition*](Signposts#conditions), the *VolumeAssessment* uses **`PSEUDO_CONDITIONS`** that are derived from the directory and name of the modified DEM Raster.

### Rasters<a name="vaoutras"></a>

The module creates terrain change (volume difference) Rasters in the directory `VolumeAssessment/Output/PSEUDO_CONDITION/`). Raster names contain a reach identifier (`r00`, `r01`, \... `r07` corresponding to spreadsheet rows 6--13) when one or several [reaches](#vasetreaches) were selected. Otherwise, the Raster names start with a `"ras"` string. Moreover, the Raster names include an `"exc"` or `"fill"` string to indicate excavation (or scour / erosion) and fill, respectively.

### Maps<a name="vaoutmaps"></a>

The `Map Maker` (or activated checkbox) produces `pdf` maps of volume difference Rasters in `RiverArchitect/02_Maps/PSEUDO_CONDITION/` (map preparation steps are [above described](#vamap) and in the [[Mapping] wiki]). 


### Workbook (spreadsheets)<a name="vaoutspread"></a>

The volumetric differences in m<sup>3</sup> or cubic yards are reach-wise or Raster-wise written to a workbook in the directory `VolumeAssessment/Output/PSEUDO_CONDITION/`, where also the [output Rasters](#vaoutras) are located. The workbook template (`volumes_template.xlsx`) is located in `VolumeAssessment/.templates/` and must not be modified. When *VolumeAssessment* is run for the first time for a `PSEUDO_CONDITION`, it creates a copy of the workbook template, which is called `PSEUDO_CONDITION_volumes.xlsx`. *VolumeAssessment* makes two copies of the `template` sheet for excavation and fill, respectively. Thus, one of the spreadsheet copies is called `excavate_YYYYMMDDHHhMM` and lists the reach-wise / Raster-wise excavation volumes in the chosen unit system. The other spreadsheet copy is called `fill_YYYYMMDDHHhMM` and lists the reach-wise / Raster-wise fill volumes in the chosen unit system. The strings `YYYYMMDD` and `HHhMM` indicate the date and time of the program execution. Repeating runs of *VolumeAssessment* on the same modified DEM will append two more copies (excavate and fill) of the `template` sheet with the date-time indicator. It is recommended to cut-paste `PSEUDO_CONDITION_volumes.xlsx` in a `VolumeAssessment/Products/` directory after every run to keep results well-arranged and to force the module to create a new `PSEUDO_CONDITION_volumes.xlsx` file for every run.

***

# Working principles<a name="vaprin"></a>

The modified DEM (`PSEUDO_CONDITION`) is subtracted from the input DEM to obtain difference DEMs indicating the *dz* differences in elevation. The module uses a level of change detection `lod` of 0.99 ft (or 0.305 m) to avoid the consideration of DEM imprecision because of pixel size-averaging (excavation): `diff_dem_neg = Con(Abs(input_dem - mod_dem)>= lod, Abs(input_dem - mod_dem), 0.0)` (and vice versa for fill).<br/>
The excavation and fill volumes result from `arcpy`'s `SurfaceVolume_3d` function, which requires an *ArcGIS* `3D` extension:<br/>
`volume_excavation = arcpy.SurfaceVolume_3d(diff_dem_neg, "", "ABOVE", 0.0, 1.0)`<br/>
`volume_fill = arcpy.SurfaceVolume_3d(diff_dem_pos, "", "ABOVE", 0.0, 1.0)`<br/>
The `volume_...` variables are stored in a list that is finally written to the [output workbook](#vaoutspread).

***

# Code modification: Change sensitivity threshold (lod) for terrain modification detection<a name="vacode"></a>

The `lod` variable serves for the elimination of virtual terrain differences that may result from pixel sizes and / or Raster transformations (see [above explanations](#vaprin)). The internal variable name for `lod` is `self.volume_threshold` and it is defined in the initiator of the `VolumeAssessment` class (`VolumeAssessment/cVolumeAssessment`). The assigned values of 0.99 ft (U.S. customary) or 0.305 m (SI metric) can be changed in  `class VolumeAssessment()` -> `def __init__(self, ...):` -> `# set unit system` paragraph`:<br/>

```python
  if self.units == "us":
      self.convert_volume_to_cy = 0.037 #ft3 -> cy: float((1/3)**3)
      self.unit_info = " cubic yard"
      self.volume_threshold = 0.99  # ft -- CHANGE lod US customary HERE --
  else:
      self.convert_volume_to_cy = 1.0  # m3
      self.unit_info = " cubic meter"
      self.volume_threshold = 0.30  # m -- CHANGE lod SI metric HERE --

```


[1]: https://github.com/RiverArchitect/RA_wiki/Installation
[2]: https://github.com/RiverArchitect/RA_wiki/Signposts
[3]: https://github.com/RiverArchitect/RA_wiki/LifespanDesign
[4]: https://github.com/RiverArchitect/RA_wiki/MaxLifespan
[5]: https://github.com/RiverArchitect/RA_wiki/VolumeAssessment
[6]: https://github.com/RiverArchitect/RA_wiki/SHArC
[7]: https://github.com/RiverArchitect/RA_wiki/ProjectMaker
[8]: https://github.com/RiverArchitect/RA_wiki/Tools
[9]: https://github.com/RiverArchitect/RA_wiki/FAQ