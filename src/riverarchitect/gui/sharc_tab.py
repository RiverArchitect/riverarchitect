"""Habitat Area (SHArC) tab (tkinter fallback)."""

import os
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askdirectory
from tkinter.messagebox import showerror, showwarning

from .base import RaModuleGui
from .. import config

__all__ = ["SharcGui"]


class SharcGui(RaModuleGui):
    """Habitat suitability curves applied to the hydraulics, integrated over flow duration."""

    title = "Habitat Area (SHArC)"

    def __init__(self, master=None):
        super().__init__(master)
        self.output_dir = ""
        self._fish = None
        self._build()

    def _build(self):
        row = 0
        tk.Label(self, text="Habitat Area (SHArC)", font=("TkDefaultFont", 13, "bold")) \
            .grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=self.pad_x, pady=(10, 2))
        row += 1
        tk.Label(self, text="Applies habitat suitability curves to depth and velocity, then "
                            "integrates\nthe usable area over the flow duration curve.",
                 justify=tk.LEFT, fg="dim gray") \
            .grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=self.pad_x, pady=(0, 8))

        row += 1
        tk.Label(self, text="Condition:").grid(row=row, column=0, sticky=tk.W,
                                               padx=self.pad_x, pady=self.pad_y)
        self.condition_var = tk.StringVar()
        self.condition_box = ttk.Combobox(self, textvariable=self.condition_var, width=28,
                                          values=self.condition_list, state="readonly")
        if self.condition_list:
            self.condition_box.current(0)
        self.condition_box.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Species:").grid(row=row, column=0, sticky=tk.W,
                                             padx=self.pad_x, pady=self.pad_y)
        self.species_var = tk.StringVar()
        self.species_box = ttk.Combobox(self, textvariable=self.species_var, width=28,
                                        state="readonly")
        self.species_box.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)
        self.species_box.bind("<<ComboboxSelected>>", lambda _e: self._populate_lifestages())

        row += 1
        tk.Label(self, text="Lifestage:").grid(row=row, column=0, sticky=tk.W,
                                               padx=self.pad_x, pady=self.pad_y)
        self.lifestage_var = tk.StringVar()
        self.lifestage_box = ttk.Combobox(self, textvariable=self.lifestage_var, width=28,
                                          state="readonly")
        self.lifestage_box.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Combine method:").grid(row=row, column=0, sticky=tk.W,
                                                    padx=self.pad_x, pady=self.pad_y)
        self.method_var = tk.StringVar(value="geometric_mean")
        ttk.Combobox(self, textvariable=self.method_var, width=28, state="readonly",
                     values=["geometric_mean", "product"]) \
            .grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Usable habitat threshold:").grid(
            row=row, column=0, sticky=tk.W, padx=self.pad_x, pady=self.pad_y)
        self.threshold_var = tk.StringVar(value="0.4")
        tk.Entry(self, textvariable=self.threshold_var, width=10).grid(
            row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        self.weighted_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self, text="weight usable area by the mean suitability",
                       variable=self.weighted_var) \
            .grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Output directory (optional):").grid(
            row=row, column=0, sticky=tk.W, padx=self.pad_x, pady=self.pad_y)
        self.b_output = tk.Button(self, width=38, text="Select directory ...",
                                  command=self.select_output)
        self.b_output.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        self.b_run = tk.Button(self, width=30, bg="pale green",
                               text="Calculate habitat suitability", command=self.run_analysis)
        self.b_run.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x, pady=(12, 6))

        row += 1
        self.results = tk.Text(self, height=11, width=86, state=tk.DISABLED,
                               bg="gray95", relief=tk.FLAT)
        self.results.grid(row=row, column=0, columnspan=3, sticky=tk.W,
                          padx=self.pad_x, pady=self.pad_y)
        self._load_fish()

    def _load_fish(self):
        try:
            from ..sharc import FishDatabase
            self._fish = FishDatabase()
        except Exception as exc:
            self.b_run.config(state=tk.DISABLED)
            self._write("The habitat suitability database could not be loaded (%s).\n\n"
                        "Use the `ra-env` environment for analysis." % exc)
            return
        self.species_box.config(values=self._fish.species)
        if self._fish.species:
            self.species_box.current(0)
            self._populate_lifestages()

    def _populate_lifestages(self):
        if self._fish is None:
            return
        stages = self._fish.lifestages(self.species_var.get())
        self.lifestage_box.config(values=stages)
        if stages:
            self.lifestage_box.current(0)

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
        name = self.condition_var.get()
        species = self.species_var.get()
        lifestage = self.lifestage_var.get()
        if not (name and species and lifestage):
            showwarning("Missing input", "Select a condition, a species and a lifestage.")
            return
        try:
            threshold = float(self.threshold_var.get())
        except ValueError:
            showerror("Invalid input", "The threshold must be a number between 0 and 1.")
            return

        unit = self.unit
        method = self.method_var.get()
        weighted = self.weighted_var.get()
        output_dir = self.output_dir or None

        self.b_run.config(state=tk.DISABLED, text="Calculating ...")
        self._write("Calculating habitat suitability for %s - %s ..." % (species, lifestage))

        def work():
            try:
                from ..sharc import SHArC
                analysis = SHArC(name, unit=unit, combine_method=method,
                                 threshold=threshold)
                result = analysis.run(species, lifestage, output_dir=output_dir,
                                      weighted=weighted)
                self.after(0, lambda: self._finish(result))
            except Exception as exc:
                self.after(0, lambda: self._fail(exc))

        threading.Thread(target=work, daemon=True).start()

    def _finish(self, result):
        self.b_run.config(state=tk.NORMAL, text="Calculate habitat suitability")
        area = result["area_unit"]
        lines = ["%s - %s  (%s, threshold %.2f)"
                 % (result["species"], result["lifestage"], result["combine_method"],
                    result["threshold"]), "",
                 "%10s %15s %11s" % ("Q (%s)" % result["discharge_unit"],
                                     "usable (%s)" % area, "mean cHSI"),
                 "-" * 40]
        for row in result["per_discharge"]:
            lines.append("%10.0f %15.0f %11.3f"
                         % (row["discharge"], row["usable_area"], row["mean_chsi"]))
        if "sharea" in result:
            lines += ["", "Seasonal Habitat Area: %.0f %s" % (result["sharea"], area)]
        else:
            lines += ["", "No flow duration workbook for code '%s' - SHArea not computed."
                      % result["shortname"]]
        if result.get("output_dir"):
            lines += ["", "Written to: %s" % result["output_dir"]]
        self._write("\n".join(lines))

    def _fail(self, exc):
        self.b_run.config(state=tk.NORMAL, text="Calculate habitat suitability")
        self._write("ERROR: %s" % exc)
        showerror("Habitat suitability failed", str(exc))

    def _write(self, text):
        self.results.config(state=tk.NORMAL)
        self.results.delete("1.0", tk.END)
        self.results.insert(tk.END, text)
        self.results.config(state=tk.DISABLED)
