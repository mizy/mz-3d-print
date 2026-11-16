#!/usr/bin/env python3
"""纯立体字版「苗壮」：两个字连成一体，没有底板、没有边框、没有底座。

主人 2026-10-31 的原话：「…不要有后面的碑的基底，它不是个碑，它是个立体字」。
所以这里只出字本身，靠两样东西把它焊成一件：
  ① 底部连体梁：横跨两个字之间的空隙，8mm 高，与字同厚；
  ② 笔画桥：字体里本来就断开的部件（如「苗」的艹 与 田、行楷的散笔）之间，
     在最近点之间补一根 R2 的圆筋 —— 不打桥就会得到一堆散件，合不起来。

打印姿态就是模型姿态：平放、字面朝上（+Z），零支撑。

跑法: uv run --offline --python 3.13 --with cadgen==0.7.26 python build_solid.py
产物: miao-zhuang-solid-<字体>.stl/.3mf + -report.json
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(Path.home() / ".cah-data/skills/shared/3d-print-ideas/scripts"))

from build123d import (Align, Axis, Box, Cylinder, Location, Plane, Pos,  # noqa: E402
                       Text, chamfer, extrude, export_stl)
from OCP.BRepExtrema import BRepExtrema_DistShapeShape  # noqa: E402

import model as M  # noqa: E402
import scad_build as SB  # noqa: E402
from build_mesh import stroke_stats  # noqa: E402 —— 笔画宽度只量一次

FONTS = [("weibei", "魏碑"), ("xingkai", "行楷"), ("baoli", "报隶")]
BRIDGE_R = 2.0
BRIDGE_INSET = 1.0
THICK = [10.0]   # 由 main 写进实际字厚，bridge 只读


def nearest_pair(a, b):
    """两个实体的最近点对（OCC 距离求解器，直接给点）。"""
    solver = BRepExtrema_DistShapeShape(a.wrapped, b.wrapped)
    solver.Perform()
    p1 = solver.PointOnShape1(1)
    p2 = solver.PointOnShape2(1)
    return (np.array([p1.X(), p1.Y(), p1.Z()]), np.array([p2.X(), p2.Y(), p2.Z()]))


def bridge(a, b):
    """在 a、b 最近点之间补一根方筋（高度严格 = 字厚），两端各插进实体 1mm。

    用棱柱不用圆柱：圆柱会把 z 撑出字厚（最近点常落在字面顶盖上），成品厚度就变了。
    """
    p1, p2 = nearest_pair(a, b)
    p1, p2 = p1.copy(), p2.copy()
    p1[2] = p2[2] = 0.0                     # 只在 XY 平面找方向，筋的高度锁死在 0..thick
    axis = p2[:2] - p1[:2]
    length = float(np.linalg.norm(axis))
    if length < 1e-6:
        return None
    d = axis / length
    mid = (p1[:2] + p2[:2]) / 2
    rod = Plane(origin=(mid[0], mid[1], 0), x_dir=(d[0], d[1], 0)) * Box(
        length + 2 * BRIDGE_INSET, 2 * BRIDGE_R, THICK[0],
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    return rod


def weld(shape):
    """把散件按最近距离两两连起来，直到只剩一个连通体。"""
    bodies = list(shape.solids())
    joins = 0
    while len(bodies) > 1:
        best, pair = None, None
        for i in range(len(bodies)):
            for j in range(i + 1, len(bodies)):
                p1, p2 = nearest_pair(bodies[i], bodies[j])
                d = float(np.linalg.norm(p2 - p1))
                if best is None or d < best:
                    best, pair = d, (i, j)
        rod = bridge(bodies[pair[0]], bodies[pair[1]])
        merged = bodies[pair[0]] + bodies[pair[1]] + rod
        bodies = [merged] + [b for k, b in enumerate(bodies) if k not in pair]
        joins += 1
        if joins > 12:
            raise SystemExit("焊接次数超限，字体碎件太多")
    return bodies[0], joins


def split_clusters(letters):
    """按 X 把连通件分成「左字 / 右字」两簇（每一簇仍可能有多块，等 weld 焊）。"""
    boxes = [(s.bounding_box(), s) for s in letters.solids()]
    mids = np.array([b.center().X for b, _s in boxes])
    cut = (mids.min() + mids.max()) / 2
    left = [s for b, s in boxes if b.center().X <= cut]
    right = [s for b, s in boxes if b.center().X > cut]
    return left, right


def tighten(left, right, gap_mm):
    """把右字往左挪，让两字净间距 = gap_mm（字体自带边距约 18mm，不收紧像两个独立件）。"""
    lmax = max(s.bounding_box().max.X for s in left)
    rmin = min(s.bounding_box().min.X for s in right)
    dx = rmin - lmax - gap_mm
    return dx, [Pos(-dx, 0, 0) * s for s in right]


def solid_body(p, font_key, cfg):
    txt = Text(p["text"], font_size=cfg["font_size"], font_path=M.FONTS[font_key],
               align=(Align.CENTER, Align.CENTER))
    letters = extrude(txt, amount=cfg["thick"])
    left, right = split_clusters(letters)
    dx, right = tighten(left, right, cfg["gap_mm"])
    left_x = max(s.bounding_box().max.X for s in left)
    right_x = min(s.bounding_box().min.X for s in right)

    # 先在每个字内部焊散笔（桥不许跨到另一个字上去，否则会在字间架一根斜筋，很丑）
    joins = 0
    merged = []
    for cluster in (left, right):
        shape = cluster[0]
        for s in cluster[1:]:
            shape = shape + s
        shape, n = weld(shape)
        joins += n
        merged.append(shape)

    # 连体梁真正要贴住的是「底部的墨迹」，不是整个字的包围盒：
    # 苗的包围盒右缘在字腰，底部那一行到不了那儿 —— 只按包围盒搭梁会悬空，
    # 后面 weld 就会自己从字腰斜拉一根筋过去（第一版就是这么出来的斜筋）。
    y0 = txt.bounding_box().min.Y
    band_h = cfg["bar_h"]
    band = Pos(0, y0 + band_h / 2, cfg["thick"] / 2) * Box(400, band_h, cfg["thick"] + 2)
    left_bottom = merged[0] & band
    right_bottom = merged[1] & band
    x0 = left_bottom.bounding_box().max.X - cfg["bar_overlap"] * 1.5
    x1 = right_bottom.bounding_box().min.X + cfg["bar_overlap"] * 1.5
    body = merged[0] + merged[1]
    if x1 - x0 > 1.0:                     # 两字已经咬上时不画梁，免得中间多一截横杠
        body = body + Pos((x0 + x1) / 2, y0 + cfg["bar_h"] / 2, cfg["thick"] / 2) * Box(
            x1 - x0, cfg["bar_h"], cfg["thick"])
    body, extra_joins = weld(body)     # 兜底：万一连体梁没搭上，再补一根
    joins += extra_joins

    # 倒角只挑顶面周长里够长的边：字形尖角一倒就崩，短边直接跳过
    chamfered = "跳过"
    top_edges = [e for e in body.edges().group_by(Axis.Z)[-1] if e.length > 2.0]
    for length in (cfg["chamfer"], cfg["chamfer"] * 0.6, cfg["chamfer"] * 0.35):
        try:
            body = chamfer(top_edges, length=length)
            chamfered = round(length, 2)
            break
        except Exception as exc:
            chamfered = "跳过（字形尖角多，倒角会崩）"
    return body, {"gap": round(right_x - left_x, 2), "bar_span": round(max(0.0, x1 - x0), 2),
                  "split_x": round((left_x + right_x) / 2, 2),
                  "tightened_mm": round(dx, 2), "bridges": joins, "chamfer": chamfered}


def main():
    p = M.load()
    THICK[0] = M.SOLID["thick"]
    for font_key, label in FONTS:
        body, extra = solid_body(p, font_key, M.SOLID)
        name = f"miao-zhuang-solid-{font_key}"
        stl, three = HERE / f"{name}.stl", HERE / f"{name}.3mf"
        export_stl(body, str(stl), tolerance=0.05, angular_tolerance=0.2)
        SB.stl_to_3mf(stl, three, name)
        bb = body.bounding_box()
        rep = {
            "font": font_key, "label": label, "kind": "纯立体字",
            "size": [round(bb.size.X, 2), round(bb.size.Y, 2), round(bb.size.Z, 2)],
            "min_corner": [round(bb.min.X, 2), round(bb.min.Y, 2), round(bb.min.Z, 2)],
            "volume_mm3": round(body.volume, 1), "solids": len(body.solids()),
            "stroke_mm": stroke_stats(p["text"], M.FONTS[font_key], M.SOLID["font_size"]),
            "stl": stl.name, "3mf": three.name, **extra,
        }
        (HERE / f"{name}-report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2))
        print(f"{name}: {rep['size']} mm, {rep['volume_mm3']/1000:.1f} cm3, "
              f"solids {rep['solids']}, gap {extra['gap']}, bridges {extra['bridges']}, "
              f"chamfer {extra['chamfer']}")


if __name__ == "__main__":
    main()
