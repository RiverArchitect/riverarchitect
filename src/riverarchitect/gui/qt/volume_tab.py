"""Volume Assessment tab: earthworks quantities between two DEMs."""

import os

from .base import RaTab
from .qtcompat import (QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
                       QLocale, QPlainTextEdit, QProgressBar, QPushButton, QVBoxLayout)

__all__ = ["VolumeTab"]


class VolumeTab(RaTab):
    """Compare an original and a modified DEM and report fill and excavation volumes."""

    title = "Volume Assessment"
    subtitle = ("Earthworks quantities between a pre-project and a post-project DEM. "
                "Volumes are integrated under the triangulated surface through the cell "
                "centres, not summed as vertical prisms.")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_dem = ""
        self.modified_dem = ""
        self.output_dir = ""
        self.result = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self.body)
        layout.setContentsMargins(0, 0, 0, 0)

        inputs = QGroupBox("Input")
        form = QFormLayout(inputs)

        self.b_original = QPushButton("Select DEM ...")
        self.b_original.clicked.connect(self.select_original)
        form.addRow("Original (pre-project) DEM:", self.b_original)

        self.b_modified = QPushButton("Select DEM ...")
        self.b_modified.clicked.connect(self.select_modified)
        form.addRow("Modified (post-project) DEM:", self.b_modified)

        lod_row = QHBoxLayout()
        self.lod = QDoubleSpinBox()
        # Force a dot decimal separator regardless of the desktop locale. Qt would otherwise
        # render "0,990" on a German or French desktop; the value stays a float either way,
        # but a comma separator in a numeric field is exactly the ambiguity that made
        # arcpy's GetRasterProperties unusable on those systems.
        self.lod.setLocale(QLocale.c())
        self.lod.setDecimals(3)
        self.lod.setRange(0.0, 1000.0)
        self.lod.setSingleStep(0.01)
        self.lod.setValue(0.99)
        self.lod.setToolTip("Elevation differences below this magnitude are treated as "
                            "survey noise and excluded from the quantities.")
        lod_row.addWidget(self.lod)
        self.lod_unit = QLabel(self.labels["length"])
        lod_row.addWidget(self.lod_unit)
        lod_row.addStretch(1)
        form.addRow("Level of detection:", lod_row)

        self.b_output = QPushButton("Select directory ... (optional)")
        self.b_output.clicked.connect(self.select_output)
        form.addRow("Output directory:", self.b_output)

        layout.addWidget(inputs)

        run_row = QHBoxLayout()
        self.b_run = QPushButton("Compute volumes")
        self.b_run.setDefault(True)
        self.b_run.clicked.connect(self.run_assessment)
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

    def _check_rasterio(self):
        """Disable the tab when the geospatial stack is missing, instead of failing on click.

        A QGIS interpreter often has no rasterio - starting there for the sake of the Mapping
        tab is a normal thing to do, and this tab should say so rather than raise later.
        """
        try:
            import rasterio  # noqa: F401
        except ImportError as exc:
            self.b_run.setEnabled(False)
            self.results.setPlainText(
                "The geospatial stack is not available in this Python environment, so the\n"
                "volume assessment is disabled (%s).\n\n"
                "This tab needs numpy, scipy and rasterio. If you started River Architect\n"
                "with the interpreter that owns the QGIS bindings, that interpreter\n"
                "typically has no rasterio: use the `ra-env` environment for analysis, and\n"
                "the QGIS interpreter for mapping." % exc)

    # ----------------------------------------------------------------- callbacks

    def on_unit_change(self):
        self.lod_unit.setText(self.labels["length"])
        self.lod.setValue(0.99 if self.unit == "us" else 0.30)

    def select_original(self):
        path = self.choose_file("Select the original (pre-project) DEM")
        if path:
            self.original_dem = path
            self.b_original.setText(self.elide(path))

    def select_modified(self):
        path = self.choose_file("Select the modified (post-project) DEM")
        if path:
            self.modified_dem = path
            self.b_modified.setText(self.elide(path))

    def select_output(self):
        path = self.choose_directory("Select an output directory")
        if path:
            self.output_dir = path
            self.b_output.setText(self.elide(path))

    # ------------------------------------------------------------------ analysis

    def run_assessment(self):
        if not self.original_dem or not self.modified_dem:
            self.warn("Missing input", "Select both an original and a modified DEM.")
            return

        lod = self.lod.value()
        unit = self.unit
        original, modified = self.original_dem, self.modified_dem
        output_dir = self.output_dir or None

        self.b_run.setEnabled(False)
        self.b_run.setText("Computing ...")
        self.progress.setRange(0, 0)          # busy indicator
        self.progress.show()
        self.results.setPlainText("Running ...")

        def work():
            from ...volume_assessment import VolumeAssessment
            assessment = VolumeAssessment(original, modified, unit=unit,
                                          level_of_detection=lod)
            return assessment.run(output_dir=output_dir)

        self.run_in_background(work, self._finish, self._error)

    def _reset_run_button(self):
        self.b_run.setEnabled(True)
        self.b_run.setText("Compute volumes")
        self.progress.hide()
        self.progress.setRange(0, 1)

    def _finish(self, result):
        self.result = result
        self._reset_run_button()
        lines = [
            "Fill volume        : %14.2f %s" % (result["fill_volume"], result["volume_unit"]),
            "Excavation volume  : %14.2f %s" % (result["excavation_volume"],
                                                result["volume_unit"]),
            "Net volume         : %14.2f %s" % (result["net_volume"], result["volume_unit"]),
            "",
            "Fill area          : %14.2f %s" % (result["fill_area"], result["area_unit"]),
            "Excavation area    : %14.2f %s" % (result["excavation_area"],
                                                result["area_unit"]),
            "Level of detection : %14.2f %s" % (result["level_of_detection"],
                                                self.labels["length"]),
        ]
        if "rasters" in result:
            lines += ["", "Rasters written to: %s"
                      % os.path.dirname(result["rasters"]["dod"])]
        self.results.setPlainText("\n".join(lines))

    def _error(self, exc):
        self._reset_run_button()
        self.results.setPlainText("ERROR: %s" % exc)
        self.fail("Volume assessment failed", str(exc))
