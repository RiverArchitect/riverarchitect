"""Qt main window: a tabbed shell with one tab per module.

Structurally the same as the tkinter window it replaces, with the differences a real
toolkit makes possible: the menu bar belongs to the window rather than being rebuilt on
every tab change, the status bar reports the project directory, and a tab that fails to
construct is replaced by a message instead of taking the window down.
"""

import glob
import logging
import os
import threading

from ... import __version__, config, guide
from ..toolsmenu import TOOLS, format_taux, unit_name
from .qtcompat import (
    QAction, QApplication, QComboBox, QDesktopServices, QDialog, QDoubleSpinBox,
    QFileDialog, QFont, QFormLayout, QHBoxLayout, QIcon, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPlainTextEdit, QPushButton, QTabWidget, QUrl, QVBoxLayout, QWidget,
    Qt, QT_BINDING, Signal, exec_app, exec_dialog,
)
from .getstarted_tab import GetStartedTab
from .lifespan_tab import LifespanTab
from .mapping_tab import MappingTab
from .projectmaker_tab import ProjectMakerTab
from .maxlifespan_tab import MaxLifespanTab
from .recruitment_tab import RecruitmentTab
from .riverbuilder_tab import RiverBuilderTab
from .sharc_tab import SharcTab
from .stranding_tab import StrandingTab
from .terraforming_tab import TerraformingTab
from .volume_tab import VolumeTab

__all__ = ["RiverArchitectWindow", "run", "TAB_GROUPS", "TABS"]

#: Top-level tabs and their sub-tabs, reproducing the grouping of the ArcGIS version:
#: a module either stands alone or sits inside a themed group. ``None`` means the entry is
#: a single tab rather than a group.
TAB_GROUPS = (
    ("Get Started", (GetStartedTab,)),
    ("Lifespan", (LifespanTab, MaxLifespanTab)),
    ("Morphology", (TerraformingTab, RiverBuilderTab, VolumeTab)),
    ("Ecohydraulics", (SharcTab, StrandingTab, RecruitmentTab)),
    ("Project Maker", (ProjectMakerTab,)),
    ("Maps", (MappingTab,)),
)

#: Flat list of every module tab, in the order they appear.
TABS = tuple(factory for _group, factories in TAB_GROUPS for factory in factories)


