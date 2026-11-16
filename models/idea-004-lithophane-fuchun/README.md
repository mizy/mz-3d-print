<!-- generated-by: scripts/archive_design.py -->
# idea-004 富春江芦茨湾 · 透光浮雕试片

原创设计归档（我们自己建模，不是外部模型改造）。

- 建模来源：自建图片转透光浮雕管线（make_lithophane.py），源图 source.jpg
- 打印记录：未记录
- 备注：源图不是本人作品；几何与可打印性由我们的管线产出（图片转浮雕，不是模型改造）
- 归档时间：2026-11-09
- 文件清单 / SHA-256 / 几何尺寸：`ARCHIVE.json`

## 原始建模

| 文件 | 尺寸 mm | 面数 | 体积 cm³ |
|---|---|---|---|
| `lithophane-fuchun-river.stl` | 160 × 89.956 × 3 | 232400 | 24.771 |

参数化脚本（`.scad` / `.py`）也在本目录，改动后按原命令重跑即可。

## 打印工程（3MF）

| 文件 | 切片重量 | 预计时长 |
|---|---|---|
| `lithophane-fuchun-river.3mf` | 未切片 | - |

## 重跑与自检

```bash
cd idea-004-lithophane-fuchun
python3 ../../scripts/make_lithophane.py --image source.jpg --out-dir . --name lithophane-fuchun-river --width-mm 160 --preview --json
```
