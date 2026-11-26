"""Render normal vs windowed drawer side by side for a visual weight check."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE = Path(__file__).resolve().parent
NORMAL = HERE.parent / "fea_drawer_infill" / "drawer_printed.stl"
WINDOWED = HERE / "drawer_windowed.stl"


def load_stl(path):
    m = trimesh.load(path)
    m.apply_translation([-m.centroid[0], -m.centroid[1], -m.bounds[0][2]])
    return m


def draw(ax, mesh, title):
    tris = mesh.vertices[mesh.faces]
    normals = mesh.face_normals
    light = np.array([0.4, -0.6, 0.7])
    light = light / np.linalg.norm(light)
    shade = np.clip(normals @ light, 0, 1) * 0.7 + 0.3
    colors = np.stack([shade * 0.75, shade * 0.78, shade * 0.8, np.ones_like(shade)], axis=1)
    pc = Poly3DCollection(tris, facecolors=colors, edgecolors="none")
    ax.add_collection3d(pc)
    ax.set_xlim(-80, 80)
    ax.set_ylim(-120, 120)
    ax.set_zlim(0, 95)
    ax.set_box_aspect((160, 240, 95))
    ax.view_init(elev=22, azim=-58)
    ax.set_title(title, fontsize=11)
    ax.set_axis_off()


fig = plt.figure(figsize=(11, 6), dpi=150)
ax1 = fig.add_subplot(1, 2, 1, projection="3d")
ax2 = fig.add_subplot(1, 2, 2, projection="3d")
draw(ax1, load_stl(NORMAL), "V18 drawer — original (123.0 g)")
draw(ax2, load_stl(WINDOWED), "windowed trial (111.4 g)")
fig.tight_layout()
out = HERE / "compare_windowed.png"
fig.savefig(out)
print(out)
