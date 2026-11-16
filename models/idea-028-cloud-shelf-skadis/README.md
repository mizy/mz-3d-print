# idea-028 云朵托架 · SKADIS 手办搁板

原创设计归档。2026-11-07 实打，2026-11-09 重建四色分盘 3MF 并入库。

## 直接要的文件

- **四色分盘 3MF**：`3mf/cloud-shelf-skadis-4plates.3mf`
  - 盘 1 主体（奶油白 PETG）
  - 盘 2 背板 + 前挡板（灰 PETG）
  - 盘 3 云朵 ×2（白 PETG）
  - 盘 4 拱条 + 星月（黄 PLA）
- 10 件全排一盘：`3mf/cloud-shelf-all-10pcs.3mf`
- 设计说明与实测参数：`docs/DESIGN.md`
- MakerWorld 上传文案：`docs/上传文案.txt`

## 目录

```
model/stl/        原始单件 STL（母版几何，11 个文件）
model/plate-stl/  按颜色合并的分盘 STL（构建 3MF 的输入）
3mf/              四色分盘工程 + 10 件全排一盘原始 3MF
build/            3MF 构建脚本 + 工程参数模板
docs/             设计说明、打印参数、上传文案
preview/          上色渲染图、主体四视图
ARCHIVE.json      文件清单、SHA-256、尺寸
```

## 重跑四色分盘

```bash
python3 build/build_plates_3mf.py
```

脚本把 `model/plate-stl/` 的合并网格拆回独立零件，按颜色写入 4 个虚拟盘，
复用 `build/template-project_settings.json` 的 P1S 工程参数。

## 验收记录

2026-11-09 用 Bambu Studio 2.9.1 命令行切片，4 盘全部 `Success`，每盘换料次数 0：

| 盘 | 内容 | 耗材 | 切片克数 |
|---|---|---|---|
| 1 | 主体 | PETG #FABBCB | 45.3 g |
| 2 | 背板 + 前挡板 | PETG #898989 | 11.5 g |
| 3 | 云朵 ×2 | PETG #FABBCB | 2.4 g |
| 4 | 拱条 + 星月 | PLA #F7D117 | 1.66 g |

注意：这是 0.20 mm / 2 墙 / 8% 陀螺填充的统一工程参数，含支撑；实际打印主体用 0.28 mm、装饰件用 0.16 mm 时克数会不同（见 `docs/DESIGN.md`）。

## 归档契约

以后我们自己从零设计的 3D 打印件，都按这套结构存：

- `model/`：原始建模（STL / STEP / 参数化脚本）
- `3mf/`：可打印工程（多色件必须按颜色分盘）
- `docs/`：设计说明、实测参数、上传文案
- `preview/`：真几何预览图
- `ARCHIVE.json`：文件清单 + 哈希 + 尺寸

外部下载的模型不按这套归档。
