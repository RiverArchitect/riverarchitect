# Map creation with QGIS

River Architect's map production runs on QGIS print layouts, driven by {mod}`riverarchitect.mapping`.

## Requirements

QGIS 3.x with its Python bindings.

```bash
sudo apt install qgis python3-qgis        # Debian, Ubuntu
```

They cannot be installed from PyPI, and a distribution installs them for the **system** interpreter rather than for the `ra-env` analysis environment. River Architect looks for them itself and adds them to the end of its module search path, so the Maps tab normally works from `ra-env` too - see *Finding QGIS* in {doc}`../modules/maps` for the search order, the `RIVERARCHITECT_QGIS_PATH` and `QGIS_PREFIX_PATH` overrides, why `PYTHONPATH` is the wrong tool for this, and what to do when the bindings were built for a different Python.

Check what the running interpreter sees:

```bash
python -c "from riverarchitect.mapping import qgis_status; print(qgis_status()[1])"
```

`mapping` sets `QT_QPA_PLATFORM=offscreen` itself, so it renders headless without a display.

## Layout

The layout is composed programmatically in `Mapper.build_layout()`, so no binary template is needed. It contains a map frame, a legend filtered to the visible layers, a scale bar, a north arrow, a title, and a footer carrying `condition` and `page N of M`. The project itself is written to `02_Maps/<condition>/maps_<condition>_design.qgz`, so a finished map series can be reopened and edited in QGIS.

Default page size is ANSI E landscape (1117.6 x 863.6 mm). Override per instance with `mapper.page_size = (width_mm, height_mm)`.

If `templates/river_template.qgz` exists it is used as the starting project instead, so a hand-built QGIS template can carry house styling, base layers or a custom layout.

## Page series

A multi-page reach series is a QGIS **atlas**: a coverage layer holds one rectangle per page, the map frame is marked atlas-driven, and `QgsLayoutExporter.exportToPdf` writes every page in one operation. There is no per-page temporary file and no document stitching.

## Symbology

Styles are read from the packaged symbology directory (`riverarchitect/templates/symbology/<name>.qml`). `Mapper.choose_ref_layer()` maps a raster name onto a style name (`lf_sym`, `ds_sym`, ...).

The published lifespan symbology carries nine lifespan classes on a red-to-green ramp, with NoData transparent. To restyle, open a map in QGIS, edit the layer's symbology, and save it over the corresponding `.qml`.

An existing ArcGIS Pro `.lyrx` can be converted rather than rebuilt. `.lyrx` is JSON (Esri CIM), so class breaks, colours and labels convert exactly:

```bash
python -m riverarchitect.tools.lyrx2qml LifespanRasterSymbology.lyrx
```

The converter handles `CIMRasterClassifyColorizer` (to `singlebandpseudocolor`, DISCRETE) and `CIMRasterUniqueValueColorizer` (to `paletted`), and converts RGB, HSV, CMYK and gray CIM colours.

When no `.qml` matches, the layer keeps QGIS defaults and a warning is logged; maps are still produced, just unstyled.

## API

```python
from riverarchitect.mapping import Mapper

mapper = Mapper(condition, "lf")               # or "ds", "mlf", "mt"
mapper.prepare_layout(True, map_items=[...])   # True -> export immediately
mapper.make_pdf_maps("lf_grains", extent="raster")
if not mapper.error:
    ...
```

`extent` accepts `"raster"` (use the mapped raster's extent), `"MAXOF"`, or `[xmin, ymin, xmax, ymax]`. For a multi-page series, set `mapper.xy_center_points` to a list of `[x, y]` page centres together with `mapper.dx` and `mapper.dy`.

Paths are built with `os.path`, so the same code runs on Linux, macOS and Windows and no separator is ever written literally. The Mapping tab of the graphical interface drives the same API.

## Verification

Exercised end to end against `sample-data/01_Conditions/2100_sample` on Linux:

- single-raster map: 1-page PDF, 3168 x 2448 pt (ANSI E landscape), 192 dpi
- three-window reach series: 3-page PDF from one atlas export
- `.qgz` project and per-layer `.qml` written alongside the PDFs
- rendered pages checked visually: title, map, north arrow, legend with all nine lifespan classes, scale bar, no overlap; NoData transparent

## Known gaps

- Only the lifespan raster symbology ships as a converted style. Design-stage (`ds_sym`) and Max Lifespan styles fall back to QGIS defaults until `.qml` files are supplied.
