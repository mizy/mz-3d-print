# 当前已选：105g 保留厚筒方案

唯一 STEP：`Models/CHANEL_105g_KEEP_CORE.step`。实际配置：`Source/weight_trials_v5/presets/original_lower_skin0.4_keep_rib_total3.2.json`。切片总耗材约105.27g，未认证承载。其他 STEP 已移到废纸篓；下文是历史对照记录，不代表文件仍在原处。

---

# 非默认减重候选，待切片和实测

保留v5外形/卡口。仅把下筒内半径36.8改为38.0或38.5，斜肩下端内腔按原依赖同步。R38.5时下筒壁wide2.35mm/narrow2.15mm，筒脚和肩顶接口不变。

本目录明确扩展了几何候选输入范围，最低下壁2mm只是候选筛查，不是强度验证。默认parameters.json仍保留v5基线，实际候选在presets，生成时显式指定--config与独立--output。不能把实体质量等同切片耗材质量。

追加候选：盘皮0.4mm（0.2mm层高时2层），主筋above_skin=2.8mm以保持总高3.2mm；筒脚最低1.4mm，不随盘皮变薄。滚环与锁口不变。该薄皮更易受碰撞、翘曲，不是已验证受力方案。
