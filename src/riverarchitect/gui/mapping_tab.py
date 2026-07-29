"""Mapping tab: QGIS print-layout map series."""

import os
import threading
import tkinter as tk
from tkinter.filedialog import askdirectory
from tkinter.messagebox import showinfo, showerror

from .base import RaModuleGui
from .. import config

__all__ = ["MappingGui"]

MAP_TYPES = [("lf", "Lifespan"),
             ("ds", "Design"),
             ("mlf", "Max Lifespan"),
             ("mt", "Modify Terrain")]


class MappingGui(RaModuleGui):
    """Produce PDF map series from a folder of rasters using QGIS print layouts."""

    title = "Mapping"

    def __init__(self, master=None):
        super().__init__(master)
        self.raster_dir = ""
        self.output_dir = ""
        self._build()

    def _build(self):
        row = 0
        tk.Label(self, text="Mapping", font=("TkDefaultFont", 13, "bold")) \
            .grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=self.pad_x, pady=(10, 2))
        row += 1
        tk.Label(self, text="Renders rasters into PDF maps through QGIS print layouts.\n"
                            "A multi-page series is produced with a QGIS atlas.",
                 justify=tk.LEFT, fg="dim gray") \
            .grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=self.pad_x, pady=(0, 10))

        row += 1
        tk.Label(self, text="Condition name:").grid(
            row=row, column=0, sticky=tk.W, padx=self.pad_x, pady=self.pad_y)
        self.condition_var = tk.StringVar(value="")
        tk.Entry(self, textvariable=self.condition_var, width=32).grid(
            row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Map type:").grid(
            row=row, column=0, sticky=tk.W, padx=self.pad_x, pady=self.pad_y)
        self.map_type_var = tk.StringVar(value=MAP_TYPES[0][0])
        frame = tk.Frame(self)
        frame.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)
        for key, label in MAP_TYPES:
            tk.Radiobutton(frame, text=label, value=key,
                           variable=self.map_type_var).pack(side=tk.LEFT)

        row += 1
        tk.Label(self, text="Raster directory:").grid(
            row=row, column=0, sticky=tk.W, padx=self.pad_x, pady=self.pad_y)
        self.b_rasters = tk.Button(self, width=44, fg="red", text="Select directory ...",
                                   command=self.select_rasters)
        self.b_rasters.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Output directory:").grid(
            row=row, column=0, sticky=tk.W, padx=self.pad_x, pady=self.pad_y)
        self.b_output = tk.Button(self, width=44, text="Select directory ...",
                                  command=self.select_output)
        self.b_output.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        self.b_run = tk.Button(self, width=24, bg="pale green", text="Create maps",
                               command=self.run_mapping)
        self.b_run.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x, pady=(14, 6))

        row += 1
        self.status = tk.Text(self, height=9, width=84, state=tk.DISABLED,
                              bg="gray95", relief=tk.FLAT)
        self.status.grid(row=row, column=0, columnspan=3, sticky=tk.W,
                         padx=self.pad_x, pady=self.pad_y)
        self._check_qgis()

    def _check_qgis(self):
        from ..mapping import qgis_status

        available, message = qgis_status()
        self._write(message)
        self.b_run.config(state=tk.NORMAL if available else tk.DISABLED)

    def select_rasters(self):
        path = askdirectory(title="Select the directory holding the rasters to map")
        if path:
            self.raster_dir = path
            count = len([f for f in os.listdir(path) if f.lower().endswith((".tif", ".tiff"))])
            self.b_rasters.config(fg="forest green",
                                  text="Selected: %s (%d raster(s))"
                                       % (os.path.basename(path), count))

    def select_output(self):
        path = askdirectory(title="Select an output directory")
        if path:
            self.output_dir = path
            self.b_output.config(fg="forest green", text="Selected: " + os.path.basename(path))

    def run_mapping(self):
        if not self.raster_dir:
            showerror("Missing input", "Select a directory holding the rasters to map.")
            return
        condition = self.condition_var.get().strip() or "condition"
        output = self.output_dir or os.path.join(config.dir_maps(), condition)

        self.b_run.config(state=tk.DISABLED, text="Mapping ...")
        self._write("Creating maps for '%s' ...\nOutput: %s" % (condition, output))

        def work():
            try:
                from ..mapping import Mapper
                mapper = Mapper(condition, self.map_type_var.get(), self.raster_dir, output)
                mapper.prepare_layout(True)
                self.after(0, lambda: self._finish(mapper, output))
            except Exception as exc:
                self.after(0, lambda: self._fail(exc))

        threading.Thread(target=work, daemon=True).start()

    def _finish(self, mapper, output):
        self.b_run.config(state=tk.NORMAL, text="Create maps")
        pdfs = sorted(f for f in os.listdir(output) if f.lower().endswith(".pdf")) \
            if os.path.isdir(output) else []
        if mapper.error:
            self._write("Finished with errors. See the log for details.\n\n"
                        "PDFs written: %s" % (", ".join(pdfs) or "none"))
        else:
            self._write("Finished.\n\nOutput directory:\n%s\n\nPDFs written:\n  %s"
                        % (output, "\n  ".join(pdfs) or "none"))

    def _fail(self, exc):
        self.b_run.config(state=tk.NORMAL, text="Create maps")
        self._write("ERROR: %s" % exc)
        showerror("Mapping failed", str(exc))

    def _write(self, text):
        self.status.config(state=tk.NORMAL)
        self.status.delete("1.0", tk.END)
        self.status.insert(tk.END, text)
        self.status.config(state=tk.DISABLED)
