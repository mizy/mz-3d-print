# 当前入口与整理说明

- 当前打印工程：`Models/ChanelLight/PARKING_A_WINDOW_TRIAL.3mf`，保留原内容和路径，未操作打印。
- 最新自支撑模型：`Models/ChanelLight/CHANEL_PARKING_A_SELF_SUPPORT_ROOF_TRIAL.step`。
- 最新参数源码：`Source/chanel_parking_selfsupport_roof/` 与 `Source/CHANEL_SELF_SUPPORT_ROOF_PARAMETRIC_SOURCE.zip`。
- 当前报告：`Notes/chanel_selfsupport_roof/`。重量随用户工艺变化，以下历史数值不可套用。
- 明确过时交付与重复源码归入可恢复废纸篓，清单见 `Notes/cleanup_latest_manifest.json`。历史验证、装配与复现所需基准仍保留。

## 以下为历史记录，不是当前下载清单

# 最新模型：一体薄斜膜与径向斜顶

Models/ChanelLight/CHANEL_PARKING_A_SELF_SUPPORT_ROOF_TRIAL.step；Source/chanel_parking_selfsupport_roof；Notes/chanel_selfsupport_roof。用户实际工艺自动支撑开启，副本复切Support/界面路径均0，总108.19g；仍有微量桥接/实物未验证。原3MF替换另看project_replace_status.json，不能据模型保存认定工程已替换。

# 最新减重候选：切片总103.03g（不是精确100g）

Models/ChanelLight/CHANEL_PARKING_A_WINDOW_LIGHT_TRIAL.step；Source/chanel_parking_A_window_light；完整报告Notes/chanel_parking_A_window_light。扣支撑约100.98g仅为估算，未称重；新模型未做力学/实物验证，外筒开窗减少纸芯支承。原官方基准和119g方案均保留。

## 当前 A 停线槽修正版（rev2）

Models/ChanelLight/CHANEL_OFFICIAL_LIGHT_PARKING_A_TRIAL.step，Source/chanel_parking_A_rev2，报告 Notes/chanel_parking_A_rev2。两半总切片耗材119.1411g，比原轻量119.6321g少0.4910g（0.41%），不是大幅减重。槽外移0.9mm消除首版薄壁；槽处滚环局部截面少约24.6–24.7%，仍须实物夹持与承载验证。运行AMS前释放线尾。

下文若出现119.071g/0.561g，为已拒绝的首版R96槽研究，不是可用交付；REJECTED_THIN_WALL文件不得打印。正式原基准和原轻量版未覆盖。

# 官方参数化基准与轻量双 C 派生：完成记录

两版本分别保留，各 STEP 包含可独立选择的宽、窄两实体。来源为官方 Wiki STL 附件的原生 CAD 逆向重建，不是厂商原生 CAD、标注公差图或三角面封装 STEP。STEP 不含参数特征树；可编辑 JSON、Python 和少量弧线/平面草图数据在 Source 两个独立目录中。

## 验证结果
- 从最终保存的两套源码独立运行再生；回读均 2 个有效实体，逐件面数与体积和审查版一致（报告 source_reproduction.json）。
- 基准 Ø200，宽高40.7 / 窄高34.1 mm，每半4个 Ø3.5 线孔；恢复完整内导管、四桥、外口 Ø55 及倒角、锁口、定位键与标记。
- 基准对官方网格全件离散截面：宽36层最大约0.028921 mm，窄22层最大0.011490 mm。不是全表面误差上界；浅标记采用少量原生曲面近似。
- 两版本最终 STEP 直接三角化：均0开放边、0非流形；双件分别 CLI 切片成功，无返回的 warning_message。源模型没有网格补洞。R31.4近重合拟合圆造成的旧薄片面已在原生草图修正。
- 实际变参验证：基准外径/线孔位置及孔径/轴孔/桥宽/宽筒孔组合、轻量logo缩放/盘皮/筋宽组合，均2有效实体且网格闭合。仅这些组合通过，不代表任意参数范围；全局筒缩放目前明确拒绝，防止假联动。
- 派生版完整中心、滚动外缘和4孔局部与基准布尔差为0，12个保护区检查通过。
- 同一 PETG+、0.4喷嘴、0.2层、2墙、顶3层0.6、底3层、5%填充及原自动支撑配置：基准总耗材168.122345 g；轻量总耗材119.632122 g。包含切片器计入的支撑等路径，不是称重，也不承诺全部机器启动耗材。旧105g重量不能套用于恢复官方结构后的方案。

## 装配和打印限制
- 正确对轴翻转后，H=66.4 mm，51°插入并旋到8°的离散路径采样无刚性交叠；8°是保留区而非最终止退扣验证。
- 接近最终止退位置存在刚性交叠：3°约4.205 mm³，0°约0.369 mm³。官方原 STL 独立积分也有约4.197/0.364 mm³，不能归因于重建独有，也不能因此推断弹性越障安全。
- 尚未实物试配、承载测试、可靠性认证或有限元强度分析。0.4 mm盘皮在0.2层高下仅2层，必须先试打/试配，再验证装满料盘受力。
- 官方页面提示打印料盘仅作临时/应急用途，不应使用它烘干耗材。
- 可下载的 spacing shim 尚未参数化或验证，未宣称包含；附件数量与安装要求未确证。
- 未操作用户当前 Studio，未发送打印。干燥盒保持独立。

## 旧方案
Models/CHANEL_105g_KEEP_CORE.step 及旧修复网格仍作为历史原件留存，但中心导向结构错误，不再是当前入口，不建议打印。此次不覆盖或删除旧文件。

## 当前文件
- Models/OfficialBaseline/BAMBU_OFFICIAL_REFERENCE_NATIVE_BASELINE.step
- Models/ChanelLight/BAMBU_OFFICIAL_DERIVED_LIGHT_CHANEL.step
- Source/BAMBU_official_and_CHANEL_parametric_sources.zip

源码：Source/official_baseline 和 Source/chanel_official_light；各目录 README 给出已实际执行的再生命令。

## A停线槽候选（后续）
Models/ChanelLight/CHANEL_OFFICIAL_LIGHT_PARKING_A_TRIAL.step；Source/chanel_parking_A_trial；报告Notes/chanel_parking_A_trial。切片119.0711g，仅减0.561g，不代表大幅减重或已测强度。原版本保留。

## A停线槽候选（后续）
Models/ChanelLight/CHANEL_OFFICIAL_LIGHT_PARKING_A_TRIAL.step；Source/chanel_parking_A_rev2；报告Notes/chanel_parking_A_rev2。修正版切片结果见Notes/chanel_parking_A_rev2/SUMMARY.json，减重不足1g，不代表大幅减重或已测强度。原版本保留。

## 最新开窗版装配审查
Notes/window_spool_assembly/README.md；Models/AssemblyReview 下3个姿态仅供审查，不能合并打印。轴向/旋转至8°采样无交叠；0°名义止退仍有官方原件同源干涉，弹性未验证。纸芯尺寸缺失，未虚构纸芯或宣称通过。
