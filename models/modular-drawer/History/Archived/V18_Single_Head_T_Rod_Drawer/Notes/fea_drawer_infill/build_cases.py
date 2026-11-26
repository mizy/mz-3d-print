"""Build the equivalent bottom-panel case set for the V18 H100 drawer.

Print setup (from the released 3MF, print_settings_id
`0.20mm-减少实心稀疏填充省料` with project overrides):
  layer 0.2, line 0.42, 2 walls, 2 top + 2 bottom shells, 10% gyroid, PETG.

The drawer floor is 2.6 mm thick: 0.4 mm solid bottom skin + 1.8 mm 10% gyroid
core + 0.4 mm solid inner skin.  Its equivalent bending stiffness is computed
from the transformed section, then fed to fea_plate.py through
--stiffness-factor.

Outputs: bottom_panel.stl, loads_bottom.json, section.json
"""

import json

import numpy as np
import trimesh

TOTAL = 2.6
SKIN = 0.4
CORE = TOTAL - 2 * SKIN
E_SOLID = 2000.0  # PETG
RHO = 1.27  # g/cm3
SPAN_X = 142.18  # inner cavity, measured from the mesh
SPAN_Y = 228.08
AREA = SPAN_X * SPAN_Y

# Gyroid relative modulus at 10% volume fraction.  Literature range 0.05-0.15;
# take the middle and also report the bounds.
CORE_RATIOS = {"low": 0.05, "mid": 0.10, "high": 0.15}


def section(t_total=TOTAL, skin=SKIN, ratios=CORE_RATIOS):
    core = t_total - 2 * skin
    z_skin = core / 2 + skin / 2
    out = {}
    for name, k in ratios.items():
        e_core = E_SOLID * k
        d = (
            2 * E_SOLID * (skin**3 / 12 + skin * z_skin**2)
            + e_core * core**3 / 12
        )
        e_eff = 12 * d / t_total**3
        out[name] = {
            "core_modulus_ratio": k,
            "D_Nmm": round(d, 1),
            "E_eff_MPa": round(e_eff, 1),
            "stiffness_factor": round(e_eff / E_SOLID, 3),
        }
    out["geometry"] = {
        "total_mm": t_total,
        "skin_mm": skin,
        "core_mm": round(core, 2),
        "skin_center_offset_mm": round(z_skin, 2),
    }
    return out


def make_plate(path, sx, sy, t):
    plate = trimesh.creation.box(extents=[sx, sy, t])
    plate.export(path)


def grid_loads(x0, x1, y0, y1, total_n, nx, ny):
    """Approximate a uniform pressure with a grid of equal point loads.

    fea_plate.py's area-load path is broken against scikit-fem >= 9
    (`asm(..., elements=...)` API change), so the pressure is lumped onto a
    grid of nodes instead.  At 2 mm mesh the error is small.
    """
    loads = []
    each = total_n / (nx * ny)
    for x in np.linspace(x0, x1, nx):
        for y in np.linspace(y0, y1, ny):
            loads.append({"type": "point", "at": [round(float(x), 3), round(float(y), 3)], "force_n": each})
    return loads


def main():
    sec = section()
    json.dump(sec, open("section.json", "w"), indent=2)
    make_plate("bottom_panel.stl", SPAN_X, SPAN_Y, TOTAL)

    edge = [
        {"type": "line", "axis": "x", "at": -SPAN_X / 2},
        {"type": "line", "axis": "x", "at": SPAN_X / 2},
        {"type": "line", "axis": "y", "at": -SPAN_Y / 2},
        {"type": "line", "axis": "y", "at": SPAN_Y / 2},
    ]
    clamped = [dict(e, clamp=True) for e in edge]
    full = [[-SPAN_X / 2, -SPAN_Y / 2], [SPAN_X / 2, SPAN_Y / 2]]

    full_loads = {
        kg: grid_loads(-SPAN_X / 2, SPAN_X / 2, -SPAN_Y / 2, SPAN_Y / 2, kg * 9.80665, 15, 25)
        for kg in (0.5, 1.0, 2.0, 3.0)
    }
    cases = []
    for kg in (0.5, 1.0, 2.0, 3.0):
        cases.append({
            "name": f"bottom_{kg:g}kg_simple",
            "gravity": False,
            "tilt_deg": 90,
            "supports": edge,
            "loads": full_loads[kg],
        })
    for kg in (1.0, 2.0):
        cases.append({
            "name": f"bottom_{kg:g}kg_clamped",
            "gravity": False,
            "tilt_deg": 90,
            "supports": clamped,
            "loads": full_loads[kg],
        })
    # A 2 kg item concentrated in a small 40x40 patch at the centre.
    cases.append({
        "name": "bottom_2kg_40mm_patch_simple",
        "gravity": False,
        "tilt_deg": 90,
        "supports": edge,
        "loads": grid_loads(-20, 20, -20, 20, 2 * 9.80665, 7, 7),
    })
    # Single 20 N point at the centre (worst local case).
    cases.append({
        "name": "bottom_20N_point_simple",
        "gravity": False,
        "tilt_deg": 90,
        "supports": edge,
        "loads": [{"type": "point", "at": [0, 0], "force_n": 20.0}],
    })

    json.dump({"cases": cases}, open("loads_bottom.json", "w"), indent=2)
    print(json.dumps(sec, indent=2))
    print("cases:", [c["name"] for c in cases])


if __name__ == "__main__":
    main()
