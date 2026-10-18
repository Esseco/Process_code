# Process_MLIP 调用关系

此文件维护核心模块关系；完整签名以 API.md 的静态索引为准。

```text
model_config ──> create_mlip_calculator ──> 各模型的官方 ASE calculator
                       ↑
run_mlip_md ──> 参数/结构/输出预检查（_md_support）
    ├── 可选 _run_pre_relax ──> MLIPRelaxer ──> ASE 优化器 / FrechetCellFilter
    └── 各阶段 run_md ──> ASE NHC/MTK 积分、轨迹、日志、steps/s

relax_structure_mace / relax_structure_sevennet
    └── _relaxation._relax_structure ──> MLIPRelaxer（保持旧接口默认值）

export_msd ──> pymatgen DiffusionAnalyzer (max 多时间起点平均) ──> MSD CSV
fit_msd ──> MSD CSV 手动区间 ──> pymatgen 默认加权拟合 / 自设电荷 Nernst–Einstein 导率
export_traj_frames ──> ASE Trajectory / write ──> 结构文件
```

- `__init__.py` 集中导出公开 API，不加载模型。
- `_md_support.py` 是内部共享工具，不依赖流程编排模块。
- `MLIPRelaxer` 是唯一 ASE 结构优化实现，原子/晶胞优化由参数选择。
- `tests/_support.py` 只服务测试；运行库不导入 tests/ 或 examples/。
- `Process_AL_MC.relax_structure_mace` 保留兼容导出，MC/委员会计算仍归原项目。
