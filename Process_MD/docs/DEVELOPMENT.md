# 开发进度与验证

## 本轮范围

先检查环境与旧库，建立可安装骨架，并直接接通已有能力。第一版采用按职责的目录和稳定顶层 API；不实现外部工作流，不重新编写成熟算法。

## 已完成

- [x] pyproject、公共导出、参数与结果 dataclass。
- [x] ASE 结构读取、目标下限/整数矩阵超胞、PBC 与原始索引保留。
- [x] CHGNet 工厂直接调用 Process_MLIP，不复制加载逻辑。
- [x] MDRunner 复用旧 NHC NVT，支持平衡/生产和轨迹间隔，记录状态与异常。
- [x] 复用原 export_msd / fit_msd 文件接口及诊断。
- [x] 独立的 D 维度/单位换算；JSON/CSV 与拒绝覆盖。
- [x] md / analysis / io 分类，unit / integration 测试分类。
- [x] 人可读 README、Codex 导航 AGENTS.md、临时目录验证工具。
- [x] SOC 组成记录、现成 wrapped 重建、结构化 MSD/D/sigma_NE、骨架数值和运行/比较诊断。
- [x] 在原库增加同积分器分块与回调；本库时间适配、正常停止和旧调用兼容。

## 接下来的顺序

1. 按实际材料校准参考结构、配位 cutoff 和拟合窗口；继续完善有效采样诊断，已有kinisi不确定度与具体审查规则保持分离。
2. 按需求把现有临时 CSV 适配优化为原库内存结果 API；原文件接口保持兼容。
3. 通用 SOC/空位构型生成、集体相关导率与多温度外推另行明确数据与适用条件。
4. 在 Process_MLIP 增加完整 checkpoint/resume，旧接口兼容；本库调用并进行连续/恢复对比测试。
5. 外部 MD_Screening_Workflow 已接通粗筛、联合骨架告警和无跳跃平台早停；自动扩胞/升降温/任务调度后续补充，本库不加入控制规则。

当前不承诺严格 restart、自动控制、统计收敛或真实 MLIP-MD 性质；模块返回数值证据，不自动替调用方作审查决策。

## 验证方法

默认环境 py1。项目根目录：

```text
python tools/verify.py
python tools/verify.py --package
```

工具用最小合成数据，运行结束清理临时目录；--package 只复制必要源码，离线构建 wheel，在临时 --target 安装并检查导入/示例，不修改 py1 中已安装的包。打包检查需要环境中已有 pip/setuptools。

单元测试不依赖旧库；集成测试需要 Process_MLIP，分析集成另需 pymatgen-analysis-diffusion，缺少时会明确跳过。跳过不算完成该能力验证。

## 已有证据与待确认项

- 环境：Python 3.12.6，NumPy 1.26.4，ASE 3.25.0，pytest 9.1.1，CHGNet 0.4.0，PyTorch 2.9.1，pymatgen-analysis-diffusion 2024.7.15。
- 重组前：79 项测试通过；包含真实旧库调用的短 ASE LJ MD、平衡/生产动量与时间、原 MSD→拟合链、失败记录、输出保护。
- 两项边界问题已修正并有回归：部分 PBC 混合晶格向量被拒绝；UTF-8 编码失败不会清空已有文件。五项回归曾失败，修复后全套通过。
- 基础目录重组阶段曾通过 79 项检查；模块补齐后的最终检查为 `py1 -B tools/verify.py --package` → exit 0，154 passed，wheel 构建、临时安装、导入和两个示例通过。
- 原库单阶段/控制器/计时/多阶段兼容性检查共运行 29 项，28 通过，1 项因当前 ASE 缺少 full MTKNPT 跳过。测试临时目录重定向到本项目管理的 TemporaryDirectory，未改科学断言。
- 连续与分块推进的最终坐标/动量逐元素完全一致；回调可读取同步后的轨迹，正常停止记录实际步数。分段终点不对齐采样间隔现会提前拒绝，两个相关回归先失败、修正后通过。
- 验证 TemporaryDirectory 已移除；目录扫描未发现 __pycache__、pytest cache、egg-info、build/dist 或本次临时副本残留。
- 本轮对 E:/Py-Code/Process_MLIP/md.py 新增可选 segment_steps/on_segment，默认调用行为不变；静态 API.md 和 docs/project_catalog.json 已按原规范更新。未修改模型或正式计算数据。可审阅的补丁保留在 tools/patches/。
- 未验证真实模型权重预测、GPU、长 MD、尺寸/时间收敛、严格 restart，以及完整 Python/依赖版本矩阵。

## MACE-OMat 与 kinisi 增量（2026-10-21）

