"""River Builder tab: synthetic river valleys from design parameters."""

import os
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askdirectory, askopenfilename
from tkinter.messagebox import showerror

from .base import RaModuleGui

__all__ = ["RiverBuilderGui"]

#: Field key, label and default, in the order they are laid out.
FIELDS = (
    ("length", "Reach length", 350.0),
    ("bankfull_width", "Bankfull width", 20.0),
    ("bankfull_depth", "Bankfull depth (0 = from D50)", 7.0),
    ("valley_slope", "Valley slope", 0.005),
    ("d50", "Median grain size (D50)", 0.0965),
    ("floodplain_width", "Floodplain width", 30.0),
    ("terrace_width", "Terrace width", 20.0),
    ("meander_amplitude", "Meander amplitude", 15.0),
)


class RiverBuilderGui(RaModuleGui):
    """Generate a synthetic river valley and write it as a DEM."""

    title = "River Builder"

    def __init__(self, master=None):
        super().__init__(master)
        self.input_file = ""
        self.output_dir = ""
        self.result = None
        self._build()

    def _build(self):
        row = 0
        tk.Label(self, text="River Builder", font=("TkDefaultFont", 13, "bold")) \
            .grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=self.pad_x,
                  pady=(10, 2))
        row += 1
        tk.Label(self, text="Builds a river valley that does not exist yet - meandering "
                            "centreline, varying\nwidth, thalweg, floodplain and terrace - "
                            "and writes it as a DEM.",
                 justify=tk.LEFT, fg="dim gray") \
            .grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=self.pad_x,
                  pady=(0, 10))

        row += 1
        tk.Label(self, text="Name:").grid(row=row, column=0, sticky=tk.W,
                                          padx=self.pad_x, pady=self.pad_y)
        self.name_var = tk.StringVar(value="RiverBuilder")
        tk.Entry(self, textvariable=self.name_var, width=28).grid(
            row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Parameter file (optional):").grid(
            row=row, column=0, sticky=tk.W, padx=self.pad_x, pady=self.pad_y)
        self.b_input = tk.Button(self, width=38, text="Select parameter file ...",
                                 command=self.select_input)
        self.b_input.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        self.vars = {}
        for key, label, default in FIELDS:
            row += 1
            tk.Label(self, text=label + ":").grid(row=row, column=0, sticky=tk.W,
                                                  padx=self.pad_x, pady=2)
            self.vars[key] = tk.StringVar(value=str(default))
            tk.Entry(self, textvariable=self.vars[key], width=12).grid(
                row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        tk.Label(self, text="Cross-section:").grid(row=row, column=0, sticky=tk.W,
                                                   padx=self.pad_x, pady=2)
        self.shape_var = tk.StringVar(value="SU")
        ttk.Combobox(self, textvariable=self.shape_var, width=10, state="readonly",
                     values=["SU", "AU", "TZ"]).grid(row=row, column=1, sticky=tk.W,
                                                      padx=self.pad_x)

        row += 1
        tk.Label(self, text="DEM cell size:").grid(row=row, column=0, sticky=tk.W,
                                                   padx=self.pad_x, pady=2)
        self.cell_var = tk.StringVar(value="1.0")
        tk.Entry(self, textvariable=self.cell_var, width=12).grid(
            row=row, column=1, sticky=tk.W, padx=self.pad_x)
        self.l_cell_unit = tk.Label(self, text=self.labels["length"], fg="dim gray")
        self.l_cell_unit.grid(row=row, column=1, sticky=tk.W, padx=(100, 0))

        row += 1
        tk.Label(self, text="Output directory (optional):").grid(
            row=row, column=0, sticky=tk.W, padx=self.pad_x, pady=self.pad_y)
        self.b_output = tk.Button(self, width=38, text="Select directory ...",
                                  command=self.select_output)
        self.b_output.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x)

        row += 1
        self.b_run = tk.Button(self, width=24, bg="pale green", text="Build the valley",
                               command=self.run_builder)
        self.b_run.grid(row=row, column=1, sticky=tk.W, padx=self.pad_x, pady=(12, 6))

        row += 1
        self.result_text = tk.Text(self, height=12, width=84, state=tk.DISABLED,
                                   bg="gray95", relief=tk.FLAT)
        self.result_text.grid(row=row, column=0, columnspan=3, sticky=tk.W,
                              padx=self.pad_x, pady=self.pad_y)
        self._check_stack()

    def _check_stack(self):
        try:
            import rasterio  # noqa: F401
            import scipy      # noqa: F401
        except ImportError as exc:
            self.b_run.config(state=tk.DISABLED)
            self._write("The geospatial stack is not available in this Python "
                        "environment,\nso River Builder is disabled (%s).\n\n"
                        "This tab needs numpy, scipy and rasterio." % exc)

    # ----------------------------------------------------------------- callbacks

    def on_unit_change(self):
        self.l_cell_unit.config(text=self.labels["length"])

    def select_input(self):
        path = askopenfilename(title="Select a RiverBuilder parameter file",
                               filetypes=[("Parameter files", "*.txt"),
                                          ("All files", "*.*")])
        if path:
            self.input_file = path
            self.b_input.config(fg="forest green", text=os.path.basename(path))

    def select_output(self):
        path = askdirectory(title="Select an output directory")
        if path:
            self.output_dir = path
            self.b_output.config(fg="forest green", text=os.path.basename(path))

    # ------------------------------------------------------------------ analysis

    def _parameters(self):
        from ..riverbuilder import RiverBuilderInput, UserFunction

        if self.input_file:
            entry = RiverBuilderInput.read(self.input_file)
            entry.name = self.name_var.get() or entry.name
            return entry

        values = {key: float(self.vars[key].get()) for key, _l, _d in FIELDS}
        amplitude = values.pop("meander_amplitude")
        entry = RiverBuilderInput(name=self.name_var.get() or "RiverBuilder", **values)
        entry.xs_shape = self.shape_var.get()
        entry.bankfull_width_min = max(entry.bankfull_width / 2.0, 1.0)
        if amplitude > 0:
            entry.meander = [UserFunction("SIN", [amplitude, 2, 0])]
        return entry

    def run_builder(self):
        try:
            parameters = self._parameters()
            cell_size = float(self.cell_var.get())
        except Exception as exc:
            showerror("Invalid parameters", str(exc))
            return

        self.b_run.config(state=tk.DISABLED, text="Building ...")
        self._write("Building ...")

        def work():
            try:
                from ..riverbuilder import RiverBuilder
                result = RiverBuilder(parameters, unit=self.unit).run(
                    output_dir=self.output_dir or None, cell_size=cell_size)
                self.after(0, lambda: self._finish(result))
            except Exception as exc:
                self.after(0, lambda: self._fail(exc))

        threading.Thread(target=work, daemon=True).start()

    def _finish(self, result):
        self.result = result
        self.b_run.config(state=tk.NORMAL, text="Build the valley")
        length = self.labels["length"]
        low, high = result["elevation_range"]
        lines = [
            "Name              : %s" % result["name"],
            "Cross-section     : %s" % result["cross_section"],
            "Stations          : %d over %.1f %s" % (result["stations"],
                                                     result["length"], length),
            "Sinuosity         : %.3f" % result["sinuosity"],
            "Channel slope     : %.5f" % result["channel_slope"],
            "Bankfull depth    : %.2f %s" % (result["bankfull_depth"], length),
            "Mean width        : %.2f %s" % (result["bankfull_width_mean"], length),
            "Elevation range   : %.2f to %.2f %s" % (low, high, length),
            "Mapped area       : %.0f %s" % (result["area"], result["area_unit"]),
            "",
            "Written to: %s" % result["output_dir"],
        ]
        self._write("\n".join(lines))

    def _fail(self, exc):
        self.b_run.config(state=tk.NORMAL, text="Build the valley")
        self._write("ERROR: %s" % exc)
        showerror("River Builder failed", str(exc))

    def _write(self, text):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, text)
        self.result_text.config(state=tk.DISABLED)
