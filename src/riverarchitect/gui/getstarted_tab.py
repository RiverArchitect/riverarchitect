"""Get started tab (tkinter fallback): prepare a condition's derived rasters."""

import os
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askdirectory, askopenfilename
from tkinter.messagebox import showerror, showwarning

from .base import RaModuleGui
from .. import config

__all__ = ["GetStartedGui"]

#: See the Qt tab: mirrored so the tab still builds without the geospatial stack.
FALLBACK_PRODUCTS = (("detrended DEM", "detrended"),)


def _products():
    try:
        from .. import preprocessing as pre
        return pre.PRODUCTS, pre.PRODUCT_NOTES
    except ImportError:
        return FALLBACK_PRODUCTS, {}


class GetStartedGui(RaModuleGui):
    """Build the derived rasters the analysis modules read."""

    title = "Get Started"

    def __init__(self, master=None):
        super().__init__(master)
        self.output_dir = ""
        self.flow_series = ""
        self._discharges = []
        self._build()

    def _build(self):
        row = 0
        tk.Label(self, text="Get started", font=("TkDefaultFont", 13, "bold")) \
            .grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=self.pad_x, pady=(10, 2))
        row += 1
        tk.Label(self, text="Prepares a condition: the terrain products that lifespan "
                            "mapping, habitat\nsuitability and recruitment all depend on.",
                 justify=tk.LEFT, fg="dim gray") \
            .grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=self.pad_x, pady=(0, 8))

        row += 1
        tk.Label(self, text="Condition:").grid(row=row, column=0, sticky=tk.W,
                                               padx=self.pad_x, pady=self.pad_y)
        self.condition_var = tk.StringVar()
        self.condition_box = ttk.Combobox(self, textvariable=self.condition_var, width=32,
                                          values=self.condition_list, state="readonly")
        if self.condition_list:
            self.condition_box.current(0)
        self.condition_box.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)
        self.condition_box.bind("<<ComboboxSelected>>", lambda _e: self._scan_condition())

        row += 1
        tk.Label(self, text="Build:").grid(row=row, column=0, sticky=tk.W,
                                           padx=self.pad_x, pady=self.pad_y)
        products, self._notes = _products()
        self._products = products
        self.product_var = tk.StringVar(value=products[0][0])
        ttk.Combobox(self, textvariable=self.product_var, width=42, state="readonly",
                     values=[label for label, _key in products]) \
            .grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)
        self.product_var.trace_add("write", lambda *_a: self._describe())

        row += 1
        tk.Label(self, text="Reference discharge:").grid(row=row, column=0, sticky=tk.W,
                                                         padx=self.pad_x, pady=self.pad_y)
        self.discharge_var = tk.StringVar()
        self.discharge_box = ttk.Combobox(self, textvariable=self.discharge_var, width=14,
                                          state="readonly")
        self.discharge_box.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Interpolation:").grid(row=row, column=0, sticky=tk.W,
                                                   padx=self.pad_x, pady=self.pad_y)
        self.method_var = tk.StringVar(value="nearest")
        ttk.Combobox(self, textvariable=self.method_var, width=14, state="readonly",
                     values=["nearest", "idw", "kriging"]) \
            .grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Daily flow record:").grid(
            row=row, column=0, sticky=tk.W, padx=self.pad_x, pady=self.pad_y)
        self.b_series = tk.Button(self, width=38, text="Select flow record ...",
                                  command=self.select_series)
        self.b_series.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Output directory (optional):").grid(
            row=row, column=0, sticky=tk.W, padx=self.pad_x, pady=self.pad_y)
        self.b_output = tk.Button(self, width=38, text="Select directory ...",
                                  command=self.select_output)
        self.b_output.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        self.info = tk.Label(self, text="", fg="dim gray", justify=tk.LEFT, wraplength=580)
        self.info.grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=self.pad_x)

        row += 1
        self.b_run = tk.Button(self, width=30, bg="pale green", text="Build",
                               command=self.run_analysis)
        self.b_run.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x, pady=(12, 6))

        row += 1
        self.results = tk.Text(self, height=10, width=86, state=tk.DISABLED,
                               bg="gray95", relief=tk.FLAT)
        self.results.grid(row=row, column=0, columnspan=3, sticky=tk.W,
                          padx=self.pad_x, pady=self.pad_y)

        self._check_dependencies()
        self._scan_condition()
        self._describe()

    def _key(self):
        for label, key in self._products:
            if label == self.product_var.get():
                return key
        return self._products[0][1]

    def _describe(self):
        self.info.config(text=self._notes.get(self._key(), ""))

    def _check_dependencies(self):
        try:
            import rasterio  # noqa: F401
        except ImportError as exc:
            self.b_run.config(state=tk.DISABLED)
            self._write("The geospatial stack is not available here (%s).\n"
                        "Use the `ra-env` environment for analysis." % exc)

    def on_project_home_change(self):
        super().on_project_home_change()
        self.condition_box.config(values=self.condition_list)
        if self.condition_list:
            self.condition_box.current(0)
        self._scan_condition()

    def _scan_condition(self):
        name = self.condition_var.get()
        self._discharges = []
        if not name:
            return
        try:
            from ..condition import Condition
            condition = Condition(name)
            self._discharges = sorted(
                q for q in (condition.discharge_of(n)
                            for n in condition.all_depth_rasters()) if q is not None)
        except Exception as exc:
            self.info.config(text=str(exc))
            return
        from ..condition import discharge_label
        labels = [discharge_label(q) for q in self._discharges]
        self.discharge_box.config(values=labels)
        if labels:
            self.discharge_box.current(0)

    def select_series(self):
        path = askopenfilename(title="Select a daily flow record",
                               filetypes=[("Flow records", "*.csv *.xlsx *.xls"),
                                          ("All files", "*.*")])
        if path:
            self.flow_series = path
            self.b_series.config(fg="forest green", text=os.path.basename(path))

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
        key = self._key()
        if key in ("detrended", "water", "mu") and not self.discharge_var.get():
            showwarning("No discharge", "This product needs a reference discharge.")
            return
        if key == "flows" and not self.flow_series:
            showwarning("No flow record",
                        "Analyzing flows needs a daily flow record: a CSV or workbook of "
                        "dates and mean daily discharge.")
            return

        discharge = float(self.discharge_var.get()) if self.discharge_var.get() else None
        method = self.method_var.get()
        unit = self.unit
        output_dir = self.output_dir or None
        flow_series = self.flow_series or None

        self.b_run.config(state=tk.DISABLED, text="Building ...")
        self._write("Building %s ..." % self.product_var.get())

        def work():
            try:
                from .. import preprocessing as pre
                lines = pre.build_product(name, key, discharge, method, unit, output_dir,
                                          flow_series=flow_series)
                self.after(0, lambda: self._finish(lines))
            except Exception as exc:
                self.after(0, lambda: self._fail(exc))

        threading.Thread(target=work, daemon=True).start()

    def _finish(self, lines):
        self.b_run.config(state=tk.NORMAL, text="Build")
        self._write("Finished.\n\n" + "\n".join(lines))

    def _fail(self, exc):
        self.b_run.config(state=tk.NORMAL, text="Build")
        self._write("ERROR: %s" % exc)
        showerror("Could not build the product", str(exc))

    def _write(self, text):
        self.results.config(state=tk.NORMAL)
        self.results.delete("1.0", tk.END)
        self.results.insert(tk.END, text)
        self.results.config(state=tk.DISABLED)
