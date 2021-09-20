[Feature lifespan and design assessment][3]
======================================

***

- [Quick GUIde to lifespan and design maps][3]
- [Parameter hypotheses](LifespanDesign-parameters)
- **River design and restoration features**
  * [Introduction and predefined features](#featoverview)
  * [Feature-wise lifespan and design maps](#lffeats)
  * [Details and parameters of pre-defined features](#feat)
    + [Angular boulders (rocks) and grain mobility](#rocks)
    + [Backwater](#backwtr)
    + [Nature-based engineering](#bioeng)
    + [Berm Setback / Widen](#berms)
    + [Streamwood and Engineered Log Jams](#elj)
    + [Fine sediment](#finesed)
    + [Grading](#grading)
    + [Vegetation Plantings](#plants)
    + [Sediment replenishment / gravel augmentation](#gravel)
    + [Side cavities](#sidecav)
    + [Side channels / anabranches](#sidechnl)
  * [Instructions for defining new and modifying existing features](#modfeat)
- [Code extension and modification](LifespanDesign-code)

***
# Introduction and Feature Groups<a name="featoverview"></a>

The *River Architect* differentiates between feature layers that actively modify the terrain (terraforming features), vegetation plantings features as well as nature-based engineering features that provide direct aid for habitat enhancement or stabilize terrain modifications, and features that maintain artificially created habitat or support longitudinal connectivity. Feature attributes can be modified in the thresholds workbook (`RiverArchitect/LifespanDesign/.templates/threshold_values.xlsx`), which can also be open from the GUI:

![thresholds](https://github.com/RiverArchitect/Media/raw/master/images/threshold_values_illu.png)

Changes in this workbook should limit to cells with `INPUT`-type formatting and only `Feature Names` and `Feature ID`s of vegetation plantings should be modified. Other modifications may cause calculation instabilities or program crashes. The following list provides an overview of default features, where *Feature ID*s occur in output file names of Rasters, layouts, PDF-maps, and spreadsheets and plantings

-   **Terraforming features** modify the terrain elevation:
    -   Backwater, representative for swale and slackwater creation (*Feature ID: backwt*)
    -   Berm Setback (Widening, *Feature ID: widen*)
    -   Grading of terrain (Bar and Floodplain Lowering *Feature ID: grade*)
    -   Side Cavities (Bank Scalloping or Groins, *Feature ID: sideca*)
    -   Side Channels, representative for Anabranches, Multithread- or Anastomosed Channels and Flood Runners (*Feature ID: sidech*)
	
-   **Plantings features** include up to four plant species. The pre-defined plant species are ([can be modified](#modfeat), except for the fields that are marked for input in the thresholds workbook):
    -   Box Elder (*Acer Negundo*, *Feature ID: box*)
    -   (Fremont) Cottonwood (*Populus Fremontii*, *Feature ID: cot*)
    -   White Alder (*Alnus Rhombifolia*, *Feature ID: whi*)
    -   Willows (*Salix Goodingii / laevigata / lasiolepis / alba*, *Feature ID: wil*)

-   **Other nature-based engineering features** have a direct effect on habitat suitability and stabilize terrain modifications (framework features). These features are considered:
    -   Streamwood, engineered log jams (ELJ) and large woody material (LWM) placement including rootstocks (*Feature ID: elj*)
    -   Grains / Boulders (angular), representative for coarse material placement (*Feature ID: grains*)
    -   Other nature-based engineering for terrain (slope) stabilization comprises for instance brush layers and/or fascines (*Feature ID: bio*)

-   **Connectivity features** enhance the stability of (artificial) river systems that result from the above feature applications:
    -   Sediment Replenishment for restoring sediment continuity (instream, *Feature ID: gravin*)
    -   Stockpiles of gravel or Gravel Augmentation  for restoring sediment continuity(on banks or floodplain, *Feature ID: gravou*)
    -   Incorporation of Fine Sediment in soils to increase the survivorship of plantings (*Feature ID: fines*)   
    -   Flow controls are only indirectly considered in the [*SHArC*][6] module, where discharges drive habitat suitability
    -   Dam removal and the removal of other lateral barriers (e.g., ground sills) are currently not considered in *River Architect*

In addition, the *River Architect* provides the option of limiting restoration feature maps to zones of low habitat suitability (see details in the descriptions of the [*SHArC*][6] module).

## Feature-wise lifespan and design maps<a name="lffeats"></a>

The [Lifespan & Design][3] tab enables the creation of lifespan and design maps of the features defined in the `threshold_values.xlsx` workbook. The names of lifespan and design maps start with either **`lf_`** for **Lifespan Maps** or **`ds_`** for **Design Maps**, followed by the **Feature ID** defined in the `threshold_values.xlsx` workbook. **Design Maps** additionally include a string of the parameter that they define (e.g. `_Dst_` contains stable grain size diameters and `_Dw_` contains stable wood log diameters referring to a user-defined flood frequency). Thus, typical names are:

-	**Lifespan Maps**: **`lf_FeatureID.tif`**
-	**Design Maps**: **`ds_PARAMETER_FeatureID.tif`**

Moerover, lifespan and design map Rasters are saved in different layer folders, depending on the feature groups, with the following guidelines:

- 	**TERRAFORMING** (`threshold_values.xlsx` Columns `E`-`I`): `.../RiverArchitect/LifespanDesign/Output/Rasters/CONDITION_lyr10/lf_fID.tif --ds_PAR_fID.tif`
- 	**VEGETATION PLANTINGS** (`threshold_values.xlsx` Columns `J`-`M`): `.../RiverArchitect/LifespanDesign/Output/Rasters/CONDITION_lyr20/lf_fID.tif`
- 	**NATURE-BASED ENGINEERING FEATURES** (`threshold_values.xlsx` Columns `N`-`P`): `.../RiverArchitect/LifespanDesign/Output/Rasters/CONDITION_lyr20/lf_fID.tif --ds_PAR_fID.tif`
- 	**CONNECTIVITY** (`threshold_values.xlsx` Columns `Q`-`S`): `.../RiverArchitect/LifespanDesign/Output/Rasters/CONDITION_lyr30/lf_fID.tif --ds_PAR_fID.tif`

***

# Pre-defined features and hypotheses<a name="feat"></a>

The standard installation of *River Architect* comes with a set of pre-defined river design features (cf. [Schwindt et al. 2019][schwindt19]). For topographic change, scour and fill rates are considered over a 3-year observation period (2008 to 2014, see [Weber and Pasternack 2017][weber17]). The following hypotheses apply to the pre-defined features.

## Grains, Grain Mobility, and Angular boulders<a name="rocks"></a>

The mobile grain size or the necessary size for the punctual placing of boulders and comprehensive rock cover is referred to as "Grains/Boulders" in the default [`threshold_values.xlsx` workbook](#featoverview). Such information is necessary, for example, to stabilize banks or erosion-prone surfaces (e.g., [Maynord and Neill 2008][maynord08]). Lifespan maps of the mobility of the present terrain refer to the present grain size (`.../01_Conditions/CONDITION/dmean.tif`). The required minimum diameter for boulders or mobile grains results from the spatial evaluation of *D<sub>cr</sub>* on mobile grain design maps.

Recommended threshold values in the [`threshold_values.xlsx` workbook](#featoverview) are:

-   Critical dimensionless bed shear stress `taux` of *&tau;<sub>\*,cr</sub>* equal to 0.047 (dimensionless);
-   Topographic change: scour rate `tcd`-`scour` (optional) of 0.3 m (1 ft) multiplied with the number of observation years (if a topographic change raster includes scour/fill observed over multiple years);
-	Frequency threshold for design maps (e.g., 20 years);
- 	Dimensionless safety factor `SF` for design maps.

The [Lifespan & Design][3] tab enables the creation of:

-	**Lifespan Maps** with output Raster name: `.../LifespanDesign/Output/Rasters/CONDITION_lyr20/lf_grains.tif`; and
-	**Design Maps** with output Raster name: `.../LifespanDesign/Output/Rasters/CONDITION_lyr20/ds_Dst_grains.tif` in *m* or *inches*, which is a derivative of the Gauckler-Manning-Strickler formula using [Manning\'s *n*][manningsn]:<br/>
    *D<sub>cr</sub>* =  *SF* *· u<sup>2</sup> · n<sup>2</sup>* / *\[(s - 1) · h<sup>1/3</sup> · &tau;<sub>\*,cr</sub> \]* <br/>

*D<sub>cr</sub>* is the minimum required angular boulders (rocks) size (in m or inches); *s* is the dimensionless relative grain density (ratio of sediment and water density, equal to 2.68); and *n* is [Manning\'s *n*][manningsn] can be changed in the GUI (in s/ft<sup>1/3</sup> or s/m<sup>1/3</sup> - an internal conversion factor of k = 1.49 applies in the case of the US customary system). The following parameters are taken from `.../01_Conditions/CONDITION/` input *GeoTIFF*s
- *h* is the flow depth (pixel-wise, in m or ft);
- *u* is the flow velocity (pixel-wise, in m/s or fps).

**NOTE**: Lifespan and Design Rasters of mobile grains are **sensitive to the safety factor** and limitations due to **scour/fill** rates input Rasters (possibly not covering the whole project area). Verify output Rasters and omit scour/fill rates and/or the safety factor to obtain better results.


## Backwater<a name="backwtr"></a>

The creation of artificial backwaters and swales, or more generally calm water zones, makes sense where the stream power is low and the observed topographic changes are small. Recommended threshold values in the [`threshold_values.xlsx` workbook](#featoverview) are:

-   Flow velocity `u` of 0.03 m/s (0.1 fps);
-   Frequency threshold (design maps) of 5 years;
-   Critical dimensionless bed shear stress `taux` with a threshold of *&tau;<sub>\*,cr</sub>* threshold of 0.047.
-   Topographic change: fill & scour rates (`tcd`-`scour`-`fill`) of >= 0.1 m (0.3 ft) multiplied with the number of observation years (if a topographic change raster includes scour/fill observed over multiple years).
-   Morphological Units (relevance-method) with `mu_relevance = ["agriplain", "backswamp", "mining pit", "pond", "pool", "slackwater", "swale"].`

The [Lifespan & Design][3] tab enables the creation of:

-	**Lifespan Maps** with output Raster name: `.../LifespanDesign/Output/Rasters/CONDITION_lyr10/lf_backwt.tif`; and
-	**Design Maps** with output Raster name: `.../LifespanDesign/Output/Rasters/CONDITION_lyr10/ds_Dst_backwt.tif`.

## Nature-based engineering (Other) <a name="bioeng"></a>

In the context of river engineering, nature-based methods apply living materials (plants) to stabilize terrain and enhance habitat. Please note that *River Architect* internally uses the shortnames `"bioengineering"` or `"bioeng"` when referring to nature-based engineering features. Dry conditions in arid and semi-arid (Mediterranean) climate zones limits the possibilities of application. Therefore, *River Architect* additionally considers the placement of angular boulders (see [angular boulders](#rocks)). Recommended threshold values in the [`threshold_values.xlsx` workbook](#featoverview) are:

-   Depth to groundwater `d2w` with minimum and maximum values as a function of vegetation plantings requirements or integration depth of nature-based engineering features. Thus, *River Architect* applies nature-based engineering features such as fascines or geotextile between the **(min)** value in row 7 and the **(max)** value in row 8 of the [threshold value workbook](LifespanDesign#input-modify-threshold-values). Regions with at terrain slope above the threshold defined in row 20 and above the maximum Depth to the groundwater defined in row 8 get mineral nature-based engineering (such as rock paving or riprap) assigned according to the [stable grain size](#rocks). The differentiation is made because nature-based engineering features may dry out when the water table is too far away (vertically).
-   Terrain slope `S0` of 0.2 (20%).

*River Architect* uses the `.../01_Conditions/CONDITION/dem.tif` to compute the percent-wise terrain slope `S0`, where modified terrain with slopes of more than the `S0` threshold is considered to require reinforcement.

The [Lifespan & Design][3] tab enables the creation of :

-	**Lifespan Maps** with output Raster names:
	+ `.../LifespanDesign/Output/Rasters/CONDITION_lyr20/lf_bio_v_bio.tif` (vegetative nature-based engineering)
	+ `.../LifespanDesign/Output/Rasters/CONDITION_lyr20/lf_bio_m_bio.tif` (mineral, i.e., boulder, nature-based engineering)
	
These lifespan maps represent basically **Design Maps** that indicate the applicability of features. However, the units of these rasters are lifespans in years, which is necessary for the later on automated placement of most suitable features, where lifespans represent the driving parameter to identify the most suitable features.


## Berm Setback / Widen<a name="berms"></a>

Berms are artificial lateral confinements that are represented by man-made bars and dikes. Also, levees represent lateral confinement but their flood protection-function should not be deleted, and therefore, levees are not considered for setback action. *River Architect* internally replaces the strings "Bermsetback" with "Widen" because the removal of lateral confinements represents a river widening. Recommended threshold values in the [`threshold_values.xlsx` workbook](#featoverview) are:

-   Morphological Units (relevance-method) with `mu_relevance = ["bank", " floodplain ", "high floodplain", "island floodplain ", "island high floodplain ", "lateral bar", "levee", "spur dike", "terrace"]`.
-   Detrended DEM `det` with a lower limit of 5.2 m (17 ft) and an upper limit of 7.6 m (25 ft) to limit the application of berm setback and widening to economically reasonable extents.

The [Lifespan & Design][3] tab enables the creation of:

-	**Design Maps** with output Raster name: `.../LifespanDesign/Output/Rasters/CONDITION_lyr10/det_widen.tif`.

**Lifespan Maps** are not created unless activated at the bottom of the [`threshold_values.xlsx` workbook](#featoverview).


## Streamwood and Engineered Log Jams<a name="elj"></a>

Lifespan maps and design maps are created for streamwood placement and engineered log jams (ELJs). Recommended threshold values in the [`threshold_values.xlsx` workbook](#featoverview) are:

-   Flow depth `h` corresponding to 1.7 multiplied with a log diameter of (e.g., 0.6 m · 1.7 = 1.02 m or 3.34 ft) (see [Lange and Bezzola 2005)][lange05];
-   Froude number `Fr` of 1.0 (see [Lange and Bezzola 2005)][lange05];
-   Morphological Units (avoidance-method) with `mu_avoidance = [tributar channel, tributary delta]` (see below explanations);
-   Frequency threshold (design maps) of 10.0 years (computed as a function of flow depth, not Froude number, see below explanations).

Regarding morphological units, riffle-pool and plane bed morphologies are favorable for streamwood placement, where side channel and tributary systems are not convenient for wood placement. Streamwood inclusive list is defined as<br/>
`mu_good = ["riffle", "riffle transition", "pool", "floodplain", "island floodplain", "lateral bar", "medial bar", "run"]`<br/>
and the exclusive list is defined as `mu_bad = ["tributary channel", "tributary delta"]`.<br/>
For streamwood, the exclusive approach based on `mu_bad` applies (see [parameters](LifespanDesign-parameters)).<br/>
The design maps for the minimum required log diameter *D<sub>w</sub>* results from [Ruiz-Villanueva et al. (2016)][ruiz16b]'s interpolation curve as a function of the flow depth. The module applies on the single-thread formula because it returns larger values for the log diameter than the multi-thread formula when the probability of motion is set to zero: `Dw` = 0.32 / 0.18·`h`. The output map limits to regions where `Dw` is smaller than 7.6 m (300 in - lease contact us if that is not sufficient for a particular application).

The [Lifespan & Design][3] tab enables the creation of:

-	**Lifespan Maps** with output Raster name: `.../LifespanDesign/Output/Rasters/CONDITION_lyr20/lf_wood.tif`; and
-	**Design Maps** with output Raster name: `.../LifespanDesign/Output/Rasters/CONDITION_lyr20/ds_Dw_wood.tif`.

## Fine sediment<a name="finesed"></a>

Artificially introduced fine sediment facilitates the root growth of new plantings but the flow may easily entrain (mobilize) artificially placed fine sediment. Moreover, spontaneous percolation of fine sediment into the voids of the coarser existing sediment may occur. Therefore, plantings-specific parameters apply to the introduction of fine sediment, as well as filter criteria. The analysis considers fine sediment with a maximum grain diameter of 2 mm (0.08 in, i.e., sand). Recommended threshold values in the [`threshold_values.xlsx` workbook](#featoverview) are:

-   Critical dimensionless bed shear stress `taux` of *&tau;<sub>\*,cr</sub></sub>* = 0.030.
-   Topographic change rates:
	+ `scour` with respect to [White Alder](#plants) (largest for plantings) of 0.3 m (1.0 ft) multiplied with the number of years of terrain change observation 
	+ `fill` with respect to [Cottonwood](#plants) (highest for plantings) of 0.8 *times the seedling length in m or ft* and multiplied with the number of years of terrain change observation (the sample case uses Cottonwood with a planting depth of 80%, a cutting length of 7 ft (2.1 m) and a topographic change observation period of 3 years)
-   Depth to groundwater `d2w` with a lower limit of 0.3 m (1 ft) and an upper limit of 3.0 m (10 ft) corresponding to vegetation [plantings](#plants) requirements.

In general, the topographic change and depth to water table thresholds should correspond to the largest values that any plantings type (cf. [Vegetation Plantings](#plants)) supports because only these areas are of interest for the incorporation of fine sediment in soils.

The [Lifespan & Design][3] tab enables the creation of:

-	**Lifespan Maps** with output Raster name: `.../LifespanDesign/Output/Rasters/CONDITION_lyr30/lf_fines.tif`; and
-	**Design Maps** with output Raster name: `.../LifespanDesign/Output/Rasters/CONDITION_lyr30/ds_Dcf_fines.tif`.

The critical stable grain size of fine sediment `Dcf` is the maximum admissible size of fine sediment including the (D<sub>max, fine</sub> < 2 mm or 0.08 in) that results from a [grain mobility analysis](#rocks). The design maps use filter criteria according to the [USACE (2000)][usace00] to avoid percolation of fine sediment in the matrix of coarser present grain size:

-	*D<sub>15, fine</sub> > D<sub>15, coarse</sub>* / 20;
-	*D<sub>85, fine</sub> > D<sub>15, coarse</sub>* / 5;
-	*D<sub>max, fine</sub>* must be finer than sand (i.e., *<* 2 mm or 0.08 in), to satisfy its *fine* character.

*D<sub>15, coarse</sub>* is calculated as `0.25 * dmean.tif`. The 0.25 multiplicator is an empirical value - please contact us for discussions (email to: river.architect.program[AT]gmail.com).


## Grading<a name="grading"></a>

Grading aims at the reconnection of high floodplains and isolated islands through floodplain terracing and bar lowering. Grading is from an interest in areas where potential plantings cannot reach the groundwater table or where even high discharges cannot rework the channel. Low dimensionless bed shear stress, infrequent grain mobilization or low scour rates indicate relevant sites. The following parameter Rasters and hypotheses apply to lifespan maps for grading measures (no design maps). Recommended threshold values in the [`threshold_values.xlsx` workbook](#featoverview) are:

-   Critical dimensionless bed shear stress `taux` of *&tau;<sub>\*,cr</sub>* equal to 0.047.
-   Topographic change: scour rate `tcd`-`scour` of 0.03 m (0.1 ft) multiplied with the number of observation years documented with the `scour` raster, and the `inverse` argument (i.e., areas of interest correspond to regions where the scour threshold is not exceeded).
-   Depth to groundwater `d2w` with lower and upper limits corresponding to target [plant species](#plants) in Mediterranean climates (Phreatophytes) to achieve depths to groundwater between 2.1 m (7 ft) and 3.0 m (10 ft).

Moreover, morphological unit criteria may be defined.

The [Lifespan & Design][3] tab enables the creation of:

-	**Lifespan Maps** with output Raster name: `.../LifespanDesign/Output/Rasters/CONDITION_lyr10/lf_grade.tif` contain on/off lifespans corresponding to the maximum defined lifespan (highest discharge) or `NoData` pixels, respectively.

The grading lifespan maps can also be interpreted as a **Design Map**, which are not particularly generated as long as deactivated at the bottom of the [`threshold_values.xlsx` workbook](#featoverview).

## Plantings<a name="plants"></a>

The survival analysis of plantings assumes a general cutting length of min. 2.1 m (7 ft), where approximately 80*%* of the cuttings are planted in the ground and 20*%* protrude above the ground. The *<a href="LifespanDesign">LifespanDesign</a>* module enables the differentiation between up to four indigenous plant species that are relevant for habitat enhancement. The installation contains threshold parameters for **lifespan maps** for the following plant species native to Northern California (referred to as "sample case"). The depth to the groundwater `d2w` thresholds correspond to naturally observed occurrences. **No design maps** are created because the lifespan maps already contain all relevant information.
Recommended threshold values in the [`threshold_values.xlsx` workbook](#featoverview) for phreatophytes are:

-   Box Elder (*Acer Negundo*)
	+  Flow depth `h` of 0.3 m (1 ft) (exclude all submerged regions for more than *Q<sub>sub</sub>*, which persists for more than 85 consecutive days according to [Friedman and Auble 1999][friedman99])
	+  Critical dimensionless bed shear stress `taux` of 0.047 ([Friedman and Auble 1999][friedman99])
	+  No Topographic change rate applies because Box Elder is reported to survive burial ([Kui and Stella 2016][kui16a])
	+  Depth to groundwater `d2w`  with lower and upper thresholds of 0.6 m (2 ft) to 2.0 m (6 ft), respectively.<br/>
	   *Full source ranges: 0.6 m to 4.6 m ([Stella et al. 2003][stella03])*   
    +  *Note:* A maximum submergence duration supported by Box Elder cuttings of 85 days per year needs to be considered and verified as a function of flow duration curves.

-   Cottonwood (*Populus Fremontii*)
	+ Flow depth `h` of >= 0.5 · *stem height* and 
	+ Flow velocity `u` of >= 0.9-1.2 m/s (3.0-4.0 fps) ([Stromberg et al. 1993][stromberg93], [Wilcox and Shafroth 2013][wilcox13], [Bywater-Reyes 2015][bywater15])
	+ Topographic change rates:
	   * `scour` >= 0.1 *times root depth* ([Polzin and Rood 2006][polzin06]), or >= 0.2 *times root depth* ([Kui and Stella 2016][kui16a]), or >= 0.5 *times root depth* ([Bywater-Reyes 2015][bywater15])
	   * `fill` >= 0.8 *times seedling length* ([Kui and Stella 2016][kui16a], [Polzin and Rood 2006][polzin06])
	+ Depth to groundwater  `d2w` with a lower threshold of 1.5 m (5 ft) and an upper threshold of 3 m (10 ft)<br/>
	   *Full source ranges: 0.6 m to 4.6 m ([Stella et al. 2003][stella03]), 0.6 m to 2.7 m ([SYRCL 2013][syrcl13]), 0.6 m to 2.8 m above baseflow level for the closely-related black cottonwood (*Populus trichocarpa*, extracted from [Polzin and Rood 2006][polzin06]), 0.23±0.08 m to 1.58±0.14 m for establishment of woody riparian species and up to 2.9 m for existing plants ([Shafroth et al. 1998][shafroth98], [2000][shafroth00]), up to 2.0 m ([Stromberg et al. 1996][stromberg96]), up to 1.0 m, [Stromberg et al. 1991][stromberg91]), up to 4.5 m for adult lifestages ([Busch and Smith 1995][busch95]), up to 3.5 m for adult lifestages ([Lite and Stromberg 2005][lite05]), up to 4-5 m for salicae in general ([Politti et al. 2018][politti18])*
	+  The base case applies sample values of a minimum cutting length of 2.1 m (7 ft), a topographic change observation period length of 3 years and a planting depth of 80% (0.8) of the cutting length.

-   White Alder (*Alnus Rhombifolia*)
	+  Critical dimensionless bed shear stress `taux` of 0.047
	+  Topographic change: scour rate `tcd`-`scour` *>=* 0.3 m (1 ft) ([Jablkowski et al. 2017][jablkowski17]) multiplied with the number of years of observation covered by the `scour` input raster
	+  Depth to groundwater `d2w` with a lower threshold of 0.9 m (3 ft) and an upper threshold of 1.5 m (5 ft) ([Stillwater Sciences 2006][stillwater06]) or less than 5.0 m for grown-up trees ([Claessens et al. 2010][claessens10])

-   Willows
	+  (Goodding\'s) Black willow (*Salix nigra* including *Salix Gooddingii*)
	   * Flow depth `h` of >= 1.0-1.5 *times the shrub height* ([Stromberg et al. 1993][stromberg93])
	   * Depth to groundwater `d2w` with a lower threshold of 0.3 m (1.0 ft) and an upper threshold of 1.5 m  (4.9 ft) <br/>
         *Full source ranges: 0.6 m to 2.7 m ([SYRCL 2013][syrcl13]), 0.9 m to 1.5 m ([Stillwater Sciences 2006][stillwater06]), up to 2.0 m ([Shafroth et al. 1998][shafroth98]), 0.21±0.05 m to 1.44±0.22 m for establishment of woody riparian species, up to 2.0 m for existing plants([Stromberg et al. 1996][stromberg96]), up to 3.2 m for adult lifestages, [Stromberg et al. 1996][stromberg96]), up to 4-5 m for salicae in general ([Politti et al. 2018][politti18]), up to 2.6 m for native plants ([Lite and Stromberg 2005][lite05])*
	+  Red willow (*Salix laevigata*)
	   * Depth to groundwater `d2w` with a lower threshold of 0.3 m (1.0 ft) and an upper threshold of 1.5 m  (4.9 ft) <br/>
	     *Full source ranges: 0.6 m to 2.7 m ([SYRCL 2013][syrcl13]), 0.9 m to 1.5 m ([Stillwater Sciences 2006][stillwater06]), up to 3.0 m ([USACE, YWA and 2017][usace17], [2019][usace19])*
	+  Arroyo willow (*Salix lasiolepis*)
	   * Depth to groundwater `d2w` with a lower threshold of 0.3 m (1.0 ft) and an upper threshold of 1.5 m  (4.9 ft) <br/>
	     *Full source ranges: 0.6 m to 2.7 m ([SYRCL 2013][syrcl13])*
	+  Willows (*Salix alba*)<br/>
		 *Salix alba parameters are extracted from [Pasquale et al. (2011)][pasquale11], [(2012)][pasquale12], and [(2014)][pasquale14].*
	   * Flow depth `h` of *>=* 0.2 m (0.7 ft)
	   * Critical dimensionless bed shear stress `taux` of 0.1 (if the root depth is larger than 0.5 m and the stem height is larger than 1.0 m)
	   * Topographic change: scour rate `tcd`-`scour` >= 0.1 m (0.2 ft)      
	+  The default workbook case applies sample values of a minimum cutting length of 2.1 m (7 ft), a topographic change observation period length of 3 years and a planting depth of 80% (0.8) of the cutting length.

Some of the above-listed studies on plant stability refer to sand-bed rivers, where scour depths are likelier to be achieved than in gravel-bed rivers (e.g., [Wilcock 1988][wilcock88], [Bywater-Reyes et al. 2015][bywater15]). Threshold values from studies including data from sand-beds ([Stromberg et al. 1993][stromberg93], [Wilcox and Shafroth 2013][wilcox13], [Kui and Stella 2016][kui16a]) require a safety factor of 2 to 4 regarding scour, as the root-plant surfaces are higher in the finer sand beds. The increased contact surface causes higher stability (i.e., the required drag forces for uprooting in gravel/cobble bed rivers are 2-4 times lower) ([Politti et al. 2018][politti18]).

More information on depth to groundwater `d2w` requirements can be derived from [The Nature Conservancy's website][ncw19] ([Plant Rooting Depth Database](https://groundwaterresourcehub.org/public/uploads/pdfs/Plant_Rooting_Depth_Database_20180419.xlsx)).
Indigenous plant species can be found on regional / country-specific websites listed in the following table (source: [Schwindt et al. 2019][schwindt19], supplemental material).

| Country / Region       | Platform                                                     |
| ---------------------- | ------------------------------------------------------------ |
| Canada (Arctic)        | [Flora of the Canadian Arctic Archipelago][floracanada11]    |
| China                  | [Flora of China][florachina08]                               |
| Croatia                | [Flora Croatica][florafcd18]                                 |
| Cyprus                 | [Flora of Cyprus][floracyprus16]                             |
| Czechia                | [Florabase][florabase18]                                     |
| England                | [Online Atlas of the British and Irish Flora][brc18]         |
| Finland                | [Nature Gate][naturegate18]                                  |
| France                 | [Centre de ressources national sur la flore de France][fcbn18] |
| Germany                | [Flora Web][floraweb18]                                      |
| Great Britain          | [Online Atlas of the British and Irish Flora][brc18]         |
| Greece (Ionic islands) | [Flora Ionica][floraionica18]                                |
| Ireland                | [Online Atlas of the British and Irish Flora][brc18]         |
| Israel                 | [Wildflowers of Israel][israflora18]                         |
| Italy                  | [Acta plantarum (IFPI)][actaplantarum18]                     |
| Malta                  | [Malta Wild Plants][maltaflora14]                            |
| Netherlands            | [NDFF Verspreidingsatlas][ndff18]                            |
| New Zealand            | [New Zealand Department of Conservation (Lange et al.)][delange99] |
| Norway                 | [The Flora of Svalbard][svalbardflora18]                     |
| Pakistan               | [Flora of Pakistan][florapakistan18]                         |
| Portugal               | [Sociedade Portuguesa de Botânica][floraon18]                |
| Russia                 | [Plantarium (Plantarium Project)][florarussia18]             |
| Slovakia               | [Bibdigital (CSIC)][bibdigital18]                            |
| Spain                  | [Flora Iberica][floraiberica18]                              |
| Switzerland            | [Info Flora][infoflora18]                                    |
| Turkey                 | [Plants of Turkey (TAS)][floraturkey18]                      |
| United Kingdom         | [Online Atlas of the British and Irish Flora][brc18]         |
| USA, California        | [Calflora][calflora17]                                       |
| USA, general           | [Flora of Northamerica][floranorthamerica08]                 |
| Worldwide (1)          | [Free and open access to biodiversity data][gbif18]          |
| Worldwide (2)          | [The Plant List][plantlist13]                                |

The [Lifespan & Design][3] tab enables the creation of:

-	**Lifespan Maps** with output Raster names: `.../LifespanDesign/Output/Rasters/CONDITION_lyr20/lf_box.tif --lf_cot.tif --lf_whi.tif --lf_wil.tif`. 

The lifespan maps for plant species are considered as **Design Maps** that indicate where and what plant species are sustainable. Therefore, design mapping is deactivated by default at the bottom of the [`threshold_values.xlsx` workbook](#featoverview).


## Sediment replenishment / gravel augmentation<a name="gravel"></a>

Large dams tend to retain the nearby-totality of the catchment sediment supply. The missing sediment causes channel incision and the morphological depletion of rivers in the long term. Regular artificial gravel injections can antagonize this artificial sediment scarcity (e.g., [Pasternack et al. 2010][pasternack10a]). Other authors ([Gaeuman 2008][gaeuman08] and [Ock et al. 2013][ock13]) distinguish replenishment techniques inside and outside of the main channel. According to this differentiation, two types of gravel augmentation are considered in the *LifespanDesign* module:

1.  Gravel stockpiles on floodplains and riverbanks; and
2.  Gravel injections or stockpiles directly in the main channel.

Gravel deposits on floodplains should be erodible by frequent floods (i.e., stockpiles make sense where only larger floods entrain grains). In contrast, gravel injections in the main channel aim at the immediate creation of spawning habitat that should not wash out with the next minor flood event. However, gravel injections with low longevity in the main channel can also serve for an urgent equilibrium of the river sediment budget. Therefore, the lifespan maps for gravel replenishment require two different interpretations inside and outside of the main channel: High lifespans are desirable in the main channel for immediate habitat creation and low lifespans are desirable to equilibrate the sediment budget.

Recommended threshold values in the [`threshold_values.xlsx` workbook](#featoverview) for in-channel gravel injections are:

-   Critical dimensionless bed shear stress `taux` of *&tau;<sub>\*,cr</sub>* = 0.047.
-   Gravel stockpiles on floodplains or riverbanks: Topographic change scour rate: for gravel stockpiles (default in cell `R23` of the [`threshold_values.xlsx` workbook](#featoverview): 0.3 m (or 1 ft) per year).
-	Gravel stockpiles on floodplains or riverbanks: Morphological Units (relevance-method) with `mu_relevance = ["agriplain", "backswamp", "bank", "cutbank", "flood runner", "floodplain", "high floodplain", " hillside", "island high floodplain", "island floodplain", "lateral bar", "levee", "medial bar", "mining pit", "point bar", "pond", "spur dike", "tailings ", "terrace"]`
-   Gravel injections in the main channel: Morphological Units (relevance-method) with `mu_relevance = ["chute", "fast glide", "flood runner", "bedrock", "lateral bar", "medial bar", "pool", "riffle", "riffle transition", "run", "slackwater", "slow glide", "swale", " tailings"]`

The [Lifespan & Design][3] tab enables the creation of:

-	**Lifespan Maps** with output Raster name: `.../LifespanDesign/Output/Rasters/CONDITION_lyr30/lf_gravin.tif --lf_gravou.tif`; and
-	**Design Maps** with output Raster name: `.../LifespanDesign/Output/Rasters/CONDITION_lyr30/ds_Dst_gravin.tif --ds_Dst_gravou.tif`.


## Side cavities<a name="sidecav"></a>

From a parametric point of view, side cavities make sense at channel banks to create preservable habitat and/or endorse protection to prevent bank collapses. In the latter case, groin cavities are an adequate protection measure that can additionally improve habitat conditions. The code analyses relevant sites based on the morphological units and important scour rates at banks. It excludes fill zones where artificial side cavities are prone to sedimentation making the measure ecologically inefficient. Recommended threshold values in the [`threshold_values.xlsx` workbook](#featoverview) are:

-   Topographic change rates:
	+ `fill` threshold value of 0.3 m (1 ft) multiplied with the number of observation years (i.e., if the `fill` raster includes information over multiple years) 
	+ `scour` threshold of 30.5 m (100 ft) marks an arbitrarily chosen value that leads to the exclusion of all fill-prone sites, where side cavities may be easily buried.
-   Morphological Units (relevance-method) with `mu_relevance = ["bank", "cutbank", "lateral bar", "spur dike", "tailings"]`.

The [Lifespan & Design][3] tab enables the creation of:

-	**Design Maps** with output Raster name: `.../LifespanDesign/Output/Rasters/CONDITION_lyr30/ds_mu_sideca.tif`.

The creation of **Lifespan Maps** is deactivated by default at the bottom of the [`threshold_values.xlsx` workbook](#featoverview).
*Note: The delineation of side cavities and the creation of design maps are on our research agenda. Please contact us (email to: river.architect.program[AT]gmail.com) for discussing parametric side cavity implementation.*


## Side channels / anabranches<a name="sidechnl"></a>

Any discrete parameters exist for assessing design or lifespan maps for side channels, anabranches, anastomosed or multithread channels. The identification of splays and bank rigidity requires manual and visual proof. Therefore, *River Architect* requires a user-defined input Raster: `.../RiverArchitect/01_Conditions/CONDITION/sidech.tif`. Before creating the `sidech.tif` Raster, please read the following paragraphs.<br/>

An initial decision support on the basis of design maps was contemplated by comparing the minimum energy slope *S<sub>e,min</sub>* with the terrain slope*S<sub>0</sub>*. In 1D-theory, the minimum energy slope results from the
*H*-*h* diagram ([Glenn 2015][glenn15]), based on the assumption that the minimum energy per unit force and pixel *H<sub>min</sub>* corresponds to the Froude number *Fr* = 1 with the critical flow velocity *u<sub>c</sub>* and flow
depth *h<sub>c</sub>*. The pixel unitary discharge results from *q* = *u \* h*, where *u* and *h* are pixel values from the `u` and `h` rasters. Thus, the following set of equations can be used:

  *Fr = 1 <-> 1 = u<sub>c</sub> / (g \* h<sub>c</sub>)<sup>0.5</sup> <-> u<sub>c</sub> = (g \* h<sub>c</sub>)<sup>0.5</sup>* <br/>
  *h<sub>c</sub> = (q<sup>2</sup> / g)<sup>1/3</sup>* <br/>
  *q = u\*h* <br/>

*-> H<sub>min</sub> = h<sub>c</sub> + u<sub>c</sub><sup>2</sup> / (2g) = 1.5\*(q<sup>2</sup> / g)<sup>1/3</sup>* <br/>


Thus, the available discharges and related flow velocity `u` and depth `h` rasters could be used for the following calculation (python script sample):

```python
S0 = Slope(dem.raster, "PERCENT_RISE", 1.0))/100
for h.ras in h.rasters and u.ras in u.rasters:
          # compute energetic level
          energy_level[discharge] = dem.raster + 1.5 * Power(Square(h.ras[discharge] * u.ras[discharge]) / g, 1/3)})
          # compute energy slope Se,min
          Se[discharge] = Slope(energy_level[discharge], "PERCENT_RISE", 1.0))/100
          # result = compare Se and S0 (Se / S0)
          Se_S0[discharge] = Se[discharge] / S0)})

```

This sample function uses `arcpy.sa`'s `Slope` function with the arguments `PERCENTRISE` for obtaining percent values instead of degrees and `zFactor` = 1.0 because the x-y-grid units are the same as in z-direction. `g` denotes gravity acceleration (SI metric: 9.81 m/s<sup>2</sup> or U.S. customary: 32.2 ft/s<sup>2</sup>).\
However, the underlying 2D numerical model uses the critical flow depth as an iteration criterion for stability, which causes that *S<sub>e,min</sub>* approximately equals *S<sub>0</sub>*. Thus, the *S<sub>e,min</sub>* / *S<sub>0</sub>* ratio is approximately unity and not meaningful. Otherwise, the ratio *S<sub>e,min</sub>* / *S<sub>0</sub>* indicates pixels with excess energy (*S<sub>e,min</sub>* / *S <sub>0</sub> >* 1) allegedly cause erosion. Pixels with energy shortage  (*S<sub>e,min</sub>* / *S <sub>0</sub> <* 1) allegedly result in sediment deposition. Minor topographic change would be expected where the *S<sub>e,min</sub>* / *S <sub>0</sub>*-ratio is close to unity.<br/>

Unless this problem is not solved, the *River Architect* can only indicate the adequacy of side channel construction on lifespan maps within relevant regions marked with pixel-values of `1` in `sidech.tif`. For creating `sidech.tif`, we recommend to first create a polygon shapefile and draw polygons around side-channel-relevant regions with the following criteria defined by [van Denderen et al. (2017)][vandenderen17]:

-   Intakes (connections) are at river splays (broadenings), downstream of inside bends at the inner bank, or in outer bends at the outer bend.
-   The intake (connection) bifurcation angle (between main and side channel axes) is between 40° and 50°.
-	The side (or connecting) channel’s slope is smaller or equal to the main channel’s slope.
-	The side (or connecting) channel’s length is slightly larger than the main channel (between their bifurcation and confluence).
-	The side (or connecting) channel banks are stabilized with plantings and other nature-based engineering features such as streamwood.

For creating the polygon shapefile:
1.  Open *ArcGIS Pro*
1. 	In the Catalog tab, navigate to the folder where you want to create the shapefile
1.  Create a new polygon-shapefile in the target folder ([read more on arcgis.com](https://pro.arcgis.com/en/pro-app/help/editing/create-polygon-features.htm)), name it `SideChannelDelineation`, and select the project *Coordinate System* (`Current Map`). Click on `Run`.
1.   In the map `Contents` tab, right-click on the new `SideChannelDelineation` layer, then `Attribute Table`. In the `Attribute Table`, click on the top-left *Field:* `Add` button. Name the field `gridcode` (*Field Name* = `gridcode`), *Data Type* = `Short` data type, *Number Format* = `Numeric`, *Precision* = 0, and *Scale* = 0. Go to *ArcGIS Pro*'s *Fields* ribbon (top of the window) and click `Save`.
1.  In *ArcGIS Pro*'s *Edit* ribbon (top of the window), click on `Create` (ensure that the `SideChannelDelineation` layer is selected in the *Contents* tab) > A *Create Features* opens.
1.  In the *Create Features* tab, click (highlight) on `SideChannelDelineation`, then on `Polygon`.
1.  Draw a polygon around one area corresponding to the above [van Denderen et al. (2017)][vandenderen17]-criteria (finish with the `F2`-key); repeat the creation of polygons until all potential side channel candidate sites are mapped.
1.  Go to the `Attribute Table` tab and type *`1`* in the `gridcode` field of all Polygons.
1.  `Save` edits.

Then, convert the Polygon shapefile to a `sidech.tif` GeoTIFF raster:
1. In *ArcGIS Pro*, go to the Geoprocessing tab (typically on the bottom right of the screen)
1. Search for `Polygon to Raster` and select this tool
1. In the field `Input Features` select the before created `SideChannelDelineation` layer (Polygon shapefile)
1. In the `Value Field` select `gridcode`
1. In the `Output Raster Dataset` field select a target location and type `sidech.tif`
1. Recommended: In the `Cellsize` field type `1.0`.

For getting the `sidech.tif` Raster into *River Architect* either copy the Raster in an existing `.../RiverArchitect/01_Conditions/CONDITION/` folder or select it in the creation of a new [Condition](Signposts#conditions).

Within `1`-pixels in `sidech.tif` such as a function of the following input parameters that can be defined in the [`threshold_values.xlsx` workbook](#featoverview):

-   Topographic change: fill rate `tcd`-`fill` of less than 0.1 m (0.3 ft);
-   Critical dimensionless bed shear stress `taux` should be smaller than 0.047.

The [Lifespan & Design][3] tab enables the creation of:

-	**Lifespan Maps** with output Raster names: `.../LifespanDesign/Output/Rasters/CONDITION_lyr21/lf_sidech.tif`. 

The lifespan maps for side channels are considered as **Design Maps** that indicate where side channels may be potentially sustainable. Therefore, design mapping is deactivated by default at the bottom of the [`threshold_values.xlsx` workbook](#featoverview).

Moreover, the final design of side channels can be improved by implementing habitat-enhancing pool-riffle sequences with velocity reversal effects for morphologically effective floods to yield self-maintenance according to [Caamaño et al. (2009)](https://ascelibrary.org/doi/10.1061/%28ASCE%290733-9429%282009%29135%3A1%2866%29). *River Architect* comes with a console script that enables the calculation of such self-maintaining pool-riffle sequences, where a morphologically effective discharge is considered as that discharge, which mobilizes grains. The script is located in `RiverArchitect/Tools/morphology_designer.py` (see [*River Architect* Tools](Tools)).


***

# Define new and modify existing features<a name="modfeat"></a>
The workbook `RiverArchitect/LifespanDesign/.templates/threshold_values.xlsx` contains pre-defined features and defines feature names as well as features IDs, which can be modified if needed. The workbook can be accessed either by clicking on the [*LifespanDesign*][3] GUI's "Modify survival threshold values" button (or directly from the above directory).<br/>
Modifications of feature IDs and names require careful consideration because the packages apply analysis routines as a function of the features *Python* classes. Changing feature names and parameters and IDs only provides the possibility of renaming features and modifying threshold values, as well as the unit system. The feature IDs are internal abbreviations, which also determine the names of output Rasters, shapefiles, and maps. Editing feature evaluations (e.g., adding
analysis routines) requires changes in the *Python* code as explained in the [*LifespanDesign*][3] pages.<br/>
The workbook enables changing vegetation plantings species in columns `J` to `M`. The following columns are associated with distinct feature layers (cf. definitions in the [feature overview section](#featoverview)) in the workbook:

-   Terraforming features: Columns `"E"`, `"F"`, `"G"`, `"H"`, `"I"`.
-   Plant features: Columns `"J"`, `"K"`, `"L"`, `"M"`.
-   Other nature-based engineering features: Columns `"N"`, `"O"`, `"P"`.
-   Connectivity features: Columns `"Q"`, `"R"`, `"S"`.

Detailed instructions for the usage of `threshold_values.xlsx` is provided in the [*LifespanDesign*](LifespanDesign#interface-and-choice-of-features) module, where also more information on threshold values is provided.


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

[busch95]: https://doi.org/10.2307/2937064
[bywater15]: http://dx.doi.org/10.1002/2014WR016641
[carley12]: https://www.sciencedirect.com/science/article/pii/S0169555X12003819
[claessens10]: https://doi.org/10.1093/forestry/cpp038
[friedman99]: http://dx.doi.org/10.1002/(SICI)1099-1646(199909/10)15:5<463::AID-RRR559>3.0.CO;2-Z
[gaeuman08]: http://odp.trrp.net/DataPort/doc.php?id=346
[glenn15]: https://doi.org/10.1201/b18359
[horton01a]: https://doi.org/10.1046/j.1365-3040.2001.00681.x
[horton01b]: https://doi.org/10.1890/1051-0761(2001)0111046:PRTGDV2.0.CO;2
[jablkowski17]: http://www.sciencedirect.com/science/article/pii/S0169555X1730274X
[kui16a]: http://www.sciencedirect.com/science/article/pii/S0378112716300123
[lange05]: https://www.ethz.ch/content/dam/ethz/special-interest/baug/vaw/vaw-dam/documents/das-institut/mitteilungen/2000-2009/188.pdf
[lite05]: https://doi.org/10.1016/j.biocon.2005.01.020
[manningsn]: https://en.wikipedia.org/wiki/Manning_formula#Manning_coefficient_of_roughness
[maynord08]: https://ascelibrary.org/doi/10.1061/9780784408148.apb
[ncw19]: https://groundwaterresourcehub.org/gde-tools/gde-rooting-depths-database-for-gdes
[ock13]: https://www.jstage.jst.go.jp/article/hrl/7/3/7_54/_article
[pasquale11]: https://www.hydrol-earth-syst-sci.net/15/1197/2011/
[pasquale12]: http://www.sciencedirect.com/science/article/pii/S0925857411003697
[pasquale14]: http://dx.doi.org/10.1002/hyp.9993
[pasternack10a]: http://calag.ucanr.edu/archive/?article=ca.v064n02p69
[politti18]: https://www.sciencedirect.com/science/article/pii/S0012825217301186
[polzin06]: https://link.springer.com/article/10.1672/0277-5212(2006)26%5B965:EDSSSA%5D2.0.CO;2
[ruiz16b]: https://www.sciencedirect.com/science/article/pii/S0169555X15002019?via%3Dihub
[schwindt19]: https://www.sciencedirect.com/science/article/pii/S0301479718312751
[shafroth98]: https://doi.org/10.1007/BF03161674
[shafroth00]: https://scholarsarchive.byu.edu/wnan/vol60/iss1/6/
[stella03]: http://www.stillwatersci.com/resources/2003stellaetal.pdf
[stillwater06]: http://www.stillwatersci.com/resources/2006calfed_chfl_restore.pdf
[stromberg91]: https://www.researchgate.net/profile/Brian_Richter/publication/315612144_Flood_Flows_and_Dynamics_of_Sonoran_Riparian_Forests/links/58d547f345851533785bc741/Flood-Flows-and-Dynamics-of-Sonoran-Riparian-Forests.pdf
[stromberg93]: http://www.jstor.org/stable/41712765
[stromberg96]: https://doi.org/10.1002/(SICI)1099-1646(199601)12:1<1::AID-RRR347>3.0.CO;2-D
[syrcl13]: http://yubariver.org/wp-content/uploads/2013/12/Hammon-Bar-Report-2013-SYRCL.pdf
[usace00]: https://www.publications.usace.army.mil/Portals/76/Publications/EngineerManuals/EM_1110-2-1913.pdf
[usace17]: https://www.spk.usace.army.mil/Portals/12/documents/environmental/Yuba_Jan_2018/Appendix%20C%20-%20Engineering.pdf
[usace19]: https://www.spk.usace.army.mil/Portals/12/documents/environmental/Yuba_Jan_2018/Final-Report-EA_Jan2019/YubaEcoStudyFREA-wFONSI.pdf
[vandenderen17]: https://onlinelibrary.wiley.com/doi/full/10.1002/esp.4267
[weber17]: http://www.sciencedirect.com/science/article/pii/S0169555X16309862
[wilcock88]: http://dx.doi.org/10.1029/WR024i007p01127
[wilcox13]: http://dx.doi.org/10.1002/wrcr.20256
[wyrick14]: https://www.sciencedirect.com/science/article/pii/S0169555X14000099
[wyrick16]: https://onlinelibrary.wiley.com/doi/full/10.1002/esp.3854

[floracanada11]: https://nature.ca/aaflora/data/index.htm
[florachina08]: http://flora.huh.harvard.edu/china/mss/alphabetical_families.htm
[florafcd18]: http://hirc.botanic.hr/fcd/
[floracyprus16]: http://www.flora-of-cyprus.eu/endemics
[florabase18]: http://quick.florabase.cz/
[brc18]: https://www.brc.ac.uk/plantatlas/list_plants
[naturegate18]: http://www.luontoportti.com/suomi/en/kasvit
[fcbn18]: http://www.fcbn.fr/donnees-flore/centre-de-ressources-national-sur-la-flore-de-france
[floraweb18]: http://www.floraweb.de/pflanzenarten/downloads.html
[floraionica18]: https://floraionica.univie.ac.at/index.php?site=1
[israflora18]: http://www.wildflowers.co.il/english/
[actaplantarum18]: http://actaplantarum.org/flora/flora.php
[maltaflora14]: http://www.maltawildplants.com/
[ndff18]: https://www.verspreidingsatlas.nl/vaatplanten
[delange99]: https://www.doc.govt.nz/globalassets/documents/conservation/native-plants/chatham-islands-vascular-plants-checklist.pdf
[svalbardflora18]: http://svalbardflora.no/
[florapakistan18]: http://www.tropicos.org/Project/Pakistan
[floraon18]: http://flora-on.pt/
[florarussia18]: http://www.plantarium.ru/
[bibdigital18]: http://bibdigital.rjb.csic.es/ing/Volumenes.php?Libro=6351
[floraiberica18]: http://www.floraiberica.es/PHP/familias_lista.php
[infoflora18]: https://www.infoflora.ch/en/
[floraturkey18]: https://turkiyebitkileri.com/en/
[calflora17]: http://www.calflora.org
[floranorthamerica08]: http://floranorthamerica.org/
[gbif18]: https://www.gbif.org/
[plantlist13]: http://www.theplantlist.org/