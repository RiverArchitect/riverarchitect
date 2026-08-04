# Tools

Utility routines that sit beside the analysis modules: things a project needs occasionally, that do not belong in a tab. Each is an importable module with a console-script entry point, and two of them also have an entry in the interface's **Tools** menu.

## Pool-riffle designer

```bash
riverarchitect-pool-riffle --d50 0.0914 --slope 0.004 --width 24 --pool-depth 0.915
riverarchitect-pool-riffle --d50 0.3 --slope 0.004 --width 79 --pool-depth 3 --unit us
```

Also **Tools ▸ Pool-riffle designer** in the interface.

Sizes a pool-riffle sequence that maintains itself. A sequence survives when the flow **reverses**: at low flow the riffle is faster, but as discharge rises the pool accelerates past it, scouring itself out and depositing on the riffle. Without that reversal the pool fills in within a few floods. Caamano et al. (2009) give the geometric condition,

$$
\frac{B_r}{B_p} - 1 > \frac{\Delta z}{h_r}
$$

and {mod}`riverarchitect.poolriffle` sizes a sequence that satisfies it: the **reversal discharge** from the Shields criterion, the **pool spacing** as a multiple of bankfull width after Thompson (2013), and the **pool and riffle base widths** that produce a target residual pool depth at that discharge.

The calculation is one-dimensional and cross-section-averaged - it takes a channel, not a raster - which is why it is a tool rather than a module tab. Its natural companion is **River Builder** in {doc}`modules/morphology`, which generates the valley these dimensions go into.

The answer is sensitive to Manning's `n`, which nobody measures directly, so `--roughness all` runs the design once per published estimate (Strickler, Meyer-Peter and Mueller, Rickenmann and Recking) and `--csv` writes the comparison out. Read that spread rather than one figure from one closure:

```bash
riverarchitect-pool-riffle --d50 0.0914 --slope 0.004 --width 24 --pool-depth 0.915 \
    --roughness all --csv pool_riffle.csv
```

From Python, {func}`riverarchitect.poolriffle.design_pool_riffle` returns every quantity as a named tuple, alongside `converged` and `caamano_satisfied` - the two flags that separate a design from a set of numbers that merely look like one:

```python
from riverarchitect.poolriffle import design_pool_riffle, format_design

design = design_pool_riffle(d50=0.0914, slope=0.004, base_width=24.0,
                            target_residual_depth=0.915, bank_slope=2.58)
print(format_design(design))
print(design.reversal_discharge, design.caamano_satisfied)
```

```{admonition} A pool-riffle sequence is not the bed form at every slope
:class: warning

Above about 2 % the expected morphology is step-pool or cascade, not pool-riffle, and a sequence sized here would not be a stable one. The calculation says so and continues, because the bound is a rule of thumb rather than a hard boundary - but a design past it needs a reason.
```

## Reconcile NoData

```bash
riverarchitect-reconcile-nodata <condition-folder> --dry-run
riverarchitect-reconcile-nodata <condition-folder>
```

Also **Tools ▸ Reconcile NoData in a condition** in the interface.

Conditions assembled from different preprocessing chains carry inconsistent NoData sentinels - real-world inputs mix `-999`, `-3.4e38`, `+3.4e38`, `0` and `-9999`, sometimes within one dataset. This rewrites a folder to `config.NODATA` (-999.0).

The NoData **mask is preserved exactly**; only the sentinel changes. `--dry-run` reports what would be rewritten without touching anything.

## Bed shear stress

```bash
riverarchitect-taux --velocity u000550.tif --depth h000550.tif --grains dmean.tif \
    --unit us --output-prefix out/q000550
```

Runs the Shields stress calculation of {mod}`riverarchitect.shear` on one set of rasters, outside a condition folder - useful for checking model output before it is organised as a condition, or for comparing the closure against measured stress. It writes `<prefix>_theta84.tif`, `<prefix>_ustar2.tif`, `<prefix>_h_over_ks.tif` and `<prefix>_regime.tif`, and prints how many cells fell into each resistance regime.

Depth and grain size are resampled onto the velocity raster's grid, so the three need not share an extent. They **must** share a unit system, and `--unit` must name it. Pass `--grain-kind d84` when the grain raster holds a measured $D_{84}$; the default `dmean` estimates it as $2.2\,D_{\mathrm{mean}}$, which is what the analysis modules do.

## lyrx2qml

```bash
riverarchitect-lyrx2qml input.lyrx output.qml
```

Converts an ArcGIS Pro layer file to a QGIS layer style, so a project that already has symbology does not have to rebuild it for {doc}`modules/maps`.

## Flow analysis

{mod}`riverarchitect.flows` turns a daily flow record into seasonal flow duration curves, annual peaks and Gumbel return periods. It is reachable from **Get Started ▸ analyze flows** - see {doc}`getstarted/index` - and directly as a module:

```python
from riverarchitect.flows import FlowSeries, return_periods

flows = FlowSeries("00_Flows/gauge_1969_2020.csv")

# annual maximum series, for a flood frequency analysis
peaks = flows.annual_peaks()

# Gumbel return periods, for the input_definitions.inp line
periods = return_periods(peaks, discharges=[7250, 20000, 88053])
```

`annual_peaks` prepares the annual maximum series a flood frequency analysis needs, in the form the U.S. Army Corps of Engineers' [HEC-SSP](https://www.hec.usace.army.mil/software/hec-ssp/) expects; `return_periods` adds a first estimate so a defensible starting point needs no second program. For a formal flood frequency analysis, still use HEC-SSP or an equivalent.

## File renaming

There is no renaming tool. The naming conventions are documented in {doc}`getstarted/index`, and `rename`, `mmv` or a three-line shell loop does the job without a bespoke script.

```{eval-rst}
.. seealso::

   :mod:`riverarchitect.tools`, :mod:`riverarchitect.poolriffle` and
   :mod:`riverarchitect.flows` in the API reference.
```
