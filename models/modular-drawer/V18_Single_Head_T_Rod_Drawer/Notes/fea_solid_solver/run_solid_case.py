#!/usr/bin/env python3
"""用 cad-surface-mesher 的 structural-solver 对单个闭合 STL 做线性静力实体求解。

不经过 serve_web 的自动网格（它取 bbox 最小边/2，薄壁件会粗到没法用），
直接调用 mesh_stl 指定网格尺寸，再走 solve.run_solve 的 T10 原生求解。

用法:
  python run_solid_case.py --stl bottom_panel.stl --mesh-size 2.0 \
      --fixes x_min,x_max,y_min,y_max --loads "z_min: fz=-19.6" \
      --out fea_solid_bottom_2kg
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

SOLVER_SCRIPTS = Path.home() / "projects/cad-surface-mesher/.agents/skills/structural-solver/scripts"
sys.path.insert(0, str(SOLVER_SCRIPTS))

from assembly import MATERIALS, Material  # noqa: E402
from mesh_tet import write_msh22  # noqa: E402
from solve import run_solve  # noqa: E402
from stl_volume import mesh_stl  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stl", type=Path, help="single closed STL (mutually exclusive with --geometry)")
    ap.add_argument("--geometry", help="parametric geometry, e.g. box:142.18,228.08,2.6 (mm)")
    ap.add_argument("--units", choices=["m", "mm"], default="mm")
    ap.add_argument("--mesh-size", type=float, required=True, help="unit = --units")
    ap.add_argument("--material", default="petg")
    ap.add_argument("--young-mpa", type=float, default=2000.0)
    ap.add_argument("--poisson", type=float, default=0.35)
    ap.add_argument("--fixes", default="x_min,x_max,y_min,y_max")
    ap.add_argument("--loads", default="z_min: fz=-19.6")
    ap.add_argument("--backend", choices=["auto", "gpu", "cpu"], default="cpu")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--mesh-only", action="store_true")
    args = ap.parse_args()

    MATERIALS[args.material] = Material(args.material, args.young_mpa * 1e6, args.poisson)

    t0 = time.time()
    args.out.mkdir(parents=True, exist_ok=True)
    counts = {"mesh_size": args.mesh_size, "units": args.units}
    msh = None
    if args.geometry:
        counts["geometry"] = args.geometry
    else:
        if not args.stl:
            raise SystemExit("need --stl or --geometry")
        mesh = mesh_stl(str(args.stl), args.units, args.mesh_size, order=2)
        msh = args.out / "volume.msh"
        write_msh22(mesh.nodes, mesh.elements, mesh.order, msh)
        counts.update({
            "nodes": int(len(mesh.nodes)),
            "elements_t10": int(len(mesh.elements)),
            "dof": int(3 * len(mesh.nodes)),
        })
    counts["mesh_seconds"] = round(time.time() - t0, 1)
    print(json.dumps(counts, ensure_ascii=False))
    if args.mesh_only:
        return

    fixes = [f.strip() for f in args.fixes.split(",") if f.strip()]
    loads = [l.strip() for l in args.loads.split(";") if l.strip()]
    t1 = time.time()
    result = run_solve(
        geometry=args.geometry,
        mesh_file=str(msh) if msh else None,
        units=args.units,
        material_name=args.material,
        order=2,
        mesh_size=args.mesh_size,
        fixes=fixes,
        loads=loads,
        output_dir=str(args.out),
        name=args.out.name,
        backend=args.backend,
    )
    elapsed = round(time.time() - t1, 1)

    report = result
    fields = report["results"]["field_summary"]
    summary = {
        "case": args.out.name,
        "elapsed_seconds": elapsed,
        "mesh": counts,
        "fixes": fixes,
        "loads": loads,
        "material": {"name": args.material, "E_mpa": args.young_mpa, "nu": args.poisson},
        "solver": report["runtime"]["solver"],
        "field_summary": fields,
        "gates": {k: v["passed"] for k, v in report["gates"].items()},
        "report_html": report["outputs"].get("report_html"),
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
