# v6 候选验证范围

这是阶段优化，不是完整的少特征锁口重建，也没有保持数学上完全相同的配合面。v5 默认文件保留未改。

- 默认和改锁口尺寸预设：完整构建、导出、回读均为两个有效实体。
- 对原冻结参考的独立几何核对：wide 139 截面最大差 0.027499 mm；narrow 71 截面最大差 0.029943 mm。这是抽样，不是全表面最大误差证明。
- 名义配合调整：wide孔向内0.008×k mm，narrow基底外半径增加0.005×k mm；潜在相对径向净空减少约0.013×k mm。尚未验证装配姿态/旋锁运动间隙或实物试配。
- 总面数从16,758降到10,258（38.8%）；文件从32.77 MB降到24.48 MB。复杂锁齿仍有大量曲面。
- 平台拉伸及精确名义圆柱研究包含失败案例，未合入交付。详情在 independent_research，不能把其中有效单段等同完整模型通过。

报告 default_build_validation.json 与 lock_dimension_test_validation.json 是实际运行原始输出。额外风险和汇总在 summary.json、本说明及 Models/Review/README_v6_CANDIDATE.md；不要只读旧式通用 limitations 字段就忽略配合变化。

最终导出STEP另经独立第二次回读与10个关键截面检查（含密集检查峰值高度）：2个有效实体，最大采样差wide 0.027499 mm、narrow 0.029944 mm，均低于0.03 mm。仍非全局误差/装配间隙证明，详见independent_research/final_export_independent_readback.json。
