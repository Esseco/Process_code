"""Calculate the theoretical specific capacity of an electrode material."""

from __future__ import annotations
import re
from pymatgen.core import Composition

FARADAY_CONSTANT = 96485.33212  # C mol^-1
_COMMON_ION_CHARGES = {
    "H": 1,
    "Li": 1,
    "Na": 1,
    "K": 1,
    "Mg": 2,
    "Ca": 2,
    "Zn": 2,
    "Al": 3,
}
_ION_PATTERN = re.compile(r"^([A-Z][a-z]?)(?:(\d+)([+-])|([+-]))?$")

def _parse_migrating_ion(ion: str) -> tuple[str, int]:
    """Return the element symbol and absolute charge of an ion."""
    compact_ion = ion.strip().replace(" ", "")
    match = _ION_PATTERN.fullmatch(compact_ion)
    if match is None:
        raise ValueError("迁移离子格式无效，请使用 'Li'、'Li+' 或 'Mg2+' 这样的格式。")

    symbol, charge_text, sign, single_sign = match.groups()
    if sign is not None:
        charge = int(charge_text)
    elif single_sign is not None:
        charge = 1
    else:
        try:
            charge = _COMMON_ION_CHARGES[symbol]
        except KeyError as exc:
            raise ValueError(
                f"无法推断 {symbol} 的电荷数，请显式输入，例如 'Fe2+'。"
            ) from exc

    return symbol, charge


def theoretical_specific_capacity(formula: str,migrating_ion=None) -> float:
    """Calculate theoretical specific capacity in mAh/g.

    The number of transferable ions is taken from the stoichiometric coefficient
    of ``migrating_ion`` in ``formula``. The molar mass includes the complete
    input formula.

    Args:
        formula: Electrode formula, for example ``"LiFePO4"``.

    Returns:
        Theoretical specific capacity in mAh/g.
    """
    try:
        if not migrating_ion:
            migrating_ion = 'Li' if 'Li' in formula else 'Na'
        composition = Composition(formula)
        
    except Exception as exc:
        raise ValueError(f"无法解析化学式：{formula!r}") from exc

    element, charge = _parse_migrating_ion(migrating_ion)
    ion_count = float(composition.get(element, 0.0))
    if ion_count <= 0:
        return 0

    electrons = ion_count * charge
    return electrons * FARADAY_CONSTANT / (3.6 * composition.weight)

