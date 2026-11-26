"""Front-wall check: 1.0 mm PETG wall, 142.18 x 83.4, fixed at bottom and sides.

Load case: pulling the loaded drawer by the front panel, 30 N / 50 N at the
middle of the top rim (normal to the wall).  The wall is printed vertically with
2 perimeters, so its effective modulus is close to solid (0.84 of the 1.0 mm
section is wall).
"""

import json

import numpy as np
import trimesh

W, H, T = 142.18, 83.4, 1.0
SIDE = 0.84  # factor for a 1 mm wall printed with 2 x 0.42 perimeters

plate = trimesh.creation.box(extents=[W, H, T])
plate.export("front_wall.stl")

supports = [
    {"type": "line", "axis": "x", "at": -W / 2, "clamp": True},
    {"type": "line", "axis": "x", "at": W / 2, "clamp": True},
    {"type": "line", "axis": "y", "at": -H / 2, "clamp": True},
]

def pull_spread(force, spread, n=15):
    y = H / 2 - 2.0
    return [
        {"type": "point", "at": [round(float(x), 3), y], "force_n": force / n}
        for x in np.linspace(-spread / 2, spread / 2, n)
    ]


cases = []
# A hand pulls about 60-80 mm of the rim, not a mathematical point.
for force in (30.0, 50.0):
    cases.append({
        "name": f"front_pull_{force:g}N_60mm",
        "gravity": False,
        "tilt_deg": 90,
        "supports": supports,
        "loads": pull_spread(force, 60.0),
    })
    cases.append({
        "name": f"front_pull_{force:g}N_80mm",
        "gravity": False,
        "tilt_deg": 90,
        "supports": supports,
        "loads": pull_spread(force, 80.0),
    })
# Point pull kept as a hard upper bound.
cases.append({
    "name": "front_pull_30N_point",
    "gravity": False,
    "tilt_deg": 90,
    "supports": supports,
    "loads": [{"type": "point", "at": [0, H / 2 - 1.0], "force_n": 30.0}],
})

json.dump({"cases": cases}, open("loads_wall.json", "w"), indent=2)
json.dump({"wall": {"width_mm": W, "height_mm": H, "thickness_mm": T, "stiffness_factor": SIDE}},
          open("wall_section.json", "w"), indent=2)
print("wall cases ready")
