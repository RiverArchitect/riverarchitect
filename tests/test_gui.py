"""Tests for the graphical interface: backend selection and headless construction.

These do not need a display: Qt runs with ``QT_QPA_PLATFORM=offscreen`` and the tkinter
tests are skipped when no X server is reachable.
"""

import os
import pathlib

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from riverarchitect import gui  # noqa: E402


# ------------------------------------------------------------------ backend selection

def test_at_least_one_backend_is_available():
    """A GUI must always be reachable: tkinter is in the standard library."""
    assert gui.available_backends()


def test_qt_is_preferred_when_present():
    backends = gui.available_backends()
    if "qt" not in backends:
        pytest.skip("no Qt binding installed")
    assert backends[0] == "qt"
    assert gui.select_backend() == "qt"


def test_explicit_preference_is_honoured():
    for backend in gui.available_backends():
        assert gui.select_backend(backend) == backend


def test_unknown_preference_falls_back_to_the_best_available():
    assert gui.select_backend("nonexistent") == gui.available_backends()[0]


def test_environment_variable_selects_the_backend(monkeypatch):
    backends = gui.available_backends()
    if "tk" not in backends:
        pytest.skip("tkinter not installed")
    monkeypatch.setenv("RIVERARCHITECT_GUI", "tk")
    assert gui.select_backend() == "tk"


# -------------------------------------------------------------------------- Qt window

def find_tab(window, class_name):
    """Look a tab up by class name rather than index, so tab order can change freely."""
    for tab in window.module_tabs:
        if type(tab).__name__ == class_name:
            return tab
    raise AssertionError("no %s in the window" % class_name)


@pytest.fixture(scope="module")
def qt_app():
    qtcompat = pytest.importorskip("riverarchitect.gui.qt.qtcompat")
    if not qtcompat.QT_AVAILABLE:
        pytest.skip("no Qt binding installed")
    app = qtcompat.QApplication.instance() or qtcompat.QApplication([])
    return app


def test_qt_window_builds_every_tab(qt_app):
    """Every module tab is constructed, across the top level and the nested groups."""
    from riverarchitect.gui.qt.main import RiverArchitectWindow, TAB_GROUPS, TABS

    window = RiverArchitectWindow()
    assert window.tabs.count() == len(TAB_GROUPS)
    assert len(window.module_tabs) == len(TABS)
    assert [type(tab).__name__ for tab in window.module_tabs] == \
        [factory.__name__ for factory in TABS]


def test_qt_window_exposes_every_ported_module(qt_app):
    """Every ported module must be reachable, including the nested sub-tabs."""
    from riverarchitect.gui.qt.main import RiverArchitectWindow, TABS

    window = RiverArchitectWindow()
    titles = " ".join(factory.title for factory in TABS).lower()
    for expected in ("get started", "lifespan design", "max lifespan", "terraforming",
                     "river builder", "volume assessment", "sharc", "stranding risk",
                     "recruitment", "project maker", "mapping"):
        assert expected in titles


def test_qt_groups_match_the_arcgis_structure(qt_app):
    """Top-level tabs group the modules the way the ArcGIS version did."""
    from riverarchitect.gui.qt.main import RiverArchitectWindow

    window = RiverArchitectWindow()
    top = [window.tabs.tabText(i) for i in range(window.tabs.count())]
    assert top == ["Get Started", "Lifespan", "Morphology", "Ecohydraulics",
                   "Project Maker", "Maps"]

    eco = window.groups["Ecohydraulics"]
    assert [eco.tabText(i) for i in range(eco.count())] == [
        "Habitat Area (SHArC)", "Stranding Risk", "Riparian Seedling Recruitment"]

    # Morphology carries both halves of the original ModifyTerrain plus the volumes.
    morphology = window.groups["Morphology"]
    assert [morphology.tabText(i) for i in range(morphology.count())] == [
        "Terraforming", "River Builder", "Volume Assessment"]


def test_sharc_tab_lists_the_fish_database(qt_app):
    pytest.importorskip("rasterio")
    from riverarchitect.gui.qt.main import RiverArchitectWindow

    window = RiverArchitectWindow()
    tab = find_tab(window, "SharcTab")
    species = [tab.species.itemText(i) for i in range(tab.species.count())]
    assert "Chinook Salmon" in species
    assert tab.lifestage.count() > 0


def test_qt_lifespan_tab_lists_the_default_features(qt_app):
    pytest.importorskip("rasterio")          # lifespan needs the geospatial stack
    from riverarchitect.gui.qt.main import RiverArchitectWindow
    from riverarchitect.gui.qt.qtcompat import Qt
    from riverarchitect.lifespan import FEATURES

    window = RiverArchitectWindow()
    tab = find_tab(window, "LifespanTab")
    listed = [tab.feature_list.item(i).data(Qt.ItemDataRole.UserRole)
              for i in range(tab.feature_list.count())]
    listed = [fid for fid in listed if fid]
    expected = [fid for fid, f in FEATURES.items() if f.lifespan_mapping]
    assert sorted(listed) == sorted(expected)
    assert tab.selected_features()          # something is ticked by default


