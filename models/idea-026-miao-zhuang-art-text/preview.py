#!/usr/bin/env python3
"""出交付用的效果图：正交投影 + z-buffer + 单向光照，自己算，不依赖 Blender/OpenGL。

  preview/face-<字体>.png        牌面正上方看（字朝 +Z）：判字对不对、边框够不够
  preview/assembled-<字体>.png   牌面插进底座后立起来（3/4 视角）：判整体比例
装配图只用于看图，不是打印件 —— 打印时牌面和底座分开打。

用法: python3 preview.py
"""
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(Path.home() / ".cah-data/skills/shared/3d-print-ideas/scripts"))
from check_model import read_stl  # noqa: E402

OUT = HERE / "preview"
BODY_RGB = np.array([196, 198, 204], dtype=np.float32)
BG_RGB = np.array([250, 250, 251], dtype=np.float32)
FACES = ["miao-zhuang-xingkai", "miao-zhuang-weibei"]


def load(name):
    _fmt, _n, faces, _norm = read_stl(HERE / f"{name}.stl")
    return faces.astype(np.float64)


def write_stl(path, faces):
    """二进制 STL：法线按右手法则重算，顶点顺序保持。"""
    n = np.cross(faces[:, 1] - faces[:, 0], faces[:, 2] - faces[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
    with open(path, "wb") as fh:
        fh.write(b"idea-026 assembled preview".ljust(80, b" "))
        fh.write(struct.pack("<I", len(faces)))
        for tri, nor in zip(faces, n):
            fh.write(struct.pack("<12fH", *nor, *tri[0], *tri[1], *tri[2], 0))


def render(faces, view, up, width=1600, name="r"):
    view = np.asarray(view, dtype=np.float64)
    view /= np.linalg.norm(view)
    up = np.asarray(up, dtype=np.float64)
    u = np.cross(up, view)
    u /= np.linalg.norm(u)
    w = np.cross(view, u)

    pts = faces.reshape(-1, 3)
    su, sw = pts @ u, pts @ w
    scale = (width - 120) / max(su.max() - su.min(), sw.max() - sw.min())
    height = int((sw.max() - sw.min()) * scale) + 120

    n = np.cross(faces[:, 1] - faces[:, 0], faces[:, 2] - faces[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
    light = view * 0.9 + u * 0.45 + w * 0.35
    light /= np.linalg.norm(light)
    lam = 0.42 + 0.58 * np.abs(n @ light)

    zbuf = np.full((height, width), -1e18)
    shade = np.zeros((height, width), dtype=np.float32)
    X = (faces @ u - su.min()) * scale + 60
    Y = (sw.max() - faces @ w) * scale + 60
    D = faces @ view

    for i in range(len(faces)):
        x0 = int(max(0, np.floor(X[i].min())))
        x1 = int(min(width - 1, np.ceil(X[i].max())))
        y0 = int(max(0, np.floor(Y[i].min())))
        y1 = int(min(height - 1, np.ceil(Y[i].max())))
        if x0 > x1 or y0 > y1:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        ax, ay, bx, by, cx, cy = (X[i, 0], Y[i, 0], X[i, 1], Y[i, 1], X[i, 2], Y[i, 2])
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-12:
            continue
        w0 = ((by - cy) * (gx - cx) + (cx - bx) * (gy - cy)) / den
        w1 = ((cy - ay) * (gx - cx) + (ax - cx) * (gy - cy)) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-9) & (w1 >= -1e-9) & (w2 >= -1e-9)
        if not inside.any():
            continue
        depth = w0 * D[i, 0] + w1 * D[i, 1] + w2 * D[i, 2]
        sub = zbuf[y0:y1 + 1, x0:x1 + 1]
        take = inside & (depth > sub)
        sub[take] = depth[take]
        shade[y0:y1 + 1, x0:x1 + 1][take] = lam[i]

    covered = shade > 0
    img = np.where(covered[:, :, None], shade[:, :, None] * BODY_RGB, BG_RGB)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(OUT / f"{name}.png")
    print("效果图 ->", OUT / f"{name}.png")


def assembled(face_faces, base_faces, base_h, slot_depth, slot_y, plate_t, plate_h):
    """牌面绕 X 转 -90°（字朝 -Y）插进槽：只做示意图，不参与打印。"""
    f = face_faces.copy()
    f[:, :, [1, 2]] = f[:, :, [2, 1]] * np.array([1, -1])   # (y,z) -> (z, -y)
    f[:, :, 1] += slot_y - plate_t / 2
    f[:, :, 2] += base_h - slot_depth + plate_h / 2
    return np.concatenate([base_faces, f], axis=0)


def main():
    OUT.mkdir(exist_ok=True)
    import model as M
    p = M.load()
    base = load("miao-zhuang-base")
    for name in FACES:
        face = load(name)
        render(face, view=(0, 0, 1), up=(0, 1, 0), name=f"face-{name.split('-')[-1]}")
        asm = assembled(face, base, p["base_h"], p["slot_depth"], p["slot_y"],
                        p["plate_t"], face[:, :, 1].max() - face[:, :, 1].min())
        stl = OUT / f"assembled-{name.split('-')[-1]}-preview.stl"
        write_stl(stl, asm)
        render(asm, view=(0.55, -1.0, 0.35), up=(0, 0, 1),
               name=f"assembled-{name.split('-')[-1]}")

    for key in ("weibei", "xingkai", "baoli"):
        solid = load(f"miao-zhuang-solid-{key}")
        render(solid, view=(0, 0, 1), up=(0, 1, 0), name=f"solid-{key}")
        render(solid, view=(0.35, -0.75, 0.55), up=(0, 0, 1), name=f"solid-{key}-iso")


if __name__ == "__main__":
    main()
