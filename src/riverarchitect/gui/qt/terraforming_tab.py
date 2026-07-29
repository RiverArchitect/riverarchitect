"""Terraforming tab: threshold-based grading and widening for planting."""

import os

from .base import RaTab
from .qtcompat import (QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout,
                       QLabel, QLocale, QPlainTextEdit, QProgressBar, QPushButton,
                       QVBoxLayout)

__all__ = ["TerraformingTab"]


class TerraformingTab(RaTab):
    """Lower a DEM where planned plantings cannot reach the water table."""

    title = "Terraforming"
    subtitle = ("Lowers the terrain where a planned feature sits too far above the water "
                "table for its roots, by exactly the excess. Feed the result to Volume "
                "Assessment for the earthwork quantity.")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.action_dir = ""
        self.output_dir = ""
        self.result = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self.body)
        layout.setContentsMargins(0, 0, 0, 0)

        inputs = QGroupBox("Input")
        form = QFormLayout(inputs)

        self.condition = QComboBox()
        self.condition.addItems(self.condition_list)
        form.addRow("Condition:", self.condition)

        self.b_actions = QPushButton("Select directory ...")
        self.b_actions.clicked.connect(self.select_actions)
        self.b_actions.setToolTip("The Max Lifespan output folder, holding one "
                                  "best_<feature>.tif per feature.")
        form.addRow("Feature action rasters:", self.b_actions)

        d2w_row = QHBoxLayout()
        self.d2w_max = QDoubleSpinBox()
        # A dot decimal separator regardless of the desktop locale, as in the volume tab.
        self.d2w_max.setLocale(QLocale.c())
        self.d2w_max.setDecimals(2)
        self.d2w_max.setRange(0.0, 1000.0)
        self.d2w_max.setSingleStep(0.5)
        self.d2w_max.setValue(self._default_limit())
        self.d2w_max.setToolTip("Deepest water table the plantings can still reach. "
                                "Defaults to the smallest d2w_max among the vegetation "
                                "planting features.")
        d2w_row.addWidget(self.d2w_max)
        self.d2w_unit = QLabel(self.labels["length"])
        d2w_row.addWidget(self.d2w_unit)
        d2w_row.addStretch(1)
        form.addRow("Max. depth to water table:", d2w_row)

        self.b_output = QPushButton("Select directory ... (optional)")
        self.b_output.clicked.connect(self.select_output)
        form.addRow("Output directory:", self.b_output)

        layout.addWidget(inputs)

        run_row = QHBoxLayout()
        self.b_run = QPushButton("Modify terrain")
        self.b_run.setDefault(True)
        self.b_run.clicked.connect(self.run_terraforming)
        run_row.addWidget(self.b_run)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
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

        self._check_rasterio()

    @staticmethod
    def _default_limit():
        try:
            from ...terraforming import planting_depth_limit
            return planting_depth_limit()
        except Exception:
            return 7.0

    def _check_rasterio(self):
        """Disable the tab when the geospatial stack is missing, rather than failing later."""
        try:
            import rasterio  # noqa: F401
        except ImportError as exc:
            self.b_run.setEnabled(False)
            self.results.setPlainText(
                "The geospatial stack is not available in this Python environment, so\n"
                "terraforming is disabled (%s).\n\n"
                "This tab needs numpy, scipy and rasterio. If you started River Architect\n"
                "with the interpreter that owns the QGIS bindings, that interpreter\n"
                "typically has no rasterio: use the `ra-env` environment for analysis, and\n"
                "the QGIS interpreter for mapping." % exc)

    # ----------------------------------------------------------------- callbacks

    def on_unit_change(self):
        self.d2w_unit.setText(self.labels["length"])

    def on_project_home_change(self):
        super().on_project_home_change()
        self.condition.clear()
        self.condition.addItems(self.condition_list)

    def select_actions(self):
        from ... import config

        start = os.path.join(config.dir_output("MaxLifespan"), self.condition.currentText())
        path = self.choose_directory("Select the feature action raster directory",
                                     start if os.path.isdir(start) else None)
        if path:
            self.action_dir = path
            self.b_actions.setText(self.elide(path))

    def select_output(self):
        path = self.choose_directory("Select an output directory")
        if path:
            self.output_dir = path
            self.b_output.setText(self.elide(path))

    # ------------------------------------------------------------------ analysis

    def run_terraforming(self):
        condition = self.condition.currentText()
        if not condition:
            self.warn("Missing input", "Select a condition.")
            return
        if not self.action_dir:
            self.warn("Missing input",
                      "Select the directory holding the feature action rasters.\n\n"
                      "That is normally the Max Lifespan output folder; run Max Lifespan "
                      "first if it does not exist yet.")
            return

        action_dir = self.action_dir
        d2w_max = self.d2w_max.value()
        unit = self.unit
        output_dir = self.output_dir or None

        self.b_run.setEnabled(False)
        self.b_run.setText("Modifying ...")
        self.progress.setRange(0, 0)
        self.progress.show()
        self.results.setPlainText("Running ...")

        def work():
            from ...terraforming import Terraforming
            analysis = Terraforming(condition, action_dir, unit=unit, d2w_max=d2w_max)
            return analysis.run(output_dir=output_dir)

        self.run_in_background(work, self._finish, self._error)

    def _reset_run_button(self):
        self.b_run.setEnabled(True)
        self.b_run.setText("Modify terrain")
        self.progress.hide()
        self.progress.setRange(0, 1)

    def _finish(self, result):
        self.result = result
        self._reset_run_button()
        length = self.labels["length"]
        lines = [
            "Max. depth to water table : %12.2f %s" % (result["d2w_max"], length),
            "Cells lowered             : %12d" % result["modified_cells"],
            "Area lowered              : %12.0f %s" % (result["modified_area"],
                                                       result["area_unit"]),
            "Excavated volume          : %12.0f cubic %s" % (result["cut_volume"], length),
            "Deepest cut               : %12.2f %s" % (result["max_cut"], length),
            "",
            "%-14s %10s %14s %12s" % ("feature", "cells", "area", "volume"),
        ]
        for row in result["per_feature"]:
            lines.append("%-14s %10d %14.0f %12.0f"
                         % (row["feature"], row["cells"], row["area"], row["volume"]))
        if "output_dir" in result:
            lines += ["", "Written to: %s" % result["output_dir"],
                      "Feed dem_terraformed.tif to Volume Assessment as the modified DEM."]
        self.results.setPlainText("\n".join(lines))

    def _error(self, exc):
        self._reset_run_button()
        self.results.setPlainText("ERROR: %s" % exc)
        self.fail("Terraforming failed", str(exc))
