# deepfish 手办 · P1S 0.4 · PETG / PLA Silk

模型：deepfish 手办，34 个分件；打印机 P1S / 0.4 喷嘴。
默认耗材 Bambu PETG Matte 抗拉丝（245 ℃ / 风扇 50%）；第 4 盘另有 **PLA Silk** 版
（230 ℃ / 热床 55 ℃ / 风扇 100%）。

> **版本规则（2026-11-15 起）**：本项目只维护两个 3MF——`00_源工程/` 的原始工程 +
> `01_当前.../` 的当前工程。参数、分盘、朝向都在当前工程里改，保存同一个文件；
> **不再导出 `_v2/_v3/_修正/_final`**。下面列的多个文件是旧版本，后续归档，不再新增。

> 你原话是「3Dprint/deepseek 这种样子」。我按 `3Dprint/<模型>` 建成了
> `~/Documents/3Dprint/deepfish`；如果确实要叫 `deepseek`，直接改文件夹名即可。

## 目录

| 文件夹 | 内容 | 怎么用 |
|---|---|---|
| `00_源工程/` | `deepfish_plate1_vlh.3mf`（4 盘工程，含全部几何 + VLH 曲线） | 只作源文件；要重切从这里取件 |
| `01_当前_v2_2026-11-15/` | 八个已修正、可打的切片 | **优先打这里** |
| `02_历史_v1_2026-11-14/` | v1 的 5h14 切片留档 | 只作对比，不要打 |
| `03_不要打_失败归档/` | v1 安全盘（已失败）和高件盘（brim 会连片） | **不要打** |
| `04_预览/` | 各盘官方切片缩略图 | 看布局 |
| `05_历史工作/` | 当时的脚本、Bambu 预设、完整历史 README | 复盘/重切参考 |

## 当前版本 v2（2026-11-15）

| 盘 | 文件 | 件数 | 层高 | 时间 | 克重 | 关键参数 | 状态 |
|---|---|---:|---:|---:|---:|---|---|
| 安全盘 | `deepfish_安全盘11件_PETG_v2_间距14mm.gcode.3mf` | 11 | 0.16 | **1 h 10 min** | **8.55 g** | 14 mm 间距 / 5 mm brim / 2 墙 / 8% / 外墙 100 | ✅ PETG（结构/小件） |
| 第 4 盘 | `deepfish_第4盘7件_PETG_v2_间距14mm.gcode.3mf` | 7 | 0.16 | **23 min 47 s** | **5.31 g** | 14 mm 间距 / 5 mm brim / 2 墙 / 8% / 外墙 100 | ✅ PETG（结构/小件） |
| 第 4 盘 | `deepfish_第4盘7件_PLA_Silk_v2.gcode.3mf` | 7 | 0.16 | **21 min 44 s** | **5.28 g** | 14 mm 间距 / 5 mm brim / 230 ℃ / 热床 55 / 风扇 100% | ⚠️ 0.16，可见面建议 0.12 |
| 白盘 | `deepfish_白盘13件_PETG_v2_间距14mm.gcode.3mf` | 13 | 0.16 | **1 h 50 min** | **16.07 g** | 14 mm 间距 / 5 mm brim / 0 支撑 / hat 转 90° | ⚠️ 0.16，可见面建议 0.12 |
| 剩余 6 件 | `deepfish_剩余6件_PLA_Silk_v2_0.12.gcode.3mf` | 6 | **0.12** | **1 h 23 min 49 s** | **9.48 g** | 14 mm 间距 / 5 mm brim / 0 支撑 / hat 转 90° / 60-120 | ✅ 推荐（可见面 0.12） |
| 剩余 6 件 | `deepfish_剩余6件_PLA_v2_间距14mm.gcode.3mf`（用户实验） | 6 | 0.08 | 2 h 01 min | 12.69 g | 200/350 + 450 段支撑 | ⚠️ 实验版，不推荐直接打 |
| 蓝盘 大件 | `deepfish_蓝盘_大件6件_0.08_强支撑_v2.gcode.3mf` | 6 | 0.08 | **6 h 42 min** | **38.75 g** | 18 mm / 8 mm brim / 1250 段支撑 / 蓝 PETG | ✅ **推荐（小件成功逻辑）** |
| 蓝盘 大件 | `deepfish_蓝盘_大件6件_0.08_支撑.gcode.3mf` | 6 | 0.08 | 7 h 07 min | 38.52 g | 14 mm / 5 mm brim / 支撑到发丝上部 / 蓝 PETG | 备选 |
| 蓝盘 大件 | `deepfish_蓝盘_大件6件_0.08.gcode.3mf` | 6 | 0.08 | 6 h 09 min | 34.98 g | 14 mm / 5 mm brim / 0 支撑 / 蓝 PETG | ❌ 不要打（已否决：悬空太大） |
| 蓝盘 小件 | `deepfish_蓝盘_小件10件_0.08.gcode.3mf` | 10 | 0.08 | **1 h 41 min** | **6.30 g** | 14 mm / 5 mm brim / 0 支撑 / 蓝 PETG | ✅ 小件 |
| 高件盘 | v1 在 `03_不要打_失败归档/` | 5 | 0.16 | 4 h 52 min | 45.82 g | 8 mm brim，但件间距只有 2.5 mm | ❌ 不要打，待按 18 mm 间距重切 |

