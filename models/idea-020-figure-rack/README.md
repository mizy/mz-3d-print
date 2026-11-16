<!-- generated-by: scripts/archive_design.py -->
# idea-020 桌面发带晾晒架「小人晾架」

原创设计归档（我们自己建模，不是外部模型改造）。

- 建模来源：参数化 SCAD + build123d 网格脚本
- 打印记录：未记录
- 归档时间：2026-11-09
- 文件清单 / SHA-256 / 几何尺寸：`ARCHIVE.json`

## 原始建模

| 文件 | 尺寸 mm | 面数 | 体积 cm³ |
|---|---|---|---|
| `figure-rack.stl` | 94 × 110 × 89.227 | 18220 | 145.406 |
| `model.scad` | - | - | - |

参数化脚本（`.scad` / `.py`）也在本目录，改动后按原命令重跑即可。

## 打印工程（3MF）

| 文件 | 切片重量 | 预计时长 |
|---|---|---|
| `figure-rack.3mf` | 未切片 | - |

## 文档 / 自检报告

- `DESIGN.md`

## 重跑与自检

```bash
cd idea-020-figure-rack
python3 build_mesh.py
python3 check.py
```
