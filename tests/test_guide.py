"""Tests for the Live Guide.

The guide is content, so most of what can go wrong is content going stale: a step naming a
tab that was renamed, or a settings row naming a species the fish database does not have.
These check exactly that, plus that both front ends can render every step and navigate to
the tab it names.
"""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from riverarchitect import guide  # noqa: E402


# ------------------------------------------------------------------------- content

def test_the_guide_covers_the_whole_chain_in_order():
    keys = [step.key for step in guide.STEPS]
    assert keys == ["start", "project", "getstarted", "lifespan", "thresholds",
                    "maxlifespan", "terraforming", "sharc", "hsi", "stranding",
                    "recruitment", "costs", "maps", "tools", "next"]


def test_the_guide_reaches_every_tab_the_interface_has(qt_app):
    """A tab nothing points at is a tab nobody finds.

    Takes ``qt_app`` for the skip it carries, not for the application: importing
    ``gui.qt.main`` pulls in the Qt widgets, so without a binding this raises ImportError
    rather than skipping. ``TAB_GROUPS`` is plain data, and ``test_gui`` asserts the two
    front ends declare the same one, so checking either is checking both.
    """
    from riverarchitect.gui.qt.main import TAB_GROUPS

    named = {pair for step in guide.STEPS for pair in step.tabs()}
    for group, factories in TAB_GROUPS:
        for factory in factories:
            tab = group if len(factories) == 1 else factory.title
            assert (group, tab) in named, \
                "no step sends the reader to %s > %s" % (group, tab)


def test_every_step_is_complete():
    for step in guide.STEPS:
        assert step.title
        # A step points at a tab, at a menu, or at both - but never at nothing.
        assert step.location, "%s says nowhere to go" % step.key
        assert bool(step.group) == bool(step.tab), \
            "%s names half a tab" % step.key
        assert step.paragraphs(), "%s has no body" % step.key
        assert step.settings, "%s tells the reader nothing to enter" % step.key
        assert step.expect, "%s gives no way to tell whether it worked" % step.key


def test_steps_are_numbered_in_order():
    for index, step in enumerate(guide.STEPS):
        assert step.title.startswith("%d." % index)


#: Steps that are about the program rather than about the sample reach, and so have no
#: condition to name: the max-lifespan step works on a directory, the tools and closing
#: steps on menus, and the two customisation steps on workbooks.
_CONDITIONLESS = ("maxlifespan", "tools", "next")


def test_the_guide_names_the_sample_condition_everywhere_it_matters():
    for step in guide.STEPS:
        if step.key in _CONDITIONLESS:
            continue
        values = " ".join(value for _label, value in step.settings)
        assert guide.CONDITION in values or "sample-data" in values, step.key


def test_every_menu_a_step_names_exists(qt_app):
    """A step pointing at a menu that was renamed is as dead as one pointing at a tab."""
    from riverarchitect.gui.qt.main import RiverArchitectWindow

    window = RiverArchitectWindow()
    titles = {title.replace("&", "") for title in window.menus}
    for step in guide.STEPS:
        if step.menu:
            assert step.menu in titles, \
                "the guide names a %s menu that does not exist" % step.menu


def test_step_titles_match_the_steps():
    assert guide.step_titles() == [step.title for step in guide.STEPS]


def test_as_text_renders_every_step():
    # The renderer wraps, so compare on words rather than on whole sentences.
    text = guide.as_text()
    words = set(text.split())
    for step in guide.STEPS:
        assert step.title in text
        for label, _value in step.settings:
            assert (label.split()[0] + ":") in words or label.split()[0] in words
        for path in step.writes:
            assert path in text


# --------------------------------------------------------------------- sample data

def test_sample_data_is_found_in_a_clone():
    directory = guide.sample_data_dir()
    if directory is None:
        pytest.skip("not running from a source clone")
    assert os.path.isdir(os.path.join(directory, "01_Conditions", guide.CONDITION))
    ready, message = guide.sample_data_status()
    assert ready and message


