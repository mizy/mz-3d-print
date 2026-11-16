#!/usr/bin/env python3
"""idea-016 吉他拨片盒：把 model.scad 的参数/尺寸链落成实体（STL + 3MF）。

**为什么不是 OpenSCAD**：这台机器（macOS 27 / arm64）已移除 Rosetta 2，
`~/.cah-data/tools/OpenSCAD-2021.01.app` 是 x86_64 单架构二进制，内核直接
`Bad CPU type in executable` 拒绝执行 —— `scripts/scad_build.py` 调不动它。
改走本 skill 已文档化的另一条路（SKILL.md「一句话 → 模型」/ cad_model.sh 同款工具链）：
uv 缓存里的 cadgen + build123d（OpenCASCADE 内核，离线可跑），按**同一套参数/尺寸链**建实体。
model.scad 仍是唯一数字来源：每个尺寸都从 model.load()（读 model.scad）取。

跑法（离线，走 uv 缓存）:
  uv run --offline --python 3.13 --with cadgen==0.7.26 python build_mesh.py
产物: pick-case.stl（二进制，盒身 + 上盖两件排开一次打完）+ pick-case.3mf
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = Path.home() / ".cah-data/skills/shared/3d-print-ideas/scripts"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SCRIPTS))

import model as M  # noqa: E402
import scad_build as SB  # noqa: E402 —— 3MF 写出复用 skill 里那一份
from build123d import Polygon, Pos, RectangleRounded, export_stl, extrude  # noqa: E402

NAME = "pick-case"
TOL = 0.01
ANG_TOL = 0.2


def rounded_prism(w, d, r, height):
    """圆角矩形柱体：z 从 0 到 height。"""
    body = extrude(RectangleRounded(w, d, r), amount=height)
    if body.bounding_box().min.Z < -1e-6:
        body = Pos(0, 0, height) * body
    return body


def build(p):
    # ① 盒身：外圆角柱 - 内腔（内腔多切 1mm 保证开口面切干净）
    tray = rounded_prism(p["tray_w"], p["tray_d"], p["corner_r"], p["tray_h"]) - \
        Pos(0, 0, p["floor_t"]) * rounded_prism(p["cavity_l"], p["cavity_d"], p["cavity_r"], p["cavity_h"] + 1)
    tray = Pos(p["tray_w"] / 2, p["tray_d"] / 2, 0) * tray

    # ② 上盖（打印姿态：盖板贴床、裙边朝上）
    lid = rounded_prism(p["lid_ow"], p["lid_od"], p["lid_or"], p["lid_t"])
    skirt = rounded_prism(p["lid_ow"], p["lid_od"], p["lid_or"], p["skirt_h"]) - \
        rounded_prism(p["lid_iw"], p["lid_id"], p["lid_ir"], p["skirt_h"] + 1)
    lid = lid + Pos(0, 0, p["lid_t"]) * skirt
    lid = Pos(p["tray_w"] + p["pack_gap"] + p["lid_ow"] / 2, p["lid_od"] / 2, 0) * lid
    return tray + lid


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
