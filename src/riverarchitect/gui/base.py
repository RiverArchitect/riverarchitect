"""Shared tkinter base class for River Architect module tabs.

This is the fallback interface, used when no Qt binding is installed; see
:mod:`riverarchitect.gui` for how the two front ends are chosen and
:mod:`riverarchitect.gui.qt` for the default one.

Carries over the structure of the original ``child_gui.RaModuleGui``: every module tab is a
``tk.Frame`` subclass with a unit-system toggle and a condition list. What changed is that
the base class no longer reaches into arcpy or into workbook templates to build itself, so a
tab can be constructed and tested without any geoprocessing stack - and that the *window*
owns the menu bar. The original rebuilt the whole menu bar, and resized and re-centred the
window, on every tab change; menus are now built once by
:class:`riverarchitect.gui.main.RiverArchitectGui`.
"""

import logging
import os
import tkinter as tk

from .. import config

__all__ = ["RaModuleGui"]


class RaModuleGui(tk.Frame):
    """Base class for a module tab.

    Subclasses set :attr:`title` and build their widgets in ``__init__``.

    Args:
        master: parent widget, normally the notebook tab container.
    """

    #: Tab title.
    title = "River Architect"

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

        # No self.pack() here: the notebook is the geometry manager for its tabs, and
        # calling pack() on a widget the notebook manages mixes two managers on one widget.
        self.refresh_conditions()

    # --------------------------------------------------------------------- units

    def set_unit(self, unit):
        """Switch the unit system and notify the subclass through :meth:`on_unit_change`."""
        if unit not in config.UNITS or unit == self.unit:
            return
        self.unit = unit
        self.labels = config.unit_labels(unit)
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

    def on_project_home_change(self):
        """Hook called after the project directory changed. Refreshes the condition list."""
        self.refresh_conditions()

    # ----------------------------------------------------------------- utilities

    @staticmethod
    def set_background(frame, colour):
        frame.config(bg=colour)
        for widget in frame.winfo_children():
            try:
                widget.configure(bg=colour)
            except tk.TclError:
                pass
