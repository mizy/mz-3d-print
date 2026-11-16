#!/usr/bin/env python3
"""idea-013 白菜叶钥匙扣：把 model.scad 的参数/表落成实体（STL + 3MF）+ 回读自检。

**为什么不是 OpenSCAD**：这台机器（macOS 27 / arm64）已移除 Rosetta 2，
`~/.cah-data/tools/OpenSCAD-2021.01.app` 里是 x86_64 单架构二进制，内核直接
`Bad CPU type in executable` 拒绝执行 —— `scripts/scad_build.py` 调不动它。
于是改走本 skill 已文档化的另一条路（SKILL.md「一句话 → 模型」/ cad_model.sh 同款工具链）：
uv 缓存里的 cadgen + build123d（OpenCASCADE 内核，离线可跑）按**同一套参数**建实体。

model.scad 仍是唯一数字来源：本脚本的每个尺寸都从 model.load()（读 model.scad）取，
这里不写任何独立常量 —— 几何公式与 .scad 里的 hw()/vein_rows 一一对应。

跑法（离线，走 uv 缓存；等价于 cad_model.sh 的工具链）:
  uv run --offline --python 3.13 --with cadgen==0.7.26 python build_mesh.py
产物: leaf-keychain.stl（二进制）+ leaf-keychain.3mf（与 scad_build.py 同一套 3MF 写出）
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = Path.home() / ".cah-data/skills/shared/3d-print-ideas/scripts"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SCRIPTS))

import model as M  # noqa: E402 —— 尺寸/表都从 model.scad 来
import scad_build as SB  # noqa: E402 —— 3MF 写出复用 skill 里那一份
from build123d import Cylinder, Polygon, Pos, export_stl, extrude  # noqa: E402

NAME = "leaf-keychain"
TOL = 0.01          # 网格弦差（mm）：挂孔/波边不被切得比 0.4 喷嘴还糙
ANG_TOL = 0.2       # 角度弦差（rad）


def prism(pts, height):
    """从 (x,y) 点环拉出竖直棱柱，**统一**落在 z = 0..height（不管点序让法线朝哪）。"""
    body = extrude(Polygon(*[tuple(v) for v in pts], align=None), amount=height)
    return Pos(0, 0, height) * body if body.bounding_box().min.Z < -1e-6 else body


def build(p):
    solid = prism(M.closed_loop(p), p["leaf_t"])
    for row in p["veins"]:                       # 叶脉：沉进叶面 0.6mm 的凸棱
        solid += Pos(0, 0, p["leaf_t"] - p["vein_sink"]) * prism(M.vein_poly(row), p["vein_h"])
    hole = Pos(p["hole_x"], 0, p["leaf_t"] / 2) * Cylinder(p["hole_d"] / 2, p["leaf_t"] + 4)
    return solid - hole


def main():
    p = M.load()
    part = build(p)
    bb = part.bounding_box().size
    print(f"实体: 体积 {part.volume/1000:.3f}cm³  包围盒 "
          f"[{bb.X:.3f} {bb.Y:.3f} {bb.Z:.3f}] mm  valid={part.is_valid}")
    stl, three = HERE / f"{NAME}.stl", HERE / f"{NAME}.3mf"
    export_stl(part, str(stl), tolerance=TOL, angular_tolerance=ANG_TOL)
    SB.stl_to_3mf(stl, three, NAME)
    print(f"写出 {stl.name} {stl.stat().st_size/1e6:.3f}MB + {three.name} {three.stat().st_size/1e6:.3f}MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
