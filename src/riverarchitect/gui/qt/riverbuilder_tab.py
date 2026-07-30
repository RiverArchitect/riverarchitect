"""River Builder tab: synthetic river valleys from design parameters."""

import os

from .base import RaTab
from .qtcompat import (QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout,
                       QLabel, QLineEdit, QLocale, QPlainTextEdit, QProgressBar,
                       QPushButton, QVBoxLayout)

__all__ = ["RiverBuilderTab"]


class RiverBuilderTab(RaTab):
    """Generate a synthetic river valley and write it as a DEM."""

    title = "River Builder"
    subtitle = ("Builds a river valley that does not exist yet - meandering centreline, "
                "varying width, thalweg, floodplain and terrace - from design parameters, "
                "and writes it as a DEM you can run a 2D model over.")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.input_file = ""
        self.output_dir = ""
        self.result = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self.body)
        layout.setContentsMargins(0, 0, 0, 0)

        inputs = QGroupBox("Input")
        form = QFormLayout(inputs)

        self.name = QLineEdit("RiverBuilder")
        form.addRow("Name:", self.name)

        self.b_input = QPushButton("Select parameter file ... (optional)")
        self.b_input.clicked.connect(self.select_input)
        self.b_input.setToolTip("An existing RiverBuilder input file. Without one the "
                                "values below are used.")
        form.addRow("Parameter file:", self.b_input)

        self.fields = {}
        for key, label, default, step in (
                ("length", "Reach length", 350.0, 10.0),
                ("bankfull_width", "Bankfull width", 20.0, 1.0),
                ("bankfull_depth", "Bankfull depth (0 = from D50)", 7.0, 0.5),
                ("valley_slope", "Valley slope", 0.005, 0.001),
                ("d50", "Median grain size (D50)", 0.0965, 0.005),
                ("floodplain_width", "Floodplain width", 30.0, 5.0),
                ("terrace_width", "Terrace width", 20.0, 5.0),
                ("meander_amplitude", "Meander amplitude", 15.0, 1.0)):
            box = QDoubleSpinBox()
            box.setLocale(QLocale.c())
            box.setDecimals(4)
            box.setRange(0.0, 1e6)
            box.setSingleStep(step)
            box.setValue(default)
            self.fields[key] = box
            form.addRow(label + ":", box)

        self.shape = QComboBox()
        for label, key in (("Symmetric U", "SU"), ("Asymmetric U", "AU"),
                           ("Trapezoid", "TZ")):
            self.shape.addItem(label, key)
        form.addRow("Cross-section:", self.shape)

        cell_row = QHBoxLayout()
        self.cell_size = QDoubleSpinBox()
        self.cell_size.setLocale(QLocale.c())
        self.cell_size.setDecimals(2)
        self.cell_size.setRange(0.05, 100.0)
        self.cell_size.setValue(1.0)
        cell_row.addWidget(self.cell_size)
        self.cell_unit = QLabel(self.labels["length"])
        cell_row.addWidget(self.cell_unit)
        cell_row.addStretch(1)
        form.addRow("DEM cell size:", cell_row)

        self.b_output = QPushButton("Select directory ... (optional)")
        self.b_output.clicked.connect(self.select_output)
        form.addRow("Output directory:", self.b_output)

        layout.addWidget(inputs)

        run_row = QHBoxLayout()
        self.b_run = QPushButton("Build the valley")
        self.b_run.setDefault(True)
        self.b_run.clicked.connect(self.run_builder)
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

    def _check_stack(self):
        try:
            import rasterio  # noqa: F401
            import scipy      # noqa: F401
        except ImportError as exc:
            self.b_run.setEnabled(False)
            self.results.setPlainText(
                "The geospatial stack is not available in this Python environment, so\n"
                "River Builder is disabled (%s).\n\n"
                "This tab needs numpy, scipy and rasterio." % exc)

    # ----------------------------------------------------------------- callbacks

    def on_unit_change(self):
        self.cell_unit.setText(self.labels["length"])

    def select_input(self):
        path = self.choose_file("Select a RiverBuilder parameter file",
                                "Parameter files (*.txt);;All files (*)")
        if path:
            self.input_file = path
            self.b_input.setText(self.elide(path))

    def select_output(self):
        path = self.choose_directory("Select an output directory")
        if path:
            self.output_dir = path
            self.b_output.setText(self.elide(path))

    # ------------------------------------------------------------------ analysis

    def _parameters(self):
        from ...riverbuilder import RiverBuilderInput, UserFunction

        if self.input_file:
            entry = RiverBuilderInput.read(self.input_file)
            entry.name = self.name.text() or entry.name
            return entry

        values = {key: box.value() for key, box in self.fields.items()}
        amplitude = values.pop("meander_amplitude")
        entry = RiverBuilderInput(name=self.name.text() or "RiverBuilder", **values)
        entry.xs_shape = self.shape.currentData()
        entry.bankfull_width_min = max(entry.bankfull_width / 2.0, 1.0)
        if amplitude > 0:
            entry.meander = [UserFunction("SIN", [amplitude, 2, 0])]
        return entry

    def run_builder(self):
        try:
            parameters = self._parameters()
        except Exception as exc:
            self.fail("Invalid parameters", str(exc))
            return

        cell_size = self.cell_size.value()
        unit = self.unit
        output_dir = self.output_dir or None

        self.b_run.setEnabled(False)
        self.b_run.setText("Building ...")
        self.progress.setRange(0, 0)
        self.progress.show()
        self.results.setPlainText("Building ...")

        def work():
            from ...riverbuilder import RiverBuilder
            return RiverBuilder(parameters, unit=unit).run(output_dir=output_dir,
                                                           cell_size=cell_size)

        self.run_in_background(work, self._finish, self._error)

    def _reset(self):
        self.b_run.setEnabled(True)
        self.b_run.setText("Build the valley")
        self.progress.hide()
        self.progress.setRange(0, 1)

    def _finish(self, result):
        self.result = result
        self._reset()
        length = self.labels["length"]
        low, high = result["elevation_range"]
        lines = [
            "Name              : %s" % result["name"],
            "Cross-section     : %s" % result["cross_section"],
            "Stations          : %d over %.1f %s" % (result["stations"],
                                                     result["length"], length),
            "Sinuosity         : %.3f" % result["sinuosity"],
            "Channel slope     : %.5f" % result["channel_slope"],
            "Bankfull depth    : %.2f %s" % (result["bankfull_depth"], length),
            "Mean width        : %.2f %s" % (result["bankfull_width_mean"], length),
            "Elevation range   : %.2f to %.2f %s" % (low, high, length),
            "Mapped area       : %.0f %s" % (result["area"], result["area_unit"]),
            "",
            "Written to: %s" % result["output_dir"],
            "Feed the DEM to a 2D model, then build a condition from its results.",
        ]
        self.results.setPlainText("\n".join(lines))

    def _error(self, exc):
        self._reset()
        self.results.setPlainText("ERROR: %s" % exc)
        self.fail("River Builder failed", str(exc))
