#!/usr/bin/env bash
#
# Start River Architect on Linux (and macOS).
#
#   ./runRiverArchitectLinux.sh                 # use the sample data shipped with the repo
#   ./runRiverArchitectLinux.sh /data/project   # use your own project directory
#
# Environment variables:
#   RA_PYTHON            interpreter to use, overriding the search below
#   RA_ENV               conda/mamba environment name (default: ra-env)
#   RIVERARCHITECT_GUI   force a front end: qt or tk
#   QGIS_PREFIX_PATH     where QGIS is installed, if not /usr
#
# Mapping needs the QGIS Python bindings, which are built against the interpreter QGIS was
# installed with - usually the system Python, not a conda environment. To get a working
# Mapping tab, start with that interpreter:
#
#   RA_PYTHON=/usr/bin/python3 ./runRiverArchitectLinux.sh
#
set -euo pipefail

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
RA_ENV="${RA_ENV:-ra-env}"

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

# The package is importable from src/ even without an install, which keeps a fresh clone
# working. An installed copy on sys.path still wins.
export PYTHONPATH="${HERE}/src${PYTHONPATH:+:${PYTHONPATH}}"

# Default to the sample data so that a fresh clone opens with something to look at.
if [ "$#" -ge 1 ]; then
    PROJECT="$1"
elif [ -z "${RIVERARCHITECT_HOME:-}" ] && [ -d "${HERE}/sample-data/01_Conditions" ]; then
    PROJECT="${HERE}/sample-data"
    printf 'No project directory given - using the bundled sample data.\n'
else
    PROJECT="${RIVERARCHITECT_HOME:-$PWD}"
fi

# --- find an interpreter --------------------------------------------------------------

find_python() {
    # 1. explicit override
    if [ -n "${RA_PYTHON:-}" ]; then
        command -v "${RA_PYTHON}" >/dev/null 2>&1 || die "RA_PYTHON is set to '${RA_PYTHON}', which is not executable."
        command -v "${RA_PYTHON}"
        return
    fi

    # 2. a conda/mamba environment named ${RA_ENV}
    for launcher in mamba micromamba conda; do
        if command -v "${launcher}" >/dev/null 2>&1; then
            local base
            base="$("${launcher}" info --base 2>/dev/null || true)"
            if [ -n "${base}" ] && [ -x "${base}/envs/${RA_ENV}/bin/python" ]; then
                printf '%s\n' "${base}/envs/${RA_ENV}/bin/python"
                return
            fi
        fi
    done
    # also honour a conda root that is on PATH but whose `info --base` is unavailable
    if [ -n "${CONDA_PREFIX:-}" ] && [ -x "${CONDA_PREFIX}/../${RA_ENV}/bin/python" ]; then
        printf '%s\n' "${CONDA_PREFIX}/../${RA_ENV}/bin/python"
        return
    fi

    # 3. whatever environment is already active
    if [ -n "${CONDA_PREFIX:-}" ] && [ -x "${CONDA_PREFIX}/bin/python" ]; then
        printf '%s\n' "${CONDA_PREFIX}/bin/python"
        return
    fi
    if [ -n "${VIRTUAL_ENV:-}" ] && [ -x "${VIRTUAL_ENV}/bin/python" ]; then
        printf '%s\n' "${VIRTUAL_ENV}/bin/python"
        return
    fi

    # 4. the system interpreter
    command -v python3 2>/dev/null || command -v python 2>/dev/null || true
}

PYTHON="$(find_python)"
[ -n "${PYTHON}" ] || die "No Python interpreter found. Install Miniforge and create the
       environment:  mamba env create -f '${HERE}/environment.yml'"

# --- check the dependencies before opening a window -----------------------------------

# numpy is the floor: without it nothing in the package works.
if ! "${PYTHON}" -c "import numpy" >/dev/null 2>&1; then
    die "'${PYTHON}' cannot import numpy.

       Create the environment and try again:
           mamba env create -f '${HERE}/environment.yml'
           mamba activate ${RA_ENV}
           pip install -e '${HERE}[all]'

       Or point this script at a working interpreter with RA_PYTHON=..."
fi

# rasterio is only needed by the analysis tabs. A QGIS interpreter typically lacks it, and
# starting there for the sake of the Mapping tab is a legitimate thing to do - so warn and
# carry on. The affected tabs explain themselves rather than failing on click.
if ! "${PYTHON}" -c "import rasterio" >/dev/null 2>&1; then
    printf 'WARNING: rasterio is not installed for %s.\n' "${PYTHON}" >&2
    printf '         The analysis tabs will be disabled; mapping is unaffected.\n' >&2
fi

printf 'River Architect\n'
printf '  interpreter : %s\n' "${PYTHON}"
printf '  project     : %s\n' "${PROJECT}"
printf 'Loading (please wait) ...\n'

exec "${PYTHON}" -m riverarchitect "${PROJECT}"
