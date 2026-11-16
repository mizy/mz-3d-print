<!-- generated-by: scripts/archive_design.py -->
# idea-005 二次元少女 · 实体浮雕试片

原创设计归档（我们自己建模，不是外部模型改造）。

- 建模来源：自建图片转实体浮雕管线（make_relief.py），源图 source.png；两档 105×140 / 157.5×210
- 打印记录：未记录
- 备注：源图是生成图/参考图，不是第三方模型；几何由我们的管线产出
- 归档时间：2026-11-09
- 文件清单 / SHA-256 / 几何尺寸：`ARCHIVE.json`

## 原始建模

| 文件 | 尺寸 mm | 面数 | 体积 cm³ |
|---|---|---|---|
| `relief-anime-girl-s105.stl` | 105 × 140 × 5.268 | 369248 | 53.016 |
| `relief-anime-girl-s200.stl` | 157.5 × 210 × 5.27 | 831076 | 119.777 |

参数化脚本（`.scad` / `.py`）也在本目录，改动后按原命令重跑即可。

## 打印工程（3MF）

| 文件 | 切片重量 | 预计时长 |
|---|---|---|
| `relief-anime-girl-s105.3mf` | 未切片 | - |
| `relief-anime-girl-s200.3mf` | 未切片 | - |

## 重跑与自检

```bash
cd idea-005-anime-relief
# 两档参数见 report-s105.json / report-s200.json
python3 ../../scripts/make_relief.py --image source.png --out-dir . --name relief-anime-girl-s105 --max-width-mm 105 --max-height-mm 140 --preview --json
```
