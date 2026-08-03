# Maps

{mod}`riverarchitect.mapping` - the **Maps** tab.

Renders any result raster into a publication-quality PDF through a **QGIS print layout**, with multi-page reach series driven by a QGIS atlas.

```{toctree}
:maxdepth: 1
:caption: In this section

../guide/qgis_mapping
```

## What a map is made of

A map sheet is a layout - map frame, legend, scale bar, north arrow, title, footer - composed in code by `Mapper.build_layout()`, so no binary template is required. Drop a hand-built `river_template.qgz` into `02_Maps/templates/` and that project is used as the starting point instead, which is how house styling, base layers and a custom layout are kept.

**Layer styles** are QGIS `.qml` files under the package's `templates/symbology/`, chosen by raster name (`lf_sym` for lifespan maps, `ds_sym` for design maps, and so on). Edit one in QGIS and save it over the file to restyle every map that uses it. Where no `.qml` matches, the layer keeps QGIS defaults and a warning is logged; the map is still produced, just unstyled.

**A background raster** named `background.tif` in the condition folder is picked up as a base layer, so a hillshade or an orthophoto underlies the result.

**Map extent** follows the raster being mapped by default. Pass an explicit `[xmin, ymin, xmax, ymax]`, or `"MAXOF"` for the union of the layers. For a reach series, give a list of page centres and a page size and QGIS drives the pages from a coverage layer as an atlas, writing one multi-page PDF in a single export.

## Finding QGIS

QGIS's Python bindings cannot be installed from PyPI. A distribution installs them for the **system** interpreter (`sudo apt install qgis python3-qgis` puts them in `/usr/lib/python3/dist-packages`), so a conda environment does not see them even though QGIS is installed and working perfectly.

River Architect looks for them itself. On import, `riverarchitect.mapping` tries `import qgis`; if that fails it searches the usual installation locations for the platform and, when it finds bindings that actually load, appends that directory to `sys.path`:

| Platform | Searched |
|---|---|
| Linux | `/usr/lib/python3*/dist-packages`, `/usr/share/qgis/python`, `/usr/local/share/qgis/python`, `/opt/qgis*/share/qgis/python` |
| macOS | `/Applications/QGIS*.app/Contents/Resources/python`, `~/Applications/…`, Homebrew |
| Windows | `C:/OSGeo4W*/apps/qgis*/python`, `C:/Program Files/QGIS */apps/qgis*/python` |

The search patterns are written with forward slashes on every platform, because `glob` accepts them on Windows too and `os.path.normpath` produces the native separator from them. Where a glob matches several installations the newest is tried first. On Windows the matching `bin` directories are registered with `os.add_dll_directory`, without which the extension modules import but their Qt, GDAL and PROJ libraries do not - the failure that otherwise shows up as a bare `DLL load failed`.

Two environment variables override all of it:

```bash
export RIVERARCHITECT_QGIS_PATH=/path/to/dir/containing/the/qgis/package
export QGIS_PREFIX_PATH=/path/to/installation/prefix
```

The Maps tab reports what was found - the QGIS version, the bindings directory and the prefix - or, if nothing was, exactly what to install and how to point at it.

````{admonition} Why the directory is appended and not put on PYTHONPATH
:class: warning

On Debian and Ubuntu the QGIS bindings sit in `/usr/lib/python3/dist-packages` **beside the distribution's own numpy, pandas and scipy**. `PYTHONPATH` entries come *before* an environment's own `site-packages`, so

```bash
PYTHONPATH=/usr/lib/python3/dist-packages riverarchitect     # do not do this
```

silently replaces numpy 2.5 with 1.26 and pandas 3.0 with 2.1, and every analysis then runs against a different stack from the one it was tested with. That is a worse failure than no mapping, because it produces results rather than an error.

River Architect appends instead, so the environment's own packages keep priority and only the modules it genuinely does not have - `qgis` and its `PyQt5` - come from the system.
````

````{admonition} "QGIS is installed, but the Maps tab is disabled"
:class: note

This is the single most confusing state the program has, and it has one cause: the bindings are **compiled extension modules**, so they load only in the Python minor version they were built for. A distribution builds them for its *system* interpreter, and a conda environment is usually a different version. Debian 12 ships QGIS for Python 3.11, for instance, while `ra-env` is Python 3.12.

River Architect reads the ABI tag off `qgis/_core.cpython-311-*.so` before importing anything, so the Maps tab names the version it needs rather than reporting the import error that would otherwise surface - `No module named 'PyQt5.sip'`, which sends people looking for a package that is not missing. Reinstalling QGIS does not help, and neither does any amount of searching. There are two ways out.

**Install QGIS into the environment.** conda-forge builds it against the environment's own Python, so one interpreter then does everything:

```bash
mamba install -n ra-env -c conda-forge qgis
```

**Or run the maps from the interpreter QGIS was built for**, and the analyses from `ra-env`:

```bash
RA_PYTHON=/usr/bin/python3.11 ./runRiverArchitectLinux.sh
```

That interpreter usually has no rasterio, so the analysis tabs disable themselves there. The launcher warns about both situations before it opens a window.
````

```{eval-rst}
.. seealso::

   :mod:`riverarchitect.mapping` and :mod:`riverarchitect.tools` in the API reference.
```
