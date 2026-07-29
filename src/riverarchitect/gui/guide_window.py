"""The Live Guide window for the tkinter front end.

Renders :data:`riverarchitect.guide.STEPS` one step at a time, and does the two things a
printed walkthrough cannot: point the project directory at the bundled sample data, and
bring the tab a step talks about to the front, so the reader is looking at the right
controls while they read about them.

See :mod:`riverarchitect.gui.qt.guide_window` for the Qt rendering of the same data.
"""

import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showerror, showinfo

from .. import guide

__all__ = ["GuideWindow", "open_guide"]


class GuideWindow(tk.Toplevel):
    """A step-by-step walkthrough of the sample-data example.

    Args:
        master: the main window. Used to activate tabs and to refresh them after the
            project directory changes.
        app (riverarchitect.gui.main.RiverArchitectGui): the application frame, when the
            window should drive it. Optional; without it the guide is read-only.
    """

    def __init__(self, master=None, app=None):
        super().__init__(master)
        self.app = app
        self.index = 0

        self.title(guide.TITLE)
        self.geometry("720x640")
        self.minsize(560, 480)

        self._build()
        self._show_step()

    # ---------------------------------------------------------------------- layout

    def _build(self):
        outer = ttk.Frame(self, padding=14)
        outer.pack(expand=True, fill=tk.BOTH)

        self.progress = ttk.Label(outer, foreground="dim gray")
        self.progress.pack(anchor=tk.W)

        self.heading = ttk.Label(outer, font=("TkDefaultFont", 13, "bold"),
                                 wraplength=660, justify=tk.LEFT)
        self.heading.pack(anchor=tk.W, pady=(2, 0))

        self.location = ttk.Label(outer, foreground="dim gray", wraplength=660,
                                  justify=tk.LEFT)
        self.location.pack(anchor=tk.W, pady=(0, 8))

        # A read-only Text rather than a Label: the bodies are long enough that they need
        # to scroll, and a Label cannot.
        body_frame = ttk.Frame(outer)
        body_frame.pack(expand=True, fill=tk.BOTH)
        scrollbar = ttk.Scrollbar(body_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.body = tk.Text(body_frame, wrap=tk.WORD, relief=tk.FLAT, padx=2, pady=2,
                            yscrollcommand=scrollbar.set, height=18,
                            background=self.cget("background"))
        self.body.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        scrollbar.config(command=self.body.yview)
        self.body.tag_configure("h", font=("TkDefaultFont", 9, "bold"),
                                spacing1=8, spacing3=2)
        self.body.tag_configure("p", spacing3=8)
        self.body.tag_configure("item", lmargin1=14, lmargin2=28)
        self.body.tag_configure("expect", foreground="#1a6b1a", spacing1=8, spacing3=6)
        self.body.tag_configure("mono", font=("TkFixedFont", 9), lmargin1=14, lmargin2=28)

        self.status = ttk.Label(outer, foreground="dim gray", wraplength=660,
                                justify=tk.LEFT)
        self.status.pack(anchor=tk.W, pady=(8, 4))

        actions = ttk.Frame(outer)
        actions.pack(fill=tk.X)
        self.sample_button = ttk.Button(actions, text="Use the sample data",
                                        command=self.use_sample_data)
        self.sample_button.pack(side=tk.LEFT)
        self.open_button = ttk.Button(actions, text="Open this tab",
                                      command=self.open_tab)
        self.open_button.pack(side=tk.LEFT, padx=6)

        ttk.Button(actions, text="Close", command=self.destroy).pack(side=tk.RIGHT)
        self.next_button = ttk.Button(actions, text="Next >", command=self.next_step)
        self.next_button.pack(side=tk.RIGHT, padx=6)
        self.back_button = ttk.Button(actions, text="< Back", command=self.previous_step)
        self.back_button.pack(side=tk.RIGHT)

    # ----------------------------------------------------------------------- render

    @property
    def step(self):
        return guide.STEPS[self.index]

    def _show_step(self):
        step = self.step
        self.progress.config(text="Step %d of %d" % (self.index + 1, len(guide.STEPS)))
        self.heading.config(text=step.title)
        location = step.group if step.tab == step.group \
            else "%s > %s" % (step.group, step.tab)
        self.location.config(text="Tab:  %s" % location)

        self.body.config(state=tk.NORMAL)
        self.body.delete("1.0", tk.END)
        for paragraph in step.paragraphs():
            self.body.insert(tk.END, paragraph + "\n", "p")
        if step.settings:
            self.body.insert(tk.END, "Settings\n", "h")
            for label, value in step.settings:
                self.body.insert(tk.END, "%s:  %s\n" % (label, value), "item")
        if step.expect:
            self.body.insert(tk.END, "Expect\n", "h")
            self.body.insert(tk.END, step.expect + "\n", "expect")
        if step.writes:
            self.body.insert(tk.END, "Writes\n", "h")
            for path in step.writes:
                self.body.insert(tk.END, path + "\n", "mono")
        self.body.config(state=tk.DISABLED)
        self.body.yview_moveto(0.0)

        self.back_button.state(["disabled"] if self.index == 0 else ["!disabled"])
        self.next_button.config(
            text="Finish" if self.index == len(guide.STEPS) - 1 else "Next >")
        self.open_button.state(["!disabled"] if self.app is not None else ["disabled"])
        self._update_status()

    def _update_status(self):
        ready, message = guide.sample_data_status()
        self.status.config(text=message)
        self.sample_button.state(["!disabled"] if ready and self.app is not None
                                 else ["disabled"])

    # ---------------------------------------------------------------------- actions

    def next_step(self):
        if self.index >= len(guide.STEPS) - 1:
            self.destroy()
            return
        self.index += 1
        self._show_step()

    def previous_step(self):
        if self.index > 0:
            self.index -= 1
            self._show_step()

    def use_sample_data(self):
        """Point the project directory at the bundled sample data."""
        try:
            directory = guide.activate_sample_data()
        except FileNotFoundError as exc:
            showerror(guide.TITLE, str(exc))
            return
        if self.app is not None:
            for tab in self.app.module_tabs:
                tab.on_project_home_change()
            self.app.set_unit("us")
            self.app._update_status()
        self._update_status()
        showinfo(guide.TITLE,
                 "Project directory set to the sample data:\n%s\n\n"
                 "Units set to U.S. customary, which is what these rasters are in."
                 % directory)

    def open_tab(self):
        """Bring the tab this step talks about to the front of the main window."""
        if self.app is None:
            return
        if not self.app.select_tab(self.step.group, self.step.tab):
            showerror(guide.TITLE,
                      "Could not find the %s tab. It may have failed to load; see the log."
                      % self.step.tab)


def open_guide(master=None, app=None):
    """Open the Live Guide window, or raise the one already open."""
    existing = getattr(app, "_guide_window", None)
    if existing is not None and existing.winfo_exists():
        existing.deiconify()
        existing.lift()
        return existing
    window = GuideWindow(master, app)
    if app is not None:
        app._guide_window = window
    return window
