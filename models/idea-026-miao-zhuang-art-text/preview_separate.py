#!/usr/bin/env python3
"""分体版效果图：从 plate 3MF 里读两个对象，出顶视图 + 3/4 图，再拼一张三字体总览。

用法: python3 preview_separate.py
"""
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from preview import OUT, render  # noqa: E402

NS = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
FONTS = ["weibei", "xingkai", "baoli"]


def read_plate(name):
    faces = []
    with zipfile.ZipFile(HERE / f"{name}.3mf") as z:
        root = ET.fromstring(z.read("3D/3dmodel.model"))
    for obj in root.findall(".//m:object", NS):
        verts = [(float(v.get("x")), float(v.get("y")), float(v.get("z")))
                 for v in obj.findall(".//m:vertex", NS)]
        tris = [(int(t.get("v1")), int(t.get("v2")), int(t.get("v3")))
                for t in obj.findall(".//m:triangle", NS)]
        faces.append(np.array(verts)[np.array(tris)])
    return np.concatenate(faces, axis=0)


def main():
    OUT.mkdir(exist_ok=True)
    for font in FONTS:
        faces = read_plate(f"miao-zhuang-sep-{font}-plate")
        render(faces, view=(0, 0, 1), up=(0, 1, 0), name=f"sep-{font}")
        render(faces, view=(0.35, -0.75, 0.55), up=(0, 0, 1), name=f"sep-{font}-iso")

    tiles = []
    for font in FONTS:
        for suffix in ("", "-iso"):
            tiles.append(Image.open(OUT / f"sep-{font}{suffix}.png"))
    width = max(t.width for t in tiles)
    heights = [t.height for t in tiles]
    grid = Image.new("RGB", (width * 3, max(heights[0::2]) + max(heights[1::2])),
                     (250, 250, 251))
    for i, tile in enumerate(tiles):
        col, row = i % 3, i // 3
        grid.paste(tile, (col * width + (width - tile.width) // 2,
                          row * max(heights[0::2])))
    grid.save(OUT / "sep-all.png")
    print("总览 ->", OUT / "sep-all.png")


if __name__ == "__main__":
    main()
