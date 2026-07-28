"""Tkinter graphical interface for River Architect.

Start it with the ``riverarchitect`` console script, ``python -m riverarchitect``, or::

    from riverarchitect.gui import main
    main()
"""

from .main import RiverArchitectGui, main

__all__ = ["RiverArchitectGui", "main"]
