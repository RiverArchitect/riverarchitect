# River design and restoration features

The catalogue of restoration features that {doc}`lifespans` maps, what each one is, and where its default thresholds come from. The defaults live in {data}`riverarchitect.lifespan.FEATURES` as Python, so they can be read, diffed and reviewed like any other code.

Every threshold is optional. A criterion whose threshold is unset, or whose input raster the condition does not have, is **skipped** rather than failed - which is why a sparsely defined feature still produces a useful map, and why a map that comes out emptier than expected is usually a missing input rather than a bug.

## Feature groups

| Group | What the features do |
|---|---|
| **Terraforming** | change the terrain elevation: backwaters, widening, grading, side cavities, side channels |
| **Vegetation plantings** | cuttings of a named species, judged on whether they survive their first floods |
| **Established vegetation** | the same species once grown in, with the same thresholds but a different planning question |
| **Nature-based engineering** | living and mineral material that stabilises a terrain change and adds habitat: streamwood, boulders, fascines |
| **Connectivity** | measures that keep an engineered reach supplied and functioning: gravel augmentation, fine sediment |

Feature ids are short because they name output files: `lf_<fid>.tif` for a lifespan map and `ds_<fid>.tif` for a design map.

## The defaults

Thresholds are in the condition's own unit system. The shipped values are U.S. customary, as measured on a gravel-cobble reach in Northern California, and are a starting point rather than a recommendation for another river.

### Terraforming

| Feature | id | Criteria |
|---|---|---|
| Backwater | `backwt` | $\tau_{*,cr}$ 0.047, $u \le$ 0.1 fps, scour and fill 0.3 ft, 5-year design flood, restricted to agriplain, backswamp, mining pit, pond, slackwater |
| Widen | `widen` | detrended DEM 17 to 25 ft, restricted to bank, floodplain, high floodplain, island-floodplain, island high floodplain, in-channel bar, lateral bar, levee, spur dike, terrace; design map only |
| Grading | `grade` | $\tau_{*,cr}$ 0.047, `d2w` 7 to 12 ft, scour below 0.3 ft, avoiding bedrock and hillside |
| Side cavities | `sideca` | fill below 1.0 ft, restricted to bank, cutbank, in-channel bar, lateral bar, spur dike, tailings; design map only |
| Side channels | `sidech` | $\tau_{*,cr}$ 0.047, fill below 1.0 ft |

**Backwater** creates swales, slackwaters and other calm-water zones. They belong where stream power is low and observed topographic change is small, so the velocity threshold is very low and the morphological units are the still ones.

**Widen** removes a lateral confinement - a man-made bar or dike - which is a river widening rather than a demolition. Levees are in the relevant units because they are lateral confinement, but a levee with a live flood-protection function is not a setback candidate; that judgement is not in the raster. The detrended-DEM band keeps the measure within economically plausible terrain.

**Grading** reconnects high floodplains and isolated islands by lowering them. It is wanted where plantings cannot reach the water table and where even high flows cannot rework the channel, so its topographic-change criterion is **inverted**: the areas of interest are those where the scour threshold is *not* exceeded.

**Side cavities** are bank scallops or groin fields that create preservable habitat and can protect a bank. The fill criterion is likewise inverted: a cavity that silts up is ecologically pointless.

**Side channels** cover anabranches, anastomosed and multithread channels and flood runners. There is no reliable raster criterion for where a side channel belongs: identifying splays and judging bank rigidity needs a person looking at the reach. Supply a `sidech.tif` mask of candidate areas beside the condition and the feature is evaluated inside it. Van Denderen et al. (2017) give the criteria worth drawing to:

* intakes sit at river splays, downstream of inside bends at the inner bank, or in outer bends at the outer bank;
* the bifurcation angle between main and side channel axes is 40° to 50°;
* the side channel's slope is at most the main channel's;
* its length is slightly greater than the main channel's between bifurcation and confluence;
* its banks are stabilised with plantings or streamwood.

Draw those areas as polygons in QGIS with an integer field set to 1, then rasterise them onto the condition's grid - **Raster ▸ Conversion ▸ Rasterize**, or {func}`riverarchitect.raster.rasterize` - and save the result as `sidech.tif`.

