"""Every analysis module gives the same answer block by block as it does whole.

Each test runs a module twice on the bundled sample reach: once in memory, once forced
through :mod:`riverarchitect.tiled` with blocks small enough (41 x 67 cells on a 173 x 359
grid) that every seam cuts through the channel. Rasters must match cell for cell, counts
and areas exactly; only means, which are summed in a different order, get a relative
tolerance of 1e-12.
"""

import os

import numpy as np
import pytest

from riverarchitect import config, raster

BLOCK = (41, 67)


@pytest.fixture
def sample_home():
    from riverarchitect import guide

    if guide.sample_data_dir() is None:
        pytest.skip("not running from a source clone")
    original = config.project_home()
    try:
        yield guide.activate_sample_data()
    finally:
        config.set_project_home(original)


@pytest.fixture
def modes(monkeypatch):
    """``modes(fn)`` returns ``(fn(whole), fn(blockwise))``."""
    def run(fn):
        monkeypatch.setattr(config, "TILING", "never")
        whole = fn("whole")
        monkeypatch.setattr(config, "TILING", "always")
        monkeypatch.setattr(config, "BLOCK_SIZE", BLOCK)
        monkeypatch.setattr(config, "WORKERS", 2)
        parts = fn("blocks")
        monkeypatch.setattr(config, "TILING", "never")
        return whole, parts
    return run


def same_raster(a, b):
    x, y = raster.read(a)[0], raster.read(b)[0]
    assert x.shape == y.shape
    np.testing.assert_array_equal(x, y, err_msg="%s != %s" % (a, b))


def same_rows(a, b, exact=(), approx=()):
    assert len(a) == len(b)
    for x, y in zip(a, b):
        for key in exact:
            assert x[key] == y[key], (key, x, y)
        for key in approx:
            assert x[key] == pytest.approx(y[key], rel=1e-12, abs=1e-12), (key, x, y)


# ----------------------------------------------------------------------- SHArC

@pytest.mark.parametrize("cover, weighted", [(False, False), (True, True)])
def test_sharc(sample_home, modes, tmp_path, cover, weighted):
    pytest.importorskip("openpyxl")
    from riverarchitect.sharc import SHArC

    discharges = [300.0, 1000.0, 9750.0, 42200.0]

    def run(tag):
        analysis = SHArC("2100_sample", unit="us")
        return analysis.run("Chinook salmon", "fry", discharges=discharges,
                            output_dir=str(tmp_path / tag), cover=cover,
                            weighted=weighted)

    whole, parts = modes(run)
    assert whole["cover"] == parts["cover"]
    if cover:
        assert whole["cover"]
    same_rows(whole["per_discharge"], parts["per_discharge"], exact=("discharge",),
              approx=("usable_area", "mean_chsi"))
    if not weighted:
        same_rows(whole["per_discharge"], parts["per_discharge"], exact=("usable_area",))
    assert whole.get("sharea") == pytest.approx(parts.get("sharea"), rel=1e-12)
    for a, b in zip(whole["per_discharge"], parts["per_discharge"]):
        same_raster(a["raster"], b["raster"])


def test_sharc_fraction_rule(sample_home, modes, tmp_path):
    pytest.importorskip("openpyxl")
    from riverarchitect.sharc import SHArC

    def run(tag):
        analysis = SHArC("2100_sample", unit="us", mineral_rule="fraction", cover_window=2)
        return analysis.run("Chinook salmon", "juvenile", discharges=[750.0],
                            output_dir=str(tmp_path / tag), cover=True)

    whole, parts = modes(run)
    same_rows(whole["per_discharge"], parts["per_discharge"], exact=("usable_area",),
              approx=("mean_chsi",))
    same_raster(whole["per_discharge"][0]["raster"], parts["per_discharge"][0]["raster"])


# -------------------------------------------------------------------- Lifespan

#: Between them every kind of criterion: topographic change, morphological units, bed
#: shear stress, a mobile grain, design mapping, detrended DEM, depth to water table,
#: terrain slope, depth and Froude number.
LIFESPAN_FEATURES = ["backwt", "widen", "grade", "box", "wood", "rocks", "bio"]