- **层高按可见性**：手办可见面 ≥ **0.12**，脸/头 0.08；0.16 只用于隐藏结构、底面、装配位。现有 0.16 盘如果可见面要更好，按 0.12 重切。
- 剩余 6 件推荐 `deepfish_剩余6件_PLA_Silk_v2_0.12.gcode.3mf`：0.12 mm、60/120、1 h 23 min / 9.48 g、0 支撑。
- PETG/PLA 各盘都是 `seam_position=back`、`enable_support=0`，G-code 里 `; FEATURE: Brim` 数 = 件数。
- PLA Silk 版同样 14 mm 间距、5 mm brim、0 支撑；打印前确认 PLA Silk 已装到 AMS 或外挂，并把 filament 1 映射到对应槽。
- 安全盘 11 件：waist / shoeR / shoeL / hairdai / earL / earR / hairF / hairsideL / armL / armR / ribben。
- 第 4 盘 7 件：ground / shoulderL / shoulderR / sockR / sockL / ribbenL / ribbenR。
- 头/手/腿（plate 2）已于 2026-11-14 打完（无支撑版 6.15 g / 0.76 h），本目录不再保留切片；要重打从源工程 plate 2 重切。
- 白盘 13 件 = 衣服/底座 6（skirt2 / hat / weiqun / ribbenB / root / body）+ 低件 7；`hat` 已绕 X 转 90° 放平，整盘 0 支撑。
- 蓝盘拆分：大件 6 = `hairBR / hairBL / hairsideL / hairsideR / tail / skirt`；小件 10 = `hairF / armL / armR / earL / earR / hairdai / waist / ribben / shoeL / shoeR`；两盘 0.08、0 支撑、14 mm 间距、5 mm brim，按 A4 浅蓝 PETG 切。
- 低件 7 打完后，剩下的衣服/底座 6 件用 `deepfish_剩余6件_PLA_Silk_v2_0.12.gcode.3mf`：0.12 mm / 60-120 / 1 h 23 min / 9.48 g / 0 支撑。
- 0.16 的旧切片只建议用于隐藏结构或赶时间；可见面按 0.12 重切。

