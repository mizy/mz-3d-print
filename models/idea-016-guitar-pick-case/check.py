#!/usr/bin/env python3
"""idea-016 吉他拨片盒自检：把「能不能打」逐条算出来，全过才有意义开打。

只读 model.scad / model.py / 台账 print-ideas.json 与同目录 STL，不改任何文件。
用法: python3 check.py      （退出码 0 = 全过）

  A 尺寸链自洽：内腔 = 拨片 + 2×间隙；内腔高 = 片数×厚 + 余量；盒外 = 内腔 + 2×壁；
                盖内 = 盒外 + 2×插拔间隙；盖壁厚 = 裙边厚；组装总高 ≤ 20；容量 ≥ 8 片
  B 可打印性：壁厚/底厚/盖板/裙边 ≥ 1.6（结构上没有铰链、没有薄壁）；圆角同心；
                两件排开 ≤ 90x45x20
  C 实物对账：STL 连通块 = 2（盒身 + 上盖互不相连）、每块包围盒 = 参数、每块体积 = 解析、
                两件底面都贴床、无陡悬垂面、无朝下水平面（不用桥接/支撑）、水密绕序、克数
"""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import model as M  # noqa: E402

SCRIPTS = Path.home() / ".cah-data/skills/shared/3d-print-ideas/scripts"
LEDGER = Path.home() / ".cah-data/skills/shared/3d-print-ideas/runtime/print-ideas.json"
sys.path.insert(0, str(SCRIPTS))
from check_model import read_stl  # noqa: E402

STL = HERE / "pick-case.stl"
THREE = HERE / "pick-case.3mf"

MIN_FEATURE = 1.6
MAX_STEEP_AREA = 0.01
VOL_TOL = 0.005          # 每块体积 vs 解析（圆角/圆弧网格化误差）
AREA_TOL = 0.01
MAX_G = 40.0

fails, total = [], 0


def check(ok, label, detail):
    global total
    total += 1
    print(("  ok  " if ok else " FAIL ") + label + "  " + detail)
    if not ok:
        fails.append(label)


def build_volume():
    if not LEDGER.exists():
        return None
    raw = json.loads(LEDGER.read_text()).get("printer", {}).get("buildVolume") or ""
    nums = [float(v) for v in re.findall(r"\d+(?:\.\d+)?", raw)]
    return nums[:3] if len(nums) >= 3 else None


def rrect_points(w, d, r, n_arc=90, n_edge=180):
    """圆角矩形边界采样点（角弧 + 四边，用于量壁厚）。"""
    a, b = w / 2.0, d / 2.0
    corners = [((a - r, b - r), 0.0, 90.0), ((-a + r, b - r), 90.0, 180.0),
               ((-a + r, -b + r), 180.0, 270.0), ((a - r, -b + r), 270.0, 360.0)]
    pts = []
    for i, (c, a0, a1) in enumerate(corners):
        for k in range(n_arc):
            ang = math.radians(a0 + (a1 - a0) * k / n_arc)
            pts.append((c[0] + r * math.cos(ang), c[1] + r * math.sin(ang)))
        # 本角弧终点 -> 下一角弧起点之间的直边
        p0 = (c[0] + r * math.cos(math.radians(a1)), c[1] + r * math.sin(math.radians(a1)))
        nc = corners[(i + 1) % 4]
        p1 = (nc[0][0] + r * math.cos(math.radians(nc[1])), nc[0][1] + r * math.sin(math.radians(nc[1])))
        for k in range(1, n_edge):
            t = k / n_edge
            pts.append((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t))
    return np.array(pts)


def wall_min(outer, inner):
    """两条闭合轮廓（圆角矩形）之间的最小距离 = 该处壁厚。"""
    from scipy.spatial import cKDTree
    return float(cKDTree(outer).query(inner)[0].min())


def rrect_perim(outer_w, outer_d, outer_r, inner_w, inner_d, inner_r):
    return wall_min(rrect_points(outer_w, outer_d, outer_r),
                    rrect_points(inner_w, inner_d, inner_r))


