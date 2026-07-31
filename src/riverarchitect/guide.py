"""The Live Guide: a worked example that runs on the bundled sample data.

River Architect's modules chain together - a lifespan map needs a detrended DEM and a
depth-to-water-table raster, and those have to be built first. Reading that in the
documentation is one thing; doing it is another, and the step people get stuck on is the
first one, because a condition that is not prepared produces either an error or, worse, an
empty map that looks like an answer.

This module holds that walkthrough as **data**: an ordered tuple of :class:`GuideStep`,
each naming the tab it belongs to, the settings to enter and what the result should look
like. Both front ends render the same tuple, so the guide cannot say one thing in the Qt
window and another in the tkinter one, and a test can check that the tabs it names exist.

The reach is ``2100_sample``, a real gravel-cobble reach in U.S. customary units that ships
in ``sample-data/`` of a source clone. :func:`sample_data_dir` finds it;
:func:`activate_sample_data` points the project home at it.
"""

import os

from . import config

__all__ = ["GuideStep", "STEPS", "TITLE", "CONDITION", "DOCS_URL",
           "sample_data_dir", "activate_sample_data", "sample_data_status", "as_text"]

#: Title of the guide, shown in the Help menu and as the window title.
TITLE = "Live Guide: Example"

#: The condition the guide works on.
CONDITION = "2100_sample"

#: Where the full documentation lives.
DOCS_URL = "https://riverarchitect.readthedocs.io/"


class GuideStep:
    """One step of the walkthrough.

    Args:
        key (str): short identifier, for tests and for deep links.
        title (str): heading, e.g. ``"2. Lifespan mapping"``.
        group (str): the top-level tab the step happens in, as :data:`TAB_GROUPS` names it.
        tab (str): the module tab within that group. Equal to ``group`` for a lone tab.
        body (str): the explanation, as paragraphs separated by a blank line.
        settings (tuple): ``(label, value)`` pairs to enter in the tab.
        expect (str): what the result should look like, so a reader can tell it worked.
        writes (tuple): the files the step produces, relative to the project directory.
    """

    def __init__(self, key, title, group, tab, body, settings=(), expect="", writes=()):
        self.key = key
        self.title = title
        self.group = group
        self.tab = tab
        self.body = body.strip()
        self.settings = tuple(settings)
        self.expect = expect.strip()
        self.writes = tuple(writes)

    def paragraphs(self):
        """The body split into paragraphs, for a renderer that lays them out itself."""
        return [" ".join(block.split())
                for block in self.body.split("\n\n") if block.strip()]

    def __repr__(self):
        return "GuideStep(%r)" % self.key


# --------------------------------------------------------------------- sample data

