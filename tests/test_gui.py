"""Tests for the graphical interface: backend selection and headless construction.

These do not need a display: Qt runs with ``QT_QPA_PLATFORM=offscreen`` and the tkinter
tests are skipped when no X server is reachable.
"""

import os

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
    for expected in ("get started", "lifespan design", "max lifespan", "volume assessment",
                     "sharc", "stranding risk", "recruitment", "mapping"):
        assert expected in titles


def test_qt_groups_match_the_arcgis_structure(qt_app):
    """Top-level tabs group the modules the way the ArcGIS version did."""
    from riverarchitect.gui.qt.main import RiverArchitectWindow

    window = RiverArchitectWindow()
    top = [window.tabs.tabText(i) for i in range(window.tabs.count())]
    assert top == ["Get Started", "Lifespan", "Morphology", "Ecohydraulics", "Maps"]

    eco = window.groups["Ecohydraulics"]
    assert [eco.tabText(i) for i in range(eco.count())] == [
        "Habitat Area (SHArC)", "Stranding Risk", "Riparian Seedling Recruitment"]


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
    for expected in ("get started", "lifespan design", "max lifespan", "volume assessment",
                     "sharc", "stranding risk", "recruitment", "mapping"):
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
