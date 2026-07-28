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

@pytest.fixture(scope="module")
def qt_app():
    qtcompat = pytest.importorskip("riverarchitect.gui.qt.qtcompat")
    if not qtcompat.QT_AVAILABLE:
        pytest.skip("no Qt binding installed")
    app = qtcompat.QApplication.instance() or qtcompat.QApplication([])
    return app


def test_qt_window_builds_every_tab(qt_app):
    from riverarchitect.gui.qt.main import RiverArchitectWindow, TABS

    window = RiverArchitectWindow()
    assert window.tabs.count() == len(TABS)
    titles = [window.tabs.tabText(i) for i in range(window.tabs.count())]
    assert titles == [factory.title for factory in TABS]


def test_qt_unit_switch_propagates_to_tabs(qt_app):
    from riverarchitect.gui.qt.main import RiverArchitectWindow

    window = RiverArchitectWindow()
    window.set_unit("si")
    assert all(tab.unit == "si" for tab in window.module_tabs)
    assert window.module_tabs[0].lod_unit.text() == "m"

    window.set_unit("us")
    assert all(tab.unit == "us" for tab in window.module_tabs)
    assert window.module_tabs[0].lod_unit.text() == "ft"


def test_level_of_detection_uses_a_dot_decimal_separator(qt_app):
    """A comma separator in a numeric field is the ambiguity this codebase exists to avoid."""
    from riverarchitect.gui.qt.main import RiverArchitectWindow

    window = RiverArchitectWindow()
    spinbox = window.module_tabs[0].lod
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
    volume_tab = window.module_tabs[0]
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
    mapping_tab = window.module_tabs[1]
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
    assert set(window.tabs) == {"Morphology (Volumes)", "Mapping"}


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
    window.set_unit("si")
    assert all(tab.unit == "si" for tab in window.module_tabs)
    assert window.module_tabs[0].l_lod_unit.cget("text") == "m"
