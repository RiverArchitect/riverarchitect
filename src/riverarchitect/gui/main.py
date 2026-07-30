"""Main tkinter window: a notebook of module tabs.

The fallback interface, used when no Qt binding is installed. See :mod:`riverarchitect.gui`
for the backend choice and :mod:`riverarchitect.gui.qt` for the default front end.

Carries over the structure of the original ``parent_gui.RaGui``, with three deliberate
differences:

* selecting a tab no longer calls :func:`os.chdir`. The original changed the process working
  directory per tab, which coupled unrelated modules through global state and made behaviour
  depend on click order. Paths are now explicit;
* the *window* owns the menu bar and builds it once. The original rebuilt every menu on each
  tab change, which leaked a ``tk.Menu`` per click;
* selecting a tab no longer resizes and re-centres the window, which fought whatever size
  the user had chosen.
"""

import glob
import logging
import os
import sys
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askdirectory
from tkinter.messagebox import askokcancel, showinfo, showwarning

from .. import __version__, config, guide
from .getstarted_tab import GetStartedGui
from .lifespan_tab import LifespanGui
from .mapping_tab import MappingGui
from .projectmaker_tab import ProjectMakerGui
from .maxlifespan_tab import MaxLifespanGui
from .recruitment_tab import RecruitmentGui
from .riverbuilder_tab import RiverBuilderGui
from .sharc_tab import SharcGui
from .stranding_tab import StrandingGui
from .terraforming_tab import TerraformingGui
from .volume_tab import VolumeGui

__all__ = ["RiverArchitectGui", "main", "TAB_GROUPS"]

#: Top-level tabs and their sub-tabs, matching the Qt front end and the ArcGIS version.
TAB_GROUPS = (
    ("Get Started", (GetStartedGui,)),
    ("Lifespan", (LifespanGui, MaxLifespanGui)),
    ("Morphology", (TerraformingGui, RiverBuilderGui, VolumeGui)),
    ("Ecohydraulics", (SharcGui, StrandingGui, RecruitmentGui)),
    ("Project Maker", (ProjectMakerGui,)),
    ("Maps", (MappingGui,)),
)