def face_components(tris):
    """面片按共享边并查集 -> 每个面片的连通块编号（顶点按 1e-4 取整当同一顶点）。"""
    key, ids = {}, np.zeros(tris.shape[:2], dtype=np.int64)
    for fi in range(tris.shape[0]):
        for vi in range(3):
            ids[fi, vi] = key.setdefault(tuple(np.round(tris[fi, vi], 4)), len(key))
    parent = list(range(tris.shape[0]))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    owner = {}
    for fi in range(tris.shape[0]):
        a, b, c = ids[fi]
        for e in ((min(a, b), max(a, b)), (min(b, c), max(b, c)), (min(c, a), max(c, a))):
            other = owner.setdefault(e, fi)
            if other != fi:
                ra, rb = find(fi), find(other)
                if ra != rb:
                    parent[ra] = rb
    return np.array([find(i) for i in range(tris.shape[0])])


p = M.load()
print(f"# {HERE.name}  整盘 {p['pack_x']:.1f} x {p['pack_y']:.1f} x {p['pack_z']:.1f} mm"
      f"（盒身 + 上盖两件排开），装 {p['pick_count']} 片\n")

print("A 尺寸链自洽")
check(abs(p["cavity_l"] - (p["pick_l"] + 2 * p["edge_clear"])) < 1e-9, "内腔长 = 拨片长 + 2×单边间隙",
      f"{p['cavity_l']:.2f} = {p['pick_l']:.0f} + 2×{p['edge_clear']:.2f}")
check(abs(p["cavity_d"] - (p["pick_w"] + 2 * p["edge_clear"])) < 1e-9, "内腔宽 = 拨片宽 + 2×单边间隙",
      f"{p['cavity_d']:.2f} = {p['pick_w']:.0f} + 2×{p['edge_clear']:.2f}")
check(0.5 <= p["edge_clear"] <= 1.0, "单边间隙好放好取（0.5-1.0）", f"{p['edge_clear']:.2f}mm/边")
check(p["cavity_l"] >= p["pick_l"] and p["cavity_d"] >= p["pick_w"], "内腔放得下 351 拨片",
      f"内腔 {p['cavity_l']:.1f}x{p['cavity_d']:.1f} ≥ 拨片 {p['pick_l']:.0f}x{p['pick_w']:.0f}")
check(abs(p["cavity_h"] - (p["pick_count"] * p["pick_t"] + p["stack_clear"])) < 1e-9,
      "内腔高 = 片数×厚 + 堆叠余量",
      f"{p['cavity_h']:.2f} = {p['pick_count']}×{p['pick_t']:.1f} + {p['stack_clear']:.1f}")
check(p["capacity"] >= 8, "内腔至少装得下 8 片（要求 8-10 片）",
      f"最多 {p['capacity']} 片（本次按 {p['pick_count']} 片排布），堆完余 {p['headroom']:.1f}mm")
check(abs(p["tray_w"] - (p["cavity_l"] + 2 * p["wall_t"])) < 1e-9
      and abs(p["tray_h"] - (p["floor_t"] + p["cavity_h"])) < 1e-9, "盒身 = 内腔 + 2×壁厚 / 底厚 + 内腔高",
      f"{p['tray_w']:.1f}x{p['tray_d']:.1f}x{p['tray_h']:.1f}")
check(abs(p["lid_iw"] - (p["tray_w"] + 2 * p["lid_fit"])) < 1e-9, "盖内 = 盒外 + 2×插拔间隙",
      f"{p['lid_iw']:.2f} = {p['tray_w']:.1f} + 2×{p['lid_fit']:.2f}")
check(0.2 <= p["lid_fit"] <= 0.3, "插拔间隙在 FDM 装配区间（0.2-0.3）", f"{p['lid_fit']:.2f}mm/边")
check(abs(p["skirt_wall"] - p["skirt_t"]) < 1e-9, "盖裙边壁厚均匀（外轮廓与内腔同心）",
      f"实测 {p['skirt_wall']:.2f} = 设定 {p['skirt_t']:.1f}mm")
check(abs(p["lid_ir"] - (p["corner_r"] + p["lid_fit"])) < 1e-9, "盖内圆角 = 盒外圆角 + 插拔间隙",
      f"{p['lid_ir']:.2f} = {p['corner_r']:.0f} + {p['lid_fit']:.2f}")
