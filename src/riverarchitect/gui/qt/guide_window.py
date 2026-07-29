"""The Live Guide dialog for the Qt front end.

Renders :data:`riverarchitect.guide.STEPS` one step at a time. It is deliberately
*non*-modal: the point of a live guide is that you can read a step and work in the main
window at the same time, so the dialog stays open beside it and can bring the tab a step
talks about to the front.

See :mod:`riverarchitect.gui.guide_window` for the tkinter rendering of the same data.
"""

from html import escape

from ... import guide
from .qtcompat import (QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton,
                       QTextBrowser, QVBoxLayout)

__all__ = ["GuideDialog", "open_guide"]


class GuideDialog(QDialog):
    """A step-by-step walkthrough of the sample-data example.

    Args:
        parent (QMainWindow): the main window, driven by the guide's buttons.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.window_ = parent
        self.index = 0

        self.setWindowTitle(guide.TITLE)
        self.resize(700, 640)
        # Not modal: the reader works in the main window while the guide stays open.
        self.setModal(False)

        self._build()
        self._show_step()

    # ---------------------------------------------------------------------- layout

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        self.progress = QLabel()
        self.progress.setStyleSheet("color: palette(mid);")
        layout.addWidget(self.progress)

        self.heading = QLabel()
        font = self.heading.font()
        font.setPointSize(font.pointSize() + 3)
        font.setBold(True)
        self.heading.setFont(font)
        self.heading.setWordWrap(True)
        layout.addWidget(self.heading)

        self.location = QLabel()
        self.location.setStyleSheet("color: palette(mid);")
        layout.addWidget(self.location)

        self.body = QTextBrowser()
        self.body.setOpenExternalLinks(True)
        layout.addWidget(self.body, 1)

        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setStyleSheet("color: palette(mid);")
        layout.addWidget(self.status)

        actions = QHBoxLayout()
        self.sample_button = QPushButton("Use the sample data")
        self.sample_button.clicked.connect(self.use_sample_data)
        actions.addWidget(self.sample_button)

        self.open_button = QPushButton("Open this tab")
        self.open_button.clicked.connect(self.open_tab)
        actions.addWidget(self.open_button)

        actions.addStretch(1)

        self.back_button = QPushButton("< Back")
        self.back_button.clicked.connect(self.previous_step)
        actions.addWidget(self.back_button)

        self.next_button = QPushButton("Next >")
        self.next_button.setDefault(True)
        self.next_button.clicked.connect(self.next_step)
        actions.addWidget(self.next_button)

        close = QPushButton("Close")
        close.clicked.connect(self.close)
        actions.addWidget(close)

        layout.addLayout(actions)

    # ----------------------------------------------------------------------- render

    @property
    def step(self):
        return guide.STEPS[self.index]

    def _html(self, step):
        parts = ["<style>"
                 "p { margin: 0 0 10px 0; }"
                 "h4 { margin: 14px 0 4px 0; }"
                 "td { padding: 1px 10px 1px 0; vertical-align: top; }"
                 "</style>"]
        for paragraph in step.paragraphs():
            parts.append("<p>%s</p>" % escape(paragraph))
        if step.settings:
            parts.append("<h4>Settings</h4><table>")
            for label, value in step.settings:
                parts.append("<tr><td><b>%s</b></td><td>%s</td></tr>"
                             % (escape(label), escape(value)))
            parts.append("</table>")
        if step.expect:
            parts.append("<h4>Expect</h4><p>%s</p>" % escape(step.expect))
        if step.writes:
            parts.append("<h4>Writes</h4><pre>%s</pre>"
                         % escape("\n".join(step.writes)))
        return "".join(parts)

    def _show_step(self):
        step = self.step
        self.progress.setText("Step %d of %d" % (self.index + 1, len(guide.STEPS)))
        self.heading.setText(step.title)
        location = step.group if step.tab == step.group \
            else "%s &rsaquo; %s" % (step.group, step.tab)
        self.location.setText("Tab: %s" % location)
        self.body.setHtml(self._html(step))
        self.body.verticalScrollBar().setValue(0)

        self.back_button.setEnabled(self.index > 0)
        last = self.index == len(guide.STEPS) - 1
        self.next_button.setText("Finish" if last else "Next >")
        self.open_button.setEnabled(self.window_ is not None)
        self._update_status()

    def _update_status(self):
        ready, message = guide.sample_data_status()
        self.status.setText(message)
        self.sample_button.setEnabled(bool(ready) and self.window_ is not None)

    # ---------------------------------------------------------------------- actions

    def next_step(self):
        if self.index >= len(guide.STEPS) - 1:
            self.close()
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
            QMessageBox.warning(self, guide.TITLE, str(exc))
            return
        if self.window_ is not None:
            for tab in self.window_.module_tabs:
                tab.on_project_home_change()
            self.window_.set_unit("us")
            self.window_._update_status()
        self._update_status()
        QMessageBox.information(
            self, guide.TITLE,
            "Project directory set to the sample data:\n%s\n\n"
            "Units set to U.S. customary, which is what these rasters are in." % directory)

    def open_tab(self):
        """Bring the tab this step talks about to the front of the main window."""
        if self.window_ is None:
            return
        if not self.window_.select_tab(self.step.group, self.step.tab):
            QMessageBox.warning(
                self, guide.TITLE,
                "Could not find the %s tab. It may have failed to load; see the log."
                % self.step.tab)


def open_guide(parent=None):
    """Open the Live Guide, or raise the one already open."""
    existing = getattr(parent, "_guide_dialog", None)
    if existing is not None:
        existing.show()
        existing.raise_()
        existing.activateWindow()
        return existing
    dialog = GuideDialog(parent)
    if parent is not None:
        parent._guide_dialog = dialog
    dialog.show()
    return dialog
