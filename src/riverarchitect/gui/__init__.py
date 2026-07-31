"""Graphical interface for River Architect.

Two front ends ship with the package and :func:`main` picks between them:

**Qt** (:mod:`riverarchitect.gui.qt`) is the default. It renders with the platform's native
widgets, so the window looks like the rest of the desktop on Linux, Windows and macOS, and
it scales correctly on HiDPI screens. It runs on PySide6 or on the PyQt5 that QGIS brings.

**tkinter** (:mod:`riverarchitect.gui.main`) is the fallback, used when no Qt binding is
installed. It needs nothing beyond the standard library, so the interface always opens.

Start it with the ``riverarchitect`` console script, with ``python -m riverarchitect``, or::

    from riverarchitect.gui import main
    main()

Set ``RIVERARCHITECT_GUI`` to ``qt`` or ``tk`` to force a front end, which is mostly useful
for testing or when a Qt install is misbehaving.
"""

import logging
import os
import sys

from .. import config

__all__ = ["main", "available_backends", "select_backend"]


def available_backends():
    """Return the front ends that can run here, best first.

    Returns:
        list: some of ``"qt"`` and ``"tk"``; empty if neither toolkit is importable.
    """
    backends = []
    try:
        from .qt import QT_AVAILABLE
        if QT_AVAILABLE:
            backends.append("qt")
    except ImportError:
        pass
    try:
        import tkinter  # noqa: F401
        backends.append("tk")
    except ImportError:
        pass
    return backends


def select_backend(preferred=None):
    """Choose a front end.

    Args:
        preferred (str): ``"qt"``, ``"tk"``, or None to read ``RIVERARCHITECT_GUI`` and
            otherwise take the best available.

    Returns:
        str: the chosen backend, or None when no toolkit is available.
    """
    backends = available_backends()
    if not backends:
        return None
    preferred = (preferred or os.environ.get("RIVERARCHITECT_GUI", "")).strip().lower()
    if preferred in backends:
        return preferred
    if preferred:
        logging.getLogger("riverarchitect").warning(
            "Requested interface %r is not available; using %r.", preferred, backends[0])
    return backends[0]


def _set_windows_app_id():
    if sys.platform != "win32":
        return

    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            config.APP_ID
        )
    except (AttributeError, OSError):
        pass


def main(argv=None):
    """Console-script entry point. Starts the graphical interface.

    A single positional argument sets the project directory.

    Returns:
        int: process exit status.
    """
    _set_windows_app_id()
    
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s  %(levelname)-7s %(message)s",
                        datefmt="%H:%M:%S")
    logger = logging.getLogger("riverarchitect")

    argv = sys.argv[1:] if argv is None else list(argv)
    if argv and not argv[0].startswith("-"):
        config.set_project_home(argv[0])
    logger.info("Project directory: %s", config.project_home())

    backend = select_backend()
    if backend is None:
        print("ERROR: no graphical toolkit is available.\n"
              "Install PySide6 (pip install pyside6) or the tkinter standard-library\n"
              "package (python3-tk on Debian/Ubuntu).\n\n"
              "River Architect's modules can also be used directly from Python:\n"
              "    from riverarchitect.volume_assessment import VolumeAssessment",
              file=sys.stderr)
        return 1

    if backend == "qt":
        from .qt import main as qt_main
        from .qt import QT_BINDING
        logger.info("Interface: Qt (%s)", QT_BINDING)
        return qt_main.run(["riverarchitect"])

    from .main import main as tk_main
    logger.info("Interface: tkinter")
    return tk_main([])
