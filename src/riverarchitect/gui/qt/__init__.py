"""Qt front end for River Architect.

The default interface. Runs on PySide6, or on the PyQt5 that comes with QGIS - see
:mod:`riverarchitect.gui.qt.qtcompat` for why both are supported. When neither binding is
installed, :data:`~riverarchitect.gui.qt.qtcompat.QT_AVAILABLE` is False and
:mod:`riverarchitect.gui` falls back to the tkinter interface.
"""

from .qtcompat import QT_AVAILABLE, QT_BINDING

__all__ = ["QT_AVAILABLE", "QT_BINDING", "RiverArchitectWindow", "run"]


def __getattr__(name):
    """Import the window lazily so that ``QT_AVAILABLE`` can be read without a Qt binding."""
    if name in ("RiverArchitectWindow", "run"):
        from . import main
        return getattr(main, name)
    raise AttributeError("module %r has no attribute %r" % (__name__, name))
