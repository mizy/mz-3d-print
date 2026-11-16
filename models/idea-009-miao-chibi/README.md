<!-- generated-by: scripts/archive_design.py -->
# idea-009 Q 版二次元手办

原创设计归档（我们自己建模，不是外部模型改造）。

- 建模来源：参数化 SCAD + Python 网格构建（model.scad / model.py）
- 打印记录：未记录
- 归档时间：2026-11-09
- 文件清单 / SHA-256 / 几何尺寸：`ARCHIVE.json`

## 原始建模

| 文件 | 尺寸 mm | 面数 | 体积 cm³ |
|---|---|---|---|
| `miao-chibi.stl` | 60 × 61.973 × 139.102 | 27330 | 158.819 |
| `model.scad` | - | - | - |

参数化脚本（`.scad` / `.py`）也在本目录，改动后按原命令重跑即可。

## 打印工程（3MF）

| 文件 | 切片重量 | 预计时长 |
|---|---|---|
| `miao-chibi.3mf` | 未切片 | - |

## 重跑与自检

```bash
cd idea-009-miao-chibi
python3 model.py
python3 check.py
```
