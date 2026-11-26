# V18 H100 抽屉底板受力复核（10% gyroid 预设）

日期：2026-11-24
对象：`Print_Parts/04_Drawer.step`（从发布 3MF 中回读的网格，打印姿态，底面在 Z=0）

## 1. 实际几何（射线实测）

| 项目 | 数值 |
|---|---|
| 外廓 | 144.10 × 230.00 × 86.00 mm |
| 内腔 | 142.18 × 228.08 × 83.40 mm |
| 底板厚度 | 2.60 mm |
| 侧壁/前后壁厚度 | 0.96 mm（CAD 1.00） |
| 实体体积 | 163.9 cm³（实心当量） |

## 2. 打印配置

发布 3MF 的 `print_settings_id = 0.20mm-减少实心稀疏填充省料`，工程内覆盖：

- 0.20 mm 层高，0.42 mm 线宽
- 2 圈墙
- 顶/底各 2 层实心壳（各 0.4 mm）
- 10% gyroid 稀疏填充
- PETG

因此底板不是单层薄皮，而是 **0.4 mm 实心底皮 + 1.8 mm 10% gyroid 芯 + 0.4 mm 实心内皮** 的夹芯板。

## 3. 等效弯曲刚度

取 PETG E=2000 MPa，gyroid 10% 芯相对模量 0.05/0.10/0.15 三档：

| 芯模量比 | 等效 E | 相对实心 |
|---|---|---|
| 0.05 | 1370 MPa | 0.685 |
| 0.10 | 1403 MPa | 0.701 |
| 0.15 | 1436 MPa | 0.718 |

计算取中间值 **0.70**。芯模量对结果影响很小（±2%），说明弯矩主要由上下两层实心皮承担——**把稀疏填充从 10% 提到 25%，底板刚度只增加约 7%，不划算。**

## 4. 底板计算

方法：`3d-print-ideas/scripts/fea_plate.py`，Kirchhoff 薄板 + Morley 单元；四边简支为基准（偏保守），另给四边固支上界。均布载荷用 15×25 节点等效，20N 单点按真实点载。网格 2.0 mm（12829 单元）与 1.4 mm（26288 单元）对比，挠度差 <0.3%，应力差 <7%。

| 工况 | 最大挠度 | 最大弯曲应力 | 短期安全系数 |
|---|---|---|---|
| 0.5 kg 均布 | 0.19 mm | 0.22 MPa | 124 |
| 1 kg 均布 | 0.38 mm | 0.43 MPa | 62 |
| 2 kg 均布 | 0.75 mm | 0.87 MPa | 31 |
| 3 kg 均布 | 1.13 mm | 1.30 MPa | 21 |
| 1 kg 均布，四边固支 | 0.11 mm | 0.38 MPa | 70 |
| 2 kg 均布，四边固支 | 0.21 mm | 0.77 MPa | 35 |
| 2 kg 集中在 40×40 mm | 2.28 mm | 3.64 MPa | 7.4 |
| 20 N 单点（约 2 kg 压一个小脚） | 2.61 mm | 10.8 MPa | 2.5 |

材料判据：PETG XY 48 MPa / Z 27 MPa；工具取较小值 27 MPa，边缘支座奇异点已忽略，读的是板面峰值。

## 5. 结论

1. **均匀装载不是问题。** 2 kg 铺开只下沉 0.75 mm，3 kg 也只有 1.13 mm；应力不到 1.5 MPa。抽屉中部不会因为正常收纳而塌。
2. **真正的限制是局部重物和蠕变。** 2 kg 压在 40 mm 见方的小块上，挠度就到 2.3 mm；20 N 单点（小脚、工具尖角）到 2.6 mm、10.8 MPa，短期安全系数只有 2.5。PETG 长期受力按 2 倍挠度估，单点长期会到 5 mm 量级。
3. **10% gyroid + 2 层壳这套预设对底板够用。** 想加强中部，优先把顶/底壳从 2 层加到 3 层（+约 23% 刚度），或者局部加筋/加厚；加填充密度几乎没用。
4. **侧壁是另一个方向。** 实测只有 0.96 mm，前壁顶边中央单点拉拽在线性板理论下已经远超小变形适用范围，本次不给数字结论；如果实际是抓前壁上沿中间拉抽屉，建议加握口加强或改成从两侧受力。此项需要非线性/实体模型或实物验证。

## 6. 模型边界（必须一起读）

- 底板按夹芯板等效，假定 0.4 mm 内皮连续且与 gyroid 芯有足够粘接；若内皮局部缺料或芯未接上，夹芯作用会下降。
- 四边简支忽略侧壁对底板的转动约束，偏保守；固支为乐观上界，真实在两者之间。
- 线性小变形；超过约 1–2 mm 后膜力会参与，实际挠度小于线性值，但局部应力会重新分布。
- 不含层间剥离、蠕变、温度（>40℃ 继续打折）、跌落和抽屉抽拉冲击。
- 3MF 未切片，以上质量/厚度按几何与切片参数推算，不是实际称重。

## 7. 复现

```sh
cd models/modular-drawer/V18_Single_Head_T_Rod_Drawer/Notes/fea_drawer_infill
uv run --offline --python 3.12 --with numpy --with trimesh python3 measure_drawer.py
uv run --offline --python 3.12 --with numpy --with trimesh python3 build_cases.py
UV_DEFAULT_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple \
uv run --python 3.12 --with numpy --with scipy --with trimesh --with triangle \
  --with scikit-fem --with matplotlib --with networkx \
  python3 ~/.cah-data/skills/shared/3d-print-ideas/scripts/fea_plate.py \
  bottom_panel.stl --material PETG --thickness 2.6 --stiffness-factor 0.70 \
  --loads loads_bottom.json --mesh-size 2.0 --out fea_bottom
```

产物：`measure.json`、`section.json`、`loads_bottom.json`、`fea_bottom/report.json`、`fea_bottom_check/report.json`、`fea_2kg/deflection.png`、`fea_20n/deflection.png`。
