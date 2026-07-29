"""Get started tab: prepare a condition's derived rasters."""

import os

from ... import config
from .base import RaTab
from .qtcompat import (QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
                       QPlainTextEdit, QProgressBar, QPushButton, QVBoxLayout)

__all__ = ["GetStartedTab"]

#: Product list and notes, mirrored from :mod:`riverarchitect.preprocessing` so that the tab
#: can still be built when the geospatial stack is missing - importing preprocessing pulls in
#: rasterio, and a tab must disable itself rather than fail to construct.
FALLBACK_PRODUCTS = (("detrended DEM", "detrended"),)


def _products():
    try:
        from ... import preprocessing as pre
        return pre.PRODUCTS, pre.PRODUCT_NOTES
    except ImportError:
        return FALLBACK_PRODUCTS, {}


class GetStartedTab(RaTab):
    """Build the derived rasters the analysis modules read."""

    title = "Get Started"
    subtitle = ("Prepares a condition. These are not analyses in their own right - they "
                "produce the terrain products that lifespan mapping, habitat suitability "
                "and recruitment all depend on.")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.output_dir = ""
        self._discharges = []
        self.flow_series = ""
        self._build()

    def _build(self):
        layout = QVBoxLayout(self.body)
        layout.setContentsMargins(0, 0, 0, 0)

        inputs = QGroupBox("Input")
        form = QFormLayout(inputs)

        self.condition = QComboBox()
        self.condition.addItems(self.condition_list)
        self.condition.currentTextChanged.connect(self._scan_condition)
        form.addRow("Condition:", self.condition)

        self.product = QComboBox()
        products, self._notes = _products()
        for label, key in products:
            self.product.addItem(label, key)
        self.product.currentIndexChanged.connect(self._describe_product)
        form.addRow("Build:", self.product)

        self.discharge = QComboBox()
        self.discharge.setToolTip("The discharge whose wetted area defines the thalweg or "
                                  "the water surface. Use a low, in-channel flow.")
        form.addRow("Reference discharge:", self.discharge)

        self.method = QComboBox()
        for label, key in (("Nearest neighbour", "nearest"), ("IDW", "idw"),
                           ("Kriging", "kriging")):
            self.method.addItem(label, key)
        self.method.setToolTip("How the surface is extrapolated beyond the wetted area. "
                               "Nearest neighbour is what the ArcGIS version did.")
        form.addRow("Interpolation:", self.method)

        self.b_series = QPushButton("Select flow record ...")
        self.b_series.clicked.connect(self.select_series)
        self.b_series.setToolTip("A CSV or workbook of dates and mean daily discharge. "
                                 "Only the flow analysis needs it.")
        form.addRow("Daily flow record:", self.b_series)

        self.b_output = QPushButton("Select directory ... (optional)")
        self.b_output.clicked.connect(self.select_output)
        form.addRow("Output directory:", self.b_output)

        self.info = QLabel("")
        self.info.setWordWrap(True)
        self.info.setStyleSheet("color: palette(mid);")
        form.addRow("", self.info)

        layout.addWidget(inputs)

        run_row = QHBoxLayout()
        self.b_run = QPushButton("Build")
        self.b_run.clicked.connect(self.run_analysis)
        run_row.addWidget(self.b_run)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setTextVisible(False)
        self.progress.hide()
        run_row.addWidget(self.progress, 1)
        layout.addLayout(run_row)

        self.results = QPlainTextEdit()
        self.results.setReadOnly(True)
        font = self.results.font()
        font.setFamily("monospace")
        self.results.setFont(font)
        self.results.setPlaceholderText("Results appear here.")
        layout.addWidget(self.results, 1)

        self._check_dependencies()
        self._scan_condition()
        self._describe_product()

    # ------------------------------------------------------------------ callbacks

    def _check_dependencies(self):
        try:
            import rasterio  # noqa: F401
        except ImportError as exc:
            self.b_run.setEnabled(False)
            self.results.setPlainText(
                "The geospatial stack is not available in this Python environment (%s).\n\n"
                "Use the `ra-env` environment for analysis." % exc)

    def on_project_home_change(self):
        super().on_project_home_change()
        current = self.condition.currentText()
        self.condition.clear()
        self.condition.addItems(self.condition_list)
        if current in self.condition_list:
            self.condition.setCurrentText(current)
        self._scan_condition()

    def _scan_condition(self):
        name = self.condition.currentText()
        self._discharges = []
        self.discharge.clear()
        if not name:
            self.info.setText("No condition found in %s" % config.dir_conditions())
            return
        try:
            from ...condition import Condition
            condition = Condition(name)
            self._discharges = sorted(
                q for q in (condition.discharge_of(raster_name)
                            for raster_name in condition.all_depth_rasters())
                if q is not None)
        except Exception as exc:
            self.info.setText(str(exc))
            return
        self.discharge.addItems(["%.0f" % q for q in self._discharges])
        if self._discharges:
            self.discharge.setCurrentIndex(0)
        self._describe_product()

    def _describe_product(self):
        key = self.product.currentData()
        needs_discharge = key in ("detrended", "water", "mu")
        self.discharge.setEnabled(needs_discharge)
        self.method.setEnabled(key in ("detrended", "water"))
        self.b_series.setEnabled(key == "flows")
        self.info.setText(self._notes.get(key, ""))

    def select_series(self):
        path = self.choose_file("Select a daily flow record",
                                "Flow records (*.csv *.xlsx *.xls);;All files (*)")
        if path:
            self.flow_series = path
            self.b_series.setText(self.elide(path))

    def select_output(self):
        path = self.choose_directory("Select an output directory")
        if path:
            self.output_dir = path
            self.b_output.setText(self.elide(path))

    # -------------------------------------------------------------------- analysis

    def run_analysis(self):
        name = self.condition.currentText()
        if not name:
            self.warn("No condition", "Select a condition first.")
            return
        key = self.product.currentData()
        if key in ("detrended", "water", "mu") and not self.discharge.currentText():
            self.warn("No discharge", "This product needs a reference discharge.")
            return
        if key == "flows" and not self.flow_series:
            self.warn("No flow record",
                      "Analyzing flows needs a daily flow record: a CSV or workbook of "
                      "dates and mean daily discharge.")
            return

        discharge = float(self.discharge.currentText()) if self.discharge.currentText() \
            else None
        method = self.method.currentData()
        unit = self.unit
        output_dir = self.output_dir or None
        flow_series = self.flow_series or None

        self.b_run.setEnabled(False)
        self.b_run.setText("Building ...")
        self.progress.setRange(0, 0)
        self.progress.show()
        self.results.setPlainText("Building %s for '%s' ..."
                                  % (self.product.currentText(), name))

        def work():
            from ... import preprocessing as pre
            return pre.build_product(name, key, discharge, method, unit, output_dir,
                                     flow_series=flow_series)

        self.run_in_background(work, self._finish, self._error)

    def _reset(self):
        self.b_run.setEnabled(True)
        self.b_run.setText("Build")
        self.progress.hide()
        self.progress.setRange(0, 1)

    def _finish(self, lines):
        self._reset()
        self.results.setPlainText("Finished.\n\n" + "\n".join(lines))

    def _error(self, exc):
        self._reset()
        self.results.setPlainText("ERROR: %s" % exc)
        self.fail("Could not build the product", str(exc))
