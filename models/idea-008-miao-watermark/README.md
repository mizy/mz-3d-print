<!-- generated-by: scripts/archive_design.py -->
# idea-008 苗白菜印章 + 手柄

原创设计归档（我们自己建模，不是外部模型改造）。

- 建模来源：自建印章面（位图→平顶几何）+ 独立手柄；印章 70×46.67×4.1，手柄 φ46×23.55
- 打印记录：未记录
- 归档时间：2026-11-09
- 文件清单 / SHA-256 / 几何尺寸：`ARCHIVE.json`

## 原始建模

| 文件 | 尺寸 mm | 面数 | 体积 cm³ |
|---|---|---|---|
| `miao-stamp.stl` | 70 × 46.667 × 4.1 | 146948 | 10.578 |
| `stamp-handle.scad` | - | - | - |
| `stamp-handle.stl` | 46 × 46 × 23.545 | 5564 | 22.373 |

参数化脚本（`.scad` / `.py`）也在本目录，改动后按原命令重跑即可。

## 打印工程（3MF）

| 文件 | 切片重量 | 预计时长 |
|---|---|---|
| `miao-stamp.3mf` | 未切片 | - |
| `stamp-handle.3mf` | 未切片 | - |

## 重跑与自检

```bash
cd idea-008-miao-watermark
# 手柄：OpenSCAD 打开 stamp-handle.scad
# 印章面：由 source-logotype.png 生成，参数与验收见 stamp-report.json
```
