# 香奈儿盘皮与滚环连续连接修复
原盘皮外半径94，外环内半径95，存在1mm整圈空气缝，只有主筋跨越；单实体不代表盘皮处处连接。
修复保持原老花位置、筒、锁口、斜膜、A槽。盘皮延伸至R95.8，与外环正重叠.8；加R93.6..95.8、高.8的连续搭接环，及R44..46、高.8的内接环。原四个线孔再次贯穿切除。
新增参数直接参与构建：rim_overlap、rim_bond_inner_margin、hub_overlap、hub_bond_width、bond_height，集中在light_parameters.json。默认原生CAD重建成功；任意调参未全部验证。
执行：python build_light.py --config light_parameters.json --output <新目录>。输出两个可分别选择的真实BRep实体；STEP本身不含完整特征树，参数在源码。
未改原3MF或原STEP，用户自行替换模型；本次只交新STEP。材料/工艺仍影响粘接、翘曲与实际强度，不能把几何连通证明当打印承载保证。
