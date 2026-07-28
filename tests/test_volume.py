"""Triangulated-surface volume integration, checked against analytical results."""

import numpy as np
import pytest

from riverarchitect.volume import surface_volume


def test_flat_surface():
    """A flat surface at z=5 over an 11x11 grid of 1 m cells spans a 10x10 m TIN."""
    z = np.full((11, 11), 5.0)
    result = surface_volume(z, 1.0, 1.0, plane=0.0)
    assert result["volume"] == pytest.approx(500.0)
    assert result["area_2d"] == pytest.approx(100.0)
    assert result["area_3d"] == pytest.approx(100.0)


def test_cell_prism_sum_differs():
    """The prism sum carries a perimeter error the TIN method avoids."""
    z = np.full((11, 11), 5.0)
    tin = surface_volume(z, 1.0, 1.0)["volume"]
    prism = np.nansum(z) * 1.0 * 1.0
    assert tin == pytest.approx(500.0)
    assert prism == pytest.approx(605.0)


def test_tilted_plane():
    z = np.tile(np.arange(11, dtype="float64"), (11, 1))
    assert surface_volume(z, 1.0, 1.0)["volume"] == pytest.approx(500.0)


def test_plane_crossing_reference_is_clipped():
    """z = x - 5 over x in [0, 10]: the part above zero is a 5x5 triangle per unit width."""
    z = np.tile(np.arange(11, dtype="float64") - 5.0, (11, 1))
    result = surface_volume(z, 1.0, 1.0, plane=0.0)
    assert result["volume"] == pytest.approx(125.0)
    assert result["area_2d"] == pytest.approx(50.0)


def test_reference_below():
    z = np.tile(np.arange(11, dtype="float64") - 5.0, (11, 1))
    assert surface_volume(z, 1.0, 1.0, reference="BELOW")["volume"] == pytest.approx(125.0)


def test_non_zero_reference_plane():
    z = np.full((11, 11), 5.0)
    assert surface_volume(z, 1.0, 1.0, plane=2.0)["volume"] == pytest.approx(300.0)


def test_anisotropic_cells():
    z = np.full((11, 11), 4.0)
    assert surface_volume(z, 2.0, 0.5)["volume"] == pytest.approx(400.0)


def test_nodata_triangles_excluded():
    z = np.full((11, 11), 5.0)
    z[0, :] = np.nan
    result = surface_volume(z, 1.0, 1.0)
    assert result["volume"] == pytest.approx(450.0)
    assert result["area_2d"] == pytest.approx(90.0)


def test_all_nodata():
    z = np.full((11, 11), np.nan)
    result = surface_volume(z, 1.0, 1.0)
    assert result["volume"] == 0.0
    assert result["area_2d"] == 0.0


def test_draped_area_on_45_degree_slope():
    z = np.tile(np.arange(11, dtype="float64"), (11, 1))
    result = surface_volume(z, 1.0, 1.0, plane=-1000.0)
    assert result["area_3d"] == pytest.approx(100.0 * np.sqrt(2))


def test_pyramid_converges_under_refinement():
    """A TIN approximates a pyramid whose ridges do not follow the triangulation."""
    exact = 400.0 * 10 / 3
    previous_error = None
    for step in (1.0, 0.5, 0.25):
        n = int(20 / step) + 1
        axis = (np.arange(n) - (n - 1) / 2) * step
        x, y = np.meshgrid(axis, axis)
        z = np.clip(10.0 - np.maximum(np.abs(x), np.abs(y)), 0, None)
        error = abs(surface_volume(z, step, step)["volume"] - exact)
        if previous_error is not None:
            assert error < previous_error
        previous_error = error
    assert previous_error < 0.3


def test_invalid_reference_rejected():
    with pytest.raises(ValueError):
        surface_volume(np.zeros((3, 3)), 1.0, 1.0, reference="SIDEWAYS")


def test_requires_2d_array():
    with pytest.raises(ValueError):
        surface_volume(np.zeros(5), 1.0, 1.0)
