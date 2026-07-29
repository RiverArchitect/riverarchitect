# Project Maker

Generates preliminary construction plans and evaluates **cost against gain in usable
habitat**: a unit-cost workbook supplies the rates, the terraforming and planting extents
supply the quantities, and the SHArea difference between the existing and the
with-implementation condition supplies the benefit. Their ratio is the metric that defines
the project trade-off.

```{admonition} Not ported to the open-source release
:class: caution

**Project Maker has no module and no tab in this version.** It is the last part of the
ArcGIS original that has not been rewritten, along with River Builder (see
{doc}`morphology`).

Nothing about it needs `arcpy` in principle - it is spreadsheet arithmetic over rasters this
package already produces - so it is a rewrite waiting to be done rather than a blocked one.
The pieces it would build on all exist:

* **cost quantities** come from areas and volumes, which
  {mod}`riverarchitect.terraforming`, {mod}`riverarchitect.volume_assessment` and
  {mod}`riverarchitect.maxlifespan` already report;
* **habitat benefit** is the SHArea difference between two conditions, which
  {meth}`riverarchitect.sharc.SHArC.run` already returns.

Until then, the two halves can be computed directly and divided. The legacy page below
documents the method, the workbook layout and the cost categories in full, and the original
`arcpy` source is in `ProjectMaker/` of River Architect 1.4.
```

## Computing the trade-off by hand

```python
from riverarchitect.sharc import SHArC

before = SHArC("2100_existing").run("Chinook salmon", "spawning")
after = SHArC("2100_with_project").run("Chinook salmon", "spawning")
gain = after["sharea"] - before["sharea"]        # square feet of seasonal habitat
```

Pair that with the excavation volume from {doc}`morphology` and the per-feature areas from
{doc}`lifespans`, apply your own unit rates, and the ratio is what Project Maker would have
reported.

## In this section

```{toctree}
:maxdepth: 1

Project Maker: method, cost quantities and SHArea benefit (legacy) <../wiki/ProjectMaker>
```
