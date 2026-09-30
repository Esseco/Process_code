# 价态规则的文献依据与使用边界

版本：初筛先验 v0.1。下列文献用于约束“哪些红氧对在电池正极中有实验/综述依据”以及多阴离子和阴离子氧化还原的边界。JSON 中的逐元素价态列表是对常见材料化学的启发式汇总，不是从单篇论文直接抄录的普适稳定价态表。

## 主要依据

1. Goodenough, J. B.; Kim, Y. Challenges for Rechargeable Li Batteries. Chemistry of Materials 2010, 22, 587–603. DOI: 10.1021/cm901452z. 经典正极化学与多电子/成本设计背景。
2. Assat, G.; Tarascon, J.-M. Fundamental understanding and practical challenges of anionic redox activity in Li-ion batteries. Nature Energy 2018, 3, 373–386. DOI: 10.1038/s41560-018-0097-0. 强调阴离子氧化还原高度依赖结构和局域电子态，不能只按形式价态推断可逆性。
3. Li, X. et al. Direct Visualization of the Reversible O2−/O− Redox Process in Li-Rich Cathode Materials. Advanced Materials 2018, 30, e1705197. DOI: 10.1002/adma.201705197. 在特定富锂氧化物中直接观察到可逆氧红氧过程，支持把 O2−→O− 作为可选上限，而非默认值。
4. Tong, W. et al. Elucidating anionic oxygen activity in lithium-rich layered oxides. Nature Communications 2018, 9, 947. DOI: 10.1038/s41467-018-03403-9. 氧阴离子活性受过渡金属局域环境显著影响。
5. Recent achievements on polyanion-type compounds for sodium-ion batteries. Journal of Power Sources 2017, 361, 285–299. DOI: 10.1016/j.jpowsour.2017.07.002. 综述磷酸盐、焦磷酸盐、氟磷酸盐、硅酸盐、硫酸盐及其代表性 Fe/V/Mn/Ni/Cu 等电极体系。
6. Chen, C. J. et al. Polyanion Sodium Vanadium Phosphate for Next Generation of Sodium-Ion Batteries—A Review. Advanced Functional Materials 2020. DOI: 10.1002/adfm.202001289. Na3V2(PO4)3 中 V3+/V4+ 与钠脱嵌的例子说明：即使价态允许更大跨度，结构中可逆 Na 数也可能更小。
7. Hansen, C. J. et al. Multielectron, Cation and Anion Redox in Lithium-Rich Iron Sulfide Cathodes. Journal of the American Chemical Society 2020. DOI: 10.1021/jacs.0c00909. 在特定 Li-rich Fe sulfides 中报告 Fe2+/3+ 与 S2−/S2(2−) 的协同红氧。
8. How inactive d0 transition metal controls anionic redox in disordered Li-rich oxyfluoride cathodes. Energy Storage Materials 2020. DOI: 10.1016/j.ensm.2020.07.013. 支持 oxyfluoride 中 TM 与 O 的协同作用，也表明 F 并不意味着 F− 本身必然参加可逆红氧。
9. Metal chloride cathodes for next-generation rechargeable lithium batteries. 2024, open-access review: https://pmc.ncbi.nlm.nih.gov/articles/PMC11016933/. Cl−/Cl2 转化有电池实例，但属于特殊转化型机制，不能默认作为普通氯化物框架容量。

## 为什么价态字典使用离散集合

元素的常见电化学价态通常是若干离散氧化态，不等同于区间内每个实数价态都同样稳定。程序因此存储允许态列表，例如 Fe: [2, 3]，而不是把 Fe 的“窗口”理解成连续实数。化学式电中性求解得到的混合平均价态可以是小数，但它代表不同晶位/电子态的平均，不意味着单个原子处于该分数价态。

## 多阴离子基团

第一版将常见骨架中心作为固定形式价态：
- PO4(3−)、P2O7(4−)：P(+5)
- SO4(2−)：S(+6)
- SiO4(4−)：Si(+4)
- BO3(3−)：B(+3)
- CO3(2−)：C(+4)
- NO3(−)：N(+5)

