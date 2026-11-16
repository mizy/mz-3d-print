#!/usr/bin/env python3
"""idea-020「小人晾架」自检：把「能不能打 / 站不站得住 / 装不装得住」逐条算出来。

只读 model.scad / model.py / 台账 print-ideas.json / 同目录 STL+3MF+report.json，不改任何文件。
用法: python3 check.py      （退出码 0 = 全过）

  A 尺寸链自洽：底盘 ≥ 肩宽 1.2 倍 / 配重槽装得下 Ø25 硬币 / 中央台装得下裙摆 /
              头球外露起点免支撑 / 手臂抬起角 / 挂点落在底盘内 / ≤ 打印机成型尺寸
  B 可打印性：最小实体、接头全是体积咬合（无共面贴合）、材料预算、贴床面积、
              单件连通、朝下平面跨距 ≤15mm、陡悬垂面积 = 朝下平面面积（没有额外陡悬垂）
  C 实物对账：STL/3MF 存在、包围盒 = 参数、体积 = OCC = 体素外推 = 网格、
              重心三条路线一致、接触凸包 = 底盘轮廓、check_model 全过、克数在预算内
  D 稳定性与受力：组合重心到支承边余量（空载/单侧挂满/保守/超载）、倾覆临界外伸、
              水平推力与滑动阈值、配重效果、晾杆与手臂的弯曲应力与挠度
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

STL, THREE, REPORT = HERE / "figure-rack.stl", HERE / "figure-rack.3mf", HERE / "figure-rack-report.json"

VOL_TOL = 0.003        # 网格体积 vs OCC 体积（头球面按 0.08rad 三角化，实测差 ~0.1%）
GRID_TOL = 0.01        # 体素外推 vs OCC（离散化误差）
BBOX_TOL = 0.05
HULL_TOL = 1.0         # 网格反推接触凸包 vs 参数底盘轮廓（mm）
MAX_G = 260.0          # 预计用料上限
MIN_FOOT = 3000.0      # mm² 贴床面积下限
MIN_MARGIN = 10.0      # mm 组合重心到支承边余量下限
MIN_TIP_G = 40.0       # 顶部水平推力阈值下限（g）
MIN_SF = 10.0          # 弯曲安全系数下限
MAX_DEFLECT = 0.5      # mm 跨中/端部挠度上限
MIN_ROOM_MM = 2.0      # 拳在杆上下各留的手指厚度下限（环握判据，掌托式做不到下方有料）

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
    """面片按共享边并查集 -> 连通块个数（顶点按 1e-4 取整当同一顶点）。"""
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


def mesh_volume_com(tris):
    """网格体积 + 重心（docs/stability-load-analysis.md §5.1 的有符号四面体积分）。"""
    v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
    vi = np.einsum("ij,ij->i", v0, np.cross(v1, v2)) / 6.0
    ci = (v0 + v1 + v2) / 4.0
    vol = vi.sum()
    com = (vi[:, None] * ci).sum(axis=0) / vol
    return abs(vol), np.abs(com)


def convex_hull_2d(pts):
    """二维凸包（单调链），pts = [(x,y)...] -> 逆时针顶点表。"""
    pts = sorted(set((round(x, 6), round(y, 6)) for x, y in pts))
    if len(pts) <= 2:
        return pts

    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (p[1] - out[-2][1])
                                     - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out

    return half(pts)[:-1] + half(pts[::-1])[:-1]


p = M.load()
sec = p["sec"]
rep = json.loads(REPORT.read_text()) if REPORT.exists() else {}
print(f"# {HERE.name}  外廓 {p['bbox'][0]:.1f} x {p['bbox'][1]:.1f} x {p['bbox'][2]:.1f} mm"
      f"（底盘 {2*p['base_rx']:.0f}x{2*p['base_ry']:.0f} 厚 {p['base_h']:.0f}、肩宽 {p['shoulder_w']:.0f}、"
      f"头径 {2*p['head_r']:.0f}、杆 y±{p['bar_half']:.0f}、杆距 {2*p['hand_x']:.0f}）\n")

print("A 尺寸链自洽")
check(2 * p["base_rx"] >= 1.2 * p["shoulder_w"], "底盘宽 ≥ 肩宽 1.2 倍（主人要求）",
      f"{2*p['base_rx']:.0f} ≥ 1.2×{p['shoulder_w']:.0f} = {1.2*p['shoulder_w']:.1f}"
      f"（{2*p['base_rx']/(1.2*p['shoulder_w']):.1f} 倍余量）")
hub_room = p["hub_rx"] - p["hip_r_bot"]
check(hub_room >= 2.0, "底盘中央台（小人站位）装得下裙摆底圆",
      f"中央台半宽 {p['hub_rx']:.0f} − 裙摆底半径 {p['hip_r_bot']:.0f} = {hub_room:.0f}mm 余量")
check(p["groove_w"] >= 25.0, "配重槽净宽装得下 Ø25 硬币（平放）",
      f"槽宽 {p['groove_w']:.0f} ≥ 25，槽深 {p['groove_d']:.1f}（1 元硬币厚 1.85，可叠 2 枚）")
check(p["groove_d"] >= 1.6 and p["rim_w"] >= M.MIN_FEATURE,
      "配重槽底厚 ≥ 1.6、槽外壁（最外实心环）宽度够",
      f"槽底 {p['groove_d']:.1f}mm、外壁环 {p['rim_w']:.0f}mm")
check(p["head_emerge_sin"] >= math.sin(math.radians(45.0)),
      "头球「外露起点」的法向角 ≥45°（头从肩台长出来的那一圈免支撑）",
      f"外露半径 {p['head_emerge_r']:.2f} → sin={p['head_emerge_sin']:.3f} ≥ 0.707"
      f"（等效悬垂 {math.degrees(math.asin(p['head_emerge_sin'])) - 0:.1f}° 从水平算）")
r_torso_at_cut = p["torso_r_bot"] + (p["torso_r_top"] - p["torso_r_bot"]) * \
    (p["head_cut_z"] - p["torso_z_bot"]) / (p["torso_z_top"] - p["torso_z_bot"])
check(p["head_cut_r"] < r_torso_at_cut, "头球下切面埋在躯干里（不外露 → 不会留朝下大平面）",
      f"切面 r={p['head_cut_r']:.0f} < 躯干在 z={p['head_cut_z']:.0f} 的半径 {r_torso_at_cut:.2f}")
check(p["torso_z_top"] < p["head_flat_z"] and r_torso_at_cut > p["head_cut_r"],
      "躯干顶面咬进头球（体积咬合，不是共面贴合）",
      f"躯干顶 z={p['torso_z_top']:.0f} < 头顶 z={p['head_flat_z']:.1f}")
# 手臂根部切面：绕臂轴一圈取点，逐点验「离 Z 轴的距离 < 该高度的躯干半径」——整块埋在躯干里
_q = math.hypot(p["hand_x"] - p["arm_root_x"], p["bar_z"] - p["arm_root_z"])
_axis = ((p["hand_x"] - p["arm_root_x"]) / _q, 0.0, (p["bar_z"] - p["arm_root_z"]) / _q)
_perp = ((p["bar_z"] - p["arm_root_z"]) / _q, 0.0, -(p["hand_x"] - p["arm_root_x"]) / _q)   # ⊥ 轴，在 XZ 面内
_root_pts = []
for _i in range(72):
    _a = 2 * math.pi * _i / 72
    _pt = (p["arm_root_x"] + p["arm_r_root"] * math.cos(_a) * _perp[0],
           p["arm_r_root"] * math.sin(_a),
           p["arm_root_z"] + p["arm_r_root"] * math.cos(_a) * _perp[2])
    _root_pts.append(_pt)


def _r_torso(z):
    return p["torso_r_bot"] + (p["torso_r_top"] - p["torso_r_bot"]) * \
        (z - p["torso_z_bot"]) / (p["torso_z_top"] - p["torso_z_bot"])


_worst = max((math.hypot(pt[0], pt[1]) - _r_torso(pt[2]), pt) for pt in _root_pts)
check(_worst[0] < 0, "手臂根部切面整块埋在躯干里（否则肩上会露出一块朝下的斜面，需支撑）",
      f"根部 72 点最不利：离轴 {math.hypot(_worst[1][0], _worst[1][1]):.2f} < "
      f"躯干在 z={_worst[1][2]:.1f} 的半径 {_r_torso(_worst[1][2]):.2f}"
      f"（埋深 {-_worst[0]:.2f}mm）")
check(p["strength"]["arm"]["tilt_deg"] <= M.MAX_OVERHANG_DEG,
      f"手臂与竖直夹角 ≤ {M.MAX_OVERHANG_DEG:.0f}°（抬起的手臂免支撑）",
      f"{p['strength']['arm']['tilt_deg']:.1f}°（肩 {p['arm_root_x']:.0f} → 心 {p['hand_x']:.0f}，"
      f"抬 {p['bar_z']-p['arm_root_z']:.0f}）")
hand_above = p["hand_r"] * math.sqrt(3) / 2 - p["bar_r"] * math.sqrt(3) / 2
check(hand_above >= MIN_ROOM_MM, f"拳在杆上下各包住 ≥{MIN_ROOM_MM:.0f}mm（环握：手指围合，不是掌心托）",
      f"拳半高 {p['hand_r']*math.sqrt(3)/2:.2f} − 杆半高 {p['bar_r']*math.sqrt(3)/2:.2f} = "
      f"{hand_above:.2f}mm（杆上方与下方都有实体；掌托式下方不会有料）")
head_at_bar = math.sqrt(max(0.0, p["head_r"] ** 2 - (p["bar_z"] - p["head_cz"]) ** 2))
check(p["hand_x"] - p["hand_r"] >= head_at_bar + 2.0, "拳/杆不与头相碰（留出间隙）",
      f"拳内缘 x={p['hand_x']-p['hand_r']:.1f} ≥ 头在杆高处的半径 {head_at_bar:.2f} + 2")
check(p["stop_r"] - p["bar_r"] >= 2.0, "杆端挡边比杆粗 ≥2mm（发带顺杆滑不过去）",
      f"挡边 r {p['stop_r']:.1f} − 杆 r {p['bar_r']:.1f} = {p['stop_r']-p['bar_r']:.1f}mm 台阶，"
      f"挡边长 {p['stop_len']:.0f}mm")
need_len = p["bands_max"] * p["band_span"]
check(need_len <= p["bar_len"], f"一根杆密排 {p['bands_max']} 条发带需要的杆长 ≤ 实际杆长",
      f"{p['bands_max']}×{p['band_span']:.0f} = {need_len:.0f} ≤ {p['bar_len']:.0f}mm"
      f"（杆净长，不含两端挡边）")
check(p["y_tip"] + p["band_span"] / 2 <= p["bar_half"], "最外一条发带压不到挡边上（挡边内侧还有余量）",
      f"最外挂点 y={p['y_tip']:.0f} + 半宽 {p['band_span']/2:.0f} = {p['y_tip']+p['band_span']/2:.0f}"
      f" ≤ 杆端 {p['bar_half']:.0f}")
# 逐个挂点算它到「真实支承多边形（底盘轮廓）」的内距 —— 挂点越内，载荷只会让整体更稳
_pts = [(-p["hand_x"], p["y_tip"]), (p["hand_x"], p["y_tip"]),
        (-p["hand_x"], p["y_tip"] - (p["bands_max"] - 1) * p["band_span"]),
        (p["hand_x"], p["y_tip"] - (p["bands_max"] - 1) * p["band_span"])]
_margins = [(M._margin(p["hull_pts"], q[0], q[1])[0], q) for q in _pts]
_worst_pt = min(_margins)
check(_worst_pt[0] >= 4.0, "每个挂点在支承多边形内侧 ≥4mm（含最外挂点与杆端内侧那条）",
      f"最不利挂点 ({_worst_pt[1][0]:.0f}, {_worst_pt[1][1]:.0f}) 内距 {_worst_pt[0]:.1f}mm"
      f"（最外挂点 y=±{p['y_tip']:.0f} 对底盘圆角矩形轮廓；"
      f"x 挂点 ±{p['hand_x']:.0f} 对 ±{p['base_rx']:.0f}）")
check(2 * p["hand_x"] >= p["band_span"], "两杆间距够分开（发带不互相压叠）",
      f"杆距 {2*p['hand_x']:.0f} ≥ 单条发带占宽 {p['band_span']:.0f}mm")
bv = build_volume()
if bv:
    check(all(a <= b for a, b in zip(p["bbox"], bv)), "单件 ≤ 台账里的打印机成型尺寸",
          f"{[round(v,1) for v in p['bbox']]} ≤ {bv}")

print("\nB 可打印性（模型坐标系 = 打印姿态：Z 向上、底盘底面贴床）")
feat = {"晾杆底棱": p["bar_r"], "底盘外壁环": p["rim_w"], "配重槽底": p["groove_d"],
        "手臂根部直径": 2 * p["arm_r_root"], "拳底棱": p["hand_r"]}
check(min(feat.values()) >= M.MIN_FEATURE, f"最薄实体 ≥ {M.MIN_FEATURE}mm（0.4 喷嘴 4 圈）",
      " / ".join(f"{k} {v:g}" for k, v in feat.items()))
check(p["volume_ratio"] <= M.MAX_BUDGET, f"材料预算 ≤ 外廓 {M.MAX_BUDGET:.0%}（不是实心砖）",
      f"{p['volume_ratio']:.1%}（{p['V_grid']/1000:.1f} / {p['V_outer_box']/1000:.0f} cm³）")
check(p["foot_area"] >= MIN_FOOT, f"贴床面积 ≥ {MIN_FOOT:.0f} mm²",
      f"{p['foot_area']:.0f} mm²（底盘 94×104 的 {p['foot_area']/(2*p['base_rx']*2*p['base_ry']):.0%}）")
check(abs(p["hub_rx"] - (p["base_rx"] - p["rim_w"] - p["groove_w"])) < 1e-9
      and abs(p["hub_ry"] - (p["base_ry"] - p["rim_w"] - p["groove_w"])) < 1e-9,
      "底盘尺寸链闭合：底盘 = 外壁环 + 配重槽 + 中央台（外壁环与槽同心等宽）",
      f"底盘半宽 {p['base_rx']:.0f} = 外壁 {p['rim_w']:.0f} + 槽 {p['groove_w']:.0f} + 中央台半宽 "
      f"{p['hub_rx']:.0f}（半长同理 {p['base_ry']:.0f} = {p['rim_w']:.0f}+{p['groove_w']:.0f}+{p['hub_ry']:.0f}）")
check(0 < p["V_solids"] - p["V_grid"], "接头确实是体积咬合（各构件之和 > 并集）",
      f"构件和 {p['V_solids']/1000:.1f} − 并集 {p['V_grid']/1000:.1f} = "
      f"{(p['V_solids']-p['V_grid'])/1000:.1f} cm³ 咬合量")

print("\nC 实物对账（STL / 3MF / 报告）")
for f in (STL, THREE, REPORT):
    check(f.exists(), f"{f.name} 已生成", f"{f.stat().st_size/1e3:.1f} kB" if f.exists() else "缺文件，先跑 build_mesh.py")

if STL.exists():
    fmt, n, tris, _nrm = read_stl(STL)
    v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
    cross = np.cross(v1 - v0, v2 - v0)
    nlen = np.linalg.norm(cross, axis=1)
    area = 0.5 * nlen
    nz = np.divide(cross[:, 2], nlen, out=np.zeros(n), where=nlen > 0)
    lo, hi = tris[:, :, 2].min(axis=1), tris[:, :, 2].max(axis=1)
    vol, com = mesh_volume_com(tris)
    bbox = tris.reshape(-1, 3).max(axis=0) - tris.reshape(-1, 3).min(axis=0)
    zmin = tris[:, :, 2].min()
    v_cad = rep["volume"]["cad_occ_mm3"]
    print(f"      STL {fmt} {n} 面，包围盒 [{bbox[0]:.2f} {bbox[1]:.2f} {bbox[2]:.2f}]，"
          f"网格体积 {vol/1000:.3f}cm³，OCC {v_cad/1000:.3f}，体素外推 {p['V_grid']/1000:.3f}cm³")

    check(len(np.unique(face_components(tris))) == 1, "单件连通（一块打完，不用拼）",
          f"连通块 {len(np.unique(face_components(tris)))}")
    check(all(abs(a - b) <= BBOX_TOL for a, b in zip(bbox, p["bbox"])), "包围盒 = 参数",
          f"实测 {[round(v, 2) for v in bbox]} vs 参数 {[round(v, 2) for v in p['bbox']]}")
    check(abs(vol - v_cad) <= VOL_TOL * v_cad, "网格体积 = OCC 体积（球面按 0.08rad 三角化）",
          f"差 {vol/1000 - v_cad/1000:+.4f} cm³ = {abs(vol-v_cad)/v_cad:.3%}")
    check(abs(p["V_grid"] - v_cad) <= GRID_TOL * v_cad, "体素外推体积 = OCC 体积（离散化误差 <1%）",
          f"差 {p['V_grid']/1000 - v_cad/1000:+.4f} cm³ = {abs(p['V_grid']-v_cad)/v_cad:.3%}"
          f"（1.0mm {p['grid']['step_1.0mm']['volume_mm3']/1000:.2f} / "
          f"0.5mm {p['grid']['step_0.5mm']['volume_mm3']/1000:.2f} cm³ 两口采样收敛）")
    check(abs(zmin) <= 0.01, "底盘底面贴床 z=0", f"最低点 z={zmin:.4f}")

    # 接触凸包：z≈0 的朝下面片顶点 -> 二维凸包 -> 与参数底盘轮廓比对
    bed = (nz <= -0.99) & (hi <= 0.05)
    bed_pts = tris[bed][:, :, :2].reshape(-1, 2)
    hull = convex_hull_2d([tuple(q) for q in bed_pts])
    ref = M.roundrect_poly(p["base_rx"], p["base_ry"], p["base_corner_r"])
    dev = 0.0
    for (hx, hy) in hull:                      # 凸包每个顶点到参数轮廓多边形的距离
        d = min(math.dist((hx, hy), (rx, ry)) for rx, ry in ref)
        dev = max(dev, d)
    # 反面：参数轮廓的每个顶点到凸包多边形的距离
    dev2 = 0.0
    for (rx, ry) in ref:
        d = min(math.dist((rx, ry), (hx, hy)) for hx, hy in hull)
        dev2 = max(dev2, d)
    check(dev <= HULL_TOL and dev2 <= HULL_TOL, "接触凸包（网格反推）= 参数底盘轮廓",
          f"凸包 {len(hull)} 点，最大偏差 {dev:.3f} / {dev2:.3f}mm ≤ {HULL_TOL}；"
          f"凸包面积 {abs(sum(hull[i][0]*hull[(i+1) % len(hull)][1] - hull[(i+1) % len(hull)][0]*hull[i][1] for i in range(len(hull))))/2:.0f}"
          f" mm² vs 解析 {p['foot_area']:.0f} mm²")
    check(abs(com[2] - p["com_grid"][2]) <= 0.5 and math.dist(tuple(com), tuple(rep["com_mm"]["cad_occ"])) <= 0.5,
          "重心：网格积分 = OCC = 体素（三条路线一致）",
          f"网格 [{com[0]:.2f} {com[1]:.2f} {com[2]:.2f}]，OCC {rep['com_mm']['cad_occ']}，"
          f"体素 {[round(v,2) for v in p['com_grid']]}")

    # 朝下平面：只允许窄条（≤15mm 跨距）；陡悬垂（法线离正下方 <45°）应当正好是这些窄条
    dn = (nz <= -0.99) & (lo > 0.05)
    span_all = 0.0
    if dn.any():
        # 朝下平面按「同一高度平面 + 共享顶点」分组，每组算水平包围盒的**短边** = 桥接跨距
        idx = np.where(dn)[0]
        zk = {int(i): round(float(tris[i, :, 2].min()), 2) for i in idx}
        vkey = {}
        for i in idx:
            for q in tris[i]:
                vkey.setdefault(tuple(np.round(q, 4)), []).append(int(i))
        par = {int(i): int(i) for i in idx}

        def find(x):
            while par[x] != x:
                par[x] = par[par[x]]
                x = par[x]
            return x

        byv = {}
        for k, fs in vkey.items():
            fs = [f for f in fs if f in par]
            for f in fs[1:]:
                ra, rb = find(fs[0]), find(f)
                if ra != rb:
                    par[ra] = rb
        groups = {}
        for i in idx:
            groups.setdefault((zk[int(i)], find(int(i))), []).append(int(i))
        spans = []
        for (z0, _r), fs in sorted(groups.items()):
            pts = tris[fs][:, :, :2].reshape(-1, 2)
            w = min(pts[:, 0].max() - pts[:, 0].min(), pts[:, 1].max() - pts[:, 1].min())
            spans.append((w, z0, sum(area[f] for f in fs), len(fs)))
        spans.sort(reverse=True)
        span_all = spans[0][0]
        check(span_all <= M.BRIDGE_WIDE_MAX_W,
              f"朝下平面最宽 ≤ {M.BRIDGE_WIDE_MAX_W}mm（窄条桥，不需要支撑）",
              f"{len(spans)} 块朝下平面，最宽 {span_all:.2f}mm"
              f"（" + " / ".join(f"z{z0:.0f} {w:.1f}mm" for w, z0, _a, _c in spans[:4]) + "），"
              f"合计 {area[dn].sum():.0f}mm²")
    steep = (nz < M.OVERHANG_DOWN_Z) & (lo > 0.05)
    check(abs(area[steep].sum() - area[dn].sum()) <= 1.0,
          "陡悬垂面积 = 朝下平面面积（除此之外没有需要支撑的面）",
          f"陡悬垂 {area[steep].sum():.1f}mm² = 朝下平面 {area[dn].sum():.1f}mm²"
          f"（占整件表面积 {area[steep].sum()/area.sum():.2%}，全是宽 ≤{span_all:.1f}mm 的窄条）")
    r = subprocess.run(["python3", str(SCRIPTS / "check_model.py"), str(STL), "--3mf", str(THREE),
                        "--material", "PLA"], capture_output=True, text=True)
    for line in r.stdout.strip().splitlines():
        print("      " + line.strip())
    check(r.returncode == 0 and "全过" in r.stdout, "check_model 全过（水密/绕序/体积/包围盒/STL↔3MF）",
          f"exit={r.returncode}")

    costs = {}
    for mat in ("PLA", "PETG"):
        r = subprocess.run(["node", str(SCRIPTS / "cost.mjs"), str(STL), "--material", mat, "--json"],
                           capture_output=True, text=True)
        costs[mat] = json.loads(r.stdout)["totals"]
        print(f"      cost.mjs {mat}: 预计 {costs[mat]['massPrintG']:.1f}g"
              f"（满打 {costs[mat]['massSolidG']:.1f}g）{costs[mat]['printHours']:.2f}h "
              f"{costs[mat]['totalCost']:.2f}元")
    check(0 < costs["PLA"]["massPrintG"] <= MAX_G, f"预计用料 ≤ {MAX_G:.0f}g",
          f"PLA {costs['PLA']['massPrintG']:.1f} g / PETG {costs['PETG']['massPrintG']:.1f} g")

    print("\nD 稳定性与受力（装得住吗：数字口径见 docs/stability-load-analysis.md）")
    st = p["stability"]["cases"]
    key_pack = "单侧挂满3条（左杆，自杆端向内密排）（无配重）"
    key_cons = "单侧挂满3条（左杆，三条都按杆端质点=保守）（无配重）"
    key_over = "两杆各挂满3条（超载工况）（无配重）"
    key_full = "单侧挂满3条（左杆，自杆端向内密排）（配重+72g硬币）"
    s0 = st["空载（无配重）"]["PLA"]
    check(s0["margin_mm"] >= MIN_MARGIN, f"空载：重心投影距最近支承边 ≥ {MIN_MARGIN:.0f}mm",
          f"重心 ({s0['com_mm'][0]:.1f}, {s0['com_mm'][1]:.1f})，余量 {s0['margin_mm']:.1f}mm"
          f"（自重 {s0['mass_total_g']:.0f}g，重心高 {s0['com_mm'][2]:.1f}）")
    for tag, label in ((key_pack, "单侧挂满 3 条（密排，真实排布）"),
                       (key_cons, "单侧挂满 3 条（三条都压杆端 = 保守上界）")):
        s = st[tag]["PLA"]
        check(s["margin_mm"] >= MIN_MARGIN, f"{label}：重心投影仍在支承多边形内 ≥{MIN_MARGIN:.0f}mm",
              f"总重 {s['mass_total_g']:.0f}g，重心 ({s['com_mm'][0]:.1f}, {s['com_mm'][1]:.1f})，"
              f"余量 {s['margin_mm']:.1f}mm（最近边方位 {s['nearest_edge_az_deg']:.0f}°）")
        check(s["critical_overhang_mm"] >= p["y_tip"],
              f"{label}：倾覆临界外伸 ≫ 实际挂点偏移 → 不会翻（该判据下无有限临界载荷）",
              f"临界外伸 {s['critical_overhang_mm']:.0f}mm ≫ 实际挂点 −底盘边 = "
              f"{p['y_tip'] - p['base_ry']:.0f}mm（挂点在底盘内，载荷越内越稳）")
    so = st[key_over]["PLA"]
    check(so["margin_mm"] >= MIN_MARGIN, "超载（两杆各挂满 3 条 = 6 条 240g）：仍不翻",
          f"总重 {so['mass_total_g']:.0f}g，余量 {so['margin_mm']:.1f}mm")
    sf = st[key_full]["PLA"]
    check(sf["push_to_tip_g"] > s0["push_to_tip_g"], "配重槽塞硬币（72g）提高水平推力阈值（防碰倒）",
          f"推力阈值 {s0['push_to_tip_g']:.0f}g → {sf['push_to_tip_g']:.0f}g（+"
          f"{(sf['push_to_tip_g']/s0['push_to_tip_g']-1)*100:.0f}%），"
          f"移滑阈值 {sf['slide_g']:.0f}g（μ=0.40）/ {sf['slide_g_conservative']:.0f}g（μ=0.25）")
    for tag in (key_pack,):
        s = st[tag]["PLA"]
        check(s["push_to_tip_g"] >= MIN_TIP_G, f"单侧挂满时，杆高处水平推力 ≥ {MIN_TIP_G:.0f}g 才翻",
              f"{s['push_to_tip_g']:.0f}g（推力作用在杆高 {p['bar_z']:.0f}mm，绕最近支承边）")
    b = p["strength"]["bar"]
    c1, c3 = b["单条湿发带"], b[f"一根杆挂满{p['bands_max']}条"]
    check(min(c1["sf_PLA"], c1["sf_PETG"]) >= MIN_SF, f"晾杆抗弯安全系数 ≥ {MIN_SF:.0f}×（单条 40g 挂杆端）",
          f"σ={c1['sigma_bar_MPa']:.2f} MPa（PLA {c1['sf_PLA']:.0f}× / PETG {c1['sf_PETG']:.0f}×），"
          f"端部挠度 {c1['tip_deflect_PLA_mm']:.3f}mm、跨中 {c1['mid_deflect_PLA_mm']:.4f}mm")
    check(max(c3["tip_deflect_PLA_mm"], c3["tip_deflect_PETG_mm"]) <= MAX_DEFLECT,
          f"一根杆挂满 {p['bands_max']} 条（120g）时端部挠度 ≤ {MAX_DEFLECT}mm",
          f"{c3['tip_deflect_PLA_mm']:.3f}mm(PLA) / {c3['tip_deflect_PETG_mm']:.3f}mm(PETG)，"
          f"σ={c3['sigma_bar_MPa']:.2f} MPa（安全系数 {c3['sf_PLA']:.0f}×）")
    a_ = p["strength"]["arm"]
    check(min(a_["sf_PLA"], a_["sf_PETG"]) >= MIN_SF, f"手臂抗弯安全系数 ≥ {MIN_SF:.0f}×（一根杆挂满压在一只手上）",
          f"σ={a_['sigma_MPa']:.2f} MPa（PLA {a_['sf_PLA']:.0f}×）；根部弯矩 {a_['M_Nmm']:.1f} N·mm"
          f"（横向分量法交叉验算 {a_['M_Nmm_cross_check']:.1f}）")
    check(max(a_["tip_deflect_PLA_mm"], a_["tip_deflect_PETG_mm"]) <= MAX_DEFLECT,
          f"手臂端部挠度 ≤ {MAX_DEFLECT}mm", f"{a_['tip_deflect_PLA_mm']:.4f}mm(PLA)")

print(f"\n{'PASS' if not fails else 'FAIL'}  {total - len(fails)}/{total} 项通过"
      + ("" if not fails else "  挂: " + "; ".join(fails)))
sys.exit(0 if not fails else 1)
