"""Riparian seedling recruitment tab (tkinter fallback)."""

import os
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askdirectory, askopenfilename
from tkinter.messagebox import showerror, showwarning

from .base import RaModuleGui

__all__ = ["RecruitmentGui"]


class RecruitmentGui(RaModuleGui):
    """Where cottonwood and willow seedlings can establish and survive their first season."""

    title = "Riparian Seedling Recruitment"

    def __init__(self, master=None):
        super().__init__(master)
        self.flow_path = ""
        self.parameters_path = ""
        self.vegetation_path = ""
        self.output_dir = ""
        self._build()

    def _build(self):
        row = 0
        tk.Label(self, text="Riparian seedling recruitment",
                 font=("TkDefaultFont", 13, "bold")) \
            .grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=self.pad_x, pady=(10, 2))
        row += 1
        tk.Label(self, text="Maps where all four objectives of the Recruitment Box Model "
                            "coincide: seedbed\nprepared, slow recession, no drowning, no "
                            "scour.",
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
        tk.Label(self, text="Daily flow record:").grid(row=row, column=0, sticky=tk.W,
                                                       padx=self.pad_x, pady=self.pad_y)
        self.b_flow = tk.Button(self, width=38, fg="red", text="Select flow record ...",
                                command=self.select_flow)
        self.b_flow.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Season:").grid(row=row, column=0, sticky=tk.W,
                                            padx=self.pad_x, pady=self.pad_y)
        self.year_var = tk.StringVar()
        self.year_box = ttk.Combobox(self, textvariable=self.year_var, width=12,
                                     state="readonly")
        self.year_box.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Parameters:").grid(row=row, column=0, sticky=tk.W,
                                                padx=self.pad_x, pady=self.pad_y)
        self.b_parameters = tk.Button(self, width=38,
                                      text="packaged recruitment_parameters.xlsx",
                                      command=self.select_parameters)
        self.b_parameters.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Existing vegetation:").grid(row=row, column=0, sticky=tk.W,
                                                         padx=self.pad_x, pady=self.pad_y)
        self.b_vegetation = tk.Button(self, width=38, text="Select raster ... (optional)",
                                      command=self.select_vegetation)
        self.b_vegetation.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Output directory (optional):").grid(
            row=row, column=0, sticky=tk.W, padx=self.pad_x, pady=self.pad_y)
        self.b_output = tk.Button(self, width=38, text="Select directory ...",
                                  command=self.select_output)
        self.b_output.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        self.info = tk.Label(self, text="Select a daily flow record to begin.",
                             fg="dim gray", justify=tk.LEFT, wraplength=580)
        self.info.grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=self.pad_x)

        row += 1
        self.b_run = tk.Button(self, width=30, bg="pale green",
                               text="Assess recruitment potential", command=self.run_analysis)
        self.b_run.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x, pady=(12, 6))

        row += 1
        self.results = tk.Text(self, height=11, width=86, state=tk.DISABLED,
                               bg="gray95", relief=tk.FLAT)
        self.results.grid(row=row, column=0, columnspan=3, sticky=tk.W,
                          padx=self.pad_x, pady=self.pad_y)
        self._check_dependencies()

    def _check_dependencies(self):
        try:
            import rasterio  # noqa: F401
            import pandas  # noqa: F401
        except ImportError as exc:
            self.b_run.config(state=tk.DISABLED)
            self._write("The geospatial stack is not available here (%s).\n"
                        "Use the `ra-env` environment for analysis." % exc)

    def on_project_home_change(self):
        super().on_project_home_change()
        self.condition_box.config(values=self.condition_list)
        if self.condition_list:
            self.condition_box.current(0)

    def select_flow(self):
        path = askopenfilename(title="Select the daily flow record",
                               filetypes=[("Tables", "*.xlsx *.xls *.csv"),
                                          ("All files", "*.*")])
        if not path:
            return
        self.flow_path = path
        self.b_flow.config(fg="forest green", text=os.path.basename(path))
        try:
            from ..recruitment import read_flow_series
            series = read_flow_series(path)
        except Exception as exc:
            self.info.config(text="Could not read the flow record: %s" % exc)
            return
        if not series:
            self.info.config(text="The flow record contains no usable rows.")
            return
        years = sorted({date.year for date in series})
        self.year_box.config(values=[str(value) for value in years])
        self.year_box.current(len(years) - 1)
        self.info.config(text="%d daily value(s), %s to %s."
                              % (len(series), min(series), max(series)))

    def select_parameters(self):
        path = askopenfilename(title="Select a recruitment_parameters.xlsx",
                               filetypes=[("Workbooks", "*.xlsx *.xls"),
                                          ("All files", "*.*")])
        if path:
            self.parameters_path = path
            self.b_parameters.config(fg="forest green", text=os.path.basename(path))

    def select_vegetation(self):
        path = askopenfilename(title="Select an existing vegetation raster",
                               filetypes=[("Raster files", "*.tif *.tiff"),
                                          ("All files", "*.*")])
        if path:
            self.vegetation_path = path
            self.b_vegetation.config(fg="forest green", text=os.path.basename(path))

    def select_output(self):
        path = askdirectory(title="Select an output directory")
        if path:
            self.output_dir = path
            self.b_output.config(fg="forest green", text=os.path.basename(path))

    def run_analysis(self):
        name = self.condition_var.get()
        if not name:
            showwarning("No condition", "Select a condition first.")
            return
        if not self.flow_path:
            showwarning("No flow record",
                        "Recruitment needs a daily flow record: bed preparation, recession "
                        "and scour all depend on when flows happened.")
            return
        if not self.year_var.get():
            showwarning("No season", "The flow record yielded no season to analyse.")
            return

        year = int(self.year_var.get())
        flow_path = self.flow_path
        parameters_path = self.parameters_path or None
        vegetation = self.vegetation_path or None
        unit = self.unit
        output_dir = self.output_dir or None

        self.b_run.config(state=tk.DISABLED, text="Assessing ...")
        self._write("Assessing recruitment potential for %d ..." % year)

        def work():
            try:
                from ..recruitment import RecruitmentParameters, RecruitmentPotential
                parameters = RecruitmentParameters.from_workbook(parameters_path)
                analysis = RecruitmentPotential(name, flow_path, year=year,
                                                parameters=parameters, unit=unit,
                                                existing_vegetation=vegetation)
                result = analysis.run(output_dir=output_dir)
                self.after(0, lambda: self._finish(result))
            except Exception as exc:
                self.after(0, lambda: self._fail(exc))

        threading.Thread(target=work, daemon=True).start()

    def _finish(self, result):
        self.b_run.config(state=tk.NORMAL, text="Assess recruitment potential")
        area = result["area_unit"]
        lines = ["%s, season %d" % (result["species"], result["year"]), "",
                 "%-24s %13s" % ("", "area (%s)" % area), "-" * 39,
                 "%-24s %13.0f" % ("recruitment area", result["crop_area"])]
        for name, value in result["objectives"].items():
            lines.append("%-24s %13.0f" % ("  " + name.replace("_", " "), value))
        lines += ["-" * 39,
                  "%-24s %13.0f" % ("full potential", result["recruitment_area"]),
                  "%-24s %13.0f" % ("partial potential", result["partial_area"]), "",
                  "The four objectives are multiplied, so a zero anywhere is a zero overall."]
        if result.get("output_dir"):
            lines += ["", "Written to: %s" % result["output_dir"]]
        self._write("\n".join(lines))

    def _fail(self, exc):
        self.b_run.config(state=tk.NORMAL, text="Assess recruitment potential")
        self._write("ERROR: %s" % exc)
        showerror("Recruitment assessment failed", str(exc))

    def _write(self, text):
        self.results.config(state=tk.NORMAL)
        self.results.delete("1.0", tk.END)
        self.results.insert(tk.END, text)
        self.results.config(state=tk.DISABLED)
