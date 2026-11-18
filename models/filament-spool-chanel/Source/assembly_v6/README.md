# v6 指定候选的数字装配复现

输入固定为 `Models/Review/CHANEL_SOURCE21_v6_FIT_CHANGED_CANDIDATE.step`，不是任意参数模型的通用自动装配器。

同项目环境运行 `python reproduce_assembly.py`，输出 `Models/Assembly/CHANEL_v6_ASSEMBLY_LOCK_ZONE_10deg.step` 和 `Notes/assembly_v6/generated/` 检查报告。会重建同名装配文件，不更改输入的v6候选或v5模型。

姿态：wide保持不动；narrow先将拟合筒轴中心移至原点，绕X翻转180°，再绕Z旋转10°，最后对齐wide筒轴并移至H66.430113973mm。10°是在可轴向保留的锁止区内留余量的姿态，不是精确机械止挡/弹性卡嗒定位已认证。

该程序做所列4个全实体静态BRep交集与导出回读，不重算密集运动筛查。其他实际运行脚本作为原样快照保存在Notes/assembly_v6/scripts_snapshot，包含当时临时缓存路径；不能把它们视为通用重建入口。
