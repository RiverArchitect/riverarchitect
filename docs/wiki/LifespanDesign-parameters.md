Feature lifespan and design assessment
======================================

***

- [Introduction to lifespan and design mapping][3]
- [Quick GUIde to lifespan and design maps][3]
- **Parameter hypotheses**
- [River design and restoration features](River-design-features)
- [Code extension and modification](LifespanDesign-code)

***

# Parameter hypotheses<a name="par"></a>
Combinations of recurring parameters determine the lifespans of features. The code analyses the following parameters, where the application order (hierarchy) differs from the alphabetic order for reasons of map integrity (see coding conventions in the [Signposts][2]). **Calculation details** are provided within the [**descriptions for defining threshold values**](LifespanDesign#inpras).

-   `chsi` composite Habitat Suitability Index (dimensionless value between 0 and 1)

-   `d2w` is the surface depth to the groundwater table (length units)

-   `det` is the detrended DEM (length units)

-   `Dcr` are mobile or stable grain sizes that are entrained by (non-frequent) discharges that occur according to a defined return period (see [angular boulders](#rocks))

-   `fill` corresponds to annual sediment deposition rates (length units; see also [Wyrick and Pasternack 2016][wyrick16])

-   `Fr` is the Froude number (dimensionless hydraulic variable) corresponding to `u`/(`h` *g*), where *g* denotes gravity acceleration 

-   `h` is the flow depth (length units)

-   `mu` are the morphological units (strings; see also [Wyrick and Pasternack 2014][wyrick14])

-   `Se` is the energy slope (dimensionless hydraulic variable; cf. [angular boulders](#rocks) and [side channels](River-design-features) sections)

-   `scour` corresponds to annual erosion rates (length units, see also[Wyrick and Pasternack 2016][wyrick16])

-   `sidech` delineation of priority regions for side channels ([Van Denderen et al. 2017][vandenderen17])

-   `taux` (or *&tau;<sub>\*</sub>*) is the dimensionless bed shear stress and its critical value *&tau;<sub>\*, cr</sub>* (--)

-   `tcd` combines `scour` and `fill` analysis

-   `u` is the flow velocity (length per time: fps or m/s)

-   `wild` wildcard parameter that can only take on/off values (`noData`, 0 or 1)

The code uses the `mu` raster to identify feature-adequate morphological units that are stored a `feature.mu_good` list and feature-inadequate units that are stored in a `feature.mu_bad` list. Thus, two approaches are possible: an inclusive approach that limits relevant areas using the `feature.mu_good` list and an exclusive approach that excludes non-relevant areas using the `feature.mu_bad` list. The following morphological units are considered [Wyrick and Pasternack (2014)][wyrick14]:

| Morphological Units                       |                   |
| :---------------------------------------- | :---------------- |
| agriplain                                 | bank              |
| bedrock                                   | chute             |
| cutbank                                   | fast glide        |
| flood runner                              | floodplain        |
| high floodplain                           | hillside          |
| island high floodplain                    | island-floodplain |
| lateral bar                               | levee             |
| medial bar                                | mining pit        |
| point bar                                 | pond              |
| pool                                      | riffle            |
| riffle transition                         | run               |
| slackwater                                | slow glide        |
| spur dike                                 | swale             |
| tailings                                  | terrace           |
| tributary channel                         | tributary delta   |
| in-channel bar (all within-bankfull bars) |                   |

[1]: https://github.com/RiverArchitect/RA_wiki/Installation
[2]: https://github.com/RiverArchitect/RA_wiki/Signposts
[3]: https://github.com/RiverArchitect/RA_wiki/LifespanDesign
[4]: https://github.com/RiverArchitect/RA_wiki/MaxLifespan
[5]: https://github.com/RiverArchitect/RA_wiki/ModifyTerrain
[6]: https://github.com/RiverArchitect/RA_wiki/SHArC
[7]: https://github.com/RiverArchitect/RA_wiki/ProjectMaker
[8]: https://github.com/RiverArchitect/RA_wiki/Tools
[9]: https://github.com/RiverArchitect/RA_wiki/FAQ
[10]: https://github.com/RiverArchitect/RA_wiki/Troubleshooting

[bywater15]: http://dx.doi.org/10.1002/2014WR016641
[carley12]: https://www.sciencedirect.com/science/article/pii/S0169555X12003819
[friedman99]: http://dx.doi.org/10.1002/(SICI)1099-1646(199909/10)15:5<463::AID-RRR559>3.0.CO;2-Z
[gaeuman08]: http://odp.trrp.net/DataPort/doc.php?id=346
[glenn15]: https://doi.org/10.1201/b18359
[jablkowski17]: http://www.sciencedirect.com/science/article/pii/S0169555X1730274X
[kui16a]: http://www.sciencedirect.com/science/article/pii/S0378112716300123
[lange05]: https://www.ethz.ch/content/dam/ethz/special-interest/baug/vaw/vaw-dam/documents/das-institut/mitteilungen/2000-2009/188.pdf
[manningsn]: https://en.wikipedia.org/wiki/Manning_formula#Manning_coefficient_of_roughness
[maynord08]: https://ascelibrary.org/doi/10.1061/9780784408148.apb
[ock13]: https://www.jstage.jst.go.jp/article/hrl/7/3/7_54/_article
[pasquale14]: http://dx.doi.org/10.1002/hyp.9993
[pasternack10a]: http://calag.ucanr.edu/archive/?article=ca.v064n02p69
[polzin06]: https://link.springer.com/article/10.1672/0277-5212(2006)26%5B965:EDSSSA%5D2.0.CO;2
[ruiz16b]: https://www.sciencedirect.com/science/article/pii/S0169555X15002019?via%3Dihub
[schwindt19]: https://www.sciencedirect.com/science/article/pii/S0301479718312751
[stromberg93]: http://www.jstor.org/stable/41712765
[usace00]: https://www.publications.usace.army.mil/Portals/76/Publications/EngineerManuals/EM_1110-2-1913.pdf
[vandenderen17]: https://onlinelibrary.wiley.com/doi/full/10.1002/esp.4267
[weber17]: http://www.sciencedirect.com/science/article/pii/S0169555X16309862
[wilcox13]: http://dx.doi.org/10.1002/wrcr.20256
[wyrick14]: https://www.sciencedirect.com/science/article/pii/S0169555X14000099
[wyrick16]: https://onlinelibrary.wiley.com/doi/full/10.1002/esp.3854