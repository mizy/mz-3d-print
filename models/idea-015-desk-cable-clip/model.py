#!/usr/bin/env python3
"""idea-015 桌面理线夹（三规格）：解析 model.scad -> 派生量（check.py / 成本估算共用一份）。

数字只在 model.scad 写一遍。这里按同一套式子重算每颗夹子的剖面与体积：
  孔中心高 z_axis = tape_base + d/2
  总高     h      = tape_base + d + top_wall
  总宽     dd     = d + 2*side_wall
  卡入口宽 slot   = slot_ratio * d（< d 才有卡持）
并把「三颗沿 X 排开」的整盘包围盒、贴胶面面积、解析体积算出来给 check.py 对账。

派生量：
  clips[]       每规格：d / h / dd / 孔中心高 / 卡入口宽 / 喇叭顶宽 / 最陡悬垂角 /
                剖面面积 / 体积 / 单件外廓
  pack          整盘：外廓、贴胶面积合计、解析体积合计
  V_analytic    整盘解析体积（= Σ 剖面面积×clip_w）
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SCAD = HERE / "model.scad"
sys.path.insert(0, str(Path.home() / ".cah-data/skills/shared/3d-print-ideas/scripts"))
from scad_params import read_params  # noqa: E402

CLIP_COLS = ["name", "d", "x0"]


def read_table(text, table_name, cols):
    block = re.search(rf"^\s*{table_name}\s*=\s*\[(.*?)^\s*\];", text, re.M | re.S)
    if not block:
        raise SystemExit(f"model.scad 里找不到表 {table_name}")
    rows = []
    for raw in block.group(1).splitlines():
        line = raw.split("//", 1)[0].strip().rstrip(",")
        if not line:
            continue
        m = re.match(r'^\[\s*"([^"]+)"\s*,(.*)\]$', line)
        if not m:
            raise SystemExit(f"{table_name} 里有解析不了的行: {raw.strip()}")
        name, rest = m.group(1), m.group(2)
        nums = [float(v) for v in rest.split(",") if v.strip() != ""]
        if len(nums) != len(cols) - 1:
            raise SystemExit(f"{table_name} 行「{name}」列数 {len(nums)+1} != 规定 {len(cols)}")
        rows.append(dict(zip(cols, [name] + nums)))
    return rows


def clip_geom(d, p):
    """一颗夹子的尺寸与关键角度（与 model.scad 的 z_axis_of/h_of/dd_of 同式）。"""
    r = d / 2.0
    z_axis = p["tape_base"] + r
    h = p["tape_base"] + d + p["top_wall"]
    dd = d + 2 * p["side_wall"]
    slot = p["slot_ratio"] * d
    ys = slot / 2.0
    zc = z_axis + math.sqrt(max(r * r - ys * ys, 0.0))       # 槽壁与孔壁交点高度
    yf = ys + p["flare_h"] * math.tan(math.radians(p["flare_ang"]))
    # 最陡的朝下悬垂面：孔壁在槽口那一点，其法线离水平的角度 = asin(zc - z_axis)/r 的余角
    overhang = math.degrees(math.atan2(zc - z_axis, ys))
    return {"d": d, "r": r, "z_axis": z_axis, "h": h, "dd": dd, "slot": slot,
            "z_c": zc, "y_flare": yf, "overhang_deg": overhang,
            "slot_wall_h": h - zc, "flare_top_w": 2 * yf}


def profile(d, p):
    """一颗夹子的 YZ 剖面点（(y, z)，逆时针，单一闭合多边形：窄槽把孔和外界连通，
    所以剖面是单连通、无内孔）。顺序：贴胶面左下 -> 左外壁 -> 左肩 -> 喇叭 -> 槽壁
    -> 沿孔壁绕到下 -> 右侧镜像 -> 贴胶面右下。"""
    g = clip_geom(d, p)
    r, ys, z_axis, h, dd = g["r"], g["slot"] / 2.0, g["z_axis"], g["h"], g["dd"]
    yf, zf = g["y_flare"], h - p["flare_h"]
    al = math.asin(min(1.0, ys / r))                 # 槽壁与孔壁的交点角
    pts = [(-dd / 2, 0.0), (-dd / 2, h), (-yf, h), (-ys, zf), (-ys, g["z_c"])]
    n = int(p["arc_facets"])
    sweep0, sweep1 = math.pi / 2 + al, 5 * math.pi / 2 - al   # 左交点 -> 绕底部 -> 右交点
    for k in range(1, n + 1):
        ang = sweep0 + (sweep1 - sweep0) * k / n
        pts.append((r * math.cos(ang), z_axis + r * math.sin(ang)))
    pts += [(ys, zf), (yf, h), (dd / 2, h), (dd / 2, 0.0)]
    return np.array(pts)


def shoelace(loop):
    x, y = loop[:, 0], loop[:, 1]
    return abs(float(np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y))) / 2.0


def load():
    p = read_params(SCAD)
    rows = read_table(SCAD.read_text(), "clip_rows", CLIP_COLS)
    clips = []
    for row in rows:
        g = clip_geom(row["d"], p)
        poly = profile(row["d"], p)
        area = shoelace(poly)
        g.update({"name": row["name"], "x0": row["x0"], "section_area": area,
                  "volume": area * p["clip_w"], "tape_area": p["clip_w"] * g["dd"],
                  "bbox": (p["clip_w"], g["dd"], g["h"])})
        clips.append(g)
    pack_x = (max(g["x0"] for g in clips) + p["clip_w"]) - min(g["x0"] for g in clips)
    p.update({
        "clips": clips,
        "clip_count": len(clips),
        "pack_x": pack_x,
        "pack_y": max(g["dd"] for g in clips),
        "pack_z": max(g["h"] for g in clips),
        "tape_area_total": sum(g["tape_area"] for g in clips),
        "V_analytic": sum(g["volume"] for g in clips),
        "overhang_max": max(g["overhang_deg"] for g in clips),
        "min_dd": min(g["dd"] for g in clips),
    })
    return p


def main(argv):
    ap = argparse.ArgumentParser(add_help=True, description="idea-015 派生量")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    p = load()
    if a.out:
        Path(a.out).write_text(json.dumps(p, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n")
    if a.json:
        print(json.dumps(p, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"整盘外廓 {p['pack_x']:.1f} x {p['pack_y']:.1f} x {p['pack_z']:.1f} mm，"
              f"{p['clip_count']} 颗，间距 {p['pack_gap']:.0f}mm")
        for g in p["clips"]:
            print(f"  {g['name']:6s} 线径 φ{g['d']:.0f}  单件 {g['bbox'][0]:.0f}x{g['bbox'][1]:.1f}x{g['bbox'][2]:.1f}"
                  f"  孔中心高 {g['z_axis']:.1f}  卡入口 {g['slot']:.2f}  喇叭顶 {g['flare_top_w']:.2f}"
                  f"  最陡悬垂 {g['overhang_deg']:.1f}°  体积 {g['volume']/1000:.2f}cm³")
        print(f"  贴胶面合计 {p['tape_area_total']:.0f}mm²，解析体积 {p['V_analytic']/1000:.2f}cm³"
              f"（≈{p['V_analytic']/1000*1.24:.2f}g PLA）")
        if a.out:
            print(f"派生量 -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
