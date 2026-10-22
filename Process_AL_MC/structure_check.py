"""Shared, model-free checks for periodic structures and layered TM-O frameworks.

Energy is in eV/atom and lengths in Å. No file writes, RNG or model calls.
Framework rejection means outside the layered search domain, not physically impossible.
"""

from math import isfinite, pi

import numpy as np
from pymatgen.core import Structure

RULE = "periodic-tm-o-rank-local-coordination-v3"
ALKALI = {"Na", "Li", "K"}
DEFAULT_ENERGY_JUMP_PER_ATOM = 0.05


def compact_structure_check(result):
    """Keep serializable decisions/metrics without duplicating topology graphs in MC logs."""
    summary = dict(result)
    if "framework" in summary:
        summary["framework"] = {
            k: v
            for k, v in summary["framework"].items()
            if k not in {"initial", "final", "affected_tm_sites"}
        }
        local = summary["framework"].get("local_coordination")
        if local is not None:
            summary["framework"]["local_coordination"] = {
                k: v
                for k, v in local.items()
                if k not in {"initial_counts", "final_counts", "affected_tm_sites"}
            }
    return summary


def _structure(value):
    return value if isinstance(value, Structure) else Structure.from_file(value)


def check_structure(
    structure,
    *,
    expected_composition=None,
    reference=None,
    minimum_distance=0.6,
    energy_per_atom=None,
    check_framework=False,
):
    """Return passed/invalid/uncertain evidence; only invalid warrants exclusion.

    Basic checking uses a cutoff neighbor list, including periodic self images
    and distinct coincident atoms. minimum_distance reports the closest pair
    within the cutoff, or None (all pairs >= cutoff), not an all-pairs minimum.
    Framework context is prepared once from a trusted initial geometry.
    """
    if (
        isinstance(minimum_distance, bool)
        or not isfinite(minimum_distance)
        or minimum_distance <= 0
    ):
        raise ValueError("minimum_distance must be finite and positive")
    result = {
        "status": "passed",
        "scope": "basic",
        "failed_checks": [],
        "minimum_distance": None,
        "distance_cutoff_A": float(minimum_distance),
    }
    try:
        present = _structure(structure)
        if not len(present):
            raise ValueError("empty structure")
        if not present.is_ordered:
            result.update(
                status="uncertain", reason="disordered occupancy is unsupported"
            )
            return result
        if not (
            np.isfinite(present.frac_coords).all()
            and np.isfinite(present.lattice.matrix).all()
        ):
            raise ValueError("nonfinite coordinates or lattice")
        volume = float(present.volume)
        if not isfinite(volume) or volume <= 0:
            raise ValueError("nonpositive or nonfinite volume")
        # Non-overlapping spheres cannot fit in a cell smaller than their total volume.
        if volume / len(present) < pi / 6 * minimum_distance**3:
            raise ValueError("cell too small to avoid periodic overlaps")
        if energy_per_atom is not None and not isfinite(float(energy_per_atom)):
            result["failed_checks"].append("nonfinite_energy")
        expected = expected_composition
        if expected is None and reference is not None:
            expected = reference.composition
        observed = present.composition.get_el_amt_dict()
        if expected is not None and any(
            abs(float(observed.get(k, 0)) - float(expected.get(k, 0))) > 1e-6
            for k in set(observed) | set(expected)
        ):
            result["failed_checks"].append("composition")
        if result["failed_checks"]:
            result["status"] = "invalid"
            return result
        _, _, _, distances = present.get_neighbor_list(minimum_distance)
        if len(distances):
            result["minimum_distance"] = float(np.min(distances))
            if result["minimum_distance"] < minimum_distance:
                result["failed_checks"].append("minimum_distance")
        if result["failed_checks"]:
            result["status"] = "invalid"
            return result
        if check_framework:
            result["scope"] = "framework"
            framework = (
                reference.inspect(present)
                if reference is not None
                else {
                    "status": "uncertain",
                    "auto_confirmed": False,
                    "reason": "missing initial reference",
                }
            )
            result["framework"] = framework
            if framework["auto_confirmed"]:
                result["status"] = "invalid"
                local = framework.get("local_coordination") or {}
                result["failed_checks"].append(
                    "local_coordination"
                    if local.get("auto_confirmed")
                    else "layered_framework"
                )
            elif framework["status"] != "no_clear_destruction":
                result["status"] = "uncertain"
        return result
    except (OSError, ValueError, TypeError, KeyError) as error:
        result.update(
            status="invalid", failed_checks=["structure_data"], reason=str(error)
        )
        return result


