"""Tests for the cost and habitat-benefit assessment.

A bill of quantities is arithmetic, so these assert against the arithmetic: a rate times a
quantity, percentage rates compounding in order, and a cost-benefit ratio that is the one
divided by the other.
"""

import pytest

from riverarchitect.projectmaker import (COST_ITEMS, CUBIC_YARD, FT2_PER_ACRE, LOG_LENGTH,
                                         RATES, ProjectMaker, cost_items)


# --------------------------------------------------------------------- the rate table

def test_every_item_has_a_rate_and_a_unit_in_both_systems():
    for item in COST_ITEMS:
        for system in ("us", "si"):
            assert item.rate_for(system) > 0, item.key
            assert item.unit_for(system), item.key


def test_item_keys_are_unique():
    keys = [item.key for item in COST_ITEMS]
    assert len(keys) == len(set(keys))


def test_the_groups_match_the_original_workbook():
    groups = {item.group for item in COST_ITEMS}
    assert groups == {"Terraforming", "Stabilising bioengineering",
                      "Vegetation plantings", "Other bioengineering",
                      "Maintenance", "Civil engineering"}
    assert cost_items("Terraforming")
    assert len(cost_items()) == len(COST_ITEMS)


def test_the_percentage_rates_are_the_workbook_values():
    assert [(key, fraction) for key, _label, fraction in RATES] == [
        ("mobilisation", 0.10), ("contingency", 0.10),
        ("markups", 0.165), ("permitting", 0.35)]


# ---------------------------------------------------------------------------- costs

def test_a_cost_is_the_rate_times_the_quantity():
    maker = ProjectMaker(unit="us", quantities={"earthworks": 100.0})
    costs = maker.costs()
    line = [row for row in costs["lines"] if row["key"] == "earthworks"][0]
    assert line["cost"] == pytest.approx(100.0 * 23.0)
    assert costs["construction"] == pytest.approx(2300.0)


def test_an_empty_bill_totals_zero():
    costs = ProjectMaker().costs()
    assert costs["construction"] == 0.0
    assert costs["total"] == 0.0


def test_the_percentage_rates_compound_in_order():
    """Each is a fraction of the running total, not of the construction subtotal."""
    maker = ProjectMaker(unit="us", quantities={"earthworks": 100.0})
    costs = maker.costs()

    running = 2300.0
    for _key, _label, fraction in RATES:
        running += running * fraction
    assert costs["total"] == pytest.approx(running)
    # and the compounded total exceeds a naive sum of the same percentages
    assert costs["total"] > 2300.0 * (1 + sum(f for _k, _l, f in RATES))


def test_group_subtotals_sum_to_the_construction_total():
    maker = ProjectMaker(unit="us", quantities={"earthworks": 10.0, "geotextile": 5.0,
                                                "gravel": 2.0})
    costs = maker.costs()
    assert sum(costs["groups"].values()) == pytest.approx(costs["construction"])


def test_the_unit_system_selects_the_rate():
    us = ProjectMaker(unit="us", quantities={"clearing": 1.0}).costs()
    si = ProjectMaker(unit="si", quantities={"clearing": 1.0}).costs()
    # 220 US$ per acre against 0.0544 US$ per square metre
    assert us["construction"] == pytest.approx(220.0)
    assert si["construction"] == pytest.approx(0.0544)


def test_an_unknown_unit_system_is_refused():
    with pytest.raises(ValueError, match="unit must be"):
        ProjectMaker(unit="imperial")


# ------------------------------------------------------------------------ quantities

def make_summary(**areas):
    return {"features": [{"feature": key, "area": value} for key, value in areas.items()]}


def test_an_area_priced_per_acre_is_converted():
    maker = ProjectMaker(unit="us")
    maker.quantities_from_lifespan(make_summary(cot=FT2_PER_ACRE * 2))
    assert maker.quantities["pod_cottonwood"] == pytest.approx(2.0)


def test_an_area_priced_per_square_yard_is_converted():
    maker = ProjectMaker(unit="us")
    maker.quantities_from_lifespan(make_summary(rocks=900.0))
    assert maker.quantities["boulders"] == pytest.approx(100.0)


def test_an_area_priced_per_log_becomes_a_count():
    """One log occupies log_length squared - the original's workbook assumption."""
    maker = ProjectMaker(unit="us")
    maker.quantities_from_lifespan(make_summary(wood=LOG_LENGTH ** 2 * 40))
    assert maker.quantities["streamwood"] == pytest.approx(40.0)


def test_an_area_priced_per_length_is_left_for_the_user():
    """A rate per yard of bank does not follow from an area, so it must not be guessed."""
    maker = ProjectMaker(unit="us")
    maker.quantities_from_lifespan(make_summary(gravin=5000.0))
    assert "gravel" not in maker.quantities


def test_terraforming_supplies_the_earthworks_volume():
    maker = ProjectMaker(unit="us")
    maker.quantities_from_lifespan(
        make_summary(), terraforming={"cut_volume": CUBIC_YARD * 12, "modified_area": 0.0})
    assert maker.quantities["earthworks"] == pytest.approx(12.0)


def test_metric_volumes_are_not_converted():
    maker = ProjectMaker(unit="si")
    maker.quantities_from_lifespan(
        make_summary(), terraforming={"cut_volume": 500.0, "modified_area": 0.0})
    assert maker.quantities["earthworks"] == pytest.approx(500.0)


# -------------------------------------------------------------------------- benefit

def test_habitat_gain_is_the_difference_in_sharea():
    gain = ProjectMaker.habitat_gain({"sharea": 100.0}, {"sharea": 150.0})
    assert gain["gain"] == pytest.approx(50.0)
    assert gain["relative"] == pytest.approx(0.5)


def test_plain_numbers_are_accepted_too():
    assert ProjectMaker.habitat_gain(10.0, 25.0)["gain"] == pytest.approx(15.0)


def test_a_condition_without_a_flow_duration_curve_is_refused():
    """Comparing a SHArea against nothing is not a comparison."""
    with pytest.raises(ValueError, match="no SHArea"):
        ProjectMaker.habitat_gain({"sharea": None}, {"sharea": 10.0})


def test_a_project_that_loses_habitat_has_no_ratio(tmp_path):
    maker = ProjectMaker("shrink", unit="us", quantities={"earthworks": 10.0})
    result = maker.run(before=100.0, after=80.0, output_dir=str(tmp_path))
    assert result["habitat"]["gain"] < 0
    assert result["cost_per_area"] is None


# ------------------------------------------------------------------------------ run

def test_cost_per_area_is_the_total_over_the_gain(tmp_path):
    maker = ProjectMaker("demo", unit="us", quantities={"earthworks": 100.0})
    result = maker.run(before=1000.0, after=1500.0, output_dir=str(tmp_path))
    assert result["cost_per_area"] == pytest.approx(result["costs"]["total"] / 500.0)


def test_the_report_lists_only_the_priced_lines(tmp_path):
    maker = ProjectMaker("demo", unit="us", quantities={"earthworks": 100.0})
    result = maker.run(before=1.0, after=2.0, output_dir=str(tmp_path))

    text = open(result["report"], encoding="utf-8").read()
    assert "Excavate/fill alluvial material" in text
    assert "TOTAL" in text and "net gain" in text
    # an item with no quantity is not a line in the bill
    assert "Geotextile" not in text


def test_costing_without_a_benefit_still_works(tmp_path):
    result = ProjectMaker("demo", quantities={"earthworks": 1.0}).run(
        output_dir=str(tmp_path))
    assert result["costs"]["total"] > 0
    assert "habitat" not in result
