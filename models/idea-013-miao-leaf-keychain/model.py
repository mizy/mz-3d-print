#!/usr/bin/env python3
"""idea-013 白菜叶钥匙扣：解析 model.scad 参数 -> 派生量（check.py / 成本估算共用一份）。

数字只在 model.scad 写一遍；这里照**同一套公式**在 Python 侧重算轮廓与体积，
给 check.py 拿去和 STL 实测对账 —— 对不上就说明「画出来的」和「算出来的」不是一份。

派生量：
  BBOX_X/Y/Z   期望包围盒（Y 由轮廓最大半宽算得，不是手填）
  plate_area   叶片轮廓面积（鞋带公式，精确）
  vein_union   叶脉在叶面内的并集面积（扫描线栅格，1e-2mm）
  V_analytic   = 板面积×板厚 + 叶脉并集×露出高度 - 挂孔体积（STL 体积应与之吻合）
  hole_margin  挂孔圆周到轮廓的最小净壁厚
  vein_edge    叶脉边到轮廓的最小留边（负数 = 叶脉出界）
  wave_ripple  波边峰谷幅度（mm，看波边做没做出来）
  step_mm      轮廓采样点最大间距（看波边会不会被采样切平）
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
from scad_params import read_params  # noqa: E402 —— .scad 参数解析只写一份

VEIN_COLS = ["name", "x0", "ang", "length", "w0", "w1"]


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


# ---------- 轮廓（与 model.scad 的 hw() 逐字对应） ----------
def hw(u, p):
    s = math.sin(math.pi * u ** p["shape_p"]) ** p["shape_q"]
    return p["stem_hw"] + (p["half_w"] - p["stem_hw"]) * s * \
        (1 + p["wave_amp"] * math.sin(2 * math.pi * p["wave_n"] * u))


def outline(p):
    """叶尖一侧的半轮廓点 [(x, y), ...]（y >= 0），x 从 0 到 leaf_len。"""
    n = int(p["samples"])
    return np.array([[p["leaf_len"] * i / n, hw(i / n, p)] for i in range(n + 1)])


def closed_loop(p):
    """整条闭合轮廓（上半 + 镜像下半）。"""
    top = outline(p)
    return np.vstack([top, top[-2:0:-1] * np.array([1.0, -1.0])])


def shoelace(loop):
    x, y = loop[:, 0], loop[:, 1]
    return abs(float(np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y))) / 2.0


def seg_dist(pt, loop):
    """点到闭合折线的最小距离。"""
    a, b = loop, np.roll(loop, -1, axis=0)
    ab = b - a
    t = np.clip(((pt - a) * ab).sum(axis=1) / np.maximum((ab * ab).sum(axis=1), 1e-12), 0, 1)
    proj = a + t[:, None] * ab
    return float(np.linalg.norm(proj - pt, axis=1).min())


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
    """扫描线栅格化单个凸/凹多边形 -> 布尔掩码（图像坐标 [y, x]）。"""
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
    left, right = np.nan_to_num(left), np.nan_to_num(right)   # 不成对的列（NaN）随后由 ok 丢掉
    li = np.clip(np.ceil((left - xs[0]) / res).astype(np.int64), 0, len(xs))
    ri = np.clip(np.floor((right - xs[0]) / res).astype(np.int64) + 1, 0, len(xs))
    acc = np.zeros((len(ys), len(xs) + 1), dtype=np.int32)
    rows = np.broadcast_to(np.arange(len(ys))[:, None], li.shape)
    np.add.at(acc, (rows[ok], li[ok]), 1)
    np.add.at(acc, (rows[ok], ri[ok]), -1)
    return np.cumsum(acc, axis=1)[:, :-1] % 2 == 1


def vein_union_area(p, veins, res=0.01):
    """叶脉并集落在叶片轮廓内的面积（栅格 0.01mm，误差 < 0.3%）。"""
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


def load():
    p = read_params(SCAD)
    veins = read_table(SCAD.read_text(), "vein_rows", VEIN_COLS)
    n = int(p["samples"])
    half = np.array([hw(i / n, p) for i in range(n + 1)])
    loop = closed_loop(p)
    plate_area = shoelace(loop)

    # 波边峰谷幅度：波边项对半宽的调制量
    ripple = np.array([p["wave_amp"] * math.sin(2 * math.pi * p["wave_n"] * i / n) for i in range(n + 1)])
    wave_ripple = float((ripple.max() - ripple.min()) * (p["half_w"] - p["stem_hw"]))

    # 挂孔圆周到轮廓的最小净壁厚
    hole_r = p["hole_d"] / 2.0
    circle = np.array([[p["hole_x"], 0.0]]) + hole_r * np.stack(
        [np.cos(np.linspace(0, 2 * math.pi, 361)), np.sin(np.linspace(0, 2 * math.pi, 361))], axis=1)
    hole_margin = min(seg_dist(pt, loop) for pt in circle)

    # 叶脉边到轮廓的最小留边（>0 表示全部落在叶面内）
    vein_edge = 1e9
    for v in veins:
        poly = vein_poly(v)
        for pt in poly:
            vein_edge = min(vein_edge, hw(min(max(pt[0], 0.0), p["leaf_len"]) / p["leaf_len"], p) - abs(pt[1]))

    vein_union = vein_union_area(p, veins)
    protrusion = p["vein_h"] - p["vein_sink"]
    v_analytic = plate_area * p["leaf_t"] + vein_union * protrusion - math.pi * hole_r ** 2 * p["leaf_t"]

    step = float(np.linalg.norm(np.diff(outline(p), axis=0), axis=1).max())

    p.update({
        "veins": veins,
        "BBOX_X": float(p["leaf_len"]),
        "BBOX_Y": float(2 * half.max()),
        "BBOX_Z": float(p["leaf_t"] - p["vein_sink"] + p["vein_h"]),
        "plate_area": plate_area,
        "vein_union_area": vein_union,
        "vein_protrusion": protrusion,
        "V_analytic": v_analytic,
        "hole_margin": hole_margin,
        "vein_edge": vein_edge,
        "wave_ripple": wave_ripple,
        "step_mm": step,
        "max_half_w": float(half.max()),
        "u_at_max": float(int(np.argmax(half)) / n),
        "vein_count": len(veins),
    })
    return p


def main(argv):
    ap = argparse.ArgumentParser(add_help=True, description="idea-013 派生量")
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
              f"叶脉 {p['vein_count']} 条（露出 {p['vein_protrusion']:.1f}mm）")
        print(f"  轮廓面积 {p['plate_area']:.1f}mm²，最宽处 u={p['u_at_max']:.2f}（半宽 {p['max_half_w']:.2f}）")
        print(f"  挂孔 φ{p['hole_d']:.0f} 净壁厚 {p['hole_margin']:.2f}mm，叶脉留边 {p['vein_edge']:.2f}mm")
        print(f"  波边峰谷 {p['wave_ripple']:.2f}mm，采样最大间距 {p['step_mm']:.2f}mm")
        print(f"  解析体积 {p['V_analytic']/1000:.2f}cm³（≈{p['V_analytic']/1000*1.24:.2f}g PLA）")
        if a.out:
            print(f"派生量 -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
