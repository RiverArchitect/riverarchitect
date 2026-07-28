"""Allow ``python -m riverarchitect`` to start the graphical interface."""

import sys

from .gui import main

if __name__ == "__main__":
    sys.exit(main())