def test_the_files_each_step_promises_to_read_are_there():
    """Inputs the guide names must exist, or the walkthrough stops at that step."""
    directory = guide.sample_data_dir()
    if directory is None:
        pytest.skip("not running from a source clone")
    for relative in ("00_Flows/2100_sample/flow_duration_chsp.xlsx",
                     "00_Flows/2100_sample/flow_series_2020.csv",
                     "01_Conditions/2100_sample/input_definitions.inp",
                     "01_Conditions/2100_sample/dem.tif",
                     "01_Conditions/2100_sample/dmean.tif",
                     "01_Conditions/2100_sample/h000750.tif",
                     "01_Conditions/2100_sample/u000750.tif"):
        assert os.path.isfile(os.path.join(directory, *relative.split("/"))), relative


def test_activate_sample_data_sets_the_project_home(tmp_path, monkeypatch):
    from riverarchitect import config

    if guide.sample_data_dir() is None:
        pytest.skip("not running from a source clone")
    original = config.project_home()
    try:
        directory = guide.activate_sample_data()
        assert os.path.abspath(config.project_home()) == os.path.abspath(directory)
    finally:
        config.set_project_home(original)


def test_the_species_the_guide_names_is_in_the_fish_database():
    """A settings row naming a species the workbook does not have is a dead instruction."""
    pytest.importorskip("openpyxl")
    from riverarchitect.sharc import FishDatabase

    fish = FishDatabase()
    checked = 0
    for step in guide.STEPS:
        settings = dict(step.settings)
        # The stranding tab presents the two as one control, so the guide names them that
        # way; every other tab keeps them apart.
        combined = settings.get("Species and lifestage", "")
        if combined:
            name, _, stage = combined.partition(",")
            pairs = [(name.strip(), stage.strip())]
        elif "Species" in settings:
            pairs = [(settings["Species"], settings.get("Lifestage", ""))]
        else:
            continue
        for name, stage in pairs:
            if "Cottonwood" in name or "your own" in name:
                continue    # the recruitment species is not a fish; the HSI step is generic
            species = fish.resolve_species(name)
            if stage:
                assert fish.resolve_lifestage(species, stage)
            checked += 1
    assert checked >= 3, "the species check stopped covering the steps it was written for"


# ------------------------------------------------------------------------ front ends

@pytest.fixture(scope="module")
def qt_app():
    qtcompat = pytest.importorskip("riverarchitect.gui.qt.qtcompat")
    if not qtcompat.QT_AVAILABLE:
        pytest.skip("no Qt binding installed")
    return qtcompat.QApplication.instance() or qtcompat.QApplication([])


def test_qt_guide_renders_and_navigates_every_step(qt_app, clean_guide_progress):
    from riverarchitect.gui.qt.guide_window import GuideDialog
    from riverarchitect.gui.qt.main import RiverArchitectWindow

    window = RiverArchitectWindow()
    dialog = GuideDialog(window)
    for index, step in enumerate(guide.STEPS):
        dialog._go(index)
        assert dialog.heading.text() == step.title
        assert dialog.jump.currentIndex() == index
        if not step.has_tab:
            # Nothing to raise, so the button must be off rather than erroring.
            assert not dialog.open_button.isEnabled()
            continue
        assert window.select_tab(step.group, step.tab), \
            "the guide names a tab that does not exist: %s > %s" % (step.group, step.tab)
    assert not window.select_tab("no such group")


def test_qt_guide_jumps_plays_and_pauses(qt_app, clean_guide_progress):
    from riverarchitect.gui.qt.guide_window import GuideDialog

    dialog = GuideDialog()
    assert dialog.jump.count() == len(guide.STEPS)
    assert [dialog.jump.itemText(i) for i in range(dialog.jump.count())] \
        == guide.step_titles()

    dialog.jump.setCurrentIndex(4)          # the user picking from the list
    assert dialog.index == 4

    dialog.play()
    assert dialog.timer.isActive() and dialog.play_button.text() == "Pause"
    dialog._advance()                        # the tick, without waiting for it
    assert dialog.index == 5 and dialog.timer.isActive()

    dialog.next_step()                       # manual navigation pauses the playback
    assert dialog.index == 6 and not dialog.timer.isActive()
    assert dialog.play_button.text() == "Play"

    # Playing on the last step would be a timer that can never fire.
    dialog._go(len(guide.STEPS) - 1)
    dialog.play()
    assert not dialog.timer.isActive()


