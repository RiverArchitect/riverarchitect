---
redirect_from: "/"
---


River Architect Wiki
====================
<details><summary> Table of Contents </summary><p>
  <ol>
  <li><a href="Installation">Installation</a>
    <ul>
      <li><a href="Installation#started">Install, update and launch <em>River Architect</em></a></li>
      <li><a href="Installation#structure">Program file structure</a></li>
      <li><a href="Installation#req">Requirements</a></li>
      <li><a href="Installation#logs">Logfiles</a></li>
    </ul></li>
  <li><a href="Signposts">Get started, terminology and signposts</a>
    <ul>
      <li><a href="Signposts#getstarted">Welcome and <em>Condition</em> creation</a>
      <ul>
        <li><a href="Signposts#new-condition">Create <em>Condition</em>s</a></li>
        <li><a href="Signposts#ana-flows">Analyze Flows</a></li>
        <li><a href="Signposts#inpfile">Input definition files</a></li>
        <li><a href="Signposts#inmaps">Map extent definition files</a></li>
      </ul></li>
      <li><a href="Signposts#terms">Geofile conventions</a></li>
      <li><a href="Signposts#inputs">Prepare input Rasters</a></li>
    </ul></li>
  <li>Modules
  <ul>
  <li>Lifespans
  <ul>	  
  <li>The <a href="LifespanDesign">Lifespan Design</a> module maps sustainable <a href="River-design-features">features</a>
  <ul>
    <li><a href="LifespanDesign-parameters">Parameter hypothesis</a></li>
    <li><a href="River-design-features">River design and restoration <strong>features</strong></a></li>
    <li><a href="Signposts#inpfile">Input definition files</a></li>
    <li><a href="LifespanDesign-code">Code extension and modification</a></li>
  </ul></li>
  <li>The <a href="MaxLifespan">MaxLifespan</a> module identifies best-performing <a href="River-design-features">features</a>
  <ul>
    <li><a href="MaxLifespan#actgui">Quick GUIde</a></li>
    <li><a href="MaxLifespan#actprin">Working principles</a></li>
    <li><a href="MaxLifespan#actcode">Code extension and modification</a></li>
  </ul></li>
  </ul></li>
  <li>Morphology (Terraforming)
  <ul>
    <li><a href="RiverReaches">River <strong>Reach</strong> definitions</a></li>
    <li><a href="ModifyTerrain">Modify Terrain</a>
    <ul>
      <li><a href="ModifyTerrain#mtgui">Quick GUIde</a></li>
      <li><a href="ModifyTerrain#mtdemmod">Threshold-based Grading or Widening (Broaden)</a></li>
      <li><a href="RiverBuilder">River Builder</a></li>
      <li><a href="ModifyTerrain#mtprin">Working principle</a></li>
      <li><a href="ModifyTerrain#mtcode">Code extension and modification</a></li>
    </ul></li>
    <li><a href="VolumeAssessment">Volume Assessment</a>
    <ul>
      <li><a href="VolumeAssessment#gui">Quick GUIde</a></li>
      <li><a href="VolumeAssessment#vaprin">Working principle</a></li>
      <li><a href="VolumeAssessment#vacode">Set level of detection</a></li>
    </ul></li>
  </ul></li>
  <li>Ecohydraulics
  <ul>
    <li>Assess habitat area with the <a href="SHArC">SHArC</a> module
    <ul>
      <li><a href="SHArC#hegui">Quick GUIde</a></li>
      <li><a href="SHArC#hefish">Define <strong>Physical Habitats</strong> for <strong>Fish</strong></a></li>
      <li><a href="SHArC#herunSHArea"><strong>SHArea</strong> calculation</a></li>
      <li><a href="SHArC-working-principles#heprin">Working principles</a></li>
    </ul></li>
    <li><a href="SHArC#hefish">Predefined <strong>Fish</strong> (Physical Habitats)</a></li>
    <li><a href="aqua-modification#hecode">Edit Fish (Physical Habitats) template</a></li>
    <li><a href="StrandingRisk">Stranding Risk</a>
    <ul>
      <li><a href="StrandingRisk#intro">Introduction</a></li>
      <li><a href="StrandingRisk#guide">Quick GUIde</a></li>
    </ul></li>
  </ul></li>

  <li>The <a href="ProjectMaker">Projekt Maker</a> module generates cost-benefit plans and tables of river designs
  <ul>
    <li><a href="ProjectMaker#pmquick">Quick GUIde</a></li>
    <li><a href="ProjectMaker#pmcq"><strong>Cost</strong> quantity assessment</a></li>
    <li><a href="ProjectMaker#pmSHArea">Ecological (habitat) benefit assessment (Calculate <strong>SHArea</strong>)</a></li>
  </ul></li>
  </ul></li>  

  <li><a href="Tools">Tools</a> contain beta-version routines (under development)</li>

  <li><a href="FAQ">FAQ</a></li>

  <li><a href="Troubleshooting">Troubleshooting and Error message handling</a>
  <ul>
    <li><a href="Troubleshooting#issues">Known issues</a></li>
    <li><a href="Troubleshooting#howto">How to troubleshoot</a></li>
    <li><a href="Troubleshooting#error-messages">Error messages</a></li>
    <li><a href="Troubleshooting#warning-messages">Warning messages</a></li>
  </ul></li>

  </ol>

