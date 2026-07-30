"""Project Maker tab: construction cost against the gain in habitat area."""

import os

from .base import RaTab
from .qtcompat import (QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout,
                       QLabel, QLineEdit, QLocale, QPlainTextEdit, QProgressBar,
                       QPushButton, QVBoxLayout)

__all__ = ["ProjectMakerTab"]


class ProjectMakerTab(RaTab):
    """Cost the works, compare the habitat, and report the trade-off."""

    title = "Project Maker"
    subtitle = ("Prices the works from what the earlier modules mapped, compares the "
                "seasonal habitat area before and after, and reports the cost per unit of "
                "habitat gained.")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.lifespan_dir = ""
        self.output_dir = ""
        self.result = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self.body)
        layout.setContentsMargins(0, 0, 0, 0)

        inputs = QGroupBox("Input")
        form = QFormLayout(inputs)

        self.name = QLineEdit("project")
        form.addRow("Project name:", self.name)

        self.b_lifespan = QPushButton("Select directory ...")
        self.b_lifespan.clicked.connect(self.select_lifespan)
        self.b_lifespan.setToolTip("The Max Lifespan output folder. Its per-feature areas "
                                   "become the quantities in the bill.")
        form.addRow("Max Lifespan output:", self.b_lifespan)

        self.condition_before = QComboBox()
        self.condition_before.addItems(self.condition_list)
        form.addRow("Existing condition:", self.condition_before)

        self.condition_after = QComboBox()
        self.condition_after.addItems(self.condition_list)
        form.addRow("With-project condition:", self.condition_after)

        self.species = QComboBox()
        self.lifestage = QComboBox()
        self._load_fish()
        self.species.currentIndexChanged.connect(self._load_lifestages)
        form.addRow("Species:", self.species)
        form.addRow("Lifestage:", self.lifestage)

        self.log_length = QDoubleSpinBox()
        self.log_length.setLocale(QLocale.c())
        self.log_length.setDecimals(2)
        self.log_length.setRange(1.0, 1000.0)
        self.log_length.setValue(25.0)
        self.log_length.setToolTip("Used to turn a mapped area into a count of logs or "
                                   "pieces, as the original's workbook did.")
        form.addRow("Log length:", self.log_length)

        self.b_output = QPushButton("Select directory ... (optional)")
        self.b_output.clicked.connect(self.select_output)
        form.addRow("Output directory:", self.b_output)

        layout.addWidget(inputs)

        run_row = QHBoxLayout()
        self.b_run = QPushButton("Assess the project")
        self.b_run.setDefault(True)
        self.b_run.clicked.connect(self.run_assessment)
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

        self._check_stack()

    def _load_fish(self):
        try:
            from ...sharc import FishDatabase
            self._fish = FishDatabase()
            self.species.addItems(self._fish.species)
        except Exception:
            self._fish = None
        self._load_lifestages()

    def _load_lifestages(self):
        self.lifestage.clear()
        if self._fish and self.species.currentText():
            self.lifestage.addItems(self._fish.lifestages(self.species.currentText()))

    def _check_stack(self):
        try:
            import rasterio  # noqa: F401
        except ImportError as exc:
            self.b_run.setEnabled(False)
            self.results.setPlainText(
                "The geospatial stack is not available in this Python environment, so\n"
                "Project Maker is disabled (%s)." % exc)

    # ----------------------------------------------------------------- callbacks

    def on_project_home_change(self):
        super().on_project_home_change()
        for box in (self.condition_before, self.condition_after):
            box.clear()
            box.addItems(self.condition_list)

    def select_lifespan(self):
        from ... import config

        start = config.dir_output("MaxLifespan")
        path = self.choose_directory("Select the Max Lifespan output directory",
                                     start if os.path.isdir(start) else None)
        if path:
            self.lifespan_dir = path
            self.b_lifespan.setText(self.elide(path))

    def select_output(self):
        path = self.choose_directory("Select an output directory")
        if path:
            self.output_dir = path
            self.b_output.setText(self.elide(path))

    # ------------------------------------------------------------------ analysis

    def run_assessment(self):
        before = self.condition_before.currentText()
        after = self.condition_after.currentText()
        species = self.species.currentText()
        lifestage = self.lifestage.currentText()
        if not (before and after and species and lifestage):
            self.warn("Missing input",
                      "Select both conditions, a species and a lifestage.")
            return
        if before == after:
            self.warn("Same condition",
                      "The existing and with-project conditions are the same, so there is "
                      "no gain to measure.")
            return

        name = self.name.text() or "project"
        lifespan_dir = self.lifespan_dir
        unit = self.unit
        log_length = self.log_length.value()
        output_dir = self.output_dir or None

        self.b_run.setEnabled(False)
        self.b_run.setText("Assessing ...")
        self.progress.setRange(0, 0)
        self.progress.show()
        self.results.setPlainText("Running the two habitat analyses ...")

        def work():
            from ...maxlifespan import MaxLifespan
            from ...projectmaker import ProjectMaker
            from ...sharc import SHArC

            maker = ProjectMaker(name, unit=unit, log_length=log_length)
            if lifespan_dir:
                summary = MaxLifespan(lifespan_dir, unit=unit).run(write_polygons=False)
                maker.quantities_from_lifespan(summary)
            first = SHArC(before, unit=unit).run(species, lifestage, write_rasters=False)
            second = SHArC(after, unit=unit).run(species, lifestage, write_rasters=False)
            return maker.run(before=first, after=second, output_dir=output_dir)

        self.run_in_background(work, self._finish, self._error)

    def _reset(self):
        self.b_run.setEnabled(True)
        self.b_run.setText("Assess the project")
        self.progress.hide()
        self.progress.setRange(0, 1)

    def _finish(self, result):
        self.result = result
        self._reset()
        costs = result["costs"]
        lines = ["%-38s %16s" % ("GROUP", "COST (US$)")]
        for group, amount in costs["groups"].items():
            if amount:
                lines.append("%-38s %16.2f" % (group, amount))
        lines.append("%-38s %16.2f" % ("CONSTRUCTION WORKS", costs["construction"]))
        lines.append("")
        for entry in costs["applied"]:
            lines.append("%-38s %16.2f" % ("%s (%.1f%%)" % (entry["label"],
                                                            entry["fraction"] * 100),
                                            entry["amount"]))
        lines.append("%-38s %16.2f" % ("TOTAL", costs["total"]))

        if "habitat" in result:
            habitat = result["habitat"]
            unit = result["area_unit"]
            lines += ["",
                      "%-38s %16.0f %s" % ("SHArea, existing", habitat["before"], unit),
                      "%-38s %16.0f %s" % ("SHArea, with project", habitat["after"], unit),
                      "%-38s %16.0f %s (%+.1f%%)" % ("net gain", habitat["gain"], unit,
                                                      habitat["relative"] * 100)]
            if result.get("cost_per_area"):
                lines.append("%-38s %16.2f US$" % ("cost per %s gained" % unit,
                                                    result["cost_per_area"]))
            else:
                lines.append("The project does not increase habitat area, so there is no "
                             "cost-benefit ratio.")
        if "report" in result:
            lines += ["", "Bill of quantities: %s" % result["report"]]
        self.results.setPlainText("\n".join(lines))

    def _error(self, exc):
        self._reset()
        self.results.setPlainText("ERROR: %s" % exc)
        self.fail("Project assessment failed", str(exc))
