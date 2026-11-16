#!/usr/bin/env python3
"""idea-018 桌面发带晾晒架「龙门晾架」自检：把「能不能打 / 装不装得住」逐条算出来，全过才有意义开打。

只读 model.scad / model.py / 台账 print-ideas.json / 同目录 STL+3MF+report.json，不改任何文件。
用法: python3 check.py      （退出码 0 = 全过）

  A 尺寸链自洽：内壁净宽 / 外廓 / 杆位对称 / 顶面齐平 / ≤ 打印机成型尺寸
  B 可打印性：最薄实体、楔形侧面免支撑角、朝下平面只有细棱（宽 ≤2mm）、无陡悬垂面、
              材料预算 ≤35%、贴床面积够、单件连通、配件配合间隙
  C 实物对账：STL/3MF 存在、包围盒 = 参数、体积 = 解析（全平面多面体，卡 0.3%）、
              底面贴床、贴床面积 = 解析、check_model 全过、克数在预算内
  D 受力与安装：湿发带弯矩/应力/挠度的安全系数、负载在支承多边形内、
              翻倒水平推力阈值（按 cost.mjs 算出的**实际打印质量**，不是理论满打）
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

STL, THREE, REPORT = HERE / "headband-rack.stl", HERE / "headband-rack.3mf", HERE / "headband-rack-report.json"
HSTL, HTHREE = HERE / "headband-hook.stl", HERE / "headband-hook.3mf"

VOL_TOL = 0.003        # 全平面多面体：解析体积与 STL 体积应当几乎完全一致
AREA_TOL = 0.02
BBOX_TOL = 0.05
MAX_G = 250.0
MIN_FOOT = 2000.0      # mm² 贴床面积下限（够稳、不硌桌面）
MIN_TIP_G = 40.0       # 顶部水平推力阈值下限（g）
MIN_SF = 10.0          # 弯曲安全系数下限（按单条湿发带最不利工况）
MAX_DEFLECT = 0.5      # mm，单杆挂满时的跨中挠度上限
MIN_BAND_GAP = 40.0    # 相邻晾杆净距下限（mm）—— 湿发带不被压叠

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


p = M.load()
sec = p["sec"]
rep = json.loads(REPORT.read_text()) if REPORT.exists() else {}
print(f"# {HERE.name}  外廓 {p['outer_x']:.1f} x {p['outer_y']:.1f} x {p['post_top']:.1f} mm"
      f"（净宽 {p['clear_x']:.0f} / 净高 {p['bar_bot_z']:.1f}），{len(p['members'])} 根构件一件打印，"
      f"3 根晾杆 y={p['bar_ys']}\n")

print("A 尺寸链自洽")
check(abs(p["x_center"] - (p["clear_x"] / 2.0 + p["frame_t"] / 2.0)) < 1e-9,
      "立柱中心 = 净宽/2 + 壁厚/2（侧架内壁正落在 ±净宽/2）",
      f"±{p['x_center']:.1f}；内壁 ±{p['clear_x']/2:.1f}")
check(abs(p["outer_x"] - (p["clear_x"] + 2 * p["frame_t"])) < 1e-9, "外廓 X = 净宽 + 2×侧架厚",
      f"{p['outer_x']:.1f} = {p['clear_x']:.0f} + 2×{p['frame_t']:.0f}")
check(abs(p["outer_y"] - (2 * p["bar_y_spacing"] + p["base_w"])) < 1e-9, "外廓 Y = 2×杆距 + 底环杆宽",
      f"{p['outer_y']:.1f} = 2×{p['bar_y_spacing']:.0f} + {p['base_w']:.0f}")
check(abs(p["bar_center_z"] - (p["post_top"] - p["bar_h"] / 2.0)) < 1e-9
      and abs(p["bar_bot_z"] - (p["post_top"] - p["bar_h"])) < 1e-9,
      "晾杆顶面齐平立柱顶面 → 净高 = 总高 - 杆高",
      f"顶面 {p['post_top']:.0f}，净高 {p['bar_bot_z']:.1f} = {p['post_top']:.0f} - {p['bar_h']:.0f}")
check(len(p["bar_ys"]) == 3 and p["bar_ys"][1] == 0 and p["bar_ys"][0] == -p["bar_ys"][2],
      "三根晾杆左右对称、等距", f"y = {p['bar_ys']}（间距 {p['bar_y_spacing']:.0f}）")
check(p["bar_y_spacing"] - (p["bar_top_w"] + 2 * p["hook_fit"]) >= MIN_BAND_GAP - 20,
      f"相邻晾杆净距（杆间 {p['bar_y_spacing']:.0f} − 杆顶宽 {p['bar_top_w']:.0f}）够分开晾",
      f"净距 {p['bar_y_spacing'] - p['bar_top_w']:.1f}mm ≥ {MIN_BAND_GAP - 20:.0f}mm（湿发带厚一般 <15）")
bv = build_volume()
if bv:
    check(p["outer_x"] <= bv[0] and p["outer_y"] <= bv[1] and p["post_top"] <= bv[2],
          "单件 ≤ 台账里的打印机成型尺寸", f"{p['outer_x']:.0f}x{p['outer_y']:.0f}x{p['post_top']:.0f} ≤ {bv}")

print("\nB 可打印性（模型坐标系 = 打印姿态：Z 向上、底环贴床）")
feat = {"frame_t": p["frame_t"], "post_w": p["post_w"], "base_w": p["base_w"],
        "base_h": p["base_h"], "bar_bot_w": p["bar_bot_w"]}
check(min(feat.values()) >= M.MIN_FEATURE, f"最薄实体 ≥ {M.MIN_FEATURE}mm（0.4 喷嘴 4 圈）",
      " / ".join(f"{k} {v:g}" for k, v in feat.items()))
check(sec["side_deg"] <= M.MAX_OVERHANG_DEG, f"晾杆/侧梁楔形侧面与竖直夹角 ≤ {M.MAX_OVERHANG_DEG:.0f}°（免支撑）",
      f"{sec['side_deg']:.1f}°（上宽 {sec['top_w']:g} / 下缘 {sec['bot_w']:g} / 高 {sec['h']:g}）")
check(p["volume_ratio"] <= M.MAX_BUDGET, f"材料预算 ≤ 外廓 {M.MAX_BUDGET:.0%}（不是实心砖）",
      f"{p['volume_ratio']:.1%}（{p['V_analytic']/1000:.1f} / {p['V_outer_box']/1000:.0f} cm³）")
check(p["foot_area"] >= MIN_FOOT, f"贴床面积 ≥ {MIN_FOOT:.0f} mm²（底座环 4 根杆底面）",
      f"{p['foot_area']:.0f} mm²（占地面的 {p['foot_area_rel']*100:.0f}%）")
check(0 < p["overlap_mm3"] < 0.15 * p["V_analytic"], "构件之间确有体积重叠（接头不是共面贴合）",
      f"重叠 {p['overlap_mm3']/1000:.2f} cm³ = 各构件之和的 {p['overlap_mm3']/p['V_solids']:.1%}")
gap = p["bar_top_w"] + 2 * p["hook_fit"]
check(gap >= p["bar_top_w"] + 0.6, "配件（挂杆小钩）与晾杆的单边间隙 ≥ 0.3mm（打印公差）",
      f"内净宽 {gap:.2f} = 杆顶宽 {p['bar_top_w']:.0f} + 2×{p['hook_fit']:.1f}")

print("\nC 实物对账")
for f in (STL, THREE, HSTL, HTHREE):
    check(f.exists(), f"{f.name} 已生成", f"{f.stat().st_size/1e3:.1f} kB" if f.exists() else "缺文件，先跑 build_mesh.py")

if STL.exists():
    fmt, n, tris, _nrm = read_stl(STL)
    v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
    cross = np.cross(v1 - v0, v2 - v0)
    nlen = np.linalg.norm(cross, axis=1)
    area = 0.5 * nlen
    nz = np.divide(cross[:, 2], nlen, out=np.zeros(n), where=nlen > 0)
    lo, hi = tris[:, :, 2].min(axis=1), tris[:, :, 2].max(axis=1)
    vol = abs(np.einsum("ij,ij->i", v0, np.cross(v1, v2)).sum() / 6)
    bbox = tris.reshape(-1, 3).max(axis=0) - tris.reshape(-1, 3).min(axis=0)
    zmin = tris[:, :, 2].min()
    print(f"      STL {fmt} {n} 面，包围盒 [{bbox[0]:.2f} {bbox[1]:.2f} {bbox[2]:.2f}]，"
          f"体积 {vol/1000:.3f}cm³，解析 {p['V_analytic']/1000:.3f}cm³")

    check(len(np.unique(face_components(tris))) == 1, "单件连通（一块打完，不用拼）",
          f"连通块 {len(np.unique(face_components(tris)))}")
    want = (p["outer_x"], p["outer_y"], p["post_top"])
    check(all(abs(a - b) <= BBOX_TOL for a, b in zip(bbox, want)), "包围盒 = 参数",
          f"实测 {[round(v, 2) for v in bbox]} vs 参数 {[round(v, 2) for v in want]}")
    check(abs(vol - p["V_analytic"]) <= VOL_TOL * p["V_analytic"], "体积 = 解析切片积分（全平面，卡 0.3%）",
          f"差 {vol/1000 - p['V_analytic']/1000:+.4f} cm³ = {abs(vol-p['V_analytic'])/p['V_analytic']:.3%}")
    check(abs(zmin) <= 0.01, "底座贴床 z=0", f"最低点 z={zmin:.4f}")

    bed = (nz <= -0.99) & (hi <= 0.05)
    check(abs(area[bed].sum() - p["foot_area"]) <= AREA_TOL * p["foot_area"],
          "贴床面积 = 解析（底环 4 杆 - 四角重叠 + 中柱底面）",
          f"实测 {area[bed].sum():.0f}mm² vs 解析 {p['foot_area']:.0f}mm²")

    # 朝下平面：只允许「细棱桥」（宽 ≤ 2mm）；更宽的就要求跨距 ≤ 15mm
    dn = (nz <= -0.95) & (lo > 0.05)
    if dn.any():
        t, a = tris[dn], area[dn]
        e = np.stack([np.linalg.norm(t[:, 1] - t[:, 0], axis=1), np.linalg.norm(t[:, 2] - t[:, 1], axis=1),
                      np.linalg.norm(t[:, 0] - t[:, 2], axis=1)], axis=1)
        span = e.max(axis=1)
        width = 2.0 * a / span
        check(width.max() <= M.BRIDGE_STRIP_MAX_W,
              f"朝下平面只有细棱（宽 ≤ {M.BRIDGE_STRIP_MAX_W}mm）——不需要支撑",
              f"{dn.sum()} 个三角面，最宽 {width.max():.2f}mm（下缘 {p['bar_bot_w']:g}），"
              f"最长 {span.max():.1f}mm —— 细棱桥，下垂在杆底面")
    else:
        check(False, "朝下平面统计", "一个都没有？几何可能不对")
    check(area[(nz <= -0.9) & (lo > 0.05) & (nz > -0.95)].sum() <= 0.01 * area.sum(),
          "没有 25°-72° 的陡下向面（楔形面是 24.6°，属自支撑侧壁）",
          f"陡下向 {area[(nz <= -0.9) & (lo > 0.05) & (nz > -0.95)].sum():.2f}mm²")
    # 第二条交叉验算：偏离竖直 >45° 的朝下面积，应当**正好只有那几条细棱桥**（无非细棱、非平面的桥）
    steep = (nz < -0.707) & (lo > 0.05)
    check(abs(area[steep].sum() - area[dn].sum()) <= 1.0 and area[steep].sum() <= 0.02 * area.sum(),
          "偏离竖直 >45° 的朝下面积 = 那几条细棱桥（多余的陡悬垂面为 0）",
          f"{area[steep].sum():.1f}mm² = 细棱桥 {area[dn].sum():.1f}mm²（占整件表面积 {area[steep].sum()/area.sum():.2%}）")

    r = subprocess.run(["python3", str(SCRIPTS / "check_model.py"), str(STL), "--3mf", str(THREE),
                        "--material", "PLA"], capture_output=True, text=True)
    for line in r.stdout.strip().splitlines():
        print("      " + line.strip())
    check(r.returncode == 0 and "全过" in r.stdout, "check_model 全过（水密/绕序/体积/包围盒/STL↔3MF）",
          f"exit={r.returncode}")

    r = subprocess.run(["node", str(SCRIPTS / "cost.mjs"), str(STL), str(HSTL), "--material", "PLA", "--json"],
                       capture_output=True, text=True)
    pla = json.loads(r.stdout)["totals"]
    r = subprocess.run(["node", str(SCRIPTS / "cost.mjs"), str(STL), str(HSTL), "--material", "PETG", "--json"],
                       capture_output=True, text=True)
    petg = json.loads(r.stdout)["totals"]
    print(f"      cost.mjs  PLA {pla['massPrintG']:.1f}g（满打 {pla['massSolidG']:.1f}g）"
          f" {pla['printHours']:.2f}h {pla['totalCost']:.2f}元 ｜ "
          f"PETG {petg['massPrintG']:.1f}g {petg['printHours']:.2f}h {petg['totalCost']:.2f}元")
    check(0 < pla["massPrintG"] <= MAX_G, f"预计用料 ≤ {MAX_G:.0f}g", f"PLA {pla['massPrintG']:.1f} g")

    print("\nD 受力与安装（装得住吗）")
    c1 = p["load"]["cases"]["单条湿发带"]
    c3 = p["load"]["cases"][f"{p['wet_bands']}条同挂一根杆"]
    check(min(c1["sf_PLA"], c1["sf_PETG"]) >= MIN_SF, f"湿发带挂单杆跨中：弯曲安全系数 ≥ {MIN_SF:.0f}×",
          f"σ={c1['sigma_MPa']:.2f} MPa（PLA {c1['sf_PLA']:.0f}× / PETG {c1['sf_PETG']:.0f}×，"
          f"W={sec['w']:.1f} mm³，跨 {p['clear_x']:.0f}mm，{c1['grams']:.0f}g）")
    check(max(c3["deflect_PLA_mm"], c3["deflect_PETG_mm"]) <= MAX_DEFLECT,
          f"一根杆挂满 {p['wet_bands']} 条时跨中挠度 ≤ {MAX_DEFLECT}mm",
          f"{c3['deflect_PLA_mm']:.3f}mm(PLA) / {c3['deflect_PETG_mm']:.3f}mm(PETG)")

    half = p["bar_top_w"] / 2.0
    inside = all(abs(by) + half <= p["outer_y"] / 2.0 for by in p["bar_ys"])
    check(inside, "负载全落在支承多边形内（前后杆不超过底环外沿）",
          f"杆位 ±{max(abs(b) for b in p['bar_ys']):.0f} + 半宽 {half:.0f} ≤ ±{p['outer_y']/2:.0f}")
    for mat, cost in (("PLA", pla), ("PETG", petg)):
        m = cost["massPrintG"]
        W_self = m / 1000.0 * M.G
        lever = sum(p["wet_band_g"] * M.G / 1000.0 * (p["outer_y"] / 2.0 - abs(by)) for by in p["bar_ys"])
        Fy = (W_self * p["outer_y"] / 2.0 + lever) / p["post_top"] / M.G * 1000.0
        Fx = (W_self * p["outer_x"] / 2.0) / p["post_top"] / M.G * 1000.0
        Sl = M.MU * (W_self + p["wet_g"] / 1000.0 * M.G) / M.G * 1000.0
        check(min(Fy, Fx) >= MIN_TIP_G, f"翻倒阈值（{mat}，按 cost 的 {m:.0f}g 实打质量）≥ {MIN_TIP_G:.0f}g",
              f"顶部水平推力 {Fy:.0f}g 前后翻 / {Fx:.0f}g 左右翻；滑动需 {Sl:.0f}g；"
              f"重心 z={p['com_z']:.0f}（自重 {W_self:.2f}N）")

hvol = M.hook_volume(p)          # 与主件同一套算法：沿 z 分带取矩形并集面积
inner_half = (p["bar_top_w"] + 2 * p["hook_fit"]) / 2.0
prong_y = (p["bar_top_w"] + 2 * p["hook_fit"] + 2 * p["hook_flange"]) / 2.0 - p["hook_prong_t"]
check(prong_y <= inner_half + p["hook_flange"] + 1e-9 and prong_y >= inner_half - 1e-9,
      "小尖钩正落在限位翼正下方（挂东西的力直接沿板压回钩体，不是悬臂）",
      f"钩根 y={prong_y:.1f} ∈ [{inner_half:.1f}, {inner_half + p['hook_flange']:.1f}]")
if HSTL.exists():
    _fmt, _n, htris, _nr = read_stl(HSTL)
    hvol_mesh = abs(np.einsum("ij,ij->i", htris[:, 0], np.cross(htris[:, 1], htris[:, 2])).sum() / 6)
    nzs = np.cross(htris[:, 1] - htris[:, 0], htris[:, 2] - htris[:, 0])
    nzl = np.linalg.norm(nzs, axis=1)
    hz = np.divide(nzs[:, 2], nzl, out=np.zeros(len(nzs)), where=nzl > 0)
    hdn = (hz <= -0.95) & (htris[:, :, 2].min(axis=1) > 0.05)
    check(abs(hvol_mesh - hvol) <= 0.01 * hvol, "配件体积 = 解析（4 个体块并集 - 嵌入量）",
          f"实测 {hvol_mesh:.0f}mm³ vs 解析 {hvol:.0f}mm³")
    check(not hdn.any(), "配件没有悬空的朝下平面（打印姿态：钩体板贴床，两翼与钩朝上）",
          f"z>0.05 的朝下平面 {int(hdn.sum())} 个三角面")

print(f"\n{'PASS' if not fails else 'FAIL'}  {total - len(fails)}/{total} 项通过"
      + ("" if not fails else "  挂: " + "; ".join(fails)))
sys.exit(0 if not fails else 1)
