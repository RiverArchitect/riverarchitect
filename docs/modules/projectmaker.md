# Project Maker

{mod}`riverarchitect.projectmaker` - the **Project Maker** tab.

The last step of the chain, and the only one that produces a number a funding body
recognises: what the works cost, what they buy in habitat, and the ratio between them.

## The two halves

**Cost** is a bill of quantities. Every task in
{data}`riverarchitect.projectmaker.COST_ITEMS` carries a unit rate; the quantity comes from
what the earlier modules mapped:

| Quantity | Comes from |
|---|---|
| per-feature areas - plantings, streamwood, boulders, fine sediment | {doc}`lifespans` (Max Lifespan) |
| excavation volume and the area cleared | {doc}`morphology` (Terraforming) |
| terrain acquisition | the project area |
| everything else - culverts, roads, bridges, groin cavities | entered directly |

**Benefit** is the difference in SHArea between two conditions - the existing state and the
state with the project built - for one species and lifestage. Both come from
{meth}`riverarchitect.sharc.SHArC.run`, so the comparison is like for like.

Their ratio, **cost per unit of habitat gained**, is what lets two designs be compared when
one is cheap and small and the other expensive and large.

```python
from riverarchitect.maxlifespan import MaxLifespan
from riverarchitect.projectmaker import ProjectMaker
from riverarchitect.sharc import SHArC

maker = ProjectMaker("my_project", unit="us")
maker.quantities_from_lifespan(
    MaxLifespan("Output/MaxLifespan/2100_sample").run(),
    terraforming=terraforming_result,
    project_area=336000.0)

before = SHArC("2100_existing").run("Chinook salmon", "spawning")
after = SHArC("2100_with_project").run("Chinook salmon", "spawning")

result = maker.run(before=before, after=after)
print(result["costs"]["total"], result["cost_per_area"])
```

## The rates

The unit rates are the original's `Project_assessment_vii.xlsx`, unchanged, but held as
**Python rather than a workbook** so a change to a rate shows up in review. Several were
Excel formulas averaging a range; those are recorded as the average, with the range in the
item's `note`.

They are grouped as the workbook grouped them: *Terraforming*, *Stabilising bioengineering*,
*Vegetation plantings*, *Other bioengineering*, *Maintenance* and *Civil engineering*. Four
percentage rates then apply to the construction subtotal, **compounding in order**:

| Rate | |
|---|---:|
| Site (de-)mobilization | 10% |
| Unexpected | 10% |
| Markups (overhead, profit, insurance) | 16.5% |
| Permitting | 35% |

Each is a fraction of the running total, not of the construction subtotal, so they multiply
rather than add - on the sample reach they roughly double the figure.

```{admonition} Quantities that cannot be derived are not invented
:class: important

A rate priced per **area** follows from a feature map directly. A rate priced per **log** or
**piece** follows only through an assumption - the original's workbook divided the area by a
`log_length` of 25, taking one log to occupy that squared - and `log_length` is a parameter
here for exactly that reason.

A rate priced per **yard of bank**, per **culvert** or per **bridge** does not follow from an
area at all. Those are left empty and reported in the log rather than filled with a number
that looks authoritative and is not. Enter them yourself.
```

## Reading the result

`run()` returns the bill, the group subtotals, the applied rates, the habitat gain and the
ratio, and writes a CSV bill of quantities listing only the lines that carry a quantity.

A project that does not increase habitat area has **no** cost-benefit ratio;
`cost_per_area` is `None` and the log says so, rather than reporting a negative number that
reads like a bargain.

Comparing a condition that has no flow duration curve raises rather than returning a
half-comparison: build one first with **Get Started ▸ analyze flows**
({doc}`../getstarted/index`).

## In this section

```{toctree}
:maxdepth: 1

Project Maker: method, cost quantities and SHArea benefit (legacy) <../wiki/ProjectMaker>
```

```{eval-rst}
.. seealso::

   :mod:`riverarchitect.projectmaker` in the API reference.
```
