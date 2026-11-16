<!-- generated-by: scripts/archive_design.py -->
# idea-007 立体字 / 名牌三式样

原创设计归档（我们自己建模，不是外部模型改造）。

- 建模来源：参数化 OpenSCAD 立体字：立式摆件 / 带挂孔名牌 / 钥匙扣
- 打印记录：未记录
- 归档时间：2026-11-09
- 文件清单 / SHA-256 / 几何尺寸：`ARCHIVE.json`

## 原始建模

| 文件 | 尺寸 mm | 面数 | 体积 cm³ |
|---|---|---|---|
| `keychain.scad` | - | - | - |
| `keychain.stl` | 30.472 × 30.722 × 7 | 788 | 3.562 |
| `name-stand.scad` | - | - | - |
| `name-stand.stl` | 135.402 × 16 × 43.485 | 1476 | 21.38 |
| `name-tag.scad` | - | - | - |
| `name-tag.stl` | 128.672 × 48 × 11 | 1860 | 28.89 |

参数化脚本（`.scad` / `.py`）也在本目录，改动后按原命令重跑即可。

## 打印工程（3MF）

| 文件 | 切片重量 | 预计时长 |
|---|---|---|
| `keychain.3mf` | 未切片 | - |
| `name-stand.3mf` | 未切片 | - |
| `name-tag.3mf` | 未切片 | - |

## 重跑与自检

```bash
cd sample-nameplate
# 用 OpenSCAD 分别打开 keychain.scad / name-tag.scad / name-stand.scad 导出 STL
```
