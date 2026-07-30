"""Project Maker: what a design costs, and what it buys in habitat.

The open-source replacement for the ArcGIS ``ProjectMaker`` module. It is the last step of
the chain and the only one that produces a number a funding body recognises: the cost of the
works, the gain in seasonal habitat area, and the ratio between them.

The two halves
--------------
**Cost** is a bill of quantities. Every task in :data:`COST_ITEMS` carries a unit rate; the
quantity comes from what the earlier modules mapped - the per-feature areas of
:class:`riverarchitect.maxlifespan.MaxLifespan`, the excavation volume of
:class:`riverarchitect.terraforming.Terraforming`. Percentage rates for mobilisation,
contingency, markups and permitting are applied on top, in that order, as the original's
workbook did.

**Benefit** is the difference in SHArea between two conditions - the existing state and the
state with the project built - for one species and lifestage. Both come from
:meth:`riverarchitect.sharc.SHArC.run`, so the comparison is like for like.

Their ratio, **cost per unit of habitat gained**, is the metric that lets two designs be
compared when one is cheap and small and the other expensive and large.

Relation to the original
------------------------
The original kept the unit rates in a binary workbook of cross-sheet formulas
(``Project_assessment_vii.xlsx``), pulled quantities from a second sheet that a separate
arcpy step filled in, and computed the total with Excel. The rates are Python here, so a
change to them shows up in review, and the arithmetic is explicit rather than hidden in cell
references. The rates themselves are the workbook's, unchanged; several were averages of a
range, and those are recorded as the average with the range in the note.
"""

import logging
import os

from . import config

__all__ = ["CostItem", "COST_ITEMS", "RATES", "ProjectMaker", "cost_items", "FT2_PER_ACRE",
           "CUBIC_YARD", "LOG_LENGTH"]

logger = logging.getLogger("riverarchitect")

#: Square feet per acre, and cubic feet per cubic yard - the units the U.S. rates are per.
FT2_PER_ACRE = 43560.0
CUBIC_YARD = 27.0

#: Length of one log, in the project's length unit. The original carried it as the
#: ``log_length`` defined name of its workbook and used it to turn a mapped *area* into a
#: *count* of logs, assuming each occupies ``log_length`` squared. It is the only way an
#: area-based feature map can price a per-piece item, and it is an assumption worth stating.
LOG_LENGTH = 25.0


class CostItem:
    """One line of the bill of quantities.

    Args:
        key (str): short identifier, used to supply a quantity.
        group (str): the section it sums into.
        task (str): what the money buys.
        rate (dict): ``{"us": float, "si": float}`` unit rate in US dollars.
        unit (dict): ``{"us": str, "si": str}`` the unit the rate is per.
        source (str): where the quantity comes from by default, or "" when it must be given.
        note (str): provenance of the rate, e.g. the range it averages.
    """

    def __init__(self, key, group, task, rate, unit, source="", note=""):
        self.key = key
        self.group = group
        self.task = task
        self.rate = rate
        self.unit = unit
        self.source = source
        self.note = note

    def rate_for(self, unit_system):
        return float(self.rate[str(unit_system).lower()])

    def unit_for(self, unit_system):
        return self.unit[str(unit_system).lower()]

    def __repr__(self):
        return "CostItem(%r, %r)" % (self.key, self.task)


def _item(key, group, task, us, si, unit_us, unit_si, source="", note=""):
    return CostItem(key, group, task, {"us": us, "si": si},
                    {"us": unit_us, "si": unit_si}, source, note)


