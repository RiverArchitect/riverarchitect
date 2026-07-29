"""Tests for locating the QGIS Python bindings.

A distribution installs the bindings for the *system* interpreter, so a conda environment
does not see them even though QGIS is installed and working. This is the discovery that
fixes that, and it has to work on all three platforms - which means the Windows and macOS
layouts must be testable from a Linux machine. They are, because the patterns are written
with forward slashes and resolved through :func:`os.path.normpath`.
"""

import os
import sys

import pytest

from riverarchitect import mapping


def same_path(a, b):
    """Compare two paths without caring which separator this platform uses.

    `os.path.normpath` rewrites "/" as "\\" on Windows, so a literal POSIX expectation like
    "/Applications/QGIS.app/Contents/MacOS" never matches there even when the arithmetic is
    right. Normalising both sides tests the template, not the platform.
    """
    return os.path.normpath(a).replace("\\", "/") == os.path.normpath(b).replace("\\", "/")


def touch_tree(root, *relative_dirs):
    """Create directories, each with an empty ``qgis`` package inside."""
    made = []
    for relative in relative_dirs:
        path = os.path.join(str(root), *relative.split("/"))
        os.makedirs(os.path.join(path, "qgis"), exist_ok=True)
        made.append(path)
    return made


# --------------------------------------------------------------- shipped layouts

def test_every_platform_has_a_layout():
    assert set(mapping.QGIS_LAYOUTS) == {"linux", "darwin", "win32"}
    for entries in mapping.QGIS_LAYOUTS.values():
        assert entries
        for pattern, prefix, dll_dirs in entries:
            assert pattern and prefix
            assert isinstance(dll_dirs, tuple)


def test_windows_patterns_use_forward_slashes():
    """So that `normpath` produces backslashes on Windows and the tests run anywhere."""
    for pattern, prefix, dll_dirs in mapping.QGIS_LAYOUTS["win32"]:
        for text in (pattern, prefix) + dll_dirs:
            assert "\\" not in text, text


def test_only_windows_declares_dll_directories():
    """Windows resolves dependent DLLs through an explicit list; the others do not."""
    assert any(dll_dirs for _p, _x, dll_dirs in mapping.QGIS_LAYOUTS["win32"])
    for key in ("linux", "darwin"):
        assert not any(dll_dirs for _p, _x, dll_dirs in mapping.QGIS_LAYOUTS[key])


# ------------------------------------------------------- prefix template arithmetic

def resolve(pattern, prefix_template, dll_patterns, bindings):
    """Apply the templates the way :func:`mapping.qgis_candidates` does."""
    prefix = os.path.normpath(prefix_template.format(b=bindings))
    dll_dirs = tuple(os.path.normpath(p.format(b=bindings)) for p in dll_patterns)
    return prefix, dll_dirs


def test_osgeo4w_prefix_and_dll_directories():
    """C:/OSGeo4W/apps/qgis/python -> prefix .../apps/qgis, DLLs in both bin folders."""
    pattern, prefix_template, dll_patterns = mapping.QGIS_LAYOUTS["win32"][0]
    prefix, dll_dirs = resolve(pattern, prefix_template, dll_patterns,
                               "C:/OSGeo4W/apps/qgis/python")
    assert same_path(prefix, "C:/OSGeo4W/apps/qgis")
    assert any(same_path(d, "C:/OSGeo4W/apps/qgis/bin") for d in dll_dirs)
    assert any(same_path(d, "C:/OSGeo4W/bin") for d in dll_dirs)


def test_windows_standalone_installer_prefix():
    """The standalone installer puts the version in the folder name."""
    pattern, prefix_template, dll_patterns = mapping.QGIS_LAYOUTS["win32"][1]
    prefix, dll_dirs = resolve(pattern, prefix_template, dll_patterns,
                               "C:/Program Files/QGIS 3.34.5/apps/qgis-ltr/python")
    assert same_path(prefix, "C:/Program Files/QGIS 3.34.5/apps/qgis-ltr")
    assert any(same_path(d, "C:/Program Files/QGIS 3.34.5/bin") for d in dll_dirs)


def test_macos_bundle_prefix_is_the_macos_directory():
    """QGIS looks for its providers under Contents/MacOS, not under Resources."""
    pattern, prefix_template, dll_patterns = mapping.QGIS_LAYOUTS["darwin"][0]
    prefix, _dll = resolve(pattern, prefix_template, dll_patterns,
                           "/Applications/QGIS.app/Contents/Resources/python")
    assert same_path(prefix, "/Applications/QGIS.app/Contents/MacOS")


def test_opt_prefix_climbs_out_of_share_qgis_python():
    entry = [e for e in mapping.QGIS_LAYOUTS["linux"] if e[0].startswith("/opt")][0]
    prefix, _dll = resolve(*entry, bindings="/opt/qgis3.40/share/qgis/python")
    assert same_path(prefix, "/opt/qgis3.40")


def test_debian_bindings_map_to_the_usr_prefix():
    entry = mapping.QGIS_LAYOUTS["linux"][0]
    assert entry[0] == "/usr/lib/python3/dist-packages"
    assert entry[1] == "/usr"


