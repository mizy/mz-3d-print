#!/usr/bin/env python3
"""idea-014 白菜叶冰箱贴自检：把「能不能打」逐条算出来，全过才有意义开打。

只读 model.scad / model.py / 台账 print-ideas.json 与同目录 STL，不改任何文件。
用法: python3 check.py      （退出码 0 = 全过）

  A 设计自洽：总厚 = 板厚 + 叶脉露出；Y 外廓 = 轮廓最大半宽×2；波边；叶脉不出轮廓；
              槽径 = 磁铁 φ + 压入间隙；槽深 = 磁铁厚；两槽关于叶轴镜像
  B 可打印性：板厚 / 槽顶剩料 / 槽到轮廓净壁厚 / 桥接跨距 / 两槽边距 /
              轮廓采样间距 / 外廓 ≤ 成型尺寸
  C 实物对账：STL 水密绕序（check_model）、包围盒 = 参数、体积 = 解析体积、
              陡悬垂面 ≈ 0、唯一的朝下水平面 = 两个槽顶（桥接）、克数
"""
import json
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

STL = HERE / "leaf-fridge-magnet.stl"
THREE = HERE / "leaf-fridge-magnet.3mf"

MIN_PLATE = 1.6
MIN_RELIEF = 0.6
MIN_VEIN_W = 0.8
MIN_EDGE = 0.8          # 叶脉到轮廓留边
MIN_STEP = 1.2
STEEP_LO, STEEP_HI = 0.707, 0.95   # 「陡但不到水平」= 真悬垂；|nz|>0.95 = 水平面（桥接）
VOL_TOL = 0.01
BRIDGE_TOL = 0.03
MAX_G = 25.0

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
print(f"# {HERE.name}  外廓 {p['BBOX_X']:.1f} x {p['BBOX_Y']:.1f} x {p['BBOX_Z']:.1f} mm，"
      f"{p['vein_count']} 条叶脉，{p['pocket_count']} 个 φ{p['pocket_d']:.2f}x{p['pocket_depth']:.0f} 磁铁槽\n")

print("A 设计自洽")
check(abs(p["BBOX_Z"] - (p["leaf_t"] + p["vein_protrusion"])) < 1e-9, "总厚 = 板厚 + 叶脉露出",
      f"{p['BBOX_Z']:.1f} = {p['leaf_t']:.1f} + {p['vein_protrusion']:.1f}")
check(abs(p["BBOX_Y"] - 2 * p["max_half_w"]) < 1e-9, "Y 外廓 = 最大半宽×2",
      f"{p['BBOX_Y']:.2f} = 2 × {p['max_half_w']:.2f}")
check(39.5 <= p["BBOX_Y"] <= 40.5, "Y 外廓贴着设计目标 40", f"{p['BBOX_Y']:.2f} mm")
check(0.50 <= p["u_at_max"] <= 0.80, "最宽处落在叶身偏后段", f"u={p['u_at_max']:.2f}")
check(p["wave_ripple"] >= 1.0, "波边峰谷幅度做出来了", f"{p['wave_ripple']:.2f}mm ≥1.0")
check(p["vein_edge"] >= MIN_EDGE, "叶脉不出轮廓（不会改写外廓）", f"最小留边 {p['vein_edge']:.2f}mm ≥ {MIN_EDGE}mm")
worst_vein = min(min(v["w0"], v["w1"]) for v in p["veins"])
check(worst_vein >= MIN_VEIN_W, "最窄叶脉宽 ≥ 0.8mm", f"{worst_vein:.2f}mm")
check(abs(p["pocket_d"] - (p["magnet_d"] + p["fit_clear"])) < 1e-9, "槽径 = 磁铁 φ + 压入间隙",
      f"{p['pocket_d']:.2f} = {p['magnet_d']:.0f} + {p['fit_clear']:.2f}")
check(0.2 <= p["fit_clear"] <= 0.3, "压入间隙在 FDM 装配区间",
      f"{p['fit_clear']:.2f}mm ∈ [0.20, 0.30]（孔打出来会缩，别做零间隙）")
check(abs(p["pocket_depth"] - p["magnet_t"]) <= 0.2, "槽深 = 磁铁厚 ±0.2（压入后不埋没）",
      f"{p['pocket_depth']:.1f} vs 磁铁厚 {p['magnet_t']:.1f}")
check(p["pocket_mirror_dev"] <= 0.01, "两槽关于叶轴镜像成对（吸力对称不翘）",
      f"最大偏差 {p['pocket_mirror_dev']:.3f}mm（x 相同、y 互为相反数）")

print("\nB 可打印性（背面贴床、叶脉朝上、槽口朝下）")
check(p["leaf_t"] >= MIN_PLATE, "板厚够厚", f"{p['leaf_t']:.1f}mm ≥ {MIN_PLATE}mm")
check(p["vein_protrusion"] >= MIN_RELIEF, "叶脉凸起够高", f"{p['vein_protrusion']:.1f}mm ≥ {MIN_RELIEF}mm")
check(p["pocket_ceiling"] >= MIN_PLATE, "槽顶剩料够厚（磁铁不能顶穿正面）",
      f"板厚 {p['leaf_t']:.1f} - 槽深 {p['pocket_depth']:.1f} = {p['pocket_ceiling']:.1f}mm ≥ {MIN_PLATE}mm")
