"""Project Maker tab: construction cost against the gain in habitat area."""

import os
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askdirectory
from tkinter.messagebox import showerror, showwarning

from .base import RaModuleGui

__all__ = ["ProjectMakerGui"]


class ProjectMakerGui(RaModuleGui):
    """Cost the works, compare the habitat, and report the trade-off."""

    title = "Project Maker"

    def __init__(self, master=None):
        super().__init__(master)
        self.lifespan_dir = ""
        self.output_dir = ""
        self.result = None
        self._build()

    def _build(self):
        row = 0
        tk.Label(self, text="Project Maker", font=("TkDefaultFont", 13, "bold")) \
            .grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=self.pad_x,
                  pady=(10, 2))
        row += 1
        tk.Label(self, text="Prices the works from what the earlier modules mapped, "
                            "compares the seasonal\nhabitat area before and after, and "
                            "reports the cost per unit gained.",
                 justify=tk.LEFT, fg="dim gray") \
            .grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=self.pad_x,
                  pady=(0, 10))

        row += 1
        tk.Label(self, text="Project name:").grid(row=row, column=0, sticky=tk.W,
                                                  padx=self.pad_x, pady=self.pad_y)
        self.name_var = tk.StringVar(value="project")
        tk.Entry(self, textvariable=self.name_var, width=28).grid(
            row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Max Lifespan output:").grid(row=row, column=0, sticky=tk.W,
                                                         padx=self.pad_x, pady=self.pad_y)
        self.b_lifespan = tk.Button(self, width=38, text="Select directory ...",
                                    command=self.select_lifespan)
        self.b_lifespan.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        conditions = self.condition_list or [""]
        row += 1
        tk.Label(self, text="Existing condition:").grid(row=row, column=0, sticky=tk.W,
                                                        padx=self.pad_x, pady=self.pad_y)
        self.before_var = tk.StringVar(value=conditions[0])
        self.before_menu = tk.OptionMenu(self, self.before_var, *conditions)
        self.before_menu.config(width=32)
        self.before_menu.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="With-project condition:").grid(row=row, column=0, sticky=tk.W,
                                                            padx=self.pad_x,
                                                            pady=self.pad_y)
        self.after_var = tk.StringVar(value=conditions[-1])
        self.after_menu = tk.OptionMenu(self, self.after_var, *conditions)
        self.after_menu.config(width=32)
        self.after_menu.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Species:").grid(row=row, column=0, sticky=tk.W,
                                             padx=self.pad_x, pady=self.pad_y)
        self.species_var = tk.StringVar()
        self.species_box = ttk.Combobox(self, textvariable=self.species_var, width=30,
                                        state="readonly")
        self.species_box.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)
        self.species_box.bind("<<ComboboxSelected>>", lambda _e: self._load_lifestages())

        row += 1
        tk.Label(self, text="Lifestage:").grid(row=row, column=0, sticky=tk.W,
                                               padx=self.pad_x, pady=self.pad_y)
        self.lifestage_var = tk.StringVar()
        self.lifestage_box = ttk.Combobox(self, textvariable=self.lifestage_var, width=30,
                                          state="readonly")
        self.lifestage_box.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)
        self._load_fish()

        row += 1
        tk.Label(self, text="Log length:").grid(row=row, column=0, sticky=tk.W,
                                                padx=self.pad_x, pady=self.pad_y)
        self.log_var = tk.StringVar(value="25.0")
        tk.Entry(self, textvariable=self.log_var, width=12).grid(
            row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Output directory (optional):").grid(
            row=row, column=0, sticky=tk.W, padx=self.pad_x, pady=self.pad_y)
        self.b_output = tk.Button(self, width=38, text="Select directory ...",
                                  command=self.select_output)
        self.b_output.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        self.b_run = tk.Button(self, width=24, bg="pale green", text="Assess the project",
                               command=self.run_assessment)
        self.b_run.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x, pady=(12, 6))

        row += 1
        self.result_text = tk.Text(self, height=14, width=88, state=tk.DISABLED,
                                   bg="gray95", relief=tk.FLAT)
        self.result_text.grid(row=row, column=0, columnspan=3, sticky=tk.W,
                              padx=self.pad_x, pady=self.pad_y)
        self._check_stack()

    def _load_fish(self):
        try:
            from ..sharc import FishDatabase
            self._fish = FishDatabase()
            self.species_box.config(values=self._fish.species)
            if self._fish.species:
                self.species_var.set(self._fish.species[0])
        except Exception:
            self._fish = None
        self._load_lifestages()

    def _load_lifestages(self):
        stages = self._fish.lifestages(self.species_var.get()) if self._fish else []
        self.lifestage_box.config(values=stages)
        self.lifestage_var.set(stages[0] if stages else "")

    def _check_stack(self):
        try:
            import rasterio  # noqa: F401
        except ImportError as exc:
            self.b_run.config(state=tk.DISABLED)
            self._write("The geospatial stack is not available in this Python "
                        "environment,\nso Project Maker is disabled (%s)." % exc)

    # ----------------------------------------------------------------- callbacks

    def on_project_home_change(self):
        super().on_project_home_change()
        conditions = self.condition_list or [""]
        for menu_widget, variable in ((self.before_menu, self.before_var),
                                      (self.after_menu, self.after_var)):
            menu = menu_widget["menu"]
            menu.delete(0, tk.END)
            for name in conditions:
                menu.add_command(label=name,
                                 command=lambda value=name, v=variable: v.set(value))
            variable.set(conditions[0])

    def select_lifespan(self):
        from .. import config

        start = config.dir_output("MaxLifespan")
        path = askdirectory(title="Select the Max Lifespan output directory",
                            initialdir=start if os.path.isdir(start)
                            else config.project_home())
        if path:
            self.lifespan_dir = path
            self.b_lifespan.config(fg="forest green", text=os.path.basename(path))

    def select_output(self):
        path = askdirectory(title="Select an output directory")
        if path:
            self.output_dir = path
            self.b_output.config(fg="forest green", text=os.path.basename(path))

    # ------------------------------------------------------------------ analysis

    def run_assessment(self):
        before, after = self.before_var.get(), self.after_var.get()
        species, lifestage = self.species_var.get(), self.lifestage_var.get()
        if not (before and after and species and lifestage):
            showwarning("Missing input",
                        "Select both conditions, a species and a lifestage.")
            return
        if before == after:
            showwarning("Same condition",
                        "The existing and with-project conditions are the same, so there "
                        "is no gain to measure.")
            return
        try:
            log_length = float(self.log_var.get())
        except ValueError:
            showerror("Invalid input", "The log length must be a number.")
            return

        self.b_run.config(state=tk.DISABLED, text="Assessing ...")
        self._write("Running the two habitat analyses ...")

        def work():
            try:
                from ..maxlifespan import MaxLifespan
                from ..projectmaker import ProjectMaker
                from ..sharc import SHArC

                maker = ProjectMaker(self.name_var.get() or "project", unit=self.unit,
                                     log_length=log_length)
                if self.lifespan_dir:
                    summary = MaxLifespan(self.lifespan_dir, unit=self.unit).run(
                        write_polygons=False)
                    maker.quantities_from_lifespan(summary)
                first = SHArC(before, unit=self.unit).run(species, lifestage,
                                                          write_rasters=False)
                second = SHArC(after, unit=self.unit).run(species, lifestage,
                                                          write_rasters=False)
                result = maker.run(before=first, after=second,
                                   output_dir=self.output_dir or None)
                self.after(0, lambda: self._finish(result))
            except Exception as exc:
                self.after(0, lambda: self._fail(exc))

        threading.Thread(target=work, daemon=True).start()

    def _finish(self, result):
        self.result = result
        self.b_run.config(state=tk.NORMAL, text="Assess the project")
        costs = result["costs"]
        lines = ["%-38s %16s" % ("GROUP", "COST (US$)")]
        for group, amount in costs["groups"].items():
            if amount:
                lines.append("%-38s %16.2f" % (group, amount))
        lines.append("%-38s %16.2f" % ("CONSTRUCTION WORKS", costs["construction"]))
        lines.append("")
        for entry in costs["applied"]:
            lines.append("%-38s %16.2f" % ("%s (%.1f%%)" % (entry["label"],
                                                            entry["fraction"] * 100),
                                            entry["amount"]))
        lines.append("%-38s %16.2f" % ("TOTAL", costs["total"]))

        if "habitat" in result:
            habitat = result["habitat"]
            unit = result["area_unit"]
            lines += ["",
                      "%-38s %16.0f %s" % ("SHArea, existing", habitat["before"], unit),
                      "%-38s %16.0f %s" % ("SHArea, with project", habitat["after"], unit),
                      "%-38s %16.0f %s (%+.1f%%)" % ("net gain", habitat["gain"], unit,
                                                      habitat["relative"] * 100)]
            if result.get("cost_per_area"):
                lines.append("%-38s %16.2f US$" % ("cost per %s gained" % unit,
                                                    result["cost_per_area"]))
        if "report" in result:
            lines += ["", "Bill of quantities: %s" % result["report"]]
        self._write("\n".join(lines))

    def _fail(self, exc):
        self.b_run.config(state=tk.NORMAL, text="Assess the project")
        self._write("ERROR: %s" % exc)
        showerror("Project assessment failed", str(exc))

    def _write(self, text):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, text)
        self.result_text.config(state=tk.DISABLED)
