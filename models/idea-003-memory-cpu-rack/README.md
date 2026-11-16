<!-- generated-by: scripts/archive_design.py -->
# idea-003 内存条 + CPU 展示架（含 v17 SKADIS 洞洞板版）

原创设计归档（我们自己建模，不是外部模型改造）。

- 建模来源：参数化建模：OpenSCAD rack.scad + Python 派生尺寸/重心 + 自检；v2→v8 迭代，v17 为 SKADIS 洞洞板试制版
- 打印记录：v17 的 universal_tray 小托架 2026-10-30 实打并卡进洞洞板
- 归档时间：2026-11-09
- 文件清单 / SHA-256 / 几何尺寸：`ARCHIVE.json`

## 原始建模

| 文件 | 尺寸 mm | 面数 | 体积 cm³ |
|---|---|---|---|
| `memory-cpu-display-rack-v2.stl` | 191 × 100.348 × 197.719 | 3012 | 274.362 |
| `memory-cpu-display-rack-v3.stl` | 200 × 103.015 × 186.526 | 4252 | 269.091 |
| `memory-cpu-display-rack-v4-wide-cpu.stl` | 200 × 103.015 × 199 | 4382 | 290.377 |
| `memory-cpu-display-rack-v5.stl` | 200 × 183.015 × 186.526 | 4408 | - |
| `memory-cpu-display-rack-v6.stl` | 196 × 168.015 × 186.526 | 2670 | 330.124 |
| `memory-cpu-display-rack-v7.stl` | 196 × 155.015 × 186.526 | 2686 | 299.148 |
| `memory-cpu-display-rack-v8.stl` | 196 × 155.015 × 186.526 | 42066 | 319.788 |
| `rack.scad` | - | - | - |

参数化脚本（`.scad` / `.py`）也在本目录，改动后按原命令重跑即可。

## 打印工程（3MF）

| 文件 | 切片重量 | 预计时长 |
|---|---|---|
| `anime-relief/miao-anime-depth-120x48-emboss.3mf` | 未切片 | - |
| `anime-relief/miao-anime-depth-120x48.3mf` | 未切片 | - |
| `anime-relief/miao-anime-relief-120x61.3mf` | 未切片 | - |
| `anime-relief/miao-anime-relief-150x76.3mf` | 未切片 | - |
| `memory-cpu-display-rack-v5.3mf` | 未切片 | - |
| `memory-cpu-display-rack-v6.3mf` | 未切片 | - |
| `memory-cpu-display-rack-v7.3mf` | 未切片 | - |
| `memory-cpu-display-rack-v8.3mf` | 未切片 | - |
| `v17-skadis/print-plates/00_fit_test-hookfix.3mf` | 未切片 | - |
| `v17-skadis/print-plates/00_fit_test-hookfix.sliced.3mf` | 7.43 g | 26m39s |
| `v17-skadis/print-plates/00_fit_test.sliced.3mf` | 7.48 g | 26m59s |
| `v17-skadis/print-plates/00_optional_fit_test.3mf` | 未切片 | - |
| `v17-skadis/print-plates/01_board-232.sliced.3mf` | 125.59 g | 4h05m |
| `v17-skadis/print-plates/01_board.3mf` | 未切片 | - |
| `v17-skadis/print-plates/02_relief_feet_trays-hookfix.3mf` | 未切片 | - |
| `v17-skadis/print-plates/02_relief_feet_trays-hookfix.sliced.3mf` | 85.96 g | 3h33m |
| `v17-skadis/print-plates/02_relief_feet_trays.3mf` | 未切片 | - |
| `v17-skadis/print-plates/02_relief_feet_trays.sliced.3mf` | 85.9 g | 3h33m |

## 文档 / 自检报告

- `design-v3.md`
- `v17-skadis/README.txt`
- `v17-skadis/design.html`
- `v17-skadis/print-plates/打印说明.txt`

## 重跑与自检

```bash
cd idea-003-memory-cpu-rack
python3 check.py
python3 preview.py
# 尺寸在 rack.scad；改完用 OpenSCAD 重新导出 STL
```