class RiverArchitectGui(tk.Frame):
    """Top-level window holding one tab per module."""

    def __init__(self, master=None):
        super().__init__(master)
        self.logger = logging.getLogger("riverarchitect")
        self.pack(expand=True, fill=tk.BOTH)

        top = self.winfo_toplevel()
        top.title("River Architect %s" % __version__)
        top.geometry("960x720")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill=tk.BOTH)

        self.tabs = {}
        self.module_tabs = []
        self.groups = {}
        for group, factories in TAB_GROUPS:
            if len(factories) == 1:
                # A group of one is just a tab; nesting it would only add a click.
                self.notebook.add(self._make_tab(self.notebook, factories[0]), text=group)
                continue
            inner = ttk.Notebook(self.notebook)
            for factory in factories:
                inner.add(self._make_tab(inner, factory), text=factory.title)
            self.groups[group] = inner
            self.notebook.add(inner, text=group)

        self.unit = tk.StringVar(value="us")
        self._build_menus()

        self.status = tk.Label(self, anchor=tk.W, relief=tk.SUNKEN, fg="dim gray")
        self.status.pack(side=tk.BOTTOM, fill=tk.X)
        self._update_status()

    def _make_tab(self, parent, factory):
        """Build a module tab, or a message standing in for one that could not load."""
        try:
            tab = factory(parent)
        except Exception as exc:  # a broken module must not take the whole GUI down
            self.logger.error("Could not load the %s tab: %s", factory.title, exc)
            tab = self._placeholder(parent, factory.title, exc)
        else:
            self.module_tabs.append(tab)
        self.tabs[factory.title] = tab
        return tab

    def _placeholder(self, parent, label, exc):
        frame = tk.Frame(parent)
        tk.Label(frame, text="The %s tab could not be loaded." % label,
                 font=("TkDefaultFont", 11, "bold")).pack(padx=20, pady=(30, 8))
        tk.Label(frame, text=str(exc), fg="firebrick", wraplength=600,
                 justify=tk.LEFT).pack(padx=20)
        return frame

    # --------------------------------------------------------------------- menus

    def _build_menus(self):
        """Build the menu bar once. It belongs to the window, not to a tab."""
        top = self.winfo_toplevel()
        menu_bar = tk.Menu(self)
        top.config(menu=menu_bar)

        project_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Project", menu=project_menu)
        project_menu.add_command(label="Set project directory ...",
                                 command=self.choose_project_home)
        project_menu.add_separator()
        project_menu.add_command(label="Quit", command=self.quit_program)

        unit_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Units", menu=unit_menu)
        unit_menu.add_radiobutton(label="U.S. customary", value="us", variable=self.unit,
                                  command=lambda: self.set_unit("us"))
        unit_menu.add_radiobutton(label="SI (metric)", value="si", variable=self.unit,
                                  command=lambda: self.set_unit("si"))

        tools_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Reconcile NoData in a condition ...",
                               command=self.run_reconcile_nodata)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.open_documentation)
        help_menu.add_command(label=guide.TITLE, command=self.open_live_guide)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)

    # ----------------------------------------------------------------- navigation

    def select_tab(self, group, tab=None):
        """Bring a module tab to the front. Used by the Live Guide.

        Args:
            group (str): the top-level tab, as :data:`TAB_GROUPS` names it.
            tab (str): the module tab within it. Defaults to the group itself.

        Returns:
            bool: True when the tab was found and selected.
        """
        tab = tab or group
        for index in range(len(self.notebook.tabs())):
            if self.notebook.tab(index, "text") != group:
                continue
            self.notebook.select(index)
            inner = self.groups.get(group)
            if inner is None:
                return True
            for inner_index in range(len(inner.tabs())):
                if inner.tab(inner_index, "text") == tab:
                    inner.select(inner_index)
                    return True
            return tab == group
        return False

    # -------------------------------------------------------------------- actions

    def set_unit(self, unit):
        """Switch the unit system for every tab."""
        self.unit.set(unit)
        for tab in self.module_tabs:
            tab.set_unit(unit)

    def choose_project_home(self):
        directory = askdirectory(title="Select the River Architect project directory",
                                 initialdir=config.project_home())
        if not directory:
            return
        config.set_project_home(directory)
        for tab in self.module_tabs:
            tab.on_project_home_change()
        self._update_status()
        conditions = self.module_tabs[0].condition_list if self.module_tabs else []
        showinfo("Project directory",
                 "Project directory set to:\n%s\n\n%d condition(s) found."
                 % (directory, len(conditions)))

    def run_reconcile_nodata(self):
        """Run the NoData reconciliation tool on a chosen condition folder."""
        from ..tools import reconcile_nodata

        directory = askdirectory(title="Select a condition folder to reconcile",
                                 initialdir=config.dir_conditions())
        if not directory:
            return
        rasters = sorted(glob.glob(os.path.join(directory, "*.tif")))
        if not rasters:
            showwarning("Reconcile NoData", "No GeoTIFFs found in\n%s" % directory)
            return
        if not askokcancel("Reconcile NoData",
                           "Rewrite %d raster(s) in\n%s\nto NoData = %s?\n\n"
                           "The NoData mask is preserved exactly; only the sentinel changes."
                           % (len(rasters), directory, config.NODATA)):
            return

        changed = failed = 0
        for path in rasters:
            try:
                if reconcile_nodata.reconcile(path):
                    changed += 1
            except Exception as exc:  # pragma: no cover - surfaced to the user
                failed += 1
                self.logger.error("Could not reconcile %s: %s", path, exc)
        message = "%d raster(s) updated." % changed
        if failed:
            message += "\n%d could not be read; see the log." % failed
        showinfo("Reconcile NoData", message)

    @staticmethod
    def open_documentation():
        import webbrowser
        webbrowser.open(guide.DOCS_URL)

    def open_live_guide(self):
        """Open the step-by-step walkthrough of the sample-data example."""
        from .guide_window import open_guide
        open_guide(self.winfo_toplevel(), self)

    def show_about(self):
        showinfo("About River Architect",
                 "River Architect %s\n\n"
                 "Open-source analysis and design of fluvial ecosystems.\n"
                 "https://riverarchitect.readthedocs.io/\n\n"
                 "Interface: tkinter (install PySide6 for the Qt interface)\n"
                 "Project directory:\n%s" % (__version__, config.project_home()))

    def quit_program(self):
        if askokcancel("Close", "Do you really want to quit?"):
            self.winfo_toplevel().destroy()

    def _update_status(self):
        self.status.config(text=" Project: %s" % config.project_home())


def main(argv=None):
    """Start the tkinter interface.

    Normally reached through :func:`riverarchitect.gui.main`, which picks a front end.
    """
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s  %(levelname)-7s %(message)s",
                        datefmt="%H:%M:%S")

    argv = sys.argv[1:] if argv is None else list(argv)
    if argv and not argv[0].startswith("-"):
        config.set_project_home(argv[0])

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print("ERROR: no display available for the graphical interface (%s).\n"
              "River Architect's modules can be used directly from Python:\n"
              "    from riverarchitect.volume_assessment import VolumeAssessment" % exc,
              file=sys.stderr)
        return 1

    RiverArchitectGui(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
