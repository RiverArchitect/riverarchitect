# River Architect Tools

*Tool* scripts can be considered as beta versions of future functionalities that will be implemented in *River Architect*. Typically, *Tools* are basic commandline scripts for creative design support. Currently, routines for the hydraulic design of pool-riffle sequences or flood analysis are available, where the flood analysis applies to the U.S. Army Corps of Engineers' [`HEC-SPP`][hecspp] software. The *Tools* routines are located in `RiverArchitect/Tools/`. 

***

# Main Tool scripts

Run the following scripts with Esri's *Python* environment ([read more](Installation.md#raenv))

 - `make_annualpeak.py` prepares required input data for statistic flow analyses and with the U.S. Army Corps of Engineers' [`HEC-SPP`][hecspp] software.

 - `make_flowduration.py` creates flow duration curves (annual averages) for the assessment of AUA.

 - `morphologydesigner.py` creates design tables for self-sustaining pool-riffle channels (uses `cHydraulic.py` and `cPoolRiffle.py`).
 
 - `rename_files.py` facilitates renaming input files for conditions according to [raster file name conventions](Signposts.md#nameconvention) by adding, removing or replacing a file name prefix and suffix.<a name="renamefiles"></a>

 - `run_make_….bat` are a batchfiles that run `make_….py` on Windows x64.

 - `run_morphology_designer.bat` is a batchfiles that runs `morphology_designer.py` on Windows x64.


# Class and Function files

The code execution depends on the following folders and scripts:

 - `.templates` folder contains a template workbooks for multiple purposes.

 - `Products` folder contains results of any script in this folder.

 - `cHydraulic.py` contains a class with routines for calculating cross-section-averaged flow characteristics.

 - `cInputOutput.py` contains classes required for reading and writing data, as well as calculation progress logging.

 - `cPoolRiffle.py` provides routines for designing self-sustaining pool-riffle channels.

 - `fTools.py` is a set of functions used by other Python applications within this folder.


[1]: Installation.md
[2]: Signposts.md
[3]: LifespanDesign.md
[4]: MaxLifespan.md
[5]: ModifyTerrain.md
[6]: https://github.com/RiverArchitect/RA_wiki/HabitatEvaluation
[7]: ProjectMaker.md
[8]: Tools.md
[9]: FAQ.md
[10]: Troubleshooting.md

[wyrick14]: https://www.sciencedirect.com/science/article/pii/S0169555X14000099
[hecspp]: https://www.hec.usace.army.mil/software/hec-ssp/