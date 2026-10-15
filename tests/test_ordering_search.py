from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json

import pytest
from pymatgen.core import Structure, Lattice

from Process_AL_MC import plan_ordering_search, prepare_ordering_search, run_ordering_search
from Process_AL_MC.ordering.history import OccupationStore
from Process_AL_MC.ordering.planning import build_structure


def reference():
    return Structure(
        Lattice.hexagonal(3, 10),
        ["Na", "Na", "Ni", "Ni", "O", "O", "O", "O"],
        [
            [0, 0, 0.15],
            [0.5, 0.5, 0.65],
            [0, 0, 0.4],
            [0.5, 0.5, 0.9],
            [0, 0.5, 0.3],
            [0.5, 0, 0.5],
            [0, 0.5, 0.8],
            [0.5, 0, 0],
        ],
    )


def plan(**kwargs):
    arguments = dict(
        phase="P2",
        tm_ratios={"Ni": 1, "Mn": 1},
        na_content="1/2",
        h_matrices=[[[1, 0, 0], [0, 1, 0], [0, 0, 1]]],
        oxidation_states={"Na": 1, "Ni": 3, "Mn": 4, "O": -2},
        model={"version": "fake", "model_path": "/remote/fake.model", "sha256": "0" * 64},
        options={
            "initial_pool_size": 12,
            "chains_per_H": 3,
            "max_steps": 4,
            "max_duplicate_trials": 4,
            "max_restarts": 2,
            "patience": 20,
            "workers": 3,
            "seed": 7,
            "min_distance": 0,
        },
    )
    arguments.update(kwargs)
    arguments["model"].setdefault("sha256", "0" * 64)
    return plan_ordering_search(reference(), **arguments)


