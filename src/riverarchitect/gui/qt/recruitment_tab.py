"""Riparian seedling recruitment tab: the Recruitment Box Model."""

import os

from ... import config
from .base import RaTab
from .qtcompat import (QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
                       QPlainTextEdit, QProgressBar, QPushButton, QVBoxLayout)

__all__ = ["RecruitmentTab"]


class RecruitmentTab(RaTab):
    """Where cottonwood and willow seedlings can establish and survive their first season."""

    title = "Riparian Seedling Recruitment"
    subtitle = ("Maps where all four objectives of the Recruitment Box Model coincide: a "
                "flow prepared the seedbed, the water table receded slowly enough, the "
                "seedling was not drowned, and no later flow scoured it out.")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.flow_path = ""
        self.vegetation_path = ""
        self.output_dir = ""
        self._build()

    def _build(self):
        layout = QVBoxLayout(self.body)
        layout.setContentsMargins(0, 0, 0, 0)

        inputs = QGroupBox("Input")
        form = QFormLayout(inputs)

        self.condition = QComboBox()
        self.condition.addItems(self.condition_list)
        form.addRow("Condition:", self.condition)

        self.b_flow = QPushButton("Select daily flow record ...")
        self.b_flow.clicked.connect(self.select_flow)
        self.b_flow.setToolTip("A spreadsheet or CSV with a date column and a mean daily "
                               "discharge column. This is the one input the other modules "
                               "do not need: recruitment depends on when flows happened.")
        form.addRow("Flow record:", self.b_flow)

        self.year = QComboBox()
        self.year.setToolTip("The season to analyse. Populated from the flow record.")
        form.addRow("Season:", self.year)

        self.b_parameters = QPushButton("packaged recruitment_parameters.xlsx")
        self.b_parameters.clicked.connect(self.select_parameters)
        self.parameters_path = ""
        form.addRow("Parameters:", self.b_parameters)

        self.b_vegetation = QPushButton("Select raster ... (optional)")
        self.b_vegetation.clicked.connect(self.select_vegetation)
        self.b_vegetation.setToolTip("Ground that already carries vegetation cannot recruit "
                                     "a new seedling and is excluded.")
        form.addRow("Existing vegetation:", self.b_vegetation)

        self.b_output = QPushButton("Select directory ... (optional)")
        self.b_output.clicked.connect(self.select_output)
        form.addRow("Output directory:", self.b_output)

        self.info = QLabel("Select a daily flow record to begin.")
        self.info.setWordWrap(True)
        self.info.setStyleSheet("color: palette(mid);")
        form.addRow("", self.info)

        layout.addWidget(inputs)

        run_row = QHBoxLayout()
        self.b_run = QPushButton("Assess recruitment potential")
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

    # ------------------------------------------------------------------ callbacks

    def _check_dependencies(self):
        try:
            import rasterio  # noqa: F401
            import pandas  # noqa: F401
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

    def select_flow(self):
        path = self.choose_file("Select the daily flow record",
                                "Tables (*.xlsx *.xls *.csv);;All files (*)")
        if not path:
            return
        self.flow_path = path
        self.b_flow.setText(self.elide(path))
        self._scan_flow()

    def _scan_flow(self):
        self.year.clear()
        try:
            from ...recruitment import read_flow_series
            series = read_flow_series(self.flow_path)
        except Exception as exc:
            self.info.setText("Could not read the flow record: %s" % exc)
            return
        if not series:
            self.info.setText("The flow record contains no usable rows.")
            return
        years = sorted({date.year for date in series})
        self.year.addItems([str(value) for value in years])
        self.year.setCurrentIndex(len(years) - 1)
        self.info.setText("%d daily value(s), %s to %s."
                          % (len(series), min(series), max(series)))

    def select_parameters(self):
        path = self.choose_file("Select a recruitment_parameters.xlsx",
                                "Workbooks (*.xlsx *.xls);;All files (*)")
        if path:
            self.parameters_path = path
            self.b_parameters.setText(self.elide(path))

    def select_vegetation(self):
        path = self.choose_file("Select an existing vegetation raster")
        if path:
            self.vegetation_path = path
            self.b_vegetation.setText(self.elide(path))

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
        if not self.flow_path:
            self.warn("No flow record",
                      "Recruitment needs a daily flow record: bed preparation, recession "
                      "and scour all depend on when flows happened, not just which flows "
                      "are possible.")
            return
        if not self.year.currentText():
            self.warn("No season", "The flow record yielded no season to analyse.")
            return

        year = int(self.year.currentText())
        flow_path = self.flow_path
        parameters_path = self.parameters_path or None
        vegetation = self.vegetation_path or None
        unit = self.unit
        output_dir = self.output_dir or None

        self.b_run.setEnabled(False)
        self.b_run.setText("Assessing ...")
        self.progress.setRange(0, 0)
        self.progress.show()
        self.results.setPlainText("Assessing recruitment potential for %d ...\n"
                                  "This walks the flow record day by day." % year)

        def work():
            from ...recruitment import RecruitmentParameters, RecruitmentPotential
            parameters = RecruitmentParameters.from_workbook(parameters_path)
            analysis = RecruitmentPotential(name, flow_path, year=year,
                                            parameters=parameters, unit=unit,
                                            existing_vegetation=vegetation)
            return analysis.run(output_dir=output_dir)

        self.run_in_background(work, self._finish, self._error)

    def _reset(self):
        self.b_run.setEnabled(True)
        self.b_run.setText("Assess recruitment potential")
        self.progress.hide()
        self.progress.setRange(0, 1)

    def _finish(self, result):
        self._reset()
        area = result["area_unit"]
        lines = ["%s, season %d" % (result["species"], result["year"]), "",
                 "%-24s %14s" % ("", "area (%s)" % area),
                 "-" * 40,
                 "%-24s %14.0f" % ("recruitment area", result["crop_area"])]
        for name, value in result["objectives"].items():
            lines.append("%-24s %14.0f" % ("  " + name.replace("_", " "), value))
        lines += ["-" * 40,
                  "%-24s %14.0f" % ("full potential", result["recruitment_area"]),
                  "%-24s %14.0f" % ("partial potential", result["partial_area"]),
                  "",
                  "Each objective is scored 1, 0.5 or 0 and the four are multiplied, so a",
                  "zero anywhere is a zero overall - the seedling has to survive all four."]
        if result.get("output_dir"):
            lines += ["", "Written to:", result["output_dir"]]
        self.results.setPlainText("\n".join(lines))

    def _error(self, exc):
        self._reset()
        self.results.setPlainText("ERROR: %s" % exc)
        self.fail("Recruitment assessment failed", str(exc))
