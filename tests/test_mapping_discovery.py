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


def test_candidates_are_not_repeated(tmp_path, monkeypatch):
    """Two patterns matching one directory must yield it once.

    On Debian both the literal ``/usr/lib/python3/dist-packages`` entry and the
    ``/usr/lib/python3*/dist-packages`` glob resolve to the same place, and a directory
    tried twice is reported twice on failure - which reads as two broken installations
    rather than one.
    """
    shared, = touch_tree(tmp_path, "lib/python3/dist-packages")
    base = str(tmp_path).replace(os.sep, "/")
    monkeypatch.setattr(mapping, "_qgis_platform", lambda: "linux")
    monkeypatch.setitem(mapping.QGIS_LAYOUTS, "linux",
                        ((base + "/lib/python3/dist-packages", "/usr", ()),
                         (base + "/lib/python3*/dist-packages", "/usr", ())))
    monkeypatch.delenv("RIVERARCHITECT_QGIS_PATH", raising=False)
    monkeypatch.delenv("QGIS_PREFIX_PATH", raising=False)

    found = [c[0] for c in mapping.qgis_candidates() if same_path(c[0], shared)]
    assert len(found) == 1


# ------------------------------------------------------------------------ ABI tags

def test_the_abi_tag_names_the_python_the_bindings_need(tmp_path):
    """`_core.cpython-311-...so` means Python 3.11, whatever this interpreter is."""
    bindings, = touch_tree(tmp_path, "dist-packages")
    open(os.path.join(bindings, "qgis",
                      "_core.cpython-311-x86_64-linux-gnu.so"), "w").close()
    assert mapping.bindings_python_version(bindings) == (3, 11)


def test_the_windows_abi_tag_is_read_too(tmp_path):
    """Windows tags extension modules `cp313`, not `cpython-313`."""
    bindings, = touch_tree(tmp_path, "python")
    open(os.path.join(bindings, "qgis", "_core.cp313-win_amd64.pyd"), "w").close()
    assert mapping.bindings_python_version(bindings) == (3, 13)


def test_an_untagged_directory_reports_nothing_rather_than_guessing(tmp_path):
    """`None` means "cannot tell", which must not be read as "incompatible"."""
    bindings, = touch_tree(tmp_path, "python")
    assert mapping.bindings_python_version(bindings) is None


def test_bindings_for_another_python_are_rejected_without_touching_sys_path(
        tmp_path, monkeypatch):
    """The ABI check happens before the import, so nothing is added and removed again.

    It also has to produce a reason a user can act on. Importing anyway raises
    ``No module named 'PyQt5.sip'``, which sends people looking for a package that is not
    missing: PyQt5 *is* there, its sip extension simply carries the same foreign tag.
    """
    bindings, = touch_tree(tmp_path, "dist-packages")
    foreign = (3, sys.version_info[1] + 1)
    open(os.path.join(bindings, "qgis",
                      "_core.cpython-%d%d-x86_64-linux-gnu.so" % foreign), "w").close()

    base = str(tmp_path).replace(os.sep, "/")
    monkeypatch.setattr(mapping, "_qgis_platform", lambda: "linux")
    monkeypatch.setitem(mapping.QGIS_LAYOUTS, "linux",
                        ((base + "/dist-packages", "/usr", ()),))
    monkeypatch.delenv("RIVERARCHITECT_QGIS_PATH", raising=False)
    monkeypatch.delenv("QGIS_PREFIX_PATH", raising=False)
    monkeypatch.setattr(mapping, "_qgis_rejected", [])
    monkeypatch.setattr(mapping, "_qgis_abi_wanted", set())
    monkeypatch.setattr(sys, "path", list(sys.path))

    assert mapping._locate_qgis_bindings() is None
    assert not any(same_path(p, bindings) for p in sys.path)
    assert mapping._qgis_abi_wanted == {foreign}
    (path, reason), = mapping._qgis_rejected
    assert same_path(path, bindings)
    assert "built for Python %d.%d" % foreign in reason
    assert "this interpreter is %d.%d" % sys.version_info[:2] in reason


def test_the_status_message_explains_a_version_mismatch(monkeypatch):
    """The Maps tab must say it is a wrong-Python problem, not a missing-package one."""
    monkeypatch.setattr(mapping, "QGIS_AVAILABLE", False)
    monkeypatch.setattr(mapping, "_qgis_abi_wanted", {(3, 11)})
    monkeypatch.setattr(mapping, "_qgis_rejected",
                        [("/usr/lib/python3/dist-packages",
                          "built for Python 3.11, this interpreter is 3.12")])

    available, message = mapping.qgis_status()
    assert not available
    assert "/usr/lib/python3/dist-packages" in message
    assert "built for Python 3.11" in message
    # both ways out, so nobody concludes that QGIS is simply not installed
    assert "conda-forge qgis" in message
    assert "RA_PYTHON=" in message


def test_the_launcher_warns_only_about_a_version_mismatch(monkeypatch):
    """A missing QGIS is an ordinary optional dependency and must not warn at start-up.

    The Maps tab already explains that case. What deserves a warning before a window opens
    is the one that looks like a River Architect bug: QGIS installed, and mapping off.
    """
    monkeypatch.setattr(mapping, "QGIS_AVAILABLE", False)
    monkeypatch.setattr(mapping, "_qgis_abi_wanted", set())
    monkeypatch.setattr(mapping, "_qgis_rejected", [])
    assert mapping.qgis_launcher_warning() == ""

    monkeypatch.setattr(mapping, "_qgis_abi_wanted", {(3, 11)})
    monkeypatch.setattr(mapping, "_qgis_rejected",
                        [("/usr/lib/python3/dist-packages",
                          "built for Python 3.11, this interpreter is 3.12")])
    warning = mapping.qgis_launcher_warning("runRiverArchitectWin.bat")
    assert warning.startswith("WARNING: ")
    assert "/usr/lib/python3/dist-packages" in warning
    assert "runRiverArchitectWin.bat" in warning


def test_no_warning_when_mapping_works(monkeypatch):
    monkeypatch.setattr(mapping, "QGIS_AVAILABLE", True)
    monkeypatch.setattr(mapping, "_qgis_abi_wanted", {(3, 11)})
    assert mapping.qgis_launcher_warning() == ""


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