def test_qt_guide_saves_and_resumes_its_position(qt_app, clean_guide_progress):
    from riverarchitect.gui.qt.guide_window import GuideDialog

    dialog = GuideDialog()
    dialog._go(guide.step_index("costs"))
    assert guide.load_progress() == "costs"
    dialog.close()

    resumed = GuideDialog()
    assert resumed.step.key == "costs" and resumed.resumed

    resumed.restart()
    assert resumed.index == 0
    assert guide.load_progress() == "start"  # showing step 0 saves step 0

    fresh = GuideDialog(resume=False)
    assert fresh.index == 0 and not fresh.resumed


def test_qt_help_menu_offers_the_documentation_and_the_guide(qt_app):
    from riverarchitect.gui.qt.main import RiverArchitectWindow

    window = RiverArchitectWindow()
    menus = {menu.title().replace("&", ""): menu
             for menu in window.menuBar().findChildren(type(window.menuBar().addMenu("x")))}
    assert "Help" in menus
    entries = [action.text() for action in menus["Help"].actions() if action.text()]
    assert "Documentation" in entries
    assert guide.TITLE in entries


def tk_root():
    tk = pytest.importorskip("tkinter")
    try:
        return tk.Tk()
    except tk.TclError:
        pytest.skip("no display for tkinter")


def test_tk_guide_renders_and_navigates_every_step(clean_guide_progress):
    import tkinter as tk

    root = tk_root()
    try:
        from riverarchitect.gui.guide_window import GuideWindow
        from riverarchitect.gui.main import RiverArchitectGui

        app = RiverArchitectGui(root)
        window = GuideWindow(root, app)
        for index, step in enumerate(guide.STEPS):
            window._go(index)
            assert window.heading.cget("text") == step.title
            assert window.body.get("1.0", tk.END).strip()
            assert window.jump.current() == index
            if not step.has_tab:
                assert "disabled" in window.open_button.state()
                continue
            assert app.select_tab(step.group, step.tab), \
                "the guide names a tab that does not exist: %s > %s" % (step.group,
                                                                        step.tab)
        assert not app.select_tab("no such group")
    finally:
        root.destroy()


def test_tk_guide_jumps_plays_and_resumes(clean_guide_progress):
    root = tk_root()
    try:
        from riverarchitect.gui.guide_window import GuideWindow

        window = GuideWindow(root)
        assert list(window.jump.cget("values")) == guide.step_titles()

        window.jump_to(4)
        assert window.index == 4

        window.play()
        assert window.playing() and window.play_button.cget("text") == "Pause"
        window._advance()
        assert window.index == 5 and window.playing()

        window.previous_step()
        assert window.index == 4 and not window.playing()
        assert window.play_button.cget("text") == "Play"

        window._go(guide.step_index("maps"))
        assert guide.load_progress() == "maps"
        window.destroy()

        resumed = GuideWindow(root)
        assert resumed.step.key == "maps" and resumed.resumed
        resumed.restart()
        assert resumed.index == 0
    finally:
        root.destroy()


# -------------------------------------------------------------------------- progress

def test_progress_round_trips(clean_guide_progress):
    assert guide.load_progress() is None
    assert guide.save_progress("sharc")
    assert guide.load_progress() == "sharc"
    assert guide.clear_progress()
    assert guide.load_progress() is None


def test_a_saved_step_that_no_longer_exists_starts_from_the_beginning(clean_guide_progress):
    """Renaming a step must not strand a reader on a position that resolves to nothing."""
    guide.save_progress("a-step-that-was-removed")
    assert guide.load_progress() is None
    assert guide.step_index("a-step-that-was-removed") == 0


def test_a_corrupt_progress_file_is_not_an_error(clean_guide_progress):
    import os

    os.makedirs(os.path.dirname(guide.progress_path()), exist_ok=True)
    with open(guide.progress_path(), "w", encoding="utf-8") as handle:
        handle.write("{not json")
    assert guide.load_progress() is None


def test_progress_lives_outside_the_project_directory(clean_guide_progress):
    """Switching project directories must not lose the reader's place."""
    from riverarchitect import config

    assert not guide.progress_path().startswith(config.project_home() + os.sep)


def test_both_front_ends_render_the_same_steps(qt_app):
    """The two windows read one tuple, so they cannot describe different walkthroughs."""
    from riverarchitect.gui import guide_window as tk_guide
    from riverarchitect.gui.qt import guide_window as qt_guide

    assert tk_guide.guide.STEPS is qt_guide.guide.STEPS is guide.STEPS
