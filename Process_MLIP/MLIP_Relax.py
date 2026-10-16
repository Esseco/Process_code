from ase.optimize import BFGS, FIRE, LBFGS
from ase.io import write
import numpy as np
from numbers import Real


class MLIPRelaxer:
    """Relax ASE Atoms with an explicitly supplied calculator.

    Modifies the supplied Atoms and retains its constraints. Energies are eV,
    fmax is eV/Å. Cell relaxation also tests filter stress degrees of freedom.
    maxstep=None uses the ASE optimizer default; positive values limit optimizer
    steps (Å for atom variables). FrechetCellFilter scales cell variables by
    exp_cell_factor, defaulting to atom count; no direct strain bound is imposed.
    """

    def __init__(
        self,
        atoms,
        calculator,
        fmax=0.05,
        steps=200,
        optimizer="BFGS",
        relax_cell=False,
        *,
        maxstep=None,
        exp_cell_factor=None,
    ):

        if len(atoms) == 0:
            raise ValueError("atoms must not be empty")
        if not np.isfinite(fmax) or fmax <= 0:
            raise ValueError("fmax must be finite and positive")
        if not isinstance(steps, int) or isinstance(steps, bool) or steps < 0:
            raise ValueError("steps must be a nonnegative integer")
        for key, value in (("maxstep", maxstep), ("exp_cell_factor", exp_cell_factor)):
            if value is not None and (isinstance(value, bool) or not isinstance(value, Real)
                                      or not np.isfinite(value) or value <= 0):
                raise ValueError(f"{key} must be None or finite and positive")
        self.atoms = atoms
        self.calculator = calculator
        self.fmax = fmax
        self.steps = steps
        self.optimizer = optimizer
        self.relax_cell = relax_cell
        self.maxstep = maxstep
        self.exp_cell_factor = exp_cell_factor

        self.atoms.calc = self.calculator

    def _get_optimizer(self):

        optimizer_map = {
            "BFGS": BFGS,
            "FIRE": FIRE,
            "LBFGS": LBFGS,
        }

        if self.optimizer not in optimizer_map:
            raise ValueError(f"Optimizer {self.optimizer} not found in ASE")

        return optimizer_map[self.optimizer]

    def relax(
        self,
        traj_file="relax.traj",
        log_file="relax.log",
        final_structure=None,
    ):

        optimizer_class = self._get_optimizer()

        if self.relax_cell:
            try:
                from ase.filters import FrechetCellFilter
            except ImportError as exc:
                raise ImportError("Cell relaxation requires ASE >= 3.23 with FrechetCellFilter") from exc
            system = FrechetCellFilter(self.atoms, exp_cell_factor=self.exp_cell_factor)
        else:
            system = self.atoms

        options = {} if self.maxstep is None else dict(maxstep=float(self.maxstep))
        with optimizer_class(system, trajectory=traj_file, logfile=log_file, **options) as opt:
            converged = bool(opt.run(fmax=self.fmax, steps=self.steps))
            steps_used = int(opt.get_number_of_steps())

        energy = self.atoms.get_potential_energy()
        natoms = len(self.atoms)
        energy_per_atom = energy / natoms
        forces = self.atoms.get_forces()
        if not np.isfinite(energy) or not np.all(np.isfinite(forces)):
            raise RuntimeError("Calculator returned non-finite energy or forces")

        if final_structure is not None:
            write(final_structure, self.atoms)

        results = {
            "optimizer_converged": converged,
            "relax_steps_used": steps_used,
            "force_max_ev_per_angstrom": float(np.linalg.norm(forces, axis=1).max()),
            "energy_unit": "eV",
            "cell_filter": "FrechetCellFilter" if self.relax_cell else None,
            "maxstep": self.maxstep,
            "exp_cell_factor": (float(system.exp_cell_factor) if self.relax_cell else None),
            "final_struct": self.atoms,        
            "energy": energy,                
            "natoms": natoms,                
            "energy_per_atom": energy_per_atom, 
            "trajectory_file": traj_file,
            "log_file": log_file,
        }

        return results
