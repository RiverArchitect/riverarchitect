"""Ecohydraulics tab: fish stranding risk over a receding hydrograph."""

import os

from ... import config
from ...condition import discharge_label
from .base import RaTab
from .qtcompat import (QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout,
                       QLabel, QLocale, QPlainTextEdit, QProgressBar, QPushButton,
                       QVBoxLayout)

__all__ = ["StrandingTab"]


class StrandingTab(RaTab):
    """Find wetted areas that disconnect from the main channel as discharge falls."""

    title = "Stranding Risk"
    subtitle = ("As a hydrograph recedes the wetted area breaks apart. Pools that lose their "
                "connection to the main channel trap fish. This finds them, per discharge, "
                "and reports the flow at which each spot becomes a trap.")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.output_dir = ""
        self._discharges = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self.body)
        layout.setContentsMargins(0, 0, 0, 0)

        inputs = QGroupBox("Input")
        form = QFormLayout(inputs)

        self.condition = QComboBox()
        self.condition.addItems(self.condition_list)
        self.condition.currentTextChanged.connect(self._scan_discharges)
        form.addRow("Condition:", self.condition)

        self.fish = QComboBox()
        try:
            from ...stranding import TRAVEL_THRESHOLDS
            for (species, lifestage), values in TRAVEL_THRESHOLDS.items():
                self.fish.addItem("%s, %s" % (species, lifestage),
                                  (species, lifestage, values["h_min"]))
        except ImportError:
            pass
        self.fish.addItem("Custom", None)
        self.fish.currentIndexChanged.connect(self._apply_fish)
        form.addRow("Species and lifestage:", self.fish)

        depth_row = QHBoxLayout()
        self.h_min = QDoubleSpinBox()
        self.h_min.setLocale(QLocale.c())
        self.h_min.setDecimals(2)
        self.h_min.setRange(0.0, 100.0)
        self.h_min.setSingleStep(0.05)
        self.h_min.setValue(0.2)
        self.h_min.setToolTip("Cells shallower than this do not count as wetted. The single "
                              "most influential parameter here - report it with the result.")
        depth_row.addWidget(self.h_min)
        self.h_unit = QLabel(self.labels["length"])
        depth_row.addWidget(self.h_unit)
        depth_row.addStretch(1)
        form.addRow("Minimum swimming depth:", depth_row)

        range_row = QHBoxLayout()
        self.q_low = QComboBox()
        self.q_high = QComboBox()
        range_row.addWidget(QLabel("from"))
        range_row.addWidget(self.q_high)
        range_row.addWidget(QLabel("down to"))
        range_row.addWidget(self.q_low)
        self.q_unit = QLabel(self.labels["q"])
        range_row.addWidget(self.q_unit)
        range_row.addStretch(1)
        form.addRow("Discharge range:", range_row)

        self.b_output = QPushButton("Select directory ... (optional)")
        self.b_output.clicked.connect(self.select_output)
        form.addRow("Output directory:", self.b_output)

        self.info = QLabel("")
        self.info.setWordWrap(True)
        self.info.setStyleSheet("color: palette(mid);")
        form.addRow("", self.info)

        layout.addWidget(inputs)

        run_row = QHBoxLayout()
        self.b_run = QPushButton("Assess stranding risk")
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
        self._scan_discharges()

    # ------------------------------------------------------------------ callbacks

    def _check_dependencies(self):
        try:
            import rasterio  # noqa: F401
        except ImportError as exc:
            self.b_run.setEnabled(False)
            self.results.setPlainText(
                "The geospatial stack is not available in this Python environment, so the "
                "stranding analysis is disabled (%s).\n\n"
                "Use the `ra-env` environment for analysis." % exc)

    def on_unit_change(self):
        self.h_unit.setText(self.labels["length"])
        self.q_unit.setText(self.labels["q"])

    def on_project_home_change(self):
        super().on_project_home_change()
        current = self.condition.currentText()
        self.condition.clear()
        self.condition.addItems(self.condition_list)
        if current in self.condition_list:
            self.condition.setCurrentText(current)
        self._scan_discharges()

    def _apply_fish(self):
        data = self.fish.currentData()
        if data:
            self.h_min.setValue(data[2])

    def _scan_discharges(self):
        name = self.condition.currentText()
        self._discharges = []
        self.q_low.clear()
        self.q_high.clear()
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

        if not self._discharges:
            self.info.setText("This condition has no depth rasters.")
            self.b_run.setEnabled(False)
            return

        labels = [discharge_label(q) for q in self._discharges]
        self.q_low.addItems(labels)
        self.q_high.addItems(labels)
        self.q_low.setCurrentIndex(0)
        self.q_high.setCurrentIndex(min(len(labels) - 1, 12))
        self.info.setText("%d depth raster(s) available, %g to %g %s."
                          % (len(self._discharges), self._discharges[0],
                             self._discharges[-1], self.labels["q"]))

    def select_output(self):
        path = self.choose_directory("Select an output directory")
        if path:
            self.output_dir = path
            self.b_output.setText(self.elide(path))

    # -------------------------------------------------------------------- analysis

    def run_analysis(self):
        name = self.condition.currentText()
        if not name or not self._discharges:
            self.warn("No condition", "Select a condition with depth rasters.")
            return

        low = float(self.q_low.currentText())
        high = float(self.q_high.currentText())
        if high <= low:
            self.warn("Discharge range",
                      "The starting discharge must be higher than the final one: a "
                      "stranding analysis walks a *falling* hydrograph.")
            return

        chosen = sorted((q for q in self._discharges if low <= q <= high), reverse=True)
        h_min = self.h_min.value()
        unit = self.unit
        output_dir = self.output_dir or None

        self.b_run.setEnabled(False)
        self.b_run.setText("Assessing ...")
        self.progress.setRange(0, 0)
        self.progress.show()
        self.results.setPlainText("Walking %d discharge(s) from %g down to %g %s ..."
                                  % (len(chosen), high, low, self.labels["q"]))

        def work():
            from ...stranding import StrandingRisk
            analysis = StrandingRisk(name, discharges=chosen, h_min=h_min, unit=unit)
            return analysis.run(output_dir=output_dir)

        self.run_in_background(work, self._finish, self._error)

    def _reset(self):
        self.b_run.setEnabled(True)
        self.b_run.setText("Assess stranding risk")
        self.progress.hide()
        self.progress.setRange(0, 1)

    def _finish(self, result):
        self._reset()
        area = result["area_unit"]
        discharge = result["discharge_unit"]
        lines = ["Minimum swimming depth: %.2f %s" % (result["h_min"],
                                                      self.labels["length"]), "",
                 "%10s %7s %14s %14s %8s" % ("Q (%s)" % discharge, "pools",
                                             "wetted (%s)" % area, "stranded (%s)" % area,
                                             "%"),
                 "-" * 60]
        for row in result["per_discharge"]:
            lines.append("%10s %7d %14.0f %14.0f %7.2f"
                         % (discharge_label(row["discharge"]), row["pools"],
                            row["wetted_area"], row["stranded_area"],
                            row["percent_stranded"]))
        lines += ["",
                  "Worst discharge : %g %s, %.0f %s stranded"
                  % (result["worst_discharge"], discharge,
                     result["worst_stranded_area"], area),
                  "Ever disconnected: %.0f %s"
                  % (result["total_disconnected_area"], area)]
        if result.get("velocity_limited", False):
            lines += ["",
                      "Escape routes account for the %.1f %s swimming speed: fast water is"
                      % (result["u_max"], self.labels["u"]),
                      "passable downstream and not upstream."]
        else:
            lines += ["",
                      "Note: depth only. Applying the swimming-speed criterion needs the flow",
                      "direction - ux<Q>.tif and uy<Q>.tif beside the condition, or a",
                      "velocity_field - so an area counts as connected even where the escape",
                      "route runs against a current a fish could not beat."]
        if result.get("output_dir"):
            lines += ["", "Written to:", result["output_dir"]]
        self.results.setPlainText("\n".join(lines))

    def _error(self, exc):
        self._reset()
        self.results.setPlainText("ERROR: %s" % exc)
        self.fail("Stranding assessment failed", str(exc))
