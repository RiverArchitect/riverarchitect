"""Shared behaviour for Qt module tabs.

The tkinter base class (:mod:`riverarchitect.gui.base`) owns its own menu bar and resizes
the whole window whenever its tab is selected. Neither is right in a Qt application: menus
belong to the main window, and a tab must not move the window under the user. What is left
here is what a tab genuinely shares - the unit system, the condition list, and a way to run
work off the interface thread.
"""

import logging
import os
import threading

from ... import config
from .qtcompat import (QFileDialog, QLabel, QMessageBox, QSizePolicy, QVBoxLayout, QWidget,
                       Qt, Signal)

__all__ = ["RaTab"]


class RaTab(QWidget):
    """Base class for a module tab.

    Subclasses set :attr:`title` and :attr:`subtitle`, then build their widgets into
    :attr:`body`. Long-running work goes through :meth:`run_in_background`, which keeps the
    interface responsive and marshals the result back onto the Qt thread.
    """

    #: Tab label.
    title = "River Architect"
    #: One or two lines shown under the tab heading.
    subtitle = ""

    #: Emitted from a worker thread when background work finishes. Internal.
    _finished = Signal(object, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger("riverarchitect")

        self.unit = "us"
        self.labels = config.unit_labels(self.unit)
        self.condition_list = []
        self.refresh_conditions()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        heading = QLabel(self.title)
        font = heading.font()
        font.setPointSize(font.pointSize() + 4)
        font.setBold(True)
        heading.setFont(font)
        layout.addWidget(heading)

        if self.subtitle:
            note = QLabel(self.subtitle)
            note.setWordWrap(True)
            note.setStyleSheet("color: palette(mid);")
            layout.addWidget(note)

        self.body = QWidget(self)
        self.body.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.body)

        self._finished.connect(self._on_finished)
        self._callback = None

    # ------------------------------------------------------------------ background

    def run_in_background(self, work, on_success, on_error):
        """Run ``work()`` on a worker thread and deliver the outcome on the Qt thread.

        Qt widgets may only be touched from the thread that created them, so the worker
        emits a signal instead of calling back directly. A queued signal connection is the
        Qt equivalent of tkinter's ``widget.after(0, ...)``.
        """
        self._callback = (on_success, on_error)

        def runner():
            try:
                self._finished.emit(work(), None)
            except Exception as exc:  # surfaced to the user by the error callback
                self._finished.emit(None, exc)

        threading.Thread(target=runner, daemon=True).start()

    def _on_finished(self, result, error):
        if self._callback is None:
            return
        on_success, on_error = self._callback
        self._callback = None
        if error is not None:
            on_error(error)
        else:
            on_success(result)

    # ----------------------------------------------------------------------- units

    def set_unit(self, unit):
        """Switch the unit system and notify the subclass through :meth:`on_unit_change`."""
        if unit not in config.UNITS or unit == self.unit:
            return
        self.unit = unit
        self.labels = config.unit_labels(unit)
        self.on_unit_change()

    def on_unit_change(self):
        """Hook called after the unit system changed. Does nothing by default."""

    # ------------------------------------------------------------------ conditions

    def refresh_conditions(self):
        """Reload the list of conditions available in the project directory."""
        try:
            self.condition_list = sorted(
                name for name in os.listdir(config.dir_conditions())
                if os.path.isdir(os.path.join(config.dir_conditions(), name))
                and not name.startswith("."))
        except OSError:
            self.condition_list = []
        return self.condition_list

    def on_project_home_change(self):
        """Hook called after the project directory changed. Refreshes the condition list."""
        self.refresh_conditions()

    # ------------------------------------------------------------------- utilities

    def choose_file(self, caption, patterns="Raster files (*.tif *.tiff *.flt *.asc);;"
                                            "All files (*)"):
        path, _ = QFileDialog.getOpenFileName(self, caption, config.project_home(), patterns)
        return path

    def choose_directory(self, caption, start=None):
        return QFileDialog.getExistingDirectory(self, caption, start or config.project_home())

    def warn(self, title, text):
        QMessageBox.warning(self, title, text)

    def fail(self, title, text):
        QMessageBox.critical(self, title, text)

    @staticmethod
    def elide(path, limit=54):
        """Shorten a path for a button label, keeping the file name readable."""
        if not path:
            return ""
        if len(path) <= limit:
            return path
        return "..." + os.sep + os.path.basename(path)
