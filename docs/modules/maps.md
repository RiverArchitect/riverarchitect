# Maps

{mod}`riverarchitect.mapping` - the **Maps** tab.

Renders any result raster into a publication-quality PDF through a **QGIS print layout**,
with multi-page reach series driven by a QGIS atlas. It replaces the original's ArcGIS
layout templates and `.lyr` symbology.

## Finding QGIS

QGIS's Python bindings cannot be installed from PyPI. A distribution installs them for the
**system** interpreter (`sudo apt install qgis python3-qgis` puts them in
`/usr/lib/python3/dist-packages`), so a conda environment does not see them even though QGIS
is installed and working perfectly.

River Architect looks for them itself. On import, `riverarchitect.mapping` tries
`import qgis`; if that fails it searches the usual installation locations for the platform
and, when it finds bindings that actually load, appends that directory to `sys.path`:

| Platform | Searched |
|---|---|
| Linux | `/usr/lib/python3*/dist-packages`, `/usr/share/qgis/python`, `/usr/local/share/qgis/python`, `/opt/qgis*/share/qgis/python` |
| macOS | `/Applications/QGIS*.app/Contents/Resources/python`, `~/Applications/…`, Homebrew |
| Windows | `C:\OSGeo4W*\apps\qgis*\python`, `C:\Program Files\QGIS *\apps\qgis*\python` |

Where a glob matches several installations the newest is tried first. On Windows the
matching `bin` directories are registered with `os.add_dll_directory`, without which the
extension modules import but their Qt, GDAL and PROJ libraries do not - the failure that
otherwise shows up as a bare `DLL load failed`.

Two environment variables override all of it:

```bash
export RIVERARCHITECT_QGIS_PATH=/path/to/dir/containing/the/qgis/package
export QGIS_PREFIX_PATH=/path/to/installation/prefix
```

The Maps tab reports what was found - the QGIS version, the bindings directory and the
prefix - or, if nothing was, exactly what to install and how to point at it.

````{admonition} Why the directory is appended and not put on PYTHONPATH
:class: warning

On Debian and Ubuntu the QGIS bindings sit in `/usr/lib/python3/dist-packages` **beside the
distribution's own numpy, pandas and scipy**. `PYTHONPATH` entries come *before* an
environment's own `site-packages`, so

```bash
PYTHONPATH=/usr/lib/python3/dist-packages riverarchitect     # do not do this
```

silently replaces numpy 2.5 with 1.26 and pandas 3.0 with 2.1, and every analysis then runs
against a different stack from the one it was tested with. That is a worse failure than no
mapping, because it produces results rather than an error.

River Architect appends instead, so the environment's own packages keep priority and only
the modules it genuinely does not have - `qgis` and its `PyQt5` - come from the system.
````

````{admonition} If the bindings are built for a different Python
:class: note

Discovery only succeeds when the bindings are ABI-compatible with the running interpreter -
in practice, the same Python minor version. Ubuntu 24.04 ships Python 3.12 and the `ra-env`
environment is Python 3.12, so they match. When they do not, the Maps tab says so and names
the directory it rejected, and the fallback is to start River Architect with the interpreter
QGIS was installed for:

```bash
RA_PYTHON=/usr/bin/python3 ./runRiverArchitectLinux.sh
```

That interpreter usually has no rasterio, so the analysis tabs disable themselves instead -
which is why matching versions is much the better outcome.
````

Layer styles ship as QGIS `.qml` files under the package's `templates/symbology/`. The
`riverarchitect-lyrx2qml` console script converts an ArcGIS Pro `.lyrx` to `.qml`, so a
project that has already invested in symbology does not have to redo it.

## In this section

```{toctree}
:maxdepth: 1

../guide/qgis_mapping
Mapping with River Architect (legacy) <../wiki/Mapping>
```

```{eval-rst}
.. seealso::

   :mod:`riverarchitect.mapping` and :mod:`riverarchitect.tools` in the API reference.
```
