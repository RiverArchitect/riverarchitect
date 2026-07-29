# Development

How River Architect is put together, and what adding to it involves.

## Principles

Development follows the *Zen of Python*
([PEP 20](https://www.python.org/dev/peps/pep-0020/)) - in particular *explicit is better
than implicit*, *flat is better than nested*, and *errors should never pass silently*. The
third one is not decoration here: the ArcGIS original wrapped most of its analysis in bare
`except` blocks, and the criteria that quietly disappeared inside them are exactly the
defects this rewrite had to find.

Two invariants matter more than any style rule, because they are the two ways raster code
silently produces *wrong results* rather than errors:

**NoData is `numpy.nan` in memory.** Read through {func}`riverarchitect.raster.read`, which
applies the declared mask. Never compare cell values against a sentinel: real inputs carry
`-999`, `-3.4e38`, `3.4e38`, `0` and `-9999` interchangeably, sometimes within one dataset.
`config.NODATA` is what we *write*, never what we test against.

**Alignment is explicit.** `arcpy.env.extent` silently reconciled operands of differing
extent; numpy does not - it either raises or broadcasts into nonsense. Call
{func}`riverarchitect.raster.align` before combining rasters that do not provably share a
grid. Real DEM and depth rasters routinely differ.

Also: {func}`riverarchitect.raster.con` with two arguments yields NoData on the false
branch, matching two-argument `arcpy.sa.Con`. Passing `0` instead creates wetted-area
artefacts.

## Adding a module

A module is five things, in this order. The chain is the same whether you are adding a whole
analysis or extending one.

### 1. The analysis, as a plain module

`src/riverarchitect/<name>.py`, importable and usable without any interface. It takes a
{class}`riverarchitect.condition.Condition` or explicit paths, returns a summary dict, and
writes its rasters where the caller asks. No global state, no working-directory changes, no
`print`.

Log through the `riverarchitect` logger so a caller decides what is visible:

```python
import logging
logger = logging.getLogger("riverarchitect")
```

Add it to the lazy import list in `src/riverarchitect/__init__.py`, so a missing optional
dependency only breaks the module that needs it:

```python
def __getattr__(name):
    if name in (..., "yourmodule"):
        ...
```

### 2. Tests

`tests/test_<name>.py`, with `tmp_path` fixtures that synthesise GeoTIFFs. The suite needs no
external data and runs in about ten seconds.

Assert against **analytically exact** answers where the maths allows it - the volume tests
check flat and tilted planes, clipping, anisotropic cells and a draped area of 100·√2. A test
that merely records current output is much weaker: it locks in whatever the code does today,
including its bugs.

For anything spatial, check the result on the real sample condition as well
({doc}`../guide/example_walkthrough`). The unit tests use synthetic rasters and will not
catch a fidelity gap.

### 3. A tab in both front ends

`src/riverarchitect/gui/qt/<name>_tab.py` and `src/riverarchitect/gui/<name>_tab.py`.
Subclass `RaTab` (Qt) or `RaModuleGui` (tkinter), set `title` and, for Qt, `subtitle`.

Register it in **both** `TAB_GROUPS` declarations - `gui/qt/main.py` and `gui/main.py`:

```python
TAB_GROUPS = (
    ("Get Started", (GetStartedTab,)),
    ("Lifespan", (LifespanTab, MaxLifespanTab)),
    ("Morphology", (TerraformingTab, VolumeTab)),
    ("Ecohydraulics", (SharcTab, StrandingTab, RecruitmentTab)),
    ("Maps", (MappingTab,)),
)
```

A test asserts the two stay identical, so they cannot drift apart. A group of one renders as
a plain tab; a group of several nests.

Long work goes on a thread and marshals its result back to the interface thread -
`run_in_background()` in Qt, `widget.after(0, ...)` in tkinter. A tab that needs a dependency
the environment may lack should disable itself with an explanation rather than fail when the
user clicks *Run*; `mapping_tab` is the model for that.

```{admonition} Prefer a product over a tab where one fits
:class: tip

Anything that prepares a condition belongs in
{data}`riverarchitect.preprocessing.PRODUCTS` rather than in a new tab. Both front ends
render that tuple, so an entry there appears in the interface on both without either being
touched - which is how *analyze flows* was added.
```

### 4. Documentation

* an API page, `docs/api/<name>.rst`, added to `docs/api/index.rst`;
* a section in the module page it belongs to under `docs/modules/`;
* a step in {mod}`riverarchitect.guide` if it is part of the standard chain - both front ends
  render that tuple, and a test checks every step names a tab that exists.

Keep the docs build at **zero warnings**:

```bash
python -m sphinx -b html -W docs docs/_build/html
```

`toc.not_included` is deliberately not suppressed: a page in no toctree is a page nobody can
reach, and that is how stale documentation accumulates.

### 5. The changelog

`CHANGELOG.md`, under `## [Unreleased]`. It is rendered by GitHub and copied verbatim into
the release notes, so write plain Markdown there rather than the MyST directives the rest of
the documentation uses.

## Conventions

**Google-style docstrings**; `napoleon` renders them. Public functions carry their `arcpy`
counterpart in the docstring where one exists, because that is how users coming from the
original will search.

**Say why, not what.** A comment that restates the code is noise; a comment explaining why a
two-argument `con` is used, or why a directory is appended rather than prepended to
`sys.path`, is what stops the next person from "fixing" it.

**Lookup tables stay diffable** where they can. Feature thresholds live in
{data}`riverarchitect.lifespan.FEATURES` as Python rather than in a binary workbook, so a
change to them shows up in review. Tables that genuinely have to stay binary - `Fish.xlsx`,
`morphological_units.xlsx`, `recruitment_parameters.xlsx` - are packaged under
`src/riverarchitect/templates/`.

## The layout

```text
src/riverarchitect/
├── raster.py            the core: I/O, alignment, map algebra, interpolation,
│                        connectivity, zonal statistics
├── condition.py         a condition folder and its input_definitions.inp
├── preprocessing.py     GetStarted: the terrain products everything else reads
├── flows.py             seasonal flow duration curves, annual peaks, return periods
├── lifespan.py          LifespanDesign          maxlifespan.py   MaxLifespan
├── terraforming.py      ModifyTerrain           volume.py        volume integration
├── sharc.py             SHArC                   volume_assessment.py
├── stranding.py         StrandingRisk           recruitment.py   RiparianRecruitment
├── mapping.py           QGIS print layouts, the only module that imports QGIS
├── guide.py             the Live Guide, as data both front ends render
├── config.py            paths, units, NODATA
├── gui/                 tkinter front end, and gui/qt/ the Qt one
├── templates/           packaged workbooks and QGIS layer styles
└── tools/               reconcile_nodata, lyrx2qml
```

`raster.py` is the foundation - it is the open-source replacement for arcpy's raster algebra,
and nearly everything else builds on it. `volume.py` is pure numpy with no I/O.
`mapping.py` keeps QGIS behind a guarded import and must go on degrading gracefully without
it.

## Contributing

New code goes to <https://github.com/RiverArchitect/riverarchitect>. `CONTRIBUTING.md` in the
repository covers the branch and pull-request workflow, and `CODE_OF_CONDUCT.md` the
expectations for participation.

Before opening a pull request:

```bash
pytest                                            # the full suite
python -m sphinx -b html -W docs docs/_build/html # zero warnings
```

## In this section

```{toctree}
:maxdepth: 2

../guide/arcpy_migration
../api/index
```
