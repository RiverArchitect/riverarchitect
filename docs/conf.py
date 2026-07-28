"""Sphinx configuration for the River Architect documentation.

Deliberately lean. The previous configuration pulled in myst-nb, jupyter-sphinx, thebe,
ablog, IPython directives and several packages installed straight from git master branches;
that combination broke often and for reasons unrelated to the documentation itself. What is
left is what the docs actually use.
"""

import os
import sys
from datetime import date

# The package lives under src/; make it importable for autodoc.
sys.path.insert(0, os.path.abspath("../src"))

# -- Project ----------------------------------------------------------------

project = "River Architect"
author = "River Architect Development Team"
copyright = "%d, %s" % (date.today().year, author)

try:
    from riverarchitect import __version__ as version
except Exception:  # pragma: no cover - autodoc mocks may not be in place yet
    version = "1.0.0"
release = version

# -- General ----------------------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
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
    "qgis", "PyQt5",
]

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
    "substitution",
    "tasklist",
]
myst_heading_anchors = 3
myst_url_schemes = ("http", "https", "mailto")
# The legacy wiki pages carry many cross-references written for GitHub's wiki renderer.
# They are kept verbatim for provenance; do not fail a build over them.
suppress_warnings = ["myst.header", "myst.xref_missing", "image.nonlocal_uri",
                     "toc.not_included"]

# -- HTML -------------------------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "navigation_depth": 3,
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
if os.path.isfile(os.path.join(_here, "img", "icon.svg")):
    html_logo = "img/icon.svg"
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

latex_documents = [(master_doc, "riverarchitect.tex", project, author, "manual")]
man_pages = [(master_doc, "riverarchitect", project, [author], 1)]
