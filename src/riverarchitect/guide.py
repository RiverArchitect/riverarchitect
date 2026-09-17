"""The Live Guide: a worked example that runs on the bundled sample data.

River Architect's modules chain together - a lifespan map needs a detrended DEM and a
depth-to-water-table raster, and those have to be built first. Reading that in the
documentation is one thing; doing it is another, and the step people get stuck on is the
first one, because a condition that is not prepared produces either an error or, worse, an
empty map that looks like an answer.

This module holds that walkthrough as **data**: an ordered tuple of :class:`GuideStep`,
each naming the tab or menu it belongs to, the settings to enter and what the result should
look like. Both front ends render the same tuple, so the guide cannot say one thing in the
Qt window and another in the tkinter one, and a test can check that the tabs and menus it
names exist.

The walk covers the whole project life cycle, not only the analyses: setting a project up
from your own model output, calibrating the thresholds and suitability criteria the
analyses run on, pricing the works, drawing the maps, and the tools around the edges.

It is meant to be *watched* as much as read. :func:`save_progress` remembers where a reader
stopped, so closing the window and coming back tomorrow resumes rather than restarts, and
both front ends drive the tuple with a play/pause control and a jump list.

The reach is ``2100_sample``, a real gravel-cobble reach in U.S. customary units that ships
in ``sample-data/`` of a source clone. :func:`sample_data_dir` finds it;
:func:`activate_sample_data` points the project home at it.
"""

import json
import logging
import os

from . import config

__all__ = ["GuideStep", "STEPS", "TITLE", "CONDITION", "DOCS_URL", "AUTOPLAY_SECONDS",
           "sample_data_dir", "activate_sample_data", "sample_data_status", "as_text",
           "step_index", "step_titles", "progress_path", "load_progress", "save_progress",
           "clear_progress"]

logger = logging.getLogger("riverarchitect")

#: Title of the guide, shown in the Help menu and as the window title.
TITLE = "Live Guide: Example"

#: The condition the guide works on.
CONDITION = "2100_sample"

#: Where the full documentation lives.
DOCS_URL = "https://riverarchitect.readthedocs.io/"

#: Seconds a step stays on screen when the guide is playing itself.
#:
#: Long enough to read a step rather than to glance at it: the bodies run to several
#: paragraphs, and a tour that moves on before the reader has finished is worse than one
#: they drive by hand.
AUTOPLAY_SECONDS = 30


class GuideStep:
    """One step of the walkthrough.

    A step points at a tab, at a menu, or at both - the tools step names the Tools menu and
    a tab, the closing step names only the Help menu.

    Args:
        key (str): short identifier, for tests, for deep links and for the saved position.
        title (str): heading, e.g. ``"3. Lifespan mapping"``.
        group (str): the top-level tab the step happens in, as ``TAB_GROUPS`` names it.
            Empty for a step that is only about a menu.
        tab (str): the module tab within that group. Equal to ``group`` for a lone tab.
        body (str): the explanation, as paragraphs separated by a blank line.
        settings (tuple): ``(label, value)`` pairs to enter in the tab.
        expect (str): what the result should look like, so a reader can tell it worked.
        writes (tuple): the files the step produces, relative to the project directory.
        menu (str): the menu bar entry the step uses, without its accelerator, e.g.
            ``"Tools"``. Empty when the step needs no menu.
        extra_tabs (tuple): further ``(group, tab)`` pairs the step sends the reader to
            alongside its own. A step that says "then open Volume Assessment beside it"
            names it here, so that a tab mentioned in prose is still a tab the guide is
            known to cover and a test can hold it to that.
    """

    def __init__(self, key, title, group, tab, body, settings=(), expect="", writes=(),
                 menu="", extra_tabs=()):
        self.key = key
        self.title = title
        self.group = group
        self.tab = tab
        self.body = body.strip()
        self.settings = tuple(settings)
        self.expect = expect.strip()
        self.writes = tuple(writes)
        self.menu = menu
        self.extra_tabs = tuple(tuple(pair) for pair in extra_tabs)

    @property
    def location(self):
        """Where the step happens, as one line.

        ``"Lifespan > Lifespan Design"`` for a tab, ``"Get Started, Tools menu"`` when the
        step uses both, and just ``"Help"`` for a step that is only about a menu - the
        renderers prefix that one with "Menu:" instead of "Tab:", so repeating the word
        here would read as "Menu: Help menu".
        """
        if not self.group:
            return self.menu
        parts = [self.group if self.tab == self.group
                 else "%s > %s" % (self.group, self.tab)]
        for group, tab in self.extra_tabs:
            parts.append(group if tab == group else "%s > %s" % (group, tab))
        if self.menu:
            parts.append("%s menu" % self.menu)
        return ", ".join(parts)

    @property
    def has_tab(self):
        """True when the step names a tab the main window can bring to the front."""
        return bool(self.group)

    def tabs(self):
        """Every ``(group, tab)`` pair the step sends the reader to, primary first."""
        pairs = [(self.group, self.tab)] if self.group else []
        return pairs + list(self.extra_tabs)

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