def periodic_framework(structure, cutoff, *, neighbors=None):
    """Rank lattice translations around bond-graph cycles, not Cartesian axes."""
    import numpy as np

    names = [site.specie.symbol for site in structure]
    centers = {i for i, name in enumerate(names) if name not in ALKALI | {"O"}}
    if not centers:
        raise ValueError("无骨架阳离子")
    graph = {i: [] for i, name in enumerate(names) if name not in ALKALI}
    ci, ni, images, distances = (
        neighbors if neighbors is not None else structure.get_neighbor_list(cutoff)
    )
    for i, j, image, distance in zip(ci, ni, images, distances):
        i, j = int(i), int(j)
        if (
            i in graph
            and j in graph
            and 1e-8 < distance <= cutoff + 1e-8
            and ((names[i] == "O") != (names[j] == "O"))
        ):
            shift = np.rint(image).astype(int)
            graph[i].append((j, shift))
            graph[j].append((i, -shift))
    seen, ranks = set(), {}
    for start in graph:
        if start in seen:
            continue
        positions, cycles, stack = {start: np.zeros(3, dtype=int)}, [], [start]
        seen.add(start)
        while stack:
            i = stack.pop()
            for j, image in graph[i]:
                proposed = positions[i] + image
                if j not in positions:
                    positions[j] = proposed
                    seen.add(j)
                    stack.append(j)
                else:
                    cycle = proposed - positions[j]
                    if np.any(cycle):
                        cycles.append(cycle)
        rank = (
            int(np.linalg.matrix_rank(np.asarray(cycles, dtype=float))) if cycles else 0
        )
        for i in positions:
            ranks[i] = rank
    fractions = {
        str(rank): sum(ranks[i] == rank for i in centers) / len(centers)
        for rank in range(4)
    }
    pairs = set()
    for oxygen in (i for i in graph if names[i] == "O"):
        tm = sorted({j for j, _ in graph[oxygen] if j in centers})
        pairs.update((i, j) for k, i in enumerate(tm) for j in tm[k + 1 :])
    return {
        "cutoff_A": float(cutoff),
        "tm_rank_fractions": fractions,
        "tm_site_ranks": {str(i): ranks[i] for i in centers},
        "tm_neighbor_pairs": [list(pair) for pair in sorted(pairs)],
        "framework_cations": len(centers),
    }


