# Process_MD 开发导航

默认使用 `py1`。先读 `README.md`，再按任务阅读：

- `docs/ARCHITECTURE.md`：目录职责、依赖、复用映射与科学边界。
- `docs/DEVELOPMENT.md`：已完成内容、后续顺序和验证记录。
- `docs/MODULES.md`：通用模块 API、可提供的审查证据和未实现边界。
- `process_md/__init__.py`：用户可导入的公共 API。

## 修改原则

- 本项目是基础库，不加入工作流、自动决策或调度。
- 先调用已有 `Process_MLIP`，再考虑新增。通用 MD/MSD 能力缺口优先补进原库；本项目只做参数/结果适配。不复制积分器、模型工厂、unwrap 或 MSD 算法。
- 保留原库公开接口、科学单位、模型 head/dtype/能量基准。模型与分析依赖延迟加载，不自动安装、下载或更换模型。
- 不硬编码 `Py-Code` 的机器路径，不在代码中修改 `sys.path`。调用旧功能前，环境应能 `import Process_MLIP`。
- 当前 `checkpoint_interval=None`；请求 checkpoint 或严格 resume 必须报错，直到完整状态协议和恢复测试实现。轨迹末帧不是严格 restart。
- 连续分段可用 segment_ps/on_segment，调用原库的同一积分器；回调只是通用原语，不加入自动审查阈值。扩展原库的补丁位于 tools/patches/，不要自动重复应用。
- 尽量保持顶层 `from process_md import ...` 稳定；内部按 md / analysis / io 分类。
- MACE/CHGNet工厂均委托原库，参数原样转发。estimate_hop_distance只提供最近占据位点距离代理，不加入workflow的3d²停止规则。
- kinisi适配在analysis/uncertainty.py，延迟加载可选依赖；不自己编写unwrap/MSD/Bayesian算法。后验D与σ_NE区间不当作WLS误差条；保留算术/质量加权漂移差异和MCMC未检验限制。不得为此直接升级py1的NumPy/模型环境。
- GEMDAT在analysis/jumps.py，使用原生解析/Transitions/Jumps；unknown计数None，输出覆盖率。1.8.1空事件兼容仅捕获特定异常且复核原生outer位点状态恒定（inner边界振动可变化），不吞其他异常。基础库不加入10ps/平台早停决策。RDF可选窗口平均最多5帧/侧，默认仍保留旧初末比较。
- rdf_repeat只对RDF复制ASE周期像，MSD/漂移/配位仍用原轨迹；默认(1,1,1)保持旧行为。实际MACE/GEMDAT/kinisi兼容环境在相邻workflow的.venv，勿改py1；已有8原子真实短MD结果，无需一般验证重复计算。

## 验证

在项目根目录运行 `python tools/verify.py`；涉及打包、导入或目录调整时运行 `python tools/verify.py --package`。

- `tests/unit/` 不要求旧库或模型；`tests/integration/` 使用已有 Process_MLIP、ASE LJ 和合成轨迹，缺依赖时会明确跳过。
- 不运行真实模型/长 MD 来验证一般接口修改；需要科学/性能验证时另行界定样本。
- 临时数据使用 TemporaryDirectory/finally，并核对清理；不复制正式项目、模型或大型历史状态。
- 交付说明实际运行的检查及未验证项；更新 `docs/DEVELOPMENT.md`，不把接口占位符描述为已实现。
