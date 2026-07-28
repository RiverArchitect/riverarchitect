"""Volume Assessment tab: earthworks quantities between two DEMs."""

import os
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter.messagebox import showinfo, showerror

from .base import RaModuleGui

__all__ = ["VolumeGui"]

RASTER_TYPES = [("Raster files", "*.tif *.tiff *.flt *.asc"), ("All files", "*.*")]


class VolumeGui(RaModuleGui):
    """Compare an original and a modified DEM and report fill/excavation volumes."""

    title = "Volume Assessment"

    def __init__(self, master=None):
        super().__init__(master)
        self.original_dem = ""
        self.modified_dem = ""
        self.output_dir = ""
        self.result = None
        self._build()

    def _build(self):
        row = 0
        tk.Label(self, text="Volume Assessment", font=("TkDefaultFont", 13, "bold")) \
            .grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=self.pad_x, pady=(10, 2))
        row += 1
        tk.Label(self, text="Earthworks quantities between a pre-project and a post-project DEM.\n"
                            "Volumes are integrated under the triangulated surface.",
                 justify=tk.LEFT, fg="dim gray") \
            .grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=self.pad_x, pady=(0, 10))

        row += 1
        tk.Label(self, text="Original (pre-project) DEM:").grid(
            row=row, column=0, sticky=tk.W, padx=self.pad_x, pady=self.pad_y)
        self.b_original = tk.Button(self, width=44, fg="red", text="Select DEM ...",
                                    command=self.select_original)
        self.b_original.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Modified (post-project) DEM:").grid(
            row=row, column=0, sticky=tk.W, padx=self.pad_x, pady=self.pad_y)
        self.b_modified = tk.Button(self, width=44, fg="red", text="Select DEM ...",
                                    command=self.select_modified)
        self.b_modified.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Level of detection:").grid(
            row=row, column=0, sticky=tk.W, padx=self.pad_x, pady=self.pad_y)
        self.lod_var = tk.StringVar(value="0.99")
        tk.Entry(self, textvariable=self.lod_var, width=10).grid(
            row=row, column=1, sticky=tk.W, padx=self.pad_x)
        self.l_lod_unit = tk.Label(self, text=self.labels["length"], fg="dim gray")
        self.l_lod_unit.grid(row=row, column=1, sticky=tk.W, padx=(90, 0))

        row += 1
        tk.Label(self, text="Output directory (optional):").grid(
            row=row, column=0, sticky=tk.W, padx=self.pad_x, pady=self.pad_y)
        self.b_output = tk.Button(self, width=44, text="Select directory ...",
                                  command=self.select_output)
        self.b_output.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        self.b_run = tk.Button(self, width=24, bg="pale green", text="Compute volumes",
                               command=self.run_assessment)
        self.b_run.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x, pady=(14, 6))

        row += 1
        self.result_text = tk.Text(self, height=9, width=84, state=tk.DISABLED,
                                   bg="gray95", relief=tk.FLAT)
        self.result_text.grid(row=row, column=0, columnspan=3, sticky=tk.W,
                              padx=self.pad_x, pady=self.pad_y)
        self._check_rasterio()

    def _check_rasterio(self):
        """Disable the tab when the geospatial stack is missing, rather than fail on click."""
        try:
            import rasterio  # noqa: F401
        except ImportError as exc:
            self.b_run.config(state=tk.DISABLED)
            self._write_result(
                "The geospatial stack is not available in this Python environment, so the\n"
                "volume assessment is disabled (%s).\n\n"
                "This tab needs numpy, scipy and rasterio. Use the `ra-env` environment for\n"
                "analysis, and the QGIS interpreter for mapping." % exc)

    # ----------------------------------------------------------------- callbacks

    def on_unit_change(self):
        self.l_lod_unit.config(text=self.labels["length"])
        self.lod_var.set("0.99" if self.unit == "us" else "0.30")

    def _short(self, path):
        return "Selected: ..." + os.sep + os.path.basename(path) if len(path) > 50 \
            else "Selected: " + path

    def select_original(self):
        path = askopenfilename(title="Select the original (pre-project) DEM",
                               filetypes=RASTER_TYPES)
        if path:
            self.original_dem = path
            self.b_original.config(fg="forest green", text=self._short(path))

    def select_modified(self):
        path = askopenfilename(title="Select the modified (post-project) DEM",
                               filetypes=RASTER_TYPES)
        if path:
            self.modified_dem = path
            self.b_modified.config(fg="forest green", text=self._short(path))

    def select_output(self):
        path = askdirectory(title="Select an output directory")
        if path:
            self.output_dir = path
            self.b_output.config(fg="forest green", text=self._short(path))

    # ------------------------------------------------------------------ analysis

    def run_assessment(self):
        if not self.original_dem or not self.modified_dem:
            showerror("Missing input", "Select both an original and a modified DEM.")
            return
        try:
            lod = float(self.lod_var.get())
        except ValueError:
            showerror("Invalid input", "The level of detection must be a number.")
            return

        self.b_run.config(state=tk.DISABLED, text="Computing ...")
        self._write_result("Running ...")

        def work():
            try:
                from ..volume_assessment import VolumeAssessment
                assessment = VolumeAssessment(self.original_dem, self.modified_dem,
                                              unit=self.unit, level_of_detection=lod)
                result = assessment.run(output_dir=self.output_dir or None)
                self.after(0, lambda: self._finish(result))
            except Exception as exc:
                self.after(0, lambda: self._fail(exc))

        threading.Thread(target=work, daemon=True).start()

    def _finish(self, result):
        self.result = result
        self.b_run.config(state=tk.NORMAL, text="Compute volumes")
        lines = [
            "Fill volume        : %14.2f %s" % (result["fill_volume"], result["volume_unit"]),
            "Excavation volume  : %14.2f %s" % (result["excavation_volume"], result["volume_unit"]),
            "Net volume         : %14.2f %s" % (result["net_volume"], result["volume_unit"]),
            "",
            "Fill area          : %14.2f %s" % (result["fill_area"], result["area_unit"]),
            "Excavation area    : %14.2f %s" % (result["excavation_area"], result["area_unit"]),
            "Level of detection : %14.2f %s" % (result["level_of_detection"],
                                                self.labels["length"]),
        ]
        if "rasters" in result:
            lines += ["", "Rasters written to: %s" % os.path.dirname(result["rasters"]["dod"])]
        self._write_result("\n".join(lines))

    def _fail(self, exc):
        self.b_run.config(state=tk.NORMAL, text="Compute volumes")
        self._write_result("ERROR: %s" % exc)
        showerror("Volume assessment failed", str(exc))

    def _write_result(self, text):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, text)
        self.result_text.config(state=tk.DISABLED)
