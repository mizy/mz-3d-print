#!/usr/bin/env python3
"""Write ARCHIVE.json: every archived file, size, SHA-256, and STL dimensions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import trimesh

ROOT = Path(__file__).resolve().parent.parent


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.name == "ARCHIVE.json" or path.name == ".DS_Store":
            continue
        item = {
            "path": str(path.relative_to(ROOT)),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        if path.suffix.lower() == ".stl":
            mesh = trimesh.load(path, force="mesh")
            bounds = mesh.bounds
            item["bbox_mm"] = [round(float(bounds[1][i] - bounds[0][i]), 3) for i in range(3)]
            item["faces"] = int(len(mesh.faces))
        files.append(item)

    manifest = {
        "design": "idea-028 云朵托架 · SKADIS 洞洞板手办搁板",
        "original": True,
        "printed_at": "2026-11-07",
        "archived_at": "2026-11-09",
        "files": files,
    }
    out = ROOT / "ARCHIVE.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {out} ({len(files)} files)")


if __name__ == "__main__":
    main()
