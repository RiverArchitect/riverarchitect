
[Feature lifespan and design assessment][3]
======================================

***

- [Quick GUIde to lifespan and design mapping][3]
- [Parameter hypotheses](LifespanDesign-parameters)
- [River design and restoration features](River-design-features)
- **Code extension and modification**
  * [Conventions](#conventions)
  * [Order of analysis (hierarchy) and temp (.cache) Raster names](#order)
  * [Add parameters](#addpar)
  * [Add analysis](#addana)
  * [Extend features](#addfeat)

***

# Code extension and modification<a name="code"></a>

The code can be extended with new parameters (e.g., direct shear stress output from the numerical model), new analyses (e.g., a new shear velocity calculation method / law), and features (e.g., another plant species or block ramps).

## Conventions

The Rasters creation results from and functions that are stored in `cLifespanDesignAnalysis.py`. functions create Rasters with lifespan data (0 to 20 years in the sample case) and functions create Rasters with design parameters such as the required stables grain size of angular boulders (rocks).<br/>
Class names start with an upper case letter and do not contain any special characters, also excluding dash or underscore signs. Instantiations of classes are all lower case letters. Features, Parameters, and Analysis classes are stored in separate files called `cFeatureLifespan.py`, `cParameters.py` and `cLifespanDesignAnalysis.py`, respectively. In addition, Feature classes may inherit subfeature classes from files names `cSubfeature.py`, for example, `cPlants.py`.<br/>
Function names consist of lower case letters only and the underscore sign "\_" separates words.<br/>
All class names, variable names, and function names are in alphabetic order (a = up, z = down), except the s, which determine the [parameter run hierarchy](#order).

## Order of analysis (hierarchy) and temp (.cache) Raster names<a name="order"></a>

The best position of restoration features and their lifespans depend on multiple parameters in most cases. The output Rasters (lifespan maps) are computed in by batch-processing every parameter (i.e., one parameter map is processed after another). This batch processing strictly follows the below-listed hierarchy:

1.  Flow depth Rasters (dimensional) starting with the lowest discharge to the highest discharge<br/>
    Internal Raster name: `ras_hQQQQQQ`

2.  Flow velocity Rasters (dimensional) starting with the lowest discharge to the highest discharge<br/>
    Internal Raster name: `ras_uQQQQQQ`

3.  Hydraulic Rasters (dimensionless)<br/>
    Internal Raster name: `ras_taux` (dimensionless bed shear stress) or `ras_Fr` (Froude number); if needed: the hierarchy among the dimensionless hydraulic numbers is not important

4.  Mobile bed, fine sediment, and stable grain size Raster analysis<br/>
    Internal Raster name: `ras_Dcr` (mobile or stable grain size)

5.  Topographic change Rasters<br/>
    Internal Raster names: `ras_fill` (fill Raster only), `ras_scour` (scour only) or `ras_tcd` (combined fill and scour)

6.  Detrended DEM Raster analysis<br/>
    Internal Raster name: `ras_det` (relevant, e.g., for berm setback)

7.  Morphological Unit Rasters<br/>
    Internal Raster name: `ras_mu`

8.  Side channel delineation<br/>
    Internal Raster name: `ras_sch`

9.  Depth to water table<br/>
    Internal Raster name: `ras_d2w` (relevant, e.g., for plantings and terrain grading)

The dimensional hydraulic maps need to be invoked before any other analysis is performed because the *u* and *h* maps are the only ones that entirely cover the area of interest, without "`noData`" pixels.<br/>
Every `feature` has a `feature.parameter_list` attribute containing a list of parameters that determine the feature lifespan and applicability space. The parameters are ordered in the `feature.parameter_list` according to the hierarchy. Once the last element of `feature.parameter_list` is processed and stored in the cache folder, the code exits the loop and copies the last `ras_parameter` to the `Output/Rasters/condition/` folder. This copy is renamed `lf_shortname`, where the usage of [shortnames](River-design-features#introduction-and-feature-groups) is necessary because `arcpy` cannot save or copy Raster with names exceeding 13 characters when GRID Rasters are used (even though the primary Raster type if *GeoTIFF*).

## Add parameters<a name="addpar"></a>

The currently implemented parameters are listed in the [parameters section](LifespanDesign-parameters). New parameters may require new input Rasters in addition to the [default Rasters](Signposts#inpfile). The Rasters need to be saved in the folder `01_Conditions/CONDITION/` using the *GeoTIFF* (or *Esri GRID*) format. Other Raster formats will result in errors when the code attempts to save the final Rasters. The template for creating a new parameter class is shown in the box. Use the following workflow to implement a new parameter in the code:

1.  Create *GeoTIFF* parameter Rasters in the folder `01_Conditions/CONDITION/`.

2.  Add a new parameter class in the file `cParameters.py` (see below explanations).

3.  Add a new function called `analyse_parameter` to the `ArcPyAnalysis` class in the file (see the [add-analysis](#addana) section ) or change existing analysis for using the new parameter.

**Add new parameter class to `cParameters.py`**
  - Replace `EXPRESSIONS` as indicated
  - Write a function in alphabetic order in `cParameters.py`; e.g., the class `Mypar` should be placed below the existing classes `GrainSizes` and `WaterTable`
  - Coding convention: the class name begins with a Capital letter (use CamelCase), where an instance of the class would begin with a small letter

```python
class PARAMETERNAME():
  def __init__(self, condition):
    self.condition=condition  # [str] planning situation, .e.g., "2008"
    self.raster_path='YOUR PATH/01_Conditions/'
    self.raster_names=['RASTER1', 'RASTER2', ..., 'RASTERi', ..., 'RASTERn']
    self.RAS1=arcpy.Raster(self.raster_path+self.condition+'/'+self.raster_names[0])
    self.RAS2=arcpy.Raster(self.raster_path+self.condition+'/'+self.raster_names[1])
    ...
    self.RASi=arcpy.Raster(self.raster_path+self.condition+'/'+self.raster_names[i-1])
    ...
    self.RASn=arcpy.Raster(self.raster_path+self.condition+'/'+self.raster_names[n-1])
```

 
## Add analysis<a name="addana"></a>

The analysis routines are differentiated between and -functions, which are contained in the file `cLifespanDesignAnalysis.py`.<br/>
`analyse_`-functions return Rasters containing estimated survival times (in years) or on/off values (1/0). An `analyse_`-function will always try to find existing Rasters produced from previous analysis functions according to the [analysis hierarchy](#order) unless a dimensional hydraulic analysis (`u`, `h` or their combination) is performed. For this reason, `analyse_`-functions use the `verify_raster_info`-function to look up for previous analyses that are stored in `raster_dict_lf`. At the end of an `analyse_`-function,  `raster_dict_lf` is updated using `raster_dict_lf.update("ras_current")`. This serial Raster analysis produces lifespan Rasters, which can be regardlessly converted to design Rasters by the `save_manager`-function when the feature properties are set to `self.ds = True` while `self.lf = False` (read more about [adding features](#addfeat)).<br/>
`design_`-functions produce Rasters containing specific parameter values, such as the critical grain size in inches. A `design_`-function will update the `raster_dict_ds`-dictionary which is passed to the `save_manager`-function when the feature variable `self.ds = True`.<br/>
The major difference between the `raster_dict_lf` and `raster_dict_ds`-dictionaries is that the `save_manager()` saves only the last hierarchy-based entry of to produced lifespan Rasters but all entries of `raster_dict_ds` to produced design Rasters. The combination of multiple parameters into one design Raster can be achieved anyway by setting `self.ds = True` while `self.lf = False` (see [add features](#addfeat) section). The latter settings convert lifespan Rasters to design
Rasters.<br/>
Use the following workflow to implement a new parameter in the code:

1.  Ensure that all required parameters are available (see the [parameter list](LifespanDesign-parameters) and [Add parameters section](#addpar)).

2.  Create an identifier string of 2 to 3 characters; the following explanations refer to a dummy identifier named `NEW` (replace with lowercase letters).

3.  Add a new `analyse_NEW` or `design_NEW`-function in the file `cLifespanDesignAnalysis.py` (cf. code example below).

4.  In `cFeatureLifespan.py` ensure that concerned features have the
    following properties:

    -   The `feature.paramter_list` needs to contain the new analysis' identifier (`NEW`)

    -   All required threshold values are defined (`feature.threshold_NEW1 = ...`)

5.  In `featureanalysis.py`, add a call of the new function:

```python
	  if parameter_name == "NEW":
	    feature_analysis.analyse_NEW(feature.threshold_NEW1, ... )
```  

 
The template for a new `analyse_NEW`-function in the file `cLifespanDesignAnalysis.py` starts with the general statement of unit conversion (controlled by user input) and continues as follows (pay attention on indentation):

```python
 def analyse_NEW(self, threshold_NEW1, ...):
     # Lines where changes are required are tagged with #--CHANGE--#
     # Convert length units of threshold values
     threshold_LENGTH = threshold_LENGTH * self.ft2m     #--CHANGE--#
     try:
      arcpy.CheckOutExtension('Spatial')  # check out license
      arcpy.gp.overwriteOutput = True
      arcpy.env.workspace = self.cache
      self.logger.info("      >>> Analyzing NEW.") #--CHANGE--#
      parameter1 = PARAMETER1(self.condition)      #--CHANGE--#
      parameter2 = PARAMETER2(self.condition)      #--CHANGE--#
      ...                                          #--CHANGE--#
      self.ras_NEW = calculation with parameter1, parameter2, ... threshold_NEW1, ...   #--CHANGE--#
      self.ras_LF = self.compare_raster_set(parameter_ras, threshold)
      # verify existing analyses
      if self.verify_raster_info():
          self.logger.info("            based on raster: " + self.raster_info_lf)
          # make temp_ras without noData pixels
          temp_ras_NEW = Con((IsNull(self.ras_NEW) == 1), (IsNull(self.ras_NEW) * some_factor), self.ras_NEW) #--CHANGE--#
          # compare temp_ras with raster_dict but use self.ras_... values if condition is True
          ras_NEW_update = Con((temp_ras_NEW == 1), self.ras_NEW, self.raster_dict_lf[self.raster_info_lf])   #--CHANGE--#
          self.ras_NEW = ras_NEW_update   #--CHANGE--#
      # update lf dictionary
      self.raster_info_lf = "ras_NEW"     #--CHANGE--#
      self.raster_dict_lf.update({self.raster_info_lf: self.raster_info_lf}) 
      arcpy.CheckInExtension('Spatial')
     except arcpy.ExecuteError:
        self.logger.info("ExecuteERROR: (arcpy) in NEW analysis.")    #--CHANGE--#
        self.logger.info(arcpy.GetMessages(2))
        arcpy.AddError(arcpy.GetMessages(2))
     except Exception as e:
        self.logger.info("ExceptionERROR: (arcpy) in NEW analysis.")  #--CHANGE--#
        self.logger.info(e.args[0])
        arcpy.AddError(e.args[0])
     except:
        self.logger.info("ERROR: (arcpy) in NEW analysis.")           #--CHANGE--#
        self.logger.info(arcpy.GetMessages())
```

The template for a new -function in the file `cLifespanDesignAnalysis.py` is as follows (pay attention on indentation):

```python
 def design_NEW(self, threshold_NEW1, ...):
     # Lines where changes are required are tagged with #--CHANGE--#
     try:
      arcpy.CheckOutExtension('Spatial')  # check out license
      arcpy.gp.overwriteOutput = True
      arcpy.env.workspace = self.cache
      self.logger.info("      >>> Designing NEW.") #--CHANGE--#
      parameter1 = PARAMETER1(self.condition)      #--CHANGE--#
      parameter2 = PARAMETER2(self.condition)      #--CHANGE--#
      ...                                          #--CHANGE--#
      self.ras_NEW1 = calculation with parameter1, parameter2, ... threshold_NEW1, ...  #--CHANGE--#
      ## if required add more design rasters (all need to be added to self.raster_dict_ds)
      self.ras_NEWi = another (optional) calculation with parameter1, parameter2, ... threshold_NEW1, ... #--CHANGE--#

      # update ds dictionary
      self.raster_dict_ds.update({self.raster_info_lf: self.ras_NEW1}) #--CHANGE--#
      # if required uncomment:
      # self.raster_dict_ds.update({self.raster_info_lf: self.ras_NEWi}) #--CHANGE--#

      arcpy.CheckInExtension('Spatial')

     except arcpy.ExecuteError:
        self.logger.info("ExecuteERROR: (arcpy) in NEW design.")    #--CHANGE--#
        self.logger.info(arcpy.GetMessages(2))
        arcpy.AddError(arcpy.GetMessages(2))
     except Exception as e:
        self.logger.info("ExceptionERROR: (arcpy) in NEW design.")  #--CHANGE--#
        self.logger.info(e.args[0])
        arcpy.AddError(e.args[0])
     except:
        self.logger.info("ERROR: (arcpy) in NEW design.")           #--CHANGE--#
        self.logger.info(arcpy.GetMessages())
```  


 
## Extend features<a name="addfeat"></a>

The currently implemented features are listed in the [Features](River-design-features) page. New features can be implemented in the `cFeatureLifespan.py` file using the following workflow:

1.  Ensure that all required parameters are available (see the [parameter list](LifespanDesign-parameters) and [Add parameters section](#addpar)).

2.  Ensure that all required analysis and / or design functions are available (see [Add analyses](#addana)).

3.  Choose a name for the new feature beginning with an uppercase letter followed by lowercase letters only; the name `NewFeature` is subsequently used for illustrative purposes

4.  In `cFeatureLifespan.py` modify the `class RestorationFeature`:
    -   Implement the new feature instantiation when called by adding the following code to `def __init__(self, feature_name, ∗sub_feature )`:

	`if feature_name == "NewFeature" and not(sub_feature):`<br/>
	`     self.feature = NewFeature()`<br/>
	`     self.sub = False`<br/>
	`     self.name = feature_name`


    -   Please note: the shortname should not have more than 6 characters; otherwise the code will cutoff the shortname
        automatically.

    -   Both the `__init__(self)` initiation and the `NewFeature` instantiation are necessary to facilitate the external access to Methods and Properties.

    -   A feature may have subfeatures (as for example `class Plantings`). In this case, replace `and not(sub_feature)` with `and sub_feature` and set `self.sub = True`.

    Add a new class to `cFeatureLifespan.py` according to the example below, considering the required hierarchically ordered `self.parameter_list`, `self.threshold_` and lifespan `(self.lf=True/False)` / design `(self.ds=True/False)` Raster analysis properties.

5.  Add new column in `LifespanDesign/.templates/threshold_values.xlsx` and add the feature name as well as relevant threshold values.

6.  Commit changes in `RiverArchitect/ModifyTerrain/cDefinitions.py` :

    -   Append the shortname to `self.id_list = ["backwt", "widen", "grade", "sideca", "sidech", "elj", "fines", "box", "cot", "whi", "wil", "rocks", "gravin", "gravou", "cust"]`

    -   Append full feature name to `self.name_ _list = ["Backwater", "Bermsetback (Widen)", "Grading", "Sidecavity", "Sidechannel", "Streamwood", "Finesediment", "Plantings: Box Elder", "Plantings: Cottonwood", "Plantings : White Alder", "Plantings: Willows", "Boulders/rocks", "Gravel replenishment", "Gravel stockpile ", "Custom DEM"]`

    -   Append feature threshold column (`thresholdvalues.xlsx`) name in  `self.threshold_cols = ["E", "Q", "G", "O", "P", "R", "F", "J", "K", "L", "M", "N", "H", "I", "S"]`

 
The template for a new `NewFeature`-class in the file `cFeatureLifespan.py` is as follows (pay attention on indentation), given that no subfeatures apply:

```python
class Newfeature():
  # This is the Newfeature class.
  def __init__(self):
      self.ds = False # identify if design map applies
      self.lf = True  # identify if lifespan map applies
      self.parameter_list = ["PAR1", "PAR2", ..., "PARi", , "PARn"] # Respect Hierarchy -- example: PAR1 = "hyd"
      self.shortname = "max6ch"
      thresh = ThresholdDirector(self.shortname) # instantiate reader of threshold values
      ## uncomment and adapt follow line if PAR = mu applies
      # self.mu_bad = thresh.get_thresh_value("mu_bad") 
      # self.mu_good = thresh.get_thresh_value("mu_good") 
      # self.mu_method = thresh.get_thresh_value("mu_method")
      self.threshold_1 = thresh.get_thresh_value("ID_1")
      self.threshold_2 = thresh.get_thresh_value("ID_2")
      ...
      self.threshold_i = thresh.get_thresh_value("ID_i")
      ...
      self.threshold_n = thresh.get_thresh_value("ID_n")
      thresh.close_wb() # close threshold workbook
  def __call__(self):
      pass
```  

Valid `ID_i` strings are either string of: `"mu bad", "mu good", "mu method","D", "d2w low", "d2w up", "det low", "det up", "fill", "Fr", "freq", "h", "inverse_tcd ", "scour", "sf", "taux", "u"`. The `get_thresh_value("ID_i")` -function is a routine of the `ThresholdDirector` class which is stored in `LifespanDesign/cThresholdDirector.py`. Modifications of the `ThresholdDirector` class are deprecated and threshold values should be modified in the spreadsheet [`LifespanDesign/.templates/threshold_values.xlsx`](LifespanDesign#modthresh).

 
If the new feature has subfeatures, the following template applies:

```python
class NewFeature(Subfeature_1, Subfeature_2, ..., Subfeature_i, ... Subfeature_n):
  # This is the NewFeature class inheriting from Subfeature_1 to Subfeature_n.
  def __init__(self, subfeature):
      self.lf = True  # identify if lifespan map applies
      self.ds = False # identify if design map applies
      if subfeature == 'subfeature_1':
          Subfeature_1.__init__(self)
      if subfeature == 'subfeature_2':
          Subfeature_2.__init__(self)
      if subfeature == 'subfeature_i':
          Subfeature_i.__init__(self)
      if subfeature == 'subfeature_n':
          Subfeature_n.__init__(self)
  def __call__(self):
      pass
```  

Then, the subfeature needs to be defined (e.g., in an external file called `cNewSubFeature.py`). In this case, add `from cNewSub
Feature import ∗` at the top of `cFeatureLifespan.py`. Use the following class-template for each subfeature(`SubFeature_1,..., SubFeature_n`). Please note that the lifespan `self.lf = True / False` and design `self.ds = True / False` properties are already assigned in the inheriting feature class.

```python
class NewSubFeature_i():
  # This is the NewSubFeature_i class.
  def __init__(self):
      self.parameter_list = ["PAR1", "PAR2", ..., "PARi", , "PARn"] # Respect Hierarchy!; example: PAR1 = "hyd"
      self.shortname = "max6ch"
      thresh = ThresholdDirector(self.shortname) # instantiate reader of threshold values
      ## uncomment and adapt follow line if PAR = mu applies
      # self.mu_bad = thresh.get_thresh_value("mu_bad") 
      # self.mu_good = thresh.get_thresh_value("mu_good") 
      # self.mu_method = thresh.get_thresh_value("mu_method")
      self.threshold_1 = thresh.get_thresh_value("ID_1")
      self.threshold_2 = thresh.get_thresh_value("ID_2")
      ...
      self.threshold_i = thresh.get_thresh_value("ID_i")
      ...
      self.threshold_n = thresh.get_thresh_value("ID_n")
      thresh.close_wb() # close threshold workbook
  def __call__(self):
      pass
```  

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