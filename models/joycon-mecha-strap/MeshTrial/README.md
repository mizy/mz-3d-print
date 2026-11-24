# 机甲侧饰腕带：封闭网格试印版

这不是参数化 STEP，也不是装机验证合格品。未做切片。

## 选择文件
- 单色打印主体：`BODY_SINGLE_SOLID_MESH_TRIAL.stl`。已经检查为一个封闭、法向一致的连通网格，包含连接好的侧饰。
- 双色主体：把 `BODY_GRAPHITE_MESH_TRIAL.stl` 与 `INLAYS_CYAN_MESH_TRIAL.stl` 按共同坐标作为同一个对象的不同部件导入，不要自动分别居中。分别设深灰、青色。两色是无体积重叠的分区，组合体等同上述单色主体。
- 按钮：`BUTTON_ORIGINAL_PRINT_TWO.stl`，需要两颗。保留作者原按钮形状，只平移，不添加未经验证的回位机构。
- `preview.png` 是实际主体网格渲染，未装按钮，不代表装机验证。

## 验证与限制
原作者两个主体组件先做网格并集，再增加原创侧饰。主件导出回读后封闭、法向一致且只有一个连通体。坐标合并精度 0.0001 mm；没有对原功能部分缩放或重设计，网格误差仍继承原 STL。主体约 101.052 × 15.200 × 12.700 mm，新增侧饰约 351.680 mm³。按钮也为封闭网格，但行程、按压力、复位、原控制器配合间隙和锁止安全均没有实测。

原设计无独立弹簧，从控制器底部滑入，与原厂腕带结构不同。不要强行推入，也不要依赖试印件进行挥动游戏。

来源：Cool Kid，Fully 3d Printable Replacement Strap for Nintendo Switch Joy-Con，Printables 580201，CC BY 4.0。原作者基于 youmu_i19 的 Nintendo Switch Joy-Con Strap。改动为网格并集、原创侧饰、分色分区与极小精度顶点合并。无原作者认可或任天堂认证。
https://www.printables.com/model/580201-fully-3d-printable-replacement-strap-for-nintendo-/files
https://creativecommons.org/licenses/by/4.0/

可重建源：项目 `Source/build_mesh_trial.py`、`Source/parameters.json` 与 `Reference/`。原解析 STEP 和 CAD 试版保留，未冒充修复成功；完整机甲图复刻、按钮舒适优化仍未完成。
