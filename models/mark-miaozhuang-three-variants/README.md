# 苗壮 Logo · 三版本资产（2026-11-12 入档）

来源：主人 2026-11-12 20:48 通过飞书发来的 `Miaozhuang_Three_Variants.zip`
（原始包留档 `source-upload-2026-11-12.zip`，内部文件时间 2026-11-09）。

图形：`miaozhuang-logo.svg` —— 「芽 + 立方体」，不是 11-01 那枚「苗壯」小篆印章
（那枚在 `../mark-miao-zhuang/`）。两套是不同的东西，别混用。

| 版本 | 文件 | 尺寸 (mm) | 说明 |
|---|---|---|---|
| 01 阴刻印章 | `01_Intaglio_Stamp.stl` | 76 × 96.21 × 40 | 印面 76×96.2、Logo 宽 60、阴刻深 1.2、左右镜像、背面握柄 Ø32 |
| 02 凸起铭牌 | `02_Raised_Logo_Plaque.stl` | 114 × 144.31 × 10 | 底板 5 + Logo 凸起 5，正常方向，单体 |
| 03 手办底座 | `03_Figurine_Display_Base.stl` | Ø160 × 18 | 展示面 Ø100 抬高 19，前方 Logo 宽 26、凸 1.2 |

## 复核（2026-11-12 本机重跑）

- 三份 STL：trimesh 读入均 watertight、body_count = 1，尺寸与 `geometry_report.json` 一致。
- 体积：01 = 56.06 cm³、02 = 106.95 cm³、03 = 313.96 cm³。
- 原包自带的 STEP / FreeCAD / Blender / 校验脚本全部保留，可继续改参数。

## 使用前必看

- 01 是**阴刻（白文）**：背景着色、Logo 留白。要「只有 Logo 着色」得另做镜像阳刻。
- 01 实物盖章需要弹性材料 + 合适印泥，本机 AMS 只有 PETG，直接用 PETG 打只能当刚性样机。
- 02 的 5 mm 凸字可直接 PETG 打；按面分色需要 AMS。
- 03 只是底座方案，没有脚孔/磁铁/插销；装手办前先确认脚印与重心（见 `docs/stability-load-analysis.md`）。
