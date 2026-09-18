# Update to the latest release

River Architect is installed from a clone of the repository, so an update is a `git pull` and a refresh of the environment. The commands are the same on Linux, macOS and Windows.

:::{admonition} The whole update, in four commands
:class: tip

```bash
cd riverarchitect              # your clone
git pull
mamba env update -f environment.yml --prune
pip install -e ".[all]"
```

On Windows, run them in the **Miniforge Prompt**. Activate the environment first (`mamba activate ra-env`) if it is not already active.
:::

That is all that is needed in the normal case. `git pull` brings the new code, `mamba env update` adds dependencies the release introduced and `--prune` removes ones it dropped, and `pip install -e` re-registers the package so new console scripts and entry points work. An editable install picks up the new code without reinstalling, but the last command is cheap and keeps the metadata honest.

## Check what you are running

```bash
mamba activate ra-env
python -c "import riverarchitect; print(riverarchitect.__version__)"
```

The number should match the newest entry in [`CHANGELOG.md`](https://github.com/RiverArchitect/riverarchitect/blob/main/CHANGELOG.md), which lists what changed and flags anything that needs an adjustment on your side. Read the entry for every version between the one you had and the one you are on.

## Stay on a released version

`git pull` on `main` gives you the development state. To follow releases instead:

```bash
git fetch --tags
git tag                       # the released versions, oldest first
git checkout v2.10.0          # the one you want
```

Then run the two environment commands above. Return to the development line with `git checkout main`.

## Your projects are not touched

An update replaces code only. Project directories, with their conditions, flow records and `Output/` results, live outside the package and are left exactly as they were, so nothing has to be backed up or migrated first. Rerun an analysis if a changelog entry says its results have changed.

## When an update misbehaves

**The interface or an import fails after pulling**
: The environment is behind the code. Run `mamba env update -f environment.yml --prune` again, in the activated environment, and watch for solver errors.

**`git pull` reports local changes**
: You have edited files in the clone. `git stash` sets them aside, `git stash pop` brings them back after the pull.

**The environment will not resolve**
: Recreate it, which takes a few minutes and is harmless: `mamba env remove -n ra-env`, then `mamba env create -f environment.yml`, then `pip install -e ".[all]"`.

**A result changed and you did not expect it to**
: Check the changelog entry for the versions you crossed. If it is not documented there, it is a defect worth [an issue](https://github.com/RiverArchitect/riverarchitect/issues).

{doc}`installation_detailed` covers the dependency choices and the rest of the failure modes.
