# License

River Architect is released under the **BSD 3-Clause License**, an
[OSI-approved](https://opensource.org/license/bsd-3-clause) permissive open-source licence.

In short: you may use, modify and redistribute it, in source or binary form, commercially or
not, provided you keep the copyright notice and the disclaimer, and do not use the project's
name or its contributors' names to endorse anything derived from it. There is no warranty.

```{admonition} No Esri licence is required
:class: note

This is the open-source release: the geoprocessing runs on GDAL and the mapping on QGIS, so
nothing in River Architect requires ArcGIS, a Spatial Analyst extension, or any other
proprietary licence. The 1.x series did - see {doc}`guide/arcpy_migration`.
```

## Full text

```text
BSD 3-Clause License

Copyright (c) 2020-2026, River Architect Development Team
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

The authoritative copy is `LICENSE` in the repository root.

## Citing River Architect

The method is documented in an open-access, peer-reviewed paper. Please cite it in work that
uses the software:

> Schwindt, S., Larrieu, K., Pasternack, G.B., Rabone, G. (2020). River Architect.
> *SoftwareX* 11, 100438. <https://doi.org/10.1016/j.softx.2020.100438>

## Third-party components

River Architect builds on other open-source projects, each under its own licence: GDAL and
rasterio, numpy, scipy, pandas, geopandas and shapely, openpyxl, Qt through PySide6 or PyQt5,
and QGIS for map production. Their terms apply to those components, not to River Architect.

The **sample data** in `sample-data/` is provided for demonstration and testing; see
`sample-data/README.md` for its provenance and the upstream repository it comes from.

The **legacy wiki pages** kept under *Concepts and legacy modules* are preserved from the
original River Architect wiki, with only their links rewritten.
