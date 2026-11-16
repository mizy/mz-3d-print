#!/usr/bin/env python3
"""idea-014 白菜叶冰箱贴：解析 model.scad 参数 -> 派生量（check.py / 成本估算共用一份）。

数字只在 model.scad 写一遍；这里照**同一套公式**在 Python 侧重算轮廓、
磁铁槽留边与体积，给 check.py 拿去和 STL 实测对账。

派生量：
  BBOX_X/Y/Z    期望包围盒（Y 由轮廓最大半宽算得）
  plate_area    叶片轮廓面积（鞋带公式，精确）
  vein_union    叶脉在叶面内的并集面积（扫描线栅格）
  V_analytic    = 板面积×板厚 + 叶脉并集×露出 - 槽数×πr²×槽深（STL 体积应与之吻合）
  pocket_edge   每个槽圆周到轮廓的最小净壁厚（负 = 槽出界）
  pocket_gap    两槽最近边距（不相交才装得下两颗磁铁）
  pocket_ceiling= 板厚 - 槽深（槽顶剩料，FDM 里就是那片桥接盖）
  bridge_area   两槽顶的圆面积合计（水平桥接面，理论上不需要支撑）
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

VEIN_COLS = ["name", "x0", "ang", "length", "w0", "w1"]
POCKET_COLS = ["name", "cx", "cy"]


def read_table(text, table_name, cols):
    """读 `table_name = [ ["名字", 数字...], ... ];`，列数不对就报错（不静默少读一行）。"""
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


def hw(u, p):
    s = math.sin(math.pi * u ** p["shape_p"]) ** p["shape_q"]
    return p["stem_hw"] + (p["half_w"] - p["stem_hw"]) * s * \
        (1 + p["wave_amp"] * math.sin(2 * math.pi * p["wave_n"] * u))


def outline(p):
    n = int(p["samples"])
    return np.array([[p["leaf_len"] * i / n, hw(i / n, p)] for i in range(n + 1)])


def closed_loop(p):
    top = outline(p)
    return np.vstack([top, top[-2:0:-1] * np.array([1.0, -1.0])])


def shoelace(loop):
    x, y = loop[:, 0], loop[:, 1]
    return abs(float(np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y))) / 2.0


def vein_poly(row):
    """叶脉条带（梯形）的 4 个角点，按 +法线侧去、-法线侧回的顺序（不自交）。"""
    ang = math.radians(row["ang"])
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    for t, w in ((0.0, row["w0"]), (1.0, row["w1"]), (1.0, row["w1"]), (0.0, row["w0"])):
        cx, cy = row["x0"] + t * row["length"] * ca, t * row["length"] * sa
        half = w / 2.0
        side = 1.0 if len(pts) < 2 else -1.0
        pts.append((cx - side * sa * half, cy + side * ca * half))
    return np.array(pts)


def _raster(poly, xs, ys, res):
    P = np.asarray(poly, float)
    a, b = P, np.roll(P, -1, axis=0)
    xa, ya, xb, yb = a[:, 0], a[:, 1], b[:, 0], b[:, 1]
    Y = ys[:, None]
    cond = ((ya <= Y) & (Y < yb)) | ((yb <= Y) & (Y < ya))
    denom = np.where(yb == ya, 1.0, yb - ya)
    X = np.where(cond, xa + (Y - ya) / denom * (xb - xa), np.nan)
    Xs = np.sort(X, axis=1)
    left, right = Xs[:, 0::2], Xs[:, 1::2]
    ok = np.isfinite(left) & np.isfinite(right)
    left, right = np.nan_to_num(left), np.nan_to_num(right)
    li = np.clip(np.ceil((left - xs[0]) / res).astype(np.int64), 0, len(xs))
    ri = np.clip(np.floor((right - xs[0]) / res).astype(np.int64) + 1, 0, len(xs))
    acc = np.zeros((len(ys), len(xs) + 1), dtype=np.int32)
    rows = np.broadcast_to(np.arange(len(ys))[:, None], li.shape)
    np.add.at(acc, (rows[ok], li[ok]), 1)
    np.add.at(acc, (rows[ok], ri[ok]), -1)
    return np.cumsum(acc, axis=1)[:, :-1] % 2 == 1


def vein_union_area(p, veins, res=0.01):
    if not veins:
        return 0.0
    lo = min(min(v["x0"], v["x0"] + v["length"]) for v in veins) - 2
    hi = max(max(v["x0"], v["x0"] + v["length"]) for v in veins) + 2
    wide = max(v["w0"] for v in veins) + 2
    xs = np.arange(lo, hi + res, res)
    ys = np.arange(-wide, wide + res, res)
    mask = np.zeros((len(ys), len(xs)), dtype=bool)
    for v in veins:
        mask |= _raster(vein_poly(v), xs, ys, res)
    inplate = np.abs(ys)[:, None] <= np.array([hw(min(max(x, 0.0), p["leaf_len"]) / p["leaf_len"], p)
                                               for x in xs])[None, :]
    return float((mask & inplate).sum()) * res * res


def pocket_edge_margin(p, pocket):
    """槽圆周到叶片轮廓的最小净壁厚（沿圆周 720 点算）。"""
    r = p["pocket_d"] / 2.0
    ang = np.linspace(0, 2 * math.pi, 721)
    us = np.clip((pocket["cx"] + r * np.cos(ang)) / p["leaf_len"], 0.0, 1.0)
    hws = np.array([hw(u, p) for u in us])
    return float((hws - np.abs(pocket["cy"] + r * np.sin(ang))).min())


def load():
    p = read_params(SCAD)
    text = SCAD.read_text()
    veins = read_table(text, "vein_rows", VEIN_COLS)
    pockets = read_table(text, "pocket_rows", POCKET_COLS)
    n = int(p["samples"])
    half = np.array([hw(i / n, p) for i in range(n + 1)])
    loop = closed_loop(p)
    plate_area = shoelace(loop)

    ripple = np.array([p["wave_amp"] * math.sin(2 * math.pi * p["wave_n"] * i / n) for i in range(n + 1)])
    wave_ripple = float((ripple.max() - ripple.min()) * (p["half_w"] - p["stem_hw"]))

    vein_edge = min(hw(min(max(pt[0], 0.0), p["leaf_len"]) / p["leaf_len"], p) - abs(pt[1])
                    for v in veins for pt in vein_poly(v))

    # 槽：圆周到轮廓净壁厚 / 两槽最近边距 / 槽顶盖
    pocket_edges = [pocket_edge_margin(p, q) for q in pockets]
    gaps = []
    for i in range(len(pockets)):
        for j in range(i + 1, len(pockets)):
            gaps.append(math.hypot(pockets[i]["cx"] - pockets[j]["cx"],
                                   pockets[i]["cy"] - pockets[j]["cy"]) - p["pocket_d"])
    pocket_gap = min(gaps) if gaps else float("inf")
    ceiling = p["leaf_t"] - p["pocket_depth"]

    pocket_vol = len(pockets) * math.pi * (p["pocket_d"] / 2.0) ** 2 * p["pocket_depth"]
    vein_union = vein_union_area(p, veins)
    protrusion = p["vein_h"] - p["vein_sink"]
    v_analytic = plate_area * p["leaf_t"] + vein_union * protrusion - pocket_vol

    step = float(np.linalg.norm(np.diff(outline(p), axis=0), axis=1).max())

    # 两槽必须关于叶轴（y=0）镜像成对：x 相同、y 互为相反数，磁吸力才对称不翘
    mirror_dev = float("inf")
    for i in range(len(pockets)):
        for j in range(i + 1, len(pockets)):
            mirror_dev = min(mirror_dev, max(abs(pockets[i]["cx"] - pockets[j]["cx"]),
                                             abs(pockets[i]["cy"] + pockets[j]["cy"])))
    if len(pockets) < 2:
        mirror_dev = float("inf")

    p.update({
        "veins": veins, "pockets": pockets,
        "BBOX_X": float(p["leaf_len"]),
        "BBOX_Y": float(2 * half.max()),
        "BBOX_Z": float(p["leaf_t"] - p["vein_sink"] + p["vein_h"]),
        "plate_area": plate_area,
        "vein_union_area": vein_union,
        "vein_protrusion": protrusion,
        "V_analytic": v_analytic,
        "pocket_edge": min(pocket_edges),
        "pocket_gap": pocket_gap,
        "pocket_ceiling": ceiling,
        "bridge_area": len(pockets) * math.pi * (p["pocket_d"] / 2.0) ** 2,
        "pocket_mirror_dev": mirror_dev,
        "vein_edge": vein_edge,
        "wave_ripple": wave_ripple,
        "step_mm": step,
        "max_half_w": float(half.max()),
        "u_at_max": float(int(np.argmax(half)) / n),
        "vein_count": len(veins),
        "pocket_count": len(pockets),
    })
    return p


def main(argv):
    ap = argparse.ArgumentParser(add_help=True, description="idea-014 派生量")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    p = load()
    if a.out:
        Path(a.out).write_text(json.dumps(p, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    if a.json:
        print(json.dumps(p, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"外廓 {p['BBOX_X']:.1f} x {p['BBOX_Y']:.1f} x {p['BBOX_Z']:.1f} mm，"
              f"叶脉 {p['vein_count']} 条，磁铁槽 {p['pocket_count']} 个 φ{p['pocket_d']:.0f}x{p['pocket_depth']:.0f}")
        print(f"  槽顶剩料 {p['pocket_ceiling']:.1f}mm，槽到轮廓净壁厚 {p['pocket_edge']:.2f}mm，"
              f"两槽边距 {p['pocket_gap']:.2f}mm")
        print(f"  波边峰谷 {p['wave_ripple']:.2f}mm，叶脉留边 {p['vein_edge']:.2f}mm，"
              f"采样最大间距 {p['step_mm']:.2f}mm")
        print(f"  解析体积 {p['V_analytic']/1000:.2f}cm³（≈{p['V_analytic']/1000*1.24:.2f}g PLA）")
        if a.out:
            print(f"派生量 -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