def sample_data_dir():
    """Locate the bundled ``sample-data`` directory, or return ``None``.

    It ships in a source clone, not in a wheel, so an installed copy of River Architect
    normally has no sample data and the guide says so rather than failing.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        # editable install or a run from a clone: src/riverarchitect -> repository root
        os.path.join(here, os.pardir, os.pardir, "sample-data"),
        # a layout that keeps the data beside the package
        os.path.join(here, "sample-data"),
        os.path.join(os.getcwd(), "sample-data"),
    ]
    for candidate in candidates:
        candidate = os.path.abspath(candidate)
        if os.path.isdir(os.path.join(candidate, "01_Conditions", CONDITION)):
            return candidate
    return None


def activate_sample_data():
    """Point the project home at the bundled sample data.

    Returns:
        str: the directory now in use.

    Raises:
        FileNotFoundError: when no bundled sample data can be found.
    """
    directory = sample_data_dir()
    if directory is None:
        raise FileNotFoundError(
            "no bundled sample-data directory found. It ships with a source clone of "
            "River Architect, not with an installed wheel - clone the repository, or set "
            "the project directory to your own data and follow the guide against that.")
    config.set_project_home(directory)
    return directory


def sample_data_status():
    """One line describing whether the guide can run, and against what.

    Returns:
        tuple: ``(ready, message)``.
    """
    directory = sample_data_dir()
    if directory is None:
        return False, ("No bundled sample data found. The guide still describes every "
                       "step; run it against your own condition, or clone the repository "
                       "to get sample-data/.")
    if os.path.abspath(config.project_home()) == os.path.abspath(directory):
        return True, "Project directory is the sample data: %s" % directory
    return True, ("Sample data found at %s. Use the button below to work on it."
                  % directory)


# --------------------------------------------------------------------------- steps

STEPS = (
    GuideStep(
        key="start",
        title="0. What you are about to do",
        group="Get Started",
        tab="Get Started",
        body="""
        This walkthrough runs the whole chain on 2100_sample: a real gravel-cobble reach
        in U.S. customary units, with a DEM, a mean grain size raster, a DEM of difference
        and 60 pairs of modelled flow depth and velocity rasters between 300 and 88053 cfs.

        The order matters. Every later module reads a raster that Get Started produces, so
        preparing the condition is not optional housekeeping - it is step one of the
        analysis. The chain is: prepare the condition, map feature lifespans, pick the best
        feature per cell, terraform the ground those features need, then the three
        ecohydraulic analyses - which are independent of one another but all need the
        prepared condition.

        Set the units to U.S. customary before you start (Units menu). The sample rasters
        are in feet and feet per second, and a unit mismatch does not raise an error - it
        quietly produces wrong thresholds.
        """,
        settings=(("Project directory", "sample-data/"),
                  ("Units", "U.S. customary"),
                  ("Condition", CONDITION)),
        expect="The status bar shows the sample-data directory and the condition list "
               "offers 2100_sample.",
    ),
    GuideStep(
        key="getstarted",
        title="1. Prepare the condition (Get Started)",
        group="Get Started",
        tab="Get Started",
        body="""
        Build the three terrain products the later modules read. Use 750 cfs as the
        reference discharge: it is an in-channel low flow, which is what a detrended DEM and
        a water surface should be keyed to.

        The detrended DEM is elevation above the local thalweg, which is what makes an
        elevation comparable between the upstream and downstream ends of a reach. The water
        surface product extrapolates a continuous water level out of the wetted area and
        writes wle.tif, h_interp.tif and d2w.tif - the depth to the water table is what the
        vegetation-planting features are keyed to. Morphological units classify the wetted
        area into pools, riffles, runs and the rest from depth and velocity.

        The condition already ships dem_detrend.tif, d2w.tif and mu.tif, so you can compare
        what you build against them. They agree closely (r = 0.99); the small constant
        offset is the different reference discharge, not an error.

        Then build the bed shear stress. Unlike the three above it needs no reference
        discharge - it runs over every modelled discharge and writes four rasters for each:
        ts (the dimensionless Shields stress, the quantity the feature thresholds are
        compared against), tb (u*^2), hks (relative submergence) and regime. Open a regime
        raster before trusting a stress map: it says which resistance law applied in each
        cell, and on this reach about 95 % of wet cells fall in the Rickenmann-Recking
        branch, where the single logarithmic law of the ArcGIS version did not apply.

        Build the fifth product too: analyze flows. Point it at
        00_Flows/2100_sample/flow_series_2020.csv and it writes one seasonal flow duration
        curve per species and lifestage. Habitat area is integrated over that curve, so
        without it step 5 can report usable areas but not SHArea - the single number the
        project gets judged on.
        """,
        settings=(("Condition", CONDITION),
                  ("Reference discharge", "750 cfs"),
                  ("Interpolation", "nearest"),
                  ("Daily flow record", "00_Flows/2100_sample/flow_series_2020.csv"),
                  ("Products", "detrended DEM; water surface, depth and depth to water "
                               "table; morphological units; dimensionless bed shear "
                               "stress (taux); analyze flows")),
        expect="Roughly 11 000 thalweg cells are reported, eight morphological unit types "
               "are found in the wetted area, taux is written for all 60 discharges, and "
               "14 flow duration workbooks are written.",
        writes=("01_Conditions/2100_sample/dem_detrend.tif",
                "01_Conditions/2100_sample/wle.tif",
                "01_Conditions/2100_sample/h_interp.tif",
                "01_Conditions/2100_sample/d2w.tif",
                "01_Conditions/2100_sample/mu.tif",
                "01_Conditions/2100_sample/{ts,tb,hks,regime}<Q>.tif",
                "00_Flows/2100_sample/flow_duration_<code>.xlsx"),
    ),
    GuideStep(
        key="lifespan",
        title="2. Lifespan and design mapping",
        group="Lifespan",
        tab="Lifespan Design",
        body="""
        For each restoration feature this asks, per cell: how many years is it expected to
        survive here? Every modelled discharge carries a flood return period from
        input_definitions.inp, and for every criterion the feature has a threshold for, the
        analysis finds the lowest return period at which that threshold is exceeded. Cells
        that survive every modelled flood stay NoData - their lifespan is longer than the
        largest modelled event and cannot be quantified from the data.

        Start with Angular boulders (rocks). It is the clearest case: a boulder fails when
        the flow can move a grain of the size actually present, so its lifespan map is the
        earliest flood that mobilises the bed, and its design map is the stable grain size
        at the 20-year flood. Then run all features to see the spread.

        Two results are worth reading rather than glancing at. Angular boulders map only
        about 18 sqft, because the feature is restricted to cells that scour by 3 ft or more
        and this reach barely does - without that restriction it is 66 000 sqft. And several
        features report identical areas: their hydraulic criteria differ, but at the largest
        floods every cell inside their shared depth-to-water-table band fails eventually, so
        the mapped extent is the same even though the lifespans within it are not.

        Each discharge also leaves two diagnostic rasters, hks<Q>.tif and regime<Q>.tif.
        They show the relative submergence h/k_s and which bed-resistance closure the
        dimensionless shear stress used there: 1 Rickenmann-Recking, 2 blended,
        3 Keulegan-Einstein, 0 invalid. On this reach almost every wet cell is regime 1.
        """,
        settings=(("Condition", CONDITION),
                  ("Features", "Angular boulders (rocks), then all"),
                  ("Units", "U.S. customary")),
        expect="19 features map. Streamwood covers the most ground (~332 000 sqft), "
               "Angular boulders the least. Design maps appear for backwt, rocks, gravin "
               "and gravou, and hks/regime diagnostics for every discharge.",
        writes=("Output/LifespanDesign/2100_sample/lf_<feature>.tif",
                "Output/LifespanDesign/2100_sample/ds_<feature>.tif",
                "Output/LifespanDesign/2100_sample/hks<Q>.tif",
                "Output/LifespanDesign/2100_sample/regime<Q>.tif"),
    ),
    GuideStep(
        key="maxlifespan",
        title="3. Best feature per cell (Max Lifespan)",
        group="Lifespan",
        tab="Max Lifespan",
        body="""
        Lifespan mapping answers "how long does this feature last here?". This answers the
        planner's question instead: which feature belongs here, and how long will it last?

        It takes the cell-wise maximum across the lifespan rasters of step 2, and a feature
        wins a cell where its own lifespan equals that maximum. Ties are kept rather than
        broken, so a cell where two features both reach the maximum appears in both layers -
        that is deliberate, and it is why the shares add up to more than 100%. It tells you
        the choice is yours.

        Each winner is written as a mask raster and polygonised into a GeoPackage, so the
        result can be drawn as action areas on a map.
        """,
        settings=(("Lifespan directory", "Output/LifespanDesign/2100_sample"),
                  ("Write polygons", "yes")),
        expect="About 338 000 sqft is mapped. Streamwood wins roughly three quarters of it "
               "and other nature-based engineering most of the rest.",
        writes=("Output/MaxLifespan/2100_sample/max_lf.tif",
                "Output/MaxLifespan/2100_sample/best_<feature>.tif",
                "Output/MaxLifespan/2100_sample/best_<feature>.gpkg"),
    ),
    GuideStep(
        key="terraforming",
        title="4. Terraforming and earthworks (Morphology)",
        group="Morphology",
        tab="Terraforming",
        body="""
        Step 3 says which feature belongs where. This step asks what the terrain would have
        to look like for those features to work, and what that costs in earth movement.

        Where a planned planting sits further above the water table than its roots can
        reach, the ground is lowered by exactly the excess - so the cell lands at the
        deepest tolerable depth to water and no lower. The limit defaults to 7 ft, the
        smallest depth-to-water tolerance among the planting features: the terrain has to
        suit the most demanding species planned, not the least.

        Point it at the Max Lifespan output folder from step 3. Features are applied in
        sequence and each works on the terrain the previous one left, because lowering the
        ground also lowers its depth to the water table.

        Then open Volume Assessment beside it, give it dem.tif as the original and
        dem_terraformed.tif as the modified DEM, and it reports the excavation volume.
        Volumes are integrated under the triangulated surface, not summed as prisms, so the
        quantity is comparable with the original software and with a contractor's estimate.

        Remember that a threshold-based modification is a proposal, not a construction
        drawing: it needs computer-aided design - edge smoothing and real-world geometry -
        before anyone digs.
        """,
        settings=(("Condition", CONDITION),
                  ("Feature action rasters", "Output/MaxLifespan/2100_sample"),
                  ("Max. depth to water table", "7 ft"),
                  ("Then", "Volume Assessment on dem.tif vs dem_terraformed.tif")),
        expect="A few hundred cells are lowered, the deepest cut around 9 ft, and Volume "
               "Assessment reports excavation only - lowering ground never places fill.",
        writes=("Output/Terraforming/2100_sample/dem_terraformed.tif",
                "Output/Terraforming/2100_sample/cut_depth.tif",
                "Output/Terraforming/2100_sample/d2w_terraformed.tif"),
    ),
    GuideStep(
        key="sharc",
        title="5. Habitat suitability and usable area (SHArC)",
        group="Ecohydraulics",
        tab="Habitat Area (SHArC)",
        body="""
        This is the first of the three ecohydraulic analyses and the one the other two lean
        on. Habitat suitability curves from Fish.xlsx map flow depth and velocity onto an
        index between 0 and 1; their geometric mean is the composite habitat suitability
        index (cHSI), masked to the wetted area. Usable habitat area at a discharge is the
        area where cHSI exceeds the threshold - 0.4 by default.

        Run Chinook Salmon, spawning. Because the flow duration workbook
        00_Flows/2100_sample/flow_duration_chsp.xlsx exists for that species code, the
        result also carries SHArea: usable area integrated over the flow duration curve, so
        habitat that only exists at a rare discharge counts for little. That single number
        is what a project gets judged on.

        Read the mean cHSI column, not only the usable area. Mean cHSI falls cleanly from
        0.51 at 300 cfs to 0.04 at 42200, which is what you would expect: spawning wants
        shallow, moderate flow. Usable area is not monotonic - it falls to about 16 000 sqft
        near 4000 cfs, then climbs to a second peak of about 66 000 sqft near 9750 cfs,
        because at that flow a large area of channel margin is inundated shallowly enough to
        clear the threshold even though the reach as a whole is less suitable. Area and
        quality are different questions, and SHArea is the one that weighs them together.

        Two discharges break the pattern entirely, and both are the data rather than the
        analysis. At 550 cfs the usable area collapses because u000550.tif tops out at
        1.4 ft/s where its neighbours at 500 and 600 cfs reach 4.5. At 88053 cfs the depth
        raster peaks at 6.8 ft where 42200 cfs reaches 22 ft, so it is a low-flow result
        wearing a flood's file name. Real conditions contain rasters like these, and finding
        them is part of the work.
        """,
        settings=(("Condition", CONDITION),
                  ("Species", "Chinook Salmon"),
                  ("Lifestage", "spawning"),
                  ("Combine method", "geometric mean"),
                  ("cHSI threshold", "0.4"),
                  ("Flow duration", "00_Flows/2100_sample/flow_duration_chsp.xlsx")),
        expect="60 discharges are evaluated; usable area is about 50 000 sqft at 300 cfs "
               "and peaks near 66 000 sqft at 9750 cfs, and SHArea is around 24 000 sqft.",
        writes=("Output/SHArC/2100_sample/csi_chsp<Q>.tif",),
    ),
    GuideStep(
        key="stranding",
        title="6. Stranding risk",
        group="Ecohydraulics",
        tab="Stranding Risk",
        body="""
        As discharge falls the wetted area shrinks and breaks apart, and pools that lose
        their connection to the main channel trap fish. Threshold each depth raster at the
        minimum swimming depth of the species and lifestage, label the wetted regions, and
        every region that does not reach the main channel is a stranding risk.

        Run Chinook Salmon fry: the minimum swimming depth comes from Fish.xlsx and is
        0.2 ft. That threshold is the single most influential parameter in the analysis, so
        report it alongside any result you quote.

        The main channel is defined once, at the lowest analysed discharge, and every higher
        discharge is judged against it - the same target the original built its least-cost
        escape routes towards. Q_disconnect.tif records the highest discharge at which each
        cell was disconnected, which is the flow at which that spot becomes a trap as the
        hydrograph recedes.

        One caveat on this reach: the 88053 cfs rasters look like a low-flow result rather
        than a 50-year flood, so ignore that row. It is an upstream data problem, and it is
        also why the stranded percentage is reported against the largest *measured* wetted
        extent rather than against the highest discharge's.
        """,
        settings=(("Condition", CONDITION),
                  ("Species", "Chinook Salmon"),
                  ("Lifestage", "fry"),
                  ("Minimum swimming depth", "0.2 ft"),
                  ("Connectivity", "4")),
        expect="Almost every one of the 60 discharges produces disconnected pools. The "
               "worst is 7250 cfs with 63 pools and about 2200 sqft stranded; roughly "
               "13 000 sqft is disconnected at some point in the recession.",
        writes=("Output/StrandingRisk/2100_sample/disconnected_<Q>.tif",
                "Output/StrandingRisk/2100_sample/Q_disconnect.tif",
                "Output/StrandingRisk/2100_sample/pools_<Q>.gpkg"),
    ),
    GuideStep(
        key="recruitment",
        title="7. Riparian recruitment",
        group="Ecohydraulics",
        tab="Riparian Seedling Recruitment",
        body="""
        Cottonwood and willow seedlings establish only where four things happen in the right
        order over a single season: a winter flow clears a seedbed, the water table then
        drops slowly enough for roots to follow, the seedling is not drowned by prolonged
        inundation, and no later flow uproots it. Each is scored 1, 0.5 or 0, and the
        recruitment potential is their product - a zero anywhere is a zero overall.

        This is the one module that needs a **daily flow record**, because bed preparation,
        recession and scour are about when flows happened, not just which flows are
        possible. The sample condition ships flow duration curves but no dated record, so a
        synthetic water year is provided:
        00_Flows/2100_sample/flow_series_2020.csv. Its discharges are the reach's own,
        taken from its flow duration curve; only their ordering in time is invented. Treat
        recruitment results here as a demonstration of the method rather than as a finding
        about the reach.

        Select 2020 as the analysis year. The crop area - where recruitment is possible at
        all - is the band between the lowest and highest wetted extent during seed
        dispersal, because seeds only land where the water reached.
        """,
        settings=(("Condition", CONDITION),
                  ("Flow series", "00_Flows/2100_sample/flow_series_2020.csv"),
                  ("Year", "2020"),
                  ("Species", "Fremont Cottonwood")),
        expect="A crop area of about 72 000 sqft, of which roughly 32 000 sqft reaches full "
               "recruitment potential. Bed preparation is the limiting objective.",
        writes=("Output/RiparianRecruitment/2100_sample_2020/recruitment_potential.tif",
                "Output/RiparianRecruitment/2100_sample_2020/bed_preparation.tif",
                "Output/RiparianRecruitment/2100_sample_2020/desiccation_survival.tif",
                "Output/RiparianRecruitment/2100_sample_2020/inundation_survival.tif",
                "Output/RiparianRecruitment/2100_sample_2020/scour_survival.tif"),
    ),
    GuideStep(
        key="maps",
        title="8. Make maps, and what to check",
        group="Maps",
        tab="Mapping",
        body="""
        The Maps tab draws any of those rasters into a QGIS print layout and exports a PDF.
        It needs QGIS bindings, which are built against the system Python rather than the
        conda environment; without them the tab still opens and says so.

        Before trusting any of the numbers above on your own data, check three things. Are
        the units right - the whole analysis is silent about a unit mismatch. Is the
        condition prepared - a missing d2w.tif does not raise, it just drops the criterion
        that needed it. And does input_definitions.inp list a return period for every
        discharge - lifespan mapping only uses the discharges that carry one, which on this
        reach is 17 of the 60 rasters on disk.
        """,
        settings=(("Condition", CONDITION),
                  ("Map type", "lifespan, habitat or stranding")),
        expect="A QGIS project and a PDF under 02_Maps/, or a clear message that QGIS is "
               "not available.",
        writes=("02_Maps/",),
    ),
)


def as_text(steps=None, width=88):
    """Render the guide as plain text, for a terminal or a log.

    Args:
        steps (tuple): the steps to render. Defaults to :data:`STEPS`.
        width (int): wrap width.

    Returns:
        str: the whole guide.
    """
    import textwrap

    lines = [TITLE, "=" * len(TITLE), ""]
    for step in (steps or STEPS):
        lines.append(step.title)
        lines.append("-" * len(step.title))
        location = step.group if step.tab == step.group else "%s > %s" % (step.group,
                                                                         step.tab)
        lines.append("Tab: %s" % location)
        lines.append("")
        for paragraph in step.paragraphs():
            lines.extend(textwrap.wrap(paragraph, width))
            lines.append("")
        if step.settings:
            lines.append("Settings:")
            for label, value in step.settings:
                lines.extend(textwrap.wrap("%s: %s" % (label, value), width,
                                           initial_indent="  - ",
                                           subsequent_indent="    "))
            lines.append("")
        if step.expect:
            lines.extend(textwrap.wrap("Expect: %s" % step.expect, width,
                                       subsequent_indent="  "))
            lines.append("")
        if step.writes:
            lines.append("Writes:")
            lines.extend("  %s" % path for path in step.writes)
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"
