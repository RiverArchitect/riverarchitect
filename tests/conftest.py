"""Shared fixtures.

The Live Guide remembers where a reader stopped, in a file under
:func:`riverarchitect.config.user_config_dir`. That is real user state, so the suite points
it at a temporary directory for the whole session: a test run must not move the position of
whoever is sitting at this machine, and one test must not inherit another's.
"""

import pytest


@pytest.fixture(autouse=True, scope="session")
def isolated_user_config(tmp_path_factory):
    directory = tmp_path_factory.mktemp("user-config")
    import os

    previous = os.environ.get("RIVERARCHITECT_CONFIG_HOME")
    os.environ["RIVERARCHITECT_CONFIG_HOME"] = str(directory)
    yield str(directory)
    if previous is None:
        os.environ.pop("RIVERARCHITECT_CONFIG_HOME", None)
    else:
        os.environ["RIVERARCHITECT_CONFIG_HOME"] = previous


@pytest.fixture
def clean_guide_progress(isolated_user_config):
    """A guide with no saved position, restored afterwards."""
    from riverarchitect import guide

    guide.clear_progress()
    yield
    guide.clear_progress()
