"""Qt binding shim: run on PySide6, or on the PyQt5 that ships with QGIS.

River Architect is used from two different interpreters. Analysis runs in a conda
environment, where PySide6 installs cleanly from PyPI or conda-forge. Mapping has to run in
whichever interpreter owns the QGIS bindings, and QGIS brings its own PyQt5 - installing a
second Qt into that interpreter is how you get two Qt libraries in one process and a
segfault. So the interface targets whatever Qt is already there:

1. PySide6, if it is importable, and
2. PyQt5 otherwise, which is what a QGIS-enabled interpreter has.

Only the handful of names the interface actually uses are re-exported, and only in the
fully-qualified enum form (``Qt.AlignmentFlag.AlignLeft``, not ``Qt.AlignLeft``), which is
the spelling both bindings accept.

:data:`QT_BINDING` names the binding in use; :data:`QT_AVAILABLE` is False when neither is
installed, which is what makes the tkinter fallback kick in.
"""

QT_AVAILABLE = True
QT_BINDING = None

try:
    from PySide6 import QtCore, QtGui, QtWidgets           # noqa: F401
    from PySide6.QtCore import Signal, Slot                # noqa: F401
    QT_BINDING = "PySide6"
except ImportError:
    try:
        from PyQt5 import QtCore, QtGui, QtWidgets         # noqa: F401
        from PyQt5.QtCore import pyqtSignal as Signal      # noqa: F401
        from PyQt5.QtCore import pyqtSlot as Slot          # noqa: F401
        QT_BINDING = "PyQt5"
    except ImportError:
        QT_AVAILABLE = False

if QT_AVAILABLE:
    Qt = QtCore.Qt
    QTimer = QtCore.QTimer
    QObject = QtCore.QObject
    QLocale = QtCore.QLocale

    QAction = QtGui.QAction if QT_BINDING == "PySide6" else QtWidgets.QAction
    QFont = QtGui.QFont
    QIcon = QtGui.QIcon
    QDesktopServices = QtGui.QDesktopServices
    QUrl = QtCore.QUrl

    QApplication = QtWidgets.QApplication
    QMainWindow = QtWidgets.QMainWindow
    QDialog = QtWidgets.QDialog
    QScrollArea = QtWidgets.QScrollArea
    QTextBrowser = QtWidgets.QTextBrowser
    QWidget = QtWidgets.QWidget
    QTabWidget = QtWidgets.QTabWidget
    QLabel = QtWidgets.QLabel
    QPushButton = QtWidgets.QPushButton
    QLineEdit = QtWidgets.QLineEdit
    QDoubleSpinBox = QtWidgets.QDoubleSpinBox
    QComboBox = QtWidgets.QComboBox
    QPlainTextEdit = QtWidgets.QPlainTextEdit
    QGroupBox = QtWidgets.QGroupBox
    QFormLayout = QtWidgets.QFormLayout
    QVBoxLayout = QtWidgets.QVBoxLayout
    QHBoxLayout = QtWidgets.QHBoxLayout
    QFileDialog = QtWidgets.QFileDialog
    QMessageBox = QtWidgets.QMessageBox
    QProgressBar = QtWidgets.QProgressBar
    QStatusBar = QtWidgets.QStatusBar
    QSizePolicy = QtWidgets.QSizePolicy

    def exec_app(app):
        """Start the event loop. ``exec_()`` on PyQt5, ``exec()`` on PySide6."""
        return app.exec() if hasattr(app, "exec") else app.exec_()

    def exec_dialog(dialog):
        """Show a modal dialog and return its result code."""
        return dialog.exec() if hasattr(dialog, "exec") else dialog.exec_()

__all__ = ["QT_AVAILABLE", "QT_BINDING", "Signal", "Slot", "exec_app", "exec_dialog"]
