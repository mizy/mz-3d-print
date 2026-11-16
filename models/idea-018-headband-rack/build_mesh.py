#!/usr/bin/env python3
"""idea-018 桌面发带晾晒架「龙门晾架」：把 model.scad 的参数落成实体（STL + 3MF + 报告）。

**为什么不是 OpenSCAD**：本机（macOS 27 / arm64）已移除 Rosetta 2，
`~/.cah-data/tools/OpenSCAD-2021.01.app` 是 x86_64 单架构二进制，内核直接
`Bad CPU type in executable` 拒绝执行 —— `scripts/scad_build.py` 调不动它。
改走本 skill 已文档化的另一条路（SKILL.md「一句话 → 模型」/ cad_model.sh 同款工具链）：
uv 缓存里的 cadgen + build123d（OpenCASCADE 内核，离线可跑），按**同一套参数**建实体。
`model.scad` 仍是唯一数字来源：每个尺寸都来自 model.load()。

跑法（离线，走 uv 缓存）:
  uv run --offline --python 3.13 --with cadgen==0.7.26 python build_mesh.py
产物:
  headband-rack.stl / .3mf         主件（一件打印、免支撑、无装配）
  headband-hook.stl / .3mf         可选配件（挂杆小钩）
  headband-rack-report.json        复核报告（check_model 原始输出 + 解析体积 + 受力/翻倒）

几何全部是**平面多面体**（矩形柱 + 楔形柱），没有曲面 —— 所以 STL 的体积应该和
解析体积（model.py 的切片积分）几乎完全一致，check.py 按 0.3% 断言。
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
from build123d import Box, Plane, Polygon, Pos, Rot, export_stl, extrude  # noqa: E402

RACK, HOOK = "headband-rack", "headband-hook"
TOL, ANG_TOL = 0.02, 0.3
# 主件接头**按参数精确相接**：构件之间本来就是「互相咬进去」的体积重叠（底环四角、立柱穿过
# 底环、晾杆两端埋进立柱顶），不是共面贴合，OCC 并集不会留退化面 —— 包围盒严格等于参数
# （check.py 按 ±0.05 断言）。配件那几块板之间是真正的共面接缝，刻意嵌进 model.HOOK_EMBED
# 的深度（藏在钩体肚子里，看不见）；配件的解析体积由 model.hook_volume() 用同一套坐标算。
H_EMBED = M.HOOK_EMBED


def wedge(top_w, bot_w, h, length, axis="x"):
    """楔形棱柱：截面在 (u=水平, v=+Z) 平面，上宽 top_w、下缘 bot_w、高 h；沿 axis 方向长 length、居中。"""
    pts = M.wedge_section(top_w, bot_w, h)["pts"]
    solid = extrude(Plane.YZ * Polygon(*pts), amount=length)
    solid = Pos(-length / 2.0, 0, 0) * solid
    return Rot(Z=90) * solid if axis == "y" else solid


def build_rack(p):
    xc, ox, oy = p["x_center"], p["outer_x"], p["outer_y"]
    bz, pz, bh = p["bar_center_z"], p["post_top"], p["base_h"]
    solids = []
    for sx in (-1, 1):                                   # 底座环：2 根纵杆（沿 Y）
        solids.append(Pos(sx * xc, 0, bh / 2.0) * Box(p["frame_t"], oy, bh))
    for sy in (-1, 1):                                   # 底座环：2 根横杆（沿 X）
        solids.append(Pos(0, sy * p["bar_y_spacing"], bh / 2.0) * Box(ox, p["base_w"], bh))
    for sx in (-1, 1):                                   # 6 根立柱（顶面 = post_top）
        for by in p["bar_ys"]:
            solids.append(Pos(sx * xc, by, pz / 2.0) * Box(p["frame_t"], p["post_w"], pz))
    for by in p["bar_ys"]:                               # 3 根晾杆（沿 X，两端与立柱外面平齐）
        solids.append(Pos(0, by, bz) * wedge(p["bar_top_w"], p["bar_bot_w"], p["bar_h"], ox))
    for sx in (-1, 1):                                   # 2 根侧梁（沿 Y，两端搭在立柱中心）
        solids.append(Pos(sx * xc, 0, bz)
                      * wedge(p["bar_top_w"], p["bar_bot_w"], p["bar_h"],
                              2.0 * p["bar_y_spacing"] + p["post_w"], axis="y"))
    part = solids[0]
    for s in solids[1:]:
        part = part + s
    return part, len(solids)


def build_hook(p):
    """挂杆小钩：坐在晾杆上平面上，两片限位翼夹住上平面定心，一侧垂一根小尖钩。
    建模坐标 = 使用姿态（杆顶面 z=0、杆轴心线 y=0）；最后整体翻过来（打印姿态：板贴床、钩朝上）。"""
    inner = p["bar_top_w"] + 2.0 * p["hook_fit"]                 # 两翼内壁净宽
    body_y = inner + 2.0 * p["hook_flange"]
    t, fh, ft = p["hook_body_t"], p["hook_flange_h"], p["hook_flange"]
    solids = [Pos(0, 0, -t / 2.0) * Box(p["hook_x"], body_y, t)]
    for sy in (-1, 1):                                           # 限位翼：上端埋进钩体 H_EMBED（共面接缝改成体积重叠）
        cy = sy * (inner + ft) / 2.0
        solids.append(Pos(0, cy, -t - fh / 2.0 + H_EMBED / 2.0) * Box(p["hook_x"], ft, fh + H_EMBED))
    prong = Pos(0, body_y / 2.0 - p["hook_prong_t"] / 2.0,
                -t - p["hook_prong_h"] / 2.0 + H_EMBED / 2.0) * Box(p["hook_prong_w"], p["hook_prong_t"],
                                                                     p["hook_prong_h"] + H_EMBED)
    solids.append(prong)
    part = solids[0]
    for s in solids[1:]:
        part = part + s
    return Rot(X=180) * part, len(solids)          # 翻过来：板贴床、两翼与小钩朝上（免支撑）


def emit(part, name, note):
    stl, three = HERE / f"{name}.stl", HERE / f"{name}.3mf"
    export_stl(part, str(stl), tolerance=TOL, angular_tolerance=ANG_TOL)
    SB.stl_to_3mf(stl, three, name)
    check = SB.check_stl(stl, three)
    bb = part.bounding_box().size
    print(f"[{name}] 体积 {part.volume/1000:.3f}cm³ 包围盒 [{bb.X:.3f} {bb.Y:.3f} {bb.Z:.3f}] "
          f"valid={part.is_valid}  {note}")
    print(f"          {stl.name} {stl.stat().st_size/1e3:.1f}kB + {three.name} "
          f"{three.stat().st_size/1e3:.1f}kB  check_model failures={check.get('failures') or '无'}")
    return {"stl": stl.name, "three_mf": three.name, "stl_bytes": stl.stat().st_size,
            "volume_cad_mm3": round(part.volume, 3),
            "bbox_cad_mm": [round(v, 3) for v in (bb.X, bb.Y, bb.Z)],
            "check_model": check}


def main():
    p = M.load()
    rack, n_rack = build_rack(p)
    hook, n_hook = build_hook(p)
    files = {"rack": emit(rack, RACK, f"主件：{n_rack} 根构件并成一件"),
             "hook": emit(hook, HOOK, f"可选配件：{n_hook} 个体块并成一件")}

    hbb = hook.bounding_box().size
    report = {
        "name": RACK, "idea": "idea-018",
        "design": "桌面龙门晾架：底座环 + 6 立柱 + 3 晾杆 + 2 侧梁，一件打印、免支撑、无装配",
        "bbox_mm": [round(p["outer_x"], 3), round(p["outer_y"], 3), round(p["post_top"], 3)],
        "clear_mm": {"x": round(p["clear_x"], 3), "z_under_bar": round(p["bar_bot_z"], 3),
                     "y_between_rails": round(p["outer_y"] - 2.0 * p["base_w"], 3)},
        "volume_analytic_mm3": round(p["V_analytic"], 3),
        "volume_samples_mm3": {k: round(v, 3) for k, v in p["V_samples"].items()},
        "volume_solids_mm3": round(p["V_solids"], 3),
        "joint_overlap_mm3": round(p["overlap_mm3"], 3),
        "material_ratio": round(p["volume_ratio"], 4),
        "mass_g": {k: round(v, 2) for k, v in p["mass_g"].items()},
        "com_mm": [0.0, round(p["com_y"], 3), round(p["com_z"], 3)],
        "foot_area_mm2": round(p["foot_area"], 1),
        "members": [{"name": m["name"], "len": round(m["len"], 2), "area_mm2": round(m["area"], 2),
                     "vol_mm3": round(m["vol"], 1)} for m in p["members"]],
        "section": p["load"]["section"],
        "load": p["load"],
        "tipping": p["tipping"],
        "bridge": p["bridge"],
        "print_orientation": {
            "姿态": "模型坐标系即打印姿态：Z 向上、底座环贴床", "supports": "不需要",
            "bridges": f"{p['bridge']['count']} 条 {p['bridge']['strip_w']}mm 宽细棱，"
                       f"跨 {p['bridge']['bar_span']:.0f}mm(晾杆) / {p['bridge']['beam_span']:.0f}mm(侧梁)",
            "min_feature_mm": min(p["frame_t"], p["post_w"], p["base_w"], p["base_h"], p["bar_bot_w"]),
        },
        "hook": {
            "bbox_mm": [round(v, 3) for v in (hbb.X, hbb.Y, hbb.Z)],
            "inner_gap_mm": round(p["bar_top_w"] + 2.0 * p["hook_fit"], 2),
            "prong_len_mm": p["hook_prong_h"], "per_plate": 4,
            "volume_analytic_mm3": round(M.hook_volume(p), 1),
        },
        "files": files,
    }
    out = HERE / f"{RACK}-report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(f"报告 -> {out.name}")
    bad = [k for k, v in files.items() if (v["check_model"].get("failures") or [])]
    if bad:
        print(f"FAIL check_model: {bad}", file=sys.stderr)
        return 1
    print("check_model: 两份都过 ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