def test_qt_lifespan_tab_offers_the_plant_species(qt_app):
    """The four plantings of the original are selectable by their full names."""
    pytest.importorskip("rasterio")
    from riverarchitect.gui.qt.main import RiverArchitectWindow

    window = RiverArchitectWindow()
    tab = find_tab(window, "LifespanTab")
    labels = " ".join(tab.feature_list.item(i).text()
                      for i in range(tab.feature_list.count()))
    for name in ("Box Elder", "Cottonwood", "White Alder", "Willow"):
        assert name in labels


def test_qt_max_lifespan_tab_finds_the_plant_rasters(qt_app, tmp_path):
    """Pointed at a folder of plant lifespan maps, the tab lists them and enables the run.

    The tab hands every ``lf_*.tif`` in the directory to MaxLifespan, so mapping only the
    three plants into their own folder is how a planner restricts the assessment to them.
    """
    pytest.importorskip("rasterio")
    import numpy as np

    from riverarchitect import raster
    from riverarchitect.gui.qt.main import RiverArchitectWindow

    from affine import Affine
    profile = {"driver": "GTiff", "height": 2, "width": 2, "count": 1, "dtype": "float32",
               "crs": "EPSG:32633", "transform": Affine(1.0, 0.0, 0.0, 0.0, -1.0, 2.0)}
    for fid in ("cot", "wil", "whi"):
        raster.write(str(tmp_path / ("lf_%s.tif" % fid)), np.full((2, 2), 5.0), profile)

    window = RiverArchitectWindow()
    tab = find_tab(window, "MaxLifespanTab")
    tab.lifespan_dir = str(tmp_path)
    tab._scan()
    assert "3 feature(s) found" in tab.found.text()
    for fid in ("cot", "wil", "whi"):
        assert fid in tab.found.text()
    assert tab.b_run.isEnabled()


def test_qt_unit_switch_propagates_to_tabs(qt_app):
    from riverarchitect.gui.qt.main import RiverArchitectWindow

    window = RiverArchitectWindow()
    volume_tab = find_tab(window, "VolumeTab")
    window.set_unit("si")
    assert all(tab.unit == "si" for tab in window.module_tabs)
    assert volume_tab.lod_unit.text() == "m"

    window.set_unit("us")
    assert all(tab.unit == "us" for tab in window.module_tabs)
    assert volume_tab.lod_unit.text() == "ft"


def test_level_of_detection_uses_a_dot_decimal_separator(qt_app):
    """A comma separator in a numeric field is the ambiguity this codebase exists to avoid."""
    from riverarchitect.gui.qt.main import RiverArchitectWindow

    window = RiverArchitectWindow()
    spinbox = find_tab(window, "VolumeTab").lod
    assert "," not in spinbox.text()
    assert spinbox.value() == pytest.approx(0.99)


def test_volume_tab_degrades_without_rasterio(qt_app):
    """A QGIS interpreter typically has no rasterio; the tab must say so, not fail on click."""
    from riverarchitect.gui.qt.main import RiverArchitectWindow

    try:
        import rasterio  # noqa: F401
        has_rasterio = True
    except ImportError:
        has_rasterio = False

    window = RiverArchitectWindow()
    volume_tab = find_tab(window, "VolumeTab")
    if has_rasterio:
        assert volume_tab.b_run.isEnabled()
    else:
        assert not volume_tab.b_run.isEnabled()
        assert "geospatial stack" in volume_tab.results.toPlainText()


def test_mapping_tab_degrades_without_qgis(qt_app):
    """Without QGIS the tab must explain itself, not raise."""
    from riverarchitect.gui.qt.main import RiverArchitectWindow
    from riverarchitect.mapping import QGIS_AVAILABLE

    window = RiverArchitectWindow()
    mapping_tab = find_tab(window, "MappingTab")
    if QGIS_AVAILABLE:
        assert mapping_tab.b_run.isEnabled()
    else:
        assert not mapping_tab.b_run.isEnabled()
        assert "QGIS" in mapping_tab.status.toPlainText()


# --------------------------------------------------------------------- tkinter window

@pytest.fixture
def tk_root():
    tkinter = pytest.importorskip("tkinter")
    try:
        root = tkinter.Tk()
    except tkinter.TclError:
        pytest.skip("no display for tkinter")
    yield root
    root.destroy()


