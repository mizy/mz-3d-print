# idea-017 镂空分隔收纳篮（苗壮制造）

塞进柜子/抽屉，把一个空间分隔成 3×2 六个格子收纳；墙面、隔板、底板都开孔减料（镂空），
正面外壁浮雕「苗壮制造」。

| 项 | 值 |
|---|---|
| 外廓 | **193.2 × 121.6 × 60.0 mm**（正面有浮雕，Y 向含凸起 122.4） |
| 内腔 | 189.2 × 117.6 × 58.0 mm（3×2 格，单格 62 × 58） |
| 壁/隔板/底板 | 2.0 / 1.6 / 2.0 mm（0.4 喷嘴 5 / 4 / 5 圈） |
| 镂空 | 墙面孔 25 + 底板孔 24 = **49 个孔**；最小韧带 6.0mm，孔顶平段 14mm（≤ 桥接上限 15） |
| 用料 | 解析 138.3 cm³ ≈ **171 g PLA / 约 6.9 h / 6.2 元**（外廓的 9.8%） |
| 打印姿态 | 底面整块贴床、全部竖直壁 → **免支撑、免桥接** |
| 自检 | `check.py` **32/32 全过** + `check_model.py` 全过（水密 / 绕序 / STL↔3MF） |

## 怎么跑

```bash
cd ~/.cah-data/skills/shared/3d-print-ideas/models/idea-017-lattice-drawer-divider
uv run --offline --python 3.13 --with cadgen==0.7.26 python build_mesh.py   # -> .stl + .3mf + -report.json
python3 check.py                                                            # 32 项物理断言
python3 ../../scripts/stl_preview.py lattice-divider.stl                     # 四联预览图
node ../../scripts/cost.mjs lattice-divider.stl --material PLA               # 克数/费用
```

> **为什么不是 OpenSCAD**：本机（macOS 27 / arm64）已无 Rosetta 2，`~/.cah-data/tools/OpenSCAD-2021.01.app`
> 是 x86_64 单架构二进制，内核直接 `Bad CPU type in executable` 拒绝执行，`scripts/scad_build.py` 调不动它。
> 实体改由 `build_mesh.py` 走 skill 里另一条已文档化的离线路线（uv 缓存里的 cadgen + build123d /
> OpenCASCADE）；**参数仍只写在 `model.scad` 一处**（build_mesh.py 通过 model.py 读它，自己不写常量）。
> 哪天有 arm64 版 OpenSCAD，`model.scad` 就是现成的复核入口。

## 文件归谁

| 文件 | 归谁 | 写什么 |
|---|---|---|
| `model.scad` | 这件模型 | 参数段（唯一数字来源）：格数/格宽/高度/壁厚/镂空尺度/品牌字尺寸 |
| `model.py` | 这件模型 | 派生尺寸链 + 孔位布局（那套「排几个孔、排多高」的规则）+ 解析体积 |
| `build_mesh.py` | 这件模型 | 建实体（含字体基线校验）、出 STL/3MF、调 check_model |
| `check.py` | 这件模型 | 32 条物理断言：尺寸链 / 可打印性 / 实物对账 |
| `lattice-divider-report.json` | 构建产物 | 实测包围盒、体积、字体校验、check_model 结果 |

## 改尺寸（量到柜格内径之后）

只改 `model.scad` 里这几行，然后重跑上面四条命令：

```
cells_x / cells_y     # 要几个格子（横向 / 纵向）
cell_w  / cell_d      # 单格内宽 / 内深
outer_h               # 总高
```

`check.py` 会自己重算孔位与韧带，并重新断言——不用手改孔的位置。

## 已知待确认（台账 idea-017 里同步记着）

1. 柜子/抽屉**内宽×内深×内高**：现在按常见柜格估的 3×2 格（193×122×60），量一个数就能贴合。
2. 要不要做**多件并排互卡**的模块版（几件 120×120 的小篮拼满更宽的柜子，更省料吃余料）。
3. 单格底板孔要不要留 1.5mm 薄底挡小件（钥匙/耳钉不掉下去）。
4. 品牌字放哪：正面外壁（现在）/ 底板内侧 / 每格内壁都刻一枚。
