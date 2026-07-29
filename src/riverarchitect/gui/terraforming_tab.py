"""Terraforming tab: threshold-based grading and widening for planting."""

import os
import threading
import tkinter as tk
from tkinter.filedialog import askdirectory
from tkinter.messagebox import showerror

from .base import RaModuleGui

__all__ = ["TerraformingGui"]


class TerraformingGui(RaModuleGui):
    """Lower a DEM where planned plantings cannot reach the water table."""

    title = "Terraforming"

    def __init__(self, master=None):
        super().__init__(master)
        self.action_dir = ""
        self.output_dir = ""
        self.result = None
        self._build()

    def _build(self):
        row = 0
        tk.Label(self, text="Terraforming", font=("TkDefaultFont", 13, "bold")) \
            .grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=self.pad_x,
                  pady=(10, 2))
        row += 1
        tk.Label(self, text="Lowers the terrain where a planned feature sits too far above "
                            "the water table\nfor its roots, by exactly the excess. Feed "
                            "the result to Volume Assessment.",
                 justify=tk.LEFT, fg="dim gray") \
            .grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=self.pad_x,
                  pady=(0, 10))

        row += 1
        tk.Label(self, text="Condition:").grid(row=row, column=0, sticky=tk.W,
                                               padx=self.pad_x, pady=self.pad_y)
        self.condition_var = tk.StringVar(value=self.condition_list[0]
                                          if self.condition_list else "")
        self.condition_menu = tk.OptionMenu(self, self.condition_var,
                                            *(self.condition_list or [""]))
        self.condition_menu.config(width=40)
        self.condition_menu.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Feature action rasters:").grid(
            row=row, column=0, sticky=tk.W, padx=self.pad_x, pady=self.pad_y)
        self.b_actions = tk.Button(self, width=44, fg="red",
                                   text="Select directory ...",
                                   command=self.select_actions)
        self.b_actions.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Max. depth to water table:").grid(
            row=row, column=0, sticky=tk.W, padx=self.pad_x, pady=self.pad_y)
        self.d2w_var = tk.StringVar(value="%.2f" % self._default_limit())
        tk.Entry(self, textvariable=self.d2w_var, width=10).grid(
            row=row, column=1, sticky=tk.W, padx=self.pad_x)
        self.l_d2w_unit = tk.Label(self, text=self.labels["length"], fg="dim gray")
        self.l_d2w_unit.grid(row=row, column=1, sticky=tk.W, padx=(90, 0))

        row += 1
        tk.Label(self, text="Output directory (optional):").grid(
            row=row, column=0, sticky=tk.W, padx=self.pad_x, pady=self.pad_y)
        self.b_output = tk.Button(self, width=44, text="Select directory ...",
                                  command=self.select_output)
        self.b_output.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        self.b_run = tk.Button(self, width=24, bg="pale green", text="Modify terrain",
                               command=self.run_terraforming)
        self.b_run.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x, pady=(14, 6))

        row += 1
        self.result_text = tk.Text(self, height=12, width=84, state=tk.DISABLED,
                                   bg="gray95", relief=tk.FLAT)
        self.result_text.grid(row=row, column=0, columnspan=3, sticky=tk.W,
                              padx=self.pad_x, pady=self.pad_y)
        self._check_rasterio()

    @staticmethod
    def _default_limit():
        try:
            from ..terraforming import planting_depth_limit
            return planting_depth_limit()
        except Exception:
            return 7.0

    def _check_rasterio(self):
        """Disable the tab when the geospatial stack is missing, rather than fail on click."""
        try:
            import rasterio  # noqa: F401
        except ImportError as exc:
            self.b_run.config(state=tk.DISABLED)
            self._write_result(
                "The geospatial stack is not available in this Python environment, so\n"
                "terraforming is disabled (%s).\n\n"
                "This tab needs numpy, scipy and rasterio. Use the `ra-env` environment for\n"
                "analysis, and the QGIS interpreter for mapping." % exc)

    # ----------------------------------------------------------------- callbacks

    def on_unit_change(self):
        self.l_d2w_unit.config(text=self.labels["length"])

    def on_project_home_change(self):
        super().on_project_home_change()
        menu = self.condition_menu["menu"]
        menu.delete(0, tk.END)
        for name in self.condition_list:
            menu.add_command(label=name,
                             command=lambda value=name: self.condition_var.set(value))
        self.condition_var.set(self.condition_list[0] if self.condition_list else "")

    def _short(self, path):
        return "Selected: ..." + os.sep + os.path.basename(path) if len(path) > 50 \
            else "Selected: " + path

    def select_actions(self):
        from .. import config

        start = os.path.join(config.dir_output("MaxLifespan"), self.condition_var.get())
        path = askdirectory(title="Select the feature action raster directory",
                            initialdir=start if os.path.isdir(start)
                            else config.project_home())
        if path:
            self.action_dir = path
            self.b_actions.config(fg="forest green", text=self._short(path))

    def select_output(self):
        path = askdirectory(title="Select an output directory")
        if path:
            self.output_dir = path
            self.b_output.config(fg="forest green", text=self._short(path))

    # ------------------------------------------------------------------ analysis

    def run_terraforming(self):
        condition = self.condition_var.get()
        if not condition:
            showerror("Missing input", "Select a condition.")
            return
        if not self.action_dir:
            showerror("Missing input",
                      "Select the directory holding the feature action rasters.\n\n"
                      "That is normally the Max Lifespan output folder; run Max Lifespan "
                      "first if it does not exist yet.")
            return
        try:
            d2w_max = float(self.d2w_var.get())
        except ValueError:
            showerror("Invalid input",
                      "The maximum depth to the water table must be a number.")
            return

        self.b_run.config(state=tk.DISABLED, text="Modifying ...")
        self._write_result("Running ...")

        def work():
            try:
                from ..terraforming import Terraforming
                analysis = Terraforming(condition, self.action_dir, unit=self.unit,
                                        d2w_max=d2w_max)
                result = analysis.run(output_dir=self.output_dir or None)
                self.after(0, lambda: self._finish(result))
            except Exception as exc:
                self.after(0, lambda: self._fail(exc))

        threading.Thread(target=work, daemon=True).start()

    def _finish(self, result):
        self.result = result
        self.b_run.config(state=tk.NORMAL, text="Modify terrain")
        length = self.labels["length"]
        lines = [
            "Max. depth to water table : %12.2f %s" % (result["d2w_max"], length),
            "Cells lowered             : %12d" % result["modified_cells"],
            "Area lowered              : %12.0f %s" % (result["modified_area"],
                                                       result["area_unit"]),
            "Excavated volume          : %12.0f cubic %s" % (result["cut_volume"], length),
            "Deepest cut               : %12.2f %s" % (result["max_cut"], length),
            "",
            "%-14s %10s %14s %12s" % ("feature", "cells", "area", "volume"),
        ]
        for row in result["per_feature"]:
            lines.append("%-14s %10d %14.0f %12.0f"
                         % (row["feature"], row["cells"], row["area"], row["volume"]))
        if "output_dir" in result:
            lines += ["", "Written to: %s" % result["output_dir"],
                      "Feed dem_terraformed.tif to Volume Assessment as the modified DEM."]
        self._write_result("\n".join(lines))

    def _fail(self, exc):
        self.b_run.config(state=tk.NORMAL, text="Modify terrain")
        self._write_result("ERROR: %s" % exc)
        showerror("Terraforming failed", str(exc))

    def _write_result(self, text):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, text)
        self.result_text.config(state=tk.DISABLED)
