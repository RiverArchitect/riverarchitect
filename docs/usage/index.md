# Usage (Quick Start)

How to actually run River Architect, once {doc}`../setup/index` is done. Three ways in,
depending on what you want:

| Start here | If you want |
|---|---|
| {doc}`../guide/example_walkthrough` | to run the whole chain on the sample reach, module by module, with the numbers each step should produce |
| {doc}`../guide/quickstart` | to call the modules from Python and see the API in a page |
| {doc}`../guide/gui` | to know what each tab, field and menu does |

```{admonition} The interface can walk you through it
:class: tip

**Help ▸ Live Guide: Example** opens the same walkthrough *inside* the program. It sets the
project directory to the sample data, and each step brings the tab it talks about to the
front, so you read and click in the same window.
```

## The order the modules go in

This is the one thing worth knowing before anything else. The modules chain, and the step
people get stuck on is the first one: a condition that has not been prepared produces either
an error or - worse - an empty map that looks like an answer.

```text
  Get Started      prepare the condition          detrended DEM, water surface,
       |                                          d2w, morphological units,
       |                                          flow duration curves
       v
  Lifespan         how long does each feature     lf_<feature>.tif
       |           survive at each cell?          ds_<feature>.tif
       v
  Max Lifespan     which feature belongs here?    max_lf.tif, best_<feature>.tif
       |
       +--------> Morphology     lower the terrain where plantings
       |                         cannot reach the water table, and
       |                         quantify the earthworks
       |
       +--------> Ecohydraulics  habitat area, stranding risk,
       |                         riparian recruitment
       |
       v
  Maps             PDF map series through QGIS print layouts
```

The three ecohydraulic analyses are independent of one another, but all of them need the
prepared condition. Habitat area additionally needs a flow duration curve, which *Get
Started* builds from a daily flow record.

## Units

Set the unit system before anything else, from the **Units** menu or the `unit` argument.
It does **not** convert your rasters - it states what they already are. A mismatch does not
raise an error anywhere in the chain; it silently applies metric thresholds to data in feet.

## In this section

```{toctree}
:maxdepth: 2

../guide/example_walkthrough
../guide/quickstart
../guide/gui
../guide/tutorial
```
