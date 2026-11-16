# STEP 装配层级修正

唯一交付文件仍为 `Models/LV_bowl_and_logo.step`。实际STEP/XCAF回读层级为根装配下的 `Bowl` 与独立 `Logo_with_tenons`；Bowl 包含底板、浅蓝主体和米白口沿3个零件，总计4个实体、2色。

保持底部个人署名、前Logo、位置与几何不变，几何体积差在数值容差内。`hierarchy-validation.json` 是结构与几何检查，不是 Studio 验收。**Bambu Studio GUI 导入后的对象/部件层级尚未经验证**，不要将STEP正确层级等同于Studio一定按预期分组。用户仍需自己核对导入结果、分配耗材及切片。未操作Studio、未启动打印。

复现脚本为历史记录，含本次输入与输出路径；运行前必须先调整路径，避免覆盖当前文件。