```{admonition} The energy-slope approach does not work, and it is worth knowing why
:class: note

Comparing the minimum energy slope $S_{e,min}$ against the terrain slope $S_0$ looks like it should identify erosion and deposition, with $H_{min} = 1.5(q^2/g)^{1/3}$ at $Fr = 1$. It does not, because a 2D model that uses critical depth as a stability criterion drives $S_{e,min}$ towards $S_0$, so the ratio is approximately unity everywhere and carries no information. This is why `sidech.tif` is a manual input.
```

### Vegetation plantings and established vegetation

| Feature | id | Criteria |
|---|---|---|
| Generic planting | `Generic` / `Generic_est` | $\tau_{*,cr}$ 0.06 |
| Box Elder (*Acer negundo*) | `box` / `Box_est` | $\tau_{*,cr}$ 0.06, $h \le$ 1 ft, `d2w` 1 to 7 ft |
| Cottonwood (*Populus fremontii*) | `cot` / `cot_est` | $h \le$ 2.1 ft, $u \le$ 3 fps, `d2w` 1 to 7 ft |
| White Alder (*Alnus rhombifolia*) | `whi` / `Whi_est` | $\tau_{*,cr}$ 0.06, `d2w` 1 to 7 ft |
| Willow (*Salix* spp.) | `wil` / `Wil_est` | $\tau_{*,cr}$ 0.1, $h \le$ 2.1 ft, `d2w` 1 to 7 ft |

The shipped species are native to Northern California; substitute your own. Plantings produce lifespan maps only - the lifespan map *is* the answer to where a species is sustainable, so there is no separate design map.

The analysis assumes cuttings about 2.1 m (7 ft) long with roughly 80 % of that in the ground. The depth-to-water-table bands are the ones observed in the field, and they are narrower than the full range each species tolerates:

* **Box Elder** survives burial, which is why no topographic-change rate applies, but not prolonged submergence - Friedman and Auble (1999) report a limit near 85 consecutive days, worth checking against your flow duration curve. Reported `d2w` range 0.6 to 4.6 m (Stella et al. 2003).
* **Cottonwood** is the one with a velocity criterion: uprooting has been reported from about 0.9 to 1.2 m/s (Stromberg et al. 1993, Wilcox and Shafroth 2013, Bywater-Reyes et al. 2015). Scour thresholds in the literature range from 0.1 to 0.5 times root depth, and fill from about 0.8 times seedling length.
* **White Alder** tolerates a scour rate near 0.3 m (Jablkowski et al. 2017); reported `d2w` 0.9 to 1.5 m for seedlings and up to 5 m for grown trees.
* **Willow** carries the highest critical shear stress of the four once rooted deeper than about 0.5 m (Pasquale et al. 2014).

```{admonition} Sand-bed thresholds need a safety factor on gravel
:class: warning

Several of the plant-stability studies were done on sand-bed rivers, where scour depths are reached more easily and root-plant contact surfaces are larger. Applying those scour thresholds to a gravel or cobble bed overestimates stability by a factor of 2 to 4 (Politti et al. 2018). Adjust the rate rather than trusting the default.
```

For species elsewhere, The Nature Conservancy's [plant rooting depth database](https://groundwaterresourcehub.org/gde-tools/gde-rooting-depths-database-for-gdes) and the national flora databases (Calflora, Info Flora, FloraWeb, Flora Iberica, GBIF and their equivalents) are the usual sources for the `d2w` band.

### Nature-based engineering

| Feature | id | Criteria |
|---|---|---|
| Streamwood | `wood` | $h \le$ 3.34 ft, $Fr \le$ 1.0, 10-year design flood |
| Angular boulders | `rocks` | $\tau_{*,cr}$ 0.047, safety factor 1.3, scour 3 ft, 20-year design flood |
| Other nature-based eng. | `bio` | `d2w` up to 12 ft, terrain slope 0.2 |

**Angular boulders** covers both the placement of rock and the mobility of the bed already there. Run against the condition's own `dmean.tif` it maps how stable the present grain size is; its design map gives the diameter that would stay put at the design flood. That diameter comes from a Gauckler-Manning-Strickler rearrangement, {meth}`riverarchitect.lifespan.LifespanDesign.critical_grain_size`:

$$
D_{cr} = \frac{SF\,u^2 n^2}{(s-1)\,h^{1/3}\,\tau_{*,cr}}
$$

with $s = 2.68$ the relative grain density, $n$ Manning's roughness (settable in the interface and as `manning_n`; the U.S. customary conversion factor of 1.49 is applied internally) and $SF$ the safety factor. Both the safety factor and a partial scour raster move this result a long way - if a design map looks implausible, drop each in turn and see which one did it.

