# V18 抽屉三案 · 可独立替换的单件 STEP

三件都是从同一份正式 V18 素面抽屉做的原生 BRep，仅替换抽屉，不动框架、导轨、拨片、配合或原 STEP/3MF。三件均为 **144.10 × 230 × 86 mm、1 个有效实体**。各挑一个使用，不是三个零件拼成一个。无插片或支架。

| 方案 | 文件 | 变更 |
| --- | --- | --- |
| A 双侧叶脉 | [04_Drawer_A_Leaf_Vein.step](04_Drawer_A_Leaf_Vein.step) | 每侧 12 个通孔；0.96 mm 原侧壁，设计窗内实算开孔占比约 34.0%，关键孔间最小连筋约 3.58 mm。 |
| B 波浪前握口 | [V18_B_Wave_Grip_Drawer.step](V18_B_Wave_Grip_Drawer.step) | 前口宽约 66.1 mm、深约 13 mm；两侧仍封闭，前侧上沿从 79.6 mm 向后渐回 84 mm，其他原结构不动。 |
| C 前面画框窗 | [C_Front_Picture_Window.step](C_Front_Picture_Window.step) | 前板贯穿圆角窗 96 × 40 mm、R10，保持原上方握口；平底摆放时窗上缘约有 76 mm 水平跨度。**未验证免支撑。** |

[A/B/C 与原版的实际 CAD 对比](Comparison_CN.png) · [独立 CAD 回读](QA/Independent_Compatibility.json)

三案是限区纯减材。独立回读核对了完整外包络、底面和后止挡区域，未发现新增几何会挤占原装配运动；原方案左右总滑动间隙名义 0.60 mm。开孔使材料减少，不代表强度不变。没有切片、试印、载荷、手感或物理抽拉测试；首件先空屉试装、试抽并核对挡片，小物仍优先用素面 V18。A 可留通风，B保留封闭侧壁，C不替代承重/支撑检查。

## 可编辑重建

三案输入的素面 V18 原文件 SHA-256 `4fab31b0c8a9abac78bae99e9d4ee4634a2a545abd49272ac800f2d9df6a380b`。在 ZIP 内输入是 `Source/Seed/04_Drawer.step`；在 3D 打印项目内用 `../../Print_Parts/04_Drawer.step`，不要覆盖它。下面从本目录在能导入 FreeCAD 1.x、Part、Import 的 Python 中运行，输出用新的临时目录：

```sh
seed=Source/Seed/04_Drawer.step
[ -f "$seed" ] || seed=../../Print_Parts/04_Drawer.step
work=$(mktemp -d)
python3 Source/A/build_leaf.py "$seed" "$work/A" --config Source/A/Leaf_Vein_Parameters.json
mkdir "$work/B"
cp "$seed" "$work/B/V18_Baseline_Drawer.step"
cp Source/B/wave_params.json "$work/B/"
python3 Source/B/build_wave_tray.py --config "$work/B/wave_params.json" --out "$work/B/out"
python3 Source/C/build_c_front_window.py "$seed" Source/C/C_parameters.json "$work/C"
python3 Source/check_trays.py "$seed" QA/Edit_Regions.json "$work/Independent_Compatibility.json"
```

B 同时附原可编辑 FreeCAD 文档；它保留基准、切削和完工形体，直接改几何参数时仍应重运行脚本。STEP 是精确交换几何，不带特征历史。
