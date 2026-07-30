# Tools

Section 4 of the original wiki. Utility routines that sit beside the analysis modules:
things a project needs occasionally, that do not belong in a tab.

In the original these were loose console scripts under `RiverArchitect/Tools/`, described as
"beta versions of future functionalities". In this release the ones that earned their place
are **importable modules with console-script entry points**, and the ones that were really
part of an analysis have moved into it.

## Available now

### Reconcile NoData

```bash
riverarchitect-reconcile-nodata <condition-folder> --dry-run
riverarchitect-reconcile-nodata <condition-folder>
```

Also **Tools ▸ Reconcile NoData in a condition** in the interface.

Conditions assembled from different preprocessing chains carry inconsistent NoData
sentinels - real-world inputs mix `-999`, `-3.4e38`, `+3.4e38`, `0` and `-9999`, sometimes
within one dataset. This rewrites a folder to `config.NODATA` (-999.0).

The NoData **mask is preserved exactly**; only the sentinel changes. `--dry-run` reports what
would be rewritten without touching anything.

### lyrx2qml

```bash
riverarchitect-lyrx2qml input.lyrx output.qml
```

Converts an ArcGIS Pro layer file to a QGIS layer style, so a project that has already
invested in symbology does not have to rebuild it for {doc}`modules/maps`.

### Flow analysis

{mod}`riverarchitect.flows` replaces the original's `make_annual_flow_duration.py` and
`make_annual_peak.py`, which were console scripts with the station name and the file paths
edited into the source. It is now a module, and it is reachable from **Get Started ▸ analyze
flows** - see {doc}`getstarted/index`.

```python
from riverarchitect.flows import FlowSeries, return_periods

flows = FlowSeries("00_Flows/gauge_1969_2020.csv")

# annual maximum series, for a flood frequency analysis
peaks = flows.annual_peaks()

# Gumbel return periods, for the input_definitions.inp line
periods = return_periods(peaks, discharges=[7250, 20000, 88053])
```

`annual_peaks` prepares exactly the series the original exported for the U.S. Army Corps of
Engineers' [HEC-SSP](https://www.hec.usace.army.mil/software/hec-ssp/); `return_periods` adds
a first estimate so that a defensible starting point needs no second program. For a formal
flood frequency analysis, still use HEC-SSP or an equivalent.

### File renaming

The original's `rename_files.py` added, removed or replaced prefixes and suffixes to make
input files match the naming conventions. No replacement ships here: the conventions are
documented in {doc}`getstarted/index`, and `rename`, `mmv` or a three-line shell loop does
the job without a bespoke script.

## Not ported

**`morphology_designer.py`** (with `cHydraulic.py` and `cPoolRiffle.py`) produced design
tables for self-sustaining pool-riffle channels from cross-section-averaged hydraulics. It
is independent of the raster analysis and of `arcpy`, and has not been rewritten. The legacy
page below describes it.

For a synthetic channel *geometry* rather than a design table, see **River Builder** in
{doc}`modules/morphology`, which is ported.

## In this section

```{toctree}
:maxdepth: 1

River Architect Tools (legacy) <wiki/Tools>
```

```{eval-rst}
.. seealso::

   :mod:`riverarchitect.tools` and :mod:`riverarchitect.flows` in the API reference.
```
