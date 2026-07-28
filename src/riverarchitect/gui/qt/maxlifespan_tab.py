"""Max lifespan tab: which feature belongs where."""

import os

from ... import config
from .base import RaTab
from .qtcompat import (QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
                       QPlainTextEdit, QProgressBar, QPushButton, QVBoxLayout)

__all__ = ["MaxLifespanTab"]


class MaxLifespanTab(RaTab):
    """Combine per-feature lifespan maps into a best-feature assessment."""

    title = "Max Lifespan"
    subtitle = ("Compares the lifespan maps of several features and reports, per cell, which "
                "feature lasts longest. Run the lifespan tab first; this reads its output.")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.lifespan_dir = ""
        self.output_dir = ""
        self._build()

    def _build(self):
        layout = QVBoxLayout(self.body)
        layout.setContentsMargins(0, 0, 0, 0)

        inputs = QGroupBox("Input")
        form = QFormLayout(inputs)

        self.condition = QComboBox()
        self.condition.addItems(self.condition_list)
        self.condition.currentTextChanged.connect(self._use_default_dir)
        form.addRow("Condition:", self.condition)

        self.b_lifespan = QPushButton("Select directory ...")
        self.b_lifespan.clicked.connect(self.select_lifespan_dir)
        form.addRow("Lifespan rasters:", self.b_lifespan)

        self.b_output = QPushButton("Select directory ... (optional)")
        self.b_output.clicked.connect(self.select_output)
        form.addRow("Output directory:", self.b_output)

        self.found = QLabel("")
        self.found.setWordWrap(True)
        self.found.setStyleSheet("color: palette(mid);")
        form.addRow("", self.found)

        layout.addWidget(inputs)

        run_row = QHBoxLayout()
        self.b_run = QPushButton("Assess best features")
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

        self._use_default_dir()

    # ------------------------------------------------------------------ callbacks

    def on_project_home_change(self):
        super().on_project_home_change()
        current = self.condition.currentText()
        self.condition.clear()
        self.condition.addItems(self.condition_list)
        if current in self.condition_list:
            self.condition.setCurrentText(current)
        self._use_default_dir()

    def _use_default_dir(self):
        name = self.condition.currentText()
        if not name:
            return
        default = os.path.join(config.dir_output("LifespanDesign"), name)
        self.lifespan_dir = default
        self.b_lifespan.setText(self.elide(default))
        self._scan()

    def _scan(self):
        import glob
        if not self.lifespan_dir or not os.path.isdir(self.lifespan_dir):
            self.found.setText("No lifespan rasters yet - run the lifespan tab first.")
            self.b_run.setEnabled(False)
            return
        rasters = sorted(glob.glob(os.path.join(self.lifespan_dir, "lf_*.tif")))
        names = [os.path.basename(path)[3:-4] for path in rasters]
        if names:
            self.found.setText("%d feature(s) found: %s" % (len(names), ", ".join(names)))
            self.b_run.setEnabled(True)
        else:
            self.found.setText("No lf_*.tif rasters in that directory.")
            self.b_run.setEnabled(False)

    def select_lifespan_dir(self):
        path = self.choose_directory("Select the directory holding the lf_*.tif rasters",
                                     self.lifespan_dir or config.dir_output("LifespanDesign"))
        if path:
            self.lifespan_dir = path
            self.b_lifespan.setText(self.elide(path))
            self._scan()

    def select_output(self):
        path = self.choose_directory("Select an output directory")
        if path:
            self.output_dir = path
            self.b_output.setText(self.elide(path))

    # -------------------------------------------------------------------- analysis

    def run_analysis(self):
        if not self.lifespan_dir:
            self.warn("Missing input", "Select the directory holding the lifespan rasters.")
            return
        lifespan_dir = self.lifespan_dir
        unit = self.unit
        output_dir = self.output_dir or None

        self.b_run.setEnabled(False)
        self.b_run.setText("Assessing ...")
        self.progress.setRange(0, 0)
        self.progress.show()
        self.results.setPlainText("Assessing best features ...")

        def work():
            from ...maxlifespan import MaxLifespan
            return MaxLifespan(lifespan_dir, unit=unit).run(output_dir=output_dir)

        self.run_in_background(work, self._finish, self._error)

    def _reset(self):
        self.b_run.setEnabled(True)
        self.b_run.setText("Assess best features")
        self.progress.hide()
        self.progress.setRange(0, 1)

    def _finish(self, result):
        self._reset()
        unit = result["area_unit"]
        lines = ["Total mapped area: %.0f %s" % (result["total_mapped_area"], unit), "",
                 "%-12s %14s %8s  %s" % ("feature", "area (%s)" % unit, "share", "max years"),
                 "-" * 56]
        for entry in result["features"]:
            lines.append("%-12s %14.0f %7.1f%%  %s"
                         % (entry["feature"], entry["area"], entry["share"],
                            entry.get("max_lifespan", "-")))
        lines += ["",
                  "A cell counts for every feature that reaches the maximum, so the shares",
                  "can exceed 100%: where they do, the choice between those features is",
                  "yours to make on other grounds.",
                  "", "Written to:", result["output_dir"]]
        self.results.setPlainText("\n".join(lines))

    def _error(self, exc):
        self._reset()
        self.results.setPlainText("ERROR: %s" % exc)
        self.fail("Best-feature assessment failed", str(exc))
