"""Lifespan and design mapping tab."""

import os

from ... import config
from .base import RaTab
from .qtcompat import (QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout,
                       QLabel, QLocale, QPlainTextEdit, QProgressBar, QPushButton,
                       Qt, QVBoxLayout, QtWidgets)

__all__ = ["LifespanTab"]


class LifespanTab(RaTab):
    """Map how long each restoration feature survives, and how big it has to be."""

    title = "Lifespan Design"
    subtitle = ("Predicts how many years a restoration feature survives at each cell, from "
                "the flood return periods of the modelled discharges, and the dimensions it "
                "needs to reach a target lifespan.")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.output_dir = ""
        self.results_data = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self.body)
        layout.setContentsMargins(0, 0, 0, 0)

        top = QHBoxLayout()

        inputs = QGroupBox("Input")
        form = QFormLayout(inputs)

        self.condition = QComboBox()
        self.condition.addItems(self.condition_list)
        self.condition.currentTextChanged.connect(self._describe_condition)
        form.addRow("Condition:", self.condition)

        self.manning = QDoubleSpinBox()
        self.manning.setLocale(QLocale.c())
        self.manning.setDecimals(5)
        self.manning.setRange(0.001, 1.0)
        self.manning.setSingleStep(0.005)
        self.manning.setValue(0.04739)
        self.manning.setToolTip("Manning's n in s/m^(1/3). Converted internally for U.S. "
                                "customary units.")
        form.addRow("Manning's n:", self.manning)

        self.b_output = QPushButton("Select directory ... (optional)")
        self.b_output.clicked.connect(self.select_output)
        form.addRow("Output directory:", self.b_output)

        self.info = QLabel("")
        self.info.setWordWrap(True)
        self.info.setStyleSheet("color: palette(mid);")
        form.addRow("", self.info)

        top.addWidget(inputs, 1)

        features = QGroupBox("Features")
        features_layout = QVBoxLayout(features)
        self.feature_list = QtWidgets.QListWidget()
        self.feature_list.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self._populate_features()
        features_layout.addWidget(self.feature_list)

        buttons = QHBoxLayout()
        for label, slot in (("All", lambda: self._check_all(True)),
                            ("None", lambda: self._check_all(False))):
            button = QPushButton(label)
            button.clicked.connect(slot)
            buttons.addWidget(button)
        buttons.addStretch(1)
        features_layout.addLayout(buttons)

        top.addWidget(features, 1)
        layout.addLayout(top)

        run_row = QHBoxLayout()
        self.b_run = QPushButton("Create lifespan and design maps")
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
        self._describe_condition()

    # ------------------------------------------------------------------- features

    def _populate_features(self):
        self.feature_list.clear()
        try:
            from ...lifespan import feature_groups
        except ImportError:
            return
        for group, features in feature_groups().items():
            header = QtWidgets.QListWidgetItem(group.upper())
            header.setFlags(Qt.ItemFlag.NoItemFlags)
            font = header.font()
            font.setBold(True)
            header.setFont(font)
            self.feature_list.addItem(header)
            for feature in features:
                if not feature.lifespan_mapping:
                    continue
                item = QtWidgets.QListWidgetItem("   %s" % feature.name)
                item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                item.setCheckState(Qt.CheckState.Checked if feature.fid == "rocks"
                                   else Qt.CheckState.Unchecked)
                item.setData(Qt.ItemDataRole.UserRole, feature.fid)
                self.feature_list.addItem(item)

    def _check_all(self, checked):
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for index in range(self.feature_list.count()):
            item = self.feature_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole):
                item.setCheckState(state)

    def selected_features(self):
        """Feature ids the user has ticked."""
        chosen = []
        for index in range(self.feature_list.count()):
            item = self.feature_list.item(index)
            fid = item.data(Qt.ItemDataRole.UserRole)
            if fid and item.checkState() == Qt.CheckState.Checked:
                chosen.append(fid)
        return chosen

    # ------------------------------------------------------------------ callbacks

    def _check_dependencies(self):
        try:
            import rasterio  # noqa: F401
        except ImportError as exc:
            self.b_run.setEnabled(False)
            self.results.setPlainText(
                "The geospatial stack is not available in this Python environment, so "
                "lifespan mapping is disabled (%s).\n\n"
                "Use the `ra-env` environment for analysis." % exc)

    def on_project_home_change(self):
        super().on_project_home_change()
        current = self.condition.currentText()
        self.condition.clear()
        self.condition.addItems(self.condition_list)
        if current in self.condition_list:
            self.condition.setCurrentText(current)
        self._describe_condition()

    def _describe_condition(self):
        name = self.condition.currentText()
        if not name:
            self.info.setText("No condition found in %s" % config.dir_conditions())
            return
        try:
            from ...condition import Condition
            condition = Condition(name)
        except Exception as exc:
            self.info.setText(str(exc))
            return
        pairs = len(list(condition.hydraulic_pairs()))
        self.info.setText("%d discharge(s) with a return period, longest %.0f years."
                          % (pairs, condition.max_lifespan))

    def select_output(self):
        path = self.choose_directory("Select an output directory")
        if path:
            self.output_dir = path
            self.b_output.setText(self.elide(path))

    # -------------------------------------------------------------------- analysis

    def run_analysis(self):
        features = self.selected_features()
        if not features:
            self.warn("No feature selected", "Tick at least one feature to map.")
            return
        name = self.condition.currentText()
        if not name:
            self.warn("No condition", "Select a condition first.")
            return

        unit = self.unit
        manning = self.manning.value()
        output_dir = self.output_dir or os.path.join(
            config.dir_output("LifespanDesign"), name)

        self.b_run.setEnabled(False)
        self.b_run.setText("Mapping ...")
        self.progress.setRange(0, 0)
        self.progress.show()
        self.results.setPlainText("Mapping %d feature(s) for '%s' ...\nOutput: %s"
                                  % (len(features), name, output_dir))

        def work():
            from ...lifespan import LifespanDesign
            analysis = LifespanDesign(name, unit=unit, manning_n=manning)
            return analysis.run(features, output_dir=output_dir), output_dir

        self.run_in_background(work, self._finish, self._error)

    def _reset(self):
        self.b_run.setEnabled(True)
        self.b_run.setText("Create lifespan and design maps")
        self.progress.hide()
        self.progress.setRange(0, 1)

    def _finish(self, payload):
        results, output_dir = payload
        self.results_data = results
        self._reset()
        if not results:
            self.results.setPlainText("No feature could be mapped. The condition may be "
                                      "missing the rasters these features need.")
            return
        unit = results[0].get("area_unit", "sqft")
        lines = ["%-10s %-28s %14s  %s" % ("feature", "name", "area (%s)" % unit, "lifespan")]
        lines.append("-" * 78)
        for entry in results:
            span = "%s to %s years" % (entry.get("min_lifespan", "-"),
                                       entry.get("max_lifespan", "-")) \
                if "min_lifespan" in entry else "nothing mapped"
            lines.append("%-10s %-28s %14.0f  %s"
                         % (entry["feature"], entry["name"][:28], entry["area"], span))
        lines += ["", "Rasters written to:", output_dir]
        self.results.setPlainText("\n".join(lines))

    def _error(self, exc):
        self._reset()
        self.results.setPlainText("ERROR: %s" % exc)
        self.fail("Lifespan mapping failed", str(exc))