def test_lifespan_every_criterion(sample_home, modes, tmp_path):
    from riverarchitect.lifespan import LifespanDesign

    def run(tag):
        if tag == "blocks":
            config.BLOCK_SIZE = (61, 127)          # nine blocks
        analysis = LifespanDesign("2100_sample", unit="us")
        results = analysis.run(LIFESPAN_FEATURES, output_dir=str(tmp_path / tag))
        assert not analysis.error
        return results

    whole, parts = modes(run)
    assert [r["feature"] for r in whole] == [r["feature"] for r in parts]
    assert len(whole) == len(LIFESPAN_FEATURES)
    blocks_dir, whole_dir = str(tmp_path / "blocks"), str(tmp_path / "whole")
    for a, b in zip(whole, parts):
        # Only the output folder may differ, whatever the platform's separator.
        assert a == {k: v.replace(blocks_dir, whole_dir) if isinstance(v, str) else v
                     for k, v in b.items()}
        for key in ("lifespan_raster", "design_raster"):
            if key in a:
                same_raster(a[key], b[key])
    shear = sorted(os.listdir(tmp_path / "whole"))
    assert shear == sorted(os.listdir(tmp_path / "blocks"))
    for name in shear:
        if name.startswith(("ts", "tb", "hks", "regime")):
            same_raster(str(tmp_path / "whole" / name), str(tmp_path / "blocks" / name))


# --------------------------------------------------------------- preprocessing

def _condition_paths():
    from riverarchitect.condition import Condition

    condition = Condition("2100_sample")
    return (condition, condition.path(condition.dem_raster),
            condition.path(condition.depth_raster_for(750.0)),
            condition.path(condition.velocity_raster_for(750.0)))


@pytest.mark.parametrize("method, step", [("nearest", 1), ("nearest", 3), ("idw", 2)])
def test_water_surface_products(sample_home, modes, tmp_path, method, step):
    from riverarchitect import preprocessing as pre

    _condition, dem, depth, _velocity = _condition_paths()

    def run(tag):
        out = tmp_path / tag
        out.mkdir()
        pre.detrended_dem(dem, depth, str(out / "det.tif"), method=method, step=step)
        pre.water_level_elevation(dem, depth, str(out / "wle.tif"), method=method,
                                  step=step)
        # From the file in both modes: in memory the float64 surface would be passed on,
        # block by block its float32 copy on disk.
        wle = str(out / "wle.tif")
        pre.interpolated_depth(dem, depth, str(out / "h.tif"), wle=wle)
        pre.depth_to_water_table(dem, depth, str(out / "d2w.tif"), wle=wle)
        return out

    whole, parts = modes(run)
    dem_array = raster.read(dem)[0]
    for name in ("det.tif", "h.tif", "d2w.tif"):
        same_raster(str(whole / name), str(parts / name))
    # The surface is extrapolated over the whole grid in memory, and only over blocks
    # holding terrain block by block.
    a, b = raster.read(str(whole / "wle.tif"))[0], raster.read(str(parts / "wle.tif"))[0]
    kept = np.isfinite(b)
    np.testing.assert_array_equal(a[kept], b[kept])
    from riverarchitect import tiled

    config.TILING, config.BLOCK_SIZE = "always", BLOCK
    try:
        for block in tiled.blocks(raster.profile_of(dem)):
            rows, cols = block.window.toslices()
            if np.isfinite(dem_array[rows, cols]).any():
                assert kept[rows, cols].all()
    finally:
        config.TILING = "never"


def test_morphological_units_and_shear(sample_home, modes, tmp_path):
    from riverarchitect import preprocessing as pre

    condition, _dem, depth, velocity = _condition_paths()

    def run(tag):
        out = tmp_path / tag
        out.mkdir()
        pre.morphological_units(depth, velocity, str(out / "mu.tif"), unit="us")
        results = pre.bed_shear_stress(condition, unit="us", output_dir=str(out),
                                       discharges=[300.0, 750.0, 42200.0])
        return out, results

    (whole, a), (parts, b) = modes(run)
    assert [r["regime"] for r in a] == [r["regime"] for r in b]
    assert sorted(os.listdir(whole)) == sorted(os.listdir(parts))
    for name in os.listdir(whole):
        same_raster(str(whole / name), str(parts / name))