class RiverArchitectWindow(QMainWindow):
    """Top-level window holding one tab per module."""

    #: Emitted from a worker thread when a Tools-menu run finishes. Internal.
    _tool_finished = Signal(object, object)

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("riverarchitect")
        self._tool_callback = None
        self._tool_finished.connect(self._on_tool_finished)

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
        # Keyed by title, so a menu can be reached again after it is built. Going back
        # through `QAction.menu()` instead is a trap: PySide hands that wrapper ownership
        # of the QMenu and deletes the C++ object when the wrapper is collected.
        self.menus = {}

        project_menu = self._add_menu("&Project")
        action = QAction("Set project directory ...", self)
        action.triggered.connect(self.choose_project_home)
        project_menu.addAction(action)
        project_menu.addSeparator()
        action = QAction("&Quit", self)
        action.setShortcut("Ctrl+Q")
        action.triggered.connect(self.close)
        project_menu.addAction(action)

        units_menu = self._add_menu("&Units")
        self.unit_actions = {}
        for unit, label in (("us", "U.S. customary"), ("si", "SI (metric)")):
            action = QAction(label, self, checkable=True)
            action.setChecked(unit == "us")
            action.triggered.connect(lambda _checked=False, u=unit: self.set_unit(u))
            units_menu.addAction(action)
            self.unit_actions[unit] = action

        tools_menu = self._add_menu("&Tools")
        for label, handler, _module in TOOLS:
            action = QAction(label, self)
            action.triggered.connect(getattr(self, handler))
            tools_menu.addAction(action)

        help_menu = self._add_menu("&Help")
        action = QAction("Documentation", self)
        action.setShortcut("F1")
        action.triggered.connect(self.open_documentation)
        help_menu.addAction(action)
        action = QAction(guide.TITLE, self)
        action.triggered.connect(self.open_live_guide)
        help_menu.addAction(action)
        help_menu.addSeparator()
        action = QAction("About", self)
        action.triggered.connect(self.show_about)
        help_menu.addAction(action)

    def _add_menu(self, title):
        """Add a top-level menu and keep a reference to it. See :meth:`_build_menus`."""
        menu = self.menuBar().addMenu(title)
        self.menus[title] = menu
        return menu

    # -------------------------------------------------------------- navigation

    def select_tab(self, group, tab=None):
        """Bring a module tab to the front. Used by the Live Guide.

        Args:
            group (str): the top-level tab, as :data:`TAB_GROUPS` names it.
            tab (str): the module tab within it. Defaults to the group itself.

        Returns:
            bool: True when the tab was found and selected.
        """
        tab = tab or group
        for index in range(self.tabs.count()):
            if self.tabs.tabText(index) != group:
                continue
            self.tabs.setCurrentIndex(index)
            inner = self.groups.get(group)
            if inner is None:
                return True
            for inner_index in range(inner.count()):
                if inner.tabText(inner_index) == tab:
                    inner.setCurrentIndex(inner_index)
                    return True
            return tab == group
        return False

    # ----------------------------------------------------------------- actions

    @staticmethod
    def open_documentation():
        QDesktopServices.openUrl(QUrl(guide.DOCS_URL))

    def open_live_guide(self):
        """Open the step-by-step walkthrough of the sample-data example."""
        from .guide_window import open_guide
        open_guide(self)

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

    # ------------------------------------------------------------------- background

    def run_tool_in_background(self, work, on_success, on_error):
        """Run ``work()`` off the interface thread, delivering the outcome back on it.

        The same contract as :meth:`riverarchitect.gui.qt.base.RaTab.run_in_background`,
        which belongs to the tabs rather than to the window. Tools-menu wizards are windows
        of their own and need it too: a shear-stress run over a whole condition takes long
        enough that a frozen menu bar would look like a crash.
        """
        self._tool_callback = (on_success, on_error)

        def runner():
            try:
                self._tool_finished.emit(work(), None)
            except Exception as exc:  # surfaced to the user by the error callback
                self._tool_finished.emit(None, exc)

        threading.Thread(target=runner, daemon=True).start()

    def _on_tool_finished(self, result, error):
        if self._tool_callback is None:
            return
        on_success, on_error = self._tool_callback
        self._tool_callback = None
        if error is not None:
            on_error(error)
        else:
            on_success(result)

    # ------------------------------------------------------------------ tool wizards

    def run_taux(self):
        """Compute the regime-aware dimensionless bed shear stress from three rasters.

        A wizard rather than a tab because it works on loose rasters: the point of the tool
        is to check model output *before* it has been organised into a condition folder,
        which is what the Get Started tab would require.
        """
        from ...tools import taux

        if not taux.dependencies_available():
            QMessageBox.critical(self, "Bed shear stress",
                                 "This tool needs numpy and rasterio, which could not be "
                                 "imported.")
            return

        unit = self.current_unit()
        dialog = QDialog(self)
        dialog.setWindowTitle("Bed shear stress")
        layout = QVBoxLayout(dialog)
        note = QLabel(
            "Shields stress from depth-averaged velocity, water depth and grain size. The "
            "velocity raster defines the output grid; the other two are resampled onto it, "
            "so they need not share an extent. All three must be in %s." % unit_name(unit))
        note.setWordWrap(True)
        layout.addWidget(note)

        form = QFormLayout()
        pickers = {}
        for name, label in (("velocity", "Velocity raster"), ("depth", "Water depth raster"),
                            ("grains", "Grain size raster")):
            pickers[name] = self._file_row(dialog, form, label)

        grain_kind = QComboBox(dialog)
        for value, label in (("dmean", "mean grain size (D84 = 2.2 Dmean)"),
                             ("d50", "median grain size (D84 = 2.2 D50)"),
                             ("d84", "measured D84")):
            grain_kind.addItem(label, value)
        form.addRow("The grain raster holds", grain_kind)

        prefix = QLineEdit(dialog)
        prefix.setPlaceholderText("out/q000550")
        prefix_button = QPushButton("Browse ...", dialog)
        prefix_button.clicked.connect(lambda: self._pick_prefix(dialog, prefix))
        prefix_row = QHBoxLayout()
        prefix_row.addWidget(prefix, 1)
        prefix_row.addWidget(prefix_button)
        form.addRow("Output prefix", prefix_row)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        run = QPushButton("Compute", dialog)
        close = QPushButton("Close", dialog)
        buttons.addStretch(1)
        buttons.addWidget(run)
        buttons.addWidget(close)
        layout.addLayout(buttons)

        output = QPlainTextEdit(dialog)
        output.setReadOnly(True)
        output.setFont(QFont("monospace"))
        output.setMinimumHeight(200)
        output.setPlainText("Choose three rasters and an output prefix, then Compute.")
        layout.addWidget(output)

        def compute():
            paths = {name: field.text().strip() for name, field in pickers.items()}
            missing = [name for name, path in paths.items() if not os.path.isfile(path)]
            if missing:
                output.setPlainText("Not a readable file: %s." % ", ".join(sorted(missing)))
                return
            if not prefix.text().strip():
                output.setPlainText("Give an output prefix; the four rasters are named "
                                    "after it.")
                return
            run.setEnabled(False)
            output.setPlainText("Computing ...")
            self.run_tool_in_background(
                lambda: taux.compute(paths["velocity"], paths["depth"], paths["grains"],
                                     prefix.text().strip(),
                                     grain_kind=grain_kind.currentData(), unit=unit),
                lambda written: (run.setEnabled(True),
                                 output.setPlainText(format_taux(written))),
                lambda exc: (run.setEnabled(True),
                             output.setPlainText("Could not compute:\n%s" % exc)))

        run.clicked.connect(compute)
        close.clicked.connect(dialog.close)
        exec_dialog(dialog)

    def run_lyrx2qml(self):
        """Convert an ArcGIS Pro layer file to a QGIS layer style."""
        import contextlib
        import io

        from ...tools import lyrx2qml

        source, _ = QFileDialog.getOpenFileName(
            self, "Select an ArcGIS Pro layer file", config.project_home(),
            "ArcGIS layer files (*.lyrx);;All files (*)")
        if not source:
            return
        target, _ = QFileDialog.getSaveFileName(
            self, "Write the QGIS layer style to",
            os.path.splitext(source)[0] + ".qml", "QGIS layer styles (*.qml)")
        if not target:
            return

        # convert() reports what it found on stdout, which is the useful part of the
        # answer: which colorizer, and how many class breaks came across.
        log = io.StringIO()
        try:
            with contextlib.redirect_stdout(log):
                written = lyrx2qml.convert(source, target)
        except Exception as exc:
            self.logger.error("Could not convert %s: %s", source, exc)
            QMessageBox.critical(self, "lyrx to qml", "Could not convert:\n%s" % exc)
            return

        if written is None:
            QMessageBox.warning(self, "lyrx to qml",
                                "Nothing was written.\n\n%s" % log.getvalue().strip())
            return
        QMessageBox.information(self, "lyrx to qml",
                                "Wrote %s\n\n%s" % (written, log.getvalue().strip()))

    def _file_row(self, dialog, form, label):
        """Add a read-only-ish path field with a Browse button, and return the field."""
        field = QLineEdit(dialog)
        button = QPushButton("Browse ...", dialog)

        def browse():
            path, _ = QFileDialog.getOpenFileName(
                dialog, "Select the %s" % label.lower(), config.dir_conditions(),
                "Raster files (*.tif *.tiff *.flt *.asc);;All files (*)")
            if path:
                field.setText(path)

        button.clicked.connect(browse)
        row = QHBoxLayout()
        row.addWidget(field, 1)
        row.addWidget(button)
        form.addRow(label, row)
        return field

    def _pick_prefix(self, dialog, field):
        path, _ = QFileDialog.getSaveFileName(
            dialog, "Output prefix (the suffixes are added for you)",
            field.text() or config.project_home(), "All files (*)")
        if path:
            field.setText(path)

    def current_unit(self):
        """The unit system the Units menu is set to.

        The window keeps no unit attribute of its own; the checked action is the single
        source of truth, the same one :meth:`set_unit` drives.
        """
        return next((key for key, action in self.unit_actions.items()
                     if action.isChecked()), "us")

    def run_pool_riffle(self):
        """Size a self-maintaining pool-riffle sequence from a channel and a target depth.

        A dialog rather than a tab: the calculation takes a cross-section, not a condition,
        so it has nothing to read from the project directory and nothing to write into it.
        """
        from ...poolriffle import design_pool_riffle, format_design

        unit = self.current_unit()
        labels = config.unit_labels(unit)
        fields = (
            ("d50", "Median grain size (%s)" % labels["length"], 0.3, 6),
            ("slope", "Channel bed slope (-)", 0.004, 5),
            ("width", "Channel base width (%s)" % labels["length"], 79.0, 3),
            ("pool_depth", "Target residual pool depth (%s)" % labels["length"], 3.0, 3),
            ("bank_slope", "Bank slope 1:m (-)", 2.58, 2),
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("Pool-riffle designer")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(
            "Sizes a pool-riffle sequence that maintains itself: the widths that\n"
            "produce the target pool depth at the discharge which just mobilises\n"
            "the bed. Values are in %s." % labels["length"]))
        form = QFormLayout()
        boxes = {}
        for name, label, default, decimals in fields:
            box = QDoubleSpinBox(dialog)
            box.setDecimals(decimals)
            box.setRange(1e-6, 1e6)
            box.setValue(default)
            form.addRow(label, box)
            boxes[name] = box
        layout.addLayout(form)

        buttons = QHBoxLayout()
        compute = QPushButton("Compute", dialog)
        close = QPushButton("Close", dialog)
        buttons.addStretch(1)
        buttons.addWidget(compute)
        buttons.addWidget(close)
        layout.addLayout(buttons)

        output = QPlainTextEdit(dialog)
        output.setReadOnly(True)
        output.setFont(QFont("monospace"))
        output.setMinimumHeight(260)
        layout.addWidget(output)

        def compute_design():
            try:
                design = design_pool_riffle(
                    d50=boxes["d50"].value(), slope=boxes["slope"].value(),
                    base_width=boxes["width"].value(),
                    target_residual_depth=boxes["pool_depth"].value(),
                    bank_slope=boxes["bank_slope"].value(), unit=unit)
            except ValueError as exc:
                output.setPlainText("Cannot design this channel:\n%s" % exc)
                return
            output.setPlainText(format_design(design))

        compute.clicked.connect(compute_design)
        close.clicked.connect(dialog.close)
        compute_design()
        exec_dialog(dialog)

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
    app.setApplicationDisplayName("River Architect")
    app.setApplicationVersion(__version__)
    app.setDesktopFileName(config.APP_ID)

    icon = QIcon(config.icon_path())
    app.setWindowIcon(icon)

    window = RiverArchitectWindow()
    window.setWindowIcon(icon)
    window.show()
    return exec_app(app)
    
