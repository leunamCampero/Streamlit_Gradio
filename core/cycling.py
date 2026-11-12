"""
Cycling-network model of the PhD thesis (ECC 2025 / CDC 2025 / ITSC 2025 papers).

Everything the apps need, in one small module:

    traffic factor      f_a = psi * exp(AADT_a / 1000)   if DoS_a <= 4
                            = psi * 2.03                 if DoS_a == 5  (shared with pedestrians)
                            = psi                        if DoS_a == 6  (fully separated)
    cyclist distance    b_a = d_a * s_a * f_a ** rho     (s_a = slope factor, Table IV)
    upgrade cost        Cerema costs, EUR per metre, COST[from DoS][to DoS]

The Grenoble network (3,452 nodes, 4,993 edges, 308 km) is loaded from ``data/network``;
optimised networks from the papers are DoS vectors stored in ``data/solutions``.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

DATA = Path(__file__).resolve().parents[1] / "data"

# --------------------------------------------------------------------------------------
# Parameters (values of the papers)
# --------------------------------------------------------------------------------------
DOS_LEVELS = (1, 2, 3, 4, 5, 6)
DOS_NAMES = {
    6: "Dedicated bike lanes, fully separated",
    5: "Shared with pedestrians, separated from cars",
    4: "Mixed traffic, 30 km/h, no bike lane",
    3: "Shared roads with cycling pictograms",
    2: "Painted bike lanes",
    1: "Unmarked shared car-bike lanes",
}
DOS_COLORS = {6: "#1b7837", 5: "#5aae61", 4: "#7b8fc7", 3: "#fdae61", 2: "#f46d43", 1: "#b2182b"}
AADT = {6: 14_400, 5: 16_000, 4: 960, 3: 3_120, 2: 6_912, 1: 8_448}  # veh/day next to each DoS
RHO, PSI, KAPPA, PEDESTRIAN_FACTOR = 0.04, 0.84, 0.14, 2.03
SLOPE_TABLE = ((2.0, 1.0), (4.0, 1.371), (6.0, 2.203), (float("inf"), 4.239))
COST = {  # EUR per metre to go from DoS a (outer key) to DoS b (inner key)
    1: {1: 0, 2: 150, 3: 250, 4: 300, 5: 500, 6: 750},
    2: {2: 0, 3: 100, 4: 150, 5: 350, 6: 600},
    3: {3: 0, 4: 50, 5: 250, 6: 500},
    4: {4: 0, 5: 200, 6: 450},
    5: {5: 0, 6: 250},
    6: {6: 0},
}
COST_MATRIX = np.full((7, 7), np.inf)
for _a, _row in COST.items():
    for _b, _c in _row.items():
        COST_MATRIX[_a, _b] = _c

# Optimised networks from the papers: key -> (label, file in data/solutions or None)
SOLUTIONS = {
    "original": ("Today's network", None),
    "ecc2025_gab": ("ECC 2025 - GAB, 50 % budget", "ecc2025_gab.csv"),
    "ecc2025_mlcc": ("ECC 2025 - MLCC, 50 % budget", "ecc2025_mlcc.csv"),
    "cdc2025_ga_u": ("CDC 2025 - GA-U (utilitarian), 5.7 % budget", "cdc2025_ga_u.csv"),
    "cdc2025_ga_s": ("CDC 2025 - GA-S (sufficientarian, lambda 40 %), 5.7 % budget", "cdc2025_ga_s_lam40.csv"),
    "cdc2025_mlcc": ("CDC 2025 - MLCC, 5.7 % budget", "cdc2025_mlcc.csv"),
    "itsc2025_eps0.6": ("ITSC 2025 - GA, eps* = 0.6, 1/3 budget", "itsc2025_eps0.6.csv"),
}


# --------------------------------------------------------------------------------------
# Element-wise factors
# --------------------------------------------------------------------------------------
def traffic_factor(dos, psi: float = PSI, aadt: dict | None = None) -> np.ndarray:
    """f_a (Eq. 2) for an array of DoS levels."""
    aadt = AADT if aadt is None else aadt
    dos = np.asarray(dos)
    a = np.array([aadt[int(k)] for k in dos.ravel()], dtype=float).reshape(dos.shape) / 1000.0
    f = psi * np.exp(a)
    f = np.where(dos == 5, psi * PEDESTRIAN_FACTOR, f)
    return np.where(dos == 6, psi, f)


F_MIN = float(traffic_factor([6])[0])  # DoS 6 -> f_hat = 0
F_MAX = float(traffic_factor([1])[0])  # DoS 1 -> f_hat = 1


def traffic_factor_hat(dos) -> np.ndarray:
    """Min-max normalised traffic factor (used in the exposure J_E)."""
    return (traffic_factor(dos) - F_MIN) / (F_MAX - F_MIN)


def slope_factor(slope_pct) -> np.ndarray:
    """Uphill slope factor s_a (Table IV); downhill = reciprocal of the uphill value."""
    s = np.asarray(slope_pct, dtype=float)
    up = np.abs(s)
    out = np.ones_like(up)
    lower = -np.inf
    for upper, factor in SLOPE_TABLE:
        out = np.where((up >= lower) & (up < upper) & (up >= 2.0), factor, out)
        lower = upper
    return np.where(s >= 0, out, 1.0 / out)


def cyclist_distance(length_m, slope_pct, dos, rho: float = RHO, psi: float = PSI) -> np.ndarray:
    """b_a = d_a * s_a * f_a**rho for arrays of arcs."""
    return np.asarray(length_m, float) * slope_factor(slope_pct) * traffic_factor(dos, psi) ** rho


def dos_table(rho: float = RHO, psi: float = PSI) -> pd.DataFrame:
    """Table I of the papers + the factors that enter the model."""
    dos = np.array(DOS_LEVELS[::-1])
    f = traffic_factor(dos, psi)
    return pd.DataFrame({
        "DoS": dos,
        "description": [DOS_NAMES[d] for d in dos],
        "AADT (veh/day)": [AADT[d] for d in dos],
        "traffic factor f": f.round(3),
        "f^rho (route penalty)": (f ** rho).round(4),
        "f_hat (exposure)": traffic_factor_hat(dos).round(5),
    })


# --------------------------------------------------------------------------------------
# Network
# --------------------------------------------------------------------------------------
@dataclass
class Route:
    nodes: list[int]
    edges: list[int]
    length_m: float
    cyclist_distance: float
    km_per_dos: dict[int, float]
    exposure: float  # sum of d_a * f_hat_a (in km): km-equivalent of riding next to DoS-1 traffic

    def to_dict(self) -> dict:
        return {
            "n_nodes": len(self.nodes),
            "length_km": round(self.length_m / 1000, 3),
            "cyclist_distance_km": round(self.cyclist_distance / 1000, 3),
            "km_per_dos": {k: round(v, 3) for k, v in self.km_per_dos.items()},
            "km_exposed_dos_1_3": round(sum(self.km_per_dos[k] for k in (1, 2, 3)), 3),
            "exposure_km_equiv": round(self.exposure, 4),
        }


class GrenobleNetwork:
    """Grenoble bike network with routing, costs and the optimised networks of the papers."""

    def __init__(self, data: Path = DATA):
        self.data = Path(data)
        self.nodes = pd.read_csv(self.data / "network" / "grenoble_nodes.csv")
        self.edges = pd.read_csv(self.data / "network" / "grenoble_edges.csv")
        self.zones = pd.read_csv(self.data / "network" / "iris_zones.csv")
        self.N, self.E = len(self.nodes), len(self.edges)
        self.lon = self.nodes["lon"].to_numpy()
        self.lat = self.nodes["lat"].to_numpy()
        self.u = self.edges["u"].to_numpy()
        self.v = self.edges["v"].to_numpy()
        self.length = self.edges["length_m"].to_numpy()
        self.slope = self.edges["slope_pct"].to_numpy()
        self.dos0 = self.edges["dos"].to_numpy().astype(int)
        self._solutions: dict[str, np.ndarray] = {}

    # ---------------------------------------------------------------- solutions
    def dos(self, solution: str = "original") -> np.ndarray:
        """DoS vector (one value per edge) of a network from the papers."""
        if solution not in SOLUTIONS:
            raise KeyError(f"unknown solution {solution!r}; choose from {list(SOLUTIONS)}")
        if solution not in self._solutions:
            file = SOLUTIONS[solution][1]
            if file is None:
                d = self.dos0.copy()
            else:
                s = pd.read_csv(self.data / "solutions" / file).sort_values("edge_id")
                d = s["dos"].to_numpy().astype(int)
            self._solutions[solution] = d
        return self._solutions[solution]

    def km_per_dos(self, dos) -> dict[int, float]:
        dos = np.asarray(dos)
        return {k: float(self.length[dos == k].sum() / 1000) for k in DOS_LEVELS[::-1]}

    def upgrade_cost(self, dos, dos_from=None) -> float:
        dos_from = self.dos0 if dos_from is None else np.asarray(dos_from)
        return float(np.sum(self.length * COST_MATRIX[dos_from, np.asarray(dos)]))

    def max_budget(self) -> float:
        """B_max: cost of upgrading the whole network to DoS 6."""
        return self.upgrade_cost(np.full(self.E, 6))

    def summary(self, solution: str = "original") -> dict:
        d = self.dos(solution)
        cost = self.upgrade_cost(d)
        return {
            "solution": solution,
            "label": SOLUTIONS[solution][0],
            "km_per_dos": {k: round(v, 2) for k, v in self.km_per_dos(d).items()},
            "upgrade_cost_eur": round(cost),
            "share_of_B_max": round(cost / self.max_budget(), 4),
            "edges_upgraded": int(np.sum(d != self.dos0)),
        }

    # ---------------------------------------------------------------- geometry
    def nearest_node(self, lon: float, lat: float) -> int:
        k = np.cos(np.radians(lat))
        return int(np.argmin(((self.lon - lon) * k) ** 2 + (self.lat - lat) ** 2))

    def zone_node(self, zone_id: int) -> int:
        """Most 'central' node of an IRIS zone (largest share of the zone's demand)."""
        sub = self.nodes[self.nodes["zone_id"] == zone_id]
        if sub.empty:
            raise KeyError(f"no node in zone {zone_id}")
        return int(sub.loc[sub["zone_weight"].idxmax(), "node_id"])

    def edge_lines(self, dos=None, mask=None) -> dict[int, tuple[list, list]]:
        """For plotting: per DoS level, lon / lat lists with None between edges.

        mask: optional boolean array; only edges where mask is True are returned.
        """
        dos = self.dos0 if dos is None else np.asarray(dos)
        mask = np.ones(self.E, bool) if mask is None else np.asarray(mask, bool)
        out = {}
        for k in DOS_LEVELS:
            idx = np.flatnonzero((dos == k) & mask)
            lons = np.column_stack([self.lon[self.u[idx]], self.lon[self.v[idx]], np.full(len(idx), np.nan)])
            lats = np.column_stack([self.lat[self.u[idx]], self.lat[self.v[idx]], np.full(len(idx), np.nan)])
            out[k] = ([None if np.isnan(x) else x for x in lons.ravel()],
                      [None if np.isnan(x) else x for x in lats.ravel()])
        return out

    # ---------------------------------------------------------------- routing
    def _graph(self, dos: np.ndarray, weight: str, rho: float):
        if weight == "length":
            fwd = bwd = self.length
        else:
            fwd = cyclist_distance(self.length, self.slope, dos, rho)
            bwd = cyclist_distance(self.length, -self.slope, dos, rho)
        tail = np.concatenate([self.u, self.v])
        head = np.concatenate([self.v, self.u])
        cost = np.concatenate([fwd, bwd])
        eid = np.concatenate([np.arange(self.E), np.arange(self.E)])
        # keep only the cheapest arc when two edges join the same pair of nodes
        order = np.lexsort((cost, head, tail))
        tail, head, cost, eid = tail[order], head[order], cost[order], eid[order]
        first = np.ones(len(tail), bool)
        first[1:] = (tail[1:] != tail[:-1]) | (head[1:] != head[:-1])
        tail, head, cost, eid = tail[first], head[first], cost[first], eid[first]
        A = csr_matrix((cost, (tail, head)), shape=(self.N, self.N))
        lookup = dict(zip(zip(tail.tolist(), head.tolist()), eid.tolist()))
        return A, lookup

    def route(self, origin: int, destination: int, solution: str = "original",
              weight: str = "cyclist", rho: float = RHO) -> Route:
        """Shortest path for the cyclist distance (weight='cyclist') or plain length."""
        if weight not in ("cyclist", "length"):
            raise ValueError("weight must be 'cyclist' or 'length'")
        A, lookup = _cached_graph(self, solution, weight, round(rho, 6))
        dist, pred = dijkstra(A, directed=True, indices=origin, return_predecessors=True)
        if not np.isfinite(dist[destination]):
            raise ValueError(f"node {destination} is not reachable from node {origin}")
        path = [destination]
        while path[-1] != origin:
            path.append(int(pred[path[-1]]))
        path.reverse()
        edges = [lookup[(a, b)] for a, b in zip(path, path[1:])]
        dos = self.dos(solution)
        e = np.array(edges, dtype=int)
        fwd = np.array([self.u[i] == a for i, a in zip(edges, path)])
        slope = np.where(fwd, self.slope[e], -self.slope[e]) if len(e) else np.array([])
        b = cyclist_distance(self.length[e], slope, dos[e], rho) if len(e) else np.array([0.0])
        kms = {k: float(self.length[e][dos[e] == k].sum() / 1000) for k in DOS_LEVELS[::-1]}
        exposure = float(np.sum(self.length[e] * traffic_factor_hat(dos[e])) / 1000) if len(e) else 0.0
        return Route(path, edges, float(self.length[e].sum()), float(np.sum(b)), kms, exposure)

    def route_coords(self, route: Route) -> tuple[list[float], list[float]]:
        return self.lon[route.nodes].tolist(), self.lat[route.nodes].tolist()


@lru_cache(maxsize=32)
def _cached_graph(net: GrenobleNetwork, solution: str, weight: str, rho: float):
    return net._graph(net.dos(solution), weight, rho)


@lru_cache(maxsize=1)
def load_network() -> GrenobleNetwork:
    return GrenobleNetwork()


def load_result(name: str) -> pd.DataFrame:
    """A result table of the papers, e.g. load_result('cdc2025_summary')."""
    return pd.read_csv(DATA / "results" / f"{name}.csv")