# ------------------------------------------------------------------------ progress

def step_index(key, default=0):
    """Index of the step with this key, or ``default`` when there is no such step.

    Progress is stored as a key rather than as a number so that inserting a step does not
    move every saved position along by one.
    """
    for index, step in enumerate(STEPS):
        if step.key == key:
            return index
    return default


def step_titles():
    """Every step title, in order - what a jump list shows."""
    return [step.title for step in STEPS]


def progress_path():
    """File the reader's position in the walkthrough is remembered in."""
    return os.path.join(config.user_config_dir(), "guide_progress.json")


def load_progress():
    """The key of the step the reader last had open, or ``None``.

    Never raises. A missing, unreadable or malformed file means "start at the beginning",
    which is exactly what a first run looks like, so there is nothing to report.
    """
    try:
        with open(progress_path(), "r", encoding="utf-8") as handle:
            key = json.load(handle).get("step")
    except (OSError, ValueError):
        return None
    return key if any(step.key == key for step in STEPS) else None


def save_progress(key):
    """Remember the step the reader is on.

    Args:
        key (str): the step key.

    Returns:
        bool: True when it was written. A read-only home directory is not worth an error
        dialog in the middle of a walkthrough, so a failure is logged and swallowed.
    """
    try:
        os.makedirs(config.user_config_dir(), exist_ok=True)
        with open(progress_path(), "w", encoding="utf-8") as handle:
            json.dump({"step": key}, handle)
    except OSError as exc:
        logger.debug("could not save the guide position: %s", exc)
        return False
    return True


def clear_progress():
    """Forget the saved position, so the guide starts from the beginning again."""
    try:
        os.remove(progress_path())
    except OSError:
        return False
    return True


# --------------------------------------------------------------------------- steps

