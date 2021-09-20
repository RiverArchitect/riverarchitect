Stranding Risk Assessment
====================

***

- [Introduction to the Stranding Risk Module](#intro)
- [Quick GUIde to Stranding Risk Assessment](#guide)
- [Defining Travel Thresholds](#defining-travel-thresholds)
- [Methodology](#methodology)
  * [Interpolating Hydraulic Rasters](#interpolating-hydraulic-rasters)
  * [Escape Route Calculations](#escape-route-calculations)
  * [Calculating Disconnected Habitat Area](#calculating-disconnected-area)
  * [Determining Q<sub>disconnect</sub>](#determining-qdisconnect)
  * [Disconnection Frequencies](#disc-freq)
  * [Estimating Ramping Rates](#ramping-rates)
- [References](#references)

***

# Introduction to Stranding Risk Module<a name="intro"></a>

The *Stranding Risk* module can be used to map areas susceptible to stranding and calculate stranding risk metrics for a given fish species, lifestage, and flow reduction scenario. Output rasters include: 
- wetted areas that become disconnected from the river mainstem
- discharge at which each area becomes disconnected
- average frequency at which each area disconnects
- habitat suitability of each area prior to disconnection
- estimated ramping rate

# Quick GUIde to Stranding Risk Assessment<a name="guide"></a>

***

![gui_start_stranding](https://github.com/RiverArchitect/Media/raw/master/images/gui_start_stranding.PNG)

To begin using the Stranding Risk module, first select a hydraulic [Condition](Signposts#conditions). 

*Note*: In order to determine where velocity is a barrier to fish passage, the selected condition must include velocity angle rasters. Otherwise, velocity barriers will not be considered. In order to create the `disconnected_habitat` output raster, cHSI rasters must have already been calculated for the applied [Condition](Signposts#conditions) and [Physical Habitat](SHArC#hefish) using the [SHArC](SHArC) module. In order to create the `disc_freq` output raster, flows must have already been analyzed ([Make flow duration curves](Signposts#ana-flows)) for the applied [Condition](Signposts#conditions) and [Physical Habitat](SHArC#hefish).

Next, select at least one [Physical Habitat](SHArC#hefish) (fish species/lifestage) from the dropdown menu. The Physical Habitat contains data specific to the fish species/lifestage. Physical Habitat data is used by the Stranding Risk module to determine if fish are able to traverse wetted areas by accounting for the organism's minimum swimming depth and maximum swimming speed (Physical Habitat data are also used by [SHArC](SHArC) to determine habitat suitability). These data can be viewed/edited via the drop-down menu: `Select Physical Habitat `  --> `DEFINE FISH SPECIES` (scroll to the "Travel Thresholds" section of the workbook).

Once the desired condition and Physical Habitat(s) are selected, choose model discharges Q<sub>high</sub> and Q<sub>low</sub>. This defines the range of discharges over which to apply the stranding risk analysis, simulating the changes in habitat connectivity for a flow reduction from Q<sub>high</sub> to Q<sub>low</sub>.

Next, input a time period for the downramping. This is the amount of time (in minutes) over which the downramping is expected to occur. This parameter is used to estimate ramping rates as described in [Estimating Ramping Rates](#ramping-rates).

Lastly, select an interpolation method. See [Interpolating Hydraulic Rasters](#interpolating-hydraulic-rasters) for more information.

For further explanation of the methodology used in the analysis, see [Methodology](StrandingRisk#Methodology).

Outputs are stored in `StrandingRisk\Output\Condition_name\`. These outputs include:

- interpolated rasters (`h_interp`, `u_interp`, `va_interp`): interpolated depth, velocity (magnitude), and velocity angle rasters. See [Interpolating Hydraulic Rasters](StrandingRisk#interpolating-hydraulic-rasters) for more information.'

Outputs specific to the applied flow reduction are stored in the subdirectory `StrandingRisk\Output\Condition_name\flow_red_Qhigh_Qlow`. These outputs include:

- `shortest_paths\`: directory containing a raster for each model discharge in the range Q<sub>low</sub>-Q<sub>high</sub>, indicating the minimum distance/least cost required to escape to the river mainstem at Q<sub>low</sub>, subject to constraints imposed by the travel thresholds for the selected Physical Habitat. See [Escape Route Calculations](StrandingRisk#escape-route-calculations) for more.
- `disc_areas\`: directory containing a shapefile for each model discharge indicating wetted areas which are effectively disconnected at that discharge. See [Calculating Disconnected Habitat Area](StrandingRisk#calculating-disconnected-area) for more.
- `disconnected_area.xlsx`: a spreadsheet containing plotted data of discharge vs disconnected area.
- `disconnected_habitat_specieslifestage.tif`: a raster showing all wetted areas which become disconnected in the applied flow reduction scenario, weighted by the combined habitat suitability index (cHSI) at Q<sub>high</sub> (before the flow reduction occurs). See [Calculating Disconnected Habitat Area](StrandingRisk#calculating-disconnected-area) for more.
- `Q_disconnect.tif`: a raster showing the highest model discharge for which areas are disconnected from the mainstem at Q<sub>low</sub>. Locations that are not disconnected at any modeled discharge are assigned a value of zero. Thus, this map indicates locations and discharges below which stranding risks may occur. See [Determining Q<sub>disconnect</sub>](StrandingRisk#determining-qdisconnect) for more.
- `disc_freq.tif`: a raster showing the historical frequency for which each area becomes disconnected, in number of times per year, confined to the season of interest for the analyzed species/lifestage. See [Disconnection Frequencies](#disc-freq) for more.
- `ramping_rate_time.tif`: a raster showing the estimated ramping rate before disconnection occurs. See [Estimating Ramping Rates](#ramping-rates) for more.

***

# Defining Travel Thresholds

***

Whether or not areas are considered to be connected/navigable for a given fish species/lifestage is dependent upon travel thresholds that are defined in the `Fish.xlsx` workbook (see [SHArC](SHArC) for more details). These include a minimum swimming depth and maximum swimming speed. To view/modify the species/lifestage specific travel thresholds, use the drop-down menu: "Select Physical Habitat" --> "DEFINE FISH SPECIES".

***

# Methodology<a name="methods"></a>

***

## Interpolating Hydraulic Rasters

The analysis begins by performing an interpolation of the water surface elevation across the extent of the DEM. This step is taken in order to approximate how the water surface extends across floodplain areas, thus identifying the presence of disconnected pools that would not be captured by steady-state hydrodynamic model outputs. The interpolation is performed for each discharge as follows:

- The water depth raster is added to the DEM elevation to produce a water surface elevation (WSE) raster.
- the WSE is interpolated across the DEM extent using an Inverse Distance Weighted (IDW) interpolation scheme on the 12 nearest neighbors.
- The DEM is subtracted from the interpolated WSE raster to produce an interpolated depth raster. Only positive values are saved (negative values indicate an estimated depth to groundwater).
- Interpolated velocity and velocity angle rasters are created, where velocity is set to zero in the newly interpolated areas.
- Interpolated rasters are stored in `StrandingRisk\Condition_name\h_interp`, `StrandingRisk\Condition_name\u_interp`, `StrandingRisk\Condition_name\va_interp`. All interpolated rasters are saved with a corresponding .info.txt file which records the interpolation method and input rasters used in its creation.

The available interpolation methods are:

- `IDW`: Inverse distance weighted interpolation. Each null cell in the low flow depth raster is assigned a weighted average of its 12 nearest neighbors. Each weight is inversely proportional to the second power of the distance between the interpolated cell and its neighbor. Thus, the closest neighbors to an interpolated cell receive the largest weights. This method was found to have the best balance of computational speed and accuracy when tested via cross-validation.
- `Kriging`: Ordinary Kriging interpolation. This method also uses a weighted average of the 12 nearest neighbors, but weights are calculated using a semi-variogram, which describes the variance of the input data set as a function of the distance between points. A spherical functional form is also assumed for the fitted semi-variogram. Kriging is the most accurate interpolation method if certain assumptions are met regarding normality and stationarity of error terms. However, it is also the most computationally expensive method. This method was found to have comparable accuracy compared to IDW, but with significantly higher computational costs.
- `Nearest Neighbor`: The simplest method, which sets the water surface elevation of each null cell to that of the nearest neighboring cell.

## Escape Route Calculations<a name="calc-escape"></a>

The "shortest escape route" output maps (stored in the `shortest_paths\` output directory) show the length/cost of the shortest/least-cost path from each pixel back into the mainstem of the river channel at Q<sub>low</sub>, accounting for both depth and velocity travel thresholds. In this context, the mainstem is defined as the largest continuous portion of interpolated wetted area deeper than the minimum swimming depth at Q<sub>low</sub>. Conceptually, the shortest escape route to the mainstem is found from each starting pixel as follows:

- If the starting pixel is already in the mainstem, it assigned a default value of zero. Otherwise, look at all wetted pixels adjacent to the starting pixel.
- Apply depth and velocity travel criteria (see below).
- If both the depth and velocity travel criteria are satisfied, the fish is considered to be able to move from the current pixel to the neighbor. An associated cost of traveling to the neighboring cell can also be computed.
- Apply this method iteratively to each reachable neighbor. The path which reaches a cell in the mainstem with the smallest total cost is the least-cost path to the mainstem.

***

### Applying Depth and Velocity Travel Criteria<a name="hu-criteria"></a>

The applied depth and velocity thresholds parameterize the ability of the target fish to travel throughout the river corridor. The criteria to satisfy for travel from cell A to adjacent cell B are defined by three criteria:
- Domain criterion: both cells A and B are wetted.
- Depth criterion: depth at cell B is > d_{min}.
- Velocity criterion: the fish can overcome the current at cell A to reach cell B traveling at v_f

![connect_vel](https://github.com/RiverArchitect/Media/raw/master/images/connect_vel_condition.png)

From the center of each cell, the area is divided into 8 octants corresponding to the 8 neighboring cells, with each octant centered on the direction to its neighboring cell and spanning 45°. If it is possible to add the water velocity vector (𝑣<sub>𝑤</sub>) to a vector with the magnitude of the maximum swimming speed (𝑣<sub>𝑓</sub>) to yield a vector (𝑉) falling within an octant, then the velocity threshold criteria is satisfied for travel to the corresponding neighboring cell. A specific example is shown in this diagram where the resultant velocity vector 𝑉 points into the upper quadrant, thus the velocity threshold criteria is satisfied for travel to the upper neighbor. Octants are colored blue/red based on whether the criteria is/is not satisfied for travel in that direction.

***

Least cost path calculations are implemented in a computationally efficient way by constructing a weighted, directed adjacency graph (stored as a dictionary) and then dynamically traversing the graph working outwards from the mainstem to find shortest path lengths using Dijkstra's algorithm (see explanation below):

![connect_graph](https://github.com/RiverArchitect/Media/raw/master/images/connect_graph.png)

Applying the travel criteria at each cell yields a set of neighboring cells for which travel is possible. Each cell which can reach other cells or be reached is represented as a vertex of the graph. Reachability of neighboring vertices is represented by edges connecting the vertices, with an arrow symbol indicating the direction of possible travel (edges without arrows indicate travel is possible in both directions). For each edge, an associated cost of traveling along the edge is calculated, yielding a weighted digraph to represent possible fish travel and the associated costs. The least-cost path leading from each vertex to any of the vertices in the target area (corresponding to river mainstem at a lower discharge) is then computed and the path length/cost is stored as a value in the output raster at the location of the starting vertex. Here the target vertices are shown in gold and the least-cost path from point A is shown in blue (where the cost function applied is Euclidean distance).

***

## Calculating Disconnected Habitat Area<a name="calc-habitat"></a>

Even if there is wetted area connecting two locations, they may not be considered connected in the context of fish passage. This is because low water depths or high velocities may effectively act as "hydraulic barriers", limiting fish mobility. The applied Physical Habitat contains threshold values for the minimum swimming depth and maximum swimming speed. After escape routes are calculated for a given discharge, the resultant path length raster shows which areas are able to reach the river mainstem for the given hydraulic conditions and biological limitations. Wetted areas in the corresponding interpolated depth raster for which a least-cost path cannot be calculated are considered to be disconnected areas. These disconnected areas are then cropped within the wetted area at Q<sub>high</sub> (not interpolated), as floodplains outside the Q<sub>high</sub> wetted area are assumed to not be active for the simulated flow reduction. Resultant disconnected areas are saved to a shapefile for each discharge in the `disc_areas` output directory.

Once disconnected areas have been calculated, they are weighted by the combined habitat suitability index (cHSI) at Q<sub>high</sub> for the target Physical Habitat. The resultant raster is stored as `disconnected_habitat` in the output directory. Since cHSI serves as a proxy for fish density in habitat-limited environments, the cHSI at Q<sub>high</sub> in areas that become disconnected by the flow reduction serves as a spatially-distributed stranding risk metric.

***

## Determining Q<sub>disconnect</sub>

The `Q_disconnect` map outputs provide estimates of the discharges at which wetted areas become disconnected from the mainstem of the river channel. Estimating these discharges is done as follows:

- Assign all pixels wetted at the highest discharge a default value of zero.
- Iterating over discharges in ascending order, pixels within disconnected area polygons are assigned a value of the corresponding discharge.
- The resultant raster is saved as the `Q_disconnect.tif` map output.

Note that the default value of zero indicates pixels wetted at the highest discharge but not present within any of the disconnected area polygons. Other values indicate the highest modeled discharge for which the pixel is disconnected from the channel mainstem.

![Q_disc_ex](https://github.com/RiverArchitect/Media/raw/master/images/Q_disc_example.png)

***

## Disconnection Frequencies <a name="disc-freq"></a>

For each disconnected area, `Q_disconnect` can be combined with the hydrologic flow record in order to calculate the average number of potential stranding events occurring per year. This is generated by computing the total number of times mean daily flow drops below `Q_disconnect` during the season of interest for the applied species/lifestage ([Physical Habitat](SHArC#hefish)) and dividing by the number of years on record.

A `disc_freq` output map will be produced provided that flows have already been analyzed ([Make flow duration curves](Signposts#ana-flows)) for the applied [Condition](Signposts#conditions) and [Physical Habitat](SHArC#hefish).

***

## Estimating Ramping Rates <a name="ramping-rates"></a>

Ramping rates are estimated by applying the following assumptions:

- the flow reduction scenario is characterized by a linearly downramping hydrograph from Q<sub>high</sub> to Q<sub>low</sub> over the input time period
- Downstream attenuation of the hydrograph is not considered

Ramping rates are estimated via linear approximation, using the difference in depths between model discharges prior to disconnection.

The ramping rate output raster is stored as `ramping_rate_###min.tif`, where `###` corresponds to the input time period over which the downramping occurs.

***

# References

Travel thresholds used to define Physical Habitats in `Fish.xlsx` can be estimated from the following sources:

[Bell, M. C. (1991). Fisheries Handbook of Engineering Requirements and Biological Criteria (3 ed.). Portland, Oregon.](https://www.fs.fed.us/biology/nsaec/fishxing/fplibrary/Bell_1991_Fisheries_handbook_of_engineering_requirements_and.pdf)

[CDFG. (2012). Standard Operating Procedure for Critical Riffle Analysis for Fish Passage in California DFG-IFP-001, updated February 2013. California Department of Fish and Game, DFG-IFP-00(September), 1–25.](https://nrm.dfg.ca.gov/FileHandler.ashx?DocumentID=150377)

[Katopodis, C., & Gervais, R. (2016). Fish swimming performance database and analyses. DFO Can. Sci. Advis. Sec. Res. Doc. 2016/002.](https://waves-vagues.dfo-mpo.gc.ca/Library/362248.pdf)

[U.S. Forest Service FishXing Data Table](http://www.fsl.orst.edu/geowater/FX3/help/SwimData/swimtable.htm) (various sources)
