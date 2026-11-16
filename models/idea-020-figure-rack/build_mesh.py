#!/usr/bin/env python3
"""idea-020「小人晾架」：把 model.scad 的参数落成实体（STL + 3MF + 复核报告）。

**为什么不是 OpenSCAD**：本机（macOS 27 / arm64）已移除 Rosetta 2，
`~/.cah-data/tools/OpenSCAD-2021.01.app` 是 x86_64 单架构二进制，内核直接
`Bad CPU type in executable` 拒绝执行 —— `scripts/scad_build.py` 调不动它。
改走本 skill 已文档化的另一条路（SKILL.md「一句话 → 模型」/ cad_model.sh 同款工具链）：
uv 缓存里的 cadgen + build123d（OpenCASCADE 内核，离线可跑）。
`model.scad` 仍是唯一数字来源：每个尺寸都来自 model.load()，本文件不写常量；
**实体清单也只写一份**（model.primitives），build123d 照着建，
model.py 用同一份清单做体素积分 —— 形状不可能两边算岔。

跑法（离线，走 uv 缓存）:
  uv run --offline --python 3.13 --with cadgen==0.7.26 python build_mesh.py
产物:
  figure-rack.stl / .3mf     主件（一件打印、免支撑、无装配、纯重力固定）
  figure-rack-report.json    复核报告（OCC 体积/重心 + 体素对账 + check_model + 受力/稳定性）

接头处理：构件之间一律**体积咬合**（裙摆咬进底盘 1mm、躯干顶咬进头球 1mm、手臂埋进拳里），
不做共面贴合 —— OCC 并集不留退化面，包围盒严格等于参数（check.py 按 ±0.05 断言）。
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = Path.home() / ".cah-data/skills/shared/3d-print-ideas/scripts"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SCRIPTS))

import model as M  # noqa: E402
import scad_build as SB  # noqa: E402 —— 3MF 写出与 STL 复核复用 skill 里那一份
from build123d import (Box, CenterOf, Cone, Plane, Polygon, Pos, Rot,  # noqa: E402
                       Sphere, export_stl, extrude)

NAME = "figure-rack"
# 头球是唯一曲面：弦高按角度公差走（0.08rad ≈ 4.6° → 弦高 R(1-cos2.3°) ≈ 0.016mm），
# 这样 STL 体积与 OCC 体积差 < 0.1%；沿用 idea-018 的 0.3rad 会让球面掉 1.5% 体积。
TOL, ANG_TOL = 0.01, 0.08


def make_prism_z(m):
    """多边形截面沿 Z 挤出：底面贴 z0（挤出方向靠包围盒归一，不依赖多边形绕序）。"""
    s = extrude(Plane.XY * Polygon(*m["poly"]), amount=(m["z1"] - m["z0"]))
    bb = s.bounding_box()
    return Pos(-(bb.min.X + bb.max.X) / 2.0, -(bb.min.Y + bb.max.Y) / 2.0, m["z0"] - bb.min.Z) * s


def make_prism_y(m):
    """多边形截面沿 Y 挤出：截面的 u→X、v→Z，再整体摆到 (cx, y0..y1, cz)。"""
    s = extrude(Plane.XZ * Polygon(*m["poly"]), amount=(m["y1"] - m["y0"]))
    bb = s.bounding_box()
    return Pos(m["cx"] - (bb.min.X + bb.max.X) / 2.0, m["y1"] - bb.max.Y,
               m["cz"] - (bb.min.Z + bb.max.Z) / 2.0) * s


def make_frustum(m):
    """圆锥台：Cone 默认轴 = Z、居中；按 d（在 XZ 平面内）绕 Y 转到位。"""
    length, d = m["L"], m["d"]
    s = Cone(bottom_radius=m["r0"], top_radius=m["r1"], height=length)
    ang = math.degrees(math.atan2(d[0], d[2]))
    if abs(ang) > 1e-9:
        s = Rot(Y=ang) * s
    return Pos(m["o"][0] + d[0] * length / 2.0, m["o"][1] + d[1] * length / 2.0,
               m["o"][2] + d[2] * length / 2.0) * s


def make_member(m):
    if m["kind"] == "prism_z":
        return make_prism_z(m)
    if m["kind"] == "prism_y":
        return make_prism_y(m)
    if m["kind"] == "frustum":
        return make_frustum(m)
    if m["kind"] == "sphere_band":
        # 头上下一律用平面切（下刀埋进躯干、上刀切掉球极点）——球极点会让 OCC 三角化留重复有向边
        big = 4.0 * m["R"]
        return ((Pos(*m["c"]) * Sphere(m["R"]))
                & (Pos(m["c"][0], m["c"][1], m["z0"] + big / 2.0) * Box(big, big, big))
                & (Pos(m["c"][0], m["c"][1], m["z1"] - big / 2.0) * Box(big, big, big)))
    raise ValueError(m["kind"])


def build(p):
    members, cuts = p["members"], p["cuts"]
    part = make_member(members[0])
    for m in members[1:]:
        part = part + make_member(m)
    for c in cuts:
        tool = make_prism_z(c)
        if c.get("neg_poly"):
            tool = tool - make_prism_z({"poly": c["neg_poly"], "z0": c["z0"], "z1": c["z1"]})
        part = part - tool
    return part


def main():
    p = M.load()
    part = build(p)
    stl, three = HERE / f"{NAME}.stl", HERE / f"{NAME}.3mf"
    export_stl(part, str(stl), tolerance=TOL, angular_tolerance=ANG_TOL)
    SB.stl_to_3mf(stl, three, NAME)
    check = SB.check_stl(stl, three)
    bb = part.bounding_box().size
    com = part.center(CenterOf.MASS)
    print(f"[{NAME}] OCC 体积 {part.volume/1000:.3f}cm³（体素外推 {p['V_grid']/1000:.3f}，"
          f"构件和 {p['V_solids']/1000:.3f}）valid={part.is_valid}")
    print(f"          包围盒 [{bb.X:.3f} {bb.Y:.3f} {bb.Z:.3f}] vs 参数 {p['bbox']}；"
          f"重心 [{com.X:.2f} {com.Y:.2f} {com.Z:.2f}] vs 体素 {[round(v,2) for v in p['com_grid']]}")
    print(f"          {stl.name} {stl.stat().st_size/1e3:.1f}kB + {three.name} "
          f"{three.stat().st_size/1e3:.1f}kB  check_model failures={check.get('failures') or '无'}")

    v_cad = part.volume
    report = {
        "name": NAME, "idea": "idea-020",
        "design": "桌面发带晾架「小人晾架」：宽底盘（配重槽）+ Q 版小人（头/躯干/裙摆/双臂）+ "
                  "两只环握的拳各持一根前后向晾杆 + 4 个杆端挡边，一件打印、全程免支撑、无装配、纯重力固定",
        "bbox_mm": [round(v, 3) for v in (bb.X, bb.Y, bb.Z)],
        "bbox_param_mm": list(p["bbox"]),
        "volume": {
            "cad_occ_mm3": round(v_cad, 3),
            "grid_extrapolated_mm3": round(p["V_grid"], 3),
            "grid_samples_mm3": {k: round(v["volume_mm3"], 3) for k, v in p["grid"].items()
                                 if k.startswith("step")},
            "members_sum_mm3": round(p["V_solids"], 3),
            "outer_box_mm3": round(p["V_outer_box"], 3),
            "material_ratio": round(p["V_grid"] / p["V_outer_box"], 4),
        },
        "com_mm": {"cad_occ": [round(v, 3) for v in (com.X, com.Y, com.Z)],
                   "grid": [round(v, 3) for v in p["com_grid"]]},
        "mass_g": {k: round(v, 2) for k, v in p["mass_g"].items()},
        "mass_solids_overlap_g": {k: round(v, 2) for k, v in p["mass_solids_g"].items()},
        "foot_area_mm2": round(p["foot_area"], 1),
        "geometry": {
            "base_mm": [2 * p["base_rx"], 2 * p["base_ry"], p["base_h"]],
            "hub_mm": [2 * p["hub_rx"], 2 * p["hub_ry"]], "rim_w": p["rim_w"],
            "groove_w": p["groove_w"], "groove_d": p["groove_d"],
            "shoulder_w": p["shoulder_w"], "head_r": p["head_r"], "head_top": round(p["head_top"], 2),
            "head_emerge_r": round(p["head_emerge_r"], 2),
            "head_emerge_sin": round(p["head_emerge_sin"], 4),
            "bar_z": p["bar_z"], "bar_r": p["bar_r"], "bar_len": p["bar_len"],
            "bar_span_with_stops": p["bar_span"], "bar_pitch_mm": 2 * p["hand_x"],
            "stop_r": p["stop_r"], "stop_len": p["stop_len"],
            "hand_r": p["hand_r"], "hand_len": p["hand_len"],
            "arm_tilt_deg": round(p["strength"]["arm"]["tilt_deg"], 2),
        },
        "sections": {k: {kk: round(vv, 4) for kk, vv in v.items() if kk != "n_pts"}
                    for k, v in p["sec"].items()},
        "members": [{"name": m["name"], "kind": m["kind"], "volume_mm3": round(m["volume"], 1)}
                    for m in p["members"]],
        "strength": p["strength"],
        "stability": p["stability"],
        "use_case": {
            "bands_per_bar": p["bands_max"], "band_span_mm": p["band_span"],
            "wet_band_g": p["wet_band_g"], "ballast_g": p["ballast_g"],
            "load_y_tip_mm": round(p["y_tip"], 2), "load_x_mm": p["hand_x"],
            "ballast": p["ballast"],
        },
        "print_orientation": {
            "姿态": "模型坐标系即打印姿态：Z 向上、底盘底面贴床（z=0）",
            "supports": "不需要（见 check.py 的朝下平面/陡悬垂面积统计）",
            "min_feature_mm": min(p["bar_r"], p["rim_w"], p["groove_d"], 2 * p["arm_r_root"]),
        },
        "files": {"stl": stl.name, "three_mf": three.name, "stl_bytes": stl.stat().st_size,
                  "check_model": check},
    }
    out = HERE / f"{NAME}-report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(f"报告 -> {out.name}")

    bad = []
    if check.get("failures"):
        bad.append(f"check_model: {check['failures']}")
    for got, want, tag in ((bb.X, p["bbox"][0], "X"), (bb.Y, p["bbox"][1], "Y"), (bb.Z, p["bbox"][2], "Z")):
        if abs(got - want) > 0.05:
            bad.append(f"包围盒 {tag}: {got:.3f} vs 参数 {want:.3f}")
    if abs(v_cad - p["V_grid"]) > 0.01 * v_cad:
        bad.append(f"OCC 体积与体素外推差 {abs(v_cad-p['V_grid'])/v_cad:.2%} > 1%")
    d_com = math.dist((com.X, com.Y, com.Z), p["com_grid"])
    if d_com > 1.0:
        bad.append(f"重心 OCC 与体素差 {d_com:.2f}mm > 1mm")
    if bad:
        print("FAIL 对账：" + "; ".join(bad), file=sys.stderr)
        return 1
    print("对账：包围盒 = 参数 ✅  OCC 体积 = 体素外推 ✅  重心一致 ✅  check_model 全过 ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