def test_explicit_H_keeps_matrix_identity_and_integer_composition():
    result = plan()
    item = result["matrices"][0]
    assert item["H"] == [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    assert len(item["initial_occupations"]) == 3
    assert len({json.dumps(o, sort_keys=True) for o in item["initial_occupations"]}) == 3
    assert all(
        sum(o["na"]) == 1 and sorted(o["tm"]) == ["Mn", "Ni"] for o in item["initial_occupations"]
    )


def test_neutrality_and_range_errors_are_visible():
    with pytest.raises(ValueError, match="neutral"):
        plan(oxidation_states={"Na": 1, "Ni": 2, "Mn": 4, "O": -2})
    with pytest.raises(ValueError):
        plan(max_det_H=12)
    with pytest.raises(ValueError):
        plan(h_matrices=[[[0, 0, 0], [0, 1, 0], [0, 0, 1]]])


def test_shared_claim_is_atomic_across_workers(tmp_path):
    store = OccupationStore(tmp_path / "history.sqlite", {"identity": "exact-H-and-model"})

    def claim(i):
        return store.claim("same-key", "same-tm", {"na": [1, 0], "tm": ["Ni", "Mn"]}, str(i))[
            "status"
        ]

    with ThreadPoolExecutor(max_workers=8) as pool:
        statuses = list(pool.map(claim, range(20)))
    assert statuses.count("claimed") == 1
    assert statuses.count("busy") == 19


def test_run_joint_search_groups_TM_and_retains_all_Na_details(tmp_path):
    job = plan()
    prepared = prepare_ordering_search(job, tmp_path / "search")
    called = []

    def evaluate(structure, context):
        called.append(context["occupation_key"])
        energy = -sum(
            (i + 1) * (1 if s.specie.symbol == "Mn" else 0.1) for i, s in enumerate(structure)
        )
        return {
            "structure": structure.as_dict(),
            "energy_per_atom": energy,
            "converged": True,
            "phase": "P2",
            "max_force": 0,
        }

    result = run_ordering_search(prepared["directory"], evaluator=evaluate)
    assert len(called) == len(set(called))
    assert result["status"] == "completed"
    assert result["joint_count"] <= 4
    assert result["representative_count"] <= 2
    assert Path(result["global_ranking_csv"]).is_file()
    assert Path(result["all_joint_csv"]).is_file()
    again = run_ordering_search(
        prepared["directory"], evaluator=lambda *a: pytest.fail("cached run evaluates")
    )
    assert again["joint_count"] == result["joint_count"]


def test_wrong_phase_and_unconverged_are_diagnostics_only(tmp_path):
    prepared = prepare_ordering_search(plan(), tmp_path / "search")

    def evaluate(structure, context):
        return {
            "structure": structure.as_dict(),
            "energy_per_atom": -1,
            "converged": False,
            "phase": "O3",
        }

    result = run_ordering_search(prepared["directory"], evaluator=evaluate)
    assert result["representative_count"] == 0
    assert result["diagnostic_count"] > 0


def test_model_or_settings_change_cannot_reuse_run(tmp_path):
    prepared = prepare_ordering_search(plan(), tmp_path / "search")
    changed = plan(model={"version": "other", "model_path": "/remote/fake.model"})
    with pytest.raises(ValueError, match="different"):
        prepare_ordering_search(changed, prepared["directory"])


def test_fullNa_uses_TM_only_without_Na_swaps():
    result = plan(na_content=1, oxidation_states={"Na": 1, "Ni": 3, "Mn": 3, "O": -2})
    assert result["matrices"][0]["move_kind"] == "tm_only"
    assert result["matrices"][0]["space_size"] == 2


def test_upper_bound_enumeration_and_multiple_exact_matrices():
    result = plan(h_matrices=None, max_det_H=2)
    assert all(m["det_H"] <= 2 for m in result["matrices"])
    exact = plan(h_matrices=[[[1, 0, 0], [0, 1, 0], [0, 0, 1]], [[1, 1, 0], [0, 2, 0], [0, 0, 1]]])
    assert len(exact["matrices"]) == 2
    assert len({m["matrix_id"] for m in exact["matrices"]}) == 2


def test_default_pymatgen_and_optimized_ewald_match_direct_sum():
    from pymatgen.analysis.ewald import EwaldSummation

    result = plan(oxidation_states=None)
    matrix = result["matrices"][0]
    assert matrix["charge_source"] == "pymatgen_oxi_state_guesses"
    for occupation, expected in zip(
        matrix["initial_occupations"], matrix["initial_ewald_energies"]
    ):
        structure = build_structure(matrix, occupation)
        structure.unset_charge()
        structure.add_oxidation_state_by_element(matrix["charge_scheme"])
        assert float(EwaldSummation(structure).total_energy) == pytest.approx(expected, abs=1e-5)


def test_fixedNa_TM_only_initializations_share_exact_Na_pattern():
    result = plan(
        options={
            "move_kind": "tm_only",
            "min_distance": 0,
            "chains_per_H": 3,
            "initial_pool_size": 12,
        }
    )
    matrix = result["matrices"][0]
    assert len({tuple(o["na"]) for o in matrix["initial_occupations"]}) == 1
    assert matrix["space_size"] == 2


def test_generic_three_element_TM_encoding():
    expanded = reference().copy()
    expanded.make_supercell([3, 1, 1])
    result = plan_ordering_search(
        expanded,
        phase="P2",
        tm_ratios={"Co": 1, "Ni": 1, "Mn": 1},
        na_content=1,
        h_matrices=[[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        model={"version": "fake", "model_path": "fake", "sha256": "0" * 64},
        oxidation_states={"Na": 1, "Co": 3, "Ni": 3, "Mn": 3, "O": -2},
        options={"min_distance": 0, "initial_pool_size": 8},
    )
    assert result["matrices"][0]["tm_counts"] == {"Co": 2, "Mn": 2, "Ni": 2}


def test_running_claim_requires_explicit_reconciliation(tmp_path):
    store = OccupationStore(tmp_path / "history.sqlite", {"H": "one"})
    assert store.claim("key", "tm", {"na": [1], "tm": ["Ni"]}, "a")["status"] == "claimed"
    with pytest.raises(ValueError):
        store.reconcile("key", verified_not_running=False, note="checked")
    store.reconcile(
        "key", verified_not_running=True, note="external job stopped, no complete output"
    )
    assert store.claim("key", "tm", {"na": [1], "tm": ["Ni"]}, "b")["status"] == "claimed"


def test_duplicates_restart_without_extra_evaluations(tmp_path, monkeypatch):
    from Process_AL_MC.ordering.search import run_chain

    result = plan(
        options={
            "min_distance": 0,
            "max_steps": 2,
            "max_duplicate_trials": 3,
            "max_restarts": 2,
            "chains_per_H": 1,
            "initial_pool_size": 2,
            "patience": 20,
        }
    )
    matrix = result["matrices"][0]
    initial = matrix["initial_occupations"][0]
    store = OccupationStore(tmp_path / "history.sqlite", {"test": "duplicates"})
    calls = []

    def evaluate(structure, ctx):
        calls.append(ctx["occupation_key"])
        return {
            "structure": structure.as_dict(),
            "energy_per_atom": -1,
            "phase": "P2",
            "converged": True,
        }

    monkeypatch.setattr("Process_AL_MC.ordering.search.trial", lambda *args: initial)
    monkeypatch.setattr("Process_AL_MC.ordering.search.random_occupation", lambda *args: initial)
    summary = run_chain(result, matrix, initial, 0, tmp_path, store, evaluate)
    assert summary["stop_reason"] == "duplicate_stagnation"
    assert summary["restart_count"] == 2
    assert len(calls) == 1 and summary["actual_mlip_calls"] == 1


def test_two_H_rankings_do_not_collapse_across_H(tmp_path):
    result = plan(h_matrices=[[[1, 0, 0], [0, 1, 0], [0, 0, 1]], [[1, 1, 0], [0, 1, 0], [0, 0, 1]]])
    prepared = prepare_ordering_search(result, tmp_path / "search")

    def evaluate(structure, ctx):
        return {
            "structure": structure.as_dict(),
            "energy_per_atom": -1,
            "phase": "P2",
            "converged": True,
        }

    searched = run_ordering_search(prepared["directory"], evaluator=evaluate)
    assert searched["representative_count"] == 4
    assert all(
        (Path(prepared["directory"]) / "matrices" / m["matrix_id"] / "ranking.csv").is_file()
        for m in result["matrices"]
    )


def test_main_model_path_is_primary_and_not_passed_with_model_paths(monkeypatch):
    from Process_AL_MC.ordering.evaluation import MACEOrderingEvaluator
    from Process_AL_MC.ordering.common import options

    kwargs = []

    def fake(**values):
        kwargs.append(values)
        assert not (values.get("model_path") and values.get("model_paths"))
        return object()

    monkeypatch.setattr("Process_AL_MC.MC_sample.LayeredOxide_MCOrderingClass", fake)
    MACEOrderingEvaluator(
        {
            "model_path": "main",
            "model_paths": ["committee", "main"],
            "mace_default_dtype": "float32",
        },
        options(),
    )
    assert kwargs[0]["model_paths"] == ["main", "committee"]
    assert kwargs[0]["main_model_index"] == 0 and kwargs[0]["mace_default_dtype"] == "float32"


def test_result_directory_is_portable_and_corruption_detected(tmp_path):
    import shutil
    from Process_AL_MC import inspect_ordering_search

    prepared = prepare_ordering_search(plan(), tmp_path / "search")

    def evaluate(structure, ctx):
        return {
            "structure": structure.as_dict(),
            "energy_per_atom": -1,
            "phase": "P2",
            "converged": True,
        }

    run_ordering_search(prepared["directory"], evaluator=evaluate)
    shutil.copytree(prepared["directory"], tmp_path / "returned")
    inspected = inspect_ordering_search(tmp_path / "returned")
    assert inspected["global_ranking_csv"] == str(tmp_path / "returned" / "global_ranking.csv")
    with (tmp_path / "returned" / "global_ranking.csv").open("a", encoding="utf-8") as stream:
        stream.write("corrupted\n")
    with pytest.raises(ValueError, match="checksum"):
        inspect_ordering_search(tmp_path / "returned")


def test_repeats_and_restarts_preserve_claim_budget(tmp_path):
    store = OccupationStore(tmp_path / "history.sqlite", {"fixed": "budget"})
    assert store.claim("a", "a", {}, "owner", budget=1)["status"] == "claimed"
    store.fail("a", "owner", "fake failure")
    store.reconcile("a", verified_not_running=True, note="checked failure")
    assert store.claim("a", "a", {}, "owner", budget=1)["status"] == "budget_limit"
    assert store.calls("owner") == 1


@pytest.mark.parametrize(
    "bad",
    [
        {"max_steps": True},
        {"workers": 0},
        {"temperature": float("nan")},
        {"na_move_fraction": 2},
        {"relax_cell": 1},
        {"move_kind": "wrong"},
    ],
)
def test_invalid_options_are_rejected(bad):
    with pytest.raises(ValueError):
        plan(options=bad)


def test_model_bytes_are_frozen_before_prepare_and_first_execution(tmp_path):
    from Process_AL_MC.ordering.common import freeze_model, file_digest

    path = tmp_path / "main.model"
    path.write_bytes(b"approved model")
    model = freeze_model({"version": "v1", "model_path": str(path)})
    assert model["sha256"] == file_digest(path)
    job = plan(model=model)
    prepared = prepare_ordering_search(job, tmp_path / "search")
    path.write_bytes(b"replaced model")
    with pytest.raises(ValueError, match="checksum"):
        prepare_ordering_search(job, tmp_path / "other")
    with pytest.raises(ValueError, match="checksum"):
        run_ordering_search(prepared["directory"])
    with pytest.raises(ValueError, match="SHA"):
        freeze_model({"version": "remote", "model_path": str(tmp_path / "missing.model")})


@pytest.mark.parametrize("phase,repeats", [("P2", 7), ("O3", 5)])
def test_phase_layer_count_scales_with_c_repetition(monkeypatch, phase, repeats):
    from types import SimpleNamespace
    import numpy as np
    from Process_AL_MC.ordering.evaluation import identify_phase

    layers = int(phase[1:]) * repeats
    structure = Structure(
        Lattice.hexagonal(3, 10 * repeats),
        ["Na"] * layers,
        [[0, 0, i / layers] for i in range(layers)],
    )

    def neighbors(self, site, radius):
        result = []
        for z in (1, -1):
            offset = 0 if z == 1 or phase.startswith("P") else np.pi / 3
            for angle in np.arange(3) * 2 * np.pi / 3 + offset:
                result.append(
                    SimpleNamespace(
                        specie=SimpleNamespace(symbol="O"),
                        nn_distance=2,
                        coords=site.coords + np.array([np.cos(angle), np.sin(angle), z]),
                    )
                )
        return result

    monkeypatch.setattr(Structure, "get_neighbors", neighbors)
    assert identify_phase(structure, phase, [[1, 0, 0], [0, 1, 0], [0, 0, repeats]]) == phase
