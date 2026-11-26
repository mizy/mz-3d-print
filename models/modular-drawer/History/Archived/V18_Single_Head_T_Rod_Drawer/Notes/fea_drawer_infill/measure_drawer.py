"""Measure the V18 drawer mesh: bbox, bottom thickness, wall thickness, inner span.

Input: drawer_printed.stl (print orientation, mm, bottom on Z=0).
Output: JSON to stdout plus a short human summary.
"""

"""Measure the V18 drawer mesh with ray casts: bottom thickness, wall thickness, inner span.

Input: drawer_printed.stl (print orientation, mm, bottom on Z=0).
Output: JSON to stdout.
"""

import json

import numpy as np
import trimesh


mesh = trimesh.load("drawer_printed.stl")
V = np.asarray(mesh.vertices)
F = np.asarray(mesh.faces)


def hit_list(origin, direction):
    """Return hit coordinates along the dominant ray axis."""
    d = np.asarray(direction, dtype=float)
    axis = int(np.argmax(np.abs(d)))
    return [round(float(origin[axis] + t * d[axis]), 3) for t in hits(origin, direction)]


def hits(origin, direction, eps=1e-9):
    """Sorted ray parameters t where the ray hits the mesh (numpy Moller-Trumbore)."""
    o = np.asarray(origin, dtype=float)
    d = np.asarray(direction, dtype=float)
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    e1, e2 = b - a, c - a
    h = np.cross(d, e2)
    det = np.einsum("ij,ij->i", e1, h)
    mask = np.abs(det) > eps
    inv = np.zeros_like(det)
    inv[mask] = 1.0 / det[mask]
    s = o - a
    u = np.einsum("ij,ij->i", s, h) * inv
    q = np.cross(s, e1)
    v = np.einsum("j,ij->i", d, q) * inv
    t = np.einsum("ij,ij->i", e2, q) * inv
    ok = mask & (u >= 0) & (u <= 1) & (v >= 0) & (u + v <= 1) & (t > 1e-6)
    return np.sort(t[ok])


result = {
    "watertight": bool(mesh.is_watertight),
    "volume_mm3": round(float(mesh.volume), 1),
    "surface_area_mm2": round(float(mesh.area), 1),
    "bbox_min": [round(float(v), 2) for v in mesh.bounds[0]],
    "bbox_max": [round(float(v), 2) for v in mesh.bounds[1]],
    "extents": [round(float(v), 2) for v in mesh.extents],
}

# Vertical ray through the middle: inner floor height and outer bottom.
for x, y in ((0.0, -20.0), (0.0, 40.0), (30.0, -60.0), (-40.0, 20.0)):
    zs = hit_list([x, y, 120.0], [0, 0, -1])
    result.setdefault("vertical_hits", []).append({"x": x, "y": y, "z": zs})

# Horizontal rays at several heights: wall thickness on X (left/right) and Y (front/back).
for z in (10.0, 40.0, 70.0):
    entry = {"z": z}
    for axis, name in ((0, "x"), (1, "y")):
        d = [0, 0, 0]
        d[axis] = 1
        o = [0.0, 0.0, z]
        entry[name] = hit_list(o, d)
    result.setdefault("horizontal_hits", []).append(entry)

# Floor top surface: cast a grid of vertical rays and collect the highest hit below 20mm.
top = []
for x in np.linspace(-65, 65, 11):
    for y in np.linspace(-110, 110, 15):
        zs = [z for z in hit_list([float(x), float(y), 50.0], [0, 0, -1]) if z < 20]
        if zs:
            top.append((min(zs), max(zs)))
if top:
    result["floor_top_min"] = round(min(t[0] for t in top), 3)
    result["floor_top_max"] = round(max(t[0] for t in top), 3)
    result["floor_bottom_max"] = round(max(t[1] for t in top), 3)

print(json.dumps(result, ensure_ascii=False, indent=2))