check(abs(p["cavity_r"] - (p["corner_r"] - p["wall_t"])) < 1e-9, "内腔圆角 = 盒外圆角 - 壁厚（同心）",
      f"{p['cavity_r']:.1f} = {p['corner_r']:.0f} - {p['wall_t']:.1f}")
cav_wall = rrect_perim(p["tray_w"], p["tray_d"], p["corner_r"],
                       p["cavity_l"], p["cavity_d"], p["cavity_r"])
check(cav_wall >= p["wall_t"] - 0.05, "四周壁厚（含四角）处处达标",
      f"最薄 {cav_wall:.2f}mm ≥ {p['wall_t']:.1f}mm（直壁与圆角都量了）")
lid_wall = rrect_perim(p["lid_ow"], p["lid_od"], p["lid_or"],
                       p["lid_iw"], p["lid_id"], p["lid_ir"])
check(lid_wall >= p["skirt_t"] - 0.05, "盖裙边壁厚（含四角）处处达标",
      f"最薄 {lid_wall:.2f}mm ≥ {p['skirt_t']:.1f}mm")
check(p["assembled_h"] <= 20.0, "盖上去的总高 ≤ 20", f"{p['assembled_h']:.1f} = 盒 {p['tray_h']:.1f} + 盖板 {p['lid_t']:.1f}")

print("\nB 可打印性（两件都平底贴床、竖壁朝上；插拔盖没有铰链）")
check(p["min_feature"] >= MIN_FEATURE, f"最薄实体 ≥ {MIN_FEATURE}mm",
      f"底 {p['floor_t']:.1f} / 壁 {p['wall_t']:.1f} / 盖板 {p['lid_t']:.1f} / 裙边 {p['skirt_t']:.1f}"
      f"（无薄壁铰链：盖是整片插拔件）")
check(p["floor_t"] >= MIN_FEATURE, "盒底够厚（不变形、不翘）", f"{p['floor_t']:.1f}mm ≥ {MIN_FEATURE}mm")
check(p["skirt_h"] >= 2.0, "裙边够高（套得住、不掉）", f"{p['skirt_h']:.1f}mm ≥ 2.0mm")
check(p["pack_x"] <= 90 and p["pack_y"] <= 45 and p["pack_z"] <= 20, "两件排开 ≤ 90x45x20",
      f"{p['pack_x']:.1f} x {p['pack_y']:.1f} x {p['pack_z']:.1f} mm")
bv = build_volume()
if bv:
    check(p["pack_x"] <= bv[0] and p["pack_y"] <= bv[1] and p["pack_z"] <= bv[2],
          "整盘 ≤ 打印机成型尺寸", f"{p['pack_x']:.1f}x{p['pack_y']:.1f}x{p['pack_z']:.1f} ≤ {bv}")
else:
    print("  skip  整盘 ≤ 成型尺寸  台账里没读到 buildVolume")

print("\nC 实物对账")
if not STL.exists():
    print(f"  FAIL 没有 {STL.name}，先跑 build_mesh.py")
    fails.append("STL 未编译")
