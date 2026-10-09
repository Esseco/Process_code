import gzip
import json
import math
import random
import shutil
from pathlib import Path

import numpy as np
from ase.filters import FrechetCellFilter
from ase.optimize import LBFGS
from pymatgen.core import Structure
from pymatgen.io.ase import AseAtomsAdaptor
from scipy.optimize import linear_sum_assignment


class LayeredOxide_MCOrderingClass:
    """MLIP relaxation and MC ordering for layered Na-TM-O systems.

    Supported modes are ``TM_MC_random``, ``TM_MC_input``,
    ``Na_MC_input``, and ``Relax``. Models can be loaded when the object is
    created; the structure, mode, output directory, and run parameters can be
    supplied later to :meth:`run`.

    Committee:
        - one main model performs relaxation
        - all models evaluate each relaxed structure
        - MC accept/reject uses committee mean energy per atom

    Output:
        settings.json
        trace.json
        status.json
        initial_unrelaxed.vasp
        initial_relaxed.vasp
        initial_relax_traj.json
        pool/
            rank_XXX_step_YYYY.vasp
            rank_XXX_step_YYYY_relax_traj.json
            pool_summary.json
    """

    MODES = {
        "TM_MC_random",
        "TM_MC_input",
        "Na_MC_input",
        "Relax",
    }

    RUN_OPTIONS = {
        "temperature",
        "max_steps",
        "seed",
        "pool_size",
        "fmax",
        "relax_steps",
        "relax_cell",
        "save_every",
        "patience",
        "energy_tol",
        "tm_original_element",
        "tm_ratios",
        "full_na_structure",
        "max_duplicate_trials",
        "save_relax_traj",
    }

    def __init__(
        self,
        structure=None,
        mode=None,
        out_dir=None,
        temperature=300,
        max_steps=1000,
        seed=0,
        pool_size=50,
        fmax=0.05,
        relax_steps=150,
        relax_cell=True,
        save_every=100,
        patience=10,
        energy_tol=1e-3,
        tm_original_element=None,
        tm_ratios=None,
        na_remove_num=0,
        max_duplicate_trials=100,
        model_path=None,
        model_paths=None,
        main_model_index=0,
        model_type="chgnet",
        device="cpu",
        mace_head=None,
        mace_default_dtype="float64",
        initialize="random",
        full_na_structure=None,
        save_relax_traj=False,
    ):
        self.structure = (
            self._load_structure(structure)
            if structure is not None
            else None
        )
        self.mode = mode
        self.out_dir = Path(out_dir) if out_dir is not None else None
        self.pool_dir = (
            self.out_dir / "pool"
            if self.out_dir is not None
            else None
        )

        self.temperature = temperature
        self.kb = 8.617333262145e-5
        self.max_steps = max_steps
        self.seed = seed
        self.pool_size = pool_size
        self.fmax = fmax
        self.relax_steps = relax_steps
        self.relax_cell = relax_cell
        self.save_every = save_every

        self.patience = patience
        self.energy_tol = energy_tol
        self.last_improve_step = 0

        self.tm_original_element = tm_original_element
        self.tm_ratios = tm_ratios
        self.na_remove_num = na_remove_num
        self.max_duplicate_trials = max_duplicate_trials
        self.save_relax_traj = bool(save_relax_traj)

        self.model_path = model_path
        self.model_paths = model_paths
        self.main_model_index = main_model_index
        self.model_type = str(model_type).lower()
        self.device = device
        self.mace_head = mace_head
        self.mace_default_dtype = mace_default_dtype

        if self.model_type not in {"chgnet", "mace"}:
            raise ValueError("model_type must be either 'chgnet' or 'mace'.")

        self.initialize = initialize

        self.full_na_structure = (
            self._load_structure(full_na_structure)
            if full_na_structure is not None
            else None
        )
        random.seed(seed)
        np.random.seed(seed)

        self.models = self._load_models(
            model_path=self.model_path,
            model_paths=self.model_paths,
        )

        if not (0 <= self.main_model_index < len(self.models)):
            raise ValueError("main_model_index out of range.")

        self.model = self.models[self.main_model_index]
        self.committee_size = len(self.models)

        self.relaxer = self._build_relaxer()

        print(
            f"Loaded {self.committee_size} {self.model_type.upper()} model(s). "
            f"Main model index = {self.main_model_index}."
        )

        self.visited = set()
        self.trace = []
        self.pool = []

        self.current_structure = None
        self.current_eval = None
        self.current_key = None
        self.best_energy = None

        self.tm_indices = None
        self.na_template = None
        self.na_site_indices = None
        self.na_occupation = None

        if self.out_dir is not None:
            self._prepare_output_dirs()
            self._save_settings()

    # ============================================================
    # IO
    # ============================================================

    def _prepare_output_dirs(self):
        """Create the output directories after run configuration is known."""
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.pool_dir = self.out_dir / "pool"
        self.pool_dir.mkdir(parents=True, exist_ok=True)

    def _configure_run(self, structure=None, mode=None, out_dir=None, **options):
        """Apply and validate parameters supplied when starting a run."""
        unknown_options = set(options) - self.RUN_OPTIONS
        if unknown_options:
            names = ", ".join(sorted(unknown_options))
            raise TypeError(f"Unknown run option(s): {names}")

        if structure is not None:
            self.structure = self._load_structure(structure)
        if mode is not None:
            self.mode = mode
        if out_dir is not None:
            self.out_dir = Path(out_dir)

        for name, value in options.items():
            if name == "full_na_structure":
                value = (
                    self._load_structure(value)
                    if value is not None
                    else None
                )
            setattr(self, name, value)

        if self.structure is None:
            raise ValueError("structure must be provided to run().")
        if self.mode is None:
            raise ValueError("mode must be provided to run().")
        if self.out_dir is None:
            raise ValueError("out_dir must be provided to run().")

        # Compatibility with the previous mode + initialize interface.
        if self.mode == "TM":
            self.mode = (
                "TM_MC_random"
                if self.initialize == "random"
                else "TM_MC_input"
            )
        elif self.mode == "Na" and self.initialize == "input":
            self.mode = "Na_MC_input"

        if self.mode not in self.MODES:
            valid = ", ".join(sorted(self.MODES))
            raise ValueError(f"mode must be one of: {valid}.")

        if self.mode == "TM_MC_random":
            if self.tm_original_element is None or self.tm_ratios is None:
                raise ValueError(
                    "TM_MC_random requires tm_original_element and tm_ratios."
                )
            self.initialize = "random"
        elif self.mode == "TM_MC_input":
            self.initialize = "input"
        elif self.mode == "Na_MC_input":
            if self.full_na_structure is None:
                raise ValueError(
                    "Na_MC_input requires full_na_structure."
                )
            self.initialize = "input"

        random.seed(self.seed)
        np.random.seed(self.seed)
        self.visited = set()
        self.trace = []
        self.pool = []
        self.current_structure = None
        self.current_eval = None
        self.current_key = None
        self.best_energy = None
        self.last_improve_step = 0
        self._prepare_output_dirs()
        self._save_settings()

    def _load_structure(self, structure):
        if isinstance(structure, Structure):
            return structure.copy()
        return Structure.from_file(structure)

    def _save_vasp(self, structure, path):
        structure.copy().sort().to(str(path), fmt="poscar")

    def _json_default(self, obj):
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        raise TypeError(
            f"Object of type {obj.__class__.__name__} is not JSON serializable"
        )

    def _save_json(self, data, path):
        with gzip.open(f"{path}.gz", "wt", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=self._json_default)

    def _save_settings(self):
        model_paths = self.model_paths
        if model_paths is None and self.model_path is not None:
            model_paths = [self.model_path]

        self._save_json(
            {
                "mode": self.mode,
                "temperature": self.temperature,
                "max_steps": self.max_steps,
                "seed": self.seed,
                "pool_size": self.pool_size,
                "fmax": self.fmax,
                "relax_steps": self.relax_steps,
                "relax_cell": self.relax_cell,
                "save_every": self.save_every,
                "patience": self.patience,
                "energy_tol": self.energy_tol,
                "tm_original_element": self.tm_original_element,
                "tm_ratios": self.tm_ratios,
                "na_remove_num": self.na_remove_num,
                "max_duplicate_trials": self.max_duplicate_trials,
                "save_relax_traj": self.save_relax_traj,
                "model_path": str(self.model_path) if self.model_path else None,
                "model_paths": (
                    [str(p) for p in model_paths]
                    if model_paths is not None
                    else None
                ),
                "committee_size": self.committee_size,
                "main_model_index": self.main_model_index,
                "model_type": self.model_type,
                "device": self.device,
                "mace_head": self.mace_head,
                "mace_default_dtype": self.mace_default_dtype,
                "accept_energy": "committee_mean_energy_per_atom",
                "trajectory_contains_structure": True,
                "trajectory_contains_committee_info": True,
                
            },
            self.out_dir / "settings.json",
        )

    # ============================================================
    # Model loading
    # ============================================================


    def _build_occ_from_input_structure(self):
        full = self.full_na_structure
        current = self.structure

        full_na_coords = np.array([
            site.frac_coords
            for site in full
            if site.specie.symbol == "Na"
        ])

        current_na_coords = np.array([
            site.frac_coords
            for site in current
            if site.specie.symbol == "Na"
        ])

        if len(current_na_coords) > len(full_na_coords):
            raise ValueError(
                f"Input has {len(current_na_coords)} Na atoms, "
                f"but full structure has only {len(full_na_coords)} Na sites."
            )

        # 周期性边界下的实际距离
        distances = full.lattice.get_all_distances(
            full_na_coords,
            current_na_coords,
        )

        full_indices, _ = linear_sum_assignment(distances)
        occupied = set(full_indices)

        occ = [
            "Na" if i in occupied else "Vac"
            for i in range(len(full_na_coords))
        ]

        assert occ.count("Na") == len(current_na_coords)
        return occ
    def _load_models(self, model_path=None, model_paths=None):
        if model_paths is not None and model_path is not None:
            raise ValueError("Use either model_path or model_paths, not both.")

        if model_paths is None:
            if model_path is None:
                if self.model_type == "mace":
                    raise ValueError(
                        "MACE requires model_path or model_paths. "
                        "Pass one or more MACE model files."
                    )
                model_paths = [None]
            else:
                model_paths = [model_path]

        if isinstance(model_paths, (str, Path)):
            model_paths = [model_paths]

        if len(model_paths) == 0:
            raise ValueError("No model paths provided.")

        if self.model_type == "mace":
            return self._load_mace_models(model_paths)

        try:
            from chgnet.model import CHGNet
        except ImportError as exc:
            raise ImportError(
                "CHGNet is required for model_type='chgnet'."
            ) from exc

        models = []

        for i, path in enumerate(model_paths):
            if isinstance(path, CHGNet):
                print(f"Use pre-loaded CHGNet as model {i}")
                models.append(path)
            elif path is None:
                print(f"Load default CHGNet as model {i}")
                models.append(CHGNet.load())
            else:
                print(f"Load CHGNet model {i} from {path}")
                models.append(CHGNet.from_file(path))

        if len(models) == 0:
            raise ValueError("No model loaded.")

        return models

    def _load_mace_models(self, model_paths):
        """Load each MACE file as an independent committee member."""
        try:
            from mace.calculators import MACECalculator
        except ImportError as exc:
            raise ImportError(
                "MACE is required for model_type='mace'. Install mace-torch "
                "in the active Python environment."
            ) from exc

        models = []
        for i, path in enumerate(model_paths):
            if path is None:
                raise ValueError("A MACE model path cannot be None.")

            kwargs = {
                "model_paths": str(path),
                "device": self.device,
                "default_dtype": self.mace_default_dtype,
            }
            if self.mace_head is not None:
                kwargs["head"] = self.mace_head

            print(f"Load MACE model {i} from {path}")
            models.append(MACECalculator(**kwargs))

        return models

    def _build_relaxer(self):
        if self.model_type == "mace":
            return None

        try:
            from chgnet.model.dynamics import StructOptimizer
        except ImportError as exc:
            raise ImportError(
                "CHGNet is required for model_type='chgnet'."
            ) from exc

        return StructOptimizer(
            self.model,
            optimizer_class="LBFGSLineSearch",
        )

    # ============================================================
    # Initialization
    # ============================================================

    def prepare(self):
        if self.mode.startswith("TM_MC_"):
            self._prepare_tm()
        else:
            self._prepare_na()

    def _prepare_tm(self):

        s = self.structure.copy()

        if self.initialize == "random":

            if (
                self.tm_original_element is None
                or self.tm_ratios is None
            ):
                raise ValueError(
                    "TM random initialization needs "
                    "tm_original_element and tm_ratios."
                )

            self.tm_indices = [
                i
                for i, site in enumerate(s)
                if site.specie.symbol == self.tm_original_element
            ]

            if len(self.tm_indices) == 0:
                raise ValueError(
                    f"No {self.tm_original_element} sites found."
                )

            species = self._species_from_ratios(
                ratios=self.tm_ratios,
                total=len(self.tm_indices),
            )

            random.shuffle(species)

            for idx, elem in zip(self.tm_indices, species):
                s[idx] = elem

        elif self.initialize == "input":
            self.tm_indices = [
                i
                for i, site in enumerate(s)
                if site.specie.symbol not in {"Na", "O"}
            ]

            if len(self.tm_indices) == 0:
                raise ValueError(
                    "No TM sites found in the input structure."
                )

        else:
            raise ValueError(
                "initialize must be 'random' or 'input'"
            )

        self._save_vasp(
            s,
            self.out_dir / "initial_unrelaxed.vasp"
        )

        relaxed, eval_data, relax_traj = self._relax_and_evaluate(
            s,
            traj_dir=self.out_dir,
        )

        self.current_structure = relaxed
        self.current_eval = eval_data
        self.current_key = self._tm_key(relaxed)
        self.best_energy = eval_data["energy_mean_per_atom"]
        self.last_improve_step = 0

        self.visited.add(self.current_key)

        self._update_pool(
            structure=relaxed,
            eval_data=eval_data,
            key=self.current_key,
            step=0,
            relax_traj=relax_traj,
        )

        self._save_vasp(
            relaxed,
            self.out_dir / "initial_relaxed.vasp"
        )

    def _prepare_na(self):
        full = self.full_na_structure.copy()
        self.na_template = full.copy()
        self.na_site_indices = [
            i
            for i, site in enumerate(full)
            if site.specie.symbol == "Na"
        ]
        occ = self._build_occ_from_input_structure()

        if len(occ) != len(self.na_site_indices):
            raise RuntimeError(
                "Occupation length does not match Na template."
            )

        self.na_occupation = occ

        s = self._structure_from_na_occ(occ)

        self._save_vasp(s, self.out_dir / "initial_unrelaxed.vasp")

        relaxed, eval_data, relax_traj = self._relax_and_evaluate(
            s,
            traj_dir=self.out_dir,
        )

        self.current_structure = relaxed
        self.current_eval = eval_data
        self.current_key = self._na_key(occ)
        self.best_energy = eval_data["energy_mean_per_atom"]
        self.last_improve_step = 0

        self.visited.add(self.current_key)

        self._update_pool(
            structure=relaxed,
            eval_data=eval_data,
            key=self.current_key,
            step=0,
            relax_traj=relax_traj,
        )

        self._save_vasp(relaxed, self.out_dir / "initial_relaxed.vasp")

    def _na_mc_has_no_valid_swap(self):
        """Return whether zero or full Na occupancy prevents a Na/Vac swap."""
        input_na_count = sum(
            site.specie.symbol == "Na" for site in self.structure
        )
        full_na_count = sum(
            site.specie.symbol == "Na" for site in self.full_na_structure
        )
        return input_na_count == 0 or input_na_count == full_na_count

    def _species_from_ratios(self, ratios, total):
        elems = list(ratios.keys())
        vals = np.array(list(ratios.values()), dtype=float)
        vals /= vals.sum()

        raw = vals * total
        counts = np.floor(raw).astype(int)
        remain = total - counts.sum()

        for i in np.argsort(-(raw - counts))[:remain]:
            counts[i] += 1

        species = []

        for elem, count in zip(elems, counts):
            species.extend([elem] * int(count))

        return species

    # ============================================================
    # Keys and builders
    # ============================================================

    def _tm_key(self, structure):
        return tuple(structure[i].specie.symbol for i in self.tm_indices)

    def _na_key(self, occ):
        return tuple(occ)

    def _structure_from_na_occ(self, occ):
        s = self.na_template.copy()

        remove_indices = [
            site_idx
            for o, site_idx in zip(occ, self.na_site_indices)
            if o == "Vac"
        ]

        for idx in sorted(remove_indices, reverse=True):
            s.remove_sites([idx])

        return s

    # ============================================================
    # CHGNet relax / evaluate / trajectory
    # ============================================================

    def _relax_with_main_model(self, structure):
        if self.model_type == "mace":
            return self._relax_with_mace(structure)

        return self.relaxer.relax(
            structure,
            fmax=self.fmax,
            steps=self.relax_steps,
            relax_cell=self.relax_cell,
            verbose=False,
        )

    def _relax_with_mace(self, structure):
        """Relax with the selected MACE calculator and retain all frames."""
        atoms = AseAtomsAdaptor.get_atoms(structure)
        atoms.calc = self.model
        trajectory = [atoms.copy()]

        target = FrechetCellFilter(atoms) if self.relax_cell else atoms
        optimizer = LBFGS(target, logfile=None)

        def capture_frame():
            trajectory.append(atoms.copy())

        optimizer.attach(capture_frame, interval=1)
        optimizer.run(fmax=self.fmax, steps=self.relax_steps)

        final_structure = AseAtomsAdaptor.get_structure(atoms)
        return {
            "final_structure": final_structure,
            "trajectory": trajectory,
        }

    def _predict_energy_force(self, model, structure):
        if self.model_type == "mace":
            atoms = AseAtomsAdaptor.get_atoms(structure)
            atoms.calc = model
            energy_per_atom = atoms.get_potential_energy() / len(atoms)
            forces = atoms.get_forces()
            return float(energy_per_atom), np.asarray(forces, dtype=float)

        pred = model.predict_structure(structure)

        energy_per_atom = pred.get("e", None)
        forces = pred.get("f", None)

        if energy_per_atom is None:
            raise RuntimeError("CHGNet prediction does not contain energy key 'e'.")

        if forces is None:
            raise RuntimeError("CHGNet prediction does not contain force key 'f'.")

        return float(energy_per_atom), np.array(forces, dtype=float)

    def _evaluate_committee(self, structure):
        n_atoms = len(structure)

        energies_per_atom = []
        forces = []

        for model in self.models:
            e_per_atom, f = self._predict_energy_force(model, structure)
            energies_per_atom.append(e_per_atom)
            forces.append(f)

        energies_per_atom = np.array(energies_per_atom, dtype=float)
        energies_total = energies_per_atom * n_atoms
        forces = np.array(forces, dtype=float)  # K, N, 3

        energy_mean_per_atom = float(np.mean(energies_per_atom))
        energy_std_per_atom = float(np.std(energies_per_atom))
        energy_var_per_atom = float(energy_std_per_atom**2)

        force_mean = np.mean(forces, axis=0)
        force_diff = forces - force_mean[None, :, :]

        force_atom_deviation = np.sqrt(
            np.mean(np.sum(force_diff**2, axis=2), axis=0)
        )

        force_uncertainty_per_atom = float(np.mean(force_atom_deviation))
        force_uncertainty_max = float(np.max(force_atom_deviation))

        return {
            "n_atoms": int(n_atoms),
            "energy_mean_per_atom": energy_mean_per_atom,
            "energy_std_per_atom": energy_std_per_atom,
            "energy_var_per_atom": energy_var_per_atom,
            "energy_per_model_per_atom": [
                float(x) for x in energies_per_atom.tolist()
            ],
            "energy_per_model_total": [
                float(x) for x in energies_total.tolist()
            ],
            "force_uncertainty_per_atom": force_uncertainty_per_atom,
            "force_uncertainty_var_per_atom": float(force_uncertainty_per_atom**2),
            "force_uncertainty_max": force_uncertainty_max,
            "force_uncertainty_var_max": float(force_uncertainty_max**2),
            "force_atom_deviation": [
                float(x) for x in force_atom_deviation.tolist()
            ],
        }

    def _structure_to_json_dict(self, structure):
        return structure.as_dict()

    def _make_traj_frame_json(self, step, structure, eval_data):
        return {
            "step": step,
            "structure": self._structure_to_json_dict(structure),
            "n_atoms": int(eval_data["n_atoms"]),
            "energy_mean_per_atom": float(eval_data["energy_mean_per_atom"]),
            "energy_std_per_atom": float(eval_data["energy_std_per_atom"]),
            "energy_var_per_atom": float(eval_data["energy_var_per_atom"]),
            "energy_per_model_per_atom": [
                float(x) for x in eval_data["energy_per_model_per_atom"]
            ],
            "energy_per_model_total": [
                float(x) for x in eval_data["energy_per_model_total"]
            ],
            "force_uncertainty_per_atom": float(
                eval_data["force_uncertainty_per_atom"]
            ),
            "force_uncertainty_var_per_atom": float(
                eval_data["force_uncertainty_var_per_atom"]
            ),
            "force_uncertainty_max": float(eval_data["force_uncertainty_max"]),
            "force_uncertainty_var_max": float(
                eval_data["force_uncertainty_var_max"]
            ),
            "force_atom_deviation": [
                float(x) for x in eval_data["force_atom_deviation"]
            ],
        }

    def _get_traj_structures(self, trajectory):
        """
        Extract pymatgen structures from CHGNet TrajectoryObserver.

        For many CHGNet versions:
            trajectory.atoms          = one ASE Atoms object
            trajectory.atom_positions = list of cartesian positions, one per step
            trajectory.cells          = list of cells, one per step

        We reconstruct every relaxation frame using:
            species from trajectory.atoms
            positions from trajectory.atom_positions
            cells from trajectory.cells
        """

        if trajectory is None:
            return []

        structures = []

        # Case 1: normal list/tuple of full structures or ASE Atoms
        if isinstance(trajectory, (list, tuple)):
            for frame in trajectory:
                if isinstance(frame, Structure):
                    structures.append(frame.copy())
                else:
                    structures.append(AseAtomsAdaptor.get_structure(frame))
            return structures

        # Case 2: CHGNet TrajectoryObserver
        if (
            hasattr(trajectory, "atoms")
            and hasattr(trajectory, "atom_positions")
            and hasattr(trajectory, "cells")
        ):
            atoms = trajectory.atoms

            # trajectory.atoms is usually ONE ASE Atoms object, not a list of frames.
            species = atoms.get_chemical_symbols()

            positions_list = trajectory.atom_positions
            cells_list = trajectory.cells

            for positions, cell in zip(positions_list, cells_list):
                struct = Structure(
                    lattice=cell,
                    species=species,
                    coords=positions,
                    coords_are_cartesian=True,
                )
                structures.append(struct)

            return structures

        # Case 3: fallback if trajectory.atoms is really a list of ASE Atoms
        if hasattr(trajectory, "atoms"):
            atoms_obj = trajectory.atoms

            if isinstance(atoms_obj, (list, tuple)):
                for frame in atoms_obj:
                    if isinstance(frame, Structure):
                        structures.append(frame.copy())
                    else:
                        structures.append(AseAtomsAdaptor.get_structure(frame))
                return structures

            # If it is a single ASE Atoms object, convert only one frame
            try:
                return [AseAtomsAdaptor.get_structure(atoms_obj)]
            except Exception:
                return []

        return []

    @staticmethod
    def _structures_match(first, second, atol=1e-8):
        """Return whether two structures represent the same periodic geometry."""
        if len(first) != len(second):
            return False

        first_species = [site.specie.symbol for site in first]
        second_species = [site.specie.symbol for site in second]
        if first_species != second_species:
            return False

        if not np.allclose(first.lattice.matrix, second.lattice.matrix, atol=atol):
            return False

        frac_diff = np.asarray(first.frac_coords) - np.asarray(second.frac_coords)
        frac_diff -= np.rint(frac_diff)
        return bool(np.allclose(frac_diff, 0.0, atol=atol))

    def _relax_and_evaluate(self, structure, traj_dir=None):
        relax_result = self._relax_with_main_model(structure)

        relaxed = relax_result["final_structure"]
        trajectory = relax_result.get("trajectory", None)

        traj_json = []
        traj_structures = self._get_traj_structures(trajectory) if self.save_relax_traj else []

        # Some CHGNet versions start their trajectory after the first optimizer
        # update. Always expose the unrelaxed input as step 0, without duplicating
        # it when the backend already recorded that frame (as MACE normally does).
        if self.save_relax_traj and (not traj_structures or not self._structures_match(
            structure,
            traj_structures[0],
        )):
            traj_structures.insert(0, structure.copy())

        for istep, pmg_struct in enumerate(traj_structures):
            eval_data = self._evaluate_committee(pmg_struct)
            traj_json.append(
                self._make_traj_frame_json(
                    step=int(istep),
                    structure=pmg_struct,
                    eval_data=eval_data,
                )
            )

        final_eval = self._evaluate_committee(relaxed)

        # 防止 trajectory 没有最后一步，或者最后一步和 final_structure 不完全一致
        if self.save_relax_traj:
            traj_json.append(
                self._make_traj_frame_json(
                    step="final",
                    structure=relaxed,
                    eval_data=final_eval,
                )
            )

        if self.save_relax_traj and traj_dir is not None:
            traj_dir.mkdir(parents=True, exist_ok=True)
            self._save_json(traj_json, traj_dir / "initial_relax_traj.json")

        return relaxed, final_eval, traj_json

    # ============================================================
    # Trial moves
    # ============================================================

    def _trial(self):
        if self.mode.startswith("TM_MC_"):
            return self._trial_tm()
        return self._trial_na()

    def _trial_tm(self):
        for _ in range(self.max_duplicate_trials):
            s = self.current_structure.copy()

            i, j = self._choose_two_different_sites(
                structure=s,
                indices=self.tm_indices,
            )

            ei = s[i].specie.symbol
            ej = s[j].specie.symbol

            s[i] = ej
            s[j] = ei

            key = self._tm_key(s)

            if key not in self.visited:
                return s, key, None

        return None, None, None

    def _trial_na(self):
        for _ in range(self.max_duplicate_trials):
            occ = list(self.na_occupation)

            na_pos = [i for i, x in enumerate(occ) if x == "Na"]
            vac_pos = [i for i, x in enumerate(occ) if x == "Vac"]

            i = random.choice(na_pos)
            j = random.choice(vac_pos)

            occ[i], occ[j] = occ[j], occ[i]

            key = self._na_key(occ)

            if key not in self.visited:
                s = self._structure_from_na_occ(occ)
                return s, key, occ

        return None, None, None

    def _choose_two_different_sites(self, structure, indices):
        for _ in range(1000):
            i, j = random.sample(indices, 2)

            if structure[i].specie.symbol != structure[j].specie.symbol:
                return i, j

        raise RuntimeError("Cannot find two different species to swap.")

    # ============================================================
    # MC
    # ============================================================

    def _accept(self, trial_eval):
        trial_energy = trial_eval["energy_mean_per_atom"]
        current_energy = self.current_eval["energy_mean_per_atom"]
        dE = trial_energy - current_energy

        if dE <= 0:
            return True, 1.0, dE

        prob = math.exp(-dE / (self.kb * self.temperature))
        return random.random() < prob, prob, dE

    def _should_stop(self, step):
        if self.patience is None:
            return False

        return step - self.last_improve_step >= self.patience

    # ============================================================
    # Save pool / checkpoint
    # ============================================================

    def _summary_eval(self, eval_data):
        return {
            "n_atoms": int(eval_data["n_atoms"]),
            "energy_mean_per_atom": float(eval_data["energy_mean_per_atom"]),
            "energy_std_per_atom": float(eval_data["energy_std_per_atom"]),
            "energy_var_per_atom": float(eval_data["energy_var_per_atom"]),
            "force_uncertainty_per_atom": float(
                eval_data["force_uncertainty_per_atom"]
            ),
            "force_uncertainty_var_per_atom": float(
                eval_data["force_uncertainty_var_per_atom"]
            ),
            "force_uncertainty_max": float(eval_data["force_uncertainty_max"]),
            "force_uncertainty_var_max": float(
                eval_data["force_uncertainty_var_max"]
            ),
            "energy_per_model_per_atom": [
                float(x) for x in eval_data["energy_per_model_per_atom"]
            ],
        }

    def _update_pool(self, structure, eval_data, key, step, relax_traj=None):
        self.pool.append(
            {
                "step": int(step),
                "energy": float(eval_data["energy_mean_per_atom"]),
                "eval": dict(eval_data),
                "key": key,
                "structure": structure.copy(),
                "relax_traj": relax_traj if relax_traj is not None else [],
            }
        )

        unique = {}

        for item in self.pool:
            k = item["key"]

            if k not in unique or item["energy"] < unique[k]["energy"]:
                unique[k] = item

        self.pool = sorted(unique.values(), key=lambda x: x["energy"])
        self.pool = self.pool[: self.pool_size]

    def _save_pool(self):
        if self.pool_dir.exists():
            shutil.rmtree(self.pool_dir)

        self.pool_dir.mkdir(parents=True, exist_ok=True)

        summary = []

        for rank, item in enumerate(self.pool):
            prefix = f"rank_{rank:03d}_step_{item['step']:04d}"

            structure_file = self.pool_dir / f"{prefix}.vasp"
            traj_file = self.pool_dir / f"{prefix}_relax_traj.json"

            self._save_vasp(item["structure"], structure_file)
            if self.save_relax_traj:
                self._save_json(item["relax_traj"], traj_file)

            eval_data = item["eval"]

            summary.append(
                {
                    "rank": int(rank),
                    "step": int(item["step"]),
                    "energy_mean_per_atom": float(
                        eval_data["energy_mean_per_atom"]
                    ),
                    "energy_std_per_atom": float(
                        eval_data["energy_std_per_atom"]
                    ),
                    "energy_var_per_atom": float(
                        eval_data["energy_var_per_atom"]
                    ),
                    "force_uncertainty_per_atom": float(
                        eval_data["force_uncertainty_per_atom"]
                    ),
                    "force_uncertainty_var_per_atom": float(
                        eval_data["force_uncertainty_var_per_atom"]
                    ),
                    "force_uncertainty_max": float(
                        eval_data["force_uncertainty_max"]
                    ),
                    "force_uncertainty_var_max": float(
                        eval_data["force_uncertainty_var_max"]
                    ),
                    "structure_file": structure_file.name,
                    "relax_traj_file": traj_file.name if self.save_relax_traj else None,
                    "relax_traj_contains_structure": self.save_relax_traj,
                    "relax_traj_contains_committee_info": self.save_relax_traj,
                    "relax_traj_n_frames": int(len(item["relax_traj"])),
                }
            )

        self._save_json(summary, self.pool_dir / "pool_summary.json")

    def _save_checkpoint(self):
        self._save_json(self.trace, self.out_dir / "trace.json")

        self._save_json(
            {
                "mode": self.mode,
                "current": (
                    self._summary_eval(self.current_eval)
                    if self.current_eval is not None
                    else None
                ),
                "best_energy_mean_per_atom": self.best_energy,
                "visited_count": len(self.visited),
                "pool_size": len(self.pool),
                "last_improve_step": self.last_improve_step,
            },
            self.out_dir / "status.json",
        )

        self._save_pool()

    # ============================================================
    # Run
    # ============================================================

    def _run_relax(self):
        """Relax one structure with the model committee without running MC.

        The main model performs the relaxation and every model evaluates each
        trajectory frame and the final structure. Output file names and data
        fields match those produced for the initial structure by ``run()``.

        Returns:
            A tuple of ``(relaxed_structure, final_evaluation, trajectory)``.
        """
        input_structure = self.structure.copy()

        # Keep repeated calls independent from an earlier MC or relaxation run.
        self.visited = set()
        self.trace = []
        self.pool = []

        self._save_vasp(
            input_structure,
            self.out_dir / "initial_unrelaxed.vasp",
        )

        relaxed, eval_data, relax_traj = self._relax_and_evaluate(
            input_structure,
            traj_dir=self.out_dir,
        )

        self.current_structure = relaxed
        self.current_eval = eval_data
        self.current_key = ("relax_only",)
        self.best_energy = eval_data["energy_mean_per_atom"]
        self.last_improve_step = 0
        self.visited.add(self.current_key)

        self._update_pool(
            structure=relaxed,
            eval_data=eval_data,
            key=self.current_key,
            step=0,
            relax_traj=relax_traj,
        )
        self._save_vasp(
            relaxed,
            self.out_dir / "initial_relaxed.vasp",
        )

        self.trace = [
            {
                "step": 0,
                "status": "relax_only",
                **self._summary_eval(eval_data),
            }
        ]
        self._save_checkpoint()

        print(
            "Relaxation done. "
            f"Energy = {self.best_energy:.6f} eV/atom"
        )
        print(f"Results saved to {self.out_dir}")

        return relaxed, eval_data, relax_traj

    def run(self, structure=None, mode=None, out_dir=None, **options):
        """Configure and execute one MC or relaxation run.

        Args:
            structure: Structure file path or pymatgen ``Structure``.
            mode: One of ``TM_MC_random``, ``TM_MC_input``,
                ``Na_MC_input``, or ``Relax``.
            out_dir: Directory in which to save the run outputs.
            **options: Optional run parameters such as ``max_steps``,
                ``tm_ratios``, ``full_na_structure``, and ``patience``.

        Returns:
            For ``Relax`` and ``Na_MC_input`` without a valid Na/Vac swap, the
            relaxed structure, final committee evaluation, and relaxation
            trajectory. Other MC runs return ``None``.
        """
        self._configure_run(
            structure=structure,
            mode=mode,
            out_dir=out_dir,
            **options,
        )

        if self.mode == "Relax":
            return self._run_relax()

        if self.mode == "Na_MC_input" and self._na_mc_has_no_valid_swap():
            print(
                "Input structure has zero or full Na occupancy; "
                "skip Na/Vac MC and relax directly."
            )
            return self._run_relax()

        self.prepare()

        for step in range(1, self.max_steps + 1):
            trial_s, trial_key, extra = self._trial()

            if trial_s is None:
                self.trace.append(
                    {
                        "step": int(step),
                        "status": "duplicate_skipped",
                        "current_energy_mean_per_atom": float(
                            self.current_eval["energy_mean_per_atom"]
                        ),
                        "current_energy_std_per_atom": float(
                            self.current_eval["energy_std_per_atom"]
                        ),
                        "current_force_uncertainty_per_atom": float(
                            self.current_eval["force_uncertainty_per_atom"]
                        ),
                        "current_force_uncertainty_max": float(
                            self.current_eval["force_uncertainty_max"]
                        ),
                        "best_energy_mean_per_atom": float(self.best_energy),
                        "visited_count": int(len(self.visited)),
                    }
                )
                continue

            self.visited.add(trial_key)

            trial_relaxed, trial_eval, trial_relax_traj = self._relax_and_evaluate(
                trial_s
            )

            accepted, prob, dE = self._accept(trial_eval)
 
            if accepted:
                self.current_structure = trial_relaxed
                self.current_eval = trial_eval
                self.current_key = trial_key

                if self.mode == "Na_MC_input":
                    self.na_occupation = extra

            trial_energy = trial_eval["energy_mean_per_atom"]

            if trial_energy < self.best_energy - self.energy_tol:
                self.best_energy = trial_energy
                self.last_improve_step = step

            self._update_pool(
                structure=trial_relaxed,
                eval_data=trial_eval,
                key=trial_key,
                step=step,
                relax_traj=trial_relax_traj,
            )

            self.trace.append(
                {
                    "step": int(step),
                    "status": "normal",
                    "accepted": bool(accepted),
                    "accept_prob": float(prob),
                    "delta_E_mean_per_atom": float(dE),
                    "visited_count": int(len(self.visited)),
                    "trial_energy_mean_per_atom": float(
                        trial_eval["energy_mean_per_atom"]
                    ),
                    "trial_energy_std_per_atom": float(
                        trial_eval["energy_std_per_atom"]
                    ),
                    "trial_energy_var_per_atom": float(
                        trial_eval["energy_var_per_atom"]
                    ),
                    "trial_force_uncertainty_per_atom": float(
                        trial_eval["force_uncertainty_per_atom"]
                    ),
                    "trial_force_uncertainty_var_per_atom": float(
                        trial_eval["force_uncertainty_var_per_atom"]
                    ),
                    "trial_force_uncertainty_max": float(
                        trial_eval["force_uncertainty_max"]
                    ),
                    "trial_force_uncertainty_var_max": float(
                        trial_eval["force_uncertainty_var_max"]
                    ),
                    "trial_energy_per_model_per_atom": [
                        float(x) for x in trial_eval["energy_per_model_per_atom"]
                    ],
                    "current_energy_mean_per_atom": float(
                        self.current_eval["energy_mean_per_atom"]
                    ),
                    "current_energy_std_per_atom": float(
                        self.current_eval["energy_std_per_atom"]
                    ),
                    "current_energy_var_per_atom": float(
                        self.current_eval["energy_var_per_atom"]
                    ),
                    "current_force_uncertainty_per_atom": float(
                        self.current_eval["force_uncertainty_per_atom"]
                    ),
                    "current_force_uncertainty_var_per_atom": float(
                        self.current_eval["force_uncertainty_var_per_atom"]
                    ),
                    "current_force_uncertainty_max": float(
                        self.current_eval["force_uncertainty_max"]
                    ),
                    "current_force_uncertainty_var_max": float(
                        self.current_eval["force_uncertainty_var_max"]
                    ),
                    "best_energy_mean_per_atom": float(self.best_energy),
                }
            )

            if step % self.save_every == 0:
                self._save_checkpoint()

                print(
                    f"[{step}] "
                    f"current={self.current_eval['energy_mean_per_atom']:.6f}, "
                    f"current_Estd={self.current_eval['energy_std_per_atom']:.6f}, "
                    f"current_Func={self.current_eval['force_uncertainty_per_atom']:.6f}, "
                    f"best={self.best_energy:.6f}, "
                    f"visited={len(self.visited)}"
                )

            if self._should_stop(step):
                self.trace.append(
                    {
                        "step": int(step),
                        "status": "early_stop",
                        "best_energy_mean_per_atom": float(self.best_energy),
                        "last_improve_step": int(self.last_improve_step),
                        "patience": self.patience,
                        "energy_tol": float(self.energy_tol),
                    }
                )
                break

        self._save_checkpoint()

        print(f"Done. Best energy = {self.best_energy:.6f} eV/atom")
        print(f"Results saved to {self.out_dir}")
