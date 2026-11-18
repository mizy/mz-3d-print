# 当前已选：105g 保留厚筒方案

唯一 STEP：`Models/CHANEL_105g_KEEP_CORE.step`。实际配置：`Source/weight_trials_v5/presets/original_lower_skin0.4_keep_rib_total3.2.json`。切片总耗材约105.27g，未认证承载。其他 STEP 已移到废纸篓；下文是历史对照记录，不代表文件仍在原处。

---

# 非默认减重候选：保留原件，不保证强度

- CHANEL_V5_SKIN0_4_KEEP_CORE_TRIAL.step：仅盘皮0.6→0.4mm；保留原下筒R36.8内孔、外壁、肩、卡口；主筋宽4mm/总高3.2mm、滚环、筒脚最低1.4mm均保持。优先比较这一组，以减少承力区域变化。
- CHANEL_V5_LOWER_R38_5_TRIAL.step：仅下筒内R38.5，对照试验；下壁wide2.35/narrow2.15mm。切片未显示有意义的低料收益，不推荐仅凭实体体积变小就采用。
- CHANEL_V5_LOWER_R38_5_SKIN0_4_TRIAL.step：薄下筒+薄盘皮对照；减重主要来自盘皮，薄筒可能因填缝而抵消稀疏节省。

全部为单STEP双独立有效实体，CAD回读通过；每组6个保护区截面对v5差为0（抽样，不是所有面的全局证明）。

0.4mm盘皮是Z厚度：在0.2mm层高下只有2层，不等于0.4mm喷嘴/线宽。两层皮更易碰损、翘曲；5%填充和2墙也没有受力验证。不能从“有效实体”推出能承载。

准确切片质量及参数以Notes/weight_trials_v5/independent_slicing报告为准。切片总耗材含支撑等，并非净成品秤重，更不保证机器启动清嘴耗材全部计入。默认v5/v6均未替换。下一步干燥剂结构集成尚未进入这些模型。

源代码和完整输入：Source/weight_trials_v5。R38.0预设只有组件体积研究，未作为第四组完整STEP交付。