- 新增 lazy MACE 委托工厂，完整保留原工厂 head/dtype/加速选项；未改原 Process_MLIP 或模型文件。
- estimate_hop_distance 通过ASE邻居表返回最近占据的同种移动离子间距（Å），含周期自身像；只是几何代理，阈值与决策归workflow。
- uncertainty.py 使用kinisi2.1原生ASE解析及Bayesian推断，返回独立后验D/σ_NE中位数、区间、窗口、种子和诊断；不重写unwrap/MSD/MCMC。
- py1运行 `tools/verify.py --package`：**193 passed, 1 skipped**（py1未安装kinisi，原生集成按依赖跳过）；wheel构建、临时安装及两个示例通过。
- 另在已有py-mace的NumPy2环境，用TemporaryDirectory的target依赖执行kinisi真实最小分析，未修改现有环境：kinisi2.1.0、scipp25.12.0、emcee3.1.6、dynesty2.1.5、statsmodels0.14.6。181帧×20原子（12Li随机游走+8O），320个后验样本；95%区间、NE中位/上下界转换与RNG恢复断言通过。D中位7.46436e-6 cm²/s、区间[5.03148e-6,9.79950e-6]仅为合成接口检查，不是材料结论。
- 默认workflow MACE-OMat加载器在py-mace读取现有本地权重，对8原子LiF执行一次能量/力调用，数值有限；未运行长MD或GPU。
- 所有上述验证临时目录已清理。MCMC收敛、真实材料性质、结构/时间/尺寸收敛和严格restart仍未验证。

## GEMDAT 与窗口骨架证据（2026-10-21）

- jumps.py新增原生GEMDAT位点/驻留事件接口、PBC重建核对、算术框架漂移、覆盖率与unknown。默认首帧占据位点，允许完整空位位点结构；缺失映射不解释成零事件。
- 原生GEMDAT1.8.1在outer位点状态恒定时存在空事件vstack错误；仅该精确异常下，复用原生位点分配、确认outer状态恒定，再构造原生空Transitions并调用Jumps。inner区域边界振动允许变化，不复制识别算法，不吞其他异常。
- validate_framework保留旧默认，增加可选早晚窗口各最多5帧ASE RDF平均及所选帧索引；数值与自动判断分离。
- py1最终完整 `tools/verify.py --package`：222 passed、12因可选GEMDAT/kinisi缺失而跳过；wheel、临时安装、导入和两个示例通过。
- 另用py1基底的TemporaryDirectory --target最小依赖最终验证24单元+11原生集成全部通过：GEMDAT1.8.1、MDAnalysis2.11.0、NumPy1.26.4、ASE3.25.0。静态、inner边界振动、驻留过滤、PBC、漂移、缺位点与别名检查覆盖。再次独立运行workflow原生接线测试1 passed：GEMDAT零跳跃→pymatgen MSD/WLS→生产10ps平台停止（301帧6原子静态数据）。
- 临时依赖及轨迹在子进程退出后清理；py1依旧未安装GEMDAT/kinisi，未升级NumPy。完整GEMDAT依赖解析可能拉kinisi/NumPy≥2，建议兼容环境安装。kinisi代码本轮未变，既有原生验证见上一节。
- 仅验证接口与合成数据；未跑真实材料长MD、未校准结构/平台经验阈值、未证明熔化/长期稳定或MCMC收敛。

## 兼容环境与真实短MD（2026-10-22）

- 相邻MD_Screening_Workflow的`.venv`只读复用py-mace，补齐GEMDAT1.8.1、kinisi2.1.0和NumPy2兼容的pymatgen-analysis-diffusion2025.11.15。py1与py-mace安装清单前后分别498、184条，指纹一致；未升级基础环境。环境重建和已有可选包告警见workflow的environment/README.md。
- `validate_framework`增加可选`rdf_repeat`，仅重复RDF快照的周期像，不改变MD、骨架MSD或配位；默认(1,1,1)。小LiF晶胞因此可低成本获得RDF近邻峰，周期像不增加独立样本。
- 新运行环境最终`tools/verify.py --package`：246 passed，无跳过；py1复核234 passed、12项可选依赖跳过。wheel构建、临时安装、导入和示例通过；验证工具采用短TemporaryDirectory避免Windows构建路径过长，退出后清理。
- 实际本地MACE-OMat/CPU/800 K/8原子LiF完成1900步、1.9 ps，耗时471.3秒。四个检查点结构无联合失稳告警；原生GEMDAT返回0跳跃、100%覆盖率。平台变化0.22516未低于0.2，因此按测试预算结束，没有强行触发升温建议或输出可信D/σ。
- 只保留workflow中一份`runs/mace_omat_smoke`真实结果及专用环境。该短测验证接线和预算停止；正式5 ps初检、10 ps生产检查与200 ps生产上限不变。长MD、材料性质、阈值校准、GPU及严格restart仍未验证。
