# 验证与已知问题

空间容量候选定义已按用户要求修正为先由 CCNB 截止半径筛选贯通通道，再从 `structure.net` 中 1D/2D/3D 分量选取位点；孤立间隙和 0D 分量不计入，无贯通通道返回 0。保留单次贪心和 2 Å 周期间距；本次仅改代码与静态索引，未运行计算验证。

位点容量随后按用户粗筛需求改为按自由半径排序的一次贪心筛选，取消多起点和完整距离矩阵，保持周期最小间距条件。未运行计算或性能测试，无法给出实测提速倍数；位点数可能低于原多起点结果。

2026-10-01：新增 `Process_Struct.estimate_spatial_capacity`，默认 CCNB 间隙自由半径 0.8 Å、所选离子位点间距至少 2 Å，确定性贪心装载数换算为 mAh/g。用户要求只改代码，因此未执行计算或新增测试；其最大装载数未获全局最优证明，详见 Process_Struct/SPATIAL_CAPACITY.md。

文档索引通过 AST 静态解析，未导入全部项目，不表示所有模块可运行。原项目目录、公开接口、模型及计算结果保持原位。

检查入口：

- py1：`python -m unittest Process_Vasp.tests.test_dos Process_Vasp.tests.test_excitation Process_Vasp.tests.test_layout`。
- atomate2：`python -m unittest Process_Vasp.tests.test_atomate_directories`。
- 文档索引：`python tools/project_catalog.py`。
- 配置预览：`python templates/run_task.py templates/configs/vasp_dos.json`。

VASP 测试使用模拟数据验证处理逻辑，尚未执行真实 VASP/集群任务。模板能力以已适配 recipe 为准。

2026-10-01：Process_Vasp 按 inputs/results/structures/workflows 归档实现，templates/docs/tests 分离。py1 的 8 个测试、atomate2 的 1 个测试通过；覆盖 DOS/压缩输出、激发态准备、旧模块与新模块对象一致性、模板路径、独立运行器复制和模拟断点恢复。首次沙箱执行因临时目录权限失败，随后用正常文件权限重跑通过；遗留临时目录保留原位。实际 VASP、POTCAR 生成和集群提交未验证。

已知问题：

- Process_Chgnet 部分模块引用已不存在的 Process_VaspOut。correct_energy/get_Na_coord/get_lo_content 需确认语义与单位再迁移。
- Magmom_Function/io/__init__.py 引用旧 Process_VaspInput，且相对导入越界。
- Example/DFT/Dos_csv.py 使用旧 export_dos_to_csv 和固定服务器路径，优先使用新 DOS 配置模板。
- Ehull_test 与 Loss_Phase/Loss_hull 的同名训练实现未自动合并。
- 一些原函数缺少输入/返回说明，API.md 标注缺失，不凭函数名编造科学语义。
- Process_Vasp 中此前 tmp* 测试目录存在权限问题，本次索引忽略临时目录，不删除内容。

未对全部模型训练、MC 采样、FAISS、通道批量任务、GUI 和历史示例运行测试。执行前先用小样本检查环境、模型、单位、随机种子及收敛条件。

Process_Struct/examples/percolation_sites.py 在已有 ccnb 环境对 NaFeF3 单结构实运行：0.5 Å 探针下 3D 连通，34 个间隙记录、96 条有向周期连接、48 个瓶颈标记；核对标记 CIF 回读与完整连接 CSV。1.0 Å 下无贯通通道，核对空位点表与框架 CIF。没有验证全数据集、空迁移元素分支的 NET 格式或实际迁移能垒。

2026-10-08：新增 Process_Vasp.run_amset_crt 和配置入口，调用 AMSET CRT 后处理，导出 σ/τ 张量并按输入内容/参数恢复已完成结果。仅更新实现及静态索引；未运行测试、真实 AMSET 或 VASP。已有 atomate2 环境未发现 AMSET 安装，未安装依赖。有效质量仅记录独立 AMSET 命令，未封装。

2026-10-08：新增 AMSET 超算独立任务生成和 DOS 检查点读取，质量采用官方 effmass.py 的输运定义从同次 CRT 结果导出，并输出固定 τ 下迁移率及 μ/τ。仅生成任务并更新静态索引；未运行测试、真实 AMSET 或超算提交。服务器 AMSET 安装、CPU 分区、原 DOS 网格收敛尚未验证。

2026-10-08：Process_Vasp 新增统一已完成结果解析 get_completed_result、后续任务生成 generate_followup_task、公开 run_workflow 续跑入口；原运行器支持 previous_result 配置，仅执行需要的新阶段，AMSET 也复用统一解析入口。更新静态索引；未运行测试、VASP/AMSET 或集群提交。服务器源结果在执行时验证，生成时不访问超算。

2026-10-09：加入 continue_task + 单 JSON 统一任务生成；服务器解析完成阶段及参数变更，执行 suffix 并保持原接口。AMSET 缺 DOS 时须显式 allow_vasp 和合适提交资源。仅代码/索引更新，未运行测试或真实计算。
