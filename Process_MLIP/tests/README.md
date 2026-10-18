# 回归测试

在仓库根目录运行，默认 py1，不安装模型依赖：

```bash
python -m unittest discover -s Process_MLIP/tests -t . -p "test_*.py"
python -m unittest Process_MLIP.tests.test_relax
```

原有从 `Process_MLIP` 根目录递归 discover 的命令也可使用；旧的单测试模块路径改为这里的模块名。

| 测试文件 | 覆盖范围 |
|---|---|
| test_calculators.py | 预设、四模型适配、CuEq/FlashTP/Symmetrix、旧导入和公开签名 |
| test_relax.py | 统一优化器、约束、收敛、晶胞稳定、预弛豫与模型复用 |
| test_md.py | NVT/NPT 积分、输出、随机种子、非法结构及失败处理 |
| test_md_controllers.py | 控制器选择、晶胞模式、链长度和积分子步数 |
| test_md_timing.py | 系综默认步长、显式覆盖、累计时间、steps/s 和 CUDA 同步边界 |
| test_md_workflow.py | 多阶段参数优先级、动量衔接、预检查与失败报告 |
| test_msd.py | pymatgen 多起点与手工位移对比较、归一化、周期展开、漂移、分段、短尾帧及缺依赖 |
| test_transport.py | pymatgen 默认加权、None/单端/手动区间、fs 单位、斜率下限、电荷及输出保护 |
| test_trajectory.py | 帧选择、文件格式、原子顺序、晶胞/动量及覆盖保护 |
| test_examples.py | MD/MSD/导率示例、八模型批任务、六组温度/时长扫描 |

`_support.py` 是共享夹具，不定义 TestCase；测试不再互相导入 TestCase。
`public_api.json` 保存 14 个公开签名；export_msd 新增 min_obs=30，fit_msd 两端时间默认 None，原手动区间调用兼容，拟合器用 pymatgen 原生默认值。
MSD 测试使用真实 pymatgen-analysis-diffusion（py1 已装），移除旧 ASE 单起点断言；示例用零力 calculator 跑足够长的合成时间序列，验证调用衔接，不用于物性或步长建议。

测试使用本地临时目录，结束后清理自己的输出；无需权重，不下载、不训练、不提交超算。
py1 缺少完整 MTKNPT 时仅跳过该项实测，仍验证参数传递与缺失实现报错。
真实模型精度、GPU/加速后端和长期 MD 收敛仍需在对应运行环境验证。