这些基团多数用于稳定结构框架，初筛默认不把中心原子计入可逆容量。若材料有明确的多阴离子中心红氧证据，应再单独加入体系级规则，不应只扩大通用区间。

## 卤素和硫、氧的边界

- O：默认 -2。氧红氧最多另报 O2−→O− 的形式容量上限；氧空穴、过氧键、分子氧形成和氧损失的可逆性各不相同。
- S：硫化物默认 -2；特定富锂硫化物可形成 S-S 键。S(-II)→平均 S(-I) 按每个 S 1 e 作为配对上限；S(-II)→S(0) 的 2 e/S 是转换反应上限，不能套用于普通插层框架。硫酸盐中的 S(+VI) 默认固定。
- Cl：框架氯默认 -1。Cl−/Cl2 的 1 e/Cl 只放在显式转换情景。
- F：框架氟默认 -1；第一版不提供 F−氧化情景。氟离子电池中的金属氟化/脱氟转换，不应被误认为 F− 在普通插层正极里有常规可逆阴离子红氧。

## 关键文献链接

- https://doi.org/10.1021/cm901452z
- https://doi.org/10.1038/s41560-018-0097-0
- https://doi.org/10.1002/adma.201705197
- https://doi.org/10.1038/s41467-018-03403-9
- https://doi.org/10.1016/j.jpowsour.2017.07.002
- https://doi.org/10.1002/adfm.202001289
- https://doi.org/10.1021/jacs.0c00909
- https://doi.org/10.1016/j.ensm.2020.07.013
- https://pmc.ncbi.nlm.nih.gov/articles/PMC11016933/
## v0.2：偏宽松价态范围

本版将常见电化学金属的价态列表扩展为跨相关固态化学的宽松端点集合，并加入 Ta、Re、Rh、Pd、Ag、Os、Pt、Au 及部分可变价稀土。高端价态如 Cr(VI)、Mn(VII)、Fe(V/VI)、Ru(VIII) 等只在特定配位、氧配体或多阴离子环境中稳定；它们进入上限估算不代表能在任意正极框架中稳定、可逆地参与循环。S(-II) 到二硫键中平均 S(-I) 的形式电荷差为 1 e/S，配置已相应修正。

