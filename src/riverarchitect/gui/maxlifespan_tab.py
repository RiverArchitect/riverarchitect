"""Max lifespan tab (tkinter fallback): which feature belongs where."""

import glob
import os
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askdirectory
from tkinter.messagebox import showerror, showwarning

from .base import RaModuleGui
from .. import config

__all__ = ["MaxLifespanGui"]


class MaxLifespanGui(RaModuleGui):
    """Combine per-feature lifespan maps into a best-feature assessment."""

    title = "Max Lifespan"

    def __init__(self, master=None):
        super().__init__(master)
        self.lifespan_dir = ""
        self.output_dir = ""
        self._build()

    def _build(self):
        row = 0
        tk.Label(self, text="Max lifespan", font=("TkDefaultFont", 13, "bold")) \
            .grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=self.pad_x, pady=(10, 2))
        row += 1
        tk.Label(self, text="Compares the lifespan maps of several features and reports, per "
                            "cell,\nwhich feature lasts longest. Run the lifespan tab first.",
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
        self.condition_box.bind("<<ComboboxSelected>>", lambda _e: self._use_default_dir())

        row += 1
        tk.Label(self, text="Lifespan rasters:").grid(row=row, column=0, sticky=tk.W,
                                                      padx=self.pad_x, pady=self.pad_y)
        self.b_lifespan = tk.Button(self, width=40, text="Select directory ...",
                                    command=self.select_lifespan_dir)
        self.b_lifespan.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Output directory (optional):").grid(
            row=row, column=0, sticky=tk.W, padx=self.pad_x, pady=self.pad_y)
        self.b_output = tk.Button(self, width=40, text="Select directory ...",
                                  command=self.select_output)
        self.b_output.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        self.found = tk.Label(self, text="", fg="dim gray", justify=tk.LEFT, wraplength=560)
        self.found.grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=self.pad_x)

        row += 1
        self.b_run = tk.Button(self, width=30, bg="pale green", text="Assess best features",
                               command=self.run_analysis)
        self.b_run.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x, pady=(12, 6))

        row += 1
        self.results = tk.Text(self, height=12, width=88, state=tk.DISABLED,
                               bg="gray95", relief=tk.FLAT)
        self.results.grid(row=row, column=0, columnspan=3, sticky=tk.W,
                          padx=self.pad_x, pady=self.pad_y)
        self._use_default_dir()

    def on_project_home_change(self):
        super().on_project_home_change()
        self.condition_box.config(values=self.condition_list)
        if self.condition_list:
            self.condition_box.current(0)
        self._use_default_dir()

    def _use_default_dir(self):
        name = self.condition_var.get()
        if not name:
            return
        self.lifespan_dir = os.path.join(config.dir_output("LifespanDesign"), name)
        self.b_lifespan.config(text=os.path.basename(self.lifespan_dir))
        self._scan()

    def _scan(self):
        if not self.lifespan_dir or not os.path.isdir(self.lifespan_dir):
            self.found.config(text="No lifespan rasters yet - run the lifespan tab first.")
            self.b_run.config(state=tk.DISABLED)
            return
        names = [os.path.basename(p)[3:-4]
                 for p in sorted(glob.glob(os.path.join(self.lifespan_dir, "lf_*.tif")))]
        if names:
            self.found.config(text="%d feature(s) found: %s" % (len(names), ", ".join(names)))
            self.b_run.config(state=tk.NORMAL)
        else:
            self.found.config(text="No lf_*.tif rasters in that directory.")
            self.b_run.config(state=tk.DISABLED)

    def select_lifespan_dir(self):
        path = askdirectory(title="Select the directory holding the lf_*.tif rasters",
                            initialdir=self.lifespan_dir or config.dir_output())
        if path:
            self.lifespan_dir = path
            self.b_lifespan.config(fg="forest green", text=os.path.basename(path))
            self._scan()

    def select_output(self):
        path = askdirectory(title="Select an output directory")
        if path:
            self.output_dir = path
            self.b_output.config(fg="forest green", text=os.path.basename(path))

    def run_analysis(self):
        if not self.lifespan_dir:
            showwarning("Missing input", "Select the directory holding the lifespan rasters.")
            return
        lifespan_dir, unit = self.lifespan_dir, self.unit
        output_dir = self.output_dir or None

        self.b_run.config(state=tk.DISABLED, text="Assessing ...")
        self._write("Assessing best features ...")

        def work():
            try:
                from ..maxlifespan import MaxLifespan
                result = MaxLifespan(lifespan_dir, unit=unit).run(output_dir=output_dir)
                self.after(0, lambda: self._finish(result))
            except Exception as exc:
                self.after(0, lambda: self._fail(exc))

        threading.Thread(target=work, daemon=True).start()

    def _finish(self, result):
        self.b_run.config(state=tk.NORMAL, text="Assess best features")
        unit = result["area_unit"]
        lines = ["Total mapped area: %.0f %s" % (result["total_mapped_area"], unit), "",
                 "%-12s %12s %8s  %s" % ("feature", "area (%s)" % unit, "share", "max years"),
                 "-" * 54]
        for entry in result["features"]:
            lines.append("%-12s %12.0f %7.1f%%  %s"
                         % (entry["feature"], entry["area"], entry["share"],
                            entry.get("max_lifespan", "-")))
        lines += ["",
                  "A cell counts for every feature reaching the maximum, so shares can",
                  "exceed 100%: there, the choice between those features is yours.",
                  "", "Written to: %s" % result["output_dir"]]
        self._write("\n".join(lines))

    def _fail(self, exc):
        self.b_run.config(state=tk.NORMAL, text="Assess best features")
        self._write("ERROR: %s" % exc)
        showerror("Best-feature assessment failed", str(exc))

    def _write(self, text):
        self.results.config(state=tk.NORMAL)
        self.results.delete("1.0", tk.END)
        self.results.insert(tk.END, text)
        self.results.config(state=tk.DISABLED)