STEPS = (
    GuideStep(
        key="start",
        title="0. What you are about to do",
        group="Get Started",
        tab="Get Started",
        body="""
        This walkthrough runs a whole project on 2100_sample: a real gravel-cobble reach
        in U.S. customary units, with a DEM, a mean grain size raster, a DEM of difference
        and 60 pairs of modelled water depth and velocity rasters between 300 and 88053 cfs.

        The order matters. Every later module reads a raster that Get Started produces, so
        preparing the condition is not optional housekeeping - it is step one of the
        analysis. The chain is: set the project up, prepare the condition, map feature
        lifespans, pick the best feature per cell, terraform the ground those features
        need, then the three ecohydraulic analyses - which are independent of one another
        but all need the prepared condition - then price the works and draw the maps.

        Two steps are about your numbers rather than ours. Step 4 replaces the default
        lifespan thresholds with a workbook you control, and step 8 does the same for the
        habitat suitability curves. Skip them on a first pass and come back: the defaults
        are real published values and they produce a real answer, but a project you have to
        defend runs on criteria you chose.

        Set the units to U.S. customary before you start (Units menu). The program starts
        in SI units, but the sample rasters are in feet and feet per second. River
        Architect never converts data: an analysis whose unit system disagrees with the
        coordinate system of its rasters stops with an error saying so.

        You do not have to do this in one sitting. Press Play and the guide advances by
        itself, the step list jumps anywhere, and closing the window keeps your place -
        reopening it from the Help menu comes back here.
        """,
        settings=(("Project directory", "sample-data/"),
                  ("Units", "U.S. customary"),
                  ("Condition", CONDITION)),
        expect="The status bar shows the sample-data directory and the condition list "
               "offers 2100_sample.",
    ),
    GuideStep(
        key="project",
        title="1. Set up your own project",
        group="Get Started",
        tab="Get Started",
        menu="Project",
        body="""
        The rest of this walk uses the bundled sample data, so that every number it quotes
        can be checked. This step is the one you will actually repeat: turning your own 2D
        model output into a project River Architect can read.

        A project is a directory with four sub-directories, and the program resolves
        everything against it. 01_Conditions/<name>/ holds one condition - one state of the
        river, real or planned. 00_Flows/<name>/ holds that condition's flow records and
        duration curves. 02_Maps/ collects QGIS projects and exported PDFs. Output/<module>/
        <name>/ collects results, one folder per module. Point the program at the project
        with Project > Set project directory, or set RIVERARCHITECT_HOME before launching.

        Inside a condition, names carry meaning. Each modelled discharge is a pair,
        h<Q>.tif for water depth and u<Q>.tif for depth-averaged velocity, with the
        discharge zero-padded to six digits: h000750.tif and u000750.tif are 750 cfs. A
        discharge with only one of the two is skipped by every hydraulic module. Alongside
        them go dem.tif, a mean or median grain size raster (dmean.tif), and optionally a
        DEM of difference for the scour and fill criteria.

        input_definitions.inp is the file that decides how much of the analysis you get. It
        maps each modelled discharge to a flood return period, and lifespan mapping can only
        use the discharges that carry one - on this reach, 17 of the 60 rasters on disk.
        Nothing warns you about the other 43: they are simply not part of the answer. Get
        Started can write a starting file for you, from the discharges it finds; the return
        periods are yours to fill in from a flood frequency analysis.

        One thing to do before anything else, on rasters that came from someone else's
        model. NoData arrives as -9999, -3.4e38, 3.4e38 or a plain 0 depending on who
        exported it, sometimes varying within one dataset, and a 0 that is meant to be
        NoData reads as a real depth of zero. Tools > Reconcile NoData in a condition
        rewrites a whole folder to one sentinel, preserving the mask exactly. Run it once,
        on import, and the rest of the chain stops guessing.
        """,
        settings=(("Menu", "Project > Set project directory ..."),
                  ("Project directory", "sample-data/, or your own"),
                  ("Depth and velocity rasters", "01_Conditions/<name>/h000750.tif and "
                                                 "u000750.tif, six digits per discharge"),
                  ("Terrain", "01_Conditions/<name>/dem.tif and dmean.tif"),
                  ("Return periods", "01_Conditions/<name>/input_definitions.inp"),
                  ("On import", "Tools > Reconcile NoData in a condition ...")),
        expect="The status bar names the project directory and reports how many conditions "
               "it found. Every tab's Condition list offers them.",
        writes=("01_Conditions/<name>/input_definitions.inp",),
    ),
    GuideStep(
        key="getstarted",
        title="2. Prepare the condition (Get Started)",
        group="Get Started",
        tab="Get Started",
        body="""
        Build the terrain products the later modules read. Use 750 cfs as the reference
        discharge: it is an in-channel low flow, which is what a detrended DEM and a water
        surface should be keyed to.

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
        compared against), tb (u*^2), hks (relative submergence) and regime. Step 13 comes
        back to what those diagnostics are for.

        Build the fifth product too: analyze flows. Point it at
        00_Flows/2100_sample/flow_series_2020.csv and it writes one seasonal flow duration
        curve per species and lifestage. Habitat area is integrated over that curve, so
        without it step 7 can report usable areas but not SHArea - the single number the
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
        title="3. Lifespan and design mapping",
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
                  ("Manning's n", "0.04739"),
                  ("Threshold values", "packaged defaults"),
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
        key="thresholds",
        title="4. Your own threshold values",
        group="Lifespan",
        tab="Lifespan Design",
        body="""
        Step 3 ran on published defaults. This step replaces them with yours, and it is the
        difference between a demonstration and a design you can defend.

        A threshold is a statement about your 2D model's output. Each feature carries a
        handful: h_max and u_max, the water depth and flow velocity beyond which it fails;
        froude_max; tau_cr, the critical dimensionless bed shear stress, compared against
        the ts<Q>.tif rasters step 2 built; d2w_min and d2w_max, the depth-to-water-table
        band a planting needs; det_min and det_max, a detrended elevation band; grain_max;
        and scour_rate and fill_rate, read from the DEM of difference. Every criterion is
        optional. One whose threshold is unset, or whose input raster the condition does not
        have, is skipped - which is why a sparsely defined feature still produces a map, and
        why a missing d2w.tif quietly shrinks the analysis instead of failing it.

        Press Save the defaults to write the whole set out as threshold_values.xlsx: one
        column per feature, one row per threshold, in the layout the ArcGIS version used.
        Open it, change what your reach and your literature say, and load it back with
        Threshold values. The button then shows the workbook's name instead of "packaged
        defaults", and the run uses it.

        Two traps in that workbook. Its values are U.S. customary and are used exactly as
        written - Cottonwood really is keyed to a water table 1 to 7 feet down, and there is
        no hidden conversion waiting to fix a metric number you type in. And the
        Morphological units rows use a different vocabulary from the morphological unit
        table itself, agriplain against agricultural plain; the aliases are bridged for you,
        but invent a new name and the criterion silently matches nothing.

        Run rocks again with the workbook loaded and unchanged: the area must come back at
        the same ~18 sqft. That round trip is the check that your file is being read the way
        you think it is. Then change one threshold and watch the number move.
        """,
        settings=(("Condition", CONDITION),
                  ("Save the defaults ...", "threshold_values.xlsx"),
                  ("Threshold values", "the workbook you just edited"),
                  ("Features", "the ones you changed"),
                  ("Units", "U.S. customary, matching the workbook")),
        expect="The Threshold values button shows your workbook's name, and an unedited "
               "round trip reproduces step 3 exactly - Angular boulders at about 18 sqft.",
        writes=("threshold_values.xlsx",),
    ),
    GuideStep(
        key="maxlifespan",
        title="5. Best feature per cell (Max Lifespan)",
        group="Lifespan",
        tab="Max Lifespan",
        body="""
        Lifespan mapping answers "how long does this feature last here?". This answers the
        planner's question instead: which feature belongs here, and how long will it last?

        It takes the cell-wise maximum across the lifespan rasters of step 3, and a feature
        wins a cell where its own lifespan equals that maximum. Ties are kept rather than
        broken, so a cell where two features both reach the maximum appears in both layers -
        that is deliberate, and it is why the shares add up to more than 100%. It tells you
        the choice is yours.

        Each winner is written as a mask raster and polygonised into a GeoPackage, so the
        result can be drawn as action areas on a map. Two later steps read this folder: the
        terraforming of step 6 and the cost estimate of step 11.
        """,
        settings=(("Condition", CONDITION),
                  ("Lifespan rasters", "Output/LifespanDesign/2100_sample"),
                  ("Write polygons", "yes")),
        expect="About 338 000 sqft is mapped. Streamwood wins roughly three quarters of it "
               "and other nature-based engineering most of the rest.",
        writes=("Output/MaxLifespan/2100_sample/max_lf.tif",
                "Output/MaxLifespan/2100_sample/best_<feature>.tif",
                "Output/MaxLifespan/2100_sample/best_<feature>.gpkg"),
    ),
    GuideStep(
        key="terraforming",
        title="6. Terraforming and earthworks (Morphology)",
        group="Morphology",
        tab="Terraforming",
        body="""
        Step 5 says which feature belongs where. This step asks what the terrain would have
        to look like for those features to work, and what that costs in earth movement.

        Where a planned planting sits further above the water table than its roots can
        reach, the ground is lowered by exactly the excess - so the cell lands at the
        deepest tolerable depth to water and no lower. The limit defaults to 7 ft, the
        smallest depth-to-water tolerance among the planting features: the terrain has to
        suit the most demanding species planned, not the least.

        Point it at the Max Lifespan output folder from step 5. Features are applied in
        sequence and each works on the terrain the previous one left, because lowering the
        ground also lowers its depth to the water table.

        Then open Volume Assessment beside it, give it dem.tif as the original and
        dem_terraformed.tif as the modified DEM, and it reports the excavation volume.
        Volumes are integrated under the triangulated surface, not summed as prisms, so the
        quantity is comparable with the original software and with a contractor's estimate.
        The level of detection matters here: it is the vertical change below which the two
        DEMs are treated as identical, and it keeps survey noise out of the bill.

        Remember that a threshold-based modification is a proposal, not a construction
        drawing: it needs computer-aided design - edge smoothing and real-world geometry -
        before anyone digs.
        """,
        extra_tabs=(("Morphology", "Volume Assessment"),),
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
        title="7. Habitat suitability and usable area (SHArC)",
        group="Ecohydraulics",
        tab="Habitat Area (SHArC)",
        body="""
        This is the first of the three ecohydraulic analyses and the one the other two lean
        on. Habitat suitability curves from Fish.xlsx map water depth and velocity onto an
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
                  ("Suitability curves", "packaged Fish.xlsx"),
                  ("Species", "Chinook Salmon"),
                  ("Lifestage", "spawning"),
                  ("Combine method", "geometric mean"),
                  ("Usable habitat threshold", "0.4"),
                  ("Flow duration", "00_Flows/2100_sample/flow_duration_chsp.xlsx")),
        expect="60 discharges are evaluated; usable area is about 50 000 sqft at 300 cfs "
               "and peaks near 66 000 sqft at 9750 cfs, and SHArea is around 24 000 sqft.",
        writes=("Output/SHArC/2100_sample/csi_chsp<Q>.tif",),
    ),
    GuideStep(
        key="hsi",
        title="8. Your own habitat suitability criteria",
        group="Ecohydraulics",
        tab="Habitat Area (SHArC)",
        body="""
        The curves that produced step 7 are published ones for a Californian reach. Your
        river has its own species, and often its own curves for the same species. This step
        replaces them, the way step 4 replaced the lifespan thresholds.

        Copy the packaged Fish.xlsx - the Suitability curves button names the file it is
        using, and the documentation gives its location - and edit it. The layout is one
        block of eight columns per species: the species name on row 2, its lifestages on
        row 5 at four fixed offsets, then the velocity curve from row 9 and the depth curve
        from row 38, each a pair of columns of parameter value against suitability index.
        Cover values sit on rows 72 to 85 and the stranding thresholds - minimum swimming
        depth and maximum sustained velocity - on rows 87 and 88, which is where step 9
        reads them from. Then load it back with Suitability curves; the Species and
        Lifestage lists repopulate from your workbook.

        Three settings decide what the curves then mean. Combine method: the geometric mean
        of the depth and velocity indices is the default and is forgiving of one poor
        index, while the product is harsher and drops faster. The usable habitat threshold,
        0.4, is the cHSI above which a cell counts as usable at all - it moves the reported
        area more than any curve edit will, so state it whenever you quote a number. And
        "weight usable area by the mean suitability" reports quality-weighted area instead
        of raw area, which is the fairer comparison between two designs.

        One asymmetry to know before you edit a curve. Between the points you give, the
        index is interpolated. Below the first point it holds that first suitability, but
        above the last point it drops to zero, not to the last value - because a depth
        beyond the end of a curve is unsuitable rather than maximally suitable. So the last
        point you enter is a statement about where the habitat stops.

        Finally, mind the species name. The flow duration workbooks are found by a
        four-letter code derived from the species and lifestage, so renaming Chinook Salmon
        in your workbook breaks the link to flow_duration_chsp.xlsx and SHArea quietly stops
        being reported while usable areas keep appearing.
        """,
        settings=(("Condition", CONDITION),
                  ("Suitability curves", "your own copy of Fish.xlsx"),
                  ("Species and Lifestage", "repopulated from your workbook"),
                  ("Combine method", "geometric mean, or product"),
                  ("Usable habitat threshold", "0.4"),
                  ("Weighting", "weight usable area by the mean suitability")),
        expect="The Species list shows your workbook's species, and an unedited copy "
               "reproduces step 7's areas exactly.",
        writes=("Output/SHArC/2100_sample/csi_<code><Q>.tif",),
    ),
    GuideStep(
        key="stranding",
        title="9. Stranding risk",
        group="Ecohydraulics",
        tab="Stranding Risk",
        body="""
        As discharge falls the wetted area shrinks and breaks apart, and pools that lose
        their connection to the main channel trap fish. Threshold each depth raster at the
        minimum swimming depth of the species and lifestage, label the wetted regions, and
        every region that does not reach the main channel is a stranding risk.

        Run Chinook Salmon fry: the minimum swimming depth comes from Fish.xlsx - the same
        workbook step 8 let you replace - and is 0.2 ft. That threshold is the single most
        influential parameter in the analysis, so report it alongside any result you quote.
        The Custom entry in the species list lets you set it directly.

        A stranding analysis walks a *falling* hydrograph, so the discharge range runs from
        a high flow down to a low one and the tab refuses a range the other way round. The
        main channel is defined once, at the lowest analysed discharge, and every higher
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
                  ("Species and lifestage", "Chinook Salmon, fry"),
                  ("Minimum swimming depth", "0.2 ft"),
                  ("Discharge range", "from a high flow down to the lowest")),
        expect="Almost every one of the 60 discharges produces disconnected pools. The "
               "worst is 7250 cfs with 63 pools and about 2200 sqft stranded; roughly "
               "13 000 sqft is disconnected at some point in the recession.",
        writes=("Output/StrandingRisk/2100_sample/disconnected_<Q>.tif",
                "Output/StrandingRisk/2100_sample/Q_disconnect.tif",
                "Output/StrandingRisk/2100_sample/pools_<Q>.gpkg"),
    ),
    GuideStep(
        key="recruitment",
        title="10. Riparian recruitment",
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

        Select 2020 as the season. The crop area - where recruitment is possible at all -
        is the band between the lowest and highest wetted extent during seed dispersal,
        because seeds only land where the water reached.

        The species parameters have their own workbook, recruitment_parameters.xlsx, and
        the Parameters button overrides the packaged one exactly as steps 4 and 8 override
        their workbooks: dispersal dates, recession rates and inundation tolerances are
        regional, and the packaged values are Californian.
        """,
        settings=(("Condition", CONDITION),
                  ("Flow record", "00_Flows/2100_sample/flow_series_2020.csv"),
                  ("Season", "2020"),
                  ("Parameters", "packaged recruitment_parameters.xlsx"),
                  ("Existing vegetation", "optional")),
        expect="A crop area of about 72 000 sqft, of which roughly 32 000 sqft reaches full "
               "recruitment potential. Bed preparation is the limiting objective.",
        writes=("Output/RiparianRecruitment/2100_sample_2020/recruitment_potential.tif",
                "Output/RiparianRecruitment/2100_sample_2020/bed_preparation.tif",
                "Output/RiparianRecruitment/2100_sample_2020/desiccation_survival.tif",
                "Output/RiparianRecruitment/2100_sample_2020/inundation_survival.tif",
                "Output/RiparianRecruitment/2100_sample_2020/scour_survival.tif"),
    ),
    GuideStep(
        key="costs",
        title="11. What the project costs, and what it buys",
        group="Project Maker",
        tab="Project Maker",
        body="""
        Everything so far describes a design. This step prices it and asks whether it is
        worth building - the question a funder actually puts.

        It needs two things the earlier steps produced. The Max Lifespan output folder from
        step 5 supplies the quantities: the mapped area of each winning feature becomes so
        many square feet of planting, so many cubic yards of grading, so many logs at the
        length you give. And two conditions supply the habitat comparison - the existing
        one, and a with-project one whose depth and velocity rasters come from re-running
        your 2D model over the terraformed DEM. They have to be two different conditions;
        the tab refuses to compare a condition with itself, because there would be no gain
        to measure.

        The output has two halves. The bill of quantities totals unit costs by group -
        terraforming, bioengineering, plantings, civil works, maintenance - then adds the
        markups a real estimate carries: 10 % mobilisation, 10 % contingency, 16.5 %
        overhead, profit and insurance, and 35 % permitting. Below it, SHArea before and
        after, the net gain, and the cost per unit area gained. That last figure is the
        one to compare between designs; a scheme that is cheaper in total and worse per
        square foot of habitat is not the cheaper scheme.

        The unit rates are Python, in the projectmaker module, rather than a workbook -
        diffable, reviewable, and wrong for your region. Costs are local and dated, so
        treat the shipped rates as a worked structure and put your own tender prices in
        before quoting anything to anyone.
        """,
        settings=(("Project name", "project"),
                  ("Max Lifespan output", "Output/MaxLifespan/2100_sample"),
                  ("Existing condition", CONDITION),
                  ("With-project condition", "the re-modelled, terraformed condition"),
                  ("Species", "Chinook Salmon"),
                  ("Lifestage", "spawning"),
                  ("Log length", "25 ft")),
        expect="A cost table by group with the four markups added, then SHArea before and "
               "after, the net habitat gain and the cost per unit area gained.",
        writes=("Output/ProjectMaker/project/project_costs.csv",),
    ),
    GuideStep(
        key="maps",
        title="12. Make the maps (QGIS)",
        group="Maps",
        # The Mapping tab is the only one in its group, so the notebook flattens it and the
        # label on screen reads "Maps". Naming it that way is what the reader sees.
        tab="Maps",
        body="""
        Every result so far is a raster on disk. This turns them into the thing that goes
        into a report: an atlas-driven PDF, one page per part of the reach, drawn in a QGIS
        print layout with a legend, scale bar, north arrow and title.

        Choose the map type - Lifespan, Design, Max Lifespan or Modify Terrain - and point
        it at the folder holding those rasters, which is the Output folder of whichever
        step produced them. The output lands under 02_Maps/<condition>/, alongside a saved
        QGIS project you can open and adjust by hand; the program will reuse that project
        next time rather than overwrite your changes.

        Symbology comes from packaged .qml layer styles, matched to each raster by name, so
        a lifespan map is drawn with the lifespan ramp without your doing anything. A
        raster whose name matches no style falls back to QGIS defaults - that grey linear
        ramp is the sign to add a style rather than to distrust the data. Tools > Convert
        ArcGIS .lyrx to QGIS .qml brings styles over from an ArcGIS project.

        This tab is the one part of River Architect that needs QGIS itself. The bindings are
        compiled against the system Python rather than the conda environment, so if the run
        button is disabled and the pane says QGIS is unavailable, that is a working
        installation telling you the truth rather than a fault - the documentation's
        installation page covers running the mapping module against the system interpreter.
        """,
        settings=(("Condition", CONDITION),
                  ("Map type", "Lifespan, Design, Max Lifespan or Modify Terrain"),
                  ("Raster directory", "Output/<module>/2100_sample"),
                  ("Output directory", "02_Maps/2100_sample (default)")),
        expect="A QGIS project and a multi-page PDF under 02_Maps/, or a clear message "
               "that QGIS is not available.",
        writes=("02_Maps/2100_sample/maps_2100_sample_design.qgz",
                "02_Maps/2100_sample/<map>.pdf"),
    ),
    GuideStep(
        key="tools",
        title="13. The tools around the edges",
        group="Morphology",
        tab="River Builder",
        menu="Tools",
        body="""
        Four things sit outside the chain because they are used before it, beside it, or
        instead of it.

        Bed shear stress, twice over. Step 2 built it for a whole condition, writing
        ts, tb, hks and regime for all 60 discharges; Tools > Bed shear stress does the
        same arithmetic on three loose rasters, which is the point - it runs on model output
        before that output has been organised into a condition folder at all, so a
        questionable hydraulic result can be caught on the day it comes out of the model.
        The optional output worth opening is regime<Q>.tif: it records which resistance law
        applied in each cell - 1 Rickenmann-Recking, 2 blended, 3 Keulegan-Einstein, 0
        invalid. On this reach about 95 % of wet cells are regime 1, which is exactly the
        range where a single logarithmic law does not hold, so a shear stress map computed
        the old way would have been wrong across most of the reach without saying so.

        Reconcile NoData in a condition, which step 1 already recommended on import: it
        rewrites every raster in a folder to one NoData sentinel, preserving the mask
        exactly, and it is the cheapest insurance in the program.

        The Pool-riffle designer sizes a pool-riffle sequence from grain size, bed slope,
        base width, target residual pool depth and bank slope. It is a design calculator
        rather than a mapping module, so it opens as a dialog and recomputes as you type.

        River Builder, beside this tab, goes the other way: it synthesises a valley DEM
        from channel parameters - reach length, bankfull width and depth, valley slope,
        D50, floodplain and terrace widths, meander amplitude and a cross-section shape.
        Use it to try a method when you have no survey, or to build a controlled test case.
        Volume Assessment, its neighbour, is the one step 6 sent you to: cut and fill
        between any two DEMs, not only terraformed ones.
        """,
        settings=(("Menu", "Tools > Bed shear stress ..."),
                  ("Condition-wide alternative", "Get Started > Build > dimensionless bed "
                                                 "shear stress (taux)"),
                  ("Optional outputs", "ts<Q>.tif, tb<Q>.tif, hks<Q>.tif, regime<Q>.tif"),
                  ("Also in Tools", "Reconcile NoData; Pool-riffle designer; "
                                    "Convert ArcGIS .lyrx to QGIS .qml"),
                  ("Beside this tab", "River Builder and Volume Assessment")),
        expect="The shear stress dialog reports the share of wetted cells in each "
               "resistance regime - about 95 % Rickenmann-Recking on 2100_sample - and "
               "names the four rasters it wrote.",
        writes=("<prefix>{ts,tb,hks,regime}.tif",),
    ),
    GuideStep(
        key="next",
        title="14. Where to go from here",
        group="",
        tab="",
        menu="Help",
        body="""
        That is the whole program: a project set up from your model output, thresholds and
        suitability criteria you control, five analyses, a costed design and a map series.

        Help > Documentation, or F1, opens the full documentation. Four pages earn a visit
        before your first real project. The module pages explain what each analysis
        computes and cite the literature its defaults come from. The feature catalogue
        lists every restoration feature and every threshold behind it, which is the
        reference to have open while editing the workbook from step 4. Known issues is the
        honest list of rough edges in the current release - read it before you conclude
        something is broken. And the FAQ answers the questions that come up first, starting
        with where the workbooks live.

        If you are arriving from River Architect 1.x, the arcpy migration page is the one
        to read: it records what each ArcGIS operation became, and, more usefully, the
        places where a plausible-looking port did not do what 1.4 did. Those were only
        found by running the whole chain on a real reach, which is what you have just
        watched.

        This guide is always here. Help > Live Guide reopens it at the step you left off
        on, the step list jumps anywhere in it, and Restart clears the saved position and
        begins again from step 0.
        """,
        settings=(("Menu", "Help > Documentation (F1)"),
                  ("Read first", "the module pages, the feature catalogue, known issues "
                                 "and the FAQ"),
                  ("Coming from 1.x", "the arcpy migration page"),
                  ("Reopen this guide", "Help > %s" % TITLE)),
        expect="The documentation opens in a browser. Closing this window keeps your "
               "place; Restart clears it.",
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
        lines.append("Tab: %s" % step.location if step.has_tab
                     else "Menu: %s" % step.location)
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
