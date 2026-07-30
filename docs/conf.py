"""Sphinx configuration for the River Architect documentation.

Deliberately lean. The previous configuration pulled in myst-nb, jupyter-sphinx, thebe,
ablog, IPython directives and several packages installed straight from git master branches;
that combination broke often and for reasons unrelated to the documentation itself. What is
left is what the docs actually use.
"""

import os
import sys
from datetime import date

# The package lives under src/; make it importable for autodoc. Resolve against *this file*,
# not the working directory: Read the Docs runs sphinx from inside docs/, while a local
# `sphinx -b html docs docs/_build/html` runs from the repository root. A CWD-relative path
# silently resolves to nothing in one of the two, and the build then differs between them.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

# -- Project ----------------------------------------------------------------

project = "River Architect"
author = "River Architect Development Team"
copyright = "%d, %s" % (date.today().year, author)

try:
    from riverarchitect import __version__ as version
except Exception:  # pragma: no cover - autodoc mocks may not be in place yet
    version = "2.2.0"
release = version

# -- General ----------------------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.todo",
    "sphinx_copybutton",
    "sphinx_design",
    "myst_parser",
]

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
master_doc = "index"
language = "en"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
templates_path = ["_templates"]
pygments_style = "sphinx"
numfig = True
todo_include_todos = False

# Heavy or platform-specific dependencies are mocked so that Read the Docs can import the
# package for autodoc without installing a full geospatial stack (and without QGIS, which
# is not installable from PyPI at all).
autodoc_mock_imports = [
    "numpy", "scipy", "pandas",
    "rasterio", "geopandas", "shapely", "fiona", "pyproj", "osgeo",
    "pykrige", "rasterstats", "whitebox", "matplotlib",
    "qgis", "PyQt5", "PySide6",
]


class _BlockQtBindings:
    """Keep the *real* Qt bindings out of the documentation build.

    Read the Docs never installs PySide6, so the mock above is all it needs. A developer
    building the docs locally has it installed, and there ``sphinx.ext.viewcode`` imports
    ``riverarchitect.gui.qt.qtcompat`` for real to link its source. That pulls in shiboken,
    which installs an import hook that runs ``inspect.getsource`` on every module imported
    afterwards - including autodoc's mocked ``numpy``, a self-wrapping object that sends
    ``inspect.unwrap`` into "wrapper loop when unwrapping numpy". Every later autodoc import
    then fails.

    Blocking the binding outright makes the local build behave like the Read the Docs one.
    ``qtcompat`` is written to degrade when no binding is importable, which is exactly the
    path this takes.
    """

    _blocked = ("PySide6", "shiboken6", "PyQt5")

    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in self._blocked:
            raise ImportError("Qt bindings are not imported during the docs build")
        return None


sys.meta_path.insert(0, _BlockQtBindings())

autodoc_default_options = {
    "member-order": "bysource",
    "exclude-members": "__weakref__",
}
autodoc_typehints = "description"

napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_use_ivar = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "rasterio": ("https://rasterio.readthedocs.io/en/stable/", None),
}

# -- MyST -------------------------------------------------------------------

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "dollarmath",
    "substitution",
    "tasklist",
]
myst_heading_anchors = 3
myst_url_schemes = ("http", "https", "mailto")
# The legacy wiki pages carry many cross-references written for GitHub's wiki renderer.
# They are kept verbatim for provenance; do not fail a build over them. `xref_ambiguous`
# covers their in-page anchors, such as `[Run](#run)`, which MyST tries to resolve against
# the Python domain and finds more than one match for.
# `toc.not_included` is deliberately *not* suppressed: a page in no toctree is a page
# nobody can reach, and that is how stale documentation accumulates. Every page must have a
# home in the structure, or be deleted.
suppress_warnings = ["myst.header", "myst.xref_missing", "myst.xref_ambiguous",
                     "image.nonlocal_uri",
                     # The epub builder inspects the output tree and reports every doctree
                     # cache file it finds there. Noise, not a problem with the content.
                     "epub.unknown_project_files"]

# -- HTML -------------------------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    # 4, not 3: the API reference now sits inside Development, so its module
    # pages are one level deeper than they used to be and would be cut off.
    "navigation_depth": 4,
    "collapse_navigation": False,
    "sticky_navigation": True,
    "prev_next_buttons_location": "both",
}
html_title = "River Architect %s" % version
html_static_path = ["_static"] if os.path.isdir(
    os.path.join(os.path.dirname(__file__), "_static")) else []
html_last_updated_fmt = "%Y-%m-%d"
html_show_sourcelink = True
htmlhelp_basename = "RiverArchitect"

_here = os.path.dirname(os.path.abspath(__file__))
if os.path.isfile(os.path.join(_here, "img", "icon-v2.svg")):
    html_logo = "img/icon-v2.svg"
if os.path.isfile(os.path.join(_here, "img", "browser-icon.ico")):
    html_favicon = "img/browser-icon.ico"

html_context = {
    "display_github": True,
    "github_user": "RiverArchitect",
    "github_repo": "riverarchitect",
    "github_version": "main",
    "conf_py_path": "/docs/",
}

# -- LaTeX / man ------------------------------------------------------------

# pdflatex, the Sphinx default, aborts on the Unicode this documentation contains: Greek
# letters in the hydraulics formulae, box-drawing characters in the directory trees, and
# mathematical italics in the legacy wiki pages. xelatex handles all of them.
#
# A PDF build also needs `xindy` for the index, which is why `pdf` is not in the Read the
# Docs `formats` list: a PDF failure fails the whole build and would take the HTML down
# with it. Locally: `make -C docs/_build/latex`.
latex_engine = "xelatex"
latex_documents = [(master_doc, "riverarchitect.tex", project, author, "manual")]
man_pages = [(master_doc, "riverarchitect", project, [author], 1)]
