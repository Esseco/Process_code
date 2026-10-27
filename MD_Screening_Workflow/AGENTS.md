# 开发入口

默认 `py1`。先读 README.md，再读 `md_screening/config.py`、`review.py`、`workflow.py`；方案/验证记录在 docs/。

- 本仓库负责 workflow。通用结构、积分、unwrap、MSD、拟合和骨架分析调用 Process_MD，后者复用 Process_MLIP/ASE/pymatgen。不要复制算法或通过机器路径修改 sys.path。
- run_md/screening_preset 使用调用者提供的超胞，target_atoms=None，不自动扩胞；满位点参考须与超胞匹配。旧 ScreeningConfig 默认 200 保持兼容。
- 默认前 5 ps 预检查、之后每 10 ps 累计生产检查、生产预算 200 ps；积分步长2 fs、每20 fs保存一帧。全程保持同一积分器；使用整数步调度，边界对齐保存帧。
- 默认MACE-OMat、CUDA，本地model_path或PROCESS_MD_MACE_MODEL；保留注入calculator，不下载/替换权重。Symmetrix通过enable_symmetrix和symmetrix_use_kokkos显式开启，CuEq与Symmetrix互斥。py1默认开发测试。真实MACE/GEMDAT/kinisi使用本仓库.venv，两个项目editable安装；只读借用py-mace模型栈，不升级py1/py-mace。先看environment/README.md及tools/check_runtime.py。
- 用户确认默认粗筛：生产>=10ps、MSD>3d²、R²>0.95，d为满位点参考中最近同种移动位点间距代理（ASE含PBC），支持手动覆盖。通过一次即heuristic_ready；不加alpha、D变化率/连续检查/CI宽度的隐藏门槛。
- stop_criteria=None且无reviewer为记录模式；自定义reviewer优先，不因默认结构告警提前跳过其生产分析。预算结束不写成低导率或可信D=0。
- kinisi不确定性为独立可选功能，uncertainty_on_stop默认关闭；显式启用只在通过后算一次，不影响粗筛判据。后验与WLS估计分别报告，保留漂移参考差异/MCMC未检查等限制。
- 用户最终确认生产>=10ps无有效跳跃且MSD平台早停，建议升温但不执行。GEMDAT内位点/驻留过滤，默认0.2ps；unknown/缺位点不当作零。少量跳跃不足继续至生产200ps；平台/覆盖等参数见stopping.py。
- 骨架检查用最近5/10ps窗口，MSD大+后半段持续增长+窗口平均RDF差三者联合；不称为确定熔化。默认自动审查失稳优先拒绝并省去后续分析；阈值可调。每次RDF最多前后各5帧，不加复杂序参量。
- 必须提供满位点reference_sites，含当前SOC空缺的位置，晶胞和原点与输入一致；两者使用同一扩胞矩阵。GEMDAT仅使用显式参考，d默认取参考的同种移动位点最近邻距离；记录reference_nearest_neighbor_A。缺失参考在写输出前报错，不回退到首帧或密度找位点。模型/晶胞/温度调整只记录并停止。
- framework_rdf_repeat仅对ASE RDF快照复制周期像，默认(1,1,1)，不增加MD规模或独立采样。mace_smoke例程用8原子LiF、0.1+最多1.8ps压缩窗口测试接线，不改变正式默认，也不是可信D/导率计算。已有真实结果在runs/mace_omat_smoke，不为一般验证重复跑。
- SOC 构型由外部输入，标签不等于生成 SOC；sigma_NE 不能称为集体电导率。
- 严格 restart 未实现。保留真实轨迹/动量不足以证明完整积分器恢复；不提供末帧伪恢复。
- 不自动安装/下载/更换模型，保留模型 head/dtype/能量基准。导入库不能加载 torch 或旧库。
- 运行 `python tools/verify.py`；涉及打包/导入时加 `--package`。测试用最小合成数据、短 LJ 和 TemporaryDirectory，结束后核对清理。不要跑真实长 MD 验证普通代码。
- 例程输出默认归 runs/；交付说明实际验证及未验证项，不自动推送或发布。

- 直接入口默认 compress_trajectory=True，旧 ScreeningConfig 默认 False。仅在连续 MD、分析、末结构导出成功后 gzip level 6 流式归档主轨迹，解压 SHA-256/大小校验并同步所有结果路径后删除原文件；失败保留原轨迹并记警告，不更改计算状态。归档后先解压再单独分析；不要在中途检查压缩活动轨迹。
