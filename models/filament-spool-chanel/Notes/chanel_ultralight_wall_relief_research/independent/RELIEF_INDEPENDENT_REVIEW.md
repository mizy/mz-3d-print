# 阶段2中心减壁候选独立试切

候选CHANEL_ULTRALIGHT_WALL_RELIEF_RESEARCH.step，1,693,751 bytes，SHA256 1cf5a75e60c1b3273f7990c600f8af6b637c30f0ecbf86acdb95284461745946。

使用与首骨架相同的冻结0c2e用户工艺（latest_user_snapshot.3mf）：15%grid、2墙、顶5/最小1 mm、底3、0.2 mm层、薄壁检测开启、Jucoole PETG+。不修改用户原工程/UI。

| 模式 | 宽g | 窄g | 总g |
|---|---:|---:|---:|
| 用户配置（支撑关闭） |47.585796|45.589260|93.175056|
| 仅开启自动支撑诊断 |47.585773|45.585503|93.171276|

两组差0.00378 g，均没有Support、Support interface、Overhang wall正挤出路径。仍有Bridge路径，不能称全模型没有桥接。每次两半STEP读回有效，独立网格宽70732/窄57178三角，0开放边/0非流形边；四次CLI退出0，warning_message均空。

相对首骨架101.614101 g再减8.439045 g（8.30%），距60 g仍有33.175056 g，不以体积下降替代实际切片结果。

## 源实现与风险边界

center_relief.py采用原生回转切削，只处理有限高度、桥周2 mm带保护、wide键保护。按名义源参数：wide内导管非锁段壁1.9→1.25 mm，标记凹处可能仅0.9；narrow导管2.2→1.1；外柱wide1.85→1.2、narrow2.95→1.2；环腔地板留1 mm。此处数字是源设计名义值，本次未逐面搜索全模型最小厚度，不冒称全域厚度证明。

削去非配合面仍会降低内导管抗椭圆化、轴夹持、柱弯曲/屈曲、桥根与底环刚度；壁厚减少不能仅用体积/截面积比例预测刚度，局部板壳弯曲对厚度尤其敏感。若实际AMS/轴支承依靠内孔夹持，保留孔径不等于保留功能。标记局部0.9 mm需检查实际线宽及疲劳，薄地板也需打印/承载测试。

主实现者正在做保护区布尔验证，本报告仅确认文件、拓扑、同设置切片与路径，不替代其配合/装配结论；未重跑本候选FEM或实物试验。本候选保持研究状态，不发布、不替换打印工程。原骨架正在既有Codex线程仿真，不应在同一运行中悄然换成93 g候选。

证据：slice_relief及slice_relief_auto内mesh_reports.json、slice_reports.json、result.json/Gcode；paths_relief.json、paths_relief_auto.json；pack_and_slice_latest.py、latest_user_settings.json。
