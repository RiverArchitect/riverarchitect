River Architect Wiki
====================

--------------

**Please refer to the Installation section to learn how to install, update, and launch River Architect.**

--------------

**River Architect is an `open-access, peer-reviewed (Journal
SoftwareX) <https://doi.org/10.1016/j.softx.2020.100438>`__ and
Python3-based software for the GIS-based planning of habitat enhancing
river design features regarding their lifespans, parametric
characteristics, optimum placement in the terrain, and ecological
benefits. The main graphical user interface (GUI) provides modules for
generating lifespan and design maps, terrain modification
(terraforming), assessment of digital elevation models (DEM), habitat
assets including fish stranding risk, and project cost-benefits.**

*River Architect* invites to analyses and modifications of the longevity
and ecological quality of riverscapes. Different planning bases
(“conditions”) can be easily created using an introductory module called
`GetStarted <Signposts#getstarted>`__. **Lifespan**, **Morphology
(Terraforming)** and **Ecohydraulic** assessments can then be created
based on the *Conditions*, including the creation of project plans and
cost tables with a **Project Maker** module.

`Lifespan <LifespanDesign>`__ maps indicate the expected longevity of
restoration features as a function of terrain change, morphological
characteristics, and 2D hydrodynamic modeling results. **Design maps**
are a side product of `lifespan and design mapping <LifespanDesign>`__
and indicate required feature dimensions for stability, such as the
minimum required size of angular boulders to avoid their mobilization
during floods (more information in `Schwindt et
al.2019 <https://www.sciencedirect.com/science/article/pii/S0301479718312751>`__).
**Best lifespan maps** result from the comparison of lifespan and design
maps of multiple restoration features and assign features with the
highest longevity to each pixel of a raster. Thus, the `Max
Lifespan <MaxLifespan>`__ module assess optimum features as a function
of highest lifespans among comparable feature groups such as
terraforming or vegetation planting species.

**Morphology (Terraforming)** includes routines to `Modify
Terrain <ModifyTerrain>`__ for river restoration purposes. Currently,
two terrain modification algorithms are implemented: (1) Threshold
value-based terrain modifications in terms of
`grading <River-design-features#grading>`__ or `widening / broaden
rivers <River-design-features#berms>`__ for riparian forest
establishment; and (2) `River Builder <RiverBuilder>`__ for the creation
of synthetic river valley. A `Volume Assessment <VolumeAssessment>`__
module can compare an original (pre-project or pre-terraforming
application) and a modified DEM ("with implementation" or post-feature
application) to determine required earth movement (terraforming volumes)
works.

**Ecohydraulics** assessments include the evaluation of the ecohydraulic
state and connectivity of riverscapes. The `Habitat Area <SHArC>`__
(Seasonal Habitat Area Calculator) module applies user-defined flows
(discharges) for the spatial evaluation of the habitat suitability index
(*HSI*) in terms of Seasonal Habitat Area (SHArea). The hydraulic
habitat suitability results from 2D hydrodynamic numerical model outputs
of flow depth and velocity. Also, a "cover" option can be used to assess
ecohydraulic effects of cobble, boulder, vegetation, and streamwood. The
`Stranding Risk <StrandingRisk>`__ module provides insights into the
connection of wetted areas on floodplains and how these may be improved
to enhance the survivorship of fry / juvenile fish.

The `Project Maker <ProjectMaker>`__ module creates preliminary
construction plans and evaluates the costs for gain in usable habitat
for target fish species and lifestages. A unit cost workbook provides
relevant costs and the gain in usable habitat area results from the
*SHArC* module.

A set of `Tools <Tools>`__ provides *Python* console scripts that are
under development and will be implemented in future versions of the
*River Architect* GUI.

*River Architect* represents a comprehensive tool for state-of-the-art
planning of ecologic river modifications. The integrated application of
*River Architect* to habitat enhancing project planning is illustrated
in the following flowchart. The modules and tool-scripts can also be
individually applied for other purposes than suggested in the flowchart.

.. figure:: https://github.com/RiverArchitect/Media/raw/master/images/flowchart.png
   :alt: flowchart

   flowchart

The procedure of project design following the flowchart involves the
following steps:

1.  Generate a terrain elevation model (DEM).

2.  Determine relevant discharges for 2D hydrodynamic modeling:

    -  At least three annual discharges describing the "most of the
       time" - situation of the considered river for habitat evaluation
       assessments. *River Architect*\ ’s *Tools* contain scripts for
       generating flow duration curves from gaging station data.

    -  At least three flood discharges against which potential
       `restoration features <River-design-features>`__ have to
       withstand (determine lifespan intersects).

3.  Run a 2D hydrodynamic model (steady) with all determined discharges
    to generate hydraulic snap-shots of the river.

4.  Create a `Condition <Signposts#conditions>`__ using the
    `GetStarted <Signposts#getstarted>`__ module. The *Condition* should
    include *GeoTIFFs* of the initial (existing or pre-project) river
    state:

    -  Detrended digital elevation model (DEM);

    -  Flow depth and velocity for multiple discharges Rasters from 2D
       hydrodynamic modeling (see `Signposts <Signposts#conditions>`__);

    -  Substrate map (``dmean`` for metric or ``dmean_ft`` for U.S.
       customary units); relevant methods are described in `Detert et
       al. (2018) <http://www.sciencedirect.com/science/article/pii/S1001627918300350>`__;
       `Stähly et
       al. (2017) <https://ascelibrary.org/doi/abs/10.1061/%28ASCE%29HY.1943-7900.0001286>`__;
       and [Jackson et al. (2013)];

    -  Datasets that can be used to assess design feature stability,
       such as `side channel design
       criteria <River-design-features#sidechnl>`__;

    -  Topographic change Rasters (Topographic Change Detection or DEM
       differencing according to `Wyrick and Pasternack
       2016 <https://onlinelibrary.wiley.com/doi/full/10.1002/esp.3854>`__);

    -  Depth to water table Raster (``d2w``);

    -  Morphological unit Raster (see `Wyrick and Pasternack
       (2014) <http://www.sciencedirect.com/science/article/pii/S0169555X14000099>`__).

