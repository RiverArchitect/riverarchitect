# Modules

Section 3 of the original wiki: the analyses themselves, in the order a project runs them.

| Group | Modules | Answers |
|---|---|---|
| {doc}`lifespans` | Lifespan Design, Max Lifespan | how long does a restoration feature survive here, and which feature belongs here? |
| {doc}`morphology` | Terraforming, Volume Assessment | what terrain change does the design need, and how much earth is that? |
| {doc}`ecohydraulics` | SHArC, Stranding Risk, Riparian Seedling Recruitment | what is it worth ecologically? |
| {doc}`maps` | Mapping | how does it get onto paper? |
| {doc}`projectmaker` | Project Maker | what does it cost per unit of habitat gained? |

All of them read a **condition** prepared by {doc}`../getstarted/index`, and all of them are
ordinary Python modules as well as tabs - see the {doc}`API reference <../api/index>`.

```{toctree}
:maxdepth: 2

lifespans
morphology
ecohydraulics
maps
projectmaker
```
