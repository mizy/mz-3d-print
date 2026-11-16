#!/usr/bin/env python3
"""idea-017 镂空分隔收纳篮（苗壮制造）自检：把「能不能打」逐条算出来，全过才有意义开打。

只读 model.scad / model.py / 台账 print-ideas.json / 同目录 STL+report.json，不改任何文件。
用法: python3 check.py      （退出码 0 = 全过）

  A 尺寸链自洽：格数×格宽 + 隔板 = 内腔；内腔 + 2×外壁 = 外廓；总高 - 底板 = 内腔高；
                外廓 ≤ 200x130x60（主人柜格量级）
  B 可打印性：壁/隔板/底板 ≥ 1.6（0.4 喷嘴 4 圈）；孔间与孔端韧带 ≥ 3.2；
                孔顶平段 ≤ 桥接上限 15；孔不出圆角段、不碰底板与顶面；
                镂空真的开了（每面至少几个孔、实测孔数 = 孔位清单）；材料 ≤ 外廓 35%；
                品牌浮雕：幅面放得下、字高 = 参数、凸起不刮手、字体基线校验通过（真出汉字）
  C 实物对账：STL 单件连通、包围盒 = 参数、体积 = 解析、底面贴床、贴床面积 = 外廓 - 底板孔、
                朝下平段跨距 ≤ 15、无陡悬垂面、check_model 全过、克数在预算内
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

STL = HERE / "lattice-divider.stl"
THREE = HERE / "lattice-divider.3mf"
REPORT = HERE / "lattice-divider-report.json"

MIN_FEATURE = 1.6
VOL_TOL = 0.01
AREA_TOL = 0.02
MAX_G = 250.0
MAX_BUDGET = 0.35
MAX_BRAND_RAISE = 1.2

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


def face_components(tris):
    """面片按共享边并查集 -> 连通块编号（顶点按 1e-4 取整当同一顶点）。"""
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


raw = M.read_params(M.SCAD)
p = M.load()
print(f"# {HERE.name}  外廓 {p['outer_w']:.1f} x {p['outer_d']:.1f} x {p['outer_h']:.1f} mm"
      f"（{p['cells_x']}x{p['cells_y']} 格），镂空孔 {len(p['louvers'])} + {len(p['bottom_holes'])} 个，"
      f"品牌「{p['brand_text']}」\n")

print("A 尺寸链自洽")
check(abs(p["inner_w"] - (raw["cells_x"] * raw["cell_w"] + (raw["cells_x"] - 1) * raw["divider_t"])) < 1e-9,
      "内腔宽 = 格数×格宽 + (格数-1)×隔板厚",
      f"{p['inner_w']:.1f} = {raw['cells_x']:.0f}×{raw['cell_w']:.0f} + {raw['cells_x'] - 1:.0f}×{raw['divider_t']:.1f}")
check(abs(p["inner_d"] - (raw["cells_y"] * raw["cell_d"] + (raw["cells_y"] - 1) * raw["divider_t"])) < 1e-9,
      "内腔深 = 格数×格深 + (格数-1)×隔板厚",
      f"{p['inner_d']:.1f} = {raw['cells_y']:.0f}×{raw['cell_d']:.0f} + {raw['cells_y'] - 1:.0f}×{raw['divider_t']:.1f}")
check(abs(p["outer_w"] - (p["inner_w"] + 2 * p["wall_t"])) < 1e-9
      and abs(p["outer_d"] - (p["inner_d"] + 2 * p["wall_t"])) < 1e-9, "外廓 = 内腔 + 2×外壁厚",
      f"{p['outer_w']:.1f} x {p['outer_d']:.1f}")
check(abs(p["cavity_h"] - (p["outer_h"] - p["floor_t"])) < 1e-9, "内腔高 = 总高 - 底板厚",
      f"{p['cavity_h']:.1f} = {p['outer_h']:.0f} - {p['floor_t']:.1f}")
check(abs(p["cavity_r"] - (p["corner_r"] - p["wall_t"])) < 1e-9, "内腔圆角 = 外圆角 - 壁厚（同心）",
      f"{p['cavity_r']:.1f} = {p['corner_r']:.0f} - {p['wall_t']:.1f}")
check(p["outer_w"] <= 200 and p["outer_d"] <= 130 and p["outer_h"] <= 60, "外廓 ≤ 200x130x60（柜格量级）",
      f"{p['outer_w']:.1f} x {p['outer_d']:.1f} x {p['outer_h']:.1f}")
print(f"  提示  塞进柜格：内径需 ≥ {p['outer_w'] + 2 * p['fit_clear']:.1f} x "
      f"{p['outer_d'] + 2 * p['fit_clear']:.1f} x {p['outer_h']:.0f}（留 {p['fit_clear']}mm/边）"
      f"；量到真实内径就把 cell_w/cell_d/cells_* 改掉重出")

print("\nB 可打印性（全部竖直壁 + 水平底板 → 平放免支撑）")
check(min(p["wall_t"], p["divider_t"], p["floor_t"]) >= MIN_FEATURE, f"最薄实体 ≥ {MIN_FEATURE}mm",
      f"外壁 {p['wall_t']:.1f} / 隔板 {p['divider_t']:.1f} / 底板 {p['floor_t']:.1f}")
check(p["min_ligament"] >= M.MIN_LIGAMENT, f"镂空孔间/孔端最少料 ≥ {M.MIN_LIGAMENT}mm",
      f"孔间 {p['louver_gap']:.1f} / 后墙端 {p['margin_back']:.2f} / 侧墙端 {p['margin_side']:.2f} / "
      f"排间 {p['row_gap']:.2f} / 底板孔间 {p['bottom_gap']:.1f} / 底板孔到壁 {p['bottom_edge']:.1f}"
      f"  最小 {p['min_ligament']:.2f}")
check(p["bridge_flat"] <= M.BRIDGE_MAX, f"孔顶平段 ≤ 桥接上限 {M.BRIDGE_MAX}mm（孔顶不外伸支撑）",
      f"{p['bridge_flat']:.1f} = 孔长 {p['louver_w']:.0f} - 2×圆角 {p['louver_r']:.0f}")
check(p["louver_r"] < p["louver_h"] / 2 and p["louver_r"] < p["louver_w"] / 2 and p["corner_r"] < min(p["outer_w"], p["outer_d"]) / 2,
      "圆角都做得出（半径 < 相应边的一半）",
      f"孔 R{p['louver_r']:.0f} < min({p['louver_w']:.0f},{p['louver_h']:.0f})/2；外廓 R{p['corner_r']:.0f}")
lo_z, hi_z_ok = min(p["row_zs"]) - p["louver_h"] / 2, max(p["row_zs"]) + p["louver_h"] / 2
check(lo_z >= p["sill_h"] - 1e-9 and hi_z_ok <= p["outer_h"] - p["ledge_h"] + 1e-9,
      "墙面孔都在允许高度带里（不碰底板、不破顶面）",
      f"孔 {lo_z:.1f}..{hi_z_ok:.1f} 在 {p['sill_h']:.0f}..{p['outer_h'] - p['ledge_h']:.0f} 内")
check(p["n_back"] >= 3 and p["n_side"] >= 1 and p["n_div_x"] >= 1 and p["n_div_y"] >= 1
      and p["n_bx"] * p["n_by"] >= 2, "镂空真的开了（每面/每格都有孔）",
      f"后墙 {p['n_back']}/排、侧墙 {p['n_side']}/排、隔板 {p['n_div_x']}/{p['n_div_y']}、"
      f"整件 {len(p['louvers'])} + 底板 {len(p['bottom_holes'])}")
check(len(p["louvers"]) == (p["n_back"] + 2 * p["n_side"]) * p["louver_rows"]
      + ((p["cells_x"] - 1) * p["n_div_x"] + (p["cells_y"] - 1) * p["n_div_y"]) * p["div_rows"],
      "孔位清单条数 = 逐面孔数（不多不少）",
      f"{len(p['louvers'])} 个")
check(len(p["bottom_holes"]) == p["cells_x"] * p["cells_y"] * p["n_bx"] * p["n_by"],
      "底板孔数 = 格数 × 每格孔数", f"{len(p['bottom_holes'])} = {p['cells_x'] * p['cells_y']}×{p['n_bx'] * p['n_by']}")
check(p["volume_ratio"] <= MAX_BUDGET, f"材料预算 ≤ 外廓 {MAX_BUDGET:.0%}（浅仓不是实心砖）",
      f"{p['volume_ratio']:.1%}（{p['V_no_text']/1000:.1f} / {p['V_outer_box']/1000:.0f} cm³）")
rep = json.loads(REPORT.read_text()) if REPORT.exists() else {}
brand = rep.get("brand", {})
if brand:
    check(brand["width"] + 2 * p["brand_margin"] <= p["flat_x"], "品牌字放得下正面平段（两侧留够 margin）",
          f"字宽 {brand['width']:.1f} + 2×{p['brand_margin']:.0f} ≤ 平段 {p['flat_x']:.1f}")
    check(abs(brand["height"] - p["brand_cap_h"]) <= 0.15, "字高 = 参数 brand_cap_h",
          f"实测 {brand['height']:.2f} vs {p['brand_cap_h']:.1f}")
    check(p["brand_raise"] <= MAX_BRAND_RAISE, "凸起不刮手", f"{p['brand_raise']:.1f} ≤ {MAX_BRAND_RAISE}")
    check(brand["baseline"]["ok"] is True, "字体基线校验通过（真出汉字，不是方框）",
          f"real {brand['baseline']['real_bbox']} vs bogus {brand['baseline']['bogus_bbox']}")
else:
    print("  skip  品牌字相关 4 项  —— 还没有 report.json，先跑 build_mesh.py")

print("\nC 实物对账")
if not STL.exists():
    check(False, "STL 已生成", f"缺 {STL.name}，先跑 build_mesh.py")
else:
    fmt, n, tris, _nrm = read_stl(STL)
    v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
    cross = np.cross(v1 - v0, v2 - v0)
    nlen = np.linalg.norm(cross, axis=1)
    area = 0.5 * nlen
    nz = np.divide(cross[:, 2], nlen, out=np.zeros(n), where=nlen > 0)
    lo = tris[:, :, 2].min(axis=1)
    hi = tris[:, :, 2].max(axis=1)
    vol = abs(np.einsum("ij,ij->i", v0, np.cross(v1, v2)).sum() / 6)
    bbox = tris.reshape(-1, 3).max(axis=0) - tris.reshape(-1, 3).min(axis=0)
    zmin = tris[:, :, 2].min()
    print(f"      STL {fmt} {n} 面，包围盒 [{bbox[0]:.2f} {bbox[1]:.2f} {bbox[2]:.2f}]，"
          f"体积 {vol/1000:.3f}cm³，解析 {p['V_no_text']/1000:.3f}cm³（未含浮雕）")

    check(len(np.unique(face_components(tris))) == 1, "单件连通（一块打完，不用拼）",
          f"连通块 {len(np.unique(face_components(tris)))}")
    want_bbox = (p["outer_w"], p["outer_d"] + p["brand_raise"], p["outer_h"])
    check(all(abs(a - b) <= 0.05 for a, b in zip(bbox, want_bbox)), "包围盒 = 参数（Y 含浮雕凸起）",
          f"实测 {[round(v, 2) for v in bbox]} vs {[round(v, 2) for v in want_bbox]}")
    check(abs(vol - p["V_no_text"]) <= VOL_TOL * p["V_no_text"] + 0.2, "体积 = 解析体积（±1%）",
          f"差 {vol/1000 - p['V_no_text']/1000:+.3f} cm³ = {abs(vol-p['V_no_text'])/p['V_no_text']:.2%}")
    check(abs(zmin) <= 0.01, "底面贴床 z=0", f"最低点 z={zmin:.4f}")

    bed = (nz <= -0.99) & (hi <= 0.05)
    want_bed = M.rrect_area(p["outer_w"], p["outer_d"], p["corner_r"]) \
        - len(p["bottom_holes"]) * math.pi * (p["bottom_hole_d"] / 2.0) ** 2
    check(abs(area[bed].sum() - want_bed) <= AREA_TOL * want_bed, "贴床面积 = 外廓底 - 底板孔",
          f"实测 {area[bed].sum():.0f}mm² vs 解析 {want_bed:.0f}mm²")

    down_flat = (nz <= -0.95) & (lo > 0.05)
    span = 0.0
    if down_flat.any():
        t = tris[down_flat]
        edges = np.concatenate([t[:, 1] - t[:, 0], t[:, 2] - t[:, 1], t[:, 0] - t[:, 2]])
        span = float(np.linalg.norm(edges[:, :2], axis=1).max())
    check(span <= M.BRIDGE_MAX + 0.5, "朝下平段跨距 ≤ 桥接上限（孔顶是薄桥，不用支撑）",
          f"最宽 {span:.1f}mm ≤ {M.BRIDGE_MAX}mm")

    steep = (nz < -0.707) & (lo > 0.05) & (nz > -0.95)
    check(area[steep].sum() <= 0.01 * area.sum(), "没有陡悬垂面（45°-72° 那段空着）",
          f"陡下向 {area[steep].sum():.2f}mm² = {area[steep].sum()/area.sum():.2%}")

    # 浮雕：往 -Y 突出去的那一层，必须只在正面出现、字高与参数一致、四个字形状不同（方框会四字同形）
    face_front = -p["outer_d"] / 2.0 - p["brand_raise"] - 0.05
    band_mask = tris[:, :, 1].min(axis=1) <= face_front + 0.1
    band, band_area = tris[band_mask], area[band_mask]
    if len(band) == 0:
        check(False, "正面有凸起浮雕", f"Y ≤ {face_front + 0.1:.2f} 上没有三角面")
    else:
        zr = (band[:, :, 2].min(), band[:, :, 2].max())
        xr = (band[:, :, 0].min(), band[:, :, 0].max())
        check(abs(zr[0] - (p["brand_z"] - p["brand_cap_h"] / 2)) <= 0.3
              and abs(zr[1] - (p["brand_z"] + p["brand_cap_h"] / 2)) <= 0.3, "浮雕高度带 = brand_z ± 字高/2",
              f"z {zr[0]:.2f}..{zr[1]:.2f} vs {p['brand_z'] - p['brand_cap_h']/2:.2f}..{p['brand_z'] + p['brand_cap_h']/2:.2f}")
        check(abs((xr[1] - xr[0]) - brand.get("width", xr[1] - xr[0])) <= 0.5, "浮雕横向幅面 = 字宽",
              f"{xr[1]-xr[0]:.2f} vs {brand.get('width', float('nan')):.2f}")
        cols = np.unique(np.round(band[:, :, 0], 1))
        runs, start = [], cols[0]
        for a, b in zip(cols, cols[1:]):
            if b - a > 0.6:
                runs.append((start, a))
                start = b
        runs.append((start, cols[-1]))
        glyph_area = [float(band_area[(band[:, :, 0].min(axis=1) >= x0 - 0.3)
                                      & (band[:, :, 0].max(axis=1) <= x1 + 0.3)].sum()) for x0, x1 in runs]
        ratio = max(glyph_area) / max(1e-9, min(glyph_area))
        check(len(runs) >= 4 and ratio > 1.15, "汉字是真字形不是方框（方框/缺字会各段同形同积）",
              f"笔画在 X 上分 {len(runs)} 段，面积比 {ratio:.2f}（{'、'.join(f'{a:.0f}' for a in glyph_area)} mm²）")

    r = subprocess.run(["python3", str(SCRIPTS / "check_model.py"), str(STL), "--3mf", str(THREE),
                        "--material", "PLA"], capture_output=True, text=True)
    for line in r.stdout.strip().splitlines():
        print("      " + line.strip())
    check(r.returncode == 0 and "全过" in r.stdout, "check_model 全过（水密/绕序/STL↔3MF）", f"exit={r.returncode}")

    r = subprocess.run(["node", str(SCRIPTS / "cost.mjs"), str(STL), "--material", "PLA", "--json"],
                       capture_output=True, text=True)
    cj = json.loads(r.stdout)["totals"]
    check(0 < cj["massPrintG"] <= MAX_G, f"预计用料 ≤ {MAX_G:.0f}g",
          f"{cj['massPrintG']:.1f} g（满打 {cj['massSolidG']:.1f} g），约 {cj['printHours']:.2f} h，"
          f"{cj['totalCost']:.2f} 元")

bv = build_volume()
if bv:
    check(p["outer_w"] <= bv[0] and p["outer_d"] + p["brand_raise"] <= bv[1] and p["outer_h"] <= bv[2],
          "单件 ≤ 打印机成型尺寸", f"{p['outer_w']:.1f}x{p['outer_d'] + p['brand_raise']:.1f}x{p['outer_h']:.1f} ≤ {bv}")
else:
    print("  skip  单件 ≤ 成型尺寸  台账里没读到 buildVolume")

print(f"\n{'PASS' if not fails else 'FAIL'}  {total - len(fails)}/{total} 项通过"
      + ("" if not fails else "  挂: " + "; ".join(fails)))
sys.exit(0 if not fails else 1)
