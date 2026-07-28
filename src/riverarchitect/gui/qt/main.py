"""Qt main window: a tabbed shell with one tab per module.

Structurally the same as the tkinter window it replaces, with the differences a real
toolkit makes possible: the menu bar belongs to the window rather than being rebuilt on
every tab change, the status bar reports the project directory, and a tab that fails to
construct is replaced by a message instead of taking the window down.
"""

import glob
import logging
import os

from ... import __version__, config
from .qtcompat import (QAction, QApplication, QDesktopServices, QFileDialog, QLabel,
                       QMainWindow, QMessageBox, QTabWidget, QUrl, QVBoxLayout, QWidget,
                       Qt, QT_BINDING, exec_app)
from .getstarted_tab import GetStartedTab
from .lifespan_tab import LifespanTab
from .mapping_tab import MappingTab
from .maxlifespan_tab import MaxLifespanTab
from .recruitment_tab import RecruitmentTab
from .sharc_tab import SharcTab
from .stranding_tab import StrandingTab
from .volume_tab import VolumeTab

__all__ = ["RiverArchitectWindow", "run", "TAB_GROUPS", "TABS"]

#: Top-level tabs and their sub-tabs, reproducing the grouping of the ArcGIS version:
#: a module either stands alone or sits inside a themed group. ``None`` means the entry is
#: a single tab rather than a group.
TAB_GROUPS = (
    ("Get Started", (GetStartedTab,)),
    ("Lifespan", (LifespanTab, MaxLifespanTab)),
    ("Morphology", (VolumeTab,)),
    ("Ecohydraulics", (SharcTab, StrandingTab, RecruitmentTab)),
    ("Maps", (MappingTab,)),
)

#: Flat list of every module tab, in the order they appear.
TABS = tuple(factory for _group, factories in TAB_GROUPS for factory in factories)


class RiverArchitectWindow(QMainWindow):
    """Top-level window holding one tab per module."""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("riverarchitect")

        self.setWindowTitle("River Architect %s" % __version__)
        self.resize(880, 620)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.setCentralWidget(self.tabs)

        self.module_tabs = []
        self.groups = {}
        for group, factories in TAB_GROUPS:
            if len(factories) == 1:
                # A group of one is just a tab; nesting it would only add a click.
                self.tabs.addTab(self._make_tab(factories[0]), group)
                continue
            inner = QTabWidget()
            inner.setDocumentMode(True)
            for factory in factories:
                inner.addTab(self._make_tab(factory), factory.title)
            self.groups[group] = inner
            self.tabs.addTab(inner, group)

        self._build_menus()

        self.project_label = QLabel()
        self.statusBar().addPermanentWidget(self.project_label)
        self._update_status()

    def _make_tab(self, factory):
        """Build a module tab, or a message standing in for one that could not load."""
        try:
            tab = factory()
        except Exception as exc:  # a broken module must not take the window down
            self.logger.error("Could not load the %s tab: %s", factory.title, exc)
            return self._placeholder(factory.title, exc)
        self.module_tabs.append(tab)
        return tab

    def _placeholder(self, label, exc):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)
        heading = QLabel("The %s tab could not be loaded." % label)
        font = heading.font()
        font.setBold(True)
        heading.setFont(font)
        layout.addWidget(heading)
        detail = QLabel(str(exc))
        detail.setWordWrap(True)
        detail.setStyleSheet("color: palette(mid);")
        layout.addWidget(detail)
        layout.addStretch(1)
        return widget

    # ------------------------------------------------------------------- menus

    def _build_menus(self):
        project_menu = self.menuBar().addMenu("&Project")
        action = QAction("Set project directory ...", self)
        action.triggered.connect(self.choose_project_home)
        project_menu.addAction(action)
        project_menu.addSeparator()
        action = QAction("&Quit", self)
        action.setShortcut("Ctrl+Q")
        action.triggered.connect(self.close)
        project_menu.addAction(action)

        units_menu = self.menuBar().addMenu("&Units")
        self.unit_actions = {}
        for unit, label in (("us", "U.S. customary"), ("si", "SI (metric)")):
            action = QAction(label, self, checkable=True)
            action.setChecked(unit == "us")
            action.triggered.connect(lambda _checked=False, u=unit: self.set_unit(u))
            units_menu.addAction(action)
            self.unit_actions[unit] = action

        tools_menu = self.menuBar().addMenu("&Tools")
        action = QAction("Reconcile NoData in a condition ...", self)
        action.triggered.connect(self.run_reconcile_nodata)
        tools_menu.addAction(action)

        help_menu = self.menuBar().addMenu("&Help")
        action = QAction("Documentation", self)
        action.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://riverarchitect.readthedocs.io/")))
        help_menu.addAction(action)
        action = QAction("About", self)
        action.triggered.connect(self.show_about)
        help_menu.addAction(action)

    # ----------------------------------------------------------------- actions

    def set_unit(self, unit):
        """Switch the unit system for every tab."""
        for key, action in self.unit_actions.items():
            action.setChecked(key == unit)
        for tab in self.module_tabs:
            tab.set_unit(unit)

    def choose_project_home(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select the River Architect project directory", config.project_home())
        if not directory:
            return
        config.set_project_home(directory)
        for tab in self.module_tabs:
            tab.on_project_home_change()
        self._update_status()
        conditions = self.module_tabs[0].condition_list if self.module_tabs else []
        QMessageBox.information(
            self, "Project directory",
            "Project directory set to:\n%s\n\n%d condition(s) found."
            % (directory, len(conditions)))

    def run_reconcile_nodata(self):
        from ...tools import reconcile_nodata

        directory = QFileDialog.getExistingDirectory(
            self, "Select a condition folder to reconcile", config.dir_conditions())
        if not directory:
            return
        rasters = sorted(glob.glob(os.path.join(directory, "*.tif")))
        if not rasters:
            QMessageBox.warning(self, "Reconcile NoData",
                                "No GeoTIFFs found in\n%s" % directory)
            return
        confirm = QMessageBox.question(
            self, "Reconcile NoData",
            "Rewrite %d raster(s) in\n%s\nto NoData = %s?\n\n"
            "The NoData mask is preserved exactly; only the sentinel changes."
            % (len(rasters), directory, config.NODATA))
        if confirm != QMessageBox.StandardButton.Yes:
            return

        changed = failed = 0
        for path in rasters:
            try:
                if reconcile_nodata.reconcile(path):
                    changed += 1
            except Exception as exc:
                failed += 1
                self.logger.error("Could not reconcile %s: %s", path, exc)
        message = "%d raster(s) updated." % changed
        if failed:
            message += "\n%d could not be read; see the log." % failed
        QMessageBox.information(self, "Reconcile NoData", message)

    def show_about(self):
        QMessageBox.about(
            self, "About River Architect",
            "<b>River Architect %s</b><br><br>"
            "Open-source analysis and design of fluvial ecosystems.<br>"
            "<a href='https://riverarchitect.readthedocs.io/'>"
            "riverarchitect.readthedocs.io</a><br><br>"
            "Qt binding: %s<br>"
            "Project directory:<br>%s" % (__version__, QT_BINDING, config.project_home()))

    def _update_status(self):
        self.project_label.setText("Project: %s" % config.project_home())


def run(argv=None):
    """Create the application, show the window and run the event loop."""
    app = QApplication.instance() or QApplication(argv or [])
    app.setApplicationName("River Architect")
    app.setApplicationVersion(__version__)

    window = RiverArchitectWindow()
    window.show()
    return exec_app(app)
