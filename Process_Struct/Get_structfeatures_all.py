from __future__ import annotations

import numpy as np
from itertools import combinations

from pymatgen.core import Structure, Lattice
from pymatgen.analysis.local_env import (
    CrystalNN,
    VoronoiNN,
    LocalStructOrderParams,
)

try:
    from scipy.spatial import ConvexHull
    _SCIPY_OK = True
except ImportError:
    _SCIPY_OK = False

try:
    import octadist as oc
    from Process_Struct import Octahedron
    _OC_OK = True
except ImportError:
    _OC_OK = False


class StructureFeatureExtractor:

    GLOBAL_GROUPS_REGISTRY = {
        "composition": ["Na"],
        "lattice": [
            "a", "b", "c",
            "alpha", "beta", "gamma",
            "volume"
        ],
        "layer_spacing": [
            "d_NaLayer",
            "d_TMLayer",
        ],
    }

    LOCAL_GROUPS_REGISTRY = {
        "composition": ["Na"],

        "O_neighbors": ["O_neighbors"],

        "bond_length": [
            "d_std",
            "d_max_min_ratio",
            "d_distortion_index"
        ],

        "bond_angle": [
            "BAV",
            "cis_angle_mean",
            "cis_angle_std",
            "trans_angle_mean",
            "trans_angle_dev"
        ],

        "quad_elong": [
            "QE",
            "l0_ref"
        ],

        "local_order": [
            "oct_op",
            "q4",
            "q6"
        ],

        "off_center": [
            "off_center_dist"
        ],

        "voronoi": [
            "voronoi_volume"
        ],


        "mom_angle": [
            "mom_angle_mean",
            "mom_angle_std"
        ],

        "octahedra": [
            "d_avg",
            "Oct_vol",
            "D_len",
            "D_tilt",
            "D_ang",
            "D_tors",
            "Q_elong",
            "Var_ang",
            "Q1",
            "Q2",
            "Q3",
            "Q4",
            "Q5",
            "Q6",
        ],
    }

    def __init__(
        self,
        global_features: str | list[str] | None = "all",
        local_features: str | list[str] | None = "all",
        ligand: str = "O",
        tm_elements: list[str] | None = None,
        na_species: tuple = ("Na",),
        tm_species: tuple = ("Mn", "Fe", "Co", "Ni", "Cu"),
        layer_axis: int = 2,
        layer_tol: float = 0.08,
        ligands_max_dist: float = 3.0,
    ):

        self.global_groups = self._resolve(
            global_features,
            self.GLOBAL_GROUPS_REGISTRY
        )

        self.local_groups = self._resolve(
            local_features,
            self.LOCAL_GROUPS_REGISTRY
        )

        self.ligand = ligand

        self.tm_set = set(
            tm_elements or ["Fe", "Mn", "Co", "Ni", "Cu"]
        )

        self.na_species = na_species
        self.tm_species = tm_species

        self.layer_axis = layer_axis
        self.layer_tol = layer_tol

        self.ligands_max_dist = ligands_max_dist

        self._cnn = None
        self._vnn = None

    @staticmethod
    def _resolve(req, reg):

        if req is None:
            return set()

        if req == "all":
            return set(reg.keys())

        return set(req)

    @property
    def cnn(self):

        if self._cnn is None:
            self._cnn = CrystalNN()

        return self._cnn

    def extract(
        self,
        structure: Structure,
        supercell_matrix=None,
    ) -> dict:

        tm_indices = [
            i for i, s in enumerate(structure)
            if s.specie.symbol in self.tm_set
        ]

        na_ratio = (
            2 * int(structure.composition["Na"])
            / int(structure.composition["O"])
        )

        res = {
            "global": self._extract_global(
                structure,
                supercell_matrix=supercell_matrix,
                na_ratio=na_ratio,
            ),
            "local": [],
        }

        if self.local_groups and tm_indices:

            nn_dict = self._build_nn_dict(
                structure,
                tm_indices
            )


            oct_map = (
                self._feat_octahedra_all(structure, tm_indices)
                if "octahedra" in self.local_groups
                else {}
            )

            for idx in tm_indices:

                rec = {
                    "tm_index": idx,
                    "tm_element": structure[idx].specie.symbol,
                    "Na": na_ratio,
                }

                if "O_neighbors" in self.local_groups:
                    rec.update(
                        self._get_neighbor_indices(
                            idx,
                            nn_dict
                        )
                    )

                if "bond_length" in self.local_groups:
                    rec.update(
                        self._feat_bond_length(
                            structure,
                            idx,
                            nn_dict
                        )
                    )

                if "bond_angle" in self.local_groups:
                    rec.update(
                        self._feat_bond_angle(
                            structure,
                            idx,
                            nn_dict
                        )
                    )

                if "quad_elong" in self.local_groups:
                    rec.update(
                        self._feat_quad_elong(
                            structure,
                            idx,
                            nn_dict
                        )
                    )

                if "local_order" in self.local_groups:
                    rec.update(
                        self._feat_local_order(
                            structure,
                            idx
                        )
                    )

                if "off_center" in self.local_groups:
                    rec.update(
                        self._feat_off_center(
                            structure,
                            idx,
                            nn_dict
                        )
                    )

                if "voronoi" in self.local_groups:
                    rec.update(
                        self._feat_voronoi(
                            structure,
                            idx
                        )
                    )


                if "mom_angle" in self.local_groups:
                    rec.update(
                        self._feat_mom_angle(
                            structure,
                            idx,
                            nn_dict
                        )
                    )

                if "octahedra" in self.local_groups:
                    rec.update(
                        oct_map.get(idx, {})
                    )

                res["local"].append(rec)

        return res

    @classmethod
    def extract_features(
        cls,
        structure: Structure,
        **kwargs
    ) -> dict:

        return cls(**kwargs).extract(structure)

    def _extract_global(
        self,
        structure,
        supercell_matrix=None,
        na_ratio=np.nan,
    ):

        out = {}

        if "lattice" in self.global_groups:

            lat = (
                Lattice(
                    np.linalg.inv(supercell_matrix)
                    @ structure.lattice.matrix
                )
                if supercell_matrix is not None
                else structure.lattice
            )

            out.update({
                "a": lat.a,
                "b": lat.b,
                "c": lat.c,
                "alpha": lat.alpha,
                "beta": lat.beta,
                "gamma": lat.gamma,
                "volume": lat.volume,
            })

        if "composition" in self.global_groups:
            out["Na"] = na_ratio

        if "layer_spacing" in self.global_groups:
            out.update(
                self._feat_layer_spacing(structure)
            )

        return out

    def _build_nn_dict(
        self,
        structure,
        tm_indices
    ):

        nn_dict = {
            i: self.cnn.get_nn_info(structure, i)
            for i in tm_indices
        }

        if "mom_angle" in self.local_groups:

            lig_idx = {
                n["site_index"]
                for i in tm_indices
                for n in nn_dict[i]
                if n["site"].specie.symbol == self.ligand
            }

            for j in lig_idx:
                nn_dict[j] = self.cnn.get_nn_info(
                    structure,
                    j
                )

        return nn_dict

    def _get_neighbor_indices(
        self,
        idx,
        nn_dict
    ):

        return {
            "O_neighbors": sorted([
                n["site_index"]
                for n in nn_dict[idx]
                if n["site"].specie.symbol == "O"
            ])
        }

    def _feat_bond_length(
        self,
        structure,
        idx,
        nn_dict
    ):

        bl = np.array([
            np.linalg.norm(
                n["site"].coords
                - structure[idx].coords
            )
            for n in nn_dict[idx]
            if n["site"].specie.symbol == self.ligand
        ])

        if not len(bl):

            return {
                k: np.nan
                for k in [
                    "d_std",
                    "d_max_min_ratio",
                    "d_distortion_index"
                ]
            }

        return {
            "d_std": float(bl.std()),
            "d_max_min_ratio": float(bl.max()/bl.min()),
            "d_distortion_index": float(
                np.mean(np.abs(bl - bl.mean()))
                / bl.mean()
            ),
        }

    def _feat_bond_angle(
        self,
        structure,
        idx,
        nn_dict
    ):

        nbrs = [
            n["site"].coords
            for n in nn_dict[idx]
            if n["site"].specie.symbol == self.ligand
        ]

        if len(nbrs) < 2:

            return {
                k: np.nan
                for k in [
                    "BAV",
                    "cis_angle_mean",
                    "cis_angle_std",
                    "trans_angle_mean",
                    "trans_angle_dev"
                ]
            }

        center = structure[idx].coords

        angles = np.array([
            np.degrees(
                np.arccos(
                    np.clip(
                        np.dot(i-center, j-center)
                        / (
                            np.linalg.norm(i-center)
                            * np.linalg.norm(j-center)
                        ),
                        -1,
                        1
                    )
                )
            )
            for i, j in combinations(nbrs, 2)
        ])

        cis = angles[angles < 135]
        trans = angles[angles >= 135]

        return {
            "BAV": float(
                np.sum((angles - 90)**2)
                / max(len(angles)-1, 1)
            ),

            "cis_angle_mean":
                float(cis.mean())
                if len(cis) else np.nan,

            "cis_angle_std":
                float(cis.std())
                if len(cis) else np.nan,

            "trans_angle_mean":
                float(trans.mean())
                if len(trans) else np.nan,

            "trans_angle_dev":
                float(abs(trans.mean()-180))
                if len(trans) else np.nan,
        }

    def _feat_quad_elong(
        self,
        structure,
        idx,
        nn_dict
    ):

        bl = np.array([
            np.linalg.norm(
                n["site"].coords
                - structure[idx].coords
            )
            for n in nn_dict[idx]
            if n["site"].specie.symbol == self.ligand
        ])

        if not len(bl):
            return {
                "QE": np.nan,
                "l0_ref": np.nan
            }

        try:

            l0 = (
                (
                    3 * ConvexHull([
                        n["site"].coords
                        for n in nn_dict[idx]
                        if n["site"].specie.symbol == self.ligand
                    ]).volume / 8
                ) ** (1/3)
                if (_SCIPY_OK and len(bl) >= 4)
                else bl.mean()
            )

        except:
            l0 = bl.mean()

        return {
            "QE": float(np.mean((bl/l0)**2)),
            "l0_ref": float(l0),
        }

    def _feat_local_order(
        self,
        structure,
        idx
    ):

        try:

            ops = LocalStructOrderParams(
                ["oct", "q4", "q6"]
            ).get_order_parameters(
                structure,
                idx
            )

            return {
                "oct_op": ops[0],
                "q4": ops[1],
                "q6": ops[2],
            }

        except:

            return {
                "oct_op": np.nan,
                "q4": np.nan,
                "q6": np.nan,
            }

    def _feat_off_center(
        self,
        structure,
        idx,
        nn_dict
    ):

        pts = [
            n["site"].coords
            for n in nn_dict[idx]
            if n["site"].specie.symbol == self.ligand
        ]

        if not pts:
            return {"off_center_dist": np.nan}

        return {
            "off_center_dist": float(
                np.linalg.norm(
                    structure[idx].coords
                    - np.mean(pts, axis=0)
                )
            )
        }

    def _feat_voronoi(
        self,
        structure,
        idx
    ):

        try:

            return {
                "voronoi_volume": float(
                    sum(
                        v["volume"]
                        for v in VoronoiNN(
                            compute_adj_neighbors=False
                        ).get_voronoi_polyhedra(
                            structure,
                            idx
                        ).values()
                    )
                )
            }

        except:

            return {
                "voronoi_volume": np.nan
            }


    def _feat_mom_angle(
        self,
        structure,
        idx,
        nn_dict
    ):

        angles = []

        c_coords = structure[idx].coords

        for o_nn in nn_dict[idx]:

            if o_nn["site"].specie.symbol != self.ligand:
                continue

            o_idx = o_nn["site_index"]
            o_coords = o_nn["site"].coords

            for m2 in nn_dict.get(o_idx, []):

                if (
                    m2["site"].specie.symbol in self.tm_set
                    and m2["site_index"] != idx
                ):

                    v1 = c_coords - o_coords
                    v2 = m2["site"].coords - o_coords

                    angles.append(
                        np.degrees(
                            np.arccos(
                                np.clip(
                                    np.dot(v1, v2)
                                    / (
                                        np.linalg.norm(v1)
                                        * np.linalg.norm(v2)
                                    ),
                                    -1,
                                    1
                                )
                            )
                        )
                    )

        return {
            "mom_angle_mean":
                float(np.mean(angles))
                if angles else np.nan,

            "mom_angle_std":
                float(np.std(angles))
                if angles else np.nan,
        }

    def _feat_octahedra_all(
        self,
        structure,
        tm_indices
    ):

        res = {}

        if not _OC_OK:

            return {
                i: {
                    k: np.nan
                    for k in self.LOCAL_GROUPS_REGISTRY["octahedra"]
                }
                for i in tm_indices
            }

        for i in tm_indices:

            try:

                o_info = sorted(
                    [
                        n
                        for n in self.cnn.get_nn_info(structure, i)
                        if n["site"].specie.symbol == self.ligand
                    ],
                    key=lambda x:
                        x["site"].distance(structure[i])
                )[:6]

                if len(o_info) < 6:
                    raise ValueError

                d_obj = oc.CalcDistortion(
                    [structure[i].coords.tolist()]
                    + [
                        n["site"].coords.tolist()
                        for n in o_info
                    ]
                )

                octa = Octahedron(
                    core_site=structure[i],
                    structure=structure,
                    ligands_max_distance=self.ligands_max_dist
                )

                rec = {
                    "d_avg": d_obj.d_mean,
                    "Oct_vol": octa.volume,
                    "D_len": d_obj.zeta,
                    "D_tilt": d_obj.delta,
                    "D_ang": d_obj.sigma,
                    "D_tors": d_obj.theta,
                    "Q_elong":
                        octa.calculate_quadratic_elongation(),
                    "Var_ang":
                        octa.calculate_bond_angle_variance(),
                }

                rec.update({
                    f"Q{k}": v
                    for k, v in enumerate(
                        octa.calculate_van_vleck_distortion_modes(),
                        1
                    )
                })

                res[i] = rec

            except:

                res[i] = {
                    k: np.nan
                    for k in self.LOCAL_GROUPS_REGISTRY["octahedra"]
                }

        return res

    def _feat_layer_spacing(self, structure):

        L = structure.lattice.abc[self.layer_axis]

        # =========================
        # cluster nearby layers
        # =========================

        def cluster_layers(fracs):

            if len(fracs) == 0:
                return np.array([])

            fracs = np.sort(np.array(fracs) % 1)

            groups = [[fracs[0]]]

            for x in fracs[1:]:

                if x - groups[-1][-1] < self.layer_tol:
                    groups[-1].append(x)

                else:
                    groups.append([x])

            # periodic merge
            if (
                len(groups) > 1
                and groups[0][0] + 1 - groups[-1][-1]
                < self.layer_tol
            ):

                groups[-1].extend(
                    [v + 1 for v in groups[0]]
                )

                groups.pop(0)

            centers = np.array([
                np.mean(g) % 1
                for g in groups
            ])

            return np.sort(centers)

        # =========================
        # oxygen layers
        # =========================

        o_fracs = [
            structure[i].frac_coords[self.layer_axis] % 1
            for i in range(len(structure))
            if structure[i].specie.symbol == "O"
        ]

        o_layers = cluster_layers(o_fracs)

        if len(o_layers) < 2:

            return {
                "d_NaLayer": np.nan,
                "d_TMLayer": np.nan,
            }

        d_na = []
        d_tm = []

        # =========================
        # loop over neighboring O-O slabs
        # =========================

        for i in range(len(o_layers)):

            z1 = o_layers[i]

            if i == len(o_layers) - 1:
                z2 = o_layers[0] + 1
            else:
                z2 = o_layers[i + 1]

            dz = (z2 - z1) * L

            # =========================
            # determine slab type
            # =========================

            has_tm = False

            for site in structure:

                specie = site.specie.symbol

                if specie not in self.tm_species:
                    continue

                z = site.frac_coords[self.layer_axis] % 1

                # move into same periodic image
                if z < z1:
                    z += 1

                # TM located inside this O-O slab
                if z1 < z < z2:

                    has_tm = True
                    break

            # =========================
            # classify slab
            # =========================

            # TM slab
            if has_tm:

                d_tm.append(dz)

            # Na slab OR vacancy slab
            else:

                d_na.append(dz)

        return {

            "d_NaLayer":
                float(np.mean(d_na))
                if len(d_na)
                else np.nan,

            "d_TMLayer":
                float(np.mean(d_tm))
                if len(d_tm)
                else np.nan,
        }