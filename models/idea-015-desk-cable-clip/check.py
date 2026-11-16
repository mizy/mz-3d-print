#!/usr/bin/env python3
"""idea-015 桌面理线夹（三规格）自检：把「能不能打」逐条算出来，全过才有意义开打。

只读 model.scad / model.py / 台账 print-ideas.json 与同目录 STL，不改任何文件。
用法: python3 check.py      （退出码 0 = 全过）

  A 参数自洽：每规格 总高 / 总宽 / 孔中心高 / 卡入口宽 与线径的关系；排布不重叠；
              三规格都要有（4/6/8）
  B 可打印性：壁厚（两侧/顶/贴胶面底）/ 贴胶面够不够贴双面胶 / 最陡悬垂角 ≤45° /
              单件外廓 ≤25x25x20 / 整盘 ≤ 成型尺寸
  C 实物对账：STL 贴床 z=0、包围盒 = 参数、体积 = 解析体积、贴胶面是完整平面、
              无陡悬垂面、无朝下水平面（卡入口开顶，不用桥接）、水密绕序、克数
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

STL = HERE / "cable-clip-3pcs.stl"
THREE = HERE / "cable-clip-3pcs.3mf"

MIN_WALL = 2.4         # 最薄实心壁厚
MIN_BASE = 1.6         # 贴胶面到底的最低剩料
MIN_TAPE = 80.0        # 单件贴胶面面积（够贴一条 12mm 宽双面胶）
MAX_OVERHANG = 45.0    # 悬垂角上限（超过就要支撑）
MAX_STEEP_AREA = 0.01  # 陡悬垂面（|nz|>0.707 且朝下）面积占比上限
VOL_TOL = 0.01
TAPE_TOL = 0.01
MAX_G = 30.0

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


p = M.load()
print(f"# {HERE.name}  整盘 {p['pack_x']:.1f} x {p['pack_y']:.1f} x {p['pack_z']:.1f} mm，"
      f"{p['clip_count']} 颗（" + "、".join(f"φ{g['d']:.0f}" for g in p["clips"]) + "）\n")

print("A 参数自洽")
check(sorted(g["d"] for g in p["clips"]) == [4, 6, 8], "三规格齐（φ4 / φ6 / φ8）",
      "、".join(f"φ{g['d']:.0f}" for g in p["clips"]))
for g in p["clips"]:
    tag = f"（{g['name']}）"
    check(abs(g["h"] - (p["tape_base"] + g["d"] + p["top_wall"])) < 1e-9, f"总高 = 贴胶底 + 线径 + 顶壁{tag}",
          f"{g['h']:.1f} = {p['tape_base']:.1f} + {g['d']:.0f} + {p['top_wall']:.1f}")
    check(abs(g["dd"] - (g["d"] + 2 * p["side_wall"])) < 1e-9, f"总宽 = 线径 + 2×侧壁{tag}",
          f"{g['dd']:.1f} = {g['d']:.0f} + 2×{p['side_wall']:.1f}")
    check(abs(g["z_axis"] - (p["tape_base"] + g["d"] / 2)) < 1e-9, f"孔中心高 = 贴胶底 + 半径{tag}",
          f"{g['z_axis']:.1f}")
    check(0.80 <= p["slot_ratio"] <= 0.95, f"卡入口宽 = {p['slot_ratio']:.2f}×线径（能塞进又卡得住）{tag}",
          f"{g['slot']:.2f} vs 线径 {g['d']:.0f}（{p['slot_ratio']*100:.0f}%）")
gaps = [p["clips"][i + 1]["x0"] - (p["clips"][i]["x0"] + p["clip_w"]) for i in range(len(p["clips"]) - 1)]
check(min(gaps) >= p["pack_gap"] - 1e-9, "三颗排布互不粘连（一次打多颗）",
      f"最小间距 {min(gaps):.1f}mm ≥ {p['pack_gap']:.0f}mm（机头/风扇有空间）")

print("\nB 可打印性（贴胶面平贴热床、卡入口朝上）")
for g in p["clips"]:
    tag = f"（{g['name']}）"
    check(p["side_wall"] >= MIN_WALL, f"孔两侧壁厚 ≥ {MIN_WALL}{tag}", f"{p['side_wall']:.1f}mm")
    check(p["top_wall"] >= 2.0, f"孔顶壁厚 ≥ 2.0{tag}", f"{p['top_wall']:.1f}mm")
    check(p["tape_base"] >= MIN_BASE, f"贴胶面剩料 ≥ {MIN_BASE}{tag}", f"{p['tape_base']:.1f}mm")
    check(g["tape_area"] >= MIN_TAPE, f"贴胶面够大 ≥ {MIN_TAPE:.0f}mm²{tag}",
          f"{g['tape_area']:.0f}mm²（{p['clip_w']:.0f} × {g['dd']:.1f}）")
    check(g["overhang_deg"] <= MAX_OVERHANG, f"最陡悬垂角 ≤ {MAX_OVERHANG:.0f}°{tag}",
          f"{g['overhang_deg']:.1f}°（孔壁在卡入口那一点，法线离水平这么远）")
    check(g["slot_wall_h"] >= 1.5, f"卡入口竖直段够长（能卡住线）{tag}", f"{g['slot_wall_h']:.1f}mm")
    w, dd, h = g["bbox"]
    check(w <= p["single_max"] and dd <= p["single_max"] and h <= p["single_max_h"],
          f"单件外廓 ≤ {p['single_max']:.0f}x{p['single_max']:.0f}x{p['single_max_h']:.0f}{tag}",
          f"{w:.0f} x {dd:.1f} x {h:.1f} mm")
check(p["overhang_max"] <= MAX_OVERHANG, "全盘最陡悬垂角 ≤ 45°（免支撑）", f"{p['overhang_max']:.1f}°")
bv = build_volume()
if bv:
    check(p["pack_x"] <= bv[0] and p["pack_y"] <= bv[1] and p["pack_z"] <= bv[2],
          "整盘外廓 ≤ 打印机成型尺寸",
          f"{p['pack_x']:.0f}x{p['pack_y']:.1f}x{p['pack_z']:.1f} ≤ {bv}")
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

    check(abs(zmin) <= 0.01, "贴胶面贴床 z=0", f"最低点 z={zmin:.4f}")
    for ax, name, want in ((0, "X", p["pack_x"]), (1, "Y", p["pack_y"]), (2, "Z", p["pack_z"])):
        check(abs(bbox[ax] - want) <= 0.1, f"STL {name} 外廓 = 参数", f"实测 {bbox[ax]:.3f} / 期望 {want:.3f} mm")
    check(abs(vol - p["V_analytic"]) <= VOL_TOL * p["V_analytic"], "STL 体积 = 解析体积",
          f"差 {abs(vol-p['V_analytic'])/p['V_analytic']:.2%} ≤ {VOL_TOL:.0%}")
    tape = (nz <= -0.99) & (hi_z <= 0.05)
    check(abs(area[tape].sum() - p["tape_area_total"]) <= TAPE_TOL * p["tape_area_total"],
          "贴胶面 = 完整的水平平面（双面胶贴面）",
          f"实测 {area[tape].sum():.0f}mm² vs 3×{p['clip_w']:.0f}×dd = {p['tape_area_total']:.0f}mm²")
    steep = (nz < -0.707) & (lo > 0.05)
    check(area[steep].sum() <= MAX_STEEP_AREA * area.sum(), "没有陡悬垂面（免支撑）",
          f"陡下向 {area[steep].sum():.2f}mm² = {area[steep].sum()/area.sum():.2%}")
    flat_down = (nz <= -0.95) & (lo > 0.05)
    check(area[flat_down].sum() <= 0.01 * area.sum(), "没有朝下水平面（不用桥接）",
          f"{area[flat_down].sum():.2f}mm²（卡入口开顶，孔顶不封）")

    r = subprocess.run(["python3", str(SCRIPTS / "check_model.py"), str(STL), "--3mf", str(THREE),
                        "--material", "PLA"], capture_output=True, text=True)
    for line in r.stdout.strip().splitlines():
        print("      " + line.strip())
    check(r.returncode == 0 and "全过" in r.stdout, "check_model 全过（水密/绕序/STL↔3MF）", f"exit={r.returncode}")

    r = subprocess.run(["node", str(SCRIPTS / "cost.mjs"), str(STL), "--material", "PLA", "--json"],
                       capture_output=True, text=True)
    cj = json.loads(r.stdout)["totals"]
    check(0 < cj["massPrintG"] <= MAX_G, f"预计用料 ≤ {MAX_G:.0f}g（三颗合计）",
          f"{cj['massPrintG']:.2f} g（满打 {cj['massSolidG']:.2f} g），约 {cj['printHours']:.2f} h，"
          f"{cj['totalCost']:.2f} 元")

print(f"\n{'PASS' if not fails else 'FAIL'}  {total - len(fails)}/{total} 项通过"
      + ("" if not fails else "  挂: " + "; ".join(fails)))
sys.exit(0 if not fails else 1)
