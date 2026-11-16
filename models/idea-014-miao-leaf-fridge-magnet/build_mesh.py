#!/usr/bin/env python3
"""idea-014 白菜叶冰箱贴：把 model.scad 的参数/表落成实体（STL + 3MF）。

**为什么不是 OpenSCAD**：这台机器（macOS 27 / arm64）已移除 Rosetta 2，
`~/.cah-data/tools/OpenSCAD-2021.01.app` 是 x86_64 单架构二进制，内核直接
`Bad CPU type in executable` 拒绝执行 —— `scripts/scad_build.py` 调不动它。
改走本 skill 已文档化的另一条路（SKILL.md「一句话 → 模型」/ cad_model.sh 同款工具链）：
uv 缓存里的 cadgen + build123d（OpenCASCADE 内核，离线可跑），按**同一套参数**建实体。
model.scad 仍是唯一数字来源：每个尺寸都从 model.load()（读 model.scad）取。

跑法（离线，走 uv 缓存）:
  uv run --offline --python 3.13 --with cadgen==0.7.26 python build_mesh.py
产物: leaf-fridge-magnet.stl（二进制）+ leaf-fridge-magnet.3mf
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = Path.home() / ".cah-data/skills/shared/3d-print-ideas/scripts"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SCRIPTS))

import model as M  # noqa: E402
import scad_build as SB  # noqa: E402 —— 3MF 写出复用 skill 里那一份
from build123d import Cylinder, Polygon, Pos, export_stl, extrude  # noqa: E402

NAME = "leaf-fridge-magnet"
TOL = 0.01
ANG_TOL = 0.2


def prism(pts, height):
    """从 (x,y) 点环拉出竖直棱柱，统一落在 z = 0..height。"""
    body = extrude(Polygon(*[tuple(v) for v in pts], align=None), amount=height)
    return Pos(0, 0, height) * body if body.bounding_box().min.Z < -1e-6 else body


def build(p):
    solid = prism(M.closed_loop(p), p["leaf_t"])
    for row in p["veins"]:
        solid += Pos(0, 0, p["leaf_t"] - p["vein_sink"]) * prism(M.vein_poly(row), p["vein_h"])
    # 磁铁槽：从背面（z=0）往上切 pocket_depth，槽底再往外多切 1mm 保证布尔切干净
    for q in p["pockets"]:
        solid -= Pos(q["cx"], q["cy"], (p["pocket_depth"] - 1) / 2) * \
            Cylinder(p["pocket_d"] / 2, p["pocket_depth"] + 1)
    return solid


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
