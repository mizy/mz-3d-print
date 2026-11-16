#!/usr/bin/env python3
"""idea-017 镂空分隔收纳篮（苗壮制造）：读 model.scad -> 派生量 + 孔位布局。

一份数字只写在一处：`model.scad`。这里只算「由参数推出来的东西」（尺寸链、孔位、
解析体积），`build_mesh.py`（建实体）与 `check.py`（自检）都 import 这一份 ——
三者不可能各算各的。

两个字符串参数 scad_params.py 读不到（它只认 `name = 数字;`），所以放这里：
  BRAND_TEXT / BRAND_FONT

孔位规则（写死，别绕）：
  - 每面墙能排几个孔 = fit_count(可用段长, 孔长, 孔间料) → 排到「孔端到端头还剩
    ≥ MIN_LIGAMENT 的料」为止，不够就减一个孔（宁可少开一个，不留一点皮）。
  - 可用段长 = 平段长 - 2*band_side；平段长 = 外廓 - 2*corner_r（圆角那一段不能开孔）。
  - 排高：从 sill_h 到 outer_h - ledge_h 之间等分（rows 排孔 + rows+1 条料带）。
  - 底板孔：每个格子内按 bottom_edge 退让后排孔，孔心对称于格心。

派生量：
  inner_*/outer_*/cavity_h/cavity_r   尺寸链
  flat_*/usable_*                     可开孔段
  row_zs / div_row_zs                 墙面孔与隔板孔的排高
  n_back / n_side / n_div_x / n_div_y 每面（每排）孔数
  n_bx / n_by                         每个格子里底板孔的行列数
  louvers[] / bottom_holes[]          孔位清单（build_mesh.py 直接用）
  V_base / V_dividers / V_holes / V_no_text / volume_ratio   解析体积
  bridge_flat / min_ligament_*        可打印性判据（check.py 直接用）
  brand_area_bbox                     品牌字在墙面上的可用幅面（143 字宽是实测值，见 check）
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

# 字符串参数（scad_params 读不到，只能住在这里；model.scad 顶部有同名说明）
BRAND_TEXT = "苗壮制造"
# 本机实测能出汉字的三款：Hiragino Sans GB / Heiti SC / Songti SC（PingFang SC 在 macOS 上不存在）
BRAND_FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"

MIN_LIGAMENT = 3.2   # 孔与孔、孔与边之间最少的料（0.4 喷嘴的 8 倍 ≈ 结构够用）
BRIDGE_MAX = 15.0    # 朝下平段的桥接上限（孔顶那条直边；超过就要支撑）
CORNER_LOSS = 4.0 - math.pi


def rrect_area(w, d, r):
    """圆角矩形面积（精确）。"""
    return w * d - CORNER_LOSS * r * r


def fit_count(usable, hole, gap, min_ligament=MIN_LIGAMENT):
    """在长 usable 的段里最多排几个 hole（孔间 gap），且两端剩下的料 ≥ min_ligament。"""
    n = int((usable + gap) // (hole + gap))
    while n > 0:
        span = n * hole + (n - 1) * gap
        if (usable - span) / 2.0 >= min_ligament - 1e-9:
            break
        n -= 1
    return max(0, n)


def centers(n, hole, gap):
    """n 个孔以 0 为中心对称排开，返回各孔中心（单位 mm）。"""
    return [(i - (n - 1) / 2.0) * (hole + gap) for i in range(n)]


def row_zs(low, high, rows, hole_h):
    """在 [low, high] 区间里排 rows 排孔：返回 (料带高, [各排孔心 z])。"""
    gap = (high - low - rows * hole_h) / (rows + 1)
    return gap, [low + gap + hole_h / 2.0 + i * (hole_h + gap) for i in range(rows)]


def load():
    p = read_params(SCAD)
    p["brand_text"] = BRAND_TEXT
    p["brand_font"] = BRAND_FONT

    # ---- 尺寸链 ----
    p["inner_w"] = p["cells_x"] * p["cell_w"] + (p["cells_x"] - 1) * p["divider_t"]
    p["inner_d"] = p["cells_y"] * p["cell_d"] + (p["cells_y"] - 1) * p["divider_t"]
    p["outer_w"] = p["inner_w"] + 2 * p["wall_t"]
    p["outer_d"] = p["inner_d"] + 2 * p["wall_t"]
    p["cavity_h"] = p["outer_h"] - p["floor_t"]
    p["cavity_r"] = p["corner_r"] - p["wall_t"]

    # ---- 可开孔段（圆角段不能开孔，再退 band_side） ----
    p["flat_x"] = p["outer_w"] - 2 * p["corner_r"]      # 前/后墙平段
    p["flat_y"] = p["outer_d"] - 2 * p["corner_r"]      # 左/右墙平段
    usable_x = p["flat_x"] - 2 * p["band_side"]
    usable_y = p["flat_y"] - 2 * p["band_side"]
    p["usable_x"] = usable_x
    p["usable_y"] = usable_y

    # ---- 排高 ----
    top = p["outer_h"] - p["ledge_h"]
    p["row_gap"], p["row_zs"] = row_zs(p["sill_h"], top, p["louver_rows"], p["louver_h"])
    _, p["div_row_zs"] = row_zs(p["sill_h"], top, p["div_rows"], p["louver_h"])

    # ---- 每面孔数 ----
    p["n_back"] = fit_count(usable_x, p["louver_w"], p["louver_gap"]) if p["front_solid"] else 0
    p["n_side"] = fit_count(usable_y, p["louver_w"], p["louver_gap"])
    p["n_div_x"] = fit_count(p["inner_d"] - 2 * p["band_side"], p["louver_w"], p["louver_gap"])
    p["n_div_y"] = fit_count(p["inner_w"] - 2 * p["band_side"], p["louver_w"], p["louver_gap"])
    # 每面/每排孔端到端头的实际余料（check 要 ≥ MIN_LIGAMENT）
    p["margin_back"] = (usable_x - (p["n_back"] * p["louver_w"] + max(0, p["n_back"] - 1) * p["louver_gap"])) / 2.0
    p["margin_side"] = (usable_y - (p["n_side"] * p["louver_w"] + max(0, p["n_side"] - 1) * p["louver_gap"])) / 2.0

    # ---- 底板孔（每格） ----
    cell_usable_x = p["cell_w"] - 2 * p["bottom_edge"]
    cell_usable_y = p["cell_d"] - 2 * p["bottom_edge"]
    p["n_bx"] = fit_count(cell_usable_x, p["bottom_hole_d"], p["bottom_gap"])
    p["n_by"] = fit_count(cell_usable_y, p["bottom_hole_d"], p["bottom_gap"])

    # ---- 格子中心 ----
    cell_x = [-p["inner_w"] / 2 + i * (p["cell_w"] + p["divider_t"]) + p["cell_w"] / 2
              for i in range(p["cells_x"])]
    cell_y = [-p["inner_d"] / 2 + j * (p["cell_d"] + p["divider_t"]) + p["cell_d"] / 2
              for j in range(p["cells_y"])]
    p["cell_x"], p["cell_y"] = cell_x, cell_y

    # ---- 孔位清单（build_mesh.py 直接照着切） ----
    louvers = []
    # 后墙（+Y）：孔长沿 X、厚度沿 Y
    for z in p["row_zs"]:
        for cx in centers(p["n_back"], p["louver_w"], p["louver_gap"]):
            louvers.append({"where": "back", "dir": "y", "x": cx, "y": p["outer_d"] / 2,
                            "z": z, "t": p["wall_t"]})
    # 左/右墙（∓X）：孔长沿 Y、厚度沿 X
    for side in (-1, 1):
        for z in p["row_zs"]:
            for cy in centers(p["n_side"], p["louver_w"], p["louver_gap"]):
                louvers.append({"where": "left" if side < 0 else "right", "dir": "x",
                                "x": side * p["outer_w"] / 2, "y": cy, "z": z, "t": p["wall_t"]})
    # 内隔板：垂直于 X 的（孔长沿 Y，厚度沿 X）
    for i in range(1, p["cells_x"]):
        dx = -p["inner_w"] / 2 + i * p["cell_w"] + (i - 0.5) * p["divider_t"]
        for z in p["div_row_zs"]:
            for cy in centers(p["n_div_x"], p["louver_w"], p["louver_gap"]):
                louvers.append({"where": f"div_x{i}", "dir": "x", "x": dx, "y": cy,
                                "z": z, "t": p["divider_t"]})
    # 内隔板：垂直于 Y 的（孔长沿 X，厚度沿 Y）
    for j in range(1, p["cells_y"]):
        dy = -p["inner_d"] / 2 + j * p["cell_d"] + (j - 0.5) * p["divider_t"]
        for z in p["div_row_zs"]:
            for cx in centers(p["n_div_y"], p["louver_w"], p["louver_gap"]):
                louvers.append({"where": f"div_y{j}", "dir": "y", "x": cx, "y": dy,
                                "z": z, "t": p["divider_t"]})
    p["louvers"] = louvers

    bottom_holes = []
    for cx in cell_x:
        for cy in cell_y:
            for ox in centers(p["n_bx"], p["bottom_hole_d"], p["bottom_gap"]):
                for oy in centers(p["n_by"], p["bottom_hole_d"], p["bottom_gap"]):
                    bottom_holes.append({"x": cx + ox, "y": cy + oy})
    p["bottom_holes"] = bottom_holes

    # ---- 解析体积 ----
    p["A_louver"] = p["louver_w"] * p["louver_h"] - CORNER_LOSS * p["louver_r"] ** 2
    V_louver_back = p["n_back"] * p["louver_rows"] * p["A_louver"] * p["wall_t"]
    V_louver_side = 2 * p["n_side"] * p["louver_rows"] * p["A_louver"] * p["wall_t"]
    V_louver_div = ((p["cells_x"] - 1) * p["n_div_x"] + (p["cells_y"] - 1) * p["n_div_y"]) \
        * p["div_rows"] * p["A_louver"] * p["divider_t"]
    V_bottom = len(bottom_holes) * math.pi * (p["bottom_hole_d"] / 2.0) ** 2 * p["floor_t"]
    p["V_base"] = rrect_area(p["outer_w"], p["outer_d"], p["corner_r"]) * p["outer_h"] \
        - rrect_area(p["inner_w"], p["inner_d"], p["cavity_r"]) * p["cavity_h"]
    p["V_dividers"] = (p["cells_x"] - 1) * p["divider_t"] * p["inner_d"] * p["cavity_h"] \
        + (p["cells_y"] - 1) * p["divider_t"] * p["inner_w"] * p["cavity_h"]
    p["V_holes"] = V_louver_back + V_louver_side + V_louver_div + V_bottom
    p["V_no_text"] = p["V_base"] + p["V_dividers"] - p["V_holes"]
    p["V_outer_box"] = p["outer_w"] * p["outer_d"] * p["outer_h"]
    p["volume_ratio"] = p["V_no_text"] / p["V_outer_box"]

    # ---- 可打印性判据 ----
    p["bridge_flat"] = p["louver_w"] - 2 * p["louver_r"]          # 孔顶那条朝下平段
    p["min_ligament"] = min(
        p["louver_gap"], p["margin_back"], p["margin_side"], p["row_gap"],
        p["bottom_gap"], p["bottom_edge"],
    )
    p["brand_z_min"] = p["brand_z"] - p["brand_cap_h"] / 2.0
    p["brand_z_max"] = p["brand_z"] + p["brand_cap_h"] / 2.0
    return p


def main(argv):
    ap = argparse.ArgumentParser(add_help=True, description="idea-017 派生量")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    p = load()
    if a.out:
        Path(a.out).write_text(json.dumps(p, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n")
    if a.json:
        print(json.dumps(p, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"外廓 {p['outer_w']:.1f} x {p['outer_d']:.1f} x {p['outer_h']:.1f} mm"
              f"（{p['cells_x']}x{p['cells_y']} 格，内腔 {p['inner_w']:.1f} x {p['inner_d']:.1f} x {p['cavity_h']:.1f}）")
        print(f"  墙面孔 {len(p['louvers'])} 个（后墙 {p['n_back']}/排、侧墙 {p['n_side']}/排、"
              f"隔板 {p['n_div_x']}/{p['n_div_y']} 个/排），底板孔 {len(p['bottom_holes'])} 个"
              f"（每格 {p['n_bx']}x{p['n_by']}）")
        print(f"  排高 {[round(z,1) for z in p['row_zs']]}，孔间料 {p['louver_gap']}mm，"
              f"孔顶平段 {p['bridge_flat']:.1f}mm，最小韧带 {p['min_ligament']:.2f}mm")
        print(f"  解析体积 {p['V_no_text']/1000:.2f} cm³（外廓 {p['V_outer_box']/1000:.0f} cm³ 的 "
              f"{p['volume_ratio']*100:.1f}%；未含「{p['brand_text']}」浮雕）"
              f" ≈ {p['V_no_text']/1000*1.24:.1f}g PLA")
        if a.out:
            print(f"派生量 -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
