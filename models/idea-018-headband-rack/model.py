#!/usr/bin/env python3
"""idea-018 桌面发带晾晒架「龙门晾架」：读 model.scad -> 派生量 + 解析体积 + 受力/翻倒数字。

一份数字只写在一处：`model.scad`。这里只算「由参数推出来的东西」，`build_mesh.py`（建实体）
与 `check.py`（自检）都 import 这一份 —— 三者不可能各算各的。

整件由 **等截面棱柱** 组成（底座环 4 根 + 立柱 6 根 + 晾杆 3 根 + 侧梁 2 根），所以：
  * 每根构件的体积、形心是精确的（长度 × 截面）；
  * 并集体积可以把 z 切片、每片算「轴对齐矩形并集面积」（精确扫描线），再沿 z 积分 ——
    每个 z 带内并集面积是 z 的线性函数，所以按「带边界」积分是**精确值**，
    另有均匀细步长采样做收敛对照（两者必须一致，见 check.py）。

派生量：
  x_center/outer_x/outer_y        尺寸链
  bar_ys / bar_center_z / bar_bot_z  三根晾杆的位置
  sec_*                           楔形截面：面积 / 形心 / 惯性矩 / 抗弯模量
  members                         构件清单（build_mesh.py 直接照着建）
  V_analytic / V_samples / V_solids  并集体积 / 采样收敛值 / 各构件体积之和（差值 = 接头重叠）
  com_*                           重心（按构件求和，接头重叠带来的偏差 < 1mm 量级）
  load                            湿发带受力：弯矩 / 应力 / 挠度 / 安全系数（PLA 与 PETG）
  tipping                         翻倒：绕前底沿 / 绕侧底沿 的水平推力阈值
  foot_area / bridge              贴床面积、唯一的桥接量
"""
import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCAD = HERE / "model.scad"
sys.path.insert(0, str(Path.home() / ".cah-data/skills/shared/3d-print-ideas/scripts"))
from scad_params import read_params  # noqa: E402

G = 9.80665                 # m/s²
E_PLA, E_PETG = 3500.0, 2000.0      # MPa（弯曲模量常见值）
SIGMA_PLA, SIGMA_PETG = 50.0, 47.0  # MPa（抗拉强度下限，保守）
MU = 0.40                   # 打印件 / 木桌面的静摩擦系数（放桌上是干摩擦）
MIN_FEATURE = 1.6           # 0.4 喷嘴 4 圈（skill 口径）
MAX_BUDGET = 0.35           # 材料 ≤ 外廓体积 35%（skill 口径）
MAX_OVERHANG_DEG = 45.0     # 免支撑上限（面与竖直方向夹角）
BRIDGE_STRIP_MAX_W = 2.0    # 「细棱桥」允许的朝下平面最大宽度
BRIDGE_WIDE_MAX_W = 15.0    # 更宽的朝下平面只允许这么宽的跨距


# ---------------------------------------------------------------- 截面与并集
def wedge_section(top_w, bot_w, h):
    """楔形截面（上宽 top_w、下缘 bot_w、高 h）：面积 / 形心 / 惯性矩 / 抗弯模量（精确）。"""
    a = (top_w + bot_w) / 2.0 * h
    vc = h * (bot_w + 2 * top_w) / (3.0 * (bot_w + top_w))          # 形心离下缘
    i = h ** 3 * (bot_w ** 2 + 4 * bot_w * top_w + top_w ** 2) / (36.0 * (bot_w + top_w))
    c_max = max(vc, h - vc)
    slope = math.degrees(math.atan(abs(top_w - bot_w) / 2.0 / h))    # 侧面与竖直方向夹角
    return {"area": a, "vc": vc, "i": i, "c_max": c_max, "w": i / c_max,
            "side_deg": slope, "top_w": top_w, "bot_w": bot_w, "h": h,
            "pts": [(-bot_w / 2.0, -h / 2.0), (bot_w / 2.0, -h / 2.0),
                    (top_w / 2.0, h / 2.0), (-top_w / 2.0, h / 2.0)]}