def test_tk_window_builds_every_tab(tk_root):
    from riverarchitect.gui.main import RiverArchitectGui

    window = RiverArchitectGui(tk_root)
    titles = " ".join(window.tabs).lower()
    for expected in ("get started", "lifespan design", "max lifespan", "terraforming",
                     "river builder", "volume assessment", "sharc", "stranding risk",
                     "recruitment", "project maker", "mapping"):
        assert expected in titles


def test_both_front_ends_offer_the_same_modules():
    """The fallback must not silently lack modules the Qt interface has.

    Compared through the group declarations rather than by building both windows, so the
    check does not need a display.
    """
    qtcompat = pytest.importorskip("riverarchitect.gui.qt.qtcompat")
    if not qtcompat.QT_AVAILABLE:
        pytest.skip("no Qt binding installed")
    from riverarchitect.gui.main import TAB_GROUPS as tk_groups
    from riverarchitect.gui.qt.main import TAB_GROUPS as qt_groups

    def shape(groups):
        return [(group, tuple(factory.title for factory in factories))
                for group, factories in groups]

    assert shape(tk_groups) == shape(qt_groups)


def test_tk_tab_switching_does_not_move_the_window(tk_root):
    """The original resized and re-centred the window on every tab change."""
    from riverarchitect.gui.main import RiverArchitectGui

    window = RiverArchitectGui(tk_root)
    tk_root.update()
    geometries = set()
    for index in (0, 1, 0, 1):
        window.notebook.select(index)
        tk_root.update()
        geometries.add(tk_root.winfo_geometry())
    assert len(geometries) == 1


def test_tk_unit_switch_propagates_to_tabs(tk_root):
    from riverarchitect.gui.main import RiverArchitectGui

    window = RiverArchitectGui(tk_root)
    volume_tab = next(tab for tab in window.module_tabs
                      if type(tab).__name__ == "VolumeGui")
    window.set_unit("si")
    assert all(tab.unit == "si" for tab in window.module_tabs)
    assert volume_tab.l_lod_unit.cget("text") == "m"


# ------------------------------------------------------------------------ Tools menu

def test_every_console_script_tool_is_in_the_tools_menu():
    """A tool that only has a command line is unreachable for most of the audience.

    Driven off the packaged entry points rather than a hand-kept list, so adding a console
    script without a menu entry fails here instead of going unnoticed.
    """
    import re

    from riverarchitect.gui.toolsmenu import TOOLS

    pyproject = pathlib.Path(__file__).resolve().parents[1] / "pyproject.toml"
    section = pyproject.read_text(encoding="utf-8").split("[project.scripts]", 1)[1]
    section = section.split("\n[", 1)[0]
    scripts = dict(re.findall(r'^([\w-]+)\s*=\s*"([\w.]+):', section, flags=re.M))
    scripts.pop("riverarchitect", None)      # the interface itself, not a tool

    in_menu = {module for _label, _handler, module in TOOLS}
    assert set(scripts.values()) - in_menu == set()


def test_tools_menu_modules_all_import():
    """Each entry must name a module that exists; a typo here is a dead menu item."""
    import importlib

    from riverarchitect.gui.toolsmenu import TOOLS

    for _label, _handler, module in TOOLS:
        assert importlib.import_module(module) is not None


def test_both_front_ends_implement_every_tool_handler():
    """Neither interface may lack a wizard the other offers."""
    from riverarchitect.gui.main import RiverArchitectGui
    from riverarchitect.gui.toolsmenu import handler_names

    for name in handler_names():
        assert callable(getattr(RiverArchitectGui, name, None)), name

    qtcompat = pytest.importorskip("riverarchitect.gui.qt.qtcompat")
    if not qtcompat.QT_AVAILABLE:
        pytest.skip("no Qt binding installed")
    from riverarchitect.gui.qt.main import RiverArchitectWindow

    for name in handler_names():
        assert callable(getattr(RiverArchitectWindow, name, None)), name


def test_qt_tools_menu_lists_every_tool(qt_app):
    from riverarchitect.gui.qt.main import RiverArchitectWindow
    from riverarchitect.gui.toolsmenu import TOOLS

    window = RiverArchitectWindow()
    menu = window.menus["&Tools"]
    assert [action.text() for action in menu.actions()] == [label for label, _h, _m in TOOLS]


def test_tk_tools_menu_lists_every_tool(tk_root):
    from riverarchitect.gui.main import RiverArchitectGui
    from riverarchitect.gui.toolsmenu import TOOLS

    RiverArchitectGui(tk_root)
    menu_bar = tk_root.nametowidget(tk_root.cget("menu"))
    tools = menu_bar.nametowidget(menu_bar.entrycget("Tools", "menu"))
    labels = [tools.entrycget(index, "label") for index in range(tools.index("end") + 1)]
    assert labels == [label for label, _handler, _module in TOOLS]


