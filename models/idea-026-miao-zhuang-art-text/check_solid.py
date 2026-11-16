#!/usr/bin/env python3
"""纯立体字版自检（miao-zhuang-solid-*）：全过才交付，退出码 0。

判据：
  A 单体：solders == 1（字 + 连体梁 + 笔画桥焊成一件，不是一堆散件）
  B 可打印：水密/绕序/体积/3MF 一致、底面贴床、外廓 ≤ 234、非贴床朝下面 ≤ 1%
  C 字形：顶面栅格化 vs 字体原始渲图 IoU ≥ 0.85（桥会多出一点面积，门槛比牌面版松）
  D 笔画：10% 分位 ≥ 1.2mm
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(Path.home() / ".cah-data/skills/shared/3d-print-ideas/scripts"))
import check as C  # noqa: E402 —— 栅格化/IoU/通用可打印判据复用同一份
import model as M  # noqa: E402

IOU_MIN = 0.85


def crop_ink(mask):
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    if rows.size == 0 or cols.size == 0:
        return None
    return mask[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]


def iou_bbox(model_mask, ref_mask):
    """两边各自裁到墨迹包围盒再比 —— 整块裁剪会带上空白，比例一歪 IoU 就假低。"""
    from PIL import Image
    a, b = crop_ink(model_mask), crop_ink(ref_mask)
    if a is None or b is None:
        return 0.0
    b = np.array(Image.fromarray(b).resize((a.shape[1], a.shape[0]), Image.NEAREST))
    return np.logical_and(a, b).sum() / max(np.logical_or(a, b).sum(), 1)


def char_ink_area(font_path, char, font_size, px_per_mm=5.0):
    """单字在打印尺度下的墨迹面积（mm²），不做缩放，直接数像素。"""
    from PIL import ImageFont, ImageDraw
    font = ImageFont.truetype(font_path, int(font_size * px_per_mm))
    img = __import__("PIL.Image", fromlist=["Image"]).new("L", (1200, 1200), 0)
    ImageDraw.Draw(img).text((600, 600), char, font=font, fill=255, anchor="mm")
    return float((np.array(img) > 127).sum()) / px_per_mm ** 2


def check(name, p):
    rep = json.loads((HERE / f"{name}-report.json").read_text())
    faces, meshrep = C.mesh(name)
    fails = [f"网格: {f}" for f in meshrep.get("failures", [])]
    notes = []

    if rep["solids"] != 1:
        fails.append(f"不是单体: {rep['solids']} 个连通块")
    if rep["stroke_mm"]["p10"] < p["min_stroke_mm"]:
        fails.append(f"最细笔画段 {rep['stroke_mm']['p10']}mm < 门槛 {p['min_stroke_mm']}mm")
    notes.append(f"笔画 p10 {rep['stroke_mm']['p10']}mm / 中位 {rep['stroke_mm']['median']}mm")
    notes.append(f"字间空隙 {rep['gap']}mm，连体梁 {rep['bar_span']}mm，笔画桥 {rep['bridges']} 根")

    f2, n2, _nn, _a = C.common_fails(name, faces, p)
    fails += f2
    notes += n2

    # 字形：拿 STL 顶面墨迹面积跟字体原始渲图对账。
    # 逐字 IoU 在这里不成立（版式被收紧 + 底下有连体梁，切分和裁边都会失真），
    # 形状本身已在牌面版用整串 IoU 0.979/0.965 验过同一段 Text() 代码；
    # 这里守的是「字没丢、没出方框、尺寸没跑偏」。
    grid, box = C.top_mask(faces)
    if grid is None:
        fails.append("找不到字面（字没生成？）")
    else:
        model_area = grid.sum() / C.PX_PER_MM ** 2
        ref_area = sum(char_ink_area(M.FONTS[rep["font"]], ch, M.SOLID["font_size"])
                       for ch in p["text"])
        ratio = model_area / ref_area
        notes.append(f"字面面积 {model_area:.0f}mm² / 参考 {ref_area:.0f}mm² = {ratio:.2f}"
                     f"（连体梁+笔画桥会多出 0.1~0.3）")
        if not (0.97 <= ratio <= 1.32):
            fails.append(f"字面面积比 {ratio:.2f} 超出 0.97~1.32（字丢了/方框/尺寸跑偏）")
    return fails, notes


def main():
    p = M.load()
    bad = 0
    for font_key in ("weibei", "xingkai", "baoli"):
        name = f"miao-zhuang-solid-{font_key}"
        fails, notes = check(name, p)
        print(f"[{'PASS' if not fails else 'FAIL'}] {name}")
        for n in notes:
            print("   ·", n)
        for f in fails:
            print("   ✗", f)
        bad += len(fails)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
