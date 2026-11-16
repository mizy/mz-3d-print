#!/usr/bin/env python3
"""idea-016 吉他拨片盒：解析 model.scad 参数 -> 派生量（check.py / 成本估算共用一份）。

model.scad 里 cavity_l/tray_w/... 是表达式（scad_params 只认字面量，所以读不到），
这里按**同一套式子**在 Python 侧重算一遍 —— check.py 拿它和 STL 实测对账，
对不上就说明「画出来的」和「算出来的」不是一份。

派生量：
  cavity_*/tray_*/lid_*  内腔、盒身、盖子的尺寸链
  V_tray / V_lid         解析体积（圆角矩形面积 - 圆角修正 = w*d-(4-π)r²）
  parts[]                两件的期望包围盒与体积（STL 按连通块拆开逐个对账）
  pack_*                 两件排开的整盘包围盒
  capacity               内腔最多能塞几片 / 按 pick_count 堆放还剩多少余量
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

CORNER_LOSS = 4.0 - math.pi      # 圆角相对直角少掉的面积系数


def rrect_area(w, d, r):
    """圆角矩形面积（精确）。"""
    return w * d - CORNER_LOSS * r * r


def load():
    p = read_params(SCAD)
    p["cavity_l"] = p["pick_l"] + 2 * p["edge_clear"]
    p["cavity_d"] = p["pick_w"] + 2 * p["edge_clear"]
    p["cavity_h"] = p["pick_count"] * p["pick_t"] + p["stack_clear"]
    p["tray_w"] = p["cavity_l"] + 2 * p["wall_t"]
    p["tray_d"] = p["cavity_d"] + 2 * p["wall_t"]
    p["tray_h"] = p["floor_t"] + p["cavity_h"]
    p["lid_iw"] = p["tray_w"] + 2 * p["lid_fit"]
    p["lid_id"] = p["tray_d"] + 2 * p["lid_fit"]
    p["lid_ir"] = p["corner_r"] + p["lid_fit"]
    p["lid_ow"] = p["lid_iw"] + 2 * p["skirt_t"]
    p["lid_od"] = p["lid_id"] + 2 * p["skirt_t"]
    p["lid_or"] = p["lid_ir"] + p["skirt_t"]
    p["lid_h"] = p["lid_t"] + p["skirt_h"]          # 打印姿态（裙边朝上）的总高
    p["assembled_h"] = p["tray_h"] + p["lid_t"]
    p["pack_x"] = p["tray_w"] + p["pack_gap"] + p["lid_ow"]
    p["pack_y"] = max(p["tray_d"], p["lid_od"])
    p["pack_z"] = max(p["tray_h"], p["lid_h"])

    tray_outer = rrect_area(p["tray_w"], p["tray_d"], p["corner_r"])
    cav = rrect_area(p["cavity_l"], p["cavity_d"], p["cavity_r"])
    lid_outer = rrect_area(p["lid_ow"], p["lid_od"], p["lid_or"])
    lid_inner = rrect_area(p["lid_iw"], p["lid_id"], p["lid_ir"])
    p["V_tray"] = tray_outer * p["tray_h"] - cav * p["cavity_h"]
    p["V_lid"] = lid_outer * p["lid_t"] + (lid_outer - lid_inner) * p["skirt_h"]
    p["V_analytic"] = p["V_tray"] + p["V_lid"]

    p["parts"] = [
        {"name": "盒身", "x0": 0.0, "size": (p["tray_w"], p["tray_d"], p["tray_h"]), "volume": p["V_tray"]},
        {"name": "上盖", "x0": p["tray_w"] + p["pack_gap"],
         "size": (p["lid_ow"], p["lid_od"], p["lid_h"]), "volume": p["V_lid"]},
    ]
    p["capacity"] = int(p["cavity_h"] // p["pick_t"])                 # 内腔最多塞几片
    p["headroom"] = p["cavity_h"] - p["pick_count"] * p["pick_t"]     # 10 片堆完还剩多少
    p["skirt_wall"] = (p["lid_ow"] - p["lid_iw"]) / 2.0               # 裙边实际壁厚（应 = skirt_t）
    p["min_feature"] = min(p["floor_t"], p["wall_t"], p["lid_t"], p["skirt_t"], p["corner_r"])
    p["stack_gap_total"] = p["cavity_l"] - p["pick_l"]
    return p


def main(argv):
    ap = argparse.ArgumentParser(add_help=True, description="idea-016 派生量")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    p = load()
    if a.out:
        Path(a.out).write_text(json.dumps(p, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n")
    if a.json:
        print(json.dumps(p, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"盒身 {p['tray_w']:.1f} x {p['tray_d']:.1f} x {p['tray_h']:.1f} mm，"
              f"内腔 {p['cavity_l']:.1f} x {p['cavity_d']:.1f} x {p['cavity_h']:.1f} mm")
        print(f"  装 {p['pick_count']} 片（最多塞 {p['capacity']} 片，堆完余 {p['headroom']:.1f}mm）"
              f"  单边间隙 {p['edge_clear']:.2f}mm")
        print(f"上盖 {p['lid_ow']:.1f} x {p['lid_od']:.1f} x {p['lid_h']:.1f} mm"
              f"（盖板 {p['lid_t']:.1f} + 裙边 {p['skirt_h']:.1f}，壁厚 {p['skirt_wall']:.2f}）")
        print(f"  组装总高 {p['assembled_h']:.1f}mm，插拔间隙 {p['lid_fit']:.2f}mm/边")
        print(f"整盘（两件排开）{p['pack_x']:.1f} x {p['pack_y']:.1f} x {p['pack_z']:.1f} mm")
        print(f"  解析体积 盒身 {p['V_tray']/1000:.2f} + 盖 {p['V_lid']/1000:.2f}"
              f" = {p['V_analytic']/1000:.2f}cm³（≈{p['V_analytic']/1000*1.24:.2f}g PLA）")
        if a.out:
            print(f"派生量 -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
