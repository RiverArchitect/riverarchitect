"""Fish stranding risk from wetted areas that disconnect as a hydrograph recedes.

The open-source replacement for the ArcGIS ``StrandingRisk`` module. As discharge falls the
wetted area shrinks and breaks apart; pools that lose their connection to the main channel
trap fish. That is a connected-component problem: threshold the depth raster at the minimum
swimming depth of the species and lifestage in question, label the wetted regions, and every
region except the one still joined to the main channel is a stranding risk.

Outputs
-------
* one ``disconnected_<Q>.tif`` per discharge;
* ``Q_disconnect.tif`` - the highest discharge at which each cell was disconnected, i.e. the
  flow at which that spot becomes a trap as the hydrograph recedes;
* ``escape_<Q>.tif`` - the length of the cheapest route from each cell back to the mainstem,
  optionally, as the original's ``shortest_paths`` rasters held it;
* a polygon layer of the individual pools at the worst discharge;
* a per-discharge table of wetted area, stranded area and pool count.

Relation to the original
------------------------
The original built a weighted digraph over travel-permissible cells, ran Dijkstra's algorithm
outwards from the low-flow mainstem, and called a cell disconnected when no finite-cost route
reached it. The mainstem is the largest wetted region at the *lowest* analysed discharge, and
``target_discharge`` chooses which discharge defines it.

That search is :func:`riverarchitect.raster.least_cost_distance`, and it is what
:class:`StrandingRisk` runs. With only the depth criterion applied a route exists exactly
when the wetted region touches the mainstem, so the answer coincides with the
connected-component rule in :func:`riverarchitect.raster.disconnected_mask` - which is
faster, is used when no velocity field is supplied, and is checked against the Dijkstra
result in the test suite.

The velocity criterion
----------------------
A fish cannot swim upstream against more than ``u_max``, so fast water is a one-way door: it
can be drifted down but not climbed back up. That makes the graph **directed**, and a
directed graph needs the flow *direction*, not just its magnitude - conditions ship
``u<Q>.tif`` as a speed. Supply the components through ``velocity_field`` and the criterion
is applied; without them it is skipped and :attr:`StrandingRisk.velocity_limited` says so.

Applying it as an undirected mask instead - a cell is impassable when it is fast - is not a
usable approximation and the module will not do it silently: on the sample reach at 7250 cfs
only 0.4 % of the low-flow mainstem is slower than a juvenile Chinook's 1.9 fps, so the
mainstem itself would become unreachable and almost the whole wetted area would read as
stranded.
"""

import logging
import os

import numpy as np

from . import config, raster
from .condition import Condition, discharge_token

__all__ = ["TRAVEL_THRESHOLDS", "travel_thresholds", "StrandingRisk"]

logger = logging.getLogger("riverarchitect")

#: Fallback minimum swimming depth and maximum swimming speed per species and lifestage, in
#: U.S. customary units. The packaged ``Fish.xlsx`` is the authority - :meth:`for_fish` reads
#: it first, exactly as the original's ``cFish.get_travel_threshold`` did - and this table is
#: only consulted when the workbook defines no threshold for the pair asked for. Keys are
#: matched case-insensitively, because the workbook writes ``"Chinook Salmon"`` while the
#: literature and this table write ``"Chinook salmon"``.
TRAVEL_THRESHOLDS = {
    ("Chinook salmon", "fry"): {"h_min": 0.2, "u_max": 1.9},
    ("Chinook salmon", "juvenile"): {"h_min": 0.3, "u_max": 1.9},
    ("Chinook salmon", "adult"): {"h_min": 0.9, "u_max": 11.0},
}


