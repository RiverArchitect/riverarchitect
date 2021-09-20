The to-do list for developers
===========

To edit this list, please clone the Wiki ([see descriptions](DevGit)) and follow the [Wiki writing instructions](DevWiki). More issues regarding the application of *River Architect* are listed in the [Troubslehooting Wiki](Troubleshooting#issues). Please update this [*Known issues* list ](Troubleshooting#issues) for users, too, once a problem is fixed.

### Minor future tasks (max. one day of work each) <a name="min"></a>

- General
	1. Change Error and Warning message logging from `logger.info()` to `logger.error()` and `logger.warning()` statements.

- [Lifespan](LifespanDesign)
	1. Mapping (PDF export) of lifespan maps does not work in many cases for several potential reasons: Definition of zoonm coordinates, automated layout selection, and visibility of layers (issues located in code lines `220` to `225` of `/.site_packages/riverpy/cMapper.py`). Sometimes it works anyway. Because PDF export is not a core function of *River Architect*, the PDF export problem had a low priority in the development, but should be fixed in the future.


- [Project Maker](ProjectMaker)
	1. [**Project Maker**](ProjectMaker#pmplants) places plant species in alphabeticaly order when several plant species have the same maximum lifespan at a pixel. However, users should have the option to define the order in which plant species are placed. A drop-down menu or pop-up window call (button?) in the *Project Maker* GUI (`ProjectMaker/project_maker_gui.py`, somewhere between `row=9` and `row=13`) should be implemented to enable the user selection. Moreover, an adaptation will be required in `ProjectMaker/s20_plantings_delineation.py` between lines 96 to 158 (approximately); currently, the automated hierarchical order is enforced by storing pixels, which are already assigned to a plant species, in an `arcpy.Raster()` instance called `occupied_px_ras` (first instantiation is `str()`). `occupied_px_ras` is overwritten (updated) in every loop between lines 115 and 120 (approximately).

	

### Major future tasks for *River Architect* development <a name="maj"></a>

- Add a *Load User Settings* options ([see below](#usrstgs))
- Resolve `arcpy` dependencies (move to *QGIS* and [`gdal`](https://gdal.org))
- Update and test [`River Builder`](RiverBuilder) implementation
- Couple with 2D numerical models
- Metadata:
	1. Enable to append project metadata (including baseline, budget, socio-economic context and stakeholder)
	1. Integrate metadata output in common formats (primary: [Ecological Metadata Language - EML](http://www.dcc.ac.uk/resources/metadata-standards/eml-ecological-metadata-language) format)


### User requests and issues <a name="usr"></a>

Bugs or development requests from user undergo the following steps: (1) Reception (**"Received"**), (2) **"Discussion"** of implementation (developers and users), (3) **"Implementation"**(developers), and (4) push changes (final state: **"Implemented"**). The following issues and requests were reported by users:
<!--- Please only use the following Implementation progress notes: Received / Discussion / Implementation / Implemented -->
<!--- Received requests are in the User Requests folder of our river.architect.program A gmail.com email account -->


| Description | Source | Implementation progress |
|-------------|--------|-------------------------|
| Turn threshold values of features into threshold functions| J. W. | Received | 


# DETAILED PROBLEM DESCRIPTIONS
***

## User settings  <a name="usrstgs"></a>
***

A user settings load function may use a text file to enable the following user definitions (provided by [sierrajphillips](https://github.com/sierrajphillips)):

[Lifespan Design](LifespanDesign)
- Note if wildcard raster and/or habitat matching was applied
- Record Manning's n that user input
- Note if computation extent was limited to boundary.tif

[Max Lifespan](MaxLifespan)
- Record if lifespan raster extent or an extent raster was used

[SHArC](SHArC)
- Record if calculation boundary shapefile was used
- Record which HSI combination method was used: geometric or product
- Record what SHArea threshold user input (CHSI = ?)
- For Q - Area Analysis - which flow duration curve was used?

[Stranding Risk](StrandingRisk)
- Record what Q-high and Q_low input by user
- Record which interpolation method was selected

[Project Maker](ProjectMaker)
- Record the three user inputs for lifespan (years)
- Record stability drivers set by user (Manning's n and Shields parameter)

***
