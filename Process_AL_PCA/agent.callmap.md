# Module: Process_AL_PCA

## Functions

### DiverseSelector_struct.__init__
- type: method
- purpose: unknown
- inputs: ['feature_cols', 'out_info', 'batch_size', 'pca_mode', 'pca_value', 'save_pca_dir', 'alpha', 'beta', 'cluster_decay', 'n_local_clusters', 'kmeans_niter', 'ivf_nlist', 'ivf_nprobe', 'ivf_train_size', 'use_gpu', 'missing_group_fill_factor', 'random_state', 'trim_train_q']
- outputs: ['unknown']
- calls: ['DiverseSelector_struct._validate_config']
- called_by: []
- location: Process_AL_PCA\process_pool.py:45

### DiverseSelector_struct._validate_config
- type: method
- purpose: unknown
- inputs: ['unknown']
- outputs: ['unknown']
- calls: []
- called_by: ['DiverseSelector_struct.__init__']
- location: Process_AL_PCA\process_pool.py:98

### DiverseSelector_struct._check_columns
- type: method
- purpose: unknown
- inputs: ['df_pool', 'df_train', 'group_col', 'struct_col']
- outputs: ['unknown']
- calls: []
- called_by: ['DiverseSelector_struct.select']
- location: Process_AL_PCA\process_pool.py:143

### DiverseSelector_struct.select
- type: method
- purpose: Parameters
- inputs: ['df_pool', 'df_train', 'k', 'group_col', 'struct_col', 'select_n']
- outputs: ['unknown']
- calls: ['DiverseSelector_struct._check_columns', 'DiverseSelector_struct._fit_scaler_pca', 'DiverseSelector_struct._build_local_df', 'DiverseSelector_struct._cluster_pool_locals', 'DiverseSelector_struct._compute_knn_score_ivf', 'DiverseSelector_struct._compute_grouped_knn_score_ivf', 'DiverseSelector_struct._select_local_simple', 'DiverseSelector_struct._select_structure_cluster_greedy', 'DiverseSelector_struct._save_pca_outputs']
- called_by: []
- location: Process_AL_PCA\process_pool.py:167

### DiverseSelector_struct._fit_scaler_pca
- type: method
- purpose: unknown
- inputs: ['x_pool', 'x_train']
- outputs: ['unknown']
- calls: ['RobustScaler', 'fit', 'PCA', 'vstack', 'transform']
- called_by: ['DiverseSelector_struct.select']
- location: Process_AL_PCA\process_pool.py:310

### DiverseSelector_struct._build_local_df
- type: method
- purpose: unknown
- inputs: ['df', 'coords', 'split', 'group_col', 'struct_col']
- outputs: ['unknown']
- calls: []
- called_by: ['DiverseSelector_struct.select']
- location: Process_AL_PCA\process_pool.py:379

### DiverseSelector_struct._maybe_to_gpu
- type: method
- purpose: unknown
- inputs: ['index']
- outputs: ['unknown']
- calls: ['StandardGpuResources', 'index_cpu_to_gpu']
- called_by: ['DiverseSelector_struct._compute_knn_score_ivf']
- location: Process_AL_PCA\process_pool.py:404

### DiverseSelector_struct._sample_train_for_ivf
- type: method
- purpose: unknown
- inputs: ['ref_coords']
- outputs: ['unknown']
- calls: []
- called_by: ['DiverseSelector_struct._compute_knn_score_ivf']
- location: Process_AL_PCA\process_pool.py:417

### DiverseSelector_struct._compute_knn_score_ivf
- type: method
- purpose: Approximate mean squared L2 distance to k nearest refs using IndexIVFFlat.
- inputs: ['query_coords', 'ref_coords', 'k']
- outputs: ['unknown']
- calls: ['ascontiguousarray', 'IndexFlatL2', 'IndexIVFFlat', 'DiverseSelector_struct._sample_train_for_ivf', 'train', 'DiverseSelector_struct._maybe_to_gpu', 'empty', 'search']
- called_by: ['DiverseSelector_struct.select', 'DiverseSelector_struct._compute_grouped_knn_score_ivf']
- location: Process_AL_PCA\process_pool.py:431

### DiverseSelector_struct._compute_grouped_knn_score_ivf
- type: method
- purpose: pool group g only compares with train group g.
- inputs: ['df_pool', 'df_train', 'coords_pool', 'coords_train', 'group_col', 'k']
- outputs: ['unknown']
- calls: ['DiverseSelector_struct._compute_knn_score_ivf']
- called_by: ['DiverseSelector_struct.select']
- location: Process_AL_PCA\process_pool.py:492

