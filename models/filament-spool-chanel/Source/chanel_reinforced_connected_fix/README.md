# 香奈儿连环厚盘修复
本版只交STEP，不修改用户3MF。原1mm空气缝与0.4mm两层薄皮均已纠正。

- 盘皮1.2mm，名义0.2层高对应6层，由实际切片另核。
- 外接环R93.6..95.8，高1.6mm；盘皮伸入原外环0.8mm，不再只靠筋搭桥。
- 内接环R44..46，高1.6mm。
- 8条完整主筋宽5/高3.6，图案不再削断主筋。
- 双C镂空缩放0.90；孤岛短桥固定实宽1.4mm，不随图案缩小变细。
- 原筒/卡口/自支撑斜膜保留，原四线孔贯穿，A槽与外滚面保留。

配置light_parameters.json。新增rim_overlap、rim_bond_inner_margin、hub_overlap、hub_bond_width、bond_height及logo_bridge_width直接参与原生几何构建。独立重建：python build_light.py --config light_parameters.json --output <新目录>。输出两独立实体真实BRep，不读取STL/网格。STEP不含原生特征树，可再生参数保存在源码。

这不是强度认证；层间粘接、材料、实际打印尺寸和载荷仍须试验。没有新仿真，不再用重量目标限制加强。之前单实体检查不足以发现整圈盘皮缝，本版用跨区域实体/路径连接检查。
