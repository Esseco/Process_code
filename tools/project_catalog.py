"""Rebuild source-grounded project documentation without importing projects."""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = {
    "Process_Vasp": ("VASP 输入、结果与可恢复 atomate2 工作流", "工具包", "结构文件 / VASP 计算目录", "VASP 输入、计算检查点、结果 dict、DOS DataFrame/CSV", "pymatgen, numpy, pandas, monty；工作流运行使用 atomate2 环境；CRT 后处理需要 AMSET", "实现按 inputs/results/structures/workflows 分目录；优先使用 input.py/output.py 的公开入口，旧模块导入兼容；计算输出可能压缩。", ["generate_atomate_input", "read_dos", "generate_excited_input", "read_vasp_output", "read_vasp_status", "run_amset_crt", "run_amset_postprocess", "generate_amset_task", "get_completed_result", "generate_followup_task", "run_workflow", "continue_task"]),
    "Process_Struct": ("通用结构特征、畸变、容量与连通性", "工具包", "pymatgen Structure、化学式或轨迹", "结构特征、容量、畸变及轨迹转换结果", "pymatgen, numpy, pandas, ASE；渗流/位点容量使用 ccnb；部分模块需要 octadist 等", "包使用延迟导入；不同功能的可选依赖分开检查。位点容量为间距约束下的贪心可行估计，不保证最大装载数。", ["theoretical_specific_capacity", "get_wyckoff_sites", "StructureFeatureExtractor", "Octahedron", "analyze_percolation", "estimate_spatial_capacity"]),
    "Process_LayeredOxide": ("层状氧化物相变、层特征、相图与电压", "工具包", "层状结构、组成与能量表", "变换结构、层特征、相图结果及电压", "pymatgen, numpy, pandas, scipy", "确认离子种类、层序和能量归一化；不要将默认 Na/TM 假设直接用于所有材料。", ["LayerOxide_O3_Transformer", "LayerOxidePhaseDiagram", "get_voltage", "get_layer_spacing", "row_factor"]),
    "Process_face": ("表面 slab 生成、固定原子与表面配置", "工具包", "体相 Structure、晶面与表面设置", "slab/POSCAR、约束及表面配置", "pymatgen, numpy, ASE", "部分构造器会建立输出目录；检查真空厚度、极性、对称性及固定层。", ["LOSlabProcessor", "SurfaceFixer", "get_symmetry_atom", "sym_surface_remove_atoms_single"]),
    "Process_MLIP": ("基于 ASE calculator 的通用结构弛豫", "工具包", "ASE Atoms 和 calculator", "弛豫结构、总能、每原子能、日志与轨迹", "ASE；模型 calculator 的依赖由调用者提供", "模型和设备显式传入；不能将优化器结束自动等同于达到收敛阈值。", ["MLIPRelaxer"]),
    "Process_AL_MC": ("层状氧化物 MC 排序与 MACE 弛豫", "工具包", "结构、模型路径、采样/弛豫配置", "采样池、轨迹、检查点、结构与预测结果", "ASE, pymatgen, numpy；运行模型时需要 MACE/torch", "检查随机种子、模型版本、设备与恢复配置；长任务使用独立输出目录。", ["LayeredOxide_MCOrderingClass", "relax_structure_mace", "extract_data_from_mcjson"]),
    "Process_AL_PCA": ("PCA/FAISS 结构多样性筛选", "工具包", "训练集和候选池的局域结构特征/轨迹", "筛选结构、距离/聚类及 PCA 相关结果", "faiss, scikit-learn, scipy, ASE, numpy, pandas", "faiss 是可选环境依赖；输入特征列和训练/候选分组必须明确。", ["DiverseSelector_struct", "sample_traj_xyz"]),
    "Process_Chgnet": ("CHGNet 数据转换、预测与弛豫", "历史工具包", "VASP 输出、CHGNet JSON、结构或轨迹", "训练数据 JSON、ASE 数据和模型结果", "chgnet, torch, pymatgen, ASE, numpy", "存在 Process_VaspOut 旧包名引用，当前不能假定包级导入可用；需逐项确认函数替代关系。", ["vasp_to_chgnetJson", "load_chgnet_json", "get_ase_from_json", "chgnet_relax"]),
    "Magmom_Function": ("磁矩读取、磁性检查与历史 INCAR 工具", "历史工具包", "OUTCAR 和磁性相关参数", "磁矩数组、检查结果及输入处理", "pymatgen, numpy；见具体源文件", "io/__init__.py 引用了旧 Process_VaspInput 且相对导入越界；包入口需修复后使用。", ["read_magnetic_moments_outcar", "check_magnetic_moments", "detect_converge"]),
    "Loss_Phase": ("CHGNet 凸包/相稳定性训练与数据处理", "训练实验", "结构、能量、训练标签和模型", "训练模型、损失与相稳定性相关数据", "chgnet, torch, pymatgen, numpy, pandas", "与 Ehull_test 存在同名训练文件；暂保留独立来源，不自动合并不同实验实现。", ["TrainerHull", "CombinedLossHull", "StructureDataHull", "correct_energy", "get_Ehull_from_com"]),
    "Ehull_test": ("凸包相关 CHGNet 数据集与训练器试验", "训练实验", "训练结构、能量/力/应力/磁矩及 hull 标签", "数据加载器、训练模型及损失", "chgnet, torch, pymatgen, numpy", "这是试验目录；使用前与 Loss_Phase/Loss_hull 对比实际差异。", ["StructureDataHull", "TrainerHull", "CombinedLossHull", "get_train_val_test_loader"]),
    "channel_codes_optimized": ("结构通道批处理与集群任务生成", "独立脚本", "结构目录、目标目录和批处理设置", "通道分析文件、CSV、ZIP 和 LSF 任务目录", "pymatgen, numpy, pandas, monty；见 worker 具体依赖", "Generate.py/1.py 包含集群路径与调度模板，需检查配置后再执行。", ["process_structure", "cal_channel", "get_pending", "split_groups"]),
    "octadist": ("OctaDist 八面体畸变分析与 GUI/CLI", "第三方代码", "配位结构/坐标文件", "八面体畸变参数和图形", "numpy, scipy, matplotlib, tkinter 等，按源码确认", "保留第三方命名与许可证信息；避免把 GUI 导入用作批量任务入口。", ["CalcDistortion", "calc_param", "run_cli", "extract_octa"]),
    "Process_folder": ("目录与表格辅助处理", "工具包", "目录路径、CSV 与列名", "目录及处理后的 DataFrame", "pandas；目录工具仅标准库", "表格替换逻辑可能改变符号字符串，先确认适用列，避免改变数值语义。", ["ensure_dir", "replace_hyphen"]),
    "Example": ("按主题归档的历史调用示例", "示例集", "各脚本规定的数据与路径", "按 DFT、Surface、MACE、LO_FeMn 等主题产生结果", "随所调用项目变化", "包含硬编码服务器路径和旧导入；先阅读再运行，优先改为 templates 配置入口。", []),
    "excel-diagnostics-20260930": ("Excel 诊断输出归档", "输出归档", "诊断工具产生的文件", "诊断记录", "无需作为 Python 包导入", "不是功能项目；保留文件，不纳入计算入口或自动执行。", []),
}


