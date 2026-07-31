Riparian Seedling Recruitment (RSR)
====================



- [Introduction to the Riparian Seeling Recruitment Module](#intro)
- [Quick GUIde to Riparian Seedling Recruitment Assessment](#rsr-quick)
- [Defining Criteria](#species-rc)
  - [Modifying `recruitment_criteria.xlsx`](#modify-rc)
- [Methodology](#methods)
  - [Analysis Period](#analysis-period)
  - [Interpolating Hydraulic Rasters](#interpolating-hydraulic-rasters) 
  - [Analysis Crop Area](#crop-area)
  - [Bed Preparation Assessment](#bed-preparation)
  - [Dessication Survival Assessment](#ds-assessment)
  - [Inundation Survival Assessment](#inundation-survival)
  - [Scour Survival Assessment](#scour-survival)
  - [Physical Process Parameters Metrics](#process-parameters)
  - [Combined Recruitment Potential Metric](#combined-rp-metric)
  - [Optional: Recruitment Band Criteria](#recruitment-band)
  - [Optional: Existing Vegetation](#ex-veg)
  - [Optional: Grading Limits](#grading-limits)
- [References](#references)

***

# Introduction to Riparian Seedling Recruitment Module<a name="intro"></a>

The Riparian Seedling Recruitment module can be used to map areas of seedling recruitment potentials and calculate recruitment potential metrics for a given Cottonwood species and flow record. The Riparian Seedling Recruitment module is an application based on the recruitment box model as described by [Mahoney & Rood (1998)](https://doi.org/10.1007/BF03161678). The conceptual model describes how site hydrology, seed dispersal, and drought tolerance are associated with successful cottonwood seedling recruitment.

<p align="center">
  <img src="https://github.com/RiverArchitect/Media/raw/master/images/RSR_conceptual_model.png" width=600 />
</p>

The Riparian Seedling Recruitment sub-module evaluates five physical mechanisms with consideration of timing: 

1. Dimensionless bed shear stress before seed dispersal (bed preparation)
2. Wetted area during seed dispersal period (establishment)
3. Post-germination stage recession (desiccation survival)
4. Prolonged inundation (inundation survival)
5. Dimensionless bed shear stress after establishment (scour survival). 

The model does not take climactic factors such as precipitation and temperature into consideration.   

The Riparian Recruitment module evaluates the survival of Cottonwood seedlings through their first year of life beginning with germination. The recruitment potential index ranges between 0.0 and 1.0 and the module writes the area totals for all parameters and final recruitment potential to a spreadsheet in the output folder. 

![RSR_conceptual_model](https://github.com/RiverArchitect/Media/raw/master/images/RSR_schematic.PNG)

# Quick GUIde to Riparian Recruitment Assessment<a name="rsr-quick"></a>


<p align="center">
  <img src="https://github.com/RiverArchitect/Media/raw/master/images/gui_start_recruitment.PNG" width=600 />
</p>

To begin using the Riparian Seedling Recruitment module, first select a hydraulic [Condition](Signposts.md#conditions). 

The Riparian Seedling Recruitment module requires the following files to be included in the [Condition](Signposts.md#conditions) folder: 

- DEM raster (*Note:* the file must be named `dem.tif`)
- Hydraulic rasters (velocity and depth or water surface elevation) for the range of flows. (*Note:* the file naming convention `hQQQQQQ.tif`,  `uQQQQQQ.tif` must be used) 
- Grain size raster (*Note*: must be named either `dmean_ft.tif` for U.S. customary in feet  or `dmean.tif` for SI metric in meters)

4. Optional: Existing vegetation raster 

5. Optional: Grading limits raster (for design applications) 

The tool can be run in either US (ft) or SI (metric) by changing the option in the Units drop-down tab. 

How [Existing Vegetation](#ex-veg) and [Grading Limits](#grading-limits) change the analysis is described in the [Methodology](#methods). 

*Note:* You will only need hydraulic rasters to cover the range of flows you are going to be analyzing. Determine the highest and lowest flows during the analysis period to ensure that there are no errors when the tool runs. See [Analysis Period](#analysis-period) in [Methodology](#methods) for a description of this temporal period. 

Next, select at the [Species](#species-rc) from the drop down menu, which contains data specific to the species of interest for analyzing seedling recruitment. [Species](#species-rc) data is used by the Riparian Seedling Recruitment module to determine what the threshold values associated with physical processes that cause stress or mortality for seedlings during establishment and survival. These data can be viewed/edited via the `Modify recruitment criteria` button, which opens the `recruitment_criteria.xlsx`. See [Defining Criteria](#species-rc) for more information on how to modify the worksheet and the implications of doing so. 

Next, upload the flow data that is available for the site being analyzed (daily mean flow record). The template (`flow_series_example_data.xlsx`) in the `00_Flows\InputFlowSeries` folder should be used to ensure that the correct format is provided for the module calculations.

Next, select the year-of-interest from the drop down menu, which is generated from the flow data selected. See [Analysis Period](#analysis-period) for details about the data range needed to analyze the seedling recruitment potential for a given year-of-interest. 

The last two optional buttons will take you to the [Condition](Signposts.md#condition) folder being analyzed to select the rasters that contain established vegetation canopy cover and a grading extents rasters. See [Existing Vegetation](#ex-veg) and [Grading Limits](#grading-limits) for more information about including these options in the analysis. 

Outputs are stored in `RiparianRecruitment\Output\Condition_name` :  

- `taux_QQQQQQ_QQQ.tif` : rasters of dimensionless bed shear stress (BSS) for each hydraulic raster (`uQQQQQQ.tif`). See [Bed Preparation Assessment](#bed-preparation) for more. 
- `Q_mobile_fp_taux_cr.tif` : the fully mobilized flow raster created from the set of BSS rasters by determining the lowest flow where the BSS is equal to or greater than fully prepared threshold criteria. See [Bed Preparation Assessment](#bed-preparation) for more. 
- `Q_mobile_pp_taux_cr.tif` : the partially mobilized flow raster created from the set of BSS rasters by determining the lowest flow where the BSS is equal to or greater than partially prepared threshold criteria. See [Bed Preparation Assessment](#bed-preparation) for more. 

Outputs associated specific to the year-of-interest analyzed are stored in `RiparianRecruitment\Output\Condition_name\year-of-interest ` : 

- `wa_sd_ras.tif` : a raster showing the wetted area during seed dispersal period 
- `rec_elev_band.tif` :  a raster showing the area between the recruitment band elevation criteria
- `crop_area_minus_veg.tif` : a raster showing the wetted area during seed dispersal period or the recruitment band  area with the area that has established area not anticipated to be removed by flood events excluded, which is used to crop the analysis area. See [Analysis Crop Area](#crop-area) for more.
- `bed_prep_ras.tif` : a raster showing the performance of the [Bed Preparation Assessment](#bed-preparation) with values of 0 (unprepared), 0.5 (partially prepared), and 1 (fully prepared). 
- `rr_fav_days.tif` : a raster showing the number of days with a favorable recession rate during the desiccation survival period.
- `rr_stress_days.tif` : a raster showing the number of days with a stressful recession rate during the desiccation survival period.
- `rr_lethal_days.tif` : a raster showing the number of days with a lethal recession rate during the desiccation survival period.
- `mortality_coef_ras.tif` : a raster showing the mortality coefficient calculated from the number of favorable, stressful, and lethal days.  See [Dessication Survival Assessment](#ds-assessment) for more. 
- `max_inund_days.tif` : a raster showing the maximum number of days that each cell experiences consecutive days of inundation. See [Inundation Survival Assessment](#inundation-survival) for more. 
- `inundation_surv_ras.tif` : a raster showing the performance of the [Inundation Survival Assessment](#inundation-survival) with values of 0 (lethal inundation), 0.5 (stressful inundation), and 1 (favorable inundation)
- `scour_surv_ras.tif` : a raster showing the performance of the [Scour Survival Assessment](#scour-survival) with values of 0 (fully disturbed), 0.5 (partially disturbed), and 1 (undisturbed).
- `recruitment_potential_ras.tif` : a raster showing the combined recruitment potential, which is a product of the `bed_prep_ras.tif`,  `mortality_coef_ras.tif`,  `inundation_surv_ras.tif`, and `scour_surv_ras.tif`. See [Combined Recruitment Potential Metric](#combined-rp-metric) for more. 



***

# Defining Criteria <a name="species-rc"></a>


## Modifying `recruitment_criteria.xlxs`<a name="modify-rc"></a>

The worksheet is not hard coded, but values are referenced by the descriptions of the criteria so it is important to not change the text under the column header 'DO NOT EDIT BELOW.' Species will be selected by their 'Common name' and the 'TEMPLATE' column may be used to add a new set of criteria for the species you choose to analyze. 

<p align="center">
  <img src="https://github.com/RiverArchitect/Media/raw/master/images/recruitment_criteria_xlsx.png" width=600 />
</p>

# Methodology<a name="methods"></a>


## Analysis Period<a name="analysis-period"></a>

Each process or lifestage event has an associated temporal period during which the event must occur as the timing is crucial due to limitations such as seed dispersal and viability and seedling root growth. Five temporal periods span the physical processes and lifestage events considered to evaluate seedling recruitment: 

- Bed Preparation Period (BPP)
- Seed Dispersal Period (SDP)
- Desiccation Survival Period (DSP)
- Inundation Survival Period (ISP)
- Scour Survival Period (SSP)

The five temporal periods are not completely distinct; two or more processes can operate concurrently, so overlap exists among the periods (see figure below).

<p align="center">
  <img src="https://github.com/RiverArchitect/Media/raw/master/images/RSR_hydrograph_periods.png" />
</p>

The recruitment box boundaries are set by the timing of seed dispersal and the favorable elevations where successful seedling recruitment is likely [Mahoney & Rood (1998)](https://doi.org/10.1007/BF03161678). The thresholds set by the hydrologic components and seed release can be visualized as a bounding box on a hydrograph (see figure above). The top boundary of the box is the upper elevation at which seedlings will not survive after the stage declines due to desiccation. The bottom boundary of the box is the lower elevation at which seedlings will not survive prolonged inundation or will be uprooted and/or buried. Seedling establishment includes the seed release period and the length of seed viability. The left boundary of the box is the beginning of the seed release and the right boundary is the beginning of the baseflow period. 

## Interpolating Hydraulic Rasters<a name="interpolating-hydraulic-rasters"></a>

Water surface elevation (WSE) and depth rasters are common outputs of 2D-hydraulic models. If only depth rasters are available as inputs, the WSE rasters are calculated through a simple addition of the water depth and topographic elevation. Interpolation of the WSE rasters across the topographic extents of a given site generates a water level elevation (WLE) raster. The methods for calculating WLE rasters was developed for the [Stranding Risk](StrandingRisk.md) module [Larrieu et al., 2021](https://doi.org/10.1002/eco.2268). The default spatial interpolation method used in the Riparian Seedling Recruitment module is inverse distance weighted (IDW) interpolation. Further explanation of IDW and the other available interpolation methods (Kriging and Nearest Neighbor) can be found in the Stranding Risk section on [Interpolating Hydraulic Rasters](StrandingRisk.md#interpolating-hydraulic-rasters). The WLE rasters for each corresponding hydraulic raster input is saved in the respective ‘condition’ folder to be used in future analysis (e.g. a different selected year or species).

The Riparian Seedling Recruitment module allows users to analyze mean daily flow records without the need to model every flow in the record. A second interpolation takes place to calculate WLE array for the unmodeled flows (see figure below). The algorithm uses linear interpolation to calculate the unmodeled WLE raster using two WLE rasters calculated from modeled hydraulic raster inputs. These interpolated WLE arrays are not saved as rasters to conserve memory but used as intermediate arrays to calculate the seed dispersal wetted area, recession rate, and inundation calculations. 

The linear interpolation between the spatially interpolated (modeled) WLE rasters for a given WLE associated with a flow from the daily mean flow record is calculated with the following equation:

<p align="center">
  <img src="https://github.com/RiverArchitect/Media/raw/master/
images/RSR_interpolated_wle_eq.PNG" width=400/>
</p>

<p align="center">
  <img src="https://github.com/RiverArchitect/Media/raw/master/images/RSR_WLE_interpolation.png" />
</p>



The WLE value with the DEM allows for inundation and recession rate to be determined. Inundation (water level above the ground surface) is tracked from the beginning of the seed dispersal period. When WLE value < DEM value, the elevation of the WLE is the elevation of the groundwater surface. The algorithm assumes that the groundwater surface elevation can be determined by the calculated WLE, a derivative of channel WSE. This assumption is made in rivers with coarse substrate where it would be expected that little capillary capacity is present [Mahoney & Rood (1998)](https://doi.org/10.1007/BF03161678). The assumption that the groundwater surface is not raised by capillary fringe is a conservative decision that also allows the used to consider adjusting site-specific recession rate criteria.

Potential germination is only considered during the seed dispersal period if the cell has gone dry to represent the risk of seeds being washed away from a given cell if it is inundated. The last day in the seed dispersal period where a cell has gone dry is when recession rate, prolonged inundation, and scour tracking begins to simulate the process of a viable seed finding a suitable site and germinating. This results in the variable seed dispersal period end and start dates (on a cell-by-cell basis) for the bed preparation, inundation survival, and scour survival periods 

## Analysis Crop Area<a name="crop-area"></a>

 A unique feature of this approach is that the spatial domain for all physical process analysis is set by the wetted area extents of the highest and lowest flows during the seed dispersal area giving us a wetted areas that went dry during the seed dispersal period where germination was possible. The crop represents the area that limits the analysis for all physical processes and total recruitment potential calculations (`wa_sd_ras.tif`). If the option to exclude well established vegetation is desired, the crop rasters will be saved as `crop_area_minus_veg.tif`. See [Optional: Existing Vegatation](#ex-veg) for more. 

If a recruitment band elevation method is preferred, upper and lower band elevations should be provided in the `recruitment_criteria.xlsx` as this will override the default methodology to use the wetted area extent during seed dispersal to define the crop area. 

## Bed Preparation Assessment<a name="bed-preparation"></a>

> **Historical method:** this legacy page retains the ArcPy 1.x equation for reproducibility.
> The current GDAL implementation uses a relative-submergence-dependent resistance law; see
> the [current equations and validity notes](../modules/lifespans.md#dimensionless-bed-shear-stress-taux).

In the ArcPy 1.x implementation, dimensionless bed shear stress (&tau;<sub>\*</sub>) was calculated with the following equation, which was consistent with the historical [Lifespan Design](LifespanDesign.md) module:

<p align="center">
  <img src="https://github.com/RiverArchitect/Media/raw/master/
images/RSR_dimensionless_bss_eq.PNG" width=400/>
</p>


- A threshold value for mobility according to the critical dimensionless bed shear stress τ<sub>*cr</sub> can be defined the `recruitment_criteria.xlsx` (read more for example in [Lamb et al. 2008](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2007JF000831))
- `uQQQQQQ_QQQ` (m/s or fps), `hQQQQQQ_QQQ` (m or ft), and *D<sub>84</sub>* = 2.2 · D<sub>50</sub> (m or ft) are `arcpy.Raster()`s considering that the grain diameter *D<sub>84</sub>* can be approximated by *D<sub>84</sub>* = 2.2 · *D<sub>50</sub>* ([Rickenmann and Recking 2011](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2010WR009793))
- *g* = gravitational acceleration (9.81 m/s2)
-  *s* = ratio of sediment grain and water density (2.68)

The bed preparation analysis creates a set of dimensionless bed shear stress (BSS) rasters for each hydraulic raster in a [Condition](Signposts.md#conditions). Two preliminary rasters, the partially and fully mobilized flow rasters (`Q_mobile_fp_taux_cr.tif` and `Q_mobile_pp_taux_cr.tif`), are created from the set of BSS rasters by determining the lowest flow where the BSS is equal to or greater than the BSS threshold criteria for each of those sediment transport regimes and assigns the associated flow to the cell. 

The peak flow during the bed preparation period (*Q<sub>max</sub>*) is then determined and compared to both sets of mobilized flow rasters. A value of 0 is assigned to cells where the peak bed preparation flow does not exceed either of the mobilized flow rasters to represent that the area is “unprepared.” A value of 0.5 or 1 is assigned to cells where the peak bed preparation flow exceeds the partially or fully mobilized flow rasters, respectively. The final product is the bed preparation raster, `bed_prep_ras.tif`.

## Desiccation Survival Assessment<a name="ds-assessment"></a>

Cottonwood seedlings are not drought tolerant and will become stressed if recession rates exceed the seedling ability to grow roots deep enough to keep up with recession, especially in dry climates. Recession rate is calculated by comparing the interpolated WLE rasters to the ground surface elevation on a cell-by-cell basis for each day. Recession rate calculations require a mean daily flow record to capture the daily stress that a seedling will experience. A 3-day moving average was calculated to evaluate recession rate as this captures the lag associated with infiltration and drainage of water ([Braatne et al. 2007](https://onlinelibrary.wiley.com/doi/10.1002/rra.978); [Burke et al. 2009](https://www.sciencedirect.com/science/article/pii/S0301479708002715); [Kalischuk et al., 2001](https://doi.org/10.1016/S0378-1127(00)00359-5); [Rood and Mahoney, 2000](https://www.researchgate.net/publication/279572771_Revised_instream_flow_regulation_enables_cottonwood_recruitment_along_the_St_Mary_River_Alberta_Canada)). The daily recession rate for a given cell is calculated with a 4-day moving window that retains the last three days WLE values (*WLE<sub>-3</sub>, WLE<sub>-2</sub>, WLE<sub>-1</sub>, WLE*). The following equation is used to calculate the 3-day average recession rate for a given day:  

<p align="center">
  <img src="https://github.com/RiverArchitect/Media/raw/master/
images/RSR_3-day_avg_eq.PNG" width=350/>
</p>

The recession rate criteria is determined by how quickly the cottonwood seedlings are able to grow roots. If the groundwater elevation recedes faster than the roots can grow to keep up with the recession the seedlings will become water stressed. Recession rate tracking begins at germination (during seed dispersal) to September 15, the beginning of baseflow.

The mortality coefficient (M) was developed to account for seedlings’ ability to survive lethal rates of stage decline if the drop in stage is for only a few days ([Braatne et al. 2007](https://onlinelibrary.wiley.com/doi/10.1002/rra.978); [Burke et al. 2009](https://www.sciencedirect.com/science/article/pii/S0301479708002715)). The mortality coefficient is defined as:

<p align="center">
  <img src="https://github.com/RiverArchitect/Media/raw/master/
images/RSR_mortality_coeff_eq.PNG" width=450/>
</p>


where % lethal days and % stressful days is the number of days that the 3-day moving average of the recession rate is considered lethal or stressful. A mortality coefficient value between 20 and 30 is considered stressful and greater than 30 is considered lethal. The desiccation survival period ends at the beginning of baseflow conditions, which is a hard-coded date assigned in the `recruitment_criteria.xlsx`. Four rasters area created for the desiccation survival period: total favorable days, total stressful days, total lethal days, and mortality coefficient.

## Inundation Survival Assessment<a name="inundation-survival"></a>

Inundation is tracked on a daily, cell-by-cell basis- same as recession rate. A cell is considered “inundated” if the water level elevation exceeds the ground surface (WLE > DEM) as to represent potential partial to complete shoot submergence. Inundation tracking counts the consecutive days that inundation is experienced at a cell by overwriting the day count at a given cell with each day that continuous inundation is experienced (inundated yesterday & inundated today). At the end of the inundation analysis period, the maximum consecutive inundation days raster is saved and used to calculate the inundation survival raster given the inundation criteria threshold values. Two rasters are created for the inundation survival analysis period:  `max_inund_days.tif` and `inundation_surv_ras.tif` 

## Scour Survival Assessment<a name="scour-survival"></a>

Scour is analyzed during the same period that inundation is and uses the same methodology that is used to determine bed preparation as a way of determining if a newly established seedling will experience scour induced uprooting.  See [Bed Preparation Assessment](#bed-preparation) for more. The site being undisturbed is favorable for seedling survival during the scour and survival period in contrast to sediment mobilization being favorable for the bed preparation period. The scour analysis uses the preliminary rasters from the bed preparation analysis and creates a final scour survival raster (`scour_surv_ras.tif`).

## Physical Process Parameters Metrics<a name="process-parameters"></a>

Each physical process will affect the likelihood of germination and survival, so the development of the Riparian Seedling Recruitment module required the translation of concept to code in order to represent the performance in relation to criteria thresholds as a metric. Using the resulting spatial raster data the represents the hydrophysical processes associated with successful seedling recruitment, a prediction of where areas of high recruitment potential will occur across a site can be made. Each of the physical processes is assigned a value of 0, 0.5, or 1 based on lethal, stressful, or favorable conditions, respectively (see table below).

<p align="center">
  <img src="https://github.com/RiverArchitect/Media/raw/master/images/RSR_parameter_values.png" width=700/>
</p>

## Combined Recruitment Potential Metric<a name="combined-rp-metric"></a>

The calculation to determine the combined recruitment potential is a simple multiplication of each physical process metric with equal weighting. If any of the physical processes does not occur during the relevant analysis period or has lethal consequences, the value assigned to the physical process is zero resulting in the combined value is equal to zero (see table below). If no stressful or partial values are present during the recruitment analysis period, the combined value is equal to one.

<p align="center">
  <img src="https://github.com/RiverArchitect/Media/raw/master/images/RSR_combined_rp_values.png" width=500/>
</p>

## Optional: Recruitment Band Criteria<a name="recruitment-band"></a>

There is an option to include recruitment band criteria to be considered when creating the crop raster for analysis. Providing elevations in the `recruitment_criteria.xlsx` will override the default [Analysis Area Crop](#crop-area), so  recruitment band elevations should only be provided if this is the preferred methodology. 

## Optional: Existing Vegetation<a name="ex-veg"></a>

There is an option to upload a raster of existing vegetation canopy cover to exclude this area from the [Bed Preparation Assessment](#bed-preparation). The algorithm will recognize any cell with an assigned value to be a location to be removed from the analysis. 

## Optional: Grading Limits<a name="grading-limits"></a>

There is an option to upload a raster of the grading area extents to consider how bed preparation will be modified if an area has recently been disturbed by grading activity. Grain size is taken into account by including a threshold grain size value that captures substrate that is too large to be a suitable site for germination, which can be modified in the . The graded area where the grain size is less than the threshold criteria is assigned a value of 1 as it assumed that the grading would remove vegetation and create a suitable site for germination that mimics the bed preparation process. 

***

# References

Seedling recruitment thresholds used to define Recruitment Criteria in `recruitment_criteria.xlsx` can be estimated from the following sources:

[Mahoney, J.M., Rood, S.B., 1998. Streamflow requirements for cottonwood seedling recruitment-An integrative model. Wetlands 18, 634–645.](https://doi.org/10.1007/BF03161678)

[Braatne, J.H., Jamieson, R., Gill, M., Rood, S.B., 2007. Instream flows and the decline of riparian cottonwoods along the Yakima River, Washington, USA. River Res. Appl. 23, 247–267.](https://doi.org/10.1002/rra.978)

[Burke, M., Jorde, K., Buffington, J.M., 2009. Application of a hierarchical framework for assessing environmental impacts of dam operation: Changes in streamflow, bed mobility and recruitment of riparian trees in a western North American river. J. Environ. Manage. 90, S224–S236.](https://doi.org/10.1016/j.jenvman.2008.07.022) 