#: Unit rates, reproducing ``Project_assessment_vii.xlsx`` of the original. US dollars.
#: Kept as Python rather than a workbook so a change to a rate is reviewable.
COST_ITEMS = (
    # --- framework (terraforming) ----------------------------------------------------
    _item("clearing", "Terraforming", "Clearing (vegetation)",
          220.0, 0.0544, "acre", "m2", source="terraforming_area"),
    _item("earthworks", "Terraforming",
          "Excavate/fill alluvial material (incl. transport)",
          23.0, 23.0, "cubic yard", "m3", source="earthworks_volume"),
    _item("groin_cavities", "Terraforming", "Groin cavities",
          1200.0, 1200.0, "piece", "piece"),

    # --- nature-based engineering (stabilisation) ------------------------------------
    _item("log_anchoring", "Stabilising bioengineering",
          "Anchoring (logs for plant stability)", 80.0, 80.0, "yard", "m"),
    _item("log_jam", "Stabilising bioengineering",
          "Engineered log jam, log-wise", 775.0, 775.0, "log", "log",
          note="average of 600, 1000, 300, 1200"),
    _item("root_wad", "Stabilising bioengineering", "Engineered log jam, root-wise",
          49.875, 49.875, "rootwad", "rootwad", note="(1.65*15 + 75) / 2"),
    _item("streamwood", "Stabilising bioengineering", "Streamwood (non-anchored)",
          775.0, 775.0, "log", "log", source="wood",
          note="average of 600, 1000, 300, 1200"),
    _item("boulders", "Stabilising bioengineering",
          "Angular boulder placement (instream)", 150.0, 150.0, "sq yard", "m2",
          source="rocks"),

    # --- vegetation plantings ---------------------------------------------------------
    _item("ball_method", "Vegetation plantings", "Ball method (small trees)",
          210.0, 210.0, "piece", "piece", note="average of 120, 300"),
    _item("container_trees", "Vegetation plantings", "Container trees",
          33.0, 33.0, "tree", "tree", note="20 * 1.65"),
    _item("pod_cottonwood", "Vegetation plantings", "Pod method (Cottonwood)",
          72447.5, 17.9, "acre", "m2", source="cot", note="average of 73059, 71836"),
    _item("pod_willow", "Vegetation plantings", "Pod method (Willow)",
          72447.5, 17.9, "acre", "m2", source="wil", note="average of 73059, 71836"),
    _item("stinger_cottonwood", "Vegetation plantings", "Stinger method (Cottonwood)",
          40598.0, 10.03, "acre", "m2"),
    _item("stinger_willow", "Vegetation plantings", "Stinger method (Willow)",
          40598.0, 10.03, "acre", "m2"),
    _item("box_elder", "Vegetation plantings", "Other planting methods (Box Elder)",
          40000.0, 9.88, "acre", "m2", source="box", note="average of 35000, 45000"),
    _item("white_alder", "Vegetation plantings", "Other planting methods (White Alder)",
          40000.0, 9.88, "acre", "m2", source="whi", note="average of 35000, 45000"),

    # --- other bioengineering ---------------------------------------------------------
    _item("fascine", "Other bioengineering", "Fascine",
          80.0, 80.0, "sq yard", "m2", note="(60 + 100) / 2"),
    _item("fascine_slopes", "Other bioengineering", "Fascine on slopes",
          37.5, 37.5, "yard", "m", note="(25 + 50) / 2"),
    _item("geotextile", "Other bioengineering", "Geotextile",
          7.5, 7.5, "sq yard", "m2", note="(3 + 12) / 2"),
    _item("brush_layers", "Other bioengineering",
          "Lateral brush layers (ramified willow branches)",
          15.0, 15.0, "yard", "m", note="(10 + 20) / 2"),
    _item("rock_paving", "Other bioengineering",
          "Rock paving / layering (individually placed rocks)",
          157.5, 157.5, "sq yard", "m2", note="(140 + 175) / 2"),

    # --- maintenance --------------------------------------------------------------------
    _item("fine_sediment", "Maintenance", "Fine sediment",
          3750.0, 0.927, "acre", "m2", source="fines", note="average of 2500, 5000"),
    _item("gravel", "Maintenance", "Gravel (spawning substrate)",
          1500.0, 1500.0, "yard", "m", source="gravin", note="average of 1000, 2000"),

    # --- civil engineering and other ----------------------------------------------------
    _item("culvert_concrete", "Civil engineering", "Culvert: concrete PC 300",
          250.0, 250.0, "cubic yard", "m3"),
    _item("culvert_steel", "Civil engineering", "Culvert: reinforcement steel",
          1542.2, 1542.2, "short ton", "tonne", note="1700 * 0.9071847"),
    _item("road_existing", "Civil engineering", "Roads: develop existing",
          100.0, 100.0, "yard", "m"),
    _item("road_new_easy", "Civil engineering", "Roads: new (easy terrain)",
          150.0, 150.0, "yard", "m"),
    _item("road_new_complex", "Civil engineering", "Roads: new (complex terrain)",
          300.0, 300.0, "yard", "m"),
    _item("bridge_new", "Civil engineering", "Roads: new bridge",
          1000.0, 1000.0, "sq yard", "m2"),
    _item("bridge_reinforce", "Civil engineering", "Roads: reinforce existing bridge",
          1500.0, 1500.0, "sq yard", "m2"),
    _item("land", "Civil engineering", "Terrain acquisition",
          4.25, 5.08, "sq yard", "m2", source="project_area",
          note="average of 3.29, 4.21, 5.25"),
)

#: Percentage rates applied to the construction subtotal, in the order the workbook applies
#: them: each is a fraction of the running total *before* it.
RATES = (
    ("mobilisation", "Site (de-)mobilization", 0.10),
    ("contingency", "Unexpected", 0.10),
    ("markups", "Markups (overhead, profit, insurance)", 0.165),
    ("permitting", "Permitting", 0.35),
)


def cost_items(group=None):
    """The cost items, optionally restricted to one group."""
    return tuple(item for item in COST_ITEMS if group is None or item.group == group)


