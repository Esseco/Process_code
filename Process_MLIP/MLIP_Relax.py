from ase.optimize import BFGS, FIRE, LBFGS
from ase.filters import ExpCellFilter
from ase.io import write
import numpy as np


class MLIPRelaxer:
    """Relax ASE Atoms with an explicitly supplied calculator.

    Modifies the supplied Atoms and retains its constraints. Energies are eV,
    fmax is eV/Å. Cell relaxation also tests filter stress degrees of freedom.
    """

    def __init__(
        self,
        atoms,
        calculator,
        fmax=0.05,
        steps=200,
        optimizer="BFGS",
        relax_cell=False,
    ):

        if len(atoms) == 0:
            raise ValueError("atoms must not be empty")
        if not np.isfinite(fmax) or fmax <= 0:
            raise ValueError("fmax must be finite and positive")
        if not isinstance(steps, int) or isinstance(steps, bool) or steps < 0:
            raise ValueError("steps must be a nonnegative integer")
        self.atoms = atoms
        self.calculator = calculator
        self.fmax = fmax
        self.steps = steps
        self.optimizer = optimizer
        self.relax_cell = relax_cell

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
            system = ExpCellFilter(self.atoms)
        else:
            system = self.atoms

        opt = optimizer_class(system, trajectory=traj_file, logfile=log_file)
        converged = bool(opt.run(fmax=self.fmax, steps=self.steps))

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
            "relax_steps_used": int(opt.get_number_of_steps()),
            "force_max_ev_per_angstrom": float(np.linalg.norm(forces, axis=1).max()),
            "energy_unit": "eV",
            "final_struct": self.atoms,        
            "energy": energy,                
            "natoms": natoms,                
            "energy_per_atom": energy_per_atom, 
            "trajectory_file": traj_file,
            "log_file": log_file,
        }

        return results
