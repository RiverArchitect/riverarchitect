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
    assert keys == ["start", "getstarted", "lifespan", "maxlifespan", "terraforming",
                    "sharc", "stranding", "recruitment", "maps"]


def test_every_step_is_complete():
    for step in guide.STEPS:
        assert step.title and step.group and step.tab
        assert step.paragraphs(), "%s has no body" % step.key
        assert step.settings, "%s tells the reader nothing to enter" % step.key
        assert step.expect, "%s gives no way to tell whether it worked" % step.key


def test_steps_are_numbered_in_order():
    for index, step in enumerate(guide.STEPS):
        assert step.title.startswith("%d." % index)


def test_the_guide_names_the_sample_condition_everywhere_it_matters():
    for step in guide.STEPS:
        if step.key == "maxlifespan":
            continue                      # works on a directory, not on a condition
        values = " ".join(value for _label, value in step.settings)
        assert guide.CONDITION in values or "sample-data" in values


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
    pytest.importorskip("openpyxl")
    from riverarchitect.sharc import FishDatabase

    fish = FishDatabase()
    for step in guide.STEPS:
        settings = dict(step.settings)
        if "Species" not in settings or "Cottonwood" in settings["Species"]:
            continue                      # the recruitment species is not a fish
        species = fish.resolve_species(settings["Species"])
        if "Lifestage" in settings:
            assert fish.resolve_lifestage(species, settings["Lifestage"])


# ------------------------------------------------------------------------ front ends

@pytest.fixture(scope="module")
def qt_app():
    qtcompat = pytest.importorskip("riverarchitect.gui.qt.qtcompat")
    if not qtcompat.QT_AVAILABLE:
        pytest.skip("no Qt binding installed")
    return qtcompat.QApplication.instance() or qtcompat.QApplication([])


def test_qt_guide_renders_and_navigates_every_step(qt_app):
    from riverarchitect.gui.qt.guide_window import GuideDialog
    from riverarchitect.gui.qt.main import RiverArchitectWindow

    window = RiverArchitectWindow()
    dialog = GuideDialog(window)
    for index, step in enumerate(guide.STEPS):
        dialog.index = index
        dialog._show_step()
        assert dialog.heading.text() == step.title
        assert window.select_tab(step.group, step.tab), \
            "the guide names a tab that does not exist: %s > %s" % (step.group, step.tab)
    assert not window.select_tab("no such group")


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


def test_tk_guide_renders_and_navigates_every_step():
    import tkinter as tk

    root = tk_root()
    try:
        from riverarchitect.gui.guide_window import GuideWindow
        from riverarchitect.gui.main import RiverArchitectGui

        app = RiverArchitectGui(root)
        window = GuideWindow(root, app)
        for index, step in enumerate(guide.STEPS):
            window.index = index
            window._show_step()
            assert window.heading.cget("text") == step.title
            assert window.body.get("1.0", tk.END).strip()
            assert app.select_tab(step.group, step.tab), \
                "the guide names a tab that does not exist: %s > %s" % (step.group,
                                                                        step.tab)
        assert not app.select_tab("no such group")
    finally:
        root.destroy()


def test_both_front_ends_render_the_same_steps(qt_app):
    """The two windows read one tuple, so they cannot describe different walkthroughs."""
    from riverarchitect.gui import guide_window as tk_guide
    from riverarchitect.gui.qt import guide_window as qt_guide

    assert tk_guide.guide.STEPS is qt_guide.guide.STEPS is guide.STEPS