def test_format_taux_reports_paths_and_regime_shares(tmp_path):
    from riverarchitect.gui.toolsmenu import format_taux

    report = format_taux({
        "theta84": str(tmp_path / "q_theta84.tif"),
        "regime": str(tmp_path / "q_regime.tif"),
        "_summary": {"invalid": 0, "Rickenmann-Recking": 30, "blended": 10,
                     "Keulegan-Einstein": 60},
    })
    assert "q_theta84.tif" in report
    assert "_summary" not in report
    # 30, 10 and 60 of 100 wetted cells; the invalid ones stay out of the denominator.
    assert "30.0 %" in report and "10.0 %" in report and "60.0 %" in report


LYRX = """{"layerDefinitions": [{"name": "lf_sym", "colorizer": {
  "type": "CIMRasterClassifyColorizer", "field": "Value", "classBreaks": [
    {"upperBound": 10, "label": "0 - 10", "color": {"type": "CIMRGBColor",
     "values": [255, 0, 0, 100]}},
    {"upperBound": 20, "label": "10 - 20", "color": {"type": "CIMRGBColor",
     "values": [0, 255, 0, 100]}}]}}]}"""


def test_tk_lyrx_wizard_writes_a_qml(tk_root, tmp_path, monkeypatch):
    """The wizard drives the same convert() the console script does."""
    from riverarchitect.gui import main as tk_main
    from riverarchitect.gui.main import RiverArchitectGui

    source = tmp_path / "symbology.lyrx"
    source.write_text(LYRX, encoding="utf-8")
    target = tmp_path / "symbology.qml"
    shown = {}

    monkeypatch.setattr(tk_main, "askopenfilename", lambda **kw: str(source))
    monkeypatch.setattr(tk_main, "asksaveasfilename", lambda **kw: str(target))
    monkeypatch.setattr(tk_main, "showinfo", lambda title, text: shown.update(text=text))

    RiverArchitectGui(tk_root).run_lyrx2qml()

    assert target.is_file()
    assert "singlebandpseudocolor" in target.read_text(encoding="utf-8")
    # convert() reports what it found on stdout; the wizard must surface that, not drop it.
    assert "2 class breaks" in shown["text"]


def test_tk_lyrx_wizard_reports_an_unusable_file(tk_root, tmp_path, monkeypatch):
    from riverarchitect.gui import main as tk_main
    from riverarchitect.gui.main import RiverArchitectGui

    source = tmp_path / "empty.lyrx"
    source.write_text('{"layerDefinitions": []}', encoding="utf-8")
    warned = {}

    monkeypatch.setattr(tk_main, "askopenfilename", lambda **kw: str(source))
    monkeypatch.setattr(tk_main, "asksaveasfilename", lambda **kw: str(tmp_path / "o.qml"))
    monkeypatch.setattr(tk_main, "showwarning", lambda title, text: warned.update(text=text))

    RiverArchitectGui(tk_root).run_lyrx2qml()

    assert not (tmp_path / "o.qml").exists()
    assert "no colorizer" in warned["text"]


def test_tk_taux_wizard_rejects_missing_rasters(tk_root, tmp_path):
    """Bad input must be refused on the interface thread, before any work starts."""
    import tkinter
    from tkinter import ttk

    pytest.importorskip("rasterio")
    from riverarchitect.gui.main import RiverArchitectGui

    window = RiverArchitectGui(tk_root)
    window.run_taux()
    tk_root.update()

    def walk(widget):
        for child in widget.winfo_children():
            yield child
            yield from walk(child)

    dialog = [w for w in walk(tk_root) if isinstance(w, tkinter.Toplevel)][-1]
    # ttk.Combobox subclasses tkinter.Entry, so the grain-kind picker has to be excluded.
    entries = [w for w in walk(dialog)
               if isinstance(w, tkinter.Entry) and not isinstance(w, ttk.Entry)]
    assert len(entries) == 4

    text = [w for w in walk(dialog) if isinstance(w, tkinter.Text)][0]
    button = [w for w in walk(dialog)
              if isinstance(w, tkinter.Button) and w.cget("text") == "Compute"][0]

    entries[3].insert(0, str(tmp_path / "out"))
    button.invoke()
    assert "Not a readable file" in text.get("1.0", "end")

    # A prefix left empty is refused too, rather than writing "_theta84.tif" into the cwd.
    # The three rasters only have to exist for this check; they are never opened.
    for index, name in enumerate(("u.tif", "h.tif", "d.tif")):
        (tmp_path / name).touch()
        entries[index].insert(0, str(tmp_path / name))
    entries[3].delete(0, "end")
    button.invoke()
    assert "output prefix" in text.get("1.0", "end")