def collect(directory):
    records, errors = [], []
    for path in sorted(directory.rglob("*.py")):
        if any(part.startswith("tmp") or part in ("__pycache__", ".git") for part in path.parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        except (OSError, SyntaxError, UnicodeError) as error:
            errors.append({"path": path.relative_to(ROOT).as_posix(), "error": str(error)})
            continue
        imports = sorted({
            alias.name.split(".")[0] for node in ast.walk(tree)
            if isinstance(node, ast.Import) for alias in node.names
        } | {
            node.module.split(".")[0] for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module and node.level == 0
        })
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
                functions = [node]
                if isinstance(node, ast.ClassDef):
                    functions += [child for child in node.body if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and (not child.name.startswith("_") or child.name == "__init__")]
                for item in functions:
                    name = item.name if item is node else node.name + "." + item.name
                    signature = name + "(" + ast.unparse(item.args) + ")" if hasattr(item, "args") else name
                    records.append({"file": path.relative_to(ROOT).as_posix(), "name": name,
                                    "line": item.lineno, "signature": signature,
                                    "doc": ast.get_docstring(item) or "", "imports": imports})
    return records, errors


def main():
    catalog = []
    for project, metadata in PROJECTS.items():
        directory = ROOT / project
        if not directory.exists():
            continue
        purpose, kind, inputs, outputs, dependencies, caution, preferred = metadata
        records, errors = collect(directory)
        catalog.append({"project": project, "purpose": purpose, "kind": kind,
                        "inputs": inputs, "outputs": outputs, "dependencies": dependencies,
                        "caution": caution, "preferred": preferred, "symbols": records, "scan_errors": errors})
        text = f"# {project}\n\n{purpose}。类型：{kind}。\n\n"
        text += f"## 输入与输出\n\n- 输入：{inputs}。\n- 输出：{outputs}。\n- 依赖：{dependencies}。默认先使用 py1；缺依赖时检查现有专用环境，不自动安装或升级。\n\n"
        text += "## 功能入口\n\n| 文件 | 函数 / 类 | 用途 |\n|---|---|---|\n"
        entries = [r for r in records if "." not in r["name"] and r["name"] in preferred]
        if not entries:
            entries = [r for r in records if "." not in r["name"]][:12]
        for r in entries:
            file = Path(r["file"]).relative_to(project).as_posix()
            doc = (r["doc"].splitlines() or ["见源文件和参数索引"])[0].replace("|", "/")
            text += f"| [{file}]({file}) | `{r['name']}` | {doc} |\n"
        if not entries:
            text += "| — | 无可调用 Python 入口 | 保留输出归档 |\n"
        text += f"\n## 使用与模板\n\n1. 先查 [API 参数索引](API.md)，确认真实签名及返回约定。\n2. 用 [项目任务模板](TASK_TEMPLATE.md) 明确输入、输出、参数和验证。\n3. 通用可执行入口见 [templates](../templates/README.md)；未覆盖的项目按公开函数组合，不直接批量执行历史脚本。\n\n## 注意事项\n\n{caution}\n\n"
        if project == "Process_Vasp":
            text += "专题说明：[DOS](docs/DOS_USAGE.md)、[激发态](docs/EXCITATION_USAGE.md)、[断点续算](docs/ATOMATE_WORKFLOW_USAGE.md)。\n\n"
        if project == "Process_Struct":
            text += "化学容量子项目：[Chemical_Capacity_Constraints](Chemical_Capacity_Constraints/README.md)。\n\n"
        text += "## 验证状态\n\nAPI 索引来自源码静态解析，不表示模块导入或科学计算已验证。测试覆盖与已知问题见 [仓库验证说明](../docs/VALIDATION.md)。\n\n<!-- Generated by tools/project_catalog.py; edit PROJECTS metadata for lasting changes. -->\n"
        readme = directory / "README.md"
        if not readme.exists() or "<!-- Manual project documentation -->" not in readme.read_text(encoding="utf-8"):
            readme.write_text(text, encoding="utf-8")
        api = f"# {project} 参数索引\n\n源码静态索引；保留原有函数名。类构造和公开方法分别列出。默认值不代表适用于所有体系。\n\n"
        for r in records:
            file = Path(r["file"]).relative_to(project).as_posix()
            api += f"## `{r['name']}`\n\n源文件：[{file}]({file})，第 {r['line']} 行。\n\n```python\n{r['signature']}\n```\n\n"
            api += (r["doc"] or "原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。") + "\n\n"
        if errors:
            api += "## 扫描问题\n\n" + "\n".join(f"- {e['path']}: {e['error']}" for e in errors) + "\n"
        (directory / "API.md").write_text(api, encoding="utf-8")
        task = f"# {project} 任务模板\n\n复制到具体任务记录后填写，模板本身不启动计算。\n\n"
        task += f"- 目标：{purpose}中的哪项功能？\n- 类型：{kind}。\n- 输入：{inputs}；填写绝对路径、格式、数据量及前置检查。\n- 输出：{outputs}；填写独立目标目录与已有文件处理规则。\n- 入口：从 API.md 选择函数/类及确切签名。\n- 环境：py1 或已确认的专用环境；记录关键依赖版本。\n- 参数：逐项列出值、单位、默认值和材料适用条件。\n- 随机性：如适用，记录种子、模型和采样配置。\n- 副作用：记录会写哪些文件、是否启动模型/外部计算、是否需要 GPU。\n- 重复运行：说明覆盖、追加、跳过或断点恢复策略。\n- 验证：最小输入、预期输出、形状/单位/收敛检查；报告未验证项。\n- 已知限制：{caution}\n\n"
        task += "新功能优先采用 `run(input_path, output_dir=None, *, options...)` 或现有兼容接口，业务逻辑与 CLI 分开；不要为统一外观擅自改动现有参数名。\n"
        (directory / "TASK_TEMPLATE.md").write_text(task, encoding="utf-8")
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "project_catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    index = "# 项目导航\n\n| 项目 | 类型 | 功能 |\n|---|---|---|\n"
    index += "\n".join(f"| [{r['project']}](../{r['project']}/README.md) | {r['kind']} | {r['purpose']} |" for r in catalog)
    index += "\n\n机器可读索引：[project_catalog.json](project_catalog.json)。更新：`python tools/project_catalog.py`，只解析源文件，不导入业务包。\n"
    (docs / "PROJECTS.md").write_text(index, encoding="utf-8")
    print(f"Indexed {len(catalog)} projects, {sum(len(r['symbols']) for r in catalog)} symbols")


if __name__ == "__main__":
    main()
