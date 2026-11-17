# 当前版本验证范围

当前制造件为外滚环、主筋、筒壁加厚版，无新增两条内部承力环。

当前报告：
- `FROZEN_VALIDATION.json`
- `hole_profiles.json`
- `CAD_IMPORT_STATUS.json`
- `PROTECTED_COMPARISON.json`
- `design_validation.json`
- `STEP_SERIALIZATION_VALIDATION.json`
- `CHANEL_SOURCE21_narrow.step.validation.json`
- `CHANEL_SOURCE21_wide.step.validation.json`

CAD内核回读未完成，`validated: false`不等于几何失败，也不等于兼容性通过。不得沿用旧版回读通过、98.37 g或旧版切片100 g内的结论。

`source_audit.json`、`repair_audit.json`、`stitch_audit.json`仅记录原始来源及源网格预处理，不是本次制造件的承重或CAD回读验证。被替代的旧制造审查报告可从Git历史恢复。
