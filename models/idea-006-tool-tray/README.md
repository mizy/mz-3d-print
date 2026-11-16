<!-- generated-by: scripts/archive_design.py -->
# idea-006 桌面工具收纳盘

原创设计归档（我们自己建模，不是外部模型改造）。

- 建模来源：参数化 OpenSCAD（model.scad）+ 21 项自检
- 打印记录：未记录
- 归档时间：2026-11-09
- 文件清单 / SHA-256 / 几何尺寸：`ARCHIVE.json`

## 原始建模

| 文件 | 尺寸 mm | 面数 | 体积 cm³ |
|---|---|---|---|
| `model.scad` | - | - | - |
| `tool-tray.stl` | 250 × 200 × 25 | 1836 | 226.663 |

参数化脚本（`.scad` / `.py`）也在本目录，改动后按原命令重跑即可。

## 打印工程（3MF）

| 文件 | 切片重量 | 预计时长 |
|---|---|---|
| `tool-tray.3mf` | 未切片 | - |

## 重跑与自检

```bash
cd idea-006-tool-tray
python3 model.py
python3 check.py
```