</p></details>

***
**Please refer to the [installation guide](Installation#started) for [first-time installation](Installation#started), [update](Installation#update_ra), and [launch](Installation#launch_ra) assistance.**

***

***River Architect* is an [<font color="blue">open-access, peer-reviewed (Journal SoftwareX)</font>](https://doi.org/10.1016/j.softx.2020.100438) and Python3-based software for the GIS-based planning of habitat enhancing river design features regarding their lifespans, parametric characteristics, optimum placement in the terrain, and ecological benefits. The main graphical user interface (GUI) provides modules for generating lifespan and design maps, terrain modification (terraforming), assessment of digital elevation models (DEM), habitat assets including fish stranding risk, and project cost-benefits.**

*River Architect* invites to analyses and modifications of the longevity and ecological quality of riverscapes. Different planning bases ("conditions") can be easily created using an introductory module called **[GetStarted](Signposts#getstarted)**. **Lifespan**, **Morphology (Terraforming)** and **Ecohydraulic** assessments can then be created based on the *Conditions*, including the creation of project plans and cost tables with a **Project Maker** module.

**[Lifespan](LifespanDesign)** maps indicate the expected longevity of restoration features as a function of terrain change, morphological characteristics, and 2D hydrodynamic modeling results. **Design maps** are a side product of [lifespan and design mapping](LifespanDesign) and indicate required feature dimensions for stability, such as the minimum required size of angular boulders to avoid their mobilization during floods (more information in [Schwindt et al.2019][11]). **Best lifespan maps** result from the comparison of lifespan and design maps of multiple restoration features and assign features with the highest longevity to each pixel of a raster. Thus, the **[Max Lifespan](MaxLifespan)** module assess optimum features as a function of highest lifespans among comparable feature groups such as terraforming or vegetation planting species.

**Morphology (Terraforming)** includes routines to **[Modify Terrain](ModifyTerrain)** for river restoration purposes. Currently, two terrain modification algorithms are implemented: (1) Threshold value-based terrain modifications in terms of [grading](River-design-features#grading) or [widening / broaden rivers](River-design-features#berms) for riparian forest establishment; and (2) [River Builder](RiverBuilder) for the creation of synthetic river valley. A **[Volume Assessment](VolumeAssessment)** module can compare an original (pre-project or pre-terraforming application) and a modified DEM (\"with implementation\" or post-feature application) to determine required earth movement (terraforming volumes) works.

**Ecohydraulics** assessments include the evaluation of the ecohydraulic state and connectivity of riverscapes. The **[Habitat Area](SHArC)** (Seasonal Habitat Area Calculator) module applies user-defined flows (discharges) for the spatial evaluation of the habitat suitability index (*HSI*) in terms of Seasonal Habitat Area (SHArea). The hydraulic habitat suitability results from 2D hydrodynamic numerical model outputs of flow depth and velocity. Also, a  \"cover\" option can be used to assess ecohydraulic effects of cobble, boulder, vegetation, and streamwood. The **[Stranding Risk](StrandingRisk)** module provides insights into the connection of wetted areas on floodplains and how these may be improved to enhance the survivorship of fry / juvenile fish.

The **[Project Maker](ProjectMaker)** module creates preliminary construction plans and evaluates the costs for gain in usable habitat for target fish species and lifestages. A unit cost workbook provides relevant costs and the gain in usable habitat area results from the *SHArC* module.

A set of **[Tools](Tools)** provides *Python* console scripts that are under development and will be implemented in future versions of the *River Architect* GUI.

*River Architect* represents a comprehensive tool for state-of-the-art planning of ecologic river modifications. The integrated application of *River Architect* to habitat enhancing project planning is illustrated in the following flowchart. 
The modules and tool-scripts can also be individually applied for other purposes than suggested in the flowchart.

![flowchart](https://github.com/RiverArchitect/Media/raw/master/images/flowchart.png)

The procedure of project design following the flowchart involves the following steps:

1.  Generate a terrain elevation model (DEM).

2.  Determine relevant discharges for 2D hydrodynamic modeling:

    -   At least three annual discharges describing the \"most of the time\" - situation of the considered river for habitat evaluation assessments. *River Architect*'s *Tools* contain scripts for generating flow duration curves from gaging station data.

    -   At least three flood discharges against which potential [restoration features](River-design-features) have to withstand (determine lifespan intersects).

3.  Run a 2D hydrodynamic model (steady) with all determined discharges to generate hydraulic snap-shots of the river.

4.  Create a [Condition](Signposts#conditions) using the [GetStarted](Signposts#getstarted) module. The *Condition* should include *GeoTIFFs* of the initial (existing or pre-project) river state:

    -   Detrended digital elevation model (DEM);

    -   Flow depth and velocity for multiple discharges Rasters from 2D hydrodynamic modeling (see [Signposts](Signposts#conditions));

    -   Substrate map (`dmean` for metric or `dmean_ft` for U.S. customary units); relevant methods are described in [Detert et al. (2018)][12]; [Stähly et al. (2017)][13]; and [Jackson et al. (2013)];

    -   Datasets that can be used to assess design feature stability, such as [side channel design criteria](River-design-features#sidechnl);

    -   Topographic change Rasters (Topographic Change Detection or DEM differencing according to [Wyrick and Pasternack 2016][15]);

    -   Depth to water table Raster (`d2w`);

    -   Morphological unit Raster (see [Wyrick and Pasternack (2014)][16]).

5.  Apply the [*LifespanDesign*](LifespanDesign) module to [framework (terraforming) features](River-design-features#featoverview).

6.  Lifespan and Design maps, as well as expert assessment, serve for the identification of relevant [framework (terraforming) features](River-design-features#featoverview).

7.  Iterative terraforming (if relevant):

    -   Use the [*ModifyTerrain*](ModifyTerrain) module for creating synthetic river valley with [River Builder](RiverBuilder); or apply threshold value-based terrain [grading](River-design-features#grading) or [broadening of the river bed](River-design-features#berms). *Please note that both routines require post-processing with computer-aided design (translation into real-world coordinates and/or edge smoothing).*

    -   Re-compile the flow depth and velocity maps (re-run 2D model) with the modified DEM.

    -   Verify the suitability of the modified DEM (e.g., barrier height to ensure flood safety and habitat suitability with the <a href="SHArC">SHArC</a> module); if the verification show weaknesses adapt the terraforming and re-compile the flow depth and velocity maps until terraforming is satisfactory.

    -   Use the *<a href="VolumeAssessment">VolumeAssessment</a>* module (Morphology tab) to compare pre- (initial) and post-project (modified) DEMs for determining required excavation and fill volumes.

8.  Apply the [*LifespanDesign*](LifespanDesign) module to [vegetation plantings](River-design-features#plants) and [(other) bioengineering features](River-design-features#bioeng) based on the terraformed DEM (or the original / initial DEM if no terraforming applies).

9.  Use the [*MaxLifespan*](MaxLifespan) module to identify best performing (highest lifespan) [vegetation plantings](River-design-features#plants) and [(other) bioengineering features](River-design-features#bioeng).

10. If the soils are too coarse (i.e., the capillarity is not high enough to enable plant root growth), apply the connectivity feature ["incorporate fine sediment in soils"](River-design-features#finesed).

11. If gravel augmentation methods are applicable: Consecutively apply the [*LifespanDesign*](LifespanDesign) and [*MaxLifespan*](MaxLifespan) modules to [connectivity features](River-design-features#featoverview) to foster self-sustaining, artificially created ecomorphological patterns within the terraforming process.<br/>
    If gravel is added in-stream, re-run the numerical model for the assessment of [gravel stability](River-design-features#rocks) with the [*LifespanDesign*](LifespanDesign) module and the combined habitat suitability with the [*SHArC*][6] module to compare the [**S**easonal **H**abitat **Area** (**SHArea**)](SHArC#herunSHArea) before and after enhancement of [Physical Habitats for target fish species (lifestages)](SHArC#hefish).

12. Use the [*SHArC*][6] to assess the *"existing"* (pre-project) and *"with implementation"* (post-project) habitat suitability in terms of annually usable habitat area (SHArea).

13. Use the *<a href="ProjectMaker">ProjectMaker</a>* to calculate costs, the net gain in SHArea, and their ratio as a metric defining the project trade-off.

The working principles of the [*LifespanDesign*](LifespanDesign), [*MaxLifespan*](MaxLifespan), [*ModifyTerrain*](ModifyTerrain), *<a href="VolumeAssessment">VolumeAssessment</a>*, [*SHArC*][6], and [*ProjectMaker*][7] modules are explained on their own Wiki pages. The differentiation between [terraforming (framework)](River-design-features#featoverview), [vegetation plantings and other bioengineering](River-design-features#featoverview), and [connectivity features](River-design-features#featoverview) is described within the [LifespanDesign Wiki](River-design-features). The <a href="Installation">Installation</a> Wiki pages describe the propper installation, file organization and environment of *River Architect*.

***

[1]: https://github.com/RiverArchitect/RA_wiki/Installation
[2]: https://github.com/RiverArchitect/RA_wiki/Signposts
[3]: https://github.com/RiverArchitect/RA_wiki/LifespanDesign
[4]: https://github.com/RiverArchitect/RA_wiki/MaxLifespan
[5]: https://github.com/RiverArchitect/RA_wiki/ModifyTerrain
[6]: https://github.com/RiverArchitect/RA_wiki/SHArC
[60]: https://github.com/RiverArchitect/RA_wiki/EcoMorphology
[7]: https://github.com/RiverArchitect/RA_wiki/ProjectMaker
[8]: https://github.com/RiverArchitect/RA_wiki/Tools
[9]: https://github.com/RiverArchitect/RA_wiki/FAQ
[10]: https://github.com/RiverArchitect/RA_wiki/Troubleshooting
[11]: https://www.sciencedirect.com/science/article/pii/S0301479718312751
[12]: http://www.sciencedirect.com/science/article/pii/S1001627918300350
[13]: https://ascelibrary.org/doi/abs/10.1061/%28ASCE%29HY.1943-7900.0001286
[14]: http://www.yubaaccordrmt.com/Annual%20Reports/Mapping%20and%20Modeling/LYRsubstrate20131218.pdf
[15]: https://onlinelibrary.wiley.com/doi/full/10.1002/esp.3854
[16]: http://www.sciencedirect.com/science/article/pii/S0169555X14000099
