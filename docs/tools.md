# Tools

Section 4 of the original wiki. Utility routines that sit beside the analysis modules:
things a project needs occasionally, that do not belong in a tab.

In the original these were loose console scripts under `RiverArchitect/Tools/`, described as
"beta versions of future functionalities". In this release the ones that earned their place
are **importable modules with console-script entry points**, and the ones that were really
part of an analysis have moved into it.

```{toctree}
:maxdepth: 1
:caption: In this section

River Architect Tools (legacy) <wiki/Tools>
```

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

### Bed shear stress

```bash
riverarchitect-taux --velocity u000550.tif --depth h000550.tif --grains dmean.tif \
    --unit us --output-prefix out/q000550
```

Runs the Shields stress calculation of {mod}`riverarchitect.shear` on one set of rasters,
outside a condition folder - useful for checking model output before it is organised as a
condition, or for comparing the closure against measured stress. It writes
`<prefix>_theta84.tif`, `<prefix>_ustar2.tif`, `<prefix>_h_over_ks.tif` and
`<prefix>_regime.tif`, and prints how many cells fell into each resistance regime.

Depth and grain size are resampled onto the velocity raster's grid, so the three need not
share an extent. They **must** share a unit system, and `--unit` must name it. Pass
`--grain-kind d84` when the grain raster holds a measured $D_{84}$; the default `dmean`
estimates it as $2.2\,D_{\mathrm{mean}}$, which is what the analysis modules do.

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
is independent of the raster analysis and of `arcpy`, and has not been rewritten.
{doc}`wiki/Tools` describes it.

For a synthetic channel *geometry* rather than a design table, see **River Builder** in
{doc}`modules/morphology`, which is ported.

```{eval-rst}
.. seealso::

   :mod:`riverarchitect.tools` and :mod:`riverarchitect.flows` in the API reference.
```
