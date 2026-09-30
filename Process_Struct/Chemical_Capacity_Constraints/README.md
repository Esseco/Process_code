# 化学容量约束 / Chemical Capacity Constraints

本模块位于 Process_Struct/Chemical_Capacity_Constraints，提供形式价态电荷平衡、Li/Na 含量窗口、红氧容量粗筛和多阴离子分组。它与 Process_Struct.Cal_capacity.theoretical_specific_capacity 并存：原函数按给定移动离子数直接换算容量；本模块根据价态窗口估算化学上限。

从 Py-Code 根目录或 Notebook 导入：

    from Process_Struct.Chemical_Capacity_Constraints import (
        estimate_mobile_ion_window,
        estimate_redox_capacity,
    )


这一目录提供正极材料筛选中的电荷补偿与理论可逆容量上限模块。价态规则是文献启发的粗筛先验，适合先排除明显缺少氧化还原容量的候选；不能把它当成 DFT 相稳定性、工作电压或循环可逆性的预测。

## 当前范围

- 阴离子环境：氧化物、氧卤化物、卤化物、硫化物、多阴离子，以及由自由阴离子和多阴离子共存构成的混合阴离子。
- 价态：以常见正极中的 Ti/V/Cr/Mn/Fe/Co/Ni/Cu/Nb/Mo/W 等为主；给出稀有或成本敏感元素的可选范围。
- 电荷中性：枚举允许价态组合，筛出形式电荷和为零的解。
- Qredox：默认只计阳离子氧化还原；按初始化学式中的可迁移碱金属库存封顶。
- 单位：输出电子数 e/formula，并按法拉第关系换算 mAh/g。
- 阴离子氧化还原：氧、硫、氯的情景只作为显式选择的上限；默认不计入。F− 默认不设阴离子氧化还原窗口。
- 元素替换：提供保持计量数的组成级候选排序；不生成结构，不判断替换后的结构稳定性或渗流/输运。

## 在 py1 环境使用

在此目录打开 Python 或 Notebook：

    from Process_Struct.Chemical_Capacity_Constraints import (
        estimate_redox_capacity,
        screen_substitutions,
        batch_estimate_redox_capacity,
)

    result = estimate_redox_capacity("NaFePO4", environment="polyanion")
    result["sample_neutral_valence_assignments"]
    result["q_redox_e_per_formula"]
    result["capacity_mAh_g"]

批量处理 Materials Project 结果时，将 formula_pretty 列传入 batch_estimate_redox_capacity，再用 pandas.DataFrame(results) 汇总。逐行错误会保留在 status/error 字段中。

示例：筛选 Na3V2(PO4)3 的形式价态上限：

    result = estimate_redox_capacity("Na3V2(PO4)3", environment="polyanion")

示例：替换 NaFePO4 中的 Fe，并保留同一化学计量数：

    candidates = screen_substitutions(
        "NaFePO4",
        replaced_element="Fe",
        candidate_elements=["Mn", "Ti", "V", "Cr", "Cu"],
        environment="polyanion",
        capacity_cutoff_mAh_g=100,
    )

命令行也可直接运行：

    python Process_Struct/Chemical_Capacity_Constraints/redox_capacity.py "NaFePO4" --environment polyanion

价态表可在 redox_rules.json 编辑。新元素若没有明确规则，程序会报告 unresolved_elements，而不是自动猜价态。

卤化物环境已加入 In(I)/In(III) 价态窗口，因此含 In 的氯化物和氟化物可以参与 Li/Na 含量窗口估算。该窗口是宽松的形式价态筛选范围；In(I) 的稳定性依赖具体结构和条件，计算结果不代表实际可逆容量。

## 解释输出

- sample_neutral_valence_assignments：找到的电中性形式价态组合样例。
- q_cation_oxidation_e_per_formula_uncapped：不考虑移动离子数量时，阳离子从当前价态继续氧化的电子上限。
- q_redox_e_per_formula：默认 Qredox；加入指定阴离子情景后，再受可迁移 Li/Na/K 的形式电荷库存约束。
- q_reduction_e_per_formula：当前形式价态向规则下限还原的上限。
- full_cation_swing_e_per_formula：规则价态范围的完整跨度，不代表起始 SOC 下能抽出的电子数。
- capacity_mAh_g：Qredox 上限按输入化学式摩尔质量换算的比容量；质量按输入的初始组成计算。
- capacity_range_mAh_g：如果电中性价态解不唯一，报告估计区间。

## 重要边界

1. 建议输入含 Na/Li/K 的初始放电态（或项目定义的参考 SOC）完整化学式。只输入去掉碱金属后的中性框架时，程序不知道有多少移动离子可抽取。
2. 形式价态组合只表示电荷账本可闭合。实际可逆电子数还受电压窗口、局域配位、电子结构、结构相变、氧/硫释放和扩散速率影响。
3. 多阴离子基团按常见形式价态处理：PO4 中 P(+5)，SO4 中 S(+6)，SiO4 中 Si(+4)，BO3 中 B(+3)，CO3 中 C(+4)，NO3 中 N(+5)。这些骨架中心默认不参加容量计算。
4. 自动环境识别会区分常见混合阴离子。含羟基/水、过氧键、混合价硫或缺陷化学式仍需显式指定环境并检查规则。
5. 阴离子情景不应无条件相加。氧化物中的 O2−/O−、硫化物中的 S2−/S2²−、硫到 S0，以及 Cl−/Cl2 分属不同结构/电解液机制；只有有相应材料证据时才用。
6. “低成本优先”分组只是粗略筛选标签，不是实时价格排序。Fe/Mn/Ti/Cr 可作为第一轮候选，其他元素需按地区采购价格、储量、毒性、工艺和性能再排序。
7. 替换函数只筛组成。每个候选必须回到项目的结构生成、相稳定性、渗流、离子输运和电子输运步骤复算，才可能进入 AEA。

