import json
import pickle
import faiss
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
import gc
from pathlib import Path as p
from ase.io import read, write
from pymatgen.io.ase import AseAtomsAdaptor
from scipy.spatial.distance import cdist
from sklearn.preprocessing import RobustScaler


class DiverseSelector_struct:
    """
    Fast structure-aware selector using:

    1. RobustScaler + PCA on train + pool local features.
    2. local novelty:
       pool local -> train local kNN mean squared L2 distance using FAISS IndexIVFFlat.
    3. local PCA clustering:
       pool local PCA -> local cluster_id using FAISS Kmeans.
    4. structure aggregation:
       - structure_knn_mean = mean(local novelty)
       - structure_cluster_hist = histogram of local cluster ids
    5. greedy selection:
       score = alpha * knn_mean_norm + beta * cluster_score

       cluster_score =
           sum(hist[cid] * cluster_weight[cid]) / sum(hist.values())

       After selecting one structure:
           cluster_weight[cid] *= cluster_decay
       for clusters covered by selected structure.

    Notes
    -----
    - k controls local -> train kNN novelty.
    - n_local_clusters controls local PCA clustering.
    - IndexIVFFlat is approximate and needs train().
    - Distances are squared L2 distances in PCA space.
    """

    def __init__(
        self,
        feature_cols,
        out_info=None,
        batch_size=50000,
        pca_mode="variance",
        pca_value=0.90,
        save_pca_dir=None,
        # score weights
        alpha=0.85,
        beta=0.15,
        cluster_decay=0.5,
        # local clustering
        n_local_clusters=10000,
        kmeans_niter=20,
        # IVF kNN params
        ivf_nlist=4096,
        ivf_nprobe=64,
        ivf_train_size=300000,
        use_gpu=False,
        missing_group_fill_factor=2.0,
        random_state=0,
        trim_train_q = 0.01
        
    ):
        self.feature_cols = list(feature_cols)
        self.out_info = out_info
        self.batch_size = int(batch_size)
        self.trim_train_q = trim_train_q
        self.pca_mode = pca_mode
        self.pca_value = pca_value
        self.save_pca_dir = save_pca_dir

        self.alpha = float(alpha)
        self.beta = float(beta)
        self.cluster_decay = float(cluster_decay)

        self.n_local_clusters = int(n_local_clusters)
        self.kmeans_niter = int(kmeans_niter)

        self.ivf_nlist = int(ivf_nlist)
        self.ivf_nprobe = int(ivf_nprobe)
        self.ivf_train_size = int(ivf_train_size)
        self.use_gpu = bool(use_gpu)

        self.missing_group_fill_factor = float(missing_group_fill_factor)
        self.random_state = random_state

        self._validate_config()

    # ------------------------------------------------------------------
    # validation
    # ------------------------------------------------------------------
    def _validate_config(self):
        if self.pca_mode not in {"variance", "n_components"}:
            raise ValueError("pca_mode must be 'variance' or 'n_components'")

        if self.pca_mode == "variance":
            if not isinstance(self.pca_value, (float, int)):
                raise ValueError("when pca_mode='variance', pca_value must be a float in (0, 1]")
            if not (0 < float(self.pca_value) <= 1):
                raise ValueError("when pca_mode='variance', pca_value must be in (0, 1]")
        else:
            if not isinstance(self.pca_value, (int, np.integer)):
                raise ValueError("when pca_mode='n_components', pca_value must be positive integer")
            if int(self.pca_value) <= 0:
                raise ValueError("when pca_mode='n_components', pca_value must be > 0")

        if self.batch_size <= 0:
            raise ValueError("batch_size must be > 0")

        if self.alpha < 0 or self.beta < 0:
            raise ValueError("alpha and beta must be >= 0")

        if self.alpha + self.beta <= 0:
            raise ValueError("alpha + beta must be > 0")

        if not (0 <= self.cluster_decay <= 1):
            raise ValueError("cluster_decay must be in [0, 1]")

        if self.n_local_clusters <= 0:
            raise ValueError("n_local_clusters must be > 0")

        if self.kmeans_niter <= 0:
            raise ValueError("kmeans_niter must be > 0")

        if self.ivf_nlist <= 0:
            raise ValueError("ivf_nlist must be > 0")

        if self.ivf_nprobe <= 0:
            raise ValueError("ivf_nprobe must be > 0")

        if self.ivf_train_size <= 0:
            raise ValueError("ivf_train_size must be > 0")

        if self.missing_group_fill_factor <= 0:
            raise ValueError("missing_group_fill_factor must be > 0")

    def _check_columns(self, df_pool, df_train, group_col=None, struct_col=None):
        missing_pool = [c for c in self.feature_cols if c not in df_pool.columns]
        missing_train = [c for c in self.feature_cols if c not in df_train.columns]

        if missing_pool:
            raise ValueError(f"feature columns missing in df_pool: {missing_pool}")
        if missing_train:
            raise ValueError(f"feature columns missing in df_train: {missing_train}")

        if group_col is not None:
            if group_col not in df_pool.columns:
                raise ValueError(f"group_col {group_col!r} missing in df_pool")
            if group_col not in df_train.columns:
                raise ValueError(f"group_col {group_col!r} missing in df_train")

        if struct_col is not None:
            struct_cols = [struct_col] if isinstance(struct_col, str) else list(struct_col)
            miss = [c for c in struct_cols if c not in df_pool.columns]
            if miss:
                raise ValueError(f"struct_col columns missing in df_pool: {miss}")

    # ------------------------------------------------------------------
    # main API
    # ------------------------------------------------------------------
    def select(
        self,
        df_pool,
        df_train,
        k=5,
        group_col=None,
        struct_col=None,
        select_n=None,
    ):
        """
        Parameters
        ----------
        df_pool : pd.DataFrame
            Candidate pool local rows.

        df_train : pd.DataFrame
            Existing train local rows.

        k : int
            kNN used for local novelty, i.e. pool local -> original train local.

        group_col : str or None
            If not None, compute novelty group-wise:
            pool group g only compares to train group g.

        struct_col : str, list[str], or None
            If None, select local rows by score.
            If not None, select structures using:
                score = alpha * knn_mean_norm + beta * cluster_score

        select_n : int or None
            Number of selected local rows or structures.
        """
        df_pool = df_pool.copy()
        df_train = df_train.copy()

        k = int(k)
        if k <= 0:
            raise ValueError("k must be > 0")

        if select_n is not None:
            select_n = int(select_n)
            if select_n <= 0:
                raise ValueError("select_n must be > 0")

        self._check_columns(df_pool, df_train, group_col=group_col, struct_col=struct_col)

        if len(df_pool) == 0:
            return pd.DataFrame()

        x_pool = df_pool[self.feature_cols].to_numpy(dtype=np.float32)
        x_train = df_train[self.feature_cols].to_numpy(dtype=np.float32)

        scaler, pca, coords_pool, coords_train = self._fit_scaler_pca(x_pool, x_train)

        local_pool_df = self._build_local_df(
            df=df_pool,
            coords=coords_pool,
            split="pool",
            group_col=group_col,
            struct_col=struct_col,
        )

        local_train_df = self._build_local_df(
            df=df_train,
            coords=coords_train,
            split="train",
            group_col=group_col,
            struct_col=None,
        )

        local_pool_df["pca_n_components"] = int(pca.n_components_)
        local_train_df["pca_n_components"] = int(pca.n_components_)

        # --------------------------------------------------------------
        # 1. novelty: pool local -> original train local, using IVF
        # --------------------------------------------------------------
        if group_col is None:
            novelty = self._compute_knn_score_ivf(coords_pool, coords_train, k=k)
        else:
            novelty = self._compute_grouped_knn_score_ivf(
                df_pool=df_pool,
                df_train=df_train,
                coords_pool=coords_pool,
                coords_train=coords_train,
                group_col=group_col,
                k=k,
            )

        local_pool_df["knn_score"] = novelty
        local_pool_df["novelty"] = novelty
        local_pool_df["final_score"] = novelty

        local_train_df["knn_score"] = np.nan
        local_train_df["novelty"] = np.nan
        local_train_df["final_score"] = np.nan

        local_pool_df["selected_local"] = False
        local_pool_df["selected_local_rank"] = np.nan
        local_pool_df["selected_structure"] = False
        local_pool_df["selected_structure_rank"] = np.nan
        local_pool_df["greedy_score"] = np.nan
        local_pool_df["cluster_score"] = np.nan
        local_pool_df["structure_knn_mean"] = np.nan
        local_pool_df["local_cluster_id"] = -1

        # --------------------------------------------------------------
        # 2. local PCA clustering on pool locals
        # --------------------------------------------------------------
        local_cluster_id, cluster_centers = self._cluster_pool_locals(coords_pool)
        local_pool_df["local_cluster_id"] = local_cluster_id.astype(int)

        self.local_cluster_centers_ = cluster_centers

        # --------------------------------------------------------------
        # 3. selection
        # --------------------------------------------------------------
        if struct_col is None:
            selected_df = self._select_local_simple(
                local_pool_df=local_pool_df,
                select_n=select_n,
            )
        else:
            selected_df = self._select_structure_cluster_greedy(
                local_pool_df=local_pool_df,
                struct_col=struct_col,
                select_n=select_n,
            )

        # save PCA information
        if self.save_pca_dir is not None:
            self._save_pca_outputs(
                scaler=scaler,
                pca=pca,
                local_pool_df=local_pool_df,
                local_train_df=local_train_df,
            )

        return selected_df.reset_index(drop=True)

    # ------------------------------------------------------------------
    # preprocessing
    # ------------------------------------------------------------------
    def _fit_scaler_pca(self, x_pool, x_train):
        x_train = x_train.astype(np.float32, copy=False)
        x_pool = x_pool.astype(np.float32, copy=False)

        trim_train_q = getattr(self, "trim_train_q", 0.01)

        # ==================================================
        # 1. RobustScaler-based outlier score on train only
        # ==================================================
        if trim_train_q is not None and trim_train_q > 0:
            trim_scaler = RobustScaler()
            trim_scaler.fit(x_train)

            x_train_robust = trim_scaler.transform(x_train).astype(np.float32, copy=False)

            # squared L2 norm, avoids sqrt for efficiency
            score = np.einsum("ij,ij->i", x_train_robust, x_train_robust)

            cutoff = np.quantile(score, 1.0 - trim_train_q)
            keep_mask = score <= cutoff

            x_train_fit = x_train[keep_mask]

            # safety fallback
            if x_train_fit.shape[0] < max(10, x_train.shape[1] + 1):
                x_train_fit = x_train
        else:
            x_train_fit = x_train

        # ==================================================
        # 2. Fit final scaler on trimmed train + full pool
        # ==================================================
        x_fit = np.vstack([x_train_fit, x_pool]).astype(np.float32, copy=False)

        scaler = RobustScaler()
        scaler.fit(x_fit)

        x_fit_scaled = scaler.transform(x_fit).astype(np.float32, copy=False)
        x_train_scaled = scaler.transform(x_train).astype(np.float32, copy=False)
        x_pool_scaled = scaler.transform(x_pool).astype(np.float32, copy=False)

        n_samples, n_features = x_fit_scaled.shape

        if self.pca_mode == "variance":
            n_components = float(self.pca_value)
        else:
            n_components = min(int(self.pca_value), n_samples, n_features)

        # ==================================================
        # 3. Fit PCA on trimmed reference
        # ==================================================
        pca = PCA(
            n_components=n_components,
            random_state=self.random_state,
        )

        pca.fit(x_fit_scaled)

        # ==================================================
        # 4. Transform full train / pool
        # ==================================================
        coords_train = pca.transform(x_train_scaled).astype(np.float32, copy=False)
        coords_pool = pca.transform(x_pool_scaled).astype(np.float32, copy=False)

        return scaler, pca, coords_pool, coords_train

    # ------------------------------------------------------------------
    # metadata
    # ------------------------------------------------------------------
    def _build_local_df(self, df, coords, split, group_col=None, struct_col=None):
        if self.out_info is None:
            meta_cols = [c for c in df.columns if c not in self.feature_cols]
        else:
            meta_cols = [c for c in self.out_info if c in df.columns]

        out = df[meta_cols].copy()
        out["orig_index"] = df.index.to_numpy()
        out["split"] = split
        out["pca_coords"] = [row.tolist() for row in coords]

        if group_col is not None and group_col not in out.columns:
            out[group_col] = df[group_col].values

        if struct_col is not None:
            struct_cols = [struct_col] if isinstance(struct_col, str) else list(struct_col)
            for c in struct_cols:
                if c not in out.columns:
                    out[c] = df[c].values

        return out

    # ------------------------------------------------------------------
    # FAISS helpers
    # ------------------------------------------------------------------
    def _maybe_to_gpu(self, index):
        if not self.use_gpu:
            return index

        try:
            res = faiss.StandardGpuResources()
            gpu_index = faiss.index_cpu_to_gpu(res, 0, index)
            self._gpu_resources = res
            return gpu_index
        except Exception as e:
            print(f"[FAISS] GPU unavailable, fallback to CPU. Reason: {e}", flush=True)
            return index

    def _sample_train_for_ivf(self, ref_coords):
        n_ref = len(ref_coords)
        train_size = min(self.ivf_train_size, n_ref)

        if train_size >= n_ref:
            return ref_coords

        rng = np.random.default_rng(self.random_state)
        idx = rng.choice(n_ref, size=train_size, replace=False)
        return ref_coords[idx]

    # ------------------------------------------------------------------
    # FAISS IVF distance
    # ------------------------------------------------------------------
    def _compute_knn_score_ivf(self, query_coords, ref_coords, k):
        """
        Approximate mean squared L2 distance to k nearest refs using IndexIVFFlat.
        """
        query_coords = np.ascontiguousarray(query_coords.astype(np.float32))
        ref_coords = np.ascontiguousarray(ref_coords.astype(np.float32))

        n_query = len(query_coords)
        n_ref = len(ref_coords)

        if n_query == 0:
            return np.array([], dtype=np.float32)

        if n_ref == 0:
            return np.full(n_query, np.nan, dtype=np.float32)

        k_eff = min(int(k), n_ref)
        dim = ref_coords.shape[1]

        nlist_eff = min(self.ivf_nlist, max(1, n_ref))
        nprobe_eff = min(self.ivf_nprobe, nlist_eff)

        quantizer = faiss.IndexFlatL2(dim)
        index = faiss.IndexIVFFlat(
            quantizer,
            dim,
            nlist_eff,
            faiss.METRIC_L2,
        )

        train_vectors = self._sample_train_for_ivf(ref_coords)
        train_vectors = np.ascontiguousarray(train_vectors.astype(np.float32))

        # IVF requires at least nlist training points.
        if len(train_vectors) < nlist_eff:
            nlist_eff = max(1, len(train_vectors))
            nprobe_eff = min(nprobe_eff, nlist_eff)

            quantizer = faiss.IndexFlatL2(dim)
            index = faiss.IndexIVFFlat(
                quantizer,
                dim,
                nlist_eff,
                faiss.METRIC_L2,
            )

        index.train(train_vectors)
        index.add(ref_coords)
        index.nprobe = nprobe_eff

        index = self._maybe_to_gpu(index)

        scores = np.empty(n_query, dtype=np.float32)

        for start in range(0, n_query, self.batch_size):
            end = min(start + self.batch_size, n_query)
            dist, _ = index.search(query_coords[start:end], k_eff)
            scores[start:end] = dist.mean(axis=1).astype(np.float32)

        return scores

    def _compute_grouped_knn_score_ivf(
        self,
        df_pool,
        df_train,
        coords_pool,
        coords_train,
        group_col,
        k,
    ):
        """
        pool group g only compares with train group g.
        Each group builds its own IVF index.
        """
        scores = np.full(len(df_pool), np.nan, dtype=np.float32)

        pool_groups = df_pool[group_col].to_numpy()
        train_groups = df_train[group_col].to_numpy()

        for g in pd.unique(pool_groups):
            pool_mask = pool_groups == g
            train_mask = train_groups == g

            pool_idx = np.where(pool_mask)[0]
            train_idx = np.where(train_mask)[0]

            if len(train_idx) == 0:
                continue

            scores[pool_idx] = self._compute_knn_score_ivf(
                query_coords=coords_pool[pool_idx],
                ref_coords=coords_train[train_idx],
                k=k,
            )

        finite = np.isfinite(scores)

        if finite.any():
            max_score = float(np.max(scores[finite]))
            fill_value = max_score * self.missing_group_fill_factor
            if fill_value <= 0:
                fill_value = 1.0
        else:
            fill_value = 1.0

        scores[~finite] = fill_value

        return scores.astype(np.float32)

    # ------------------------------------------------------------------
    # FAISS KMeans local clustering
    # ------------------------------------------------------------------
    def _cluster_pool_locals(self, coords_pool):
        """
        Cluster pool local PCA coords using FAISS Kmeans.
        Return local_cluster_id and cluster centers.
        """
        coords_pool = np.ascontiguousarray(coords_pool.astype(np.float32))
        n, dim = coords_pool.shape

        n_clusters_eff = min(self.n_local_clusters, n)

        print(
            f"[FAISS KMeans] n_local={n}, dim={dim}, n_clusters={n_clusters_eff}, "
            f"niter={self.kmeans_niter}, gpu={self.use_gpu}",
            flush=True,
        )

        kmeans = faiss.Kmeans(
            d=dim,
            k=n_clusters_eff,
            niter=self.kmeans_niter,
            verbose=True,
            gpu=self.use_gpu,
            seed=int(self.random_state),
        )

        kmeans.train(coords_pool)

        dist, cluster_id = kmeans.index.search(coords_pool, 1)

        cluster_id = cluster_id[:, 0].astype(np.int32)
        centers = kmeans.centroids.astype(np.float32)

        return cluster_id, centers

    # ------------------------------------------------------------------
    # normalization
    # ------------------------------------------------------------------
    @staticmethod
    def _minmax_norm(x):
        x = np.asarray(x, dtype=np.float64)
        out = np.zeros_like(x, dtype=np.float64)

        finite = np.isfinite(x)
        if finite.sum() == 0:
            return out

        xmin = np.min(x[finite])
        xmax = np.max(x[finite])

        if xmax - xmin < 1e-12:
            return out

        out[finite] = (x[finite] - xmin) / (xmax - xmin)
        return out

    # ------------------------------------------------------------------
    # local fallback selection
    # ------------------------------------------------------------------
    def _select_local_simple(self, local_pool_df, select_n=None):
        """
        If struct_col is None, simply select top local rows by novelty.
        """
        work = local_pool_df.copy()
        n = len(work)

        if select_n is None:
            select_n = n
        select_n = min(int(select_n), n)

        work = work.sort_values("novelty", ascending=False, kind="stable").copy()
        selected = work.iloc[:select_n].copy()

        selected["selected_local"] = True
        selected["selected_local_rank"] = np.arange(1, len(selected) + 1)
        selected["greedy_score"] = selected["novelty"].to_numpy(dtype=float)

        return selected.reset_index(drop=True)

    # ------------------------------------------------------------------
    # structure cluster greedy selection
    # ------------------------------------------------------------------
    def _select_structure_cluster_greedy(
        self,
        local_pool_df,
        struct_col,
        select_n=None,
    ):
        """
        Structure mode with cluster coverage greedy.

        Fixed:
            knn_mean_norm

        Dynamic:
            cluster_score based on global cluster_weight.

        Greedy:
            score = alpha * knn_mean_norm + beta * cluster_score
        """
        struct_cols = [struct_col] if isinstance(struct_col, str) else list(struct_col)

        work = local_pool_df.copy()
        work["_row_pos"] = np.arange(len(work))

        grouped = work.groupby(struct_cols, sort=False, dropna=False)

        structure_keys = []
        structure_rows = []
        structure_knn_mean = []
        structure_hist = []

        for key, sub in grouped:
            if not isinstance(key, tuple):
                key = (key,)

            rows = sub["_row_pos"].to_numpy(dtype=int)
            cids = sub["local_cluster_id"].to_numpy(dtype=np.int32)
            vals, counts = np.unique(cids, return_counts=True)

            structure_keys.append(key)
            structure_rows.append(rows)
            structure_knn_mean.append(float(np.mean(sub["knn_score"].to_numpy(dtype=np.float64))))
            structure_hist.append((vals.astype(np.int32), counts.astype(np.float64)))

        n_struct = len(structure_keys)

        if select_n is None:
            select_n = n_struct
        select_n = min(int(select_n), n_struct)

        structure_knn_mean = np.asarray(structure_knn_mean, dtype=np.float64)
        knn_mean_norm = self._minmax_norm(structure_knn_mean)

        base_score = self.alpha * knn_mean_norm

        n_clusters = int(max(local_pool_df["local_cluster_id"].max() + 1, 1))
        cluster_weight = np.ones(n_clusters, dtype=np.float64)

        selected_mask = np.zeros(n_struct, dtype=bool)
        selected_order = []
        selected_records = []

        # Initial cluster score.
        cluster_score = np.empty(n_struct, dtype=np.float64)
        for i in range(n_struct):
            vals, counts = structure_hist[i]
            denom = counts.sum()
            if denom <= 0:
                cluster_score[i] = 0.0
            else:
                cluster_score[i] = float(np.sum(counts * cluster_weight[vals]) / denom)

        for rank in range(1, select_n + 1):
            total_score = base_score + self.beta * cluster_score
            total_score[selected_mask] = -np.inf

            best_i = int(np.nanargmax(total_score))
            if not np.isfinite(total_score[best_i]):
                break

            selected_mask[best_i] = True
            selected_order.append(best_i)

            vals, counts = structure_hist[best_i]

            # Save current score before update.
            best_cluster_score = float(cluster_score[best_i])
            best_base = float(base_score[best_i])
            best_total = float(total_score[best_i])
            best_knn = float(structure_knn_mean[best_i])
            best_knn_norm = float(knn_mean_norm[best_i])

            # Update only global cluster_weight.
            cluster_weight[vals] *= self.cluster_decay

            # Recompute cluster_score using new global cluster_weight.
            # Simple version: recompute all unselected structures.
            # 60k structures * 1000 rounds is acceptable compared with FAISS distance.
            for i in range(n_struct):
                if selected_mask[i]:
                    continue
                v, c = structure_hist[i]
                denom = c.sum()
                if denom <= 0:
                    cluster_score[i] = 0.0
                else:
                    cluster_score[i] = float(np.sum(c * cluster_weight[v]) / denom)

            record = {
                "selected_structure_rank": rank,
                "structure_knn_mean": best_knn,
                "structure_knn_mean_norm": best_knn_norm,
                "base_score": best_base,
                "cluster_score": best_cluster_score,
                "greedy_score": best_total,
                "n_local": int(len(structure_rows[best_i])),
                "n_unique_clusters": int(len(vals)),
            }

            for c, v in zip(struct_cols, structure_keys[best_i]):
                record[c] = v

            selected_records.append(record)

            if rank % 50 == 0 or rank == 1:
                print(
                    f"[select] rank={rank}/{select_n}, "
                    f"knn_mean={best_knn:.6g}, "
                    f"cluster_score={best_cluster_score:.4f}, "
                    f"score={best_total:.4f}",
                    flush=True,
                )

        # Mark selected rows.
        for rank, i in enumerate(selected_order, start=1):
            rows = structure_rows[i]

            key = structure_keys[i]
            rec = selected_records[rank - 1]

            work.loc[work["_row_pos"].isin(rows), "selected_structure"] = True
            work.loc[work["_row_pos"].isin(rows), "selected_structure_rank"] = rank
            work.loc[work["_row_pos"].isin(rows), "greedy_score"] = rec["greedy_score"]
            work.loc[work["_row_pos"].isin(rows), "cluster_score"] = rec["cluster_score"]
            work.loc[work["_row_pos"].isin(rows), "structure_knn_mean"] = rec["structure_knn_mean"]
            work.loc[work["_row_pos"].isin(rows), "structure_final_score"] = rec["structure_knn_mean"]

        selected_local_rows = work[work["selected_structure"]].copy()
        selected_local_rows = selected_local_rows.drop(columns=["_row_pos"])

        summary_df = pd.DataFrame(selected_records)
        if len(summary_df) > 0:
            summary_df = summary_df.sort_values("selected_structure_rank").reset_index(drop=True)

        self.selected_structure_summary_ = summary_df
        self.cluster_weight_final_ = cluster_weight
        self.structure_hist_ = structure_hist

        selected_local_rows = selected_local_rows.sort_values(
            ["selected_structure_rank"],
            kind="stable",
        ).reset_index(drop=True)

        return selected_local_rows

    # ------------------------------------------------------------------
    # save outputs
    # ------------------------------------------------------------------
    def _save_pca_outputs(self, scaler, pca, local_pool_df, local_train_df):
        save_dir = p(self.save_pca_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        preprocess = {
            "scaler": scaler,
            "pca": pca,
            "feature_cols": self.feature_cols,
            "pca_mode": self.pca_mode,
            "pca_value": self.pca_value,
            "alpha": self.alpha,
            "beta": self.beta,
            "cluster_decay": self.cluster_decay,
            "n_local_clusters": self.n_local_clusters,
            "kmeans_niter": self.kmeans_niter,
            "ivf_nlist": self.ivf_nlist,
            "ivf_nprobe": self.ivf_nprobe,
            "ivf_train_size": self.ivf_train_size,
        }

        with open(save_dir / "preprocess_model.pkl", "wb") as f:
            pickle.dump(preprocess, f)

        with open(save_dir / "scaler_model.pkl", "wb") as f:
            pickle.dump(scaler, f)

        with open(save_dir / "pca_model.pkl", "wb") as f:
            pickle.dump(pca, f)

        all_local = pd.concat([local_train_df, local_pool_df], ignore_index=True)

        with open(save_dir / "pca_local_all.pkl", "wb") as f:
            pickle.dump(all_local, f)

        all_local.to_json(
            save_dir / "pca_local_all.json.gz",
            orient="records",
            lines=True,
            compression="gzip",
            force_ascii=False,
        )

        meta = {
            "feature_cols": self.feature_cols,
            "pca_n_components": int(pca.n_components_),
            "pca_explained_variance_ratio_sum": float(np.sum(pca.explained_variance_ratio_)),
            "pca_mode": self.pca_mode,
            "pca_value": self.pca_value,
            "scaler": "RobustScaler",
            "selector": "ivf_knn_local_cluster_structure_greedy",
            "alpha": self.alpha,
            "beta": self.beta,
            "cluster_decay": self.cluster_decay,
            "n_local_clusters": self.n_local_clusters,
            "kmeans_niter": self.kmeans_niter,
            "ivf_nlist": self.ivf_nlist,
            "ivf_nprobe": self.ivf_nprobe,
            "ivf_train_size": self.ivf_train_size,
        }

        with open(save_dir / "pca_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)


def sample_traj_xyz(
    input_file, n_frames: int = 10, include_e: bool = False,
    include_f: bool = False, include_s: bool = False,
):
    traj = read(input_file, index=":")
    total = len(traj)
    if total <= n_frames:
        idx = np.arange(total)
    else:
        idx = np.linspace(0, total - 1, n_frames, dtype=int)

    result = {
        "path": [str(input_file)] * len(idx),
        "structures": [],
        "idx": idx.tolist(),
    }
    if include_e:
        result["e"] = []
    if include_f:
        result["f"] = []
    if include_s:
        result["s"] = []
    adaptor = AseAtomsAdaptor()

    for i in idx:
        atoms = traj[i]
        structure = adaptor.get_structure(atoms)
        result["structures"].append(structure)
        if include_e:
            try:
                e = atoms.get_potential_energy()
                e = e / structure.num_sites
            except Exception:
                e = None
            result["e"].append(e)
        if include_f:
            try:
                f = atoms.get_forces()
            except Exception:
                f = None
            result["f"].append(f)
        if include_s:
            try:
                s = atoms.get_stress(voigt=False)
            except Exception:
                s = None
            result["s"].append(s)
    return result



# class DiverseSelector:
#     """
#     Parameters
#     ----------
#     feature_cols : list[str]   
#     out_info     : list[str]  | None=all
#     variance_ratio : float    
#     """

#     def __init__(self, feature_cols, out_info=None, variance_ratio=0.90):
#         self.feature_cols  = list(feature_cols)
#         self.out_info      = list(out_info) if out_info else []
#         self.variance_ratio = variance_ratio

#     def _fit_transform(self, X_pool, X_train):
#         n = len(X_pool)
#         X_all    = np.vstack([X_pool, X_train])
#         X_scaled = RobustScaler().fit_transform(X_all)
#         coords   = PCA(n_components=self.variance_ratio).fit_transform(X_scaled)
#         return coords[:n], coords[n:]

#     @staticmethod
#     def _knn_score(coords_pool, coords_train, k):
#         dist = cdist(coords_pool, coords_train)
#         k    = min(k, dist.shape[1])
#         return np.partition(dist, k - 1, axis=1)[:, :k].mean(axis=1)

#     @staticmethod
#     def _greedy_rank(coords_pool, init_scores):
#         n      = len(init_scores)
#         dist_pp = cdist(coords_pool, coords_pool)   
#         scores  = init_scores.astype(float).copy()
#         rank    = np.empty(n, dtype=int)
#         for i in range(n):
#             idx      = int(np.argmax(scores))
#             rank[idx] = i
#             scores    = np.minimum(scores, dist_pp[idx])
#             scores[idx] = -np.inf
#         return rank

#     def _run(self, df_pool, df_train, k):
#         X_pool  = df_pool[self.feature_cols].values.astype(float)
#         X_train = df_train[self.feature_cols].values.astype(float)

#         coords_pool, coords_train = self._fit_transform(X_pool, X_train)
#         knn_scores  = self._knn_score(coords_pool, coords_train, k)
#         greedy_rank = self._greedy_rank(coords_pool, knn_scores)

#         out_cols = (
#             [c for c in self.out_info if c in df_pool.columns]
#             if self.out_info
#             else [c for c in df_pool.columns if c not in self.feature_cols]
#         )
#         result   = df_pool[out_cols].reset_index(drop=True).copy()
#         result["knn_score"]   = knn_scores
#         result["greedy_rank"] = greedy_rank
#         return result

#     def select(self, df_pool, df_train, k=5, group_col=None):
#         """
#         global group_col=None
#         local  group_col=""

#         Returns
#         -------
#         pd.DataFrame
#         """
#         if group_col is None:
#             return self._run(df_pool, df_train, k)

#         parts = []
#         for g, pool_g in df_pool.groupby(group_col):
#             train_g = df_train[df_train[group_col] == g]
#             if len(train_g) == 0:
#                 print(f"[skip] {group_col}={g}: no training data")
#                 continue
#             print(f"[run]  {group_col}={g} | pool={len(pool_g)} | train={len(train_g)}")
#             parts.append(self._run(
#                 pool_g.reset_index(drop=True),
#                 train_g.reset_index(drop=True),
#                 k,
#             ))

#         return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()