MD5（v2）：
- 安全盘 `5cf5765e1bdd3e7ddd80e46bbe310548`
- 第 4 盘 PETG `8e8a502ee886d46b67c66da5012de39e`
- 第 4 盘 PLA Silk `51027287d99ee9fd5deb48ec998c6a24`
- 白盘 13 件 `3935a1e23ce454450810874ce3b4e6da`
- 剩余 6 件 PLA Silk 0.12 `ad2f083ddeec85f5b5af90144266fc13`
- 蓝盘大件（无支撑，已否决）`4d9ded17e7c7995b51d96eebba1587cd`
- 蓝盘大件（旧支撑版）`5761d90ee5113a00e76a23dfdc877dbd`
- 蓝盘大件（强支撑 v2）`601df1336630d2889339dba128cf76fe`
- 蓝盘大件（居中/非外观面朝上 v3）`c2b67881df8d3f04f7169a50610bf3c9`
- 蓝盘小件 `d11a4cdb751d0cf47d7bfc2e0763304b`

## v1 事故记录

| 文件 | 时间/克重 | 结果 | 根因 |
|---|---|---|---|
| `02_历史_v1/...plate1_vlh_sliced_5h14.3mf` | 5 h 14 min / 47.22 g | 炒面 | 16 件同盘、2 mm 间距 + 5 mm brim；两片 72 mm 发丝接触只有 5–8 mm²；同料支撑长到 70.7 mm 也在晃 |
| `03_不要打/...安全盘11件_PETG.gcode.3mf` | 1 h 10 min / 8.49 g | 第 39/116 层 FAILED | 自动摆盘默认 2 mm 间距 < 2×5 mm brim，brim 连成一片；延时确认第 16 层还分开、第 26 层已连片 |
| `03_不要打/...高件盘5件_PETG.gcode.3mf` | 4 h 52 min / 45.82 g | 未打，但布局有硬伤 | 5 件之间最近 2.5 mm，8 mm brim 必连片 |

**接缝在人脸**：源工程 `deepfish_plate1_vlh.3mf` 里是 `seam_position=aligned`，不是 `back`。
`aligned` 会沿固定特征对齐，脸朝后时接缝就落在脸上。重切头脸时：改 `back`，并把头脸件绕 Z
转 180°（脸朝 +Y 前方），切片后看预览的白点确认。

**受潮**：受潮会加重拉丝，但它不是上面两盘失败的主因；2 mm 间距 + 5 mm brim 是硬伤。
烘干后仍要用 v2 的 14 mm 间距版本。

## 规则

- 件间距 ≥ `2 × brim_width + 2 mm`：5 mm brim → **12 mm**，8 mm brim → **18 mm**。Bambu 自动摆盘默认 2 mm，不能直接切。
- 当前 AMS 四槽全是 PETG，外挂空；打 PLA Silk 前先装料并在打印对话框映射槽位。
- 2026-11-15 起允许同材质支撑，参数：`support_top_z_distance=0.32`、界面 3 层、XY 0.6。
- 上传后不自动开打；开始由人在打印机 / Bambu Handy 按。

## 重切

通用脚本：`~/.cah-data/skills/shared/bambu-studio-ai/scripts/plate_workflow.py`

```bash
PY=~/.cah-data/tools/bambu-ai-venv/bin/python
$PY -B ~/.cah-data/skills/shared/bambu-studio-ai/scripts/plate_workflow.py \
  --from-3mf ~/Documents/3Dprint/deepfish/00_源工程/deepfish_plate1_vlh.3mf \
  --plates 4 --group-by single --name deepfish_plate4 --upload
```

注意：脚本目前仍用 Bambu `--arrange 1`（默认 2 mm）；切片后会报 `min_gap < 2×brim` 警告。
看到警告不要直接打，按上面的间距要求重排（本轮 v2 是手工按 14 mm 间距排的）。

## 完整历史

`05_历史工作/deepfish-figure/README.md` 保留了 2026-11-14 的预设迭代、三盘/四盘参数、
0.16/0.12/0.08 对比和可变层高记录。里面的 `~/Downloads/...` 路径是当时的，文件已按本目录重组。
