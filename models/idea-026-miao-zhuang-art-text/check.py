#!/usr/bin/env python3
"""idea-026 自检：全过才交付，退出码 0。

只读 model.scad / 同目录 STL/3MF/report，不写文件。四类判据：

  A 尺寸链：字高/板厚/边框/底座/插槽都够厚；最细笔画（10% 分位）≥ 门槛；
           槽宽 = 板厚 + 2×单边间隙，且间隙落在 0.15~0.6 的可插拔区间
  B 可打印：单个连通体、底面贴床（min z=0）、外廓 ≤ 234mm、非贴床朝下面占比 ≤ 1%
  C 字形：把 STL 字面顶盖点云重新栅格化，跟 PIL 用同一字体渲的字做 IoU ——
          正写 IoU 高、镜像 IoU 低，能抓「字反了 / 字丢了 / 出成方框」
  D 文件：STL 水密/绕序/体积 + 3MF 顶点面数一致（check_model.py 同一套）
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(Path.home() / ".cah-data/skills/shared/3d-print-ideas/scripts"))
import model as M  # noqa: E402
import scad_build as SB  # noqa: E402
from check_model import read_stl  # noqa: E402

FACES = ["miao-zhuang-xingkai", "miao-zhuang-weibei"]
BASE = "miao-zhuang-base"
IOU_MIN = 0.80
PX_PER_MM = 5.0


def report(name):
    return json.loads((HERE / f"{name}-report.json").read_text())


def mesh(name):
    stl, three = HERE / f"{name}.stl", HERE / f"{name}.3mf"
    _fmt, _n, faces, _normals = read_stl(stl)
    return faces, SB.check_stl(stl, three if three.exists() else None)


def common_fails(name, faces, p):
    fails, notes = [], []
    v = faces.reshape(-1, 3)
    size = v.max(0) - v.min(0)
    zmin = float(v[:, 2].min())
    if abs(zmin) > 1e-3:
        fails.append(f"底面没贴床: min z = {zmin:.3f}")
    if max(size[0], size[1]) > p["bed_max_mm"]:
        fails.append(f"外廓 {size[0]:.1f}x{size[1]:.1f} 超过 {p['bed_max_mm']}")

    nn = np.cross(faces[:, 1] - faces[:, 0], faces[:, 2] - faces[:, 0])
    area = np.linalg.norm(nn, axis=1) / 2
    nn /= np.maximum(np.linalg.norm(nn, axis=1), 1e-12)[:, None]
    bed = faces[:, :, 2].max(axis=1) < 0.6  # 贴床 + 0.4 倒角带
    overhang = area[(nn[:, 2] < -0.7) & ~bed].sum() / max(area.sum(), 1e-9)
    if overhang > p["max_overhang_ratio"]:
        fails.append(f"非贴床朝下面占比 {overhang*100:.2f}% > {p['max_overhang_ratio']*100:.0f}%")
    notes.append(f"朝下面占比 {overhang*100:.2f}%")
    notes.append(f"{size[0]:.1f}×{size[1]:.1f}×{size[2]:.1f} mm")
    return fails, notes, nn, area


def glyph_mask(font_path, text, font_size, shape):
    f = ImageFont.truetype(font_path, int(font_size * PX_PER_MM))
    img = Image.new("L", (2400, 2400), 0)
    ImageDraw.Draw(img).text((1200, 1200), text, font=f, fill=255, anchor="mm")
    crop = img.crop(img.getbbox())
    return np.array(crop.resize((shape[1], shape[0]), Image.LANCZOS)) > 127


def top_mask(faces):
    """字朝 +Z：把 z≈max、法线朝 +Z 的三角面精确栅格化成正投影掩码（不是采样点，有洞会掉 IoU）。"""
    n = np.cross(faces[:, 1] - faces[:, 0], faces[:, 2] - faces[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
    zmax = faces[:, :, 2].max()
    pick = (n[:, 2] > 0.95) & (zmax - faces[:, :, 2].min(axis=1) < 0.05)
    tri = faces[pick][:, :, [0, 1]]
    if len(tri) == 0:
        return None, None
    lo = tri.reshape(-1, 2).min(0)
    hi = tri.reshape(-1, 2).max(0)
    w = max(1, int(round((hi[0] - lo[0]) * PX_PER_MM)))
    h = max(1, int(round((hi[1] - lo[1]) * PX_PER_MM)))
    grid = np.zeros((h, w), dtype=bool)
    for t in tri:
        p0, p1, p2 = (t - lo) * PX_PER_MM
        x0 = int(max(0, np.floor(min(p0[0], p1[0], p2[0]))))
        x1 = int(min(w - 1, np.ceil(max(p0[0], p1[0], p2[0]))))
        y0 = int(max(0, np.floor(min(p0[1], p1[1], p2[1]))))
        y1 = int(min(h - 1, np.ceil(max(p0[1], p1[1], p2[1]))))
        if x0 > x1 or y0 > y1:
            continue
        X, Y = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        den = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1])
        if abs(den) < 1e-12:
            continue
        wa = ((p1[1] - p2[1]) * (X - p2[0]) + (p2[0] - p1[0]) * (Y - p2[1])) / den
        wb = ((p2[1] - p0[1]) * (X - p2[0]) + (p0[0] - p2[0]) * (Y - p2[1])) / den
        inside = (wa >= -1e-9) & (wb >= -1e-9) & (wa + wb <= 1 + 1e-9)
        grid[y0:y1 + 1, x0:x1 + 1] |= inside
    return grid, (lo, hi)


def iou(grid, ref):
    ref = ref if ref.shape == grid.shape else np.array(
        Image.fromarray(ref).resize((grid.shape[1], grid.shape[0]), Image.NEAREST))
    return np.logical_and(grid, ref).sum() / max(np.logical_or(grid, ref).sum(), 1)


def check_face(name, p):
    rep = report(name)
    faces, meshrep = mesh(name)
    fails = [f"网格: {f}" for f in meshrep.get("failures", [])]
    notes = []
    for key, minimum in (("letter_h", 2.0), ("plate_t", 1.6), ("border_w", 1.2),
                         ("border_h", 0.6), ("plate_chamfer", 0.2)):
        if p[key] < minimum:
            fails.append(f"{key}={p[key]} < {minimum}")
    if rep["stroke_mm"]["p10"] < p["min_stroke_mm"]:
        fails.append(f"最细笔画段 {rep['stroke_mm']['p10']}mm < 门槛 {p['min_stroke_mm']}mm")
    notes.append(f"笔画 p10 {rep['stroke_mm']['p10']}mm / 笔尖 {rep['stroke_mm']['min']}mm"
                 f" / 中位 {rep['stroke_mm']['median']}mm")

    f2, n2, _nn, _a = common_fails(name, faces, p)
    fails += f2
    notes += n2
    if rep["solids"] != 1:
        fails.append(f"不是单体: {rep['solids']}")

    grid, box = top_mask(faces)
    if grid is None:
        fails.append("找不到字面（字没生成？）")
    else:
        ref = glyph_mask(M.FONTS[rep["font"]], p["text"], p["font_size"], grid.shape)
        # 模型 +Y 朝上、图像 y 朝下：先竖翻再比；镜像判据 = 再横翻一次
        good = iou(grid[::-1], ref)
        mirror = iou(grid[::-1, ::-1], ref)
        notes.append(f"字形 IoU {good:.3f}（镜像 {mirror:.3f}）")
        if good < IOU_MIN:
            fails.append(f"字形 IoU {good:.3f} < {IOU_MIN}")
        if mirror >= good:
            fails.append(f"字形疑似镜像（镜像 {mirror:.3f} ≥ 正写 {good:.3f}）")
        lo, hi = box
        if not (0.3 < (hi[1] - lo[1]) / (hi[0] - lo[0]) < 1.2):
            fails.append("字面长宽比异常")
    return fails, notes


def check_base(p, face_reports):
    rep = report(BASE)
    faces, meshrep = mesh(BASE)
    fails = [f"网格: {f}" for f in meshrep.get("failures", [])]
    notes = []
    for key, minimum in (("base_h", 6.0), ("slot_depth", 3.0), ("base_chamfer", 0.2)):
        if p[key] < minimum:
            fails.append(f"{key}={p[key]} < {minimum}")
    if not (0.15 <= p["slot_clear"] <= 0.6):
        fails.append(f"单边间隙 {p['slot_clear']} 不在 0.15~0.6（装不进/会晃）")
    slot_w = p["plate_t"] + 2 * p["slot_clear"]
    if abs(rep["slot_w"] - slot_w) > 0.01:
        fails.append(f"报告槽宽 {rep['slot_w']} != {slot_w}")
    if rep["chamfer"] is not True:
        fails.append(f"底座顶边倒角 {rep['chamfer']}")
    if p["slot_depth"] > p["base_h"] - 2:
        fails.append("插槽太深，底座底部剩不到 2mm")
    for fr in face_reports:
        if fr["plate_w"] > rep["base_w"] + 1e-6:
            fails.append(f"牌面 {fr['plate_w']} 比底座 {rep['base_w']} 宽")
    if not (p["plate_t"] < slot_w < p["plate_t"] + 1.0):
        fails.append("插槽间隙超出可插拔范围")

    f2, n2, _nn, _a = common_fails(BASE, faces, p)
    fails += f2
    notes += n2
    notes.append(f"槽宽 {rep['slot_w']}mm / 深 {rep['slot_depth']}mm / 单边间隙 {rep['slot_clear_per_side']}mm")
    if rep["solids"] != 1:
        fails.append(f"不是单体: {rep['solids']}")
    return fails, notes


def main():
    p = M.load()
    bad = 0
    face_reports = []
    for name in FACES:
        fails, notes = check_face(name, p)
        face_reports.append(report(name))
        print(f"[{'PASS' if not fails else 'FAIL'}] {name}")
        for n in notes:
            print("   ·", n)
        for f in fails:
            print("   ✗", f)
        bad += len(fails)
    fails, notes = check_base(p, face_reports)
    print(f"[{'PASS' if not fails else 'FAIL'}] {BASE}")
    for n in notes:
        print("   ·", n)
    for f in fails:
        print("   ✗", f)
    bad += len(fails)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