价态数据的宽范围参考 pymatgen 所列 ICSD 氧化态统计（其条目需在 ICSD 中达到一定出现次数和占比），并结合电池正极文献中的具体氧化还原对；元素价态统计不能替代局域配位和材料环境判断。[pymatgen 氧化态数据说明](https://pymatgen.org/pymatgen.core.html)；[高压多阴离子正极综述](https://pmc.ncbi.nlm.nih.gov/articles/PMC8433932/)；[Fe/Mn 多阴离子钠正极综述](https://doi.org/10.1016/j.ensm.2026.104889)。
## 混合阴离子与多阴离子处理

混合阴离子体系逐元素处理单原子阴离子，并把已识别的多原子基团作为整体固定电荷：O 通常为 −2，F/Cl/Br/I 通常为 −1；硫化物中的 S 通常为 −2，而硫酸根、亚硫酸根和硫代硫酸根按基团电荷处理。PO4、P2O7、SO4、SiO4、BO3、CO3、NO3 可由括号或计量比识别；含氟磷酸根等环境敏感基团应在公式中保留括号，或通过 `anion_groups` 显式指定。

多阴离子基团中的 O 不自动纳入晶格氧氧化还原情景。无法唯一识别的化学式会标记基团推断歧义；含复杂硫氧阴离子或非标准配体时，优先提供明确基团计数。

氟磷酸盐 Na3V2(PO4)2F3 的形式电荷账本中，PO4 固定为 −3、F 固定为 −1，初始 V 平均为 +3；常规电压窗口中报告的可逆过程主要对应两个 Na 脱出及 V3+/V4+ 转变，说明价态上限不能取代结构位点和电压窗口判断。[Na3V2(PO4)2F3 研究](https://pmc.ncbi.nlm.nih.gov/articles/PMC7070626/)。
## v0.4：普通正极框架与特殊高价含氧物种分开

常规框架估算将 Fe 限定为 +2/+3/+4、Mn 限定为 +2/+3/+4。Fe(+4) 已在特定高电压铁基正极中研究；Mn(+4) 是层状锰氧化物正极的重要稳定价态。Fe(+6) 主要以四面体铁酸根 [FeO4]2−（如 K2FeO4）存在；Mn(+6) 常见于锰酸根 [MnO4]2−，Mn(+7) 常见于高锰酸根 [MnO4]−，均属特殊高氧化态含氧物种，不应泛化成普通插层框架中的 Fe/Mn 位点价态。Mn2O7 则是高度不稳定的分子氧化物。

因此，Fe(VI) 与 Mn(VI/VII) 仅作为 special_oxoanion_states 元数据保留，默认不进入通用容量算法；若要筛选铁酸盐正极、锰酸盐/高锰酸盐或转化型体系，应另建按明确基团和反应路径核算的规则。此修正用于减少把形式上可能的高价态直接当作任意晶体框架可逆容量的情况。

参考依据：[K2FeO4 铁酸根结构及其电池研究](https://pmc.ncbi.nlm.nih.gov/articles/PMC6366229/)；[铁酸盐(VI)含氧物种综述](https://pmc.ncbi.nlm.nih.gov/articles/PMC10690715/)；[层状氧化物中 Mn(IV) 与阴离子氧化还原综述](https://pmc.ncbi.nlm.nih.gov/articles/PMC8198143/)；[Fe(III)/Fe(IV) 氧化还原正极研究](https://www.pnnl.gov/publications/electrochemical-utilization-iron-iv-li13fe04nb03o2-disordered-rocksalt-cathode)；[锰高价氧化物与储能综述](https://pubs.rsc.org/ko-kr/content/articlehtml/2026/eb/d5eb00112a)。

## v0.5：其他元素的默认高价态核查

本版将一般正极框架规则与少见的分子/离子物种端点分开。Cr(VI) 通常体现于 chromate/dichromate 等多原子氧阴离子，故 Cr 的默认框架上限设为 +4；Co(V) 为少见且强烈依赖晶格环境的高价端，默认普通氧化物正极设到 +4。Ru(VIII)/Os(VIII) 分别与 RuO4/OsO4 特殊分子氧化物相关，Re(VII) 多见于 perrhenate 等高价氧配体化学，故不再通用化为普通电池框架阳离子上限。Pt(VI) 与 Au(V) 的典型化学例子是高氧化性分子氟化物，也从默认电池宿主范围中移出。Ni(I) 不再作为普通氧化物框架的默认下端。Mo(VI)、W(VI)、V(V) 等具有固体氧化物/插层框架化学依据的价态继续保留。

这些规则是面向候选筛选的环境化学先验，不是元素所有可能氧化态的普适清单。真实高电压材料可能出现氧配体空穴、金属-氧共价电荷转移或结构转化；仅凭形式氧化态表不能区分这些机制。新版本把移出的状态及其环境逐项写入 redox_rules.json 的 default_excluded_states，便于对特殊结构有证据时恢复。

核查依据：[铬(VI)以铬酸根/重铬酸根等多原子含氧阴离子存在](https://content.ampp.org/corrosion/article/77/7/696/2437/Technical-Note-Does-Cr6-Really-Exist-Difference)；[高能层状氧化物中的过渡金属/氧阴离子氧化还原边界](https://pubs.rsc.org/en/content/articlehtml/2020/ee/c9ee02803j)；[Ru 氧化物电化学与 Ru(VI/VIII) 溶解/挥发路径](https://pubs.acs.org/chreay/article/110/11/6446/196782/Solar-Water-Splitting-Cells)；[OsO4 的挥发性与氧化剂属性](https://www.ncbi.nlm.nih.gov/mesh/68009993)；[Pt(VI) 的典型分子氟化物 PtF6](https://pmc.ncbi.nlm.nih.gov/articles/PMC8518493/)；[Au(V) 氟化物化学](https://pubs.acs.org/doi/10.1021/ic700431s)；[Re(VII) 氧配体化学](https://pmc.ncbi.nlm.nih.gov/articles/PMC6514865/)。

