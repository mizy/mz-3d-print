# 排风三通 V3（对开两瓣）打印参数

切片文件：`exhaust-tee-split_print_support.3mf`（Bambu Studio 02.08.02.61 实切，零警告）
切片时间 2026-11-01 20:44 · 574 层 · 3 h 01 min（含开机序列）· 91.9 g

## 机器与耗材

| 项 | 值 |
|---|---|
| 打印机 | Bambu Lab P1S，0.4 mm 喷嘴，纹理 PEI 板 |
| 耗材 | Bambu PETG Matte（AMS A2 黑，剩 81%；A1 白 100% 可替换） |
| 层高 | 0.20 mm（标准档，配合面精度优先，不上 0.24） |
| 单色 | 是，不开擦料塔 |

## 切片参数（--set 原样）

```
wall_loops=4                  # 1.68 mm 实体壁，止口/卡钩根部靠它
sparse_infill_density=20%     # gyroid，各向强度
sparse_infill_pattern=gyroid
top_shell_layers=5
bottom_shell_layers=4
seam_position=back            # 接缝甩到背面
seam_placement_away_from_overhangs=1   # 台账第 10 条：孔口固定缺陷先治接缝
brim_width=5                  # 两瓣高 115 mm、底薄，防倒
enable_support=1
support_type=tree(auto)
support_threshold_angle=30
support_on_build_plate_only=1 # 不在模型表面生根
support_top_z_distance=0.2
```

## 为什么必须开支撑（原设计「免支撑」的说法不成立）

实测两瓣的下向面（法向 z < -0.707，离床 >0.6 mm）：

| 高度带 | A 瓣 | B 瓣 | 位置 |
|---|---|---|---|
| z 20–30 | 727 mm² | 637 mm² | **压墙裙边 Φ68 的底面（z=22）**，外伸到 Φ59.4 管外 4.3 mm，纯水平悬垂 |
| z 80–90 | 235 mm² | 194 mm² | 支口端圈下沿（45° 悬垂） |
| z 60–80 | 132 mm² | 50 mm² | 卡钩下沿 |

裙边底面是贴墙密封面，不撑会垂 1–2 mm，泡棉胶压不住。开树形支撑后：
2 h 34 / 81.0 g（有 floating cantilever 警告）→ 3 h 01 / 91.9 g（零警告），代价 +27 min / +11 g。

## 配合尺寸（切片不改，出问题先核这里）

- 穿墙锥管 Φ57.8（进洞端）→ Φ59.4（靠墙面），按 Φ60 洞，单边 0.3–1.1 mm 间隙
- 压墙裙边 Φ68 × 2 mm 厚，45° 收坡回 Φ59.8
- 主管 Φ59.8 / 内孔 Φ55；软管插口 Φ59.8 × 26 mm
- 侧支口：外 Φ47 / 内 Φ42，与主轴 60°
- 搭接止口：深 1.2 mm，单边间隙 0.25 mm
- 空调管半圆卡口：Φ30 + 单边 0.8 mm，耳中心距主轴 48 mm
- 卡钩 3 处，钩齿 0.55 mm，卡钩应变 1.07%

## 后处理

1. 拆支撑优先清**裙边底面**（贴墙密封面），刀片刮平后贴泡棉胶
2. 支口端圈下沿、卡钩下沿的支撑点用砂纸带一下，别留硬点影响卡合
3. 两瓣先干装：止口插到底、三处卡钩逐个听响，再上墙
