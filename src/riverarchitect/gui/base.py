"""Shared tkinter base class for River Architect module tabs.

Carries over the structure of the original ``child_gui.RaModuleGui``: every module tab is a
``tk.Frame`` subclass that owns its own menus, a unit-system toggle and a condition picker.
What changed is that the base class no longer reaches into arcpy or into workbook templates
to build itself, so a tab can be constructed and tested without any geoprocessing stack.
"""

import logging
import os
import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import askokcancel, showinfo

from .. import config

__all__ = ["RaModuleGui"]


class RaModuleGui(tk.Frame):
    """Base class for a module tab.

    Subclasses should set :attr:`title`, :attr:`window_width` and :attr:`window_height` in
    their ``__init__`` and override :meth:`complete_menus` to add module-specific menus.

    Args:
        master: parent widget, normally the notebook tab container.
    """

    #: Tab title, shown in the window title bar when the tab is selected.
    title = "River Architect"
    #: Preferred window width in pixels.
    window_width = 700
    #: Preferred window height in pixels.
    window_height = 500

    def __init__(self, master=None):
        super().__init__(master)
        self.logger = logging.getLogger("riverarchitect")

        self.condition = ""
        self.condition_list = []
        self.errors = False
        self.unit = "us"
        self.labels = config.unit_labels(self.unit)

        self.pad_x = 5
        self.pad_y = 5

        self.pack(expand=True, fill=tk.BOTH)
        self.menu_bar = None
        self.unit_menu = None
        self.refresh_conditions()

    # ------------------------------------------------------------------ geometry

    def set_geometry(self, width=None, height=None, title=None):
        """Centre the window and give it a title."""
        width = width or self.window_width
        height = height or self.window_height
        title = title or self.title
        top = self.winfo_toplevel()
        x = (top.winfo_screenwidth() - width) / 2
        y = (top.winfo_screenheight() - height) / 2
        top.geometry("%dx%d+%d+%d" % (width, height, x, y))
        top.title("River Architect - %s" % title)

    # --------------------------------------------------------------------- menus

    def make_standard_menus(self):
        """Build the menus every tab shares: Units, Tools, Help, Close."""
        top = self.winfo_toplevel()
        self.menu_bar = tk.Menu(self)
        top.config(menu=self.menu_bar)

        self.unit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Units", menu=self.unit_menu)
        self._render_unit_menu()

        tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Set project directory ...",
                               command=self.choose_project_home)
        tools_menu.add_command(label="Reconcile NoData in a condition ...",
                               command=self.run_reconcile_nodata)

        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.open_documentation)
        help_menu.add_command(label="About", command=self.show_about)

        close_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Close", menu=close_menu)
        close_menu.add_command(label="Quit program", command=self.quit_program)

    def complete_menus(self):
        """Hook for subclasses to append module-specific menus. Does nothing by default."""

    def _render_unit_menu(self):
        self.unit_menu.delete(0, tk.END)
        us_mark = "[current] " if self.unit == "us" else "[        ] "
        si_mark = "[current] " if self.unit == "si" else "[        ] "
        self.unit_menu.add_command(label=us_mark + "U.S. customary",
                                   command=lambda: self.set_unit("us"))
        self.unit_menu.add_command(label=si_mark + "SI (metric)",
                                   command=lambda: self.set_unit("si"))

    def set_unit(self, unit):
        """Switch the unit system and notify the subclass through :meth:`on_unit_change`."""
        if unit not in config.UNITS:
            return
        self.unit = unit
        self.labels = config.unit_labels(unit)
        if self.unit_menu is not None:
            self._render_unit_menu()
        self.on_unit_change()

    def on_unit_change(self):
        """Hook called after the unit system changed. Does nothing by default."""

    # ---------------------------------------------------------------- conditions

    def refresh_conditions(self, listbox=None, scrollbar=None):
        """Reload the list of available conditions from the project directory."""
        directory = config.dir_conditions()
        try:
            self.condition_list = sorted(
                name for name in os.listdir(directory)
                if os.path.isdir(os.path.join(directory, name)) and not name.startswith("."))
        except OSError:
            self.condition_list = []

        if listbox is not None:
            listbox.delete(0, tk.END)
            for entry in self.condition_list:
                listbox.insert(tk.END, entry)
            if scrollbar is not None:
                scrollbar.config(command=listbox.yview)
        return self.condition_list

    def choose_project_home(self):
        """Ask for the project directory and rebuild the condition list."""
        from tkinter.filedialog import askdirectory
        directory = askdirectory(title="Select the River Architect project directory")
        if not directory:
            return
        config.set_project_home(directory)
        self.refresh_conditions()
        showinfo("Project directory",
                 "Project directory set to:\n%s\n\n%d condition(s) found."
                 % (directory, len(self.condition_list)))

    def run_reconcile_nodata(self):
        """Run the NoData reconciliation tool on a chosen condition folder."""
        from tkinter.filedialog import askdirectory
        from ..tools import reconcile_nodata

        directory = askdirectory(title="Select a condition folder to reconcile",
                                 initialdir=config.dir_conditions())
        if not directory:
            return
        if not askokcancel("Reconcile NoData",
                           "Rewrite every raster in\n%s\nto NoData = %s?\n\n"
                           "The NoData mask is preserved; only the sentinel changes."
                           % (directory, config.NODATA)):
            return
        changed = 0
        for path in sorted(__import__("glob").glob(os.path.join(directory, "*.tif"))):
            try:
                if reconcile_nodata.reconcile(path):
                    changed += 1
            except Exception as exc:  # pragma: no cover - surfaced to the user
                self.logger.error("Could not reconcile %s: %s", path, exc)
        showinfo("Reconcile NoData", "%d raster(s) updated." % changed)

    # ----------------------------------------------------------------- utilities

    @staticmethod
    def open_documentation():
        import webbrowser
        webbrowser.open("https://riverarchitect.readthedocs.io/")

    def show_about(self):
        from .. import __version__
        showinfo("About River Architect",
                 "River Architect %s\n\n"
                 "Open-source analysis and design of fluvial ecosystems.\n"
                 "https://riverarchitect.readthedocs.io/\n\n"
                 "Project directory:\n%s" % (__version__, config.project_home()))

    def quit_program(self):
        if askokcancel("Close", "Do you really want to quit?"):
            self.winfo_toplevel().destroy()

    @staticmethod
    def set_background(frame, colour):
        frame.config(bg=colour)
        for widget in frame.winfo_children():
            try:
                widget.configure(bg=colour)
            except tk.TclError:
                pass
