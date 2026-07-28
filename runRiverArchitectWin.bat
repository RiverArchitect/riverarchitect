@echo off
rem ---------------------------------------------------------------------------------------
rem  Start River Architect on Windows.
rem
rem    runRiverArchitectWin.bat                  use the sample data shipped with the repo
rem    runRiverArchitectWin.bat D:\my_project    use your own project directory
rem
rem  Environment variables:
rem    RA_PYTHON            python.exe to use, overriding the search below
rem    RA_ENV               conda/mamba environment name (default: ra-env)
rem    RIVERARCHITECT_GUI   force a front end: qt or tk
rem    QGIS_PREFIX_PATH     where QGIS is installed
rem
rem  This replaces the ArcGIS-era launcher, which called ArcGIS Pro's `propy.bat`. No Esri
rem  software is involved any more.
rem
rem  Mapping needs the QGIS Python bindings, which belong to the interpreter QGIS installed.
rem  For a working Mapping tab, run this from the OSGeo4W Shell, or set
rem    set RA_PYTHON=C:\OSGeo4W\bin\python.exe
rem ---------------------------------------------------------------------------------------

setlocal EnableDelayedExpansion

set "HERE=%~dp0"
if "%HERE:~-1%"=="\" set "HERE=%HERE:~0,-1%"

if "%RA_ENV%"=="" set "RA_ENV=ra-env"

rem The package is importable from src\ even without an install, so a fresh clone works.
if "%PYTHONPATH%"=="" (
    set "PYTHONPATH=%HERE%\src"
) else (
    set "PYTHONPATH=%HERE%\src;%PYTHONPATH%"
)

rem --- project directory ----------------------------------------------------------------

set "PROJECT=%~1"
if not "%PROJECT%"=="" goto :have_project
if not "%RIVERARCHITECT_HOME%"=="" (
    set "PROJECT=%RIVERARCHITECT_HOME%"
    goto :have_project
)
if exist "%HERE%\sample-data\01_Conditions" (
    set "PROJECT=%HERE%\sample-data"
    echo No project directory given - using the bundled sample data.
    goto :have_project
)
set "PROJECT=%CD%"
:have_project

rem --- find an interpreter --------------------------------------------------------------

set "PYTHON="

if not "%RA_PYTHON%"=="" (
    if exist "%RA_PYTHON%" (
        set "PYTHON=%RA_PYTHON%"
    ) else (
        echo ERROR: RA_PYTHON is set to "%RA_PYTHON%", which does not exist.
        goto :fail
    )
    goto :have_python
)

rem A conda/mamba environment named %RA_ENV%, in the usual install locations.
for %%B in (
    "%USERPROFILE%\miniforge3"
    "%USERPROFILE%\mambaforge"
    "%USERPROFILE%\miniconda3"
    "%USERPROFILE%\anaconda3"
    "%LOCALAPPDATA%\miniforge3"
    "%PROGRAMDATA%\miniforge3"
    "%PROGRAMDATA%\miniconda3"
) do (
    if exist "%%~B\envs\%RA_ENV%\python.exe" (
        set "PYTHON=%%~B\envs\%RA_ENV%\python.exe"
        goto :have_python
    )
)

rem An already-activated environment.
if not "%CONDA_PREFIX%"=="" (
    if exist "%CONDA_PREFIX%\python.exe" (
        set "PYTHON=%CONDA_PREFIX%\python.exe"
        goto :have_python
    )
)
if not "%VIRTUAL_ENV%"=="" (
    if exist "%VIRTUAL_ENV%\Scripts\python.exe" (
        set "PYTHON=%VIRTUAL_ENV%\Scripts\python.exe"
        goto :have_python
    )
)

rem Anything on PATH.
for /f "delims=" %%P in ('where python.exe 2^>nul') do (
    set "PYTHON=%%P"
    goto :have_python
)

echo ERROR: No Python interpreter found.
echo.
echo        Install Miniforge from https://conda-forge.org/download/ and then run,
echo        in the Miniforge Prompt:
echo.
echo            mamba env create -f "%HERE%\environment.yml"
echo            mamba activate %RA_ENV%
echo            pip install -e "%HERE%[all]"
goto :fail

:have_python

rem --- check the dependencies before opening a window -----------------------------------

rem numpy is the floor: without it nothing in the package works.
"%PYTHON%" -c "import numpy" >nul 2>&1
if errorlevel 1 (
    echo ERROR: "%PYTHON%" cannot import numpy.
    echo.
    echo        Create the environment and try again, in the Miniforge Prompt:
    echo.
    echo            mamba env create -f "%HERE%\environment.yml"
    echo            mamba activate %RA_ENV%
    echo            pip install -e "%HERE%[all]"
    echo.
    echo        Or point this script at a working interpreter with:  set RA_PYTHON=...
    goto :fail
)

rem rasterio is only needed by the analysis tabs. An OSGeo4W interpreter may lack it, and
rem starting there for the Mapping tab is legitimate - so warn and carry on.
"%PYTHON%" -c "import rasterio" >nul 2>&1
if errorlevel 1 (
    echo WARNING: rasterio is not installed for "%PYTHON%".
    echo          The analysis tabs will be disabled; mapping is unaffected.
)

echo River Architect
echo   interpreter : %PYTHON%
echo   project     : %PROJECT%
echo Loading (please wait) ...

"%PYTHON%" -m riverarchitect "%PROJECT%"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
    echo.
    echo River Architect exited with code %RC%.
    pause
)
endlocal & exit /b %RC%

:fail
echo.
pause
endlocal & exit /b 1
