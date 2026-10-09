# Process_AL_PCA 参数索引

源码静态索引；保留原有函数名。类构造和公开方法分别列出。默认值不代表适用于所有体系。

## `main`

源文件：[examples/select_diverse.py](examples/select_diverse.py)，第 9 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `DiverseSelector_struct`

源文件：[process_pool.py](process_pool.py)，第 15 行。

```python
DiverseSelector_struct
```

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

## `DiverseSelector_struct.__init__`

源文件：[process_pool.py](process_pool.py)，第 45 行。

```python
DiverseSelector_struct.__init__(self, feature_cols, out_info=None, batch_size=50000, pca_mode='variance', pca_value=0.9, save_pca_dir=None, alpha=0.85, beta=0.15, cluster_decay=0.5, n_local_clusters=10000, kmeans_niter=20, ivf_nlist=4096, ivf_nprobe=64, ivf_train_size=300000, use_gpu=False, missing_group_fill_factor=2.0, random_state=0, trim_train_q=0.01)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `DiverseSelector_struct.select`

源文件：[process_pool.py](process_pool.py)，第 167 行。

```python
DiverseSelector_struct.select(self, df_pool, df_train, k=5, group_col=None, struct_col=None, select_n=None)
```

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

## `sample_traj_xyz`

源文件：[process_pool.py](process_pool.py)，第 855 行。

```python
sample_traj_xyz(input_file, n_frames: int=10, include_e: bool=False, include_f: bool=False, include_s: bool=False)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