# ---------------------------------------------------------------- candidate order

def test_candidates_are_generated_for_a_simulated_platform(tmp_path, monkeypatch):
    """A fake OSGeo4W tree is discovered with the right prefix and DLL directories."""
    root = tmp_path / "C"
    touch_tree(root, "OSGeo4W/apps/qgis/python")
    os.makedirs(str(root / "OSGeo4W" / "bin"), exist_ok=True)
    os.makedirs(str(root / "OSGeo4W" / "apps" / "qgis" / "bin"), exist_ok=True)

    base = str(root).replace(os.sep, "/")
    monkeypatch.setattr(mapping, "_qgis_platform", lambda: "win32")
    monkeypatch.setitem(mapping.QGIS_LAYOUTS, "win32", (
        (base + "/OSGeo4W*/apps/qgis*/python", "{b}/..",
         ("{b}/../bin", "{b}/../../../bin")),
    ))
    monkeypatch.delenv("RIVERARCHITECT_QGIS_PATH", raising=False)
    monkeypatch.delenv("QGIS_PREFIX_PATH", raising=False)

    candidates = list(mapping.qgis_candidates())
    assert len(candidates) == 1
    bindings, prefix, dll_dirs = candidates[0]
    assert same_path(bindings, base + "/OSGeo4W/apps/qgis/python")
    assert same_path(prefix, base + "/OSGeo4W/apps/qgis")
    assert any(same_path(d, base + "/OSGeo4W/bin") for d in dll_dirs)
    assert all(os.path.isdir(d) for d in dll_dirs)


def test_the_newest_installation_is_tried_first(tmp_path, monkeypatch):
    """With 3.34 and 3.40 side by side, a user expects the newer one."""
    touch_tree(tmp_path, "QGIS 3.34.5/apps/qgis/python", "QGIS 3.40.1/apps/qgis/python")

    base = str(tmp_path).replace(os.sep, "/")
    monkeypatch.setattr(mapping, "_qgis_platform", lambda: "win32")
    monkeypatch.setitem(mapping.QGIS_LAYOUTS, "win32",
                        ((base + "/QGIS *dev/apps/qgis*/python", "{b}/..", ()),
                         (base + "/QGIS */apps/qgis*/python", "{b}/..", ())))
    monkeypatch.delenv("RIVERARCHITECT_QGIS_PATH", raising=False)
    monkeypatch.delenv("QGIS_PREFIX_PATH", raising=False)

    first = list(mapping.qgis_candidates())[0][0]
    assert "3.40.1" in first


def test_the_environment_variables_win(tmp_path, monkeypatch):
    """An explicit path must beat every guess, so an unusual install needs no patching."""
    explicit, = touch_tree(tmp_path, "somewhere/odd")
    monkeypatch.setenv("RIVERARCHITECT_QGIS_PATH", explicit)
    monkeypatch.setenv("QGIS_PREFIX_PATH", str(tmp_path / "prefix"))

    candidates = list(mapping.qgis_candidates())
    assert same_path(candidates[0][0], explicit)
    assert same_path(candidates[0][1], str(tmp_path / "prefix"))
    # the prefix is then also tried in its own right
    assert any(same_path(c[0], str(tmp_path / "prefix" / "python")) for c in candidates[1:])


# --------------------------------------------------------------------- behaviour

def test_the_module_reports_what_it_found():
    """Whatever the outcome, the three flags must agree with one another."""
    if mapping.QGIS_AVAILABLE:
        import qgis.core  # noqa: F401
        # QGIS_BINDINGS_PATH is None when qgis was importable without any help
        if mapping.QGIS_BINDINGS_PATH is not None:
            assert os.path.isdir(os.path.join(mapping.QGIS_BINDINGS_PATH, "qgis"))
            assert mapping.QGIS_BINDINGS_PATH in sys.path
    else:
        assert mapping.QGIS_BINDINGS_PATH is None
        with pytest.raises(ImportError):
            import qgis.core  # noqa: F401


def test_a_discovered_path_is_appended_never_prepended():
    """Prepending Debian's dist-packages silently downgrades numpy, pandas and scipy.

    That is a worse failure than no mapping, because it produces results rather than an
    error - so the discovered directory must never win a name the environment also has.
    """
    if mapping.QGIS_BINDINGS_PATH is None:
        pytest.skip("bindings were already importable, nothing was added")
    index = sys.path.index(mapping.QGIS_BINDINGS_PATH)
    site_packages = [i for i, p in enumerate(sys.path) if p.endswith("site-packages")]
    assert site_packages, "no site-packages on sys.path to compare against"
    assert index > max(site_packages)


def test_the_prefix_matches_the_bindings_that_loaded():
    """`/usr` is meaningless on macOS and Windows; the prefix must follow the bindings."""
    if not mapping.QGIS_AVAILABLE or mapping.QGIS_BINDINGS_PATH is None:
        pytest.skip("QGIS not discovered on this machine")
    assert mapping.QGIS_PREFIX
    assert os.path.isdir(mapping.QGIS_PREFIX)
