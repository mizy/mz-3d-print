# V18 抽屉单独打印准备

源项目：`Print/V18_H100_Single_Module_P1S_PETG_UNSLICED.3mf` 的 1 号盘（04_Drawer）。
切片参数原样沿用：0.20mm 预设、10% gyroid、2 圈墙、上下各 2 层壳、PETG、无支撑、自动 brim。

## 交付文件

| 文件 | 状态 | 重量 | 预计时间 |
|---|---|---|---|
| `Print/V18_H100_Drawer_single_P1S_PETG.3mf` | 未切片工程，可改参数 | — | — |
| `Print/V18_H100_Drawer_single_P1S_PETG_sliced.3mf` | 已切片，可直接打印 | **123.0 g** | **3h 02m**（10537 s） |
| `Print/V18_H100_Drawer_windowed_P1S_PETG.3mf` | 镂空试版，未切片 | — | — |
| `Print/V18_H100_Drawer_windowed_P1S_PETG_sliced.3mf` | 镂空试版，已切片 | **111.4 g** | **2h 49m**（10165 s） |

单抽屉外廓 144.1 × 230 × 86 mm，P1S 一盘正好一件，四件要打四盘。

切片验证：`result.json` 返回 `Success`，无 warning，`support_used=false`。

## 两侧镂空试版

每侧墙开一个 120 × 45 mm、R8 圆角的窗口，位置 y=55..175、z=30..75：

- 距 Z10 主导轨上方 30 mm，距顶沿 11 mm，距前后角 ≥55 mm；
- STEP 实体体积 163876.4 → 153613.8 mm³，去掉 10262.5 mm³；
- 实测切片省 **11.64 g（9.5%）**，时间省约 13 分钟。

### 但这一版不能直接打

窗口上沿是一条 **120 mm 的水平桥**，且工程里 `enable_support=0`。PETG 跨 120 mm 会明显下垂，窗口顶部会拉丝/塌边。要镂空必须改成：

- 拱顶/半圆顶窗口（无长平桥），预计只能省 6–7 g；
- 或者一排小圆孔（单孔 ≤30–40 mm），省料更少；
- 或者保留平顶但在窗口内侧加一条加强筋/桥接唇。

结论：为了 10 g 左右去动侧墙不划算，尤其侧墙还是抽屉抽拉和搬运的主要受力面。建议先打原版；真要减重，先考虑缩短墙高或减少非受力装饰，不建议降顶/底壳层数（顶面会压在 10% 填充上起鼓）。

## 复现

```sh
python3 build_drawer_3mf.py
python3 build_windowed_3mf.py
# 镂空几何需要 FreeCAD
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd cut_side_windows.py
```
