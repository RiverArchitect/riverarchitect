"""Lifespan and design mapping tab (tkinter fallback)."""

import os
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askdirectory
from tkinter.messagebox import showerror, showwarning

from .base import RaModuleGui
from .. import config

__all__ = ["LifespanGui"]


class LifespanGui(RaModuleGui):
    """Map how long each restoration feature survives, and how big it has to be."""

    title = "Lifespan Design"

    def __init__(self, master=None):
        super().__init__(master)
        self.output_dir = ""
        self._build()

    def _build(self):
        row = 0
        tk.Label(self, text="Lifespan and design", font=("TkDefaultFont", 13, "bold")) \
            .grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=self.pad_x, pady=(10, 2))
        row += 1
        tk.Label(self, text="Predicts how many years a feature survives at each cell, from "
                            "the flood return\nperiods of the modelled discharges.",
                 justify=tk.LEFT, fg="dim gray") \
            .grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=self.pad_x, pady=(0, 8))

        row += 1
        tk.Label(self, text="Condition:").grid(row=row, column=0, sticky=tk.W,
                                               padx=self.pad_x, pady=self.pad_y)
        self.condition_var = tk.StringVar()
        self.condition_box = ttk.Combobox(self, textvariable=self.condition_var, width=30,
                                          values=self.condition_list, state="readonly")
        if self.condition_list:
            self.condition_box.current(0)
        self.condition_box.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Manning's n:").grid(row=row, column=0, sticky=tk.W,
                                                 padx=self.pad_x, pady=self.pad_y)
        self.manning_var = tk.StringVar(value="0.04739")
        tk.Entry(self, textvariable=self.manning_var, width=12).grid(
            row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Features:").grid(row=row, column=0, sticky=tk.NW,
                                              padx=self.pad_x, pady=self.pad_y)
        frame = tk.Frame(self)
        frame.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)
        self.feature_box = tk.Listbox(frame, selectmode=tk.EXTENDED, height=9, width=42,
                                      exportselection=False)
        scrollbar = tk.Scrollbar(frame, command=self.feature_box.yview)
        self.feature_box.config(yscrollcommand=scrollbar.set)
        self.feature_box.pack(side=tk.LEFT)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self._populate_features()

        row += 1
        tk.Label(self, text="Output directory (optional):").grid(
            row=row, column=0, sticky=tk.W, padx=self.pad_x, pady=self.pad_y)
        self.b_output = tk.Button(self, width=40, text="Select directory ...",
                                  command=self.select_output)
        self.b_output.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        self.b_run = tk.Button(self, width=30, bg="pale green",
                               text="Create lifespan and design maps",
                               command=self.run_analysis)
        self.b_run.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x, pady=(12, 6))

        row += 1
        self.results = tk.Text(self, height=10, width=88, state=tk.DISABLED,
                               bg="gray95", relief=tk.FLAT)
        self.results.grid(row=row, column=0, columnspan=3, sticky=tk.W,
                          padx=self.pad_x, pady=self.pad_y)
        self._check_dependencies()

    def _populate_features(self):
        self.feature_ids = []
        self.feature_box.delete(0, tk.END)
        try:
            from ..lifespan import feature_groups
        except ImportError:
            return
        for group, features in feature_groups().items():
            for feature in features:
                if not feature.lifespan_mapping:
                    continue
                self.feature_box.insert(tk.END, "%-24s %s" % (feature.name, group))
                self.feature_ids.append(feature.fid)
                if feature.fid == "rocks":
                    self.feature_box.selection_set(tk.END)

    def _check_dependencies(self):
        try:
            import rasterio  # noqa: F401
        except ImportError as exc:
            self.b_run.config(state=tk.DISABLED)
            self._write("The geospatial stack is not available in this Python environment,\n"
                        "so lifespan mapping is disabled (%s).\n\n"
                        "Use the `ra-env` environment for analysis." % exc)

    def on_project_home_change(self):
        super().on_project_home_change()
        self.condition_box.config(values=self.condition_list)
        if self.condition_list:
            self.condition_box.current(0)

    def select_output(self):
        path = askdirectory(title="Select an output directory")
        if path:
            self.output_dir = path
            self.b_output.config(fg="forest green", text=os.path.basename(path))

    def run_analysis(self):
        selected = [self.feature_ids[i] for i in self.feature_box.curselection()]
        if not selected:
            showwarning("No feature selected", "Select at least one feature to map.")
            return
        name = self.condition_var.get()
        if not name:
            showwarning("No condition", "Select a condition first.")
            return
        try:
            manning = float(self.manning_var.get())
        except ValueError:
            showerror("Invalid input", "Manning's n must be a number.")
            return

        unit = self.unit
        output_dir = self.output_dir or os.path.join(
            config.dir_output("LifespanDesign"), name)

        self.b_run.config(state=tk.DISABLED, text="Mapping ...")
        self._write("Mapping %d feature(s) for '%s' ..." % (len(selected), name))

        def work():
            try:
                from ..lifespan import LifespanDesign
                analysis = LifespanDesign(name, unit=unit, manning_n=manning)
                results = analysis.run(selected, output_dir=output_dir)
                self.after(0, lambda: self._finish(results, output_dir))
            except Exception as exc:
                self.after(0, lambda: self._fail(exc))

        threading.Thread(target=work, daemon=True).start()

    def _finish(self, results, output_dir):
        self.b_run.config(state=tk.NORMAL, text="Create lifespan and design maps")
        if not results:
            self._write("No feature could be mapped. The condition may be missing the "
                        "rasters these features need.")
            return
        unit = results[0].get("area_unit", "sqft")
        lines = ["%-10s %-24s %12s  %s" % ("feature", "name", "area (%s)" % unit, "lifespan"),
                 "-" * 74]
        for entry in results:
            span = "%s to %s years" % (entry.get("min_lifespan", "-"),
                                       entry.get("max_lifespan", "-")) \
                if "min_lifespan" in entry else "nothing mapped"
            lines.append("%-10s %-24s %12.0f  %s"
                         % (entry["feature"], entry["name"][:24], entry["area"], span))
        lines += ["", "Rasters written to: %s" % output_dir]
        self._write("\n".join(lines))

    def _fail(self, exc):
        self.b_run.config(state=tk.NORMAL, text="Create lifespan and design maps")
        self._write("ERROR: %s" % exc)
        showerror("Lifespan mapping failed", str(exc))

    def _write(self, text):
        self.results.config(state=tk.NORMAL)
        self.results.delete("1.0", tk.END)
        self.results.insert(tk.END, text)
        self.results.config(state=tk.DISABLED)
