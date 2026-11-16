#!/usr/bin/env python3
"""idea-017 镂空分隔收纳篮（苗壮制造）：把 model.scad 的参数/孔位落成实体（STL + 3MF）。

**为什么不是 OpenSCAD**：本机（macOS 27 / arm64）已移除 Rosetta 2，
`~/.cah-data/tools/OpenSCAD-2021.01.app` 是 x86_64 单架构二进制，内核直接
`Bad CPU type in executable` 拒绝执行 —— `scripts/scad_build.py` 调不动它。
改走本 skill 已文档化的另一条路（SKILL.md「一句话 → 模型」/ cad_model.sh 同款工具链）：
uv 缓存里的 cadgen + build123d（OpenCASCADE 内核，离线可跑），按**同一套参数/孔位**建实体。
`model.scad` 仍是唯一数字来源：每个尺寸都来自 model.load()。

跑法（离线，走 uv 缓存）:
  uv run --offline --python 3.13 --with cadgen==0.7.26 python build_mesh.py
产物: lattice-divider.stl（二进制）+ lattice-divider.3mf + lattice-divider-report.json

字体校验（照 make_text3d.py 的套路，但换成面积/体积基线）：先拿一个不存在的字体路径
编译同一串字，几何一模一样就说明「字体其实没生效」→ 直接失败（中文会静默变方框，不报错）。
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = Path.home() / ".cah-data/skills/shared/3d-print-ideas/scripts"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SCRIPTS))

import model as M  # noqa: E402
import scad_build as SB  # noqa: E402 —— 3MF 写出与 STL 复核复用 skill 里那一份
from build123d import (  # noqa: E402
    Align, Box, Cylinder, Pos, RectangleRounded, Rot, Text, extrude, export_stl,
)

NAME = "lattice-divider"
TOL = 0.02
ANG_TOL = 0.3
BOGUS_FONT = "/nonexistent/__no_such_font__.ttf"


def prism(w, d, r, height):
    """圆角矩形柱：z 从 0 到 height，中心在 X/Y 原点。"""
    return extrude(RectangleRounded(w, d, r), amount=height)


def louver(desc, w, h, r):
    """一块「墙厚方向贯通」的圆角长孔实体（两端各多切 1mm，保证切透）。"""
    body = prism(w, h, r, desc["t"] + 2)                 # 局部：长 w 沿 X、高 h 沿 Y、厚沿 Z
    body = Pos(0, (desc["t"] + 2) / 2.0, 0) * (Rot(X=90) * body)   # 摆成：长沿 X、高沿 Z、厚沿 Y（居中）
    if desc["dir"] == "x":                               # 左/右墙与垂直于 X 的隔板：长边转到 Y
        body = Rot(Z=90) * body
    return Pos(desc["x"], desc["y"], desc["z"]) * body


def brand_text_solid(p):
    """「苗壮制造」凸起字：字高按 brand_cap_h 反推 font_size（不写死字号）。"""
    probe = Text(p["brand_text"], font_size=100, font_path=p["brand_font"])
    probe_h = probe.bounding_box().size.Y                    # CJK 字形基本满 em
    font_size = 100.0 * p["brand_cap_h"] / probe_h
    sketch = Text(p["brand_text"], font_size=font_size, font_path=p["brand_font"],
                  align=(Align.CENTER, Align.CENTER))
    bb = sketch.bounding_box().size
    solid = extrude(sketch, amount=p["brand_raise"] + 1.0)   # 多切 1mm 埋进墙里，union 才连得住
    solid = Rot(X=90) * solid                                # 局部 +Z(挤出方向) -> -Y，字头仍在 +Z
    return Pos(0, -p["outer_d"] / 2.0 + 1.0, p["brand_z"]) * solid, {"font_size": font_size,
                                                                    "width": bb.X, "height": bb.Y}


def font_baseline_check(p):
    """字体是否真生效：换一个不存在的字体路径，几何必须不一样（一样 = 悄悄退成默认字体）。"""
    good = Text(p["brand_text"], font_size=100, font_path=p["brand_font"])
    bad = Text(p["brand_text"], font_size=100, font_path=BOGUS_FONT)
    gv, bv = good.bounding_box().size, bad.bounding_box().size
    ok = abs(gv.X - bv.X) > 0.5 or abs(gv.Y - bv.Y) > 0.5
    return {"ok": bool(ok), "real_bbox": [round(gv.X, 3), round(gv.Y, 3)],
            "bogus_bbox": [round(bv.X, 3), round(bv.Y, 3)]}


def build(p):
    # ① 壳 = 外圆角柱 - 内腔（内腔多切 1mm，保证开口面切干净）
    part = prism(p["outer_w"], p["outer_d"], p["corner_r"], p["outer_h"]) \
        - Pos(0, 0, p["floor_t"]) * prism(p["inner_w"], p["inner_d"], p["cavity_r"], p["cavity_h"] + 1)
    # ② 内隔板（与外壁同高，只有竖直面）
    for i in range(1, p["cells_x"]):
        dx = -p["inner_w"] / 2 + i * p["cell_w"] + (i - 0.5) * p["divider_t"]
        part = part + Pos(dx, 0, p["floor_t"] + p["cavity_h"] / 2) * Box(p["divider_t"], p["inner_d"], p["cavity_h"])
    for j in range(1, p["cells_y"]):
        dy = -p["inner_d"] / 2 + j * p["cell_d"] + (j - 0.5) * p["divider_t"]
        part = part + Pos(0, dy, p["floor_t"] + p["cavity_h"] / 2) * Box(p["inner_w"], p["divider_t"], p["cavity_h"])
    # ③ 品牌浮雕（先并上去，④ 的孔不会切到正面实心墙上）
    text_solid, text_info = brand_text_solid(p)
    part = part + text_solid
    # ④ 镂空：墙面长孔 + 底板圆孔（一次并成一块再减，省布尔次数）
    cuts = [louver(d, p["louver_w"], p["louver_h"], p["louver_r"]) for d in p["louvers"]]
    cuts += [Pos(h["x"], h["y"], p["floor_t"] / 2.0)
             * Cylinder(p["bottom_hole_d"] / 2.0, p["floor_t"] + 2) for h in p["bottom_holes"]]
    part = part - cuts
    return part, text_info


def main():
    p = M.load()
    baseline = font_baseline_check(p)
    print(f"字体基线: real={baseline['real_bbox']} bogus={baseline['bogus_bbox']} ok={baseline['ok']}")
    if not baseline["ok"]:
        print("FAIL 字体没生效（中文会静默变方框）：换一条能出汉字的字体路径再跑", file=sys.stderr)
        return 1

    part, text_info = build(p)
    bb = part.bounding_box().size
    print(f"实体: 体积 {part.volume/1000:.3f}cm³  包围盒 [{bb.X:.3f} {bb.Y:.3f} {bb.Z:.3f}] mm "
          f"valid={part.is_valid}")
    print(f"品牌字「{p['brand_text']}」font_size={text_info['font_size']:.2f} "
          f"幅面 {text_info['width']:.2f} x {text_info['height']:.2f} mm（目标字高 {p['brand_cap_h']}）")

    stl, three, report_path = HERE / f"{NAME}.stl", HERE / f"{NAME}.3mf", HERE / f"{NAME}-report.json"
    export_stl(part, str(stl), tolerance=TOL, angular_tolerance=ANG_TOL)
    SB.stl_to_3mf(stl, three, NAME)
    check = SB.check_stl(stl, three)
    report = {
        "name": NAME, "idea": "idea-017",
        "outer_mm": [round(p["outer_w"], 3), round(p["outer_d"], 3), round(p["outer_h"], 3)],
        "inner_mm": [round(p["inner_w"], 3), round(p["inner_d"], 3), round(p["cavity_h"], 3)],
        "volume_mm3": round(part.volume, 2),
        "volume_no_text_mm3": round(p["V_no_text"], 2),
        "bbox_mm": [round(bb.X, 3), round(bb.Y, 3), round(bb.Z, 3)],
        "counts": {"louvers": len(p["louvers"]), "bottom_holes": len(p["bottom_holes"])},
        "brand": {"text": p["brand_text"], "font": p["brand_font"],
                  "raise": p["brand_raise"], "cap_h": p["brand_cap_h"],
                  **{k: round(v, 4) if isinstance(v, float) else v for k, v in text_info.items()},
                  "baseline": baseline},
        "check_model": check,
        "files": {"stl": stl.name, "three_mf": three.name, "stl_bytes": stl.stat().st_size},
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(f"写出 {stl.name} {stl.stat().st_size/1e6:.3f}MB + {three.name} {three.stat().st_size/1e6:.3f}MB "
          f"+ {report_path.name}")
    fails = check.get("failures") or []
    if fails:
        print(f"FAIL check_model: {fails}", file=sys.stderr)
        for f in (stl, three):
            f.unlink(missing_ok=True)                        # 自检不过不留半成品
        return 1
    print("check_model: 全过 ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