5.  Apply the `LifespanDesign <LifespanDesign>`__ module to `framework
    (terraforming) features <River-design-features#featoverview>`__.

6.  Lifespan and Design maps, as well as expert assessment, serve for
    the identification of relevant `framework (terraforming)
    features <River-design-features#featoverview>`__.

7.  Iterative terraforming (if relevant):

    -  Use the `ModifyTerrain <ModifyTerrain>`__ module for creating
       synthetic river valley with `River Builder <RiverBuilder>`__; or
       apply threshold value-based terrain
       `grading <River-design-features#grading>`__ or `broadening of the
       river bed <River-design-features#berms>`__. *Please note that
       both routines require post-processing with computer-aided design
       (translation into real-world coordinates and/or edge smoothing).*

    -  Re-compile the flow depth and velocity maps (re-run 2D model)
       with the modified DEM.

    -  Verify the suitability of the modified DEM (e.g., barrier height
       to ensure flood safety and habitat suitability with the SHArC
       module); if the verification show weaknesses adapt the
       terraforming and re-compile the flow depth and velocity maps
       until terraforming is satisfactory.

    -  Use the *VolumeAssessment* module (Morphology tab) to compare
       pre- (initial) and post-project (modified) DEMs for determining
       required excavation and fill volumes.

8.  Apply the `LifespanDesign <LifespanDesign>`__ module to `vegetation
    plantings <River-design-features#plants>`__ and `(other)
    bioengineering features <River-design-features#bioeng>`__ based on
    the terraformed DEM (or the original / initial DEM if no
    terraforming applies).

9.  Use the `MaxLifespan <MaxLifespan>`__ module to identify best
    performing (highest lifespan) `vegetation
    plantings <River-design-features#plants>`__ and `(other)
    bioengineering features <River-design-features#bioeng>`__.

10. If the soils are too coarse (i.e., the capillarity is not high
    enough to enable plant root growth), apply the connectivity feature
    `“incorporate fine sediment in
    soils” <River-design-features#finesed>`__.

11. If gravel augmentation methods are applicable: Consecutively apply
    the `LifespanDesign <LifespanDesign>`__ and
    `MaxLifespan <MaxLifespan>`__ modules to `connectivity
    features <River-design-features#featoverview>`__ to foster
    self-sustaining, artificially created ecomorphological patterns
    within the terraforming process. If gravel is added in-stream,
    re-run the numerical model for the assessment of `gravel
    stability <River-design-features#rocks>`__ with the
    `LifespanDesign <LifespanDesign>`__ module and the combined habitat
    suitability with the
    `SHArC <https://github.com/RiverArchitect/RA_wiki/SHArC>`__ module
    to compare the `S\ easonal H\ abitat Area
    (SHArea) <SHArC#herunSHArea>`__ before and after enhancement of
    `Physical Habitats for target fish species
    (lifestages) <SHArC#hefish>`__.

12. Use the `SHArC <https://github.com/RiverArchitect/RA_wiki/SHArC>`__
    to assess the *“existing”* (pre-project) and *“with implementation”*
    (post-project) habitat suitability in terms of annually usable
    habitat area (SHArea).

13. Use the *ProjectMaker* to calculate costs, the net gain in SHArea,
    and their ratio as a metric defining the project trade-off.

The working principles of the `LifespanDesign <LifespanDesign>`__,
`MaxLifespan <MaxLifespan>`__, `ModifyTerrain <ModifyTerrain>`__,
*VolumeAssessment*,
`SHArC <https://github.com/RiverArchitect/RA_wiki/SHArC>`__, and
`ProjectMaker <https://github.com/RiverArchitect/RA_wiki/ProjectMaker>`__
modules are explained on their own Wiki pages. The differentiation
between `terraforming
(framework) <River-design-features#featoverview>`__, `vegetation
plantings and other
bioengineering <River-design-features#featoverview>`__, and
`connectivity features <River-design-features#featoverview>`__ is
described within the `LifespanDesign Wiki <River-design-features>`__.
The Installation Wiki pages describe the proper installation, file
organization and environment of *River Architect*.

--------------

.. toctree::
  :hidden:

  Home <self>
  Installation <wiki/Installation>
  Signposts <wiki/Signposts>
  Lifespans <wiki/LifespanDesign>
  Maximum Lifespans <wiki/MaxLifespan>
  Morphology (Reach Definition) <wiki/RiverReaches>
  Morphology (Terraforming) <wiki/ModifyTerrain>
  Morphology (River Builder) <wiki/RiverBuilder>
  Morphology (Volume Assessment) <wiki/VolumeAssessment>
  Ecohydraulics (Habitat Calculator) <wiki/SHarC>
  Ecohydraulics (Stranding) <wiki/StrandingRisk>
  Project Maker <wiki/ProjectMaker>
  Auxiliary Tools <wiki/Tools>
  Troubleshooting <wiki/Troubleshooting>
  Acknowledgment and Funding <wiki/Acknowledgment>
  Disclaimer and License <wiki/Disclaimer>
  Developers <wiki/DevModule>
