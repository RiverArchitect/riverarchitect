"""Habitat Area (SHArC) tab: habitat suitability and Seasonal Habitat Area."""

import os

from ... import config
from .base import RaTab
from .qtcompat import (QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout,
                       QLabel, QLocale, QPlainTextEdit, QProgressBar, QPushButton,
                       Qt, QVBoxLayout, QtWidgets)

__all__ = ["SharcTab"]


class SharcTab(RaTab):
    """Apply habitat suitability curves to the hydraulics and integrate over flow duration."""

    title = "Habitat Area (SHArC)"
    subtitle = ("Applies the habitat suitability curves of a species and lifestage to the "
                "depth and velocity rasters, and integrates the usable area over the flow "
                "duration curve to give the Seasonal Habitat Area.")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.output_dir = ""
        self._fish = None
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

        self.species = QComboBox()
        self.species.currentTextChanged.connect(self._populate_lifestages)
        form.addRow("Species:", self.species)

        self.lifestage = QComboBox()
        form.addRow("Lifestage:", self.lifestage)

        self.method = QComboBox()
        self.method.addItem("Geometric mean", "geometric_mean")
        self.method.addItem("Product", "product")
        self.method.setToolTip("How the depth and velocity suitability indices are "
                               "combined into a composite index.")
        form.addRow("Combine method:", self.method)

        self.threshold = QDoubleSpinBox()
        self.threshold.setLocale(QLocale.c())
        self.threshold.setDecimals(2)
        self.threshold.setRange(0.0, 1.0)
        self.threshold.setSingleStep(0.05)
        self.threshold.setValue(0.4)
        self.threshold.setToolTip("Composite suitability above which a cell counts as "
                                  "usable habitat.")
        form.addRow("Usable habitat threshold:", self.threshold)

        self.weighted = QtWidgets.QCheckBox("weight usable area by the mean suitability")
        form.addRow("", self.weighted)

        self.b_output = QPushButton("Select directory ... (optional)")
        self.b_output.clicked.connect(self.select_output)
        form.addRow("Output directory:", self.b_output)

        self.info = QLabel("")
        self.info.setWordWrap(True)
        self.info.setStyleSheet("color: palette(mid);")
        form.addRow("", self.info)

        layout.addWidget(inputs)

        run_row = QHBoxLayout()
        self.b_run = QPushButton("Calculate habitat suitability")
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

        self._load_fish()
        self._scan_condition()

    # ------------------------------------------------------------------- database

    def _load_fish(self):
        try:
            from ...sharc import FishDatabase
            self._fish = FishDatabase()
        except Exception as exc:
            self.b_run.setEnabled(False)
            self.results.setPlainText(
                "The habitat suitability database could not be loaded (%s).\n\n"
                "SHArC needs Fish.xlsx and the geospatial stack; use the `ra-env` "
                "environment for analysis." % exc)
            return
        self.species.addItems(self._fish.species)

    def _populate_lifestages(self):
        if self._fish is None:
            return
        current = self.lifestage.currentText()
        self.lifestage.clear()
        stages = self._fish.lifestages(self.species.currentText())
        self.lifestage.addItems(stages)
        if current in stages:
            self.lifestage.setCurrentText(current)

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
        if not name:
            self.info.setText("No condition found in %s" % config.dir_conditions())
            return
        try:
            from ...sharc import SHArC
            analysis = SHArC(name, unit=self.unit)
            count = len(analysis.discharges)
        except Exception as exc:
            self.info.setText(str(exc))
            return
        self.info.setText("%d discharge(s) have both a depth and a velocity raster." % count)

    def select_output(self):
        path = self.choose_directory("Select an output directory")
        if path:
            self.output_dir = path
            self.b_output.setText(self.elide(path))

    # -------------------------------------------------------------------- analysis

    def run_analysis(self):
        name = self.condition.currentText()
        species = self.species.currentText()
        lifestage = self.lifestage.currentText()
        if not (name and species and lifestage):
            self.warn("Missing input", "Select a condition, a species and a lifestage.")
            return

        unit = self.unit
        method = self.method.currentData()
        threshold = self.threshold.value()
        weighted = self.weighted.isChecked()
        output_dir = self.output_dir or None

        self.b_run.setEnabled(False)
        self.b_run.setText("Calculating ...")
        self.progress.setRange(0, 0)
        self.progress.show()
        self.results.setPlainText("Calculating habitat suitability for %s - %s ...\n"
                                  "This evaluates every discharge and may take a while."
                                  % (species, lifestage))

        def work():
            from ...sharc import SHArC
            analysis = SHArC(name, unit=unit, combine_method=method, threshold=threshold)
            return analysis.run(species, lifestage, output_dir=output_dir,
                                weighted=weighted)

        self.run_in_background(work, self._finish, self._error)

    def _reset(self):
        self.b_run.setEnabled(True)
        self.b_run.setText("Calculate habitat suitability")
        self.progress.hide()
        self.progress.setRange(0, 1)

    def _finish(self, result):
        self._reset()
        area = result["area_unit"]
        lines = ["%s - %s   (code %s, %s, threshold %.2f)"
                 % (result["species"], result["lifestage"], result["shortname"],
                    result["combine_method"], result["threshold"]),
                 "",
                 "%10s %16s %12s" % ("Q (%s)" % result["discharge_unit"],
                                     "usable (%s)" % area, "mean cHSI"),
                 "-" * 42]
        for row in result["per_discharge"]:
            lines.append("%10.0f %16.0f %12.3f"
                         % (row["discharge"], row["usable_area"], row["mean_chsi"]))
        if "sharea" in result:
            lines += ["", "Seasonal Habitat Area: %.0f %s" % (result["sharea"], area),
                      "(usable area integrated over the flow duration curve)"]
        else:
            lines += ["", "No flow duration workbook found for this species code, so the",
                      "Seasonal Habitat Area was not computed. Expected:",
                      os.path.join(config.dir_flows(), result["condition"],
                                   "flow_duration_%s.xlsx" % result["shortname"])]
        if result.get("output_dir"):
            lines += ["", "Written to:", result["output_dir"]]
        self.results.setPlainText("\n".join(lines))

    def _error(self, exc):
        self._reset()
        self.results.setPlainText("ERROR: %s" % exc)
        self.fail("Habitat suitability failed", str(exc))
