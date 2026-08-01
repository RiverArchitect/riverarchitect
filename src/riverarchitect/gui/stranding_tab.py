"""Ecohydraulics tab (tkinter fallback): fish stranding risk."""

import os
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askdirectory
from tkinter.messagebox import showerror, showwarning

from .base import RaModuleGui

__all__ = ["StrandingGui"]


class StrandingGui(RaModuleGui):
    """Find wetted areas that disconnect from the main channel as discharge falls."""

    title = "Stranding Risk"

    def __init__(self, master=None):
        super().__init__(master)
        self.output_dir = ""
        self._discharges = []
        self._build()

    def _build(self):
        row = 0
        tk.Label(self, text="Ecohydraulics: fish stranding",
                 font=("TkDefaultFont", 13, "bold")) \
            .grid(row=row, column=0, columnspan=4, sticky=tk.W, padx=self.pad_x, pady=(10, 2))
        row += 1
        tk.Label(self, text="As a hydrograph recedes the wetted area breaks apart. Pools that "
                            "lose their\nconnection to the main channel trap fish.",
                 justify=tk.LEFT, fg="dim gray") \
            .grid(row=row, column=0, columnspan=4, sticky=tk.W, padx=self.pad_x, pady=(0, 8))

        row += 1
        tk.Label(self, text="Condition:").grid(row=row, column=0, sticky=tk.W,
                                               padx=self.pad_x, pady=self.pad_y)
        self.condition_var = tk.StringVar()
        self.condition_box = ttk.Combobox(self, textvariable=self.condition_var, width=28,
                                          values=self.condition_list, state="readonly")
        if self.condition_list:
            self.condition_box.current(0)
        self.condition_box.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)
        self.condition_box.bind("<<ComboboxSelected>>", lambda _e: self._scan_discharges())

        row += 1
        tk.Label(self, text="Species and lifestage:").grid(row=row, column=0, sticky=tk.W,
                                                           padx=self.pad_x, pady=self.pad_y)
        self.fish_var = tk.StringVar()
        self._fish = {}
        try:
            from ..stranding import TRAVEL_THRESHOLDS
            for (species, lifestage), values in TRAVEL_THRESHOLDS.items():
                self._fish["%s, %s" % (species, lifestage)] = values["h_min"]
        except ImportError:
            pass
        options = list(self._fish) + ["Custom"]
        self.fish_box = ttk.Combobox(self, textvariable=self.fish_var, width=28,
                                     values=options, state="readonly")
        self.fish_box.current(0)
        self.fish_box.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)
        self.fish_box.bind("<<ComboboxSelected>>", lambda _e: self._apply_fish())

        row += 1
        tk.Label(self, text="Minimum swimming depth:").grid(row=row, column=0, sticky=tk.W,
                                                            padx=self.pad_x, pady=self.pad_y)
        self.h_min_var = tk.StringVar(value="0.2")
        tk.Entry(self, textvariable=self.h_min_var, width=10).grid(
            row=row, column=1, sticky=tk.W, padx=self.pad_x)
        self.h_unit = tk.Label(self, text=self.labels["length"], fg="dim gray")
        self.h_unit.grid(row=row, column=1, sticky=tk.W, padx=(90, 0))

        row += 1
        tk.Label(self, text="Discharge range:").grid(row=row, column=0, sticky=tk.W,
                                                     padx=self.pad_x, pady=self.pad_y)
        frame = tk.Frame(self)
        frame.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)
        tk.Label(frame, text="from").pack(side=tk.LEFT)
        self.q_high_var = tk.StringVar()
        self.q_high_box = ttk.Combobox(frame, textvariable=self.q_high_var, width=9,
                                       state="readonly")
        self.q_high_box.pack(side=tk.LEFT, padx=3)
        tk.Label(frame, text="down to").pack(side=tk.LEFT)
        self.q_low_var = tk.StringVar()
        self.q_low_box = ttk.Combobox(frame, textvariable=self.q_low_var, width=9,
                                      state="readonly")
        self.q_low_box.pack(side=tk.LEFT, padx=3)
        self.q_unit = tk.Label(frame, text=self.labels["q"], fg="dim gray")
        self.q_unit.pack(side=tk.LEFT)

        row += 1
        tk.Label(self, text="Output directory (optional):").grid(
            row=row, column=0, sticky=tk.W, padx=self.pad_x, pady=self.pad_y)
        self.b_output = tk.Button(self, width=38, text="Select directory ...",
                                  command=self.select_output)
        self.b_output.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        self.info = tk.Label(self, text="", fg="dim gray", justify=tk.LEFT, wraplength=560)
        self.info.grid(row=row, column=0, columnspan=4, sticky=tk.W, padx=self.pad_x)

        row += 1
        self.b_run = tk.Button(self, width=30, bg="pale green", text="Assess stranding risk",
                               command=self.run_analysis)
        self.b_run.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x, pady=(12, 6))

        row += 1
        self.results = tk.Text(self, height=10, width=88, state=tk.DISABLED,
                               bg="gray95", relief=tk.FLAT)
        self.results.grid(row=row, column=0, columnspan=4, sticky=tk.W,
                          padx=self.pad_x, pady=self.pad_y)

        self._check_dependencies()
        self._scan_discharges()

    # ------------------------------------------------------------------ callbacks

    def _check_dependencies(self):
        try:
            import rasterio  # noqa: F401
        except ImportError as exc:
            self.b_run.config(state=tk.DISABLED)
            self._write("The geospatial stack is not available in this Python environment,\n"
                        "so the stranding analysis is disabled (%s).\n\n"
                        "Use the `ra-env` environment for analysis." % exc)

    def on_unit_change(self):
        self.h_unit.config(text=self.labels["length"])
        self.q_unit.config(text=self.labels["q"])

    def on_project_home_change(self):
        super().on_project_home_change()
        self.condition_box.config(values=self.condition_list)
        if self.condition_list:
            self.condition_box.current(0)
        self._scan_discharges()

    def _apply_fish(self):
        h_min = self._fish.get(self.fish_var.get())
        if h_min is not None:
            self.h_min_var.set(str(h_min))

    def _scan_discharges(self):
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
        self.q_low_box.config(values=labels)
        self.q_high_box.config(values=labels)
        if labels:
            self.q_low_box.current(0)
            self.q_high_box.current(min(len(labels) - 1, 12))
            self.info.config(text="%d depth raster(s) available, %s to %s %s."
                                  % (len(labels), labels[0], labels[-1], self.labels["q"]))
        else:
            self.info.config(text="This condition has no depth rasters.")
            self.b_run.config(state=tk.DISABLED)

    def select_output(self):
        path = askdirectory(title="Select an output directory")
        if path:
            self.output_dir = path
            self.b_output.config(fg="forest green", text=os.path.basename(path))

    # -------------------------------------------------------------------- analysis

    def run_analysis(self):
        name = self.condition_var.get()
        if not name or not self._discharges:
            showwarning("No condition", "Select a condition with depth rasters.")
            return
        try:
            h_min = float(self.h_min_var.get())
            low = float(self.q_low_var.get())
            high = float(self.q_high_var.get())
        except ValueError:
            showerror("Invalid input", "The depth and discharges must be numbers.")
            return
        if high <= low:
            showwarning("Discharge range",
                        "The starting discharge must be higher than the final one: a "
                        "stranding analysis walks a falling hydrograph.")
            return

        chosen = sorted((q for q in self._discharges if low <= q <= high), reverse=True)
        unit = self.unit
        output_dir = self.output_dir or None

        self.b_run.config(state=tk.DISABLED, text="Assessing ...")
        self._write("Walking %d discharge(s) ..." % len(chosen))

        def work():
            try:
                from ..stranding import StrandingRisk
                analysis = StrandingRisk(name, discharges=chosen, h_min=h_min, unit=unit)
                result = analysis.run(output_dir=output_dir)
                self.after(0, lambda: self._finish(result))
            except Exception as exc:
                self.after(0, lambda: self._fail(exc))

        threading.Thread(target=work, daemon=True).start()

    def _finish(self, result):
        self.b_run.config(state=tk.NORMAL, text="Assess stranding risk")
        area = result["area_unit"]
        discharge = result["discharge_unit"]
        lines = ["%10s %7s %13s %14s %7s" % ("Q (%s)" % discharge, "pools",
                                             "wetted (%s)" % area, "stranded (%s)" % area,
                                             "%"),
                 "-" * 58]
        from ..condition import discharge_label
        for row in result["per_discharge"]:
            lines.append("%10s %7d %13.0f %14.0f %6.2f"
                         % (discharge_label(row["discharge"]), row["pools"],
                            row["wetted_area"], row["stranded_area"],
                            row["percent_stranded"]))
        lines += ["",
                  "Worst discharge  : %g %s, %.0f %s stranded"
                  % (result["worst_discharge"], discharge,
                     result["worst_stranded_area"], area),
                  "Ever disconnected: %.0f %s" % (result["total_disconnected_area"], area),
                  ""]
        if result.get("velocity_limited", False):
            lines += ["Escape routes account for the %.1f %s swimming speed."
                      % (result["u_max"], self.labels["u"])]
        else:
            lines += ["Depth only: the swimming-speed criterion needs the flow direction",
                      "(ux<Q>.tif and uy<Q>.tif beside the condition)."]
        if result.get("output_dir"):
            lines += ["", "Written to: %s" % result["output_dir"]]
        self._write("\n".join(lines))

    def _fail(self, exc):
        self.b_run.config(state=tk.NORMAL, text="Assess stranding risk")
        self._write("ERROR: %s" % exc)
        showerror("Stranding assessment failed", str(exc))

    def _write(self, text):
        self.results.config(state=tk.NORMAL)
        self.results.delete("1.0", tk.END)
        self.results.insert(tk.END, text)
        self.results.config(state=tk.DISABLED)
