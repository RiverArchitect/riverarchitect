# <a name="define"></a>River Reach Definitions<a name="introsetreaches">

Particular rivers or reaches for the analysis can be defined from the [*LifespanDesign*][3], [*VolumeAssessment*][51] and [*ModifyTerrain*][5] modules, referring to:<br/>
`ModifyTerrain/.templates/computation_extents.xlsx`<br/>
The concerned modules provide options for reach differentiation and limit calculations to defined particular reaches. These limitations are automatically used by the other modules.
This subdivision of the computation domain enables the analysis of up to eight reaches per copy of *River Architect*. The below figure illustrates the workbook spreadsheet for reach delineation.
Changes can be effected by clicking on the `Reaches` dropdown menu and then `DEFINE REACHES`, or directly in the folder `ModifyTerrain/.templates/`. **In order to ignore any reach definitions, select `IGNORE (use Raster extents)`.**

![reache](https://github.com/RiverArchitect/Media/raw/master/images/computation_extents_illu.jpg)

If the workbook is accidentally deleted or irreparable, incorrect modifications were made, there is an offline backup copy available:<br/>
`ModifyTerrain/.templates/computation_extents - Copy.xlsx`

`ModifyTerrain/.templates/computation_extents.xlsx` can be opened, for example, by clicking on the `Reaches` drop-down menu ([*ModifyTerrain*][5] module) and then "`DEFINE REACHES`".
The extents need to correspond to the input DEM coordinate and unit system types (e.g., a georeference may be *GRS\_1980\_Lambert\_Conformal\_Conic* with the linear unit of *Foot\_US*). If the reaches 00 to 07 align from the East to the West, the `Max x` value of a reach corresponds to the `Min x` value of the next upstream reach. If a reach is situated in the south of its upstream reach, its `Max y` value corresponds to the `Min y` value of the upstream reach. Such gap-less transitions enable consistent mapping of DEM differences and excavation/fill volume calculations.<br/>
After editing, saving and closing the spreadsheet, the GUI window can be updated by clicking on the `Reaches` drop-down menu and then "`RE-BUILD MENU`". Whatever name is stored in the workbook, *River Architect* uses internal identifiers that point at the rows in the spreadsheet, and therefore, output rasters are enumerated with tags `r00`, `r01`, ... `r07`.<br/>
All reaches can be deselected by clicking on "`CLEAR ALL`" to add particular reaches only. If more than five reaches are selected, the GUI truncates the list and displays `Many / All`.

The code handlers for reaches are part of `riverpy` (`RiverArchitect/.site_packages/riverpy/`). The `Reaches` class in `cDefinitions.py` flexibly sends reach information to all modules and reads reach information using the `Read` class in `cReachManager.py`. The dictionaries and lists of the `Reaches` class include an additional entry called `"none": "none"` / `"Raster extents"` to enable reach-independent analyses.


[1]: https://github.com/RiverArchitect/RA_wiki/Installation
[2]: https://github.com/RiverArchitect/RA_wiki/Signposts
[3]: https://github.com/RiverArchitect/RA_wiki/LifespanDesign
[4]: https://github.com/RiverArchitect/RA_wiki/MaxLifespan
[5]: https://github.com/RiverArchitect/RA_wiki/ModifyTerrain
[51]: https://github.com/RiverArchitect/RA_wiki/VolumeAssessment
[6]: https://github.com/RiverArchitect/RA_wiki/SHArC
[7]: https://github.com/RiverArchitect/RA_wiki/ProjectMaker
[8]: https://github.com/RiverArchitect/RA_wiki/Tools
[9]: https://github.com/RiverArchitect/RA_wiki/FAQ
[10]: https://github.com/RiverArchitect/RA_wiki/Troubleshooting