class ProjectMaker:
    """Cost, habitat gain, and the ratio between them.

    Args:
        name (str): project name, used for the output folder.
        unit (str): ``"us"`` or ``"si"``; selects the rate column and the units it is per.
        quantities (dict): ``{item key: quantity}`` in the unit each item is priced per.
            Anything not given is zero, so a partial bill still totals.
        rates (tuple): percentage rates. Defaults to :data:`RATES`.
        log_length (float): length of one log, for turning a mapped area into a count of
            pieces. See :data:`LOG_LENGTH`.

    Attributes:
        error (bool): True when something could not be quantified.
    """

    def __init__(self, name="project", unit="us", quantities=None, rates=RATES,
                 log_length=LOG_LENGTH):
        self.name = str(name)
        self.unit = str(unit).lower()
        if self.unit not in config.UNITS:
            raise ValueError("unit must be one of %s" % (config.UNITS,))
        self.quantities = dict(quantities or {})
        self.rates = tuple(rates)
        self.log_length = float(log_length)
        self.logger = logger
        self.error = False

    # ------------------------------------------------------------------- quantities

    def quantities_from_lifespan(self, summary, terraforming=None, project_area=None):
        """Fill the quantities from what the earlier modules reported.

        Args:
            summary (dict or list): the result of
                :meth:`riverarchitect.maxlifespan.MaxLifespan.run`, or its ``features``
                list. Each feature's area is matched to the cost item that names it as its
                source.
            terraforming (dict): the result of
                :meth:`riverarchitect.terraforming.Terraforming.run`, for the earthworks
                volume and the area cleared.
            project_area (float): total area acquired, in the area unit of the condition.

        Returns:
            dict: the quantities set, for inspection.
        """
        features = summary.get("features", []) if isinstance(summary, dict) else summary
        by_feature = {entry["feature"]: entry.get("area", 0.0) for entry in features}

        skipped = []
        for item in COST_ITEMS:
            if not item.source or item.source not in by_feature:
                continue
            quantity = self._to_rate_unit(by_feature[item.source], item)
            if quantity is None:
                skipped.append(item)
                continue
            self.quantities[item.key] = quantity

        if skipped:
            # Silently pricing 250 000 logs because a feature covers 250 000 square feet is
            # how a cost estimate becomes fiction. Say what could not be derived instead.
            self.logger.info(
                "      * no quantity derived for %s: priced per %s, which does not follow "
                "from a mapped area. Enter it directly.",
                ", ".join(item.key for item in skipped),
                ", ".join(sorted({item.unit_for(self.unit) for item in skipped})))

        if terraforming:
            volume = terraforming.get("cut_volume", 0.0)
            # Terraforming reports cubic length units; the US rate is per cubic yard.
            self.quantities["earthworks"] = volume / CUBIC_YARD if self.unit == "us" \
                else volume
            self.quantities["clearing"] = self._to_rate_unit(
                terraforming.get("modified_area", 0.0), _by_key("clearing"))

        if project_area is not None:
            self.quantities["land"] = self._to_rate_unit(project_area, _by_key("land"))

        return dict(self.quantities)

    def _to_rate_unit(self, area, item):
        """Convert a mapped area into the unit an item is priced per, or None.

        ``None`` means the conversion needs an assumption this cannot make - a rate per
        yard of bank or per culvert does not follow from an area at all - and the caller
        must supply the quantity.
        """
        unit = item.unit_for(self.unit)
        if unit in ("acre",):
            return area / FT2_PER_ACRE
        if unit in ("sq yard",):
            return area / 9.0
        if unit in ("m2",):
            return area
        if unit in ("log", "piece", "tree", "rootwad"):
            # One log occupies log_length squared, as the original's workbook assumed.
            return area / (self.log_length ** 2)
        return None

    # ------------------------------------------------------------------------ costs

    def costs(self):
        """The bill of quantities, its group subtotals, and the applied rates.

        Returns:
            dict: ``lines``, ``groups``, ``construction``, ``applied`` and ``total``.
        """
        lines, groups = [], {}
        for item in COST_ITEMS:
            quantity = float(self.quantities.get(item.key, 0.0) or 0.0)
            rate = item.rate_for(self.unit)
            total = quantity * rate
            lines.append({
                "key": item.key, "group": item.group, "task": item.task,
                "rate": rate, "unit": item.unit_for(self.unit),
                "quantity": quantity, "cost": total, "note": item.note,
            })
            groups[item.group] = groups.get(item.group, 0.0) + total

        construction = sum(groups.values())
        applied, running = [], construction
        for key, label, fraction in self.rates:
            amount = running * fraction
            applied.append({"key": key, "label": label, "fraction": fraction,
                            "amount": amount})
            running += amount

        return {
            "lines": lines,
            "groups": groups,
            "construction": construction,
            "applied": applied,
            "total": running,
        }

    # ---------------------------------------------------------------------- benefit

    @staticmethod
    def habitat_gain(before, after):
        """Net gain in seasonal habitat area between two conditions.

        Args:
            before (dict or float): the existing condition's
                :meth:`riverarchitect.sharc.SHArC.run` result, or its SHArea directly.
            after (dict or float): the with-project condition, likewise.

        Returns:
            dict: ``before``, ``after``, ``gain`` and ``relative`` (the gain as a fraction
            of the existing habitat).

        Raises:
            ValueError: when a result carries no ``sharea`` - which means its condition had
                no flow duration curve, and the two numbers would not be comparable.
        """
        def sharea(value, label):
            if isinstance(value, dict):
                if value.get("sharea") is None:
                    raise ValueError(
                        "the %s condition has no SHArea. Build a flow duration curve for it "
                        "first (Get Started > analyze flows), or the comparison is not "
                        "like for like." % label)
                return float(value["sharea"])
            return float(value)

        first, second = sharea(before, "existing"), sharea(after, "with-project")
        return {
            "before": first,
            "after": second,
            "gain": second - first,
            "relative": (second - first) / first if first else float("inf"),
        }

    # ---------------------------------------------------------------------------- run

    def run(self, before=None, after=None, output_dir=None, write_report=True):
        """Cost the works, compare the habitat, and report the trade-off.

        Args:
            before, after (dict or float): the two SHArC results, or their SHArea values.
                Omit both to cost the works without a benefit.
            output_dir (str): where the report goes.
            write_report (bool): write a CSV bill of quantities.

        Returns:
            dict: the costs, the habitat gain, and the cost per unit of habitat gained.
        """
        output_dir = output_dir or os.path.join(config.dir_output("ProjectMaker"), self.name)
        result = {
            "project": self.name,
            "unit": self.unit,
            "area_unit": config.area_unit(self.unit),
            "costs": self.costs(),
        }

        if before is not None and after is not None:
            gain = self.habitat_gain(before, after)
            result["habitat"] = gain
            total = result["costs"]["total"]
            result["cost_per_area"] = (total / gain["gain"]) if gain["gain"] > 0 else None
            if gain["gain"] <= 0:
                self.logger.info("      * the project does not increase habitat area "
                                 "(%.0f -> %.0f) - there is no cost-benefit ratio to quote",
                                 gain["before"], gain["after"])

        if write_report:
            os.makedirs(output_dir, exist_ok=True)
            result["report"] = self.write_report(result, output_dir)
            result["output_dir"] = output_dir

        self.logger.info("   >> %s: construction %.0f, total %.0f US$",
                         self.name, result["costs"]["construction"],
                         result["costs"]["total"])
        return result

    def write_report(self, result, output_dir):
        """Write the bill of quantities as CSV."""
        import csv

        path = os.path.join(output_dir, "%s_costs.csv" % self.name)
        costs = result["costs"]
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["group", "task", "quantity", "unit", "rate (US$)",
                             "cost (US$)", "note"])
            for line in costs["lines"]:
                if not line["quantity"]:
                    continue
                writer.writerow([line["group"], line["task"], "%.3f" % line["quantity"],
                                 line["unit"], "%.2f" % line["rate"],
                                 "%.2f" % line["cost"], line["note"]])
            writer.writerow([])
            for group, amount in costs["groups"].items():
                if amount:
                    writer.writerow(["SUM", group, "", "", "", "%.2f" % amount, ""])
            writer.writerow(["SUM", "TOTAL CONSTRUCTION WORKS", "", "", "",
                             "%.2f" % costs["construction"], ""])
            writer.writerow([])
            for entry in costs["applied"]:
                writer.writerow(["RATE", entry["label"], "%.1f%%" % (entry["fraction"] * 100),
                                 "", "", "%.2f" % entry["amount"], ""])
            writer.writerow(["TOTAL", "", "", "", "", "%.2f" % costs["total"], ""])

            if "habitat" in result:
                habitat = result["habitat"]
                writer.writerow([])
                writer.writerow(["HABITAT", "SHArea before", "%.2f" % habitat["before"],
                                 result["area_unit"], "", "", ""])
                writer.writerow(["HABITAT", "SHArea after", "%.2f" % habitat["after"],
                                 result["area_unit"], "", "", ""])
                writer.writerow(["HABITAT", "net gain", "%.2f" % habitat["gain"],
                                 result["area_unit"], "", "", ""])
                if result.get("cost_per_area"):
                    writer.writerow(["HABITAT", "cost per %s gained" % result["area_unit"],
                                     "", "", "", "%.2f" % result["cost_per_area"], ""])
        return path


def _by_key(key):
    """The cost item with this key."""
    for item in COST_ITEMS:
        if item.key == key:
            return item
    raise KeyError("no cost item %r" % key)