**Streamwood** covers large woody material and engineered log jams. The depth threshold is about 1.7 times the log diameter (Lange and Bezzola 2005) and the Froude limit is 1.0. The design map gives the minimum stable log diameter from the Ruiz-Villanueva et al. (2016) single-thread relation, $D_w = 0.32 / 0.18\,h$, which is the conservative branch. Riffle-pool and plane-bed morphologies suit wood placement; tributary channels and deltas do not.

**Other nature-based engineering** is the fascine, brush-layer and geotextile family. It applies between the minimum and maximum depth to the water table, because these features dry out when the table is too far below them. Where the terrain slope exceeds the threshold *and* the water table is deeper than the maximum, the answer is mineral instead - rock paving or riprap sized as an angular-boulder problem. The slope is computed from `dem.tif`.

### Connectivity

| Feature | id | Criteria |
|---|---|---|
| Gravel: In | `gravin` | $\tau_{*,cr}$ 0.047, 10-year design flood, in-channel morphological units |
| Gravel: Out | `gravou` | $\tau_{*,cr}$ 0.047, scour 3 ft, 1-year design flood, bank and floodplain units |
| Incorporation of fine sediment | `fines` | $\tau_{*,cr}$ 0.03, `d2w` 1 to 10 ft, grain size up to 0.0067 ft, scour 3 ft, fill 3.36 ft |

**Gravel augmentation** comes in two forms, and their lifespan maps are read in *opposite* directions. Injections in the main channel (`gravin`) aim to create spawning habitat that should not wash out at the next minor flood, so a **high** lifespan is what you want. Stockpiles on banks and floodplains (`gravou`) are meant to be entrained by frequent floods and feed the sediment budget, so a **low** lifespan is the good outcome. That is why they carry the same critical shear stress but design floods of 10 and 1 year, and different sets of morphological units.

**Fine sediment** is incorporated into soils so new plantings can root. Its thresholds are deliberately the *largest* that any planting species supports, since only areas where some planting is viable are worth treating. The maximum grain size is sand, 2 mm (0.08 in). The design map applies the USACE (2000) filter criteria, so introduced fines do not simply percolate into the voids of the coarser bed:

$$
D_{15,fine} > \frac{D_{15,coarse}}{20}, \qquad
D_{85,fine} > \frac{D_{15,coarse}}{5}, \qquad
D_{max,fine} < 2\ \text{mm}
$$

with $D_{15,coarse}$ taken as $0.25\,D_{mean}$.

## Morphological unit criteria

A feature can be restricted to the units where it makes sense (`mu_relevant`, the inclusive method) or excluded from the ones where it does not (`mu_avoid`, the exclusive method). `mu_method` picks which applies. The classification follows Wyrick and Pasternack (2014):

| | | | |
|---|---|---|---|
| agriplain | backswamp | bank | bedrock |
| chute | cutbank | fast glide | flood runner |
| floodplain | high floodplain | hillside | in-channel bar |
| island-floodplain | island high floodplain | lateral bar | levee |
| medial bar | mining pit | point bar | pond |
| pool | riffle | riffle transition | run |
| slackwater | slow glide | spur dike | swale |
| tailings | terrace | tributary channel | tributary delta |

The floodplain units in the lower half of that list carry a code but no depth or velocity range, so they can be used as a criterion but cannot be *assigned* by {func}`riverarchitect.preprocessing.morphological_units`. {meth}`riverarchitect.preprocessing.MorphologicalUnits.classifiable` is the subset that can.

Units named in a feature but absent from the code table produce a warning naming them, and the criterion continues with the ones it does recognise.

## Customising

For a one-off change, edit {data}`riverarchitect.lifespan.FEATURES` or build a {class}`riverarchitect.lifespan.Feature` and pass it in:

```python
from riverarchitect.lifespan import Feature, FEATURES, LifespanDesign

features = dict(FEATURES)
features["myrock"] = Feature("myrock", "Local quarry rock", "Nature-based engineering",
                             tau_cr=0.047, safety_factor=1.5, design_frequency=50,
                             design_mapping=True)

LifespanDesign("2100_sample", unit="us", features=features).run(["myrock"])
```

For a project-specific set that travels with the project rather than the code, keep a `threshold_values.xlsx` and read it with {func}`riverarchitect.lifespan.load_threshold_workbook`.

