# Quick installation

This page gets River Architect running in a few minutes. If something does not work, or you
want to know *why* the steps look like this, read {doc}`installation_detailed`.

```{admonition} In short
:class: tip

1. Install [Miniforge](https://conda-forge.org/download/) (gives you `conda` and `mamba`).
2. Create the `ra-env` environment from `environment.yml`.
3. `pip install -e .` from a clone of the repository.
4. Optional: install QGIS if you want printed maps.
```

## Requirements at a glance

| | Minimum | Notes |
|---|---|---|
| Operating system | Linux, macOS or Windows | no Esri software, no Windows-only dependency |
| Python | 3.9 (3.12 recommended) | 3.12 is what `environment.yml` pins |
| Disk | ~3 GB | almost all of it is the GDAL stack |
| RAM | 4 GB | 8 GB for reach-scale rasters |
| PySide6 | 6.5 or newer | the Qt interface; falls back to tkinter without it |
| QGIS | 3.28 or newer, with Python bindings | **only** for the mapping module |

Everything except mapping works without QGIS, and the interface opens without PySide6. The
full dependency list is in {ref}`the detailed page <detailed-requirements>`.

```{note}
River Architect is not on PyPI yet, so `pip install riverarchitect` does not work. Install
from a clone of the repository as shown below.
```

## Install

::::{tab-set}

:::{tab-item} Linux
:sync: linux

```bash
# 1. Miniforge, if you do not already have conda or mamba
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh

# 2. River Architect
git clone https://github.com/RiverArchitect/riverarchitect.git
cd riverarchitect
mamba env create -f environment.yml
mamba activate ra-env
pip install -e ".[all]"

# 3. Optional: QGIS for map production (system packages, not conda)
sudo apt install qgis python3-qgis        # Debian / Ubuntu
```

On Fedora use `sudo dnf install qgis qgis-python`, on Arch
`sudo pacman -S qgis python-qgis`.
:::

:::{tab-item} Windows
:sync: windows

Run these in the **Miniforge Prompt** (installed with
[Miniforge](https://conda-forge.org/download/)), not in `cmd.exe`.

```powershell
git clone https://github.com/RiverArchitect/riverarchitect.git
cd riverarchitect
mamba env create -f environment.yml
mamba activate ra-env
pip install -e ".[all]"
```

For map production, install QGIS with the
[OSGeo4W installer](https://qgis.org/download/) (choose the *Express Desktop Install*).
QGIS ships its own Python, so run the mapping module from the **OSGeo4W Shell**:

```powershell
python-qgis -c "from qgis.core import Qgis; print(Qgis.QGIS_VERSION)"
```

```{warning}
Do not install QGIS into `ra-env`. The conda-forge `qgis` package and the OSGeo4W one
compete for the same DLLs, and the usual result is an environment where neither works.
```
:::

:::{tab-item} macOS
:sync: macos

```bash
# 1. Miniforge, if you do not already have conda or mamba
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh

# 2. River Architect
git clone https://github.com/RiverArchitect/riverarchitect.git
cd riverarchitect
mamba env create -f environment.yml
mamba activate ra-env
pip install -e ".[all]"

# 3. Optional: QGIS for map production
brew install --cask qgis
```

The Homebrew cask puts the bindings in QGIS's own interpreter:

```bash
/Applications/QGIS.app/Contents/MacOS/bin/python3 -c \
    "from qgis.core import Qgis; print(Qgis.QGIS_VERSION)"
```

On Apple silicon, use the arm64 Miniforge build. Rosetta is not needed.
:::

::::

## Check that it worked

```bash
mamba activate ra-env
python -c "import riverarchitect; print(riverarchitect.__version__)"
pytest                       # 54 tests, about a second
```

`pytest` needs the test extra: `pip install -e ".[all,test]"`.

If the mapping module is going to be used, check the QGIS bindings separately with the
interpreter that owns them (see the tabs above). River Architect reports
`QGIS_AVAILABLE = False` and disables the Mapping tab rather than crashing when they are
missing.

## Start the interface

::::{tab-set}

:::{tab-item} Linux / macOS
:sync: linux

```bash
./runRiverArchitectLinux.sh
```
:::

:::{tab-item} Windows
:sync: windows

```powershell
runRiverArchitectWin.bat
```
:::

::::

The launchers find the environment themselves, so there is nothing to activate first. With
no argument they open the sample data bundled with the repository. From an activated
environment, equivalently:

```bash
riverarchitect                    # console script
python -m riverarchitect          # equivalent
riverarchitect /path/to/project   # start with a project directory
```

{doc}`gui` covers the two front ends, the launcher options and what each tab does.

## The sample data

A real gravel-cobble reach ships with the repository in `sample-data/`, so there is nothing
extra to download. It is a complete project directory:

```bash
riverarchitect sample-data
export RIVERARCHITECT_HOME="$PWD/sample-data"     # Windows: setx RIVERARCHITECT_HOME ...
```

## Next

* {doc}`gui` covers the graphical interface and the launchers.
* {doc}`tutorial` runs lifespan mapping and fish stranding on the sample data.
* {doc}`quickstart` is a tour of the individual building blocks.
* {doc}`installation_detailed` explains the dependency choices, the project directory
  layout and what to do when an install goes wrong.
