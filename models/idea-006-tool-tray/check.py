#!/usr/bin/env python3
"""工具收纳盘自检：把「能打印」这件事逐条算出来，全过才有意义开打。

只读 model.scad / model.py / 台账 print-ideas.json（打印机体量）与同目录 STL（若已编译），
不改任何文件。用法: python3 check.py   （退出码 0 = 全过）

检查分三层：
  A 参数自洽   ：总高 = 底盘 + 最深槽；槽尺寸 = 工具尺寸 + 2×间隙
  B 可打印性   ：底盘厚度、槽深不超过工具厚（留 2mm 露出好拿）、槽间壁厚、
                 槽到外缘、外廓 ≤ 打印机成型尺寸
  C 实物对账   ：STL 已编译就核对包围盒 = 参数、水密性（调 check_model.py）
"""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import model  # noqa: E402 —— 派生量与 model.py 共用一份

SCRIPTS = Path.home() / ".cah-data/skills/shared/3d-print-ideas/scripts"
LEDGER = Path.home() / ".cah-data/skills/shared/3d-print-ideas/runtime/print-ideas.json"
MIN_WALL = 2.4      # 相邻槽之间最小实心壁厚（0.4 喷嘴 6 条线）
MIN_FLOOR = 1.6     # 槽底最小剩料（0.2 层高 8 层）
GRAB_OUT = 2.0      # 槽深最多比工具厚浅这么多，保证能捏住取出来
MATERIAL_BUDGET = 0.35  # 材料体积不得超过外廓长方体体积的 35%（浅盘不是实心砖）

fails, total = [], 0


def check(ok, label, detail):
    global total
    total += 1
    print(("  ok  " if ok else " FAIL ") + label + "  " + detail)
    if not ok:
        fails.append(label)


def boxes(p):
    """(名字, 形状, 几何) —— 方槽几何是 (x0,y0,x1,y1)，圆槽是 (cx,cy,直径)。"""
    out = []
    for r in p["rect_pockets"]:
        out.append((r["name"], "rect", model.box(r)))
    for r in p["bore_pockets"]:
        out.append((r["name"], "bore", (r["cx"], r["cy"], r["pocket_d"])))
    return out


def gap(a, b):
    """两个槽之间的净壁厚：分离轴（方-方）或点到矩形/圆的精确距离。"""
    (an, ak, ag), (bn, bk, bg) = a, b
    if ak == "rect" and bk == "rect":
        ax0, ay0, ax1, ay1 = ag
        bx0, by0, bx1, by1 = bg
        return max(max(bx0 - ax1, ax0 - bx1), max(by0 - ay1, ay0 - by1))
    if ak == "bore" and bk == "bore":
        return math.hypot(ag[0] - bg[0], ag[1] - bg[1]) - (ag[2] + bg[2]) / 2
    rect, circle = (ag, bg) if ak == "rect" else (bg, ag)   # 一圆一方：取圆的圆心半径 + 方的四边
    cx, cy, dia = circle
    x0, y0, x1, y1 = rect
    dx = max(x0 - cx, 0.0, cx - x1)
    dy = max(y0 - cy, 0.0, cy - y1)
    return math.hypot(dx, dy) - dia / 2


def build_volume():
    """从台账里抠打印机成型尺寸；抠不到返回 None（跳过，不猜）。"""
    if not LEDGER.exists():
        return None
    raw = json.loads(LEDGER.read_text()).get("printer", {}).get("buildVolume") or ""
    nums = [float(v) for v in re.findall(r"\d+(?:\.\d+)?", raw)]
    return nums[:3] if len(nums) >= 3 else None


