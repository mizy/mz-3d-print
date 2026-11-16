#!/usr/bin/env python3
"""idea-026 「苗壮」艺术字 3D 牌：build123d 建实体，出 STL + 3MF + 报告。

**为什么不用 OpenSCAD**：本机 macOS 27 / arm64 已无 Rosetta 2，skill 里那份 OpenSCAD 是
x86_64 单架构，内核直接 Bad CPU type 拒绝执行（sample-nameplate 那批是当年还能跑时出的）。
改走 skill 文档化的 build123d 路线（OpenCASCADE），参数仍只读 model.scad。

**为什么是两件**：牌面平放打印（字朝上，顶面最平整、零支撑）；底座单出带竖插槽。
一体立式拿不了——牌面立起来后，立体字每一笔横画下沿都是 100% 朝下悬垂，得全上支撑。

跑法（离线，走 uv 缓存）:
  uv run --offline --python 3.13 --with cadgen==0.7.26 python build_mesh.py

产物（同目录）:
  miao-zhuang-xingkai.stl/.3mf   行楷牌面（主推）
  miao-zhuang-weibei.stl/.3mf    魏碑牌面（同结构换字，字面更硬朗）
  miao-zhuang-base.stl/.3mf      底座（两片牌面通用，槽宽按 plate_t + 2×slot_clear）
  <name>-report.json             实测尺寸 / 体积 / 连通块 / 最细笔画
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = Path.home() / ".cah-data/skills/shared/3d-print-ideas/scripts"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SCRIPTS))

import numpy as np  # noqa: E402
from build123d import (Align, Axis, Box, Location, RectangleRounded,  # noqa: E402
                       Text, chamfer, extrude, export_stl, fillet)
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import model as M  # noqa: E402
import scad_build as SB  # noqa: E402 —— STL 复核 / 3MF 写出复用 skill 里那一份

FACES = [("miao-zhuang-xingkai", "xingkai"), ("miao-zhuang-weibei", "weibei")]
BASE_NAME = "miao-zhuang-base"


def stroke_stats(text, font_path, font_size, px_per_mm=8.0):
    """按打印尺度栅格化，用「腐蚀层数」当到边缘的距离，在骨架脊线上取笔画宽度分布。

    一次腐蚀 = 1/8mm 半径。脊线点（8 邻域内距离的局部极大）的 2×距离 ≈ 局部笔画宽。
    报 10% 分位（细笔画段）和最小值（行楷的笔尖）——平均值会掩盖打不出来的尖。
    """
    size_px = int(font_size * px_per_mm * 2)
    font = ImageFont.truetype(font_path, size_px)
    img = Image.new("L", (size_px * 3, size_px * 2), 0)
    ImageDraw.Draw(img).text((size_px, size_px // 2), text, font=font, fill=255)
    mask = np.array(img) > 127

    depth = np.zeros(mask.shape, dtype=np.int16)
    level, cur = 1, mask.copy()
    while cur.any():
        depth[cur] = level
        pad = np.zeros((cur.shape[0] + 2, cur.shape[1] + 2), dtype=bool)
        pad[1:-1, 1:-1] = cur
        cur = (pad[1:-1, 1:-1] & pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2]
               & pad[1:-1, 2:] & pad[:-2, :-2] & pad[:-2, 2:] & pad[2:, :-2] & pad[2:, 2:])
        level += 1

    padded = np.pad(depth, 1, mode="edge")
    ridge = depth > 0
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx or dy:
                ridge &= depth >= padded[1 + dy:1 + dy + depth.shape[0], 1 + dx:1 + dx + depth.shape[1]]
    widths = 2.0 * depth[ridge] / px_per_mm
    if widths.size == 0:
        return {"p10": 0.0, "min": 0.0, "median": 0.0}
    return {"p10": round(float(np.percentile(widths, 10)), 2),
            "min": round(float(widths.min()), 2),
            "median": round(float(np.percentile(widths, 50)), 2)}


def face_body(p, font_path):
    """牌面：底板（z 0..plate_t）+ 边框 + 立体字，字朝 +Z；底边倒角给插槽让口。"""
    txt = Text(p["text"], font_size=p["font_size"], font_path=font_path,
               align=(Align.CENTER, Align.CENTER))
    bb = txt.bounding_box()
    w = bb.size.X + 2 * p["pad"]
    h = bb.size.Y + 2 * p["pad"]

    plate = extrude(RectangleRounded(w, h, p["corner_r"]), amount=p["plate_t"])
    plate = chamfer(plate.edges().group_by(Axis.Z)[0], length=p["plate_chamfer"])

    ring = RectangleRounded(w, h, p["corner_r"]) - RectangleRounded(
        w - 2 * p["border_w"], h - 2 * p["border_w"], max(p["corner_r"] - p["border_w"], 0.6))
    lip = Location((0, 0, p["plate_t"]))
    border = extrude(ring, amount=p["border_h"]).moved(lip)
    letters = extrude(txt, amount=p["letter_h"]).moved(lip)
    body = plate + border + letters
    return body, {"text_w": round(bb.size.X, 2), "text_h": round(bb.size.Y, 2),
                  "plate_w": round(w, 2), "plate_h": round(h, 2)}


def base_body(p, plate_w):
    """底座：圆角方块 + 竖插槽（开口朝上，槽壁竖直，免支撑）+ 顶边倒角。"""
    bw = plate_w + 2 * p["base_side"]
    base = Box(bw, p["base_depth"], p["base_h"])
    base = base.moved(Location((0, 0, p["base_h"] / 2)))
    base = fillet(base.edges().filter_by(Axis.Z), radius=p["base_corner_r"])

    slot_w = p["plate_t"] + 2 * p["slot_clear"]
    slot = Box(bw, slot_w, p["slot_depth"] + 1)
    slot = slot.moved(Location(
        (0, p["slot_y"], p["base_h"] - p["slot_depth"] / 2 + 0.5)))
    base = base - slot
    try:
        base = chamfer(base.edges().group_by(Axis.Z)[-1], length=p["base_chamfer"])
        chamfered = True
    except Exception as exc:                      # 倒角失败不要静默：报告里写清楚
        chamfered = f"失败: {exc}"
    return base, {"base_w": round(bw, 2), "base_d": p["base_depth"], "base_h": p["base_h"],
                  "slot_w": round(slot_w, 2), "slot_depth": p["slot_depth"],
                  "slot_clear_per_side": p["slot_clear"], "chamfer": chamfered}


def emit(name, body, rep):
    stl, three = HERE / f"{name}.stl", HERE / f"{name}.3mf"
    export_stl(body, str(stl), tolerance=0.05, angular_tolerance=0.2)
    SB.stl_to_3mf(stl, three, name)
    bb = body.bounding_box()
    rep.update({
        "stl": stl.name, "3mf": three.name,
        "size": [round(bb.size.X, 2), round(bb.size.Y, 2), round(bb.size.Z, 2)],
        "min_corner": [round(bb.min.X, 2), round(bb.min.Y, 2), round(bb.min.Z, 2)],
        "volume_mm3": round(body.volume, 1), "solids": len(body.solids()),
    })
    (HERE / f"{name}-report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2))
    print(f"{name}: {rep['size']} mm, {rep['volume_mm3']/1000:.1f} cm3, solids {rep['solids']}")
    return rep


def main():
    p = M.load()
    widest = 0.0
    for name, font_key in FACES:
        body, rep = face_body(p, M.FONTS[font_key])
        rep.update({"font": font_key, "kind": "牌面",
                    "stroke_mm": stroke_stats(p["text"], M.FONTS[font_key], p["font_size"])})
        emit(name, body, rep)
        widest = max(widest, rep["plate_w"])

    body, rep = base_body(p, widest)
    rep["kind"] = "底座"
    emit(BASE_NAME, body, rep)


if __name__ == "__main__":
    main()
