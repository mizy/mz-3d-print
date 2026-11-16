# 穿墙×两瓣耦合小样（coupon）打印参数

2026-11-01 20:51 实切 · 两片同盘 · 65 层 · 23 min 27 s（含开机序列）· 4.37 g

## 参数（与正式件一致）

```
P1S 0.4 / 纹理 PEI / Bambu PETG Matte（A2 黑）
layer_height=0.2
wall_loops=4
sparse_infill_density=20%  sparse_infill_pattern=gyroid
top_shell_layers=5  bottom_shell_layers=4
seam_position=back  seam_placement_away_from_overhangs=1
enable_support=1  support_type=tree(auto)  support_threshold_angle=30
support_on_build_plate_only=1  support_top_z_distance=0.2
```

## 实测结论

- 摆盘：两片并排（x 各偏 ±40），外廓 149 × 56.4 × 13 mm，间距 11 mm
- 支撑：只有**法兰耳片底面**（z=3，92.7 mm²/片）需要，树形从底板长到 z≈2.2；
  耦合座底面（z=5）由法兰耳片托着，实测悬垂只剩 8.1 mm²，切片不生成支撑
- 首层：一圈 2.5 mm 宽半环 + 支撑底座（闭合环，接触 211 mm²/片），auto_brim 判定不需要 brim
- Φ3.4 半孔：z 9±1.7 的圆弧渐变悬垂（31 mm²/片），不设支撑，孔顶可能略毛，M3 仍可通过
- 用料：净料 3.88 g（双方自报）→ 实切 4.37 g，差 0.49 g = 墙/支撑/首层/起始

## M3 五金

Φ3.4 通孔沿 Y 贯穿座体 12 mm（每片 6 mm），**需要 2 套**：
M3×16 螺钉 + 螺母 + 平垫（12 + 2.4 + 0.5 ≈ 15，16 留 1 mm 余量）。M3×20 也行，别更长。
轻拧，孔是 PETG 半孔，强拧会裂。