def test_align_condition(sample_home, modes, tmp_path):
    from riverarchitect import preprocessing as pre

    condition, _dem, _depth, _velocity = _condition_paths()

    def run(tag):
        out = tmp_path / tag
        return out, pre.align_condition(condition.directory, output_dir=str(out),
                                        pattern="[bdf]*.tif")

    (whole, a), (parts, b) = modes(run)
    assert a == b and "aligned" in a.values()
    for name in os.listdir(whole):
        same_raster(str(whole / name), str(parts / name))


# ----------------------------------------------------------------- Recruitment

def test_recruitment(sample_home, modes, tmp_path):
    pytest.importorskip("openpyxl")
    from riverarchitect.recruitment import RecruitmentPotential

    flows = os.path.join(config.dir_flows(), "2100_sample", "flow_series_2020.csv")

    def run(tag):
        if tag == "blocks":
            # Four blocks rather than thirty: each reads the day-by-day water surfaces.
            config.BLOCK_SIZE = (97, 190)
        analysis = RecruitmentPotential("2100_sample", flows, year=2020, unit="us")
        return analysis.run(output_dir=str(tmp_path / tag))

    whole, parts = modes(run)
    assert whole["recruitment_area"] > 0
    for key in ("crop_area", "recruitment_area", "partial_area", "objectives"):
        assert whole[key] == parts[key], key
    assert sorted(whole["rasters"]) == sorted(parts["rasters"])
    for name, path in whole["rasters"].items():
        same_raster(path, parts["rasters"][name])
    assert not [n for n in os.listdir(tmp_path / "blocks") if n.startswith("wle")]


# -------------------------------------------------------------------- Stranding

STRANDING_Q = [2000.0, 1000.0, 750.0, 500.0, 300.0]


def _stranding_equal(whole, parts, directory_whole, directory_parts):
    import geopandas as gpd

    for key in ("max_wetted_area", "total_disconnected_area", "worst_discharge",
                "worst_stranded_area", "velocity_limited"):
        assert whole[key] == parts[key], key
    assert whole["per_discharge"] == parts["per_discharge"]
    assert any(row["pools"] > 1 for row in whole["per_discharge"])
    names = sorted(n for n in os.listdir(directory_whole) if n.endswith(".tif"))
    assert names == sorted(n for n in os.listdir(directory_parts) if n.endswith(".tif"))
    for name in names:
        same_raster(str(directory_whole / name), str(directory_parts / name))
    if "pools_layer" in whole:
        a, b = gpd.read_file(whole["pools_layer"]), gpd.read_file(parts["pools_layer"])
        assert len(a) == len(b)
        assert a.geometry.area.sum() == pytest.approx(b.geometry.area.sum(), rel=1e-12)
        assert a.union_all().symmetric_difference(b.union_all()).area == \
            pytest.approx(0.0, abs=1e-6)


@pytest.mark.parametrize("target", [None, False])
def test_stranding_components(sample_home, modes, tmp_path, target):
    from riverarchitect.stranding import StrandingRisk

    def run(tag):
        analysis = StrandingRisk("2100_sample", discharges=STRANDING_Q, h_min=0.3,
                                 target_discharge=target, unit="us")
        return analysis.run(output_dir=str(tmp_path / tag))

    whole, parts = modes(run)
    _stranding_equal(whole, parts, tmp_path / "whole", tmp_path / "blocks")