容量换算采用 Q(mAh/g) = 26801.4 × n(e−/formula) / M(g mol−1)。
## 按框架计算 Li/Na 含量窗口

对“给定框架，在稳定价态范围内最多/最少容纳多少 Li/Na”的问题，使用新增模块 `framework_ion_window.py`。它可接收不含移动离子的框架化学式，也可接收含 Li/Na 的参考化学式；若输入含目标离子，会先剥离该离子作为框架，并报告参考含量及可继续脱出/嵌入的数量。

    from Process_Struct.Chemical_Capacity_Constraints import estimate_mobile_ion_window

    result = estimate_mobile_ion_window("FePO4", mobile_ion="Na")
    result["x_min_mobile_per_formula"]
    result["x_max_mobile_per_formula"]
    result["delta_x_e_per_formula"]
    result["capacity_mAh_g"]

也可以直接输入完整参考态，例如 `estimate_mobile_ion_window("NaFePO4", mobile_ion="Na")`。批量计算使用 `batch_estimate_mobile_ion_windows(formulas, mobile_ion="Na")`。

该版本按各元素规则中的低/高价端点分别计算框架形式电荷，并用 `x = -Q_framework` 得到客体离子含量范围；默认允许混合价态和部分占位在端点之间连续变化，因此是偏宽松的化学上限。比容量默认按最大 Li/Na 含量态的质量归一化；另提供按框架质量归一化的结果。价态表仍可在 `redox_rules.json` 调整。

现成库的分工：pymatgen 的 `Composition.oxi_state_guesses()` 可按自定义价态列表枚举电中性组合，SMACT 可做化学式电中性筛选；pymatgen 的 `BatteryAnalyzer` 可估常规嵌入/脱出容量，但采用库内通用变价范围，且最大嵌入量不检查几何位点。因此这几个工具不能直接表达本项目这份按阴离子环境配置的宽松价态区间，新增函数负责把价态规则转换成框架的 Li/Na 含量端点。

## v0.4 Fe/Mn 高价态规则修正

常规正极框架中，氧化物、氧卤化物、多阴离子和混合阴离子环境的 Fe 默认限制为 +2/+3/+4，Mn 限制为 +2/+3/+4。Fe(VI) 铁酸根以及 Mn(VI/VII) 锰酸根/高锰酸根属于特殊含氧物种，不自动用于普通框架容量估算；例外信息记录在 special_oxoanion_states 中。若框架中没有规则表定义的可变价元素，容量返回 0。
## 混合阴离子输入

混合阴离子按“基团电荷 + 剩余单原子阴离子”分开记账。例如 Na3V2(PO4)2F3 中，两个 PO4 基团整体按 −3 计，三个游离 F 按 −1 计；PO4 内的 O 不会再次按 O²⁻ 重复扣电荷，也不会计入可选的晶格氧氧化还原。括号中的 PO4、P2O7、SO4、SO3、S2O3、SiO4、BO3、CO3、NO3 会直接识别；这些常见基团在未加括号时也会按化学计量尝试识别，并在结果中标明是否存在歧义。含氟磷酸根等上下文相关基团建议保留括号或显式传入每个化学式单位中的基团数：

    result = estimate_mobile_ion_window(
        "Na3V2(PO4)2F3",
        mobile_ion="Na",
    )
    # 无括号时显式指定同样的基团计数：
    result = estimate_mobile_ion_window(
        "Na3V2P2O8F3",
        mobile_ion="Na",
        anion_groups={"PO4": 2},
    )

容量估算函数也接受 anion_groups 参数。结果中的 recognized_anion_groups、grouped_atom_amounts 和 anion_group_assignment_ambiguous 会记录分组、电荷来源和识别歧义。分组规则是形式价态粗筛；配位环境、共价键和实际氧化还原机制仍需材料结构或实验信息确认。



## v0.5 正极框架价态范围修订

当前默认规则面向普通电池正极框架，收紧了少数主要描述分立含氧阴离子、强氧化分子或特殊高价化合物的范围。Fe 和 Mn 的范围已分别按 +2/+3/+4 处理；其他调整见 redox_rules.json 中的 default_excluded_states，其中记录了被移出默认范围的价态、环境和原因。Mo(VI)、W(VI)、V(V) 等在稳定固体氧化物框架中有化学依据的高价态仍予保留。

Cr(VI) 常以铬酸根/重铬酸根形式存在；Ru(VIII)、Os(VIII) 分别对应特殊分子氧化物 RuO4、OsO4；Re(VII) 多见于高价氧配体体系；Pt(VI)、Au(V) 的典型例子属于强氧化性氟化物。这些端点不能直接推广为普通框架位点的可逆容量。若筛选这些特殊物种，应为其明确反应另设规则。

