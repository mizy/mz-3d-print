#!/usr/bin/env python3
"""STEP -> Gmsh MSH 2.2 (T10) with explicit sizing, for structural-solver 的 --mesh 输入。

用法:
  python step_to_msh.py 04_Drawer.step --max 3.0 --min 1.0 --out drawer_3mm.msh
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import gmsh
import numpy as np


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", type=Path)
    ap.add_argument("--min", type=float, default=1.0, help="mm")
    ap.add_argument("--max", type=float, default=3.0, help="mm")
    ap.add_argument("--order", type=int, default=2, choices=[1, 2])
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    t0 = time.time()
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.model.occ.importShapes(str(args.step))
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber("Mesh.MeshSizeMin", args.min)
    gmsh.option.setNumber("Mesh.MeshSizeMax", args.max)
    gmsh.option.setNumber("Mesh.ElementOrder", args.order)
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    gmsh.option.setNumber("Mesh.HighOrderOptimize", 2)
    gmsh.model.mesh.generate(3)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    gmsh.write(str(args.out))
    node_tags, coords, _ = gmsh.model.mesh.getNodes()
    types, tags, _ = gmsh.model.mesh.getElements(3)
    tets10 = sum(len(t) for typ, t in zip(types, tags) if typ == 11)
    tets4 = sum(len(t) for typ, t in zip(types, tags) if typ == 4)
    gmsh.finalize()

    pts = np.asarray(coords).reshape(-1, 3)
    stats = {
        "step": str(args.step),
        "out": str(args.out),
        "size_min": args.min,
        "size_max": args.max,
        "order": args.order,
        "nodes": int(len(node_tags)),
        "tets_t10": int(tets10),
        "tets_t4": int(tets4),
        "bbox_mm": [pts.min(0).round(3).tolist(), pts.max(0).round(3).tolist()],
        "seconds": round(time.time() - t0, 1),
    }
    print(json.dumps(stats, ensure_ascii=False))
    args.out.with_suffix(".stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
