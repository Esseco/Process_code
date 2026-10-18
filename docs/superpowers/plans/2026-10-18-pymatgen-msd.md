# pymatgen 多时间起点 MSD 实施计划

目标：export_msd 仅使用 pymatgen-analysis-diffusion 的 DiffusionAnalyzer，保留已有调用、CSV 列及 fit_msd 调用。
执行：主代理直接按 executing-plans 实施；用户已授权，不另开分支、不提交、不修改环境。

- [x] 替换 msd.py：延迟导入 DiffusionAnalyzer，固定 smoothed="max"；开放 min_obs=30；每个分段/元素独立统计。保留 unwrapped 坐标、可选 MIC 展开及显式框架质量加权漂移修正。传入已处理的选中原子和零位移参考位点，禁用后端额外漂移。只使用 MSD，不采用后端隐式拟合。
- [x] 时间与输出：等间隔数据；报告中的末尾短帧以警告明确排除，其余不规则时间报错。CSV 列名/单位不变，time 是 lag，frame_index 是段首+lag帧数。沿用默认拒绝覆盖与分段检查；原 ASE MSD 实现删除，无回退。数据不足时在写输出前清楚报错。
- [x] 示例/文档：MSD.md、README、调用图及两个主要示例；说明约 1 ps 起始间隔、约 200 个 lag、min_obs 与分段作用。更新 fit 示例预检查的时间语义，保留 CSV 后续拟合。
- [x] 验证：py1 已装 pymatgen-analysis-diffusion 2024.7.15；手工枚举所有位移对与真实后端交叉验证，覆盖非匀速、归一化、框架/多元素/纯元素、PBC、尾帧、输出保护和缺依赖；示例调用测试与完整回归。运行静态 API 索引，记录验证范围。

注意：不再保证每帧一行或零时刻一行，这是原生 max 取样语义变化；不把重叠时间起点当独立样本。短轨迹不得悄悄回退单起点。保留源轨迹和已有 CSV。

验证记录：py1 全套 102 项 OK（原有 full MTK 缺失跳过 1 项），独立示例与真实零力 MD/批任务衔接通过；静态索引 15 项目/594 符号；--preview 与 whitespace 检查通过。自查了漂移不重复扣除、末帧等间隔、原子数归一化、CSV 索引语义和拟合 lag 范围。没有模型环境改动或超算实测。
