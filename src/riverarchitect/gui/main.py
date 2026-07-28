"""Main River Architect window: a notebook of module tabs.

Carries over the structure of the original ``parent_gui.RaGui``, with one deliberate
difference: selecting a tab no longer calls :func:`os.chdir`. The original changed the
process working directory per tab, which coupled unrelated modules together through global
state and made behaviour depend on click order. Paths are now explicit.
"""

import logging
import sys
import tkinter as tk
from tkinter import ttk

from .. import __version__, config
from .volume_tab import VolumeGui
from .mapping_tab import MappingGui

__all__ = ["RiverArchitectGui", "main"]


class RiverArchitectGui(tk.Frame):
    """Top-level window holding one tab per module."""

    def __init__(self, master=None):
        super().__init__(master)
        self.logger = logging.getLogger("riverarchitect")
        self.pack(expand=True, fill=tk.BOTH)

        top = self.winfo_toplevel()
        top.title("River Architect %s" % __version__)
        top.geometry("760x520")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill=tk.BOTH)

        self.tabs = {}
        for label, factory in (("Morphology (Volumes)", VolumeGui),
                               ("Mapping", MappingGui)):
            try:
                tab = factory(self.notebook)
            except Exception as exc:  # a broken module must not take the whole GUI down
                self.logger.error("Could not load the %s tab: %s", label, exc)
                tab = self._placeholder(label, exc)
            self.tabs[label] = tab
            self.notebook.add(tab, text=label)

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        self.on_tab_changed(None)

    def _placeholder(self, label, exc):
        frame = tk.Frame(self.notebook)
        tk.Label(frame, text="The %s tab could not be loaded." % label,
                 font=("TkDefaultFont", 11, "bold")).pack(padx=20, pady=(30, 8))
        tk.Label(frame, text=str(exc), fg="firebrick", wraplength=600,
                 justify=tk.LEFT).pack(padx=20)
        return frame

    def on_tab_changed(self, _event):
        """Give the selected tab the window title and rebuild its menus."""
        try:
            current = self.notebook.nametowidget(self.notebook.select())
        except (tk.TclError, KeyError):
            return
        if hasattr(current, "set_geometry"):
            current.set_geometry(current.window_width, current.window_height, current.title)
        if hasattr(current, "make_standard_menus"):
            current.make_standard_menus()
            current.complete_menus()


def main(argv=None):
    """Console-script entry point. Starts the GUI."""
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s  %(levelname)-7s %(message)s",
                        datefmt="%H:%M:%S")

    argv = sys.argv[1:] if argv is None else argv
    if argv:
        # a single positional argument sets the project directory
        config.set_project_home(argv[0])

    logging.getLogger("riverarchitect").info("Project directory: %s", config.project_home())

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print("ERROR: no display available for the graphical interface (%s).\n"
              "River Architect's modules can be used directly from Python:\n"
              "    from riverarchitect.volume_assessment import VolumeAssessment" % exc)
        return 1

    RiverArchitectGui(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