def main():
    p = model.load()
    print(f"# {HERE.name}  外廓 {p['tray_w']:.0f}x{p['tray_d']:.0f}x{p['tray_h']:.0f}mm，"
          f"{p['pocket_count']} 个槽\n")

    print("A 参数自洽")
    check(math.isclose(p["tray_h"], p["floor_t"] + p["max_depth"], abs_tol=1e-9),
          "总高 = 底盘 + 最深槽",
          f"{p['tray_h']:.0f} = {p['floor_t']:.0f} + {p['max_depth']:.0f}")
    for r in p["rect_pockets"]:
        check(math.isclose(r["pocket_l"], r["tool_l"] + 2 * p["gap"], abs_tol=1e-9)
              and math.isclose(r["pocket_w"], r["tool_w"] + 2 * p["gap"], abs_tol=1e-9),
              f"槽尺寸 = 工具 + 2×间隙（{r['name']}）",
              f"{r['pocket_l']:.0f}x{r['pocket_w']:.0f} = {r['tool_l']:.0f}x{r['tool_w']:.0f} + {2*p['gap']:.1f}")
    for r in p["bore_pockets"]:
        check(math.isclose(r["pocket_d"], r["tool_d"] + 2 * p["gap"], abs_tol=1e-9),
              f"圆槽直径 = 工具直径 + 2×间隙（{r['name']}）",
              f"φ{r['pocket_d']:.0f} = φ{r['tool_d']:.0f} + {2*p['gap']:.1f}")

    print("\nB 可打印性")
    check(p["floor_t"] >= MIN_FLOOR, "槽底剩料够厚",
          f"{p['floor_t']:.1f}mm ≥ {MIN_FLOOR}mm（{p['floor_t']/0.2:.0f} 层 @0.2）")
    check(p["max_depth"] <= p["tray_h"] - p["floor_t"] + 1e-9, "最深槽不切穿底盘",
          f"最深 {p['max_depth']:.0f} ≤ {p['tray_h']-p['floor_t']:.0f}mm")
    for r in p["rect_pockets"] + p["bore_pockets"]:
        check(r["depth"] <= r["tool_t"] - GRAB_OUT + 1e-9, f"槽不埋没工具（{r['name']}）",
              f"深 {r['depth']:.0f} ≤ 工具厚 {r['tool_t']:.0f} - {GRAB_OUT:.0f}mm")
    items = boxes(p)
    worst, worst_pair = 1e9, ""
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            g = gap(items[i], items[j])
            if g < worst:
                worst, worst_pair = g, f"{items[i][0]}|{items[j][0]}"
    check(worst >= MIN_WALL, "相邻槽壁厚达标", f"最薄 {worst:.2f}mm（{worst_pair}）≥ {MIN_WALL}mm")
    edge = 1e9
    for name, kind, g in items:
        if kind == "rect":
            x0, y0, x1, y1 = g
            e = min(x0, y0, p["tray_w"] - x1, p["tray_d"] - y1)
        else:
            cx, cy, d = g
            e = min(cx - d / 2, cy - d / 2, p["tray_w"] - cx - d / 2, p["tray_d"] - cy - d / 2)
        if e < edge:
            edge, edge_name = e, name
    check(edge >= p["wall_margin"] - 1e-9, "槽到外缘留够实心",
          f"最近 {edge:.2f}mm（{edge_name}）≥ {p['wall_margin']:.0f}mm")
    bv = build_volume()
    if bv:
        check(p["tray_w"] <= bv[0] and p["tray_d"] <= bv[1] and p["tray_h"] <= bv[2],
              "外廓在打印机成型尺寸内", f"{p['tray_w']:.0f}x{p['tray_d']:.0f}x{p['tray_h']:.0f} ≤ {bv}")
    else:
        print("  skip  外廓 ≤ 成型尺寸  台账里没读到 buildVolume，跳过")

    print("\nC 实物对账")
    stls = sorted(HERE.glob("*.stl"))
    if not stls:
        print("  skip  STL 复核  还没编译，先跑 scripts/scad_build.py")
    for stl in stls:
        proc = subprocess.run([sys.executable, str(SCRIPTS / "check_model.py"), str(stl), "--json"],
                              capture_output=True, text=True)
        try:
            rep = json.loads(proc.stdout)
        except json.JSONDecodeError:
            check(False, f"STL 复核（{stl.name}）", "check_model.py 没吐出 JSON")
            continue
        size = rep.get("size_mm", [0, 0, 0])
        check(not rep.get("failures"), f"STL 水密/法线（{stl.name}）",
              "、".join(rep.get("failures") or ["全过"]))
        check(all(abs(a - b) < 1e-3 for a, b in
                  zip(size, [p["tray_w"], p["tray_d"], p["tray_h"]])),
              f"STL 包围盒 = 参数（{stl.name}）",
              f"{[round(v,1) for v in size]} vs {p['tray_w'], p['tray_d'], p['tray_h']}")
        # 材料预算：浅盘不是砖头——实心块挖洞的做法料量会飙到外廓体积的 90%+
        block = p["tray_w"] * p["tray_d"] * p["tray_h"]
        vol = rep.get("volume_mm3", 0.0)
        check(vol <= MATERIAL_BUDGET * block, "材料预算（不是实心砖）",
              f"料 {vol/1000:.1f}cm³ 占外廓 {vol/block:.1%} ≤ {MATERIAL_BUDGET:.0%}"
              f"（≈{vol/1000*1.24:.0f}g PLA）")

    print(f"\n共 {total} 项，" + ("全过 ✅" if not fails else f"FAIL {len(fails)} 项 ❌: " + "; ".join(fails)))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