def union_area(rects):
    """轴对齐矩形并集面积（精确扫描线）。rects = [(x0, x1, y0, y1), ...]"""
    if not rects:
        return 0.0
    xs = sorted({r[0] for r in rects} | {r[1] for r in rects})
    total = 0.0
    for xa, xb in zip(xs, xs[1:]):
        if xb - xa <= 1e-12:
            continue
        iv = sorted((r[2], r[3]) for r in rects if r[0] <= xa + 1e-9 and r[1] >= xb - 1e-9)
        if not iv:
            continue
        length, lo0, hi0 = 0.0, iv[0][0], iv[0][1]
        for lo, hi in iv[1:]:
            if lo > hi0:
                length += hi0 - lo0
                lo0, hi0 = lo, hi
            else:
                hi0 = max(hi0, hi)
        length += hi0 - lo0
        total += (xb - xa) * length
    return total


# ---------------------------------------------------------------- 参数 -> 派生量
HOOK_EMBED = 1.0   # 配件各板之间的嵌入量（mm）：把原本的共面接缝变成体积重叠，藏在钩体肚子里看不见
                   # （build_mesh.py 用同一个常量建实体；解析体积也用同一套坐标算，两边不会跑偏）


def hook_boxes(p):
    """配件（挂杆小钩）的体块清单：全是轴对齐长方体，坐标取「使用姿态」（晾杆顶面 z=0、杆轴心线 y=0）。
    打印姿态是整件翻 180°（钩体板贴床、两翼与钩朝上）—— 体积不变，所以解析体积仍按这一套算。"""
    inner = p["bar_top_w"] + 2.0 * p["hook_fit"]
    body_y = inner + 2.0 * p["hook_flange"]
    t, fh, ft, pw, pt, ph = (p["hook_body_t"], p["hook_flange_h"], p["hook_flange"],
                             p["hook_prong_w"], p["hook_prong_t"], p["hook_prong_h"])
    boxes = [(-p["hook_x"] / 2.0, p["hook_x"] / 2.0, -body_y / 2.0, body_y / 2.0, -t, 0.0)]
    for sy in (-1, 1):                                   # 两片限位翼：上端埋进钩体 HOOK_EMBED
        y0, y1 = ((inner / 2.0, inner / 2.0 + ft) if sy > 0 else (-inner / 2.0 - ft, -inner / 2.0))
        boxes.append((-p["hook_x"] / 2.0, p["hook_x"] / 2.0, y0, y1,
                      -t - fh, -t + HOOK_EMBED))
    boxes.append((-pw / 2.0, pw / 2.0, body_y / 2.0 - pt, body_y / 2.0,   # 小尖钩：正对限位翼正下方
                  -t - ph, -t + HOOK_EMBED))
    return boxes


def hook_volume(p):
    """配件体积：沿 z 分带，每带取「轴对齐矩形并集面积」（精确），与主件同一套算法。"""
    boxes = hook_boxes(p)
    zs = sorted({b[4] for b in boxes} | {b[5] for b in boxes})
    total = 0.0
    for a, b in zip(zs, zs[1:]):
        zc = (a + b) / 2.0
        total += union_area([(x0, x1, y0, y1) for x0, x1, y0, y1, z0, z1 in boxes
                             if z0 <= zc <= z1]) * (b - a)
    return total


