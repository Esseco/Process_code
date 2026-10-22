# MACE-OMat、粗筛停止和 kinisi 实施记录

历史阶段记录。无跳跃/骨架判据现已由2026-10-21-gemdat-screening.md及README中的最终规则更新。

**Goal:** 默认 MACE-OMat；用户确认的低成本停止条件；独立可选不确定性模块。
**Architecture:** Process_MD 放通用 MACE 工厂、ASE跳距代理、kinisi适配。workflow/stopping.py 只组合指标，保持基础库可独立调用。

## 最终范围

- 用户更正模型为 mace-omat，使用本地文件配置，不混用MH-1，不下载权重。
- 生产>=10 ps、拟合末端MSD>3d²、R²>0.95；d由初始同种移动离子最近邻间距估计（含周期自身像），可手动覆盖。用户已确认3×d²，不是固定3Å²。
- 通过一次就停，状态 heuristic_ready。取消此前草拟的30ps、alpha、连续多次、D一致性和可信区间宽度门槛，理由为用户明确成本优先。
- 生产上限维持200ps；低移动性提前结束规则尚未获明确阈值，不擅自增加。到上限 budget_exhausted，不把未解析视为D=0。
- kinisi独立函数可离线调用；uncertainty_on_stop默认False，显式启用时通过后仅算一次，不参与停止判据。依赖不可用在MD前报错。
- 默认py1开发验证不变；MACE在现有py-mace环境可用，尚需分析依赖。kinisi2.1需NumPy2，隔离验证不得修改已有环境。
- 保留自定义reviewer优先、record-only模式、错误留档。骨架自动判稳与严格restart仍不开发。

## 任务

- [x] MACE委托工厂与透传测试、跳距代理及周期边界测试。
- [x] 粗筛停止、MACE默认入口、可选kinisi报告连接和73/75项阶段回归。
- [x] kinisi公开API与边界/延迟导入测试；原生小样本隔离验证另记最终结果。
- [x] 最终整套/打包检查、README/AGENTS/架构同步、残留清理。

**最终证据：** py1基础库193 passed、1依赖跳过；workflow75 passed；两库wheel构建/临时安装、独立导入和例程通过。另在未修改的py-mace基底上用临时target依赖完成真实kinisi2.1后验/NE换算/RNG断言，320样本；默认MACE-OMat加载器对8原子完成有限能量/力调用。TemporaryDirectory均清理。未跑真实材料长MD/GPU，未检查MCMC收敛。

## 依据与边界

MACE模型选择：https://mace-docs.readthedocs.io/en/latest/guide/foundation_models.html
kinisi原生后验：https://kinisi.readthedocs.io/en/latest/analyze.html
He et al 2018：https://doi.org/10.1038/s41524-018-0074-y

最后一篇说明R²不代表统计方差；当前3d²/R²门槛是用户确认的粗筛启发式，不归因为文献规定。两种估计与区间分别报告，明确漂移参考差异；不为了未来扩展新增控制框架。