def travel_thresholds(species, lifestage, fish=None):
    """Swimming thresholds for a species and lifestage.

    Reads the ``Fish.xlsx`` habitat database first and falls back to
    :data:`TRAVEL_THRESHOLDS`, so a pair the workbook does not cover still resolves and a
    project that has edited its workbook is honoured.

    Args:
        species (str): common name; case and spacing are ignored.
        lifestage (str): lifestage; case and spacing are ignored.
        fish (riverarchitect.sharc.FishDatabase): an open database to reuse. Optional.

    Returns:
        dict: ``{"h_min": ..., "u_max": ...}``, with whichever keys are defined.

    Raises:
        KeyError: when neither source defines a minimum swimming depth for the pair.
    """
    from_workbook = {}
    try:
        if fish is None:
            from .sharc import FishDatabase
            fish = FishDatabase()
        from_workbook = fish.travel_thresholds(species, lifestage)
    except Exception as exc:            # a missing or unreadable workbook is not fatal here
        logger.info("      * could not read the fish database (%s) - using the built-in "
                    "travel thresholds", exc)

    wanted = (str(species).strip().lower(), str(lifestage).strip().lower())
    fallback = {}
    for (name, stage), values in TRAVEL_THRESHOLDS.items():
        if (name.strip().lower(), stage.strip().lower()) == wanted:
            fallback = values
            break

    merged = dict(fallback)
    merged.update(from_workbook)
    if "h_min" not in merged:
        raise KeyError("no minimum swimming depth for %s %s in the fish database or the "
                       "built-in table" % (species, lifestage))
    return merged