```{admonition} Length thresholds in the workbook are unconverted
:class: warning

The workbook holds U.S. customary numbers and they are applied as they are. This looks like a missing unit conversion and is not one: the original multiplied by `ft2m` on reading and divided by it again on use, so the two cancelled. {data}`riverarchitect.lifespan.FEATURES` holds the same numbers for the same reason.
```

A new *kind* of criterion - not a new threshold on an existing one - needs code in {mod}`riverarchitect.lifespan`. {doc}`../development/index` describes what a module and a criterion consist of.

## References

Bywater-Reyes, S. et al. (2015). *Water Resources Research* 51. [doi:10.1002/2014WR016641](http://dx.doi.org/10.1002/2014WR016641) · Friedman, J.M. and Auble, G.T. (1999). *Regulated Rivers* 15. [doi:10.1002/(SICI)1099-1646(199909/10)15:5<463::AID-RRR559>3.0.CO;2-Z](http://dx.doi.org/10.1002/(SICI)1099-1646(199909/10)15:5<463::AID-RRR559>3.0.CO;2-Z) · Jablkowski, T. et al. (2017). *Geomorphology* 291. [link](http://www.sciencedirect.com/science/article/pii/S0169555X1730274X) · Kui, L. and Stella, J.C. (2016). *Forest Ecology and Management* 366. [link](http://www.sciencedirect.com/science/article/pii/S0378112716300123) · Lange, D. and Bezzola, G.R. (2005). *VAW-Mitteilung* 188, ETH Zurich. [pdf](https://www.ethz.ch/content/dam/ethz/special-interest/baug/vaw/vaw-dam/documents/das-institut/mitteilungen/2000-2009/188.pdf) · Maynord, S.T. and Neill, C.R. (2008). *Sedimentation Engineering*, ASCE. [doi:10.1061/9780784408148.apb](https://ascelibrary.org/doi/10.1061/9780784408148.apb) · Pasquale, N. et al. (2014). *Hydrological Processes* 28. [doi:10.1002/hyp.9993](http://dx.doi.org/10.1002/hyp.9993) · Pasternack, G.B. et al. (2010). *California Agriculture* 64. [link](http://calag.ucanr.edu/archive/?article=ca.v064n02p69) · Politti, E. et al. (2018). *Earth-Science Reviews* 176. [link](https://www.sciencedirect.com/science/article/pii/S0012825217301186) · Polzin, M.L. and Rood, S.B. (2006). *Wetlands* 26. [link](https://link.springer.com/article/10.1672/0277-5212(2006)26%5B965:EDSSSA%5D2.0.CO;2) · Rickenmann, D. and Recking, A. (2011). *Water Resources Research* 47. [doi:10.1029/2010WR009793](https://doi.org/10.1029/2010WR009793) · Ruiz-Villanueva, V. et al. (2016). *Geomorphology* 269. [link](https://www.sciencedirect.com/science/article/pii/S0169555X15002019) · Schwindt, S. et al. (2019). *Journal of Environmental Management* 232. [link](https://www.sciencedirect.com/science/article/pii/S0301479718312751) · Stella, J.C. et al. (2003). Stillwater Sciences. [pdf](http://www.stillwatersci.com/resources/2003stellaetal.pdf) · Stromberg, J.C. et al. (1993). *Journal of the Arizona-Nevada Academy of Science* 26. [link](http://www.jstor.org/stable/41712765) · USACE (2000). *EM 1110-2-1913*. [pdf](https://www.publications.usace.army.mil/Portals/76/Publications/EngineerManuals/EM_1110-2-1913.pdf) · van Denderen, R.P. et al. (2017). *Earth Surface Processes and Landforms* 42. [doi:10.1002/esp.4267](https://onlinelibrary.wiley.com/doi/full/10.1002/esp.4267) · Weber, M.D. and Pasternack, G.B. (2017). *Geomorphology* 288. [link](http://www.sciencedirect.com/science/article/pii/S0169555X16309862) · Wilcox, A.C. and Shafroth, P.B. (2013). *Water Resources Research* 49. [doi:10.1002/wrcr.20256](http://dx.doi.org/10.1002/wrcr.20256) · Wyrick, J.R. and Pasternack, G.B. (2014). *Geomorphology* 213. [link](https://www.sciencedirect.com/science/article/pii/S0169555X14000099)
