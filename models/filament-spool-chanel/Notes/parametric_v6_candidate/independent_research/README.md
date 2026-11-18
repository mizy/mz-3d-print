# 独立简化研究归档（非交付模型）

所有结论、失败与验证范围见 RESEARCH_STATUS.txt。此目录只归档测量、审计报告及实际日志，没有复制任何未验证候选 STEP。

- constant_band_validation.json：两段局部拉伸环的有效性、STEP 回读及对原冻结网格每 0.025 mm 截面误差。
- replace.log：原整件替换，宽件成功；窄件 clean 报错。
- check_replacement.log：宽件 STEP 回读后接缝检查成功；随后因窄件未生成而无法打开其 STEP。不要误读为宽件失败。
- replace_pipe.log：解析底管后加平台，宽件有效，窄件得到 0 实体而被拒绝。
- wide_reordered_report.json：一次宽件调序试验有效，但没有完整独立回读/全高验证，不采用。
- v6_parameter_audit.json：只读源码参数传播与仿射控制测试，不是整个参数输入域认证。

## 脚本和输入

本次独立研究脚本及临时候选位于 `/tmp/chanel_parameter_audit/compact_lock/`；临时目录可能被系统清理，不是正式交付来源。脚本包括 scan_plateaus.py、arc_inventory.py、extrusion_prototypes.py、replace_bands.py、replace_pipe_bands.py、check_replacement.py、wide_reordered.py、audit_v6_parameters.py。

原件测量输入为从既有冻结 STEP 坐标/三角索引读取的只读参考网格，仅用于误差测量，未用来逐三角面生成候选 CAD。候选使用原生圆弧、直线与拉伸。

## 结论与边界

平台拉伸与解析底管简化收益重叠，组合增加接缝复杂度，未整合。v6 解析底管包含有意的小尺寸偏移，并非无损去冗余：默认宽孔向内约 0.008 mm，窄轴基底向外约 0.005 mm。实际净空取决于高度、旋转位置和接触特征，不能仅凭几何有效性认定装配通过。无实物试配、承载、切片重量或 AMS 验证。
