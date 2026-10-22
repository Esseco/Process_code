# GEMDAT 跳跃与简洁结构检查实施计划

Goal：按用户确认的成本优先策略接入现成分析；基础库提供证据，workflow 组合停止规则。

已确认：前5 ps初检；生产每10 ps检查；生产>=10 ps，无有效跳跃且MSD平台时停止并建议升温；少量跳跃继续至最多200 ps。保留生产>=10 ps、MSD>3d²、R²>0.95的一次通过规则。暂不自动改变温度/晶胞/模型。

## 实施

- [x] Process_MD/analysis/jumps.py：延迟加载GEMDAT，调用原生Transitions/Jumps；返回事件、覆盖率和诊断。初始占据位点是默认参考，允许显式完整位点结构；映射不可靠不能解释成零跳跃。补最小原生与单元测试；不在py1升级NumPy。
- [x] Process_MD/analysis/framework.py：保留原API，增加可选少量时间窗RDF平均和骨架后段增长证据；无物理判决。ASE负责RDF，不重复算法。
- [x] workflow新增简短的检查配置与组合判据：结构失稳优先于传输通过；MSD增长+RDF显著变化联合触发，不单靠一个MSD阈值。数值异常沿用failed，标签为framework_unstable/疑似熔化而非测得熔点。
- [x] production调用GEMDAT；零跳跃+平台早停独立于D拟合是否成功；未知映射继续，不误判低导率。保留record-only、自定义reviewer优先、同一积分器、错误留档。kinisi保持可选，仅通过后计算一次，不每10ps做MCMC。
- [x] 更新公共导出、依赖extra、README/AGENTS/API说明、最小示例。运行py1两库全套及打包；临时target验证原生GEMDAT，kinisi本轮未改，沿用之前原生证据，不重复MCMC；产物清理。

## 验证重点

振动零跳跃、短暂跨界过滤、真实驻留跳跃、PBC、未占据位点/低覆盖不判零、生产切片、10ps边界、少量跳跃继续/200ps上限、结构联合判据/纯漂移/松弛平台、预检查拒绝与生产拒绝、无全局依赖修改。

## 关键取舍

- 不重写现有pymatgen MSD/WLS或kinisi贝叶斯算法；GEMDAT首先补齐跳跃识别。
- 自动结构规则是可调的保守粗筛；5ps未失稳不代表长期/热力学稳定。生产阶段复查。
- 不做熔点、复杂序参量、多温规划、自动SOC、严格restart或真实长MD验证。
- 用户已授权常规设计实施；原目录直接修改，不增加审批/强制worktree/逐任务提交。

## 进度与证据

最终py1：基础库222 passed/12 optional skips；workflow117 passed/1 optional skip；两库打包/临时安装/导入/短例程通过。临时原生GEMDAT35项（24单元+11原生）和workflow接线1项全部通过。原环境未改，临时目录清理。

取舍：保留已有pymatgen MSD/WLS与kinisi适配；不增加重复算法。结构默认1 Å²/每窗口增长0.2 Å²/RDF相对L1差0.5同时满足才报警，需材料校准。一次审查发现自定义模式短路问题，已修复并回归；另外补原生inner边界热振动的空事件兼容。无真实材料长MD、熔点或MCMC收敛验证。