@pytest.mark.parametrize("target", [None, False])
def test_stranding_escape_routes(sample_home, modes, tmp_path, target):
    """The directed search, with a flow direction invented from the speed raster."""
    from riverarchitect.condition import Condition
    from riverarchitect.stranding import StrandingRisk

    condition = Condition("2100_sample")

    def field(discharge, reference):
        speed, profile = raster.read(condition.path(condition.velocity_raster_for(discharge)))
        speed = raster.align(speed, profile, reference)
        rows, cols = np.indices(speed.shape)
        angle = 0.02 * cols + 0.05 * rows              # meandering, but deterministic
        return speed * np.cos(angle), speed * np.sin(angle)

    def run(tag):
        analysis = StrandingRisk("2100_sample", discharges=STRANDING_Q[1:], h_min=0.3,
                                 u_max=1.5, velocity_field=field, target_discharge=target,
                                 unit="us")
        assert analysis.velocity_limited
        return analysis.run(output_dir=str(tmp_path / tag), write_escape_routes=True)

    whole, parts = modes(run)
    _stranding_equal(whole, parts, tmp_path / "whole", tmp_path / "blocks")


# ------------------------------------------ MaxLifespan, Terraforming, volumes

@pytest.fixture
def lifespan_maps(sample_home, tmp_path_factory):
    """Plant lifespan maps of the sample reach, made once in memory."""
    from riverarchitect.lifespan import LifespanDesign

    output = tmp_path_factory.mktemp("lf")
    LifespanDesign("2100_sample", unit="us").run(["cot", "wil", "whi", "rocks"],
                                                  output_dir=str(output))
    return output


def test_max_lifespan_and_terraforming(lifespan_maps, modes, tmp_path):
    import geopandas as gpd

    from riverarchitect.maxlifespan import MaxLifespan
    from riverarchitect.terraforming import Terraforming

    def run(tag):
        best = MaxLifespan(str(lifespan_maps), unit="us").run(
            output_dir=str(tmp_path / tag / "max"))
        terrain = Terraforming("2100_sample", best["output_dir"], unit="us",
                               d2w_max=3.0).run(output_dir=str(tmp_path / tag / "tf"))
        return best, terrain

    (best_a, terrain_a), (best_b, terrain_b) = modes(run)
    assert best_a["total_mapped_area"] == best_b["total_mapped_area"]
    same_raster(best_a["max_lifespan_raster"], best_b["max_lifespan_raster"])
    for a, b in zip(best_a["features"], best_b["features"]):
        assert {k: v for k, v in a.items() if k not in ("raster", "polygons")} == \
            {k: v for k, v in b.items() if k not in ("raster", "polygons")}
        same_raster(a["raster"], b["raster"])
        assert ("polygons" in a) == ("polygons" in b)
        if "polygons" in a:
            x, y = gpd.read_file(a["polygons"]), gpd.read_file(b["polygons"])
            assert len(x) == len(y)
            assert x.union_all().symmetric_difference(y.union_all()).area == \
                pytest.approx(0.0, abs=1e-6)

    assert terrain_a["modified_cells"] > 0
    for key in ("modified_cells", "modified_area", "max_cut"):
        assert terrain_a[key] == terrain_b[key], key
    assert terrain_a["cut_volume"] == pytest.approx(terrain_b["cut_volume"], rel=1e-12)
    same_rows(terrain_a["per_feature"], terrain_b["per_feature"],
              exact=("feature", "cells", "area", "max_cut"), approx=("volume",))
    for key in ("dem_raster", "cut_raster", "d2w_raster"):
        same_raster(terrain_a[key], terrain_b[key])


def test_volume_assessment(sample_home, modes, tmp_path):
    from riverarchitect.volume_assessment import VolumeAssessment

    original = os.path.join(config.dir_conditions(), "2100_sample", "dem.tif")
    modified = tmp_path / "modified.tif"
    dem, profile = raster.read(original)
    rows, cols = np.indices(dem.shape)
    raster.write(str(modified), dem + 2.0 * np.sin(rows / 9.0) * np.cos(cols / 13.0),
                 profile)

    def run(tag):
        return VolumeAssessment(original, str(modified), unit="us").run(
            output_dir=str(tmp_path / tag))

    whole, parts = modes(run)
    assert whole["fill_volume"] > 0 and whole["excavation_volume"] > 0
    for key, value in whole.items():
        if key == "rasters":
            for name, path in value.items():
                same_raster(path, parts["rasters"][name])
        elif isinstance(value, float):
            assert value == pytest.approx(parts[key], rel=1e-12), key
        else:
            assert value == parts[key], key