check(p["pocket_edge"] >= p["min_edge"], "槽圆周到轮廓留够净壁厚",
      f"{p['pocket_edge']:.2f}mm ≥ {p['min_edge']:.1f}mm")
check(p["pocket_d"] <= p["bridge_max"], "槽顶圆桥跨距在桥接能力内",
      f"φ{p['pocket_d']:.2f} ≤ {p['bridge_max']:.0f}mm（背面贴床，槽顶是水平圆桥，不用支撑）")
check(p["pocket_gap"] >= 3.0, "两槽之间留料", f"最近边距 {p['pocket_gap']:.2f}mm ≥ 3.0mm")
check(p["step_mm"] <= MIN_STEP, "轮廓采样够密（波边不被切平）",
      f"最大间距 {p['step_mm']:.2f}mm ≤ {MIN_STEP}mm")
bv = build_volume()
if bv:
    check(p["BBOX_X"] <= bv[0] and p["BBOX_Y"] <= bv[1] and p["BBOX_Z"] <= bv[2],
          "外廓在打印机成型尺寸内",
          f"{p['BBOX_X']:.0f}x{p['BBOX_Y']:.0f}x{p['BBOX_Z']:.0f} ≤ {bv}")
else:
    print("  skip  外廓 ≤ 成型尺寸  台账里没读到 buildVolume")

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
    vol = abs(np.einsum("ij,ij->i", v0, np.cross(v1, v2)).sum() / 6)
    bbox = tris.reshape(-1, 3).max(axis=0) - tris.reshape(-1, 3).min(axis=0)
    zmin = tris[:, :, 2].min()
    print(f"      STL {fmt} {n} 面，包围盒 [{bbox[0]:.2f} {bbox[1]:.2f} {bbox[2]:.2f}]，"
          f"体积 {vol/1000:.3f}cm³，解析 {p['V_analytic']/1000:.3f}cm³")

    check(abs(zmin) <= 0.01, "背面贴床 z=0", f"最低点 z={zmin:.4f}")
    for ax, name, want in ((0, "X", p["BBOX_X"]), (1, "Y", p["BBOX_Y"]), (2, "Z", p["BBOX_Z"])):
        check(abs(bbox[ax] - want) <= 0.1, f"STL {name} 外廓 = 参数", f"实测 {bbox[ax]:.3f} / 期望 {want:.3f} mm")
    check(abs(vol - p["V_analytic"]) <= VOL_TOL * p["V_analytic"], "STL 体积 = 解析体积",
          f"差 {abs(vol-p['V_analytic'])/p['V_analytic']:.2%} ≤ {VOL_TOL:.0%}")
    steep = (nz < -STEEP_LO) & (nz > -STEEP_HI) & (lo > 0.05)
    check(area[steep].sum() < 0.01 * area.sum(), "没有陡悬垂面（不用支撑）",
          f"陡下向（{STEEP_LO}~{STEEP_HI}）{area[steep].sum()/100:.2f}cm² "
          f"= {area[steep].sum()/area.sum():.2%}")
    bridge = (nz <= -STEEP_HI) & (lo > 0.05)
    check(abs(area[bridge].sum() - p["bridge_area"]) <= BRIDGE_TOL * p["bridge_area"],
          "唯一的朝下水平面 = 两个槽顶（桥接）",
          f"实测 {area[bridge].sum():.1f}mm² vs 2×槽口 {p['bridge_area']:.1f}mm²")

    r = subprocess.run(["python3", str(SCRIPTS / "check_model.py"), str(STL), "--3mf", str(THREE),
                        "--material", "PLA"], capture_output=True, text=True)
    for line in r.stdout.strip().splitlines():
        print("      " + line.strip())
    check(r.returncode == 0 and "全过" in r.stdout, "check_model 全过（水密/绕序/STL↔3MF）", f"exit={r.returncode}")

    r = subprocess.run(["node", str(SCRIPTS / "cost.mjs"), str(STL), "--material", "PLA", "--json"],
                       capture_output=True, text=True)
    cj = json.loads(r.stdout)["totals"]
    check(0 < cj["massPrintG"] <= MAX_G, f"预计用料 ≤ {MAX_G:.0f}g",
          f"{cj['massPrintG']:.2f} g（满打 {cj['massSolidG']:.2f} g），约 {cj['printHours']:.2f} h，"
          f"{cj['totalCost']:.2f} 元")

print(f"\n{'PASS' if not fails else 'FAIL'}  {total - len(fails)}/{total} 项通过"
      + ("" if not fails else "  挂: " + "; ".join(fails)))
sys.exit(0 if not fails else 1)
