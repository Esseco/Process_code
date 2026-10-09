"""StructureMatcher deduplication shared by structure, VASP and surface tools.

Default matcher semantics and legacy return conventions are preserved.
Dictionary comparison spans all keys; DataFrames keep low-energy rows first.
"""
import pandas as pd
from pymatgen.analysis.structure_matcher import StructureMatcher

def deduplicate(struc_lst: list) -> list:
    """
    deduplicate 的 Docstring

    :param struc_lst: structs list
    :type struc_lst: list
    :return: deduplicated list
    :rtype: list
    """
    matcher = StructureMatcher()
    deduplicated_struc_lst = []

    for struc in struc_lst:
        flag = True
        for deduplicated_struc in deduplicated_struc_lst:
            if matcher.fit(struc, deduplicated_struc):
                flag = False
                break
        if flag:
            deduplicated_struc_lst.append(struc.copy())

    return deduplicated_struc_lst


def deduplicate_dict(struc_dict: dict) -> dict:
    matcher = StructureMatcher()
    deduplicated_dict = {}
    seen_structures = []

    for key, struc_lst in struc_dict.items():
        current_key_deduped = []

        for struc in struc_lst:
            is_duplicate = False
            for existing_struc in seen_structures:
                if matcher.fit(struc, existing_struc):
                    is_duplicate = True
                    break

            if not is_duplicate:
                copied_struc = struc.copy()
                current_key_deduped.append(copied_struc)
                seen_structures.append(struc)

        if current_key_deduped:
            deduplicated_dict[key] = current_key_deduped

    return deduplicated_dict


def deduplicate_df(
    df: pd.DataFrame,
    n_keep: int,
    struct_col: str = "struct",
    energy_col: str = "energy_mean_per_atom",
):

    matcher = StructureMatcher()

    df_sorted = df.sort_values(energy_col, ascending=True)
    keep_indices = []
    keep_structs = []

    for idx, row in df_sorted.iterrows():
        struct = row[struct_col]
        is_duplicate = False

        for saved_struct in keep_structs:
            if matcher.fit(struct, saved_struct):
                is_duplicate = True
                break

        if not is_duplicate:
            keep_indices.append(idx)
            keep_structs.append(struct)

        if len(keep_indices) >= n_keep:
            break
    print("keep_indices =", len(keep_indices))
    return df_sorted.loc[keep_indices]