### DiverseSelector_struct._cluster_pool_locals
- type: method
- purpose: Cluster pool local PCA coords using FAISS Kmeans.
- inputs: ['coords_pool']
- outputs: ['unknown']
- calls: ['ascontiguousarray', 'Kmeans', 'train']
- called_by: ['DiverseSelector_struct.select']
- location: Process_AL_PCA\process_pool.py:543

### DiverseSelector_struct._minmax_norm
- type: method
- purpose: unknown
- inputs: ['x']
- outputs: ['unknown']
- calls: ['asarray', 'zeros_like']
- called_by: ['DiverseSelector_struct._select_structure_cluster_greedy']
- location: Process_AL_PCA\process_pool.py:581

### DiverseSelector_struct._select_local_simple
- type: method
- purpose: If struct_col is None, simply select top local rows by novelty.
- inputs: ['local_pool_df', 'select_n']
- outputs: ['unknown']
- calls: ['sort_values']
- called_by: ['DiverseSelector_struct.select']
- location: Process_AL_PCA\process_pool.py:601

### DiverseSelector_struct._select_structure_cluster_greedy
- type: method
- purpose: Structure mode with cluster coverage greedy.
- inputs: ['local_pool_df', 'struct_col', 'select_n']
- outputs: ['unknown']
- calls: ['asarray', 'DiverseSelector_struct._minmax_norm', 'empty', 'sort_values']
- called_by: ['DiverseSelector_struct.select']
- location: Process_AL_PCA\process_pool.py:624

### DiverseSelector_struct._save_pca_outputs
- type: method
- purpose: unknown
- inputs: ['scaler', 'pca', 'local_pool_df', 'local_train_df']
- outputs: ['unknown']
- calls: ['concat', 'to_json', 'dump']
- called_by: ['DiverseSelector_struct.select']
- location: Process_AL_PCA\process_pool.py:791

### sample_traj_xyz
- type: function
- purpose: unknown
- inputs: ['input_file', 'n_frames', 'include_e', 'include_f', 'include_s']
- outputs: ['unknown']
- calls: ['AseAtomsAdaptor', 'get_structure', 'get_potential_energy', 'get_forces', 'get_stress']
- called_by: []
- location: Process_AL_PCA\process_pool.py:855

## Classes

### DiverseSelector_struct
- methods: ['__init__', '_validate_config', '_check_columns', 'select', '_fit_scaler_pca', '_build_local_df', '_maybe_to_gpu', '_sample_train_for_ivf', '_compute_knn_score_ivf', '_compute_grouped_knn_score_ivf', '_cluster_pool_locals', '_minmax_norm', '_select_local_simple', '_select_structure_cluster_greedy', '_save_pca_outputs']

## Entry Points

- DiverseSelector_struct.__init__, DiverseSelector_struct.select

## Call Graph Summary

子库 **Process_AL_PCA** 包含 **16** 个函数/方法，**1** 个类。

核心执行链路（从入口到关键逻辑）：
- DiverseSelector_struct.select → `DiverseSelector_struct._check_columns, DiverseSelector_struct._fit_scaler_pca, DiverseSelector_struct._build_local_df, DiverseSelector_struct._cluster_pool_locals, DiverseSelector_struct._compute_knn_score_ivf`
- DiverseSelector_struct._compute_knn_score_ivf → `ascontiguousarray, IndexFlatL2, IndexIVFFlat, DiverseSelector_struct._sample_train_for_ivf, train`
- DiverseSelector_struct._fit_scaler_pca → `RobustScaler, fit, PCA, vstack, transform`
- sample_traj_xyz → `AseAtomsAdaptor, get_structure, get_potential_energy, get_forces, get_stress`
- DiverseSelector_struct._select_structure_cluster_greedy → `asarray, DiverseSelector_struct._minmax_norm, empty, sort_values`
- DiverseSelector_struct._cluster_pool_locals → `ascontiguousarray, Kmeans, train`

## Notes

- 本分析基于 AST 静态分析，仅检测文件内直接函数调用。
- 动态调用（self.xxx、getattr、字典分发等）无法追踪。
- 外部库函数（chgnet、pymatgen、torch、ase 等）未纳入调用链。
- 不确定性信息均标注为 unknown。