def test_taux_tool(sample_home, modes, tmp_path):
    from riverarchitect.condition import Condition
    from riverarchitect.tools import taux

    condition = Condition("2100_sample")

    def run(tag):
        return taux.compute(condition.path(condition.velocity_raster_for(1000.0)),
                            condition.path(condition.depth_raster_for(1000.0)),
                            condition.path(condition.grain_raster),
                            str(tmp_path / tag / "q1000"), unit="us")

    whole, parts = modes(run)
    assert whole["_summary"] == parts["_summary"]
    for name in ("ustar2", "theta84", "h_over_ks", "regime"):
        same_raster(whole[name], parts[name])


def test_reconcile_nodata_streams(modes, tmp_path):
    import rasterio
    from rasterio.transform import from_origin

    from riverarchitect.tools import reconcile_nodata

    data = np.random.default_rng(8).random((90, 130)).astype("float32")
    data[::4, ::3] = -3.4e38
    profile = {"driver": "GTiff", "height": 90, "width": 130, "count": 1,
               "dtype": "float32", "crs": "EPSG:32610", "nodata": -3.4e38,
               "transform": from_origin(0.0, 90.0, 1.0, 1.0)}

    def run(tag):
        path = tmp_path / ("%s.tif" % tag)
        with rasterio.open(path, "w", **profile) as dst:
            dst.write(data, 1)
        assert reconcile_nodata.reconcile(str(path))
        return str(path)

    whole, parts = modes(run)
    same_raster(whole, parts)
    with rasterio.open(parts) as src:
        assert src.nodata == config.NODATA
        assert int(np.ma.count_masked(src.read(1, masked=True))) == data[::4, ::3].size


def test_derived_depth_leaves_an_existing_surface_alone(sample_home, monkeypatch, tmp_path):
    from riverarchitect import preprocessing as pre

    _condition, dem, depth, _velocity = _condition_paths()
    monkeypatch.setattr(config, "TILING", "always")
    monkeypatch.setattr(config, "BLOCK_SIZE", BLOCK)
    existing = tmp_path / "wle.tif"
    existing.write_bytes(b"not a raster, and it must stay so")
    pre.depth_to_water_table(dem, depth, str(tmp_path / "d2w.tif"))
    assert existing.read_bytes() == b"not a raster, and it must stay so"
    assert sorted(os.listdir(tmp_path)) == ["d2w.tif", "wle.tif"]


def test_recruitment_rejects_grain_in_the_wrong_units_without_rasters(sample_home, tmp_path,
                                                                       monkeypatch):
    """The all-NoData shear check holds block by block even when nothing is written."""
    pytest.importorskip("openpyxl")
    from riverarchitect.recruitment import RecruitmentPotential

    flows = os.path.join(config.dir_flows(), "2100_sample", "flow_series_2020.csv")
    monkeypatch.setattr(config, "TILING", "always")
    monkeypatch.setattr(config, "BLOCK_SIZE", (97, 190))
    analysis = RecruitmentPotential("2100_sample", flows, year=2020, unit="us")
    import riverarchitect.shear as shear

    # A grain size no closure accepts, as a raster in the wrong units would give.
    monkeypatch.setattr(shear, "d84_of", lambda grain, *a, **k: -np.abs(grain) - 1.0)
    with pytest.raises(ValueError, match="NoData everywhere"):
        analysis.run(output_dir=str(tmp_path / "out"), write_rasters=False)


def test_get_started_water_product(sample_home, modes, tmp_path):
    """What the Get Started tab builds: the derived rasters come from the float64 surface."""
    from riverarchitect import preprocessing as pre

    def run(tag):
        out = tmp_path / tag
        pre.build_product("2100_sample", "water", 750.0, output_dir=str(out), unit="us")
        return out

    whole, parts = modes(run)
    assert sorted(os.listdir(whole)) == sorted(os.listdir(parts))
    for name in ("h_interp.tif", "d2w.tif"):
        same_raster(str(whole / name), str(parts / name))
    a, b = raster.read(str(whole / "wle.tif"))[0], raster.read(str(parts / "wle.tif"))[0]
    np.testing.assert_array_equal(a[np.isfinite(b)], b[np.isfinite(b)])