def load():
    p = read_params(SCAD)
    p["x_center"] = p["clear_x"] / 2.0 + p["frame_t"] / 2.0   # 立柱中心 |x|（内壁在 clear_x/2）
    p["outer_x"] = p["clear_x"] + 2.0 * p["frame_t"]
    p["outer_y"] = 2.0 * p["bar_y_spacing"] + p["base_w"]
    p["bar_ys"] = [-p["bar_y_spacing"], 0.0, p["bar_y_spacing"]]
    p["bar_center_z"] = p["post_top"] - p["bar_h"] / 2.0
    p["bar_bot_z"] = p["post_top"] - p["bar_h"]
    p["wet_g"] = p["wet_band_g"] * p["wet_bands"]
    p["sec"] = wedge_section(p["bar_top_w"], p["bar_bot_w"], p["bar_h"])

    # ---- 构件清单（等截面棱柱；axis = 长度方向）----
    # kind: 'box' 矩形截面 / 'wedge' 楔形截面；a,b = 截面两个水平尺寸（box）
    members = []
    for sx in (-1, 1):
        members.append({"name": f"底环纵杆{'+' if sx > 0 else '-'}", "axis": "y", "kind": "box",
                        "a": p["frame_t"], "b": p["base_h"], "len": p["outer_y"],
                        "pos": (sx * p["x_center"], 0.0, p["base_h"] / 2.0)})
    for sy in (-1, 1):
        members.append({"name": f"底环横杆{'+' if sy > 0 else '-'}", "axis": "x", "kind": "box",
                        "a": p["base_w"], "b": p["base_h"], "len": p["outer_x"],
                        "pos": (0.0, sy * p["bar_y_spacing"], p["base_h"] / 2.0)})
    for sx in (-1, 1):
        for by in p["bar_ys"]:
            members.append({"name": f"立柱{sx:+.0f}/{by:+g}", "axis": "z", "kind": "box",
                            "a": p["frame_t"], "b": p["post_w"], "len": p["post_top"],
                            "pos": (sx * p["x_center"], by, p["post_top"] / 2.0)})
    for by in p["bar_ys"]:
        members.append({"name": f"晾杆y{by:+g}", "axis": "x", "kind": "wedge",
                        "len": p["outer_x"], "pos": (0.0, by, p["bar_center_z"])})
    for sx in (-1, 1):
        members.append({"name": f"侧梁{'+' if sx > 0 else '-'}", "axis": "y", "kind": "wedge",
                        "len": 2.0 * p["bar_y_spacing"], "pos": (sx * p["x_center"], 0.0, p["bar_center_z"])})
    for m in members:
        m["area"] = p["sec"]["area"] if m["kind"] == "wedge" else m["a"] * m["b"]
        m["vol"] = m["area"] * m["len"]
        com = list(m["pos"])
        if m["kind"] == "wedge":
            com[2] = p["bar_bot_z"] + p["sec"]["vc"]        # 形心偏上（上宽下窄）
        m["com"] = tuple(com)
    p["members"] = members
    p["V_solids"] = sum(m["vol"] for m in members)
    p["mass_solids_g"] = {mat: p["V_solids"] / 1000.0 * p[f"rho_{mat.lower()}"]
                          for mat in ("PLA", "PETG")}

    # ---- z 切片 -> 并集面积 -> 体积 ----
    def slices(z):
        rects = []
        if -1e-9 <= z <= p["base_h"] + 1e-9:
            for sx in (-1, 1):
                rects.append((sx * p["x_center"] - p["frame_t"] / 2.0, sx * p["x_center"] + p["frame_t"] / 2.0,
                              -p["outer_y"] / 2.0, p["outer_y"] / 2.0))
            for sy in (-1, 1):
                rects.append((-p["outer_x"] / 2.0, p["outer_x"] / 2.0,
                              sy * p["bar_y_spacing"] - p["base_w"] / 2.0,
                              sy * p["bar_y_spacing"] + p["base_w"] / 2.0))
        if z <= p["post_top"] + 1e-9:
            for sx in (-1, 1):
                for by in p["bar_ys"]:
                    rects.append((sx * p["x_center"] - p["frame_t"] / 2.0, sx * p["x_center"] + p["frame_t"] / 2.0,
                                  by - p["post_w"] / 2.0, by + p["post_w"] / 2.0))
        if p["bar_bot_z"] - 1e-9 <= z <= p["post_top"] + 1e-9:
            w = p["bar_bot_w"] + (p["bar_top_w"] - p["bar_bot_w"]) * (z - p["bar_bot_z"]) / p["bar_h"]
            for by in p["bar_ys"]:
                rects.append((-p["outer_x"] / 2.0, p["outer_x"] / 2.0, by - w / 2.0, by + w / 2.0))
            for sx in (-1, 1):
                rects.append((sx * p["x_center"] - w / 2.0, sx * p["x_center"] + w / 2.0,
                              -p["bar_y_spacing"], p["bar_y_spacing"]))
        return rects

    p["slice_rects"] = slices
    # 注意：并集面积在 z = 带边界上是**跳变**的（底环在 z=base_h 处结束），
    # 所以积分一律取每个子区间的**中点**求值 —— 带内面积是 z 的线性函数，
    # 中点法在每个带内精确；节点集合里带着带边界，就没有子区间会跨带。
    bands = sorted({0.0, p["base_h"], p["bar_bot_z"], p["post_top"]})

    def integrate(zs):
        return sum(union_area(slices((a + b) / 2.0)) * (b - a) for a, b in zip(zs, zs[1:]))

    p["V_bands"] = integrate(bands)

    def sampled(step):
        n = max(2, int(math.ceil(p["post_top"] / step)))
        zs = sorted(set(i * p["post_top"] / n for i in range(n + 1)) | set(bands))
        return integrate(zs)

    p["V_samples"] = {"step_0.5mm": sampled(0.5), "step_0.05mm": sampled(0.05)}
    p["V_analytic"] = p["V_bands"]
    p["overlap_mm3"] = p["V_solids"] - p["V_analytic"]
    p["V_outer_box"] = p["outer_x"] * p["outer_y"] * p["post_top"]
    p["volume_ratio"] = p["V_analytic"] / p["V_outer_box"]
    p["mass_g"] = {mat: p["V_analytic"] / 1000.0 * p[f"rho_{mat.lower()}"] for mat in ("PLA", "PETG")}

    # ---- 重心（按构件求和；接头重叠让它偏 < 1mm 量级）----
    p["com_y"] = sum(m["vol"] * m["com"][1] for m in members) / p["V_solids"]
    p["com_z"] = sum(m["vol"] * m["com"][2] for m in members) / p["V_solids"]

    # ---- 贴床面积 = z=0+ 的截面并集；支座多边形 = 底环外廓 ----
    p["foot_area"] = union_area(slices(1e-6))
    p["foot_area_rel"] = p["foot_area"] / (p["outer_x"] * p["outer_y"])

    # ---- 唯一的桥接量：晾杆 / 侧梁的下缘细棱 ----
    p["bridge"] = {
        "strip_w": p["bar_bot_w"],
        "bar_span": p["clear_x"],
        "beam_span": 2.0 * p["bar_y_spacing"] - p["post_w"],
        "count": len(p["bar_ys"]) + 2,
        "note": "朝下平面只有这几条 %smm 细棱；更该防的是断面陡悬垂——楔形侧面 %.1f°（< 45 免支撑）"
                % (p["bar_bot_w"], p["sec"]["side_deg"]),
    }

    # ---- 受力：湿发带挂单杆跨中（最不利）----
    L = p["clear_x"]
    sec = p["sec"]
    cases = {
        "单条湿发带": p["wet_band_g"],
        f"{p['wet_bands']}条同挂一根杆": p["wet_g"],
        "湿毛巾 300g（误用）": 300.0,
    }
    load_out = {"span_mm": L, "cases": {}}
    for name, grams in cases.items():
        P = grams * G / 1000.0                       # N
        M = P * L / 4.0                              # N·mm
        sig = M / sec["w"]                           # MPa
        out = {"grams": grams, "P_N": P, "M_Nmm": M, "sigma_MPa": sig}
        for mat, (e, s) in (("PLA", (E_PLA, SIGMA_PLA)), ("PETG", (E_PETG, SIGMA_PETG))):
            out[f"deflect_{mat}_mm"] = P * L ** 3 / (48.0 * e * sec["i"])
            out[f"sf_{mat}"] = s / sig
        load_out["cases"][name] = out
    load_out["section"] = {k: round(v, 4) if isinstance(v, float) else v
                           for k, v in sec.items() if k != "pts"}
    p["load"] = load_out

    # ---- 翻倒：绕前底沿 / 绕侧底沿 的水平推力阈值 ----
    tip = {"edge_y_mm": p["outer_y"] / 2.0, "edge_x_mm": p["outer_x"] / 2.0, "cases": {}}
    load_lever = sum(grams * G / 1000.0 * min(p["outer_y"] / 2.0, p["outer_y"] / 2.0 - abs(by))
                     for grams, by in ((p["wet_band_g"], by) for by in p["bar_ys"]))
    for mat in ("PLA", "PETG"):
        W_self = p["mass_g"][mat] / 1000.0 * G
        Fy = (W_self * p["outer_y"] / 2.0 + load_lever) / p["post_top"]
        Fx = (W_self * p["outer_x"] / 2.0) / p["post_top"]
        tip["cases"][mat] = {
            "weight_N": W_self, "mass_g": p["mass_g"][mat],
            "push_to_tip_front_g": Fy / G * 1000.0,
            "push_to_tip_side_g": Fx / G * 1000.0,
            "slide_force_g": MU * (W_self + p["wet_g"] / 1000.0 * G) / G * 1000.0,
            "load_lever_mm": load_lever / (p["wet_g"] / 1000.0 * G) if p["wet_g"] else 0.0,
        }
    p["tipping"] = tip
    return p


