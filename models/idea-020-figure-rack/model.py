#!/usr/bin/env python3
"""idea-020「小人晾架」：读 model.scad -> 派生量 + 实体清单 + 网格体积/重心 + 截面 + 受力/翻倒数字。

一份数字只写在一处：`model.scad`。这里只算「由参数推出来的东西」，
`build_mesh.py`（建实体）、`check.py`（自检）都 import 这一份 —— 三者不可能各算各的。

**实体清单只写一遍**（`primitives()`）：build_mesh.py 用 build123d 照着建 CAD，
本文件用同一份清单做「点是否在实体内」的判定，再做体素积分求体积与重心。
两边吃同一个字典，形状不可能跑偏。

四种体素基元（都带解析体积，可交叉对账）：
  prism_z / prism_y  多边形截面棱柱（底盘 = 圆角长条多边形；晾杆/拳/挡边 = 正六边形）
  frustum            圆锥台，轴方向任意（裙摆/躯干/手臂）
  sphere_cut         球被平面切掉下半（头；切面埋在躯干里，不外露）

体积/重心有三条独立路线，互相卡：
  1. V_solids  各构件解析体积之和（含接头重叠，所以偏大）
  2. V_grid    体素积分（点采样），1.0mm 与 0.5mm 两档 + Richardson 外推
  3. V_cad     build123d/OCC 对并集算的精确体积（build_mesh.py 写进报告）
再加上 STL 网格体积（check.py 算）—— 四个数必须落在同一容差带里。

派生量：
  head_cz/head_top        头球球心高 / 整件总高
  hub_rx/hub_ry           底盘中央台（小人站位）的圆角长条半尺寸
  bar_half/bar_span       晾杆半长 / 含两端挡边的总跨
  load                    湿发带受力：弯矩 / 应力 / 挠度 / 安全系数（PLA 与 PETG）
  tipping                 稳定性：组合重心、支承多边形各边余量、翻转临界外伸、水平推力阈值
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SCAD = HERE / "model.scad"
sys.path.insert(0, str(Path.home() / ".cah-data/skills/shared/3d-print-ideas/scripts"))
from scad_params import read_params  # noqa: E402

G = 9.80665                 # m/s²
E_PLA, E_PETG = 3500.0, 2000.0      # MPa（弯曲模量常见值）
SIGMA_PLA, SIGMA_PETG = 50.0, 47.0  # MPa（抗拉强度下限，保守）
MU_WOOD = 0.40              # 打印件 / 木桌面的静摩擦系数（摩擦起作用的工况）
MU_MIN = 0.25               # 保守口径（光面 / 有潮气）
MIN_FEATURE = 1.6           # 0.4 喷嘴 4 圈（skill 口径）
MAX_BUDGET = 0.35           # 材料 ≤ 外廓体积 35%（skill 口径）
MAX_OVERHANG_DEG = 45.0     # 免支撑上限（面法线与「正下方」的夹角）
BRIDGE_WIDE_MAX_W = 15.0    # 朝下平面的最大跨距（更宽的桥就得支撑）
OVERHANG_DOWN_Z = -math.cos(math.radians(MAX_OVERHANG_DEG))   # nz 判据门限 = -0.7071
SEG_ARC_PER_CORNER = 12     # 底盘四角圆弧的分段数（多边形逼近圆弧，总点数 4x13）


# ------------------------------------------------------------ 平面几何工具
def roundrect_poly(rx, ry, rc, seg=SEG_ARC_PER_CORNER):
    """圆角矩形截面（逆时针）：四段圆弧 + 四条直边。rx/ry = X/Y 半尺寸，rc = 四角圆角半径。
    rc=0 退化成矩形；rc=min(rx,ry) 退化成圆角长条（stadium）。
    底盘用它而不是用长条：挂点 (±hand_x, y_tip) 正对着四角，长条的大圆角会把内距吃掉
    （实测长条轮廓下最外挂点只剩 3.1mm 内距，圆角矩形 R12 有 15mm）。"""
    rc = max(0.0, min(rc, rx, ry))
    if rc < 1e-9:
        return [(rx, -ry), (rx, ry), (-rx, ry), (-rx, -ry)]
    pts = []
    for cx, cy, a0 in ((rx - rc, ry - rc, 0.0), (-(rx - rc), ry - rc, 90.0),
                       (-(rx - rc), -(ry - rc), 180.0), (rx - rc, -(ry - rc), 270.0)):
        for i in range(seg + 1):
            a = math.radians(a0 + 90.0 * i / seg)
            pts.append((cx + rc * math.cos(a), cy + rc * math.sin(a)))
    return pts


def hex_poly(r):
    """正六边形（平顶平底）：外接半径 r。平顶/平底棱长 = r，总高 = 1.732*r。
    朝下的平面只有那条宽 r 的底棱 —— 这是免支撑的关键（圆杆的朝下面是渐变的弧，会垂）。"""
    h = r * math.sqrt(3.0) / 2.0
    return [(r, 0.0), (r / 2.0, h), (-r / 2.0, h), (-r, 0.0), (-r / 2.0, -h), (r / 2.0, -h)]


def circle_poly(r, seg=32):
    return [(r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg))
            for i in range(seg)]


def halfplanes(pts):
    """凸多边形的外向单位法线 + 支撑量：(n_i=(nx,ny), d_i)，内部满足 n·p ≤ d。
    法线符号按「质心在内侧」自动修正，所以多边形逆/顺时针都吃。"""
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        ex, ey = x1 - x0, y1 - y0
        n = math.hypot(ex, ey)
        nx, ny = ey / n, -ex / n                    # 顺时针下的外法线
        d = nx * x0 + ny * y0
        if nx * cx + ny * cy > d:                   # 质心在外侧 -> 方向反了
            nx, ny, d = -nx, -ny, -d
        out.append(((nx, ny), d))
    return out


def poly_section(pts):
    """凸多边形截面特性（在 (u,v) 平面里，v 向上）：面积 / 形心 / 抗弯惯性矩 / 上下边缘纤维。
    I 是绕「过形心的水平轴（u 向）」的，配 ξ = M*c/I 用。"""
    a = 0.0
    su = sv = 0.0
    iu = 0.0
    for (u0, v0), (u1, v1) in zip(pts, pts[1:] + pts[:1]):
        cr = u0 * v1 - u1 * v0
        a += cr
        su += (u0 + u1) * cr
        sv += (v0 + v1) * cr
        iu += (v0 * v0 + v0 * v1 + v1 * v1) * cr
    a *= 0.5
    cu, cv = su / (6.0 * a), sv / (6.0 * a)
    i_about_c = abs(iu / 12.0 - a * cv * cv)        # 平行轴定理由形心算
    v_lo = min(p[1] for p in pts)
    v_hi = max(p[1] for p in pts)
    c_top, c_bot = v_hi - cv, cv - v_lo
    return {"area": a, "cu": cu, "cv": cv, "i": i_about_c,
            "c_top": c_top, "c_bot": c_bot, "c_max": max(c_top, c_bot),
            "w_top": i_about_c / c_top, "w_bot": i_about_c / c_bot,
            "h": v_hi - v_lo, "n_pts": len(pts)}


def fc(r0, r1):                                     # 圆锥台体积
    a = math.pi * (r0 * r0 + r0 * r1 + r1 * r1) / 3.0
    return a


# 构件之间的「体积咬合」量（mm）：一律让相邻构件互相咬进去，绝不共面贴合。
# 共面贴合（例如杆端面正好落在挡边内端面上）会让 OCC 并集留退化面、STL 出现非流形边——
# 2026-10-25 实测就是这个原因让 check_model 报「有向边重复 2 条」。
STOP_EMBED = 1.0     # 挡边往杆里咬进 1mm


# ------------------------------------------------------------ 实体清单（唯一一份）
STOP_EMBED = 1.0     # 挡边往杆里咬进 1mm


# ------------------------------------------------------------ 实体清单（唯一一份）


# ------------------------------------------------------------ 实体清单（唯一一份）
def primitives(p):
    """返回 (members, cuts)：每个元素都是「点是否在其中」的一条可判定描述，build_mesh.py 照建。
    坐标 = 模型坐标 = 打印姿态。"""
    rc = p["base_corner_r"]
    base = roundrect_poly(p["base_rx"], p["base_ry"], rc)
    ring = roundrect_poly(p["base_rx"] - p["rim_w"], p["base_ry"] - p["rim_w"], rc - p["rim_w"])
    hub = roundrect_poly(p["hub_rx"], p["hub_ry"],
                         rc - p["rim_w"] - p["groove_w"])   # 圆角被吃光 -> 中央台是直角矩形
    gap = math.hypot(p["hand_x"] - p["arm_root_x"], p["bar_z"] - p["arm_root_z"])
    ax = ((p["hand_x"] - p["arm_root_x"]) / gap, 0.0, (p["bar_z"] - p["arm_root_z"]) / gap)
    arm_len = gap + p["arm_r_hand"]                 # 末端多顶出一点，确保埋进拳里

    members = [
        {"name": "底盘", "kind": "prism_z", "poly": base, "z0": 0.0, "z1": p["base_h"]},
        {"name": "裙摆", "kind": "frustum", "o": (0.0, 0.0, p["hip_z_bot"]), "d": (0.0, 0.0, 1.0),
         "L": p["hip_z_top"] - p["hip_z_bot"], "r0": p["hip_r_bot"], "r1": p["hip_r_top"]},
        {"name": "躯干", "kind": "frustum", "o": (0.0, 0.0, p["torso_z_bot"]), "d": (0.0, 0.0, 1.0),
         "L": p["torso_z_top"] - p["torso_z_bot"], "r0": p["torso_r_bot"], "r1": p["torso_r_top"]},
        {"name": "头", "kind": "sphere_band", "c": (0.0, 0.0, p["head_cz"]), "R": p["head_r"],
         "z0": p["head_cut_z"], "z1": p["head_flat_z"]},
    ]
    for sx in (-1, 1):
        members.append({"name": f"手臂{sx:+d}", "kind": "frustum",
                        "o": (sx * p["arm_root_x"], 0.0, p["arm_root_z"]),
                        "d": (sx * ax[0], 0.0, ax[2]), "L": arm_len,
                        "r0": p["arm_r_root"], "r1": p["arm_r_hand"]})
        members.append({"name": f"拳{sx:+d}", "kind": "prism_y", "poly": hex_poly(p["hand_r"]),
                        "y0": -p["hand_len"] / 2.0, "y1": p["hand_len"] / 2.0,
                        "cx": sx * p["hand_x"], "cz": p["bar_z"]})
        members.append({"name": f"晾杆{sx:+d}", "kind": "prism_y", "poly": hex_poly(p["bar_r"]),
                        "y0": -p["bar_half"], "y1": p["bar_half"],
                        "cx": sx * p["hand_x"], "cz": p["bar_z"]})
        for sy in (-1, 1):
            members.append({"name": f"挡边{sx:+d}{sy:+d}", "kind": "prism_y",
                            "poly": hex_poly(p["stop_r"]),
                            "y0": min(sy * (p["bar_half"] - STOP_EMBED),
                                      sy * (p["bar_half"] + p["stop_len"])),
                            "y1": max(sy * (p["bar_half"] - STOP_EMBED),
                                      sy * (p["bar_half"] + p["stop_len"])),
                            "cx": sx * p["hand_x"], "cz": p["bar_z"]})

    cuts = [{"name": "配重槽", "kind": "prism_z", "poly": ring,
             "z0": p["groove_z"], "z1": p["base_h"] + 1.0, "neg_poly": hub}]
    return members, cuts


def member_volume(m):
    """构件解析体积（用于「各构件之和 vs 并集」的对账）。"""
    k = m["kind"]
    if k == "prism_z":
        return poly_section(m["poly"])["area"] * (m["z1"] - m["z0"])
    if k == "prism_y":
        return poly_section(m["poly"])["area"] * (m["y1"] - m["y0"])
    if k == "frustum":
        return fc(m["r0"], m["r1"]) * m["L"]
    if k == "sphere_band":
        # 球心起算的上下两刀之间的球带体积
        z0, z1 = m["z0"] - m["c"][2], m["z1"] - m["c"][2]
        return abs(math.pi * (m["R"] ** 2 * (z1 - z0) - (z1 ** 3 - z0 ** 3) / 3.0))
    raise ValueError(k)


# ------------------------------------------------------------ 体素积分（体积 + 重心）
def _poly_mask(hp, u, v):
    """凸多边形内部判定：u (nu,)、v (nv,) -> (nu, nv) 布尔。"""
    m = np.ones((u.size, v.size), dtype=bool)
    for (nx, ny), d in hp:
        m &= (nx * u[:, None] + ny * v[None, :]) <= d
    return m


def _inside(members, cuts, X, Y, Z):
    mask = np.zeros((X.size, Y.size, Z.size), dtype=bool)
    for m in members:
        k = m["kind"]
        if k == "prism_z":
            part = _poly_mask(halfplanes(m["poly"]), X, Y)[:, :, None] \
                & ((Z >= m["z0"]) & (Z <= m["z1"]))[None, None, :]
        elif k == "prism_y":
            part = _poly_mask(halfplanes(m["poly"]), X - m["cx"], Z - m["cz"])[:, None, :] \
                & ((Y >= m["y0"]) & (Y <= m["y1"]))[None, :, None]
        elif k == "frustum":
            dx, dy, dz = X[:, None, None] - m["o"][0], Y[None, :, None] - m["o"][1], Z[None, None, :] - m["o"][2]
            t = dx * m["d"][0] + dy * m["d"][1] + dz * m["d"][2]
            rx = dx - t * m["d"][0]
            ry = dy - t * m["d"][1]
            rz = dz - t * m["d"][2]
            rad = np.sqrt(rx * rx + ry * ry + rz * rz)
            rr = m["r0"] + (m["r1"] - m["r0"]) * np.clip(t / m["L"], 0.0, 1.0)
            part = (t >= 0.0) & (t <= m["L"]) & (rad <= rr)
        elif k == "sphere_band":
            dx, dy, dz = X[:, None, None] - m["c"][0], Y[None, :, None] - m["c"][1], Z[None, None, :] - m["c"][2]
            part = (dx * dx + dy * dy + dz * dz <= m["R"] ** 2) \
                & ((Z >= m["z0"]) & (Z <= m["z1"]))[None, None, :]
        else:
            raise ValueError(k)
        mask |= part
    for c in cuts:
        part = _poly_mask(halfplanes(c["poly"]), X, Y)[:, :, None]
        if c.get("neg_poly"):
            part = part & ~_poly_mask(halfplanes(c["neg_poly"]), X, Y)[:, :, None]
        part = part & ((Z >= c["z0"]) & (Z <= c["z1"]))[None, None, :]
        mask = mask & ~part
    return mask


def grid_measure(p, step):
    """体素积分：体积 + 重心。点采样（格心），步长 step（mm）。"""
    # 采样域 = 整件外廓（含探出底盘的杆端挡边），别只取底盘
    rx, ry, rz = p["bbox"][0] / 2.0, p["bbox"][1] / 2.0, p["bbox"][2]
    n = [int(math.ceil(2.0 * rx / step)), int(math.ceil(2.0 * ry / step)), int(math.ceil(rz / step))]
    ax = np.arange(n[0]) * step - rx
    ay = np.arange(n[1]) * step - ry
    az = np.arange(n[2]) * step
    for a in (ax, ay, az):                          # 格心
        a += step / 2.0
    members, cuts = p["members"], p["cuts"]
    mask = _inside(members, cuts, ax, ay, az)
    cnt = int(mask.sum())
    vol = cnt * step ** 3
    if cnt:
        w = mask.astype(np.float64)
        com = [float((w.sum(axis=(1, 2)) * ax).sum() / cnt),
               float((w.sum(axis=(0, 2)) * ay).sum() / cnt),
               float((w.sum(axis=(0, 1)) * az).sum() / cnt)]
    else:
        com = [0.0, 0.0, 0.0]
    return {"step_mm": step, "volume_mm3": vol, "com_mm": com, "cells": cnt}


# ------------------------------------------------------------ 载荷与稳定性
def _edge_distances(hull_pts):
    """对凸多边形每条边给出「指向内侧的单位法线 + 边上一点」，用于算重心投影到各边的有符号内距：
    正值 = 在支承多边形内侧（稳定），负值 = 越界。法线方向按「质心在内侧」自动定，所以
    多边形逆/顺时针都吃。"""
    cx = sum(q[0] for q in hull_pts) / len(hull_pts)
    cy = sum(q[1] for q in hull_pts) / len(hull_pts)
    out = []
    for (x0, y0), (x1, y1) in zip(hull_pts, hull_pts[1:] + hull_pts[:1]):
        ex, ey = x1 - x0, y1 - y0
        n = math.hypot(ex, ey)
        nx, ny = ey / n, -ex / n
        if nx * (cx - x0) + ny * (cy - y0) < 0.0:      # 质心落在外侧 -> 反号，取内法线
            nx, ny = -nx, -ny
        out.append((x0, y0, nx, ny))
    return out


def _margin(hull_pts, px, py):
    """返回 (最小内距 mm, 最近边的外法线方位角°, 最近边)。"""
    best = None
    for (x0, y0, nx, ny) in _edge_distances(hull_pts):
        d = nx * (px - x0) + ny * (py - y0)
        if best is None or d < best[0]:
            best = (d, math.degrees(math.atan2(-ny, -nx)) % 360.0, (x0, y0, nx, ny))
    return best


def _combine(base_mass, base_com, loads, ballast_g=0.0, ballast_com=(0.0, 0.0, 0.0)):
    """组合重心（只用 x/y 判倾倒；z 用于推力阈值）。loads = [(x, y, z, grams), ...]"""
    m = base_mass + sum(l[3] for l in loads) + ballast_g
    sx = base_mass * base_com[0] + sum(l[3] * l[0] for l in loads) + ballast_g * ballast_com[0]
    sy = base_mass * base_com[1] + sum(l[3] * l[1] for l in loads) + ballast_g * ballast_com[1]
    sz = base_mass * base_com[2] + sum(l[3] * l[2] for l in loads) + ballast_g * ballast_com[2]
    return m, (sx / m, sy / m, sz / m)


def load(p=None):
    if p is None:
        p = read_params(SCAD)
    p["head_cz"] = p["head_cut_z"] + math.sqrt(p["head_r"] ** 2 - p["head_cut_r"] ** 2)
    # 头顶切平：球极点处 OCC 三角化会留重复有向边（非水密），切掉一个半径 head_top_flat_r 的小平顶
    p["head_flat_z"] = p["head_cz"] + math.sqrt(p["head_r"] ** 2 - p["head_top_flat_r"] ** 2)
    p["head_top"] = p["head_flat_z"]                       # 整件 Z 外廓 = 头顶平顶
    p["hub_rx"] = p["base_rx"] - p["rim_w"] - p["groove_w"]
    p["hub_ry"] = p["base_ry"] - p["rim_w"] - p["groove_w"]
    p["groove_z"] = p["base_h"] - p["groove_d"]
    p["bar_half"] = p["bar_len"] / 2.0
    p["bar_span"] = p["bar_len"] + 2.0 * p["stop_len"]
    p["shoulder_w"] = 2.0 * p["torso_r_top"]
    p["head_sin"] = p["head_cut_r"] / p["head_r"]
    # 头球「外露起点」= 躯干顶面 (z=torso_z_top) 处的头球半径。免支撑判据看的是它：
    # 从这一圈往上才是看得见的球面；切面半径只是埋进躯干里的接口，不参与外露面的悬垂角。
    p["head_emerge_r"] = math.sqrt(max(0.0, p["head_r"] ** 2 - (p["torso_z_top"] - p["head_cz"]) ** 2))
    p["head_emerge_sin"] = p["head_emerge_r"] / p["head_r"]
    p["wet_g"] = p["wet_band_g"] * p["bands_max"]
    # 外廓：X 由底盘宽定；Y 取「底盘长」与「晾杆含挡边总跨」的较大者（杆端可以探出底盘）；
    # Z 由最高的外露面定 —— 头球顶与拳顶取大者。
    p["bbox"] = (2.0 * p["base_rx"], max(2.0 * p["base_ry"], p["bar_span"]),
                 round(max(p["head_top"], p["bar_z"] + p["hand_r"] * math.sqrt(3.0) / 2.0), 3))

    members, cuts = primitives(p)
    p["members"], p["cuts"] = members, cuts
    for m in members:
        m["volume"] = member_volume(m)
    p["V_solids"] = sum(m["volume"] for m in members)
    p["mass_solids_g"] = {mat: p["V_solids"] / 1000.0 * p[f"rho_{mat.lower()}"] for mat in ("PLA", "PETG")}

    # ---- 体素积分：体积 + 重心（两档步长 + Richardson 外推）----
    g10 = grid_measure(p, 1.0)
    g05 = grid_measure(p, 0.5)
    p["grid"] = {"step_1.0mm": g10, "step_0.5mm": g05,
                 "volume_extrapolated_mm3": 2.0 * g05["volume_mm3"] - g10["volume_mm3"]}
    p["V_grid"] = p["grid"]["volume_extrapolated_mm3"]
    p["com_grid"] = g05["com_mm"]
    p["V_outer_box"] = p["bbox"][0] * p["bbox"][1] * p["bbox"][2]
    p["volume_ratio"] = p["V_grid"] / p["V_outer_box"]
    p["mass_g"] = {mat: p["V_grid"] / 1000.0 * p[f"rho_{mat.lower()}"] for mat in ("PLA", "PETG")}

    # ---- 截面（晾杆/拳/挡边 = 六边形；手臂 = 圆）----
    p["sec"] = {"bar": poly_section(hex_poly(p["bar_r"])),
                "hand": poly_section(hex_poly(p["hand_r"])),
                "stop": poly_section(hex_poly(p["stop_r"])),
                "arm": poly_section(circle_poly(p["arm_r_root"], 64))}

    # ---- 支承多边形（底盘底面=整块圆角长条；参数版，check.py 另从网格反推一份对账）----
    hull = roundrect_poly(p["base_rx"], p["base_ry"], p["base_corner_r"])
    p["hull_pts"] = hull
    p["foot_area"] = poly_section(hull)["area"]

    # ---- 载荷位置：湿发带挂在杆上（自杆端向内密排）----
    y_tip = p["bar_half"] - p["band_span"] / 2.0
    packed = [[(-p["hand_x"], y_tip - i * p["band_span"], p["band_com_z"], p["wet_band_g"])
               for i in range(p["bands_max"])]]
    packed.append([(p["hand_x"], y_tip - i * p["band_span"], p["band_com_z"], p["wet_band_g"])
                   for i in range(p["bands_max"])])
    cases = {
        "空载": [],
        "单条（左杆最外）": [( -p["hand_x"], y_tip, p["band_com_z"], p["wet_band_g"])],
        "单侧挂满3条（左杆，自杆端向内密排）": packed[0],
        "单侧挂满3条（左杆，三条都按杆端质点=保守）":
            [(-p["hand_x"], y_tip, p["band_com_z"], p["wet_band_g"])] * p["bands_max"],
        "两杆各挂满3条（超载工况）": packed[0] + packed[1],
    }
    p["load_cases"] = cases
    p["y_tip"] = y_tip

    # ---- 结构受力：晾杆（手心夹持 = 双悬臂）与手臂（斜撑悬臂）----
    L_half = p["bar_half"]
    sb, sa = p["sec"]["bar"], p["sec"]["arm"]
    L_arm = math.hypot(p["hand_x"] - p["arm_root_x"], p["bar_z"] - p["arm_root_z"])
    theta = math.degrees(math.atan2(p["hand_x"] - p["arm_root_x"], p["bar_z"] - p["arm_root_z"]))
    strength = {"bar": {}, "arm": {"root_r": p["arm_r_root"], "len": L_arm, "tilt_deg": theta,
                                   "i": sa["i"], "c": sa["c_max"],
                                   "lever_x": p["hand_x"] - p["arm_root_x"]}, "bar_half": L_half}
    grams_list = {"单条湿发带": p["wet_band_g"], "一根杆挂满3条": p["wet_g"], "湿毛巾 300g（误用）": 300.0}
    for name, grams in grams_list.items():
        P = grams * G / 1000.0
        M = P * (L_half - p["band_span"] / 2.0)      # 挂在悬臂端（最外那条发带）
        out = {"grams": grams, "P_N": P, "M_Nmm": M, "sigma_bar_MPa": M / sb["w_bot"]}
        for mat, (e, s) in (("PLA", (E_PLA, SIGMA_PLA)), ("PETG", (E_PETG, SIGMA_PETG))):
            out[f"tip_deflect_{mat}_mm"] = P * L_half ** 3 / (3.0 * e * sb["i"])
            out[f"mid_deflect_{mat}_mm"] = P * (L_half / 2.0) ** 3 / (3.0 * e * sb["i"])
            out[f"sf_{mat}"] = s / out["sigma_bar_MPa"]
        strength["bar"][name] = out
    P_arm = p["wet_g"] * G / 1000.0                   # 一根杆挂满的总重压在一只手上
    M_arm = P_arm * (p["hand_x"] - p["arm_root_x"])   # 竖直力 × 水平力臂
    P_tr = P_arm * math.sin(math.radians(theta))      # 换成沿臂轴的横向分量
    strength["arm"].update({
        "grams": p["wet_g"], "P_N": P_arm, "M_Nmm": M_arm,
        "M_Nmm_cross_check": P_tr * L_arm,
        "sigma_MPa": M_arm * sa["c_max"] / sa["i"],
        "torsion_Nmm": sum(l[1] for l in packed[0] if l[3]) * (p["wet_band_g"] * G / 1000.0),
    })
    for mat, (e, s) in (("PLA", (E_PLA, SIGMA_PLA)), ("PETG", (E_PETG, SIGMA_PETG))):
        strength["arm"][f"tip_deflect_{mat}_mm"] = P_tr * L_arm ** 3 / (3.0 * e * sa["i"])
        strength["arm"][f"sf_{mat}"] = s / strength["arm"]["sigma_MPa"]
    p["strength"] = strength
    p["stability"] = stability(p)

    # ---- 配重槽能塞多少：环形槽面积 -> 平放 Ø25x1.85 硬币（1 元硬币 6.1g，按 72% 填充率估）----
    ring_a = (poly_section(roundrect_poly(p["base_rx"] - p["rim_w"], p["base_ry"] - p["rim_w"],
                                          p["base_corner_r"] - p["rim_w"]))["area"]
              - poly_section(roundrect_poly(p["hub_rx"], p["hub_ry"], 0.0))["area"])
    coin_a, coin_g, coin_t = math.pi * 12.5 ** 2, 6.1, 1.85
    per_layer = math.floor(ring_a * 0.72 / coin_a)
    layers = int(p["groove_d"] // coin_t)
    p["ballast"] = {"ring_area_mm2": round(ring_a, 1), "coin_od_mm": 25.0, "coin_thick_mm": coin_t,
                    "coin_g": coin_g, "coins_per_layer": per_layer, "layers": layers,
                    "coins_max": per_layer * layers, "mass_max_g": round(per_layer * layers * coin_g, 1),
                    "mass_default_g": p["ballast_g"]}
    return p


def stability(p):
    """稳定性：每个载荷工况 × 配重有无，算组合重心 / 支承多边形余量 / 翻转临界外伸 / 推力阈值。
    口径照 docs/stability-load-analysis.md：水平桌面 + 仅重力时，加载高度不进倾倒判据，
    只进水平推力阈值与后续动力学；这里多给一个「载荷越出支承边多远才到临界」的等效数字。"""
    ballast_c = (0.0, 0.0, p["groove_z"] + p["groove_d"] / 2.0)
    cases = {}
    for name, loads in p["load_cases"].items():
        for tag, bl in (("无配重", 0.0), (f"配重+{p['ballast_g']:.0f}g硬币", p["ballast_g"])):
            per = {}
            for mat in ("PLA", "PETG"):
                m0 = p["mass_g"][mat]
                _m_base, com_base = _combine(m0, p["com_grid"], [], bl, ballast_c)
                d_base, _az0, _e0 = _margin(p["hull_pts"], com_base[0], com_base[1])
                m_tot, com = _combine(m0, p["com_grid"], loads, bl, ballast_c)
                d, az, _edge = _margin(p["hull_pts"], com[0], com[1])
                w_tot, w_base = m_tot / 1000.0 * G, m0 / 1000.0 * G
                w_load = sum(l[3] for l in loads) / 1000.0 * G
                per[mat] = {
                    "mass_total_g": round(m_tot, 2),
                    "com_mm": [round(v, 2) for v in com],
                    "margin_mm": round(d, 2),
                    "nearest_edge_az_deg": round(az, 1),
                    "weight_N": round(w_tot, 4),
                    "margin_mm_unloaded": round(d_base, 2),
                    # 把载荷全部当竖直力线：要翻倒，载荷投影必须越出最近支承边这么远
                    "critical_overhang_mm": round(w_base * d_base / w_load, 1) if w_load else None,
                    # 水平推力阈值（绕最近支承边，推力作用在晾杆高度）
                    "push_to_tip_g": round(w_tot * d / p["bar_z"] / G * 1000.0, 1),
                    "slide_g": round(MU_WOOD * w_tot / G * 1000.0, 1),
                    "slide_g_conservative": round(MU_MIN * w_tot / G * 1000.0, 1),
                }
            cases[f"{name}（{tag}）"] = per
    return {"edge_mu": MU_WOOD, "edge_mu_conservative": MU_MIN, "cases": cases}


# ------------------------------------------------------------ 主入口（只打印，不落盘）
def main(argv):
    ap = argparse.ArgumentParser(add_help=True, description="idea-020 派生量")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    p = load()
    dump = {k: v for k, v in p.items() if k not in ("cuts", "hull_pts")}
    if a.out:
        Path(a.out).write_text(json.dumps(dump, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n")
    if a.json:
        print(json.dumps(dump, ensure_ascii=False, indent=2, sort_keys=True, default=str))
        return 0
    b = p["bbox"]
    print(f"外廓 {b[0]:.1f} x {b[1]:.1f} x {b[2]:.1f} mm；底盘 {2*p['base_rx']:.0f}x{2*p['base_ry']:.0f}"
          f" 厚 {p['base_h']:.0f}；肩宽 {p['shoulder_w']:.0f}（底盘宽 {2*p['base_rx']:.0f} ≥ 1.2×肩宽 "
          f"{1.2*p['shoulder_w']:.1f} ✅）")
    print(f"  头球 r={p['head_r']:.0f} 球心 z={p['head_cz']:.1f}，顶 {p['head_top']:.1f}；"
          f"躯干顶面处外露半径 {p['head_emerge_r']:.2f} → sin={p['head_emerge_sin']:.3f}"
          f" ≥ sin45=0.707 ✅（切面 r={p['head_cut_r']:.0f} 埋在躯干里）")
    print(f"  晾杆 y ∈ ±{p['bar_half']:.0f}，含挡边总跨 {p['bar_span']:.0f}"
          f"（底盘长 {2*p['base_ry']:.0f} → 杆端每侧探出 "
          f"{(p['bar_span'] - 2*p['base_ry'])/2:.1f}）；两杆间距 {2*p['hand_x']:.0f}"
          f"（发带占杆长 {p['band_span']:.0f}，一根杆密排 {p['bands_max']} 条需 "
          f"{p['bands_max']*p['band_span']:.0f}）")
    print(f"  体积：构件和 {p['V_solids']/1000:.2f} / 体素 1.0mm {p['grid']['step_1.0mm']['volume_mm3']/1000:.2f}"
          f" / 体素 0.5mm {p['grid']['step_0.5mm']['volume_mm3']/1000:.2f}"
          f" / 外推 {p['V_grid']/1000:.2f} cm³（外廓的 {p['volume_ratio']*100:.1f}%）")
    print(f"  质量（按体素外推体积）PLA {p['mass_g']['PLA']:.1f} g / PETG {p['mass_g']['PETG']:.1f} g；"
          f"重心 {[round(v,2) for v in p['com_grid']]} mm；贴床 {p['foot_area']:.0f} mm²")
    for tag in ("单侧挂满3条（左杆，自杆端向内密排）（无配重）",
                "单侧挂满3条（左杆，三条都按杆端质点=保守）（无配重）",
                "两杆各挂满3条（超载工况）（无配重）"):
        s = p["stability"]["cases"][tag]["PLA"]
        print(f"  [{tag.split('（')[0]}] 总重 {s['mass_total_g']:.0f}g，组合重心 "
              f"({s['com_mm'][0]:.1f}, {s['com_mm'][1]:.1f})，到最近支承边余量 {s['margin_mm']:.1f} mm"
              f"（{'在支承多边形内' if s['margin_mm'] > 0 else '越界'}）；"
              f"临界外伸 {s['critical_overhang_mm']:.0f} mm；推力阈值 {s['push_to_tip_g']:.0f} g")
    for name, cs in p["strength"]["bar"].items():
        print(f"  杆受力[{name}] σ={cs['sigma_bar_MPa']:.2f} MPa（SF PLA {cs['sf_PLA']:.0f}×），"
              f"端部挠度 {cs['tip_deflect_PLA_mm']:.3f} mm(PLA)")
    print(f"  臂受力：σ={p['strength']['arm']['sigma_MPa']:.2f} MPa（SF {p['strength']['arm']['sf_PLA']:.0f}×），"
          f"挠度 {p['strength']['arm']['tip_deflect_PLA_mm']:.4f} mm(PLA)，"
          f"臂与竖直 {p['strength']['arm']['tilt_deg']:.1f}°")
    if a.out:
        print(f"派生量 -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