else:
    fmt, n, tris, _nrm = read_stl(STL)
    v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
    cross = np.cross(v1 - v0, v2 - v0)
    nlen = np.linalg.norm(cross, axis=1)
    area = 0.5 * nlen
    nz = np.divide(cross[:, 2], nlen, out=np.zeros(n), where=nlen > 0)
    lo = tris[:, :, 2].min(axis=1)
    hi_z = tris[:, :, 2].max(axis=1)
    vol = abs(np.einsum("ij,ij->i", v0, np.cross(v1, v2)).sum() / 6)
    bbox = tris.reshape(-1, 3).max(axis=0) - tris.reshape(-1, 3).min(axis=0)
    zmin = tris[:, :, 2].min()
    print(f"      STL {fmt} {n} 面，包围盒 [{bbox[0]:.2f} {bbox[1]:.2f} {bbox[2]:.2f}]，"
          f"体积 {vol/1000:.3f}cm³，解析 {p['V_analytic']/1000:.3f}cm³")

    lab = face_components(tris)
    comps = np.unique(lab)
    check(len(comps) == 2, "连通块 = 2（盒身与上盖互不相连）", f"实测 {len(comps)} 块")
    measured = []
    for c in comps:
        t = tris[lab == c]
        a3, b3, c3 = t[:, 0], t[:, 1], t[:, 2]
        measured.append({
            "size": t.reshape(-1, 3).max(axis=0) - t.reshape(-1, 3).min(axis=0),
            "xmin": t.reshape(-1, 3).min(axis=0)[0],
            "vol": abs(np.einsum("ij,ij->i", a3, np.cross(b3, c3)).sum() / 6),
        })
    measured.sort(key=lambda d: d["xmin"])
    for part, meas in zip(sorted(p["parts"], key=lambda d: d["x0"]), measured):
        name, want = part["name"], part["size"]
        check(all(abs(a - b) <= 0.05 for a, b in zip(meas["size"], want)),
              f"{name} 包围盒 = 参数", f"实测 {[round(v,2) for v in meas['size']]} vs {[round(v,2) for v in want]}")
        check(abs(meas["vol"] - part["volume"]) <= VOL_TOL * part["volume"],
              f"{name} 体积 = 解析", f"{meas['vol']/1000:.3f} vs {part['volume']/1000:.3f} cm³"
              f"（差 {abs(meas['vol']-part['volume'])/part['volume']:.2%}）")

    check(abs(zmin) <= 0.01, "两件底面都贴床 z=0", f"最低点 z={zmin:.4f}")
    for ax, name, want in ((0, "X", p["pack_x"]), (1, "Y", p["pack_y"]), (2, "Z", p["pack_z"])):
        check(abs(bbox[ax] - want) <= 0.1, f"整盘 STL {name} 外廓 = 参数",
              f"实测 {bbox[ax]:.3f} / 期望 {want:.3f} mm")
    check(abs(vol - p["V_analytic"]) <= VOL_TOL * p["V_analytic"], "整盘体积 = 解析体积",
          f"差 {abs(vol-p['V_analytic'])/p['V_analytic']:.2%} ≤ {VOL_TOL:.0%}")

    bed = (nz <= -0.99) & (hi_z <= 0.05)
    want_bed = M.rrect_area(p["tray_w"], p["tray_d"], p["corner_r"]) + \
        M.rrect_area(p["lid_ow"], p["lid_od"], p["lid_or"])
    check(abs(area[bed].sum() - want_bed) <= AREA_TOL * want_bed, "贴床面 = 两件完整平底",
          f"实测 {area[bed].sum():.0f}mm² vs 解析 {want_bed:.0f}mm²（盒外底 + 盖外底）")
    steep = (nz < -0.707) & (lo > 0.05)
    check(area[steep].sum() <= MAX_STEEP_AREA * area.sum(), "没有陡悬垂面（免支撑）",
          f"陡下向 {area[steep].sum():.2f}mm² = {area[steep].sum()/area.sum():.2%}")
    flat_down = (nz <= -0.95) & (lo > 0.05)
    check(area[flat_down].sum() <= MAX_STEEP_AREA * area.sum(), "没有朝下水平面（不用桥接）",
          f"{area[flat_down].sum():.2f}mm²")

    r = subprocess.run(["python3", str(SCRIPTS / "check_model.py"), str(STL), "--3mf", str(THREE),
                        "--material", "PLA"], capture_output=True, text=True)
    for line in r.stdout.strip().splitlines():
        print("      " + line.strip())
    check(r.returncode == 0 and "全过" in r.stdout, "check_model 全过（水密/绕序/STL↔3MF）", f"exit={r.returncode}")

    r = subprocess.run(["node", str(SCRIPTS / "cost.mjs"), str(STL), "--material", "PLA", "--json"],
                       capture_output=True, text=True)
    cj = json.loads(r.stdout)["totals"]
    check(0 < cj["massPrintG"] <= MAX_G, f"预计用料 ≤ {MAX_G:.0f}g（两件合计）",
          f"{cj['massPrintG']:.2f} g（满打 {cj['massSolidG']:.2f} g），约 {cj['printHours']:.2f} h，"
          f"{cj['totalCost']:.2f} 元")

print(f"\n{'PASS' if not fails else 'FAIL'}  {total - len(fails)}/{total} 项通过"
      + ("" if not fails else "  挂: " + "; ".join(fails)))
sys.exit(0 if not fails else 1)
