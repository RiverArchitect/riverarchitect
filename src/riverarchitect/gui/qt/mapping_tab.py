"""Mapping tab: QGIS print-layout map series."""

import os

from ... import config
from .base import RaTab
from .qtcompat import (QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLineEdit,
                       QPlainTextEdit, QProgressBar, QPushButton, QVBoxLayout)

__all__ = ["MappingTab"]

MAP_TYPES = [("Lifespan", "lf"),
             ("Design", "ds"),
             ("Max lifespan", "mlf"),
             ("Modify terrain", "mt")]


class MappingTab(RaTab):
    """Render a folder of rasters into PDF maps through QGIS print layouts."""

    title = "Mapping"
    subtitle = ("Renders rasters into PDF maps through QGIS print layouts. A multi-page "
                "reach series is produced with a QGIS atlas.")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.raster_dir = ""
        self.output_dir = ""
        self._build()
        self._check_qgis()

    def _build(self):
        layout = QVBoxLayout(self.body)
        layout.setContentsMargins(0, 0, 0, 0)

        inputs = QGroupBox("Input")
        form = QFormLayout(inputs)

        self.condition = QComboBox()
        self.condition.setEditable(True)
        self.condition.addItems(self.condition_list)
        form.addRow("Condition:", self.condition)

        self.map_type = QComboBox()
        for label, key in MAP_TYPES:
            self.map_type.addItem(label, key)
        form.addRow("Map type:", self.map_type)

        self.b_rasters = QPushButton("Select directory ...")
        self.b_rasters.clicked.connect(self.select_rasters)
        form.addRow("Raster directory:", self.b_rasters)

        self.b_output = QPushButton("Select directory ... (optional)")
        self.b_output.clicked.connect(self.select_output)
        form.addRow("Output directory:", self.b_output)

        layout.addWidget(inputs)

        run_row = QHBoxLayout()
        self.b_run = QPushButton("Create maps")
        self.b_run.clicked.connect(self.run_mapping)
        run_row.addWidget(self.b_run)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setTextVisible(False)
        self.progress.hide()
        run_row.addWidget(self.progress, 1)
        layout.addLayout(run_row)

        self.status = QPlainTextEdit()
        self.status.setReadOnly(True)
        layout.addWidget(self.status, 1)

    def on_project_home_change(self):
        super().on_project_home_change()
        current = self.condition.currentText()
        self.condition.clear()
        self.condition.addItems(self.condition_list)
        if current:
            self.condition.setEditText(current)

    def _check_qgis(self):
        from ...mapping import qgis_status

        available, message = qgis_status()
        self.status.setPlainText(message)
        self.b_run.setEnabled(available)

    # ----------------------------------------------------------------- callbacks

    def select_rasters(self):
        path = self.choose_directory("Select the directory holding the rasters to map")
        if not path:
            return
        self.raster_dir = path
        count = len([f for f in os.listdir(path) if f.lower().endswith((".tif", ".tiff"))])
        self.b_rasters.setText("%s  (%d raster%s)"
                               % (os.path.basename(path), count, "" if count == 1 else "s"))

    def select_output(self):
        path = self.choose_directory("Select an output directory")
        if path:
            self.output_dir = path
            self.b_output.setText(self.elide(path))

    # ------------------------------------------------------------------- mapping

    def run_mapping(self):
        if not self.raster_dir:
            self.warn("Missing input", "Select a directory holding the rasters to map.")
            return

        condition = self.condition.currentText().strip() or "condition"
        output = self.output_dir or os.path.join(config.dir_maps(), condition)
        raster_dir = self.raster_dir
        map_type = self.map_type.currentData()

        self.b_run.setEnabled(False)
        self.b_run.setText("Mapping ...")
        self.progress.setRange(0, 0)
        self.progress.show()
        self.status.setPlainText("Creating maps for '%s' ...\nOutput: %s"
                                 % (condition, output))

        def work():
            from ...mapping import Mapper
            mapper = Mapper(condition, map_type, raster_dir, output)
            mapper.prepare_layout(True)
            return mapper, output

        self.run_in_background(work, self._finish, self._error)

    def _reset_run_button(self):
        self.b_run.setEnabled(True)
        self.b_run.setText("Create maps")
        self.progress.hide()
        self.progress.setRange(0, 1)

    def _finish(self, payload):
        mapper, output = payload
        self._reset_run_button()
        pdfs = sorted(f for f in os.listdir(output) if f.lower().endswith(".pdf")) \
            if os.path.isdir(output) else []
        listing = "\n  ".join(pdfs) if pdfs else "none"
        if mapper.error:
            self.status.setPlainText("Finished with errors; see the log for details.\n\n"
                                     "PDFs written:\n  %s" % listing)
        else:
            self.status.setPlainText("Finished.\n\nOutput directory:\n%s\n\n"
                                     "PDFs written:\n  %s" % (output, listing))

    def _error(self, exc):
        self._reset_run_button()
        self.status.setPlainText("ERROR: %s" % exc)
        self.fail("Mapping failed", str(exc))
