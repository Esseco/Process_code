# Process_AL_MC

<!-- Manual project documentation -->

Na-TM-O 层状体系的模型弛豫与 MC 排序。默认先检查 py1，实际模型运行使用已有 MACE/CHGNet 环境。构造采样对象会加载模型、设置全局 Python/numpy 随机种子，提供 out_dir 时还会写配置。

## 独立功能

| 功能 | 入口 / mode | 输入 → 输出 | 模板 |
|---|---|---|---|
| 已有 TM 排序的交换采样 | LayeredOxide_MCOrderingClass / TM_MC_input | 含多种 TM 的结构、模型 → trace/pool/status | [tm_ordering.py](examples/tm_ordering.py) |
| Na/空位交换 | 同上 / Na_MC_input | 脱钠结构、满钠模板、模型 → 候选池 | [na_vacancy_ordering.py](examples/na_vacancy_ordering.py) |
| 采样轨迹查看 | pandas.read_json | trace.json → DataFrame | [read_trace.py](examples/read_trace.py) |
| 弛豫轨迹抽结构 | extract_data_from_mcjson | 兼容 trajectory JSON → POSCAR 和信息列表 | [extract_trajectory.py](examples/extract_trajectory.py) |
| 随机 TM 初始化 | TM_MC_random | tm_original_element、tm_ratios 等 | [API 参数](API.md) |
| 单结构/委员会弛豫 | Relax / relax_structure_mace | 结构、模型 → 弛豫报告 | [MLIP 模板](../Process_MLIP/examples/mace_relax.py) |

编辑各模板顶部参数，从根目录运行 `python -m Process_AL_MC.examples.tm_ordering` 等。模板导入不加载模型，新任务拒绝已有输出目录。此处直接使用模块入口，不改包级导出。

## 采样与模型约定

主模型负责每个候选结构的弛豫，委员会全部模型评估弛豫结果；接受率使用委员会平均每原子能量。单模型的不确定性指标不能视为可靠误差估计。模型必须具有一致的元素、单位与能量基准。

seed 设置 Python/numpy 随机性，但不保证 GPU/模型完全确定性。temperature 单位 K，fmax 是 eV/Å；接受率采用每原子能量尺度，若用于物理有限温度统计需核对其与总能量 Metropolis 的差异，不能直接解释为严格平衡采样。

Na_MC_input 需要匹配的满钠位点模板；无有效 Na/Vac 交换时会直接弛豫。TM_MC_random 需要目标元素和比例；不等同于对任意材料的通用随机替换。

## 文件与恢复限制

保存 settings.json、trace.json、status.json、pool/ 和可选弛豫轨迹。MC 通常返回 None，应从文件读取结果；Relax 返回结构、委员会评估和轨迹三元组。

现有 _save_checkpoint 保存状态摘要和池，但没有 checkpoint 加载入口，缺少可恢复的完整 RNG/visited/current 等状态；本项目目前不支持精确断点续采样。重新调用 run 会开始新循环，不要对旧目录假装续算。可用已保存结构开始新的采样，但必须记录这是新任务。

Auc_code 导出器依赖 JSON 字段、目录层级和文件名（下划线拆分），不能直接接收 trace.json/pool_summary.json。轨迹模板预先检查格式，批量导出仍需检查名称冲突。

## 验证与边界

四个模板已安全导入，采样模板不会在导入时构造对象或加载模型。未运行模型或 MC 长采样。功能合并建议见 [BOUNDARIES.md](BOUNDARIES.md)，签名见 [API.md](API.md)。