def main(argv):
    ap = argparse.ArgumentParser(add_help=True, description="idea-018 派生量")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    p = load()
    if a.out:
        Path(a.out).write_text(json.dumps({k: v for k, v in p.items() if k != "slice_rects"},
                                          ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n")
    if a.json:
        print(json.dumps({k: v for k, v in p.items() if k != "slice_rects"},
                         ensure_ascii=False, indent=2, sort_keys=True, default=str))
        return 0
    s, sec = p["sec"], p["sec"]
    print(f"外廓 {p['outer_x']:.1f} x {p['outer_y']:.1f} x {p['post_top']:.1f} mm"
          f"（净宽 {p['clear_x']:.0f}，净高 {p['bar_bot_z']:.1f}，3 根晾杆 y={p['bar_ys']}）")
    print(f"  构件 {len(p['members'])} 根；并集体积 {p['V_analytic']/1000:.2f} cm³"
          f"（外廓 {p['V_outer_box']/1000:.0f} cm³ 的 {p['volume_ratio']*100:.1f}%），"
          f"接头重叠 {p['overlap_mm3']/1000:.2f} cm³")
    print(f"  采样收敛：step0.5mm {p['V_samples']['step_0.5mm']/1000:.3f} / "
          f"step0.05mm {p['V_samples']['step_0.05mm']/1000:.3f} cm³"
          f"（带积分 {p['V_bands']/1000:.3f} cm³）")
    print(f"  质量 PLA {p['mass_g']['PLA']:.1f} g / PETG {p['mass_g']['PETG']:.1f} g；"
          f"重心 y={p['com_y']:.2f} z={p['com_z']:.1f} mm；贴床 {p['foot_area']:.0f} mm²"
          f"（支座在地面的 {p['foot_area_rel']*100:.1f}%）")
    print(f"  晾杆截面：A={sec['area']:.1f} mm² I={sec['i']:.1f} mm⁴ W={sec['w']:.1f} mm³，"
          f"侧面与竖直 {sec['side_deg']:.1f}°（免支撑上限 {MAX_OVERHANG_DEG:.0f}°）")
    for name, c in p["load"]["cases"].items():
        print(f"  受力[{name}] {c['grams']:.0f}g 跨 {p['load']['span_mm']:.0f}mm："
              f"σ={c['sigma_MPa']:.2f} MPa（安全系数 PLA {c['sf_PLA']:.0f}× / PETG {c['sf_PETG']:.0f}×），"
              f"挠度 {c['deflect_PLA_mm']:.3f} mm(PLA) / {c['deflect_PETG_mm']:.3f} mm(PETG)")
    t = p["tipping"]["cases"]["PETG"]
    print(f"  翻倒（PETG {t['mass_g']:.0f}g）：顶部水平推力 {t['push_to_tip_front_g']:.0f} g 前后翻 / "
          f"{t['push_to_tip_side_g']:.0f} g 左右翻；滑动 {t['slide_force_g']:.0f} g")
    if a.out:
        print(f"派生量 -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
