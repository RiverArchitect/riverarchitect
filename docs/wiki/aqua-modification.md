SHArC - Code modification
=========================

***

- [Introduction to Habitat Suitability evaluation](SHArC#heintro)
- [Quick GUIde to habitat suitability evaluation](SHArC#hequick)
  * [Main window set-up and run](SHArC#hegui)
  * [Input: Physical Habitats and Fish](SHArC#hefish)
  * [Input: Combine methods (of habitat suitability Rasters)](SHArC#hecombine)
  * [Input: Define computation boundaries](SHArC#hebound)
  * [Input: HHSI](SHArC#hemakehsi)
  * [Input: Cover HSI](SHArC#hemakecovhsi)
  * [Combine habitat suitability Rasters](SHArC#herunchsi)
  * [Calculate SHArea](SHArC#herunSHArea)
  * [Output and application in river restoration projects](SHArC#heoutput)
  * [Quit module and logfile](SHArC#hequit)
- [Working principles](SHArC-working-principles#heprin)
  * [Cover HSI: Substrate](SHArC-working-principles#subshsi)
  * [Cover HSI: Boulder](SHArC-working-principles#bouhsi)
  * [Cover HSI: Cobble](SHArC-working-principles#cobhsi)
  * [Cover HSI: Streamwood](SHArC-working-principles#woohsi)
  * [Cover HSI: Vegetation](SHArC-working-principles#veghsi)
  * [Cover HSI combination methods](SHArC-working-principles#hecombinecov)
  * [Usable habitat area calculation](SHArC-working-principles#hewuamethods)
- **More about Physical Habitats and Modifying `Fish.xlsx`**


***

# Fish species and lifestages
See [input defintions](SHArC#hefish).

# Changing the structure of `Fish.xlsx`<a name="hecode"></a>

The `Fish.xlsx` workbook is read by the `Fish` class stored in `RiverArchitect/.site_packages/riverpy/cFish.py`. The start rows for reading velocity, depth, substrate, mineral cover and vegetation cover habitat suitability curves from the workbook are hard-coded in the `self.parameter_rows` dictionary of the `Fish` class. If rows were deleted or inserted, `self.parameter_rows` needs to be adapted.

-   `"u": row - row` needs to correspond to the row number where the flow velocity-related habitat suitability curve starts.

-   `"h": row - row` needs to correspond to the row number where the flow depth-related habitat suitability curve starts.

-   `"substrate": row - row` needs to correspond to the row number where the substrate-related (*D*) habitat suitability curve starts.

-   `"cov_min": row - row` needs to correspond to the row number where the mineral cover (cobbles and boulders)-related habitat suitability curve starts.

-   `"cov_veg": row - row` needs to correspond to the row number where the vegetation cover (plants and wood)-related habitat suitability curve starts.

The insertion or deletion of rows can be easily and robustly adapted by changing the above dictionary items. However, changing or deleting columns is more complex because the module is coded in a manner that it can theoretically read an infinite number of fish species, but always limited to the same number of lifestages.
Preferably omit non-relevant lifestages (do not put any number). Otherwise, change the code where read columns are relative incremental increases of numeric column values, starting at `self.species_row = 2`. For example, the `"spawning"` lifestage is at first place, and therefore, its relative column is `1`. The `"fry"` lifestage is in second place but it needs to jump over an extra column. Therefore, the relative column of `"fry"` is `3`, the relative column of `"juvenile"` is `5`, and the relative column of `"adult"` is `7`. If another lifestage is used for any fish species, it needs to match one of the before mentioned stored in the `self.ls_col_add` dictionary of the `Fish` class. For example, the base scenario uses *Lamprey* fish and an `"ammocoetes"` lifestage instead of `"fry"`. Therefore, the entry `{"ammocoetes": 3}` needs to be added to `self.ls_col_add`.
Currently, the following lifestages can be recognized: `self.ls_col_add = {"spawning": 1, "fry": 3, "ammocoetes": 3, "juvenile": 5, "adult": 7, "hydrologic year": 1, "season": 3, "depth > x": 5, "velocity > x": 7}`.
*The hard-coded lifestage identification represents a [known issue](Troubleshooting#issues) and we are working on improving the freedom in naming lifestages.*

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