class StrandingRisk:
    """Connectivity analysis over a receding hydrograph.

    Args:
        condition (Condition or str): the condition, or its name.
        discharges (list): discharges to walk, highest first. Defaults to every hydraulic
            raster in the condition, sorted descending.
        h_min (float): minimum swimming depth. Below it a cell does not count as wetted.
        unit (str): ``"us"`` or ``"si"``; must match the condition's rasters.
        connectivity (int): 4 (arcpy's ``RegionGroup`` default) or 8.
        target_discharge (float): the discharge whose main channel every other discharge is
            judged against. Defaults to the **lowest** analysed discharge, which is what the
            original's ``get_target_raster`` used: the mainstem is the largest wetted region
            at low flow, and a pool is stranded when no route reaches *it*. Pass ``False``
            to fall back to the largest region at each discharge separately.
        u_max (float): maximum swimming speed. Applied only together with
            ``velocity_field``; :meth:`for_fish` fills it from the habitat database.
        velocity_field (callable or dict): the flow *direction* the velocity criterion needs.
            Either a callable ``f(discharge, profile) -> (ux, uy)`` giving the eastward and
            northward velocity components on that grid, or a dict ``{discharge: (ux, uy)}``
            of arrays or raster paths. Defaults to ``ux<Q>.tif`` and ``uy<Q>.tif`` beside the
            condition's hydraulic rasters when both exist.

    Attributes:
        velocity_limited (bool): True when the velocity criterion is actually applied, which
            takes both a ``u_max`` and a velocity field. Recorded so a caller can state it
            alongside a result.
    """

    #: Species and lifestage the thresholds came from, when built by :meth:`for_fish`.
    species = None
    lifestage = None

    def __init__(self, condition, discharges=None, h_min=0.2, unit="us", connectivity=4,
                 target_discharge=None, u_max=None, velocity_field=None):
        self.condition = condition if isinstance(condition, Condition) \
            else Condition(condition)
        self.h_min = float(h_min)
        self.unit = str(unit).lower()
        self.connectivity = int(connectivity)
        self.u_max = None if u_max is None else float(u_max)
        self.logger = logger
        self.error = False

        # Scan the folder rather than trusting input_definitions.inp: that file lists only
        # the discharges carrying a flood return period, which is what lifespan mapping
        # needs. A recession analysis needs the low flows, and those are on disk but usually
        # not in the .inp.
        available = {}
        for name in self.condition.all_depth_rasters():
            discharge = self.condition.discharge_of(name)
            if discharge is not None:
                available[discharge] = self.condition.path(name)
        self._available = available

        if discharges is None:
            discharges = sorted(available, reverse=True)
        self.discharges = [float(q) for q in discharges if float(q) in available]
        if not self.discharges:
            raise ValueError("no depth rasters found for condition %r"
                             % self.condition.name)

        if target_discharge is None:
            target_discharge = min(self.discharges)
        elif target_discharge is not False:
            target_discharge = float(target_discharge)
            if target_discharge not in available:
                raise ValueError("no depth raster for the target discharge %g"
                                 % target_discharge)
        self.target_discharge = target_discharge
        self._target = None

        self.velocity_field = velocity_field if velocity_field is not None \
            else self._discover_velocity_components()

    @classmethod
    def for_fish(cls, condition, species="Chinook salmon", lifestage="fry", fish=None,
                 **kwargs):
        """Build with the travel thresholds of a species and lifestage.

        Args:
            condition (Condition or str): the condition, or its name.
            species (str): common name; case and spacing are ignored.
            lifestage (str): lifestage; case and spacing are ignored.
            fish (riverarchitect.sharc.FishDatabase): an open database to reuse. Optional.
            **kwargs: passed to the constructor. An explicit ``h_min`` or ``u_max`` wins
                over the database.
        """
        thresholds = travel_thresholds(species, lifestage, fish=fish)
        kwargs.setdefault("h_min", thresholds["h_min"])
        kwargs.setdefault("u_max", thresholds.get("u_max"))
        instance = cls(condition, **kwargs)
        instance.species = species
        instance.lifestage = lifestage
        return instance

    # --------------------------------------------------------------------- velocity

    def _discover_velocity_components(self):
        """``{discharge: (ux, uy)}`` for every discharge shipping both component rasters."""
        found = {}
        for discharge in self.discharges:
            token = discharge_token(discharge)
            paths = tuple("%s%s" % (prefix, token) for prefix in ("ux", "uy"))
            if all(self.condition.exists(name) for name in paths):
                found[discharge] = tuple(self.condition.path(name) for name in paths)
        if found:
            self.logger.info("   >> velocity components found for %d of %d discharge(s)",
                             len(found), len(self.discharges))
        return found or None

    @property
    def velocity_limited(self):
        """True when the velocity criterion is actually applied."""
        return self.u_max is not None and self.velocity_field is not None

    def velocity_components(self, discharge, reference):
        """Eastward and northward velocity at a discharge, or ``(None, None)``."""
        field = self.velocity_field
        if field is None:
            return None, None
        if callable(field):
            components = field(float(discharge), reference)
        else:
            components = field.get(float(discharge))
        if components is None:
            return None, None

        resolved = []
        for component in components:
            if isinstance(component, str):
                array, profile = raster.read(component)
                component = raster.align(array, profile, reference)
            resolved.append(np.nan_to_num(np.asarray(component, dtype="float64")))
        return resolved[0], resolved[1]

    def _travel_rule(self, discharge, reference, dx, dy):
        """``allowed(dr, dc)`` for :func:`riverarchitect.raster.least_cost_distance`.

        A fish moving from one cell to the next must hold its ground against whatever the
        flow does along that direction. Where the flow runs *with* the fish it costs nothing;
        where it runs against it, the fish has to make headway at up to ``u_max``. Taking the
        opposing component rather than the speed is what makes the graph directed: a chute
        too fast to climb can still be drifted down.
        """
        if not self.velocity_limited:
            return None
        ux, uy = self.velocity_components(discharge, reference)
        if ux is None:
            self.logger.info("      * no velocity components for Q = %g - the velocity "
                             "criterion does not apply there", discharge)
            return None

        def allowed(dr, dc):
            # Row indices grow southwards, so a step of +1 row moves -dy northwards.
            east, north = dc * abs(dx), -dr * abs(dy)
            length = float(np.hypot(east, north))
            along = (ux * east + uy * north) / length      # flow component along the step
            return along >= -self.u_max

        return allowed

    # ----------------------------------------------------------------------- target

    def _wet(self, discharge, reference):
        """Wetted mask at a discharge, on the reference grid."""
        depth, profile = raster.read(self._available[float(discharge)])
        depth = raster.align(depth, profile, reference)
        # nan_to_num keeps NoData out of the comparison rather than propagating it.
        return np.nan_to_num(depth) > self.h_min

    def main_channel(self, reference):
        """The mainstem a pool has to reach to count as connected, or None.

        The largest wetted region at :attr:`target_discharge`. Computed once and reused for
        every discharge, so a pool that is cut off at low flow stays counted as cut off even
        when a higher flow happens to make some floodplain patch larger than the channel.
        """
        if self.target_discharge is False:
            return None
        if self._target is None:
            wet = self._wet(self.target_discharge, reference)
            labels, count = raster.label_regions(wet, self.connectivity)
            if count == 0:
                self.logger.info("      * nothing is wetted at the target discharge %g - "
                                 "falling back to the largest region per discharge",
                                 self.target_discharge)
                self._target = np.zeros(wet.shape, dtype=bool)
            else:
                sizes = [int((labels == label).sum()) for label in range(1, count + 1)]
                self._target = labels == (int(np.argmax(sizes)) + 1)
                self.logger.info("   >> main channel from Q = %g: %d cell(s)",
                                 self.target_discharge, int(self._target.sum()))
        return self._target if self._target.any() else None

    # -------------------------------------------------------------- escape routes

    def escape_routes(self, discharge, reference=None):
        """Length of the cheapest route from each wetted cell back to the mainstem.

        Dijkstra's algorithm over the travel-permissible cells, exactly as the original's
        ``shortest_paths`` rasters were built: cells are vertices, steps between neighbours
        are edges weighted by the distance between cell centres, and where a velocity field
        applies the edges are one-way wherever the flow is faster than the fish can swim
        against.

        Args:
            discharge (float): the discharge to evaluate.
            reference (dict): profile every raster is aligned onto.

        Returns:
            numpy.ndarray: route length in map units, ``numpy.nan`` where dry or where no
            route to the mainstem exists at all - which is the stranding criterion.
        """
        reference = reference or raster.profile_of(self._available[self.discharges[0]])
        dx, dy = raster.cell_size(reference)
        wet = self._wet(discharge, reference)

        target = self.main_channel(reference)
        if target is None:
            # No low-flow mainstem to escape to: fall back on the largest wetted region at
            # this discharge, which is what target_discharge=False asks for.
            labels, count = raster.label_regions(wet, self.connectivity)
            if count == 0:
                return np.full(wet.shape, np.nan)
            sizes = [int((labels == label).sum()) for label in range(1, count + 1)]
            target = labels == (int(np.argmax(sizes)) + 1)

        seeds = target & wet
        if not seeds.any():
            return np.full(wet.shape, np.nan)
        return raster.least_cost_distance(
            wet, seeds, dx, dy, connectivity=self.connectivity,
            allowed=self._travel_rule(discharge, reference, dx, dy),
            towards_sources=True)

    def _disconnected(self, discharge, wet, reference):
        """``(mask, pools)`` of cells with no escape route, and how many pools they form."""
        if not self.velocity_limited:
            # Without a directed criterion a route exists exactly when the wetted region
            # touches the mainstem, so the component rule gives the same answer far faster.
            # `tests/test_lifespan.py` checks the two against each other on the sample reach.
            return raster.disconnected_mask(wet, connectivity=self.connectivity,
                                            target=self.main_channel(reference))
        mask = wet & ~np.isfinite(self.escape_routes(discharge, reference))
        _labels, pools = raster.label_regions(mask, self.connectivity)
        return mask, int(pools)

    # -------------------------------------------------------------------------- run

    def run(self, output_dir=None, write_rasters=True, write_escape_routes=False):
        """Walk the recession and quantify the disconnected area at each discharge.

        Args:
            output_dir (str): where the rasters go.
            write_rasters (bool): write the per-discharge disconnected masks and
                ``Q_disconnect.tif``.
            write_escape_routes (bool): also write one ``escape_<Q>.tif`` per discharge, the
                equivalent of the original's ``shortest_paths`` directory. Off by default
                because it doubles the number of files written.

        Returns:
            dict: ``per_discharge`` (list of row dicts), ``total_disconnected_area``,
            ``worst_discharge``, ``area_unit`` and the paths written.
        """
        output_dir = output_dir or os.path.join(
            config.dir_output("StrandingRisk"), self.condition.name)
        if write_rasters or write_escape_routes:
            os.makedirs(output_dir, exist_ok=True)

        reference = raster.profile_of(self._available[self.discharges[0]])
        dx, dy = raster.cell_size(reference)
        cell_area = dx * dy

        self.main_channel(reference)
        if self.u_max is not None and not self.velocity_limited:
            self.logger.info("   >> u_max = %g is recorded but not applied: the condition "
                             "carries flow speed, not direction. See velocity_field.",
                             self.u_max)

        rows = []
        per_discharge_masks = []
        for discharge in self.discharges:
            wet = self._wet(discharge, reference)

            mask, pools = self._disconnected(discharge, wet, reference)
            per_discharge_masks.append(raster.con(mask, float(discharge)))

            wetted_area = float(wet.sum() * cell_area)
            stranded_area = float(mask.sum() * cell_area)
            rows.append({
                "discharge": discharge,
                "pools": int(pools),
                "wetted_area": wetted_area,
                "stranded_area": stranded_area,
                "percent_stranded": (100.0 * stranded_area / wetted_area)
                                    if wetted_area else 0.0,
            })

            if write_rasters:
                raster.write(os.path.join(output_dir, "disconnected_%s.tif"
                                          % discharge_token(discharge)),
                             raster.con(mask, 1.0), reference)
            if write_escape_routes:
                raster.write(os.path.join(output_dir, "escape_%s.tif"
                                          % discharge_token(discharge)),
                             self.escape_routes(discharge, reference), reference)

        # The original expressed the disconnected area as a share of the wetted extent at
        # the *highest* discharge rather than at the discharge in hand, so the column is
        # comparable down the recession. It is the largest wetted extent that is meant, and
        # taking it by measurement rather than by discharge matters: on a condition holding
        # one bad hydraulic raster - as the sample reach does at 88053 cfs - the highest
        # discharge is not the wettest. Both bases are reported.
        reference_area = max((row["wetted_area"] for row in rows), default=0.0)
        for row in rows:
            row["percent_of_max_wetted"] = (100.0 * row["stranded_area"] / reference_area) \
                if reference_area else 0.0

        result = {
            "condition": self.condition.name,
            "h_min": self.h_min,
            "species": self.species,
            "lifestage": self.lifestage,
            "target_discharge": self.target_discharge,
            "max_wetted_area": reference_area,
            "per_discharge": rows,
            "area_unit": config.area_unit(self.unit),
            "discharge_unit": config.unit_labels(self.unit)["q"],
            "velocity_limited": self.velocity_limited,
            "u_max": self.u_max,
        }

        q_disconnect = raster.cell_statistics(per_discharge_masks, "MAXIMUM")
        result["total_disconnected_area"] = float(
            np.isfinite(q_disconnect).sum() * cell_area)

        worst = max(rows, key=lambda row: row["stranded_area"]) if rows else None
        result["worst_discharge"] = worst["discharge"] if worst else None
        result["worst_stranded_area"] = worst["stranded_area"] if worst else 0.0

        if write_rasters:
            path = os.path.join(output_dir, "Q_disconnect.tif")
            raster.write(path, q_disconnect, reference)
            result["q_disconnect_raster"] = path
            result["output_dir"] = output_dir
            if worst:
                pools_path = self.write_pools(worst["discharge"], output_dir, reference)
                if pools_path:
                    result["pools_layer"] = pools_path

        return result

    def write_pools(self, discharge, output_dir, reference=None):
        """Polygonise the disconnected pools at one discharge into a GeoPackage."""
        discharge = float(discharge)
        if discharge not in self._available:
            return None
        reference = reference or raster.profile_of(self._available[self.discharges[0]])

        mask, _pools = self._disconnected(discharge, self._wet(discharge, reference),
                                          reference)
        if not mask.any():
            return None

        pools = raster.polygonize(mask.astype("int32"), reference, mask=mask)
        pools["area"] = pools.geometry.area
        pools = pools.sort_values("area", ascending=False)
        path = os.path.join(output_dir, "pools_%s.gpkg" % discharge_token(discharge))
        try:
            pools.to_file(path, driver="GPKG")
        except Exception as exc:  # a missing vector driver must not lose the rasters
            self.logger.info("      * could not write %s (%s)", path, exc)
            return None
        return path