class LayeredFrameworkReference:
    """Cache initial cutoffs/topology; index roles permit TM species exchanges.

    Site order must preserve O/backbone/alkali roles. Whole composition must
    match. Initial and trial geometries from one relaxation satisfy this binding;
    file-backed callers additionally verify provenance before using this class.
    """

    def __init__(self, structure, *, minimum_distance=0.6):
        initial = _structure(structure)
        self.composition = initial.composition.get_el_amt_dict()
        self.roles = []
        self.status, self.reason = "uncertain", ""
        self.before = []
        try:
            basic = check_structure(initial, minimum_distance=minimum_distance)
            if basic["status"] != "passed":
                raise ValueError("initial geometry failed basic checks")
            self.roles = self._roles(initial)
            names = [site.specie.symbol for site in initial]
            centers = [i for i, role in enumerate(self.roles) if role == "TM"]
            ci, ni, _, distances = initial.get_neighbor_list(4.0)
            shells = {i: [] for i in centers}
            for i, j, distance in zip(ci, ni, distances):
                if i in shells and names[j] == "O" and distance > 1e-8:
                    shells[i].append(float(distance))
            if not shells or any(len(shell) < 6 for shell in shells.values()):
                raise ValueError("initial six-oxygen neighborhoods incomplete")
            sixth = float(np.median([sorted(shell)[5] for shell in shells.values()]))
            self.cutoffs = [sixth * factor for factor in (1.10, 1.20, 1.30)]
            neighbors = initial.get_neighbor_list(max(self.cutoffs))
            self._tm_centers = np.asarray(centers, dtype=int)
            self._tm_mask = np.asarray([role == "TM" for role in self.roles])
            self._oxygen_mask = np.asarray([role == "O" for role in self.roles])
            self._initial_coordination = self._coordination_counts(neighbors)
            self.before = [
                periodic_framework(initial, cutoff, neighbors=neighbors)
                for cutoff in self.cutoffs
            ]
            if not all(p["tm_rank_fractions"]["2"] >= 0.99 for p in self.before):
                raise ValueError(
                    "initial framework is not confirmed layered at every cutoff"
                )
            self.status = "ready"
        except (ValueError, TypeError, KeyError) as error:
            self.reason = str(error)

    @staticmethod
    def _roles(structure):
        return [
            "O"
            if s.specie.symbol == "O"
            else "alkali"
            if s.specie.symbol in ALKALI
            else "TM"
            for s in structure
        ]

    def _coordination_counts(self, neighbors):
        """Count O neighbors from the same periodic table used by the bond graphs."""
        centers, points, _, distances = neighbors
        oxygen = self._oxygen_mask[points]
        return np.asarray(
            [
                np.bincount(
                    centers[oxygen & (distances <= cutoff)], minlength=len(self.roles)
                )[self._tm_centers]
                for cutoff in self.cutoffs
            ]
        )

    def _inspect_coordination(self, neighbors):
        counts = self._coordination_counts(neighbors)
        eligible = np.all(self._initial_coordination == 6, axis=0)
        persistent = eligible & (
            np.all(counts < 6, axis=0) | np.all(counts > 6, axis=0)
        )
        affected = set(self._tm_centers[persistent].tolist())
        connected = any(
            i in affected and j in affected
            for i, j in self.before[0]["tm_neighbor_pairs"]
        )
        confirmed = connected or (len(self._tm_centers) == 1 and bool(affected))
        changed = np.any(eligible & np.any(counts != 6, axis=0))
        status = (
            "changed_confirmed"
            if confirmed
            else ("uncertain" if changed or not np.all(eligible) else "preserved")
        )
        return {
            "status": status,
            "auto_confirmed": confirmed,
            "rule": "initial-O6-persistent-same-direction-adjacent-TM-three-cutoffs-v1",
            "eligible_tm_count": int(np.count_nonzero(eligible)),
            "reference_tm_count": len(self._tm_centers),
            "affected_tm_count": len(affected),
            "affected_tm_fraction": len(affected) / len(self._tm_centers),
            "affected_tm_sites": sorted(affected),
            "cutoffs_A": self.cutoffs,
            "initial_counts": self._initial_coordination.tolist(),
            "final_counts": counts.tolist(),
        }

    def _inspect_cutoff_sensitivity(self, structure, neighbors):
        """Screen an intact six-O shell using the existing maximum-cutoff table."""
        centers, points, images, distances = neighbors
        ids = np.flatnonzero(self._tm_mask[centers] & self._oxygen_mask[points])
        ids = ids[np.argsort(centers[ids], kind="stable")].reshape(-1, 6)
        margin = float(max(self.cutoffs) - np.max(distances[ids]))
        result = {
            "rule": "O6-middle-upper-octahedral-angle-v1",
            "consistent": False,
            "max_angle_rms_deg": None,
            "angle_limit_deg": 12.0,
            "min_outer_margin_A": margin,
            "margin_limit_A": 0.1,
        }
        if margin < result["margin_limit_A"]:
            return result
        coordinates = structure.frac_coords
        vectors = (
            coordinates[points[ids]] + images[ids] - coordinates[self._tm_centers, None]
        ) @ structure.lattice.matrix
        unit = vectors / distances[ids, None]
        dots = np.einsum("tij,tkj->tik", unit, unit)
        pairs = np.triu_indices(6, 1)
        angles = np.sort(
            np.degrees(np.arccos(np.clip(dots[:, pairs[0], pairs[1]], -1, 1))), axis=1
        )
        ideal = np.asarray([90] * 12 + [180] * 3)
        worst = float(np.max(np.sqrt(np.mean((angles - ideal) ** 2, axis=1))))
        result.update(
            max_angle_rms_deg=worst, consistent=worst <= result["angle_limit_deg"]
        )
        return result

    def inspect(self, structure):
        """Apply the existing sufficient domain-rejection rule, never a validity proof."""
        result = {"rule": RULE, "status": "uncertain", "auto_confirmed": False}
        if self.status != "ready":
            return {**result, "reason": self.reason}
        if structure.composition.get_el_amt_dict() != self.composition:
            return {**result, "reason": "initial/final compositions do not correspond"}
        if self._roles(structure) != self.roles:
            return {**result, "reason": "initial/final site roles do not correspond"}
        neighbors = structure.get_neighbor_list(max(self.cutoffs))
        local = self._inspect_coordination(neighbors)
        result["local_coordination"] = local
        after = [
            periodic_framework(structure, cutoff, neighbors=neighbors)
            for cutoff in self.cutoffs
        ]
        affected = set.intersection(
            *[
                {int(i) for i, rank in p["tm_site_ranks"].items() if rank != 2}
                for p in after
            ]
        )
        count = self.roles.count("TM")
        connected = any(
            i in affected and j in affected
            for i, j in self.before[0]["tm_neighbor_pairs"]
        )
        result.update(
            initial=self.before,
            final=after,
            local_rule="至少两个初始相邻TM在全部截断下失去二维骨架；单TM原胞按其周期网络判断",
            minimum_nonlayered_tm_fraction=min(
                1 - p["tm_rank_fractions"]["2"] for p in after
            ),
            affected_tm_sites=sorted(affected),
            affected_tm_count=len(affected),
            affected_tm_fraction=len(affected) / count,
        )
        if (connected and len(affected) >= 2) or (count == 1 and len(affected) == 1):
            result.update(
                status="destroyed_confirmed",
                auto_confirmed=True,
                reason="三个键长截断下同一局部相邻TM区域均失去二维层状连通骨架",
            )
        elif local["auto_confirmed"]:
            result.update(
                status="coordination_damage_confirmed",
                auto_confirmed=True,
                reason="初始稳定六配位的相邻TM在三个固定截断下持续欠配位或持续过配位",
            )
        elif (
            all(p["tm_rank_fractions"]["2"] >= 0.99 for p in after)
            and local["status"] == "preserved"
        ):
            result.update(
                status="no_clear_destruction",
                reason="三个截断下保留二维TM–O骨架及初始稳定六配位；不等于结构已证明正常",
            )
        elif (
            all(p["tm_rank_fractions"]["2"] >= 0.99 for p in after)
            and local["status"] == "uncertain"
            and local["eligible_tm_count"] == local["reference_tm_count"]
            and np.all(np.asarray(local["final_counts"])[1:] == 6)
        ):
            sensitivity = self._inspect_cutoff_sensitivity(structure, neighbors)
            result["cutoff_sensitivity"] = sensitivity
            if sensitivity["consistent"]:
                local["status"] = "cutoff_sensitive"
                result.update(
                    status="no_clear_destruction",
                    warnings=["cutoff_sensitive_coordination"],
                    reason="仅小截断少计氧；中大截断六配位、二维骨架及角度筛查通过，保留截断敏感提示",
                )
            else:
                result["reason"] = "截断敏感但六氧壳层几何证据不足，保留未知"
        else:
            result["reason"] = "局部变化或截断间结论不一致，需人工判断可能重构"
        return result
