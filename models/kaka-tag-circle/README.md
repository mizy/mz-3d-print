# kaka-tag-circle（Ø45.7 圆形吊牌，定稿 2026-11-05）

成品与设计说明见 `../../docs/case-kaka-tag-circle.md`。这里只放能重跑的脚本。

| 文件 | 作用 |
|---|---|
| `build_kaka_tag_circle.py` | 从带横幅母版重建圆形几何：切掉下方横幅、重算包边、去掉正面名字、背面开 0.6 mm 镜像凹槽、XY 缩放到 60 mm 高 |
| `render_preview.py` | 真几何三格预览（正面 / 背面 / 背面斜视），输出 `kaka-circle-preview.png` |

## 依赖与运行

```bash
uv run --python 3.12 --with trimesh --with manifold3d --with shapely --with fonttools \
  --with matplotlib --with scipy --with networkx --with rtree \
  python3 build_kaka_tag_circle.py

uv run --python 3.12 --with trimesh --with numpy --with pillow python3 render_preview.py
```

两个脚本里的 `D` 都写死为
`/Users/mizy/projects/claude-agent-hub/outputs/dog-tag-kaka`（母版 `parametric-{white,gray,black}.stl`
与 `name.stl` 必须在该目录）。换机器先改这个常量。

## 产物

`kaka-circle-white.stl` / `-gray.stl` / `-black.stl` / `kaka-circle.stl` / `kaka-circle.json` /
`kaka-circle-preview.png`，全部同目录。

## 三条不能改的约束

1. **背面文字必须镜像**（`shapely.affinity.scale(xfact=-1)`），否则从背后是反字。
2. **凹槽开在贴床面**（`z=-0.1…0.6`），不做在顶面；这样不用支撑，字口最锐。
3. **XY 缩放不改 Z**：整件缩到 60 mm 高时 `vertices[:, :2] *= s`，厚度 3.2 和 0.2 层高都保持。
