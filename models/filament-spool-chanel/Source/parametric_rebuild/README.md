# 原生参数化源码

## 编辑与再生成

使用 Python 3.11，安装 requirements.txt 后运行 `python rebuild.py`。
输出位于 build_output/，不会自动覆盖模型根 Models/ 中已核验的交付。

- build.py：盘面、双 C 阵列、8 条主筋与肩部的尺寸参数。
- structural_body.py：外滚环、筒壁、脚部、定位键及外筒旋转截面。
- native_lock_sections.json：可编辑的锁口圆弧/直线控制参数与高度区间。
- build_lock_pipes.py / native_loft.py：将这些参数放样、缝合为原生曲面实体。
- rebuild.py：重建两半、保留独立实体导出单 STEP，并进行 CAD 回读检查。

正式重建流程不需要读取三角网格。research/ 内的网格读取代码仅用于此前测量与独立误差检验，不用于把三角面导出成 CAD。
STEP 是边界表示交换格式，不包含 CAD 软件专属的完整特征历史；可编辑生成参数保存在上述源码与 JSON 中。

## 验证与限制

最终单 STEP 完整回读为 2 个有效实体；接口抽样误差最大约 0.029 mm。
参数调整后必须重新核查有效性、关键接口和实物试配，不能沿用旧报告。
宽半导向槽下方短圆柱采用 R31.39 mm（原测量约 R31.4），该处抽检差 0.01048 mm；其余拟合与表面替换也不是逐坐标无损。
旧轮廓的约 0.015 mm 壳错位已通过名义解析轮廓重建，而非原样复制瑕疵。
未进行实物试配、承载或 AMS 运行验证，100 g 目标仍需按实际填充设置切片确认。

Review/、checkpoints/、research/legacy_initial/ 是阶段审查资料，不应当成最终可打印件。
