"""The Live Guide dialog for the Qt front end.

Renders :data:`riverarchitect.guide.STEPS` one step at a time. It is deliberately
*non*-modal: the point of a live guide is that you can read a step and work in the main
window at the same time, so the dialog stays open beside it and can bring the tab a step
talks about to the front.

The guide is meant to be watched, not only clicked through, so it can play itself. Play
advances every :data:`riverarchitect.guide.AUTOPLAY_SECONDS`, any manual navigation pauses
it - a reader who reaches for Back is not asking to race the timer - and the position is
saved on every step, so closing the window and reopening it resumes rather than restarts.

See :mod:`riverarchitect.gui.guide_window` for the tkinter rendering of the same data.
"""

from html import escape

from ... import guide
from .qtcompat import (QComboBox, QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton,
                       QTextBrowser, QTimer, QVBoxLayout)

__all__ = ["GuideDialog", "open_guide"]


class GuideDialog(QDialog):
    """A step-by-step walkthrough of the sample-data example.

    Args:
        parent (QMainWindow): the main window, driven by the guide's buttons.
        resume (bool): open at the step last left off on. False starts at the beginning,
            which is what Restart wants.
    """

    def __init__(self, parent=None, resume=True):
        super().__init__(parent)
        self.window_ = parent
        self.resumed = False
        self.index = 0
        if resume:
            key = guide.load_progress()
            if key:
                self.index = guide.step_index(key)
                self.resumed = self.index > 0

        self.setWindowTitle(guide.TITLE)
        self.resize(700, 700)
        # Not modal: the reader works in the main window while the guide stays open.
        self.setModal(False)

        self.timer = QTimer(self)
        self.timer.setInterval(guide.AUTOPLAY_SECONDS * 1000)
        self.timer.timeout.connect(self._advance)

        self._build()
        self._show_step()

    # ---------------------------------------------------------------------- layout

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        jump = QHBoxLayout()
        self.progress = QLabel()
        self.progress.setStyleSheet("color: palette(mid);")
        jump.addWidget(self.progress)
        jump.addStretch(1)
        jump.addWidget(QLabel("Go to:"))
        self.jump = QComboBox()
        self.jump.addItems(guide.step_titles())
        self.jump.setMinimumWidth(320)
        # Set before connecting: populating a combo emits the signal, and letting that
        # reach the handler during construction would pause a timer that is not running
        # and save a position the reader never chose.
        self.jump.setCurrentIndex(self.index)
        self.jump.currentIndexChanged.connect(self.jump_to)
        jump.addWidget(self.jump)
        layout.addLayout(jump)

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

        self.restart_button = QPushButton("Restart")
        self.restart_button.setToolTip("Go back to the first step and forget the saved "
                                       "position.")
        self.restart_button.clicked.connect(self.restart)
        actions.addWidget(self.restart_button)

        actions.addStretch(1)

        self.play_button = QPushButton("Play")
        self.play_button.setToolTip("Advance by itself every %d seconds. Any other "
                                    "navigation pauses it." % guide.AUTOPLAY_SECONDS)
        self.play_button.clicked.connect(self.toggle_play)
        actions.addWidget(self.play_button)

        self.back_button = QPushButton("< Back")
        self.back_button.clicked.connect(self.previous_step)
        actions.addWidget(self.back_button)

        self.next_button = QPushButton("Next >")
        self.next_button.setDefault(True)
        self.next_button.clicked.connect(self.next_step)
        actions.addWidget(self.next_button)

        close = QPushButton("Close")
        close.setToolTip("Closing keeps your place. Reopen from the Help menu.")
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
        label = "Tab: %s" if step.has_tab else "Menu: %s"
        # Plain text with a real separator character. An HTML entity would be a gamble:
        # QLabel only interprets markup when its rich-text heuristic fires, and "&rsaquo;"
        # on its own does not reliably trip it, so it can end up on screen verbatim.
        self.location.setText(label % step.location.replace(" > ", " \u203a "))
        self.body.setHtml(self._html(step))
        self.body.verticalScrollBar().setValue(0)

        if self.jump.currentIndex() != self.index:
            was = self.jump.blockSignals(True)
            self.jump.setCurrentIndex(self.index)
            self.jump.blockSignals(was)

        self.back_button.setEnabled(self.index > 0)
        last = self.index == len(guide.STEPS) - 1
        self.next_button.setText("Finish" if last else "Next >")
        self.restart_button.setEnabled(self.index > 0)
        # A step that is only about a menu has no tab to raise.
        self.open_button.setEnabled(self.window_ is not None and step.has_tab)
        guide.save_progress(step.key)
        self._update_status()

    def _update_status(self):
        ready, message = guide.sample_data_status()
        if self.resumed:
            message = ("Resumed where you left off. Restart begins again from step 1. "
                       + message)
        self.status.setText(message)
        self.sample_button.setEnabled(bool(ready) and self.window_ is not None)

    # ------------------------------------------------------------------- navigation

    def next_step(self):
        self.pause()
        if self.index >= len(guide.STEPS) - 1:
            self.close()
            return
        self._go(self.index + 1)

    def previous_step(self):
        self.pause()
        if self.index > 0:
            self._go(self.index - 1)

    def jump_to(self, index):
        """Show a step chosen from the jump list."""
        self.pause()
        self._go(index)

    def restart(self):
        """Return to the first step and forget the saved position."""
        self.pause()
        guide.clear_progress()
        self._go(0)

    def _go(self, index):
        self.index = max(0, min(int(index), len(guide.STEPS) - 1))
        self.resumed = False
        self._show_step()

    # --------------------------------------------------------------------- playback

    def toggle_play(self):
        """Start or stop advancing by itself."""
        self.pause() if self.timer.isActive() else self.play()

    def play(self):
        if self.index >= len(guide.STEPS) - 1:
            # Nothing to advance to; starting the timer here would only look broken.
            return
        self.timer.start()
        self.play_button.setText("Pause")

    def pause(self):
        self.timer.stop()
        self.play_button.setText("Play")

    def _advance(self):
        """Timer tick: move on, and stop at the end rather than closing the window."""
        if self.index >= len(guide.STEPS) - 1:
            self.pause()
            return
        self._go(self.index + 1)
        if self.index >= len(guide.STEPS) - 1:
            self.pause()

    def closeEvent(self, event):
        self.pause()
        super().closeEvent(event)

    # ---------------------------------------------------------------------- actions

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
            "Units set to U.S. customary, which is what these rasters are in. "
            "(The program otherwise starts in SI units.)" % directory)

    def open_tab(self):
        """Bring the tab this step talks about to the front of the main window."""
        if self.window_ is None or not self.step.has_tab:
            return
        self.pause()
        if not self.window_.select_tab(self.step.group, self.step.tab):
            QMessageBox.warning(
                self, guide.TITLE,
                "Could not find the %s tab. It may have failed to load; see the log."
                % self.step.tab)


def open_guide(parent=None):
    """Open the Live Guide, or raise the one already open."""
    existing = getattr(parent, "_guide_dialog", None)
    if existing is not None:
        try:
            existing.show()
            existing.raise_()
            existing.activateWindow()
            return existing
        except RuntimeError:
            # The C++ dialog was destroyed under the Python wrapper. Build a new one
            # rather than propagating "wrapped C/C++ object has been deleted".
            pass
    dialog = GuideDialog(parent)
    if parent is not None:
        parent._guide_dialog = dialog
    dialog.show()
    return dialog
