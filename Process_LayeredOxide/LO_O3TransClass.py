import numpy as np
from pymatgen.core import Structure
from pathlib import Path as p
import random
from Process_Struct import deduplicate
class LayerOxide_O3_Transformer:
    SC_Dict = {
        '1_0':([1,0,0],[0,1,0],[0,0,1]),
        '2_0':([1,0,0],[0,2,0],[0,0,1]),
        '3_0':([2,1,0],[1,2,0],[0,0,1]), 
        '3_1':([1,0,0],[0,3,0],[0,0,1]), 
        '4_0':([2,0,0],[0,2,0],[0,0,1]),
        '4_1':([1,0,0],[0,4,0],[0,0,1]),
        '6_0':([2,0,0],[0,3,0],[0,0,1]),
        '6_1':([4,2,0],[1,2,0],[0,0,1]),
        '8_0':([2,0,0],[0,4,0],[0,0,1]), 
        '9_0':([3,0,0],[0,3,0],[0,0,1]),
        '12_0':([3,0,0],[0,4,0],[0,0,1]), 
        '12_1':([4,2,0],[2,4,0],[0,0,1]),
        '15_0':([3,0,0],[0,5,0],[0,0,1]),
        '16_0':([4,0,0],[0,4,0],[0,0,1]),
        '18_0':([3,0,0],[0,6,0],[0,0,1]),
        '20_0':([4,0,0],[0,5,0],[0,0,1]),
        '24_0':([4,0,0],[0,6,0],[0,0,1]),
        '25_0':([5,0,0],[0,5,0],[0,0,1]),
        '30_0':([5,0,0],[0,6,0],[0,0,1]),
        '36_0':([6,0,0],[0,6,0],[0,0,1]),
    }
    def __init__(self, tm_elements=["Mn",'Ni' ,'Cu',"Fe"], ion_elements=["Na"], o_element="O"):
        self.tm_elements = tm_elements
        self.ion_elements = ion_elements
        self.o_element = o_element

    @staticmethod
    def _format_supercell_matrix(M):
        m_array = np.array(M)
        if m_array.ndim == 1 and len(m_array) == 3:
            return np.diag(m_array)
        elif m_array.shape == (3, 3):
            return m_array
        else:
            raise ValueError("SC Lattice Wrong")

    @staticmethod
    def _get_supercell_coords(tran_vector, M):
        M_mat = LayerOxide_O3_Transformer._format_supercell_matrix(M)
        s_orig = np.array(tran_vector)
        return np.linalg.solve(M_mat.T, s_orig)

    def _apply_logic_shifts(self, struct, tm_shift_map, ion_shift_map, M):
        tm_groups, tm_zs = self.group_by_z(struct, self.tm_elements)
        o_idx, nearest_layer = self._get_nearest_o_to_tm(struct, tm_zs)
        
        for l_idx, vec in tm_shift_map.items():
            if l_idx >= len(tm_groups): continue
            s_vec = self._get_supercell_coords(vec, M)
            to_shift = list(tm_groups[l_idx]) + [o_idx[i] for i, l in enumerate(nearest_layer) if l == l_idx]
            struct.translate_sites(to_shift, s_vec, frac_coords=True)

        if ion_shift_map:
            ion_groups, _ = self.group_by_z(struct, self.ion_elements)
            for l_idx, vec in ion_shift_map.items():
                if l_idx >= len(ion_groups): continue
                s_vec = self._get_supercell_coords(vec, M)
                struct.translate_sites(ion_groups[l_idx], s_vec, frac_coords=True)

        for i, site in enumerate(struct):
            struct.replace(i, site.species, site.frac_coords % 1.0)
        return struct

    def o3_to_op2_6layer(self, s: Structure, SC_matrix=[1, 1, 1]) -> Structure:
        struct = s.copy()
        struct.make_supercell((1, 1, 2))
        M_eff = np.array(self._format_supercell_matrix(SC_matrix))
        M_eff[2, :] *= 2
        shifts = {1: [2/3, 1/3, 0], 2: [2/3, 1/3, 0], 3: [1/3, 2/3, 0], 4: [1/3, 2/3, 0]}
        return self._apply_logic_shifts(struct, shifts, shifts, M_eff)

    def o3_to_o1(self, s: Structure, SC_matrix=[1, 1, 1]) -> Structure:
        tm_shifts = {1: [1/3, 2/3, 0], 2: [2/3, 1/3, 0]}
        na_shifts = {0: [1/3, 2/3, 0], 1: [2/3, 1/3, 0], 2: [0, 0, 0]}
        return self._apply_logic_shifts(s.copy(), tm_shifts, na_shifts, SC_matrix)

    def o3_to_p3(self, s: Structure, SC_matrix=[1, 1, 1]) -> Structure:
        tm_shifts = {1: [2/3, 1/3, 0], 2: [1/3, 2/3, 0]}
        na_shifts = {1: [2/3, 1/3, 0], 2: [1/3, 2/3, 0]}
        return self._apply_logic_shifts(s.copy(), tm_shifts, na_shifts, SC_matrix)

    def op2_6layer_to_2layer(self, structure: Structure, check_dict: dict = None):
        _, na_centers = self.group_by_z(structure, self.ion_elements)
        na_centers = np.sort(np.asarray(na_centers) % 1.0)

        new_lat = structure.lattice.matrix.copy()
        new_lat[2] /= 3.0

        struct_list = []

        def in_window(z, start, end):
            z = z % 1.0
            if start <= end:
                return start <= z < end
            return z >= start or z < end

        def nearest_na_layer(z):
            dz = np.abs(((z - na_centers + 0.5) % 1.0) - 0.5)
            return int(np.argmin(dz))

        for start in range(6):
            end = (start + 2) % 6
            sb = na_centers[start]
            eb = na_centers[end]

            keep_na_layers = {start, (start + 1) % 6}

            species = []
            coords = []

            for site in structure:
                z = site.frac_coords[2] % 1.0
                is_na = site.specie.symbol in self.ion_elements

                if is_na:
                    keep = nearest_na_layer(z) in keep_na_layers
                else:
                    keep = in_window(z, sb, eb)

                if keep:
                    species.append(site.specie)
                    coords.append([
                        site.frac_coords[0] % 1.0,
                        site.frac_coords[1] % 1.0,
                        ((z - sb) % 1.0) * 3.0,
                    ])

            ns = Structure(new_lat, species, coords, to_unit_cell=True)
            ns.sort()
            struct_list.append(ns)

        if check_dict:
            el = check_dict["element"]
            times = check_dict["times"]

            re_list = []
            for ss in struct_list:
                el_results = self.get_TM_con(ss, el)
                if np.isclose(el_results[el] / el_results["O"], times):
                    re_list.append(ss)

            return re_list

        return struct_list

    def group_by_z(self, structure: Structure, species_list: list, tolerance=0.1):
        indices = [i for i, site in enumerate(structure) if site.specie.symbol in species_list]
        if not indices: return [], []
        z_coords = np.array([structure[i].frac_coords[2] for i in indices])
        sort_idx = np.argsort(z_coords)
        sorted_indices, sorted_z = np.array(indices)[sort_idx], z_coords[sort_idx]
        split_indices = np.where(np.diff(sorted_z) > tolerance)[0] + 1
        groups = [list(g) for g in np.split(sorted_indices, split_indices)]
        if len(groups) > 1 and ((sorted_z[0] + 1.0) - sorted_z[-1] < tolerance):
            groups[0] = list(groups[-1]) + list(groups[0])
            groups.pop()
        centers = []
        for g in groups:
            zs = np.array([structure[i].frac_coords[2] for i in g])
            if np.ptp(zs) > 0.5:
                zs = np.where(zs > 0.5, zs - 1.0, zs)
            centers.append(np.mean(zs) % 1.0)
        return groups, centers
    
    def batch_transform_by_keys(self, s: Structure, A_matrix, key_prefixes: list, get_type: list = ['o1', 'p3', 'op2_6layer']):

        current_types = get_type + ['o3'] if 'o3' not in get_type else get_type
        results = {phase: {} for phase in current_types}
        
        A = self._format_supercell_matrix(A_matrix)
        method_map = {
            'o1': self.o3_to_o1,
            'p3': self.o3_to_p3,
            'op2_6layer': self.o3_to_op2_6layer
        }

        matched_keys = sorted([k for k in self.SC_Dict if any(k.startswith(f"{p}_") for p in key_prefixes)])
        
        for k in matched_keys:
            B = np.array(self.SC_Dict[k])
            M_total = np.dot(A, B)
            ec_num = int(round(abs(np.linalg.det(M_total))))
            
            s_expanded = s.copy()
            s_expanded.make_supercell(B)
            
            results['o3'][k] = {
                "structure": s_expanded.copy(),
                "extend_cell_num": ec_num,
                "matrix": M_total
            }
            
            for phase in get_type:
                if phase in method_map:
                    transformed_s = method_map[phase](s_expanded, SC_matrix=M_total)
                    results[phase][k] = {
                        "structure": transformed_s,
                        "extend_cell_num": ec_num,
                        "matrix": M_total
                    }
        return results

    def outstruct_from_batch(self, results: dict, tar: p):

        for phase, r_dict in results.items():
            sub_dir_name = 'op2' if phase == 'op2_6layer' else phase
            tar_dir = tar / sub_dir_name
            tar_dir.mkdir(exist_ok=True, parents=True)

            ec_groups = {}
            for k, r_data in r_dict.items():
                ec = r_data['extend_cell_num']
                if ec not in ec_groups:
                    ec_groups[ec] = []
                
                if phase == 'op2_6layer':
                    subs = self.op2_6layer_to_2layer(r_data['structure'])
                    valid_subs = [ss for ss in subs if self._check_Na(ss)]
                    ec_groups[ec].extend(random.sample(valid_subs, min(len(valid_subs), 2)))
                else:
                    ec_groups[ec].append(r_data['structure'])

            for ec, struct_list in ec_groups.items():

                for s in struct_list:
                    self._safe_save(s, tar_dir, f"{ec}")

    def _safe_save(self, struct: Structure, folder: p, base_name: str):
        num = 0
        while True:
            file_name = folder / f"{base_name}_{num}.vasp"
            if not file_name.exists():
                break
            num += 1
        
        struct.sort().to(filename=str(file_name), fmt='poscar')

    def _check_Na(self, struct):
        com = struct.composition
        na = com.get('Na', 0)
        o = com.get('O', 0)
        return 1 if 2 * int(na) == int(o) else 0
    @staticmethod
    def get_TM_con(struct, el):
        com = struct.composition
        el_count = com.get(el, 0)
        o_count = com.get('O', 0)
        results = {
            str(el): int(el_count),
            'O': int(o_count)
        }
        return results


    def _get_nearest_o_to_tm(self, struct, tm_zs):
        o_idx = [i for i, site in enumerate(struct) if site.specie.symbol == self.o_element]
        o_zs = np.array([struct[i].frac_coords[2] for i in o_idx])
        dist = np.abs(o_zs[:, None] - np.array(tm_zs))
        return o_idx, np.argmin(np.minimum(dist, 1.0 - dist), axis=1)

