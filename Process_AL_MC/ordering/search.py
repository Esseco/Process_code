"""TM-focused joint MC over a relaxed, fixed-reference occupation landscape."""

import math
import random
from pathlib import Path

from pymatgen.core import Structure

from .common import occupation_key, tm_key, write_json
from .planning import build_structure, random_occupation


def trial(occupation, matrix, config, rng):
    na = list(occupation["na"])
    tm = list(occupation["tm"])
    occupied = [i for i, v in enumerate(na) if v]
    vacant = [i for i, v in enumerate(na) if not v]
    can_na = matrix["move_kind"] == "na_tm" and bool(occupied and vacant)
    can_tm = len(set(tm)) > 1
    choose_na = can_na and (not can_tm or rng.random() < config["na_move_fraction"])
    if choose_na:
        i, j = rng.choice(occupied), rng.choice(vacant)
        na[i], na[j] = na[j], na[i]
    elif can_tm:
        i = rng.randrange(len(tm))
        j = rng.choice([k for k, s in enumerate(tm) if s != tm[i]])
        tm[i], tm[j] = tm[j], tm[i]
    else:
        return None
    return {"na": na, "tm": tm}


def run_chain(plan, matrix, initial, chain_index, root, store, evaluator):
    config = plan["options"]
    seed = config["seed"] + int(matrix["matrix_id"][:8], 16) + chain_index
    owner = f"{matrix['matrix_id']}:chain-{chain_index}"
    rng = random.Random(seed)
    directory = Path(root) / "matrices" / matrix["matrix_id"]
    current = initial
    current_energy = None
    best = float("inf")
    repeats, restarts, stagnation, steps, cached = 0, 0, 0, 0, 0
    reason = "max_steps"

    def evaluate(occupation):
        key = occupation_key(occupation)
        claim = store.claim(
            key, tm_key(occupation), occupation, owner, budget=config["max_steps"] + 1
        )
        if claim["status"] == "cached":
            return claim["result"], False
        if claim["status"] != "claimed":
            return None, False
        structure = build_structure(matrix, occupation)
        context = {
            "phase": plan["phase"],
            "H": matrix["H"],
            "matrix_id": matrix["matrix_id"],
            "occupation_key": key,
            "tm_key": tm_key(occupation),
            "occupation": occupation,
            "seed": seed,
            "reference": matrix["reference"],
            "reference_site_ids": structure.site_properties["ordering_reference_id"],
            "evaluation_directory": str(directory / "evaluations" / key),
        }
        try:
            observation = evaluator(structure, context)
            energy = observation.get("energy_per_atom")
            if (
                isinstance(energy, bool)
                or not isinstance(energy, (int, float))
                or not math.isfinite(energy)
            ):
                raise ValueError(
                    "Evaluator must return finite main-model energy_per_atom in eV/atom"
                )
            final = observation.get("structure")
            if isinstance(final, Structure):
                final = final.as_dict()
            decoded = Structure.from_dict(final)
            if decoded.composition.get_el_amt_dict() != structure.composition.get_el_amt_dict():
                raise ValueError("Evaluation changed fixed composition")
            # Key provenance is retained separately from any serialized POSCAR ordering.
            path = directory / "structures" / f"{key}.vasp"
            path.parent.mkdir(parents=True, exist_ok=True)
            decoded.to(filename=str(path), fmt="poscar")
            result = {
                **observation,
                "structure": final,
                "energy_per_atom": float(energy),
                "phase": observation.get("phase") or "X",
                "converged": observation.get("converged") is True,
                "structure_path": str(path),
                "reference_site_ids": context["reference_site_ids"],
                "occupation_key": key,
                "tm_key": tm_key(occupation),
                "matrix_id": matrix["matrix_id"],
                "H": matrix["H"],
                "det_H": matrix["det_H"],
                "seed": seed,
                "model_version": plan["model"]["version"],
            }
            result["ranking_eligible"] = result["converged"] and result["phase"] == plan["phase"]
            store.complete(key, owner, result)
            return result, True
        except BaseException as error:
            store.fail(key, owner, error)
            raise

    for _ in range(config["max_duplicate_trials"]):
        first, new = evaluate(current)
        if first and first["ranking_eligible"]:
            current_energy = first["energy_per_atom"]
            best = current_energy
            break
        if (
            store.count_completed() >= matrix["space_size"]
            or store.calls(owner) >= config["max_steps"] + 1
        ):
            break
        current = random_occupation(matrix, rng)
    if current_energy is None:
        reason = "no_valid_initial_state"
    while current_energy is not None:
        if store.count_completed() >= matrix["space_size"]:
            reason = "occupation_space_evaluated"
            break
        if steps >= config["max_steps"] or store.calls(owner) >= config["max_steps"] + 1:
            reason = "max_steps"
            break
        candidate = trial(current, matrix, config, rng)
        if candidate is None:
            reason = "no_exchange_freedom"
            break
        observation, new = evaluate(candidate)
        if not new:
            repeats += 1
            cached += int(observation is not None)
        else:
            repeats = 0
            steps += 1
        if observation and observation["ranking_eligible"]:
            energy = observation["energy_per_atom"]
            # Energy is per atom; convert delta to total eV for the Metropolis factor.
            delta = (energy - current_energy) * len(Structure.from_dict(observation["structure"]))
            accept = delta <= 0 or (
                config["temperature"] > 0
                and rng.random() < math.exp(-delta / (8.617333262e-5 * config["temperature"]))
            )
            if accept:
                current, current_energy = candidate, energy
            if new:
                if energy < best - config["energy_tol"]:
                    best, stagnation = energy, 0
                else:
                    stagnation += 1
        elif new:
            stagnation += 1
        if repeats >= config["max_duplicate_trials"]:
            if restarts >= config["max_restarts"]:
                reason = "duplicate_stagnation"
                break
            restarts += 1
            repeats = 0
            restart = random_occupation(matrix, rng)
            restarted, new = evaluate(restart)
            steps += int(new)
            if restarted and restarted["ranking_eligible"]:
                current, current_energy = restart, restarted["energy_per_atom"]
        if stagnation >= config["patience"]:
            reason = "energy_stagnation"
            break
    summary = {
        "status": "completed",
        "matrix_id": matrix["matrix_id"],
        "chain_index": chain_index,
        "seed": seed,
        "stop_reason": reason,
        "actual_mlip_calls": store.calls(owner),
        "actual_new_mc_steps": steps,
        "cached_observations": cached,
        "restart_count": restarts,
        "consecutive_repeats": repeats,
    }
    write_json(directory / "chains" / f"{chain_index}.json", summary)
    return summary
