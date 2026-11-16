#!/usr/bin/env python3
"""「苗壮」分体立体字：两个字各自成一个独立打印件，不焊连体梁、不压字距。

主人 2026-10-31 的原话：「我这两个字可以分开的，不用一定连在一起」。

和 build_solid.py 的区别只有一处：不再把左右两字焊成一件。
每个字内部仍然要焊（字体里「艹」和「田」本来就是断开的，不焊就是散件），
但两字之间保持独立，可以分开打、分开摆、分开上色。

产物（每个字体 3 个文件 + 1 份报告）：
  miao-zhuang-sep-<font>-1miao.stl/.3mf     「苗」独立件
  miao-zhuang-sep-<font>-2zhuang.stl/.3mf   「壮」独立件
  miao-zhuang-sep-<font>-plate.3mf          两字排好的一盘（3MF 里是两个独立对象）
  miao-zhuang-sep-<font>-report.json        尺寸/体积/连通块/桥数/切片结果

跑法:
  uv run --offline --python 3.13 --with cadgen==0.7.26 python build_separate.py
"""
import json
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(Path.home() / ".cah-data/skills/shared/3d-print-ideas/scripts"))

from build123d import Align, Axis, Pos, Text, chamfer, extrude, export_stl  # noqa: E402

import build_solid as BS  # noqa: E402 —— 内部焊接/最近点桥只写一份
import check as C  # noqa: E402
import make_lithophane as HM  # noqa: E402
import model as M  # noqa: E402
import scad_build as SB  # noqa: E402
from build_mesh import stroke_stats  # noqa: E402
from check_model import read_stl  # noqa: E402

FONTS = [("weibei", "魏碑"), ("xingkai", "行楷"), ("baoli", "报隶")]
PLATE_GAP = 8.0          # 两字墨迹之间的净距（mm）
NAME_BY_CHAR = {"苗": "1miao", "壮": "2zhuang"}


def chamfer_top(body, amount):
    """只倒顶面周长里够长的边，字形尖角一倒就崩。"""
    edges = [e for e in body.edges().group_by(Axis.Z)[-1] if e.length > 2.0]
    for length in (amount, amount * 0.6, amount * 0.35):
        try:
            return chamfer(edges, length=length), round(length, 2)
        except Exception:
            continue
    return body, "跳过（字形尖角多，倒角会崩）"


def build_char(body, name):
    """单字收尾：贴床、X 居中（Y 保持原基线）、倒角，回来时是可直接导出的一件。"""
    bb = body.bounding_box()
    body = Pos(-(bb.min.X + bb.max.X) / 2, 0, -bb.min.Z) * body
    body, chamfered = chamfer_top(body, M.SOLID["chamfer"])
    bb = body.bounding_box()
    return body, {
        "name": name,
        "size": [round(bb.size.X, 2), round(bb.size.Y, 2), round(bb.size.Z, 2)],
        "volume_mm3": round(body.volume, 1),
        "solids": len(body.solids()),
        "chamfer": chamfered,
    }


def write_3mf_multi(path, objects, title):
    """多个独立对象写进一个 3MF（每个字一个 object，切片器里能分别选中/分色）。"""
    resources, items = [], []
    for oid, (name, faces) in enumerate(objects, 1):
        verts, inv = np.unique(faces.reshape(-1, 3), axis=0, return_inverse=True)
        tris = inv.reshape(-1, 3)
        v = "\n".join('<vertex x="%.9f" y="%.9f" z="%.9f"/>' % tuple(p) for p in verts)
        t = "\n".join('<triangle v1="%d" v2="%d" v3="%d"/>' % tuple(x) for x in tris)
        resources.append(
            '  <object id="%d" type="model" name="%s">\n'
            '   <mesh>\n    <vertices>\n%s\n    </vertices>\n'
            '    <triangles>\n%s\n    </triangles>\n   </mesh>\n  </object>'
            % (oid, escape(name), v, t))
        items.append('<item objectid="%d"/>' % oid)
    model = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
        ' <metadata name="Title">%s</metadata>\n'
        ' <metadata name="Application">miao-baicai build_separate.py</metadata>\n'
        ' <resources>\n%s\n </resources>\n'
        ' <build>%s</build>\n'
        '</model>\n' % (escape(title), "\n".join(resources), "".join(items)))
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("[Content_Types].xml", HM.THREE_MF_CONTENT_TYPES)
        z.writestr("_rels/.rels", HM.THREE_MF_RELS)
        z.writestr("3D/3dmodel.model", model)


def verify_3mf_multi(path, objects):
    fails = []
    ns = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None:
            return ["3MF 压缩包 CRC 校验失败"]
        root = ET.fromstring(z.read("3D/3dmodel.model"))
    if root.get("unit") != "millimeter":
        fails.append(f"3MF unit={root.get('unit')}")
    objs = root.findall(".//m:object", ns)
    if len(objs) != len(objects):
        fails.append(f"3MF 对象数 {len(objs)} != {len(objects)}")
    for obj, (name, faces) in zip(objs, objects):
        nv = len(obj.findall(".//m:vertex", ns))
        nt = len(obj.findall(".//m:triangle", ns))
        expect_v = len(np.unique(faces.reshape(-1, 3), axis=0))
        if nv != expect_v or nt != len(faces):
            fails.append(f"3MF {name} 顶点/面 {nv}/{nt} != {expect_v}/{len(faces)}")
    return fails


def slice_plate(plate, out):
    """真实切片：时间/克数/警告以 Bambu Studio 的返回为准。"""
    import subprocess
    cmd = [
        sys.executable,
        str(Path.home() / ".cah-data/skills/shared/bambu-studio-ai/scripts/slice.py"),
        str(plate), "--printer", "P1S", "--material", "PETG",
        "--layer-height", "0.16", "-o", str(out), "--json",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(plate.parent))
    if proc.returncode != 0:
        return {"ok": False, "error": (proc.stderr or proc.stdout)[-800:]}
    try:
        rep = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "error": "slice.py 没吐 JSON: " + proc.stdout[-400:]}
    return {"ok": True, **{k: rep.get(k) for k in
                           ("print_time_s", "filament_g", "warnings", "printer", "quality")}}


def main():
    p = M.load()
    BS.THICK[0] = M.SOLID["thick"]
    chars = list(p["text"])
    if len(chars) != 2:
        raise SystemExit(f"分体版只处理两个字，当前是 {p['text']!r}")

    for font_key, label in FONTS:
        txt = Text(p["text"], font_size=M.SOLID["font_size"], font_path=M.FONTS[font_key],
                   align=(Align.CENTER, Align.CENTER))
        letters = extrude(txt, amount=M.SOLID["thick"])
        left, right = BS.split_clusters(letters)

        bodies = []
        for parts, ch in ((left, chars[0]), (right, chars[1])):
            shape = parts[0]
            for s in parts[1:]:
                shape = shape + s
            shape, joins = BS.weld(shape)
            body, rep = build_char(shape, ch)
            rep.update({"bridges_internal": joins,
                        "stroke_mm": stroke_stats(ch, M.FONTS[font_key], M.SOLID["font_size"])})
            bodies.append((body, rep))

        # 排盘：保持各自原有基线，把右字平移到净距 PLATE_GAP，再整体居中。
        lb = bodies[0][0].bounding_box()
        rb = bodies[1][0].bounding_box()
        dx = lb.max.X + PLATE_GAP - rb.min.X
        right_body = Pos(dx, 0, 0) * bodies[1][0]
        all_min_x = min(lb.min.X, rb.min.X + dx)
        all_max_x = max(lb.max.X, rb.max.X + dx)
        shift = -(all_min_x + all_max_x) / 2
        plate_bodies = [Pos(shift, 0, 0) * bodies[0][0], Pos(shift, 0, 0) * right_body]

        objects = []
        for (body, rep), ch in zip(bodies, chars):
            stem = f"miao-zhuang-sep-{font_key}-{NAME_BY_CHAR[ch]}"
            stl, three = HERE / f"{stem}.stl", HERE / f"{stem}.3mf"
            export_stl(body, str(stl), tolerance=0.05, angular_tolerance=0.2)
            SB.stl_to_3mf(stl, three, stem)
            faces, meshrep = C.mesh(stem)
            overhang_fails, overhang_notes, _nn, _area = C.common_fails(stem, faces, p)
            rep["stl"], rep["3mf"] = stl.name, three.name
            rep["mesh_failures"] = meshrep.get("failures", []) + overhang_fails
            rep["print_notes"] = overhang_notes
            objects.append((stem, faces))

        plate_name = f"miao-zhuang-sep-{font_key}-plate"
        plate_faces = []
        for body, (stem, _faces) in zip(plate_bodies, objects):
            tmp = HERE / f"_{stem}-plate.stl"
            export_stl(body, str(tmp), tolerance=0.05, angular_tolerance=0.2)
            _fmt, _n, faces, _normals = read_stl(tmp)
            plate_faces.append((stem, faces))
            tmp.unlink()
        plate_3mf = HERE / f"{plate_name}.3mf"
        write_3mf_multi(plate_3mf, [(name, f) for name, f in plate_faces], plate_name)
        pb = [b.bounding_box() for b in plate_bodies]
        plate_bbox = {
            "size": [round(max(b.max.X for b in pb) - min(b.min.X for b in pb), 2),
                     round(max(b.max.Y for b in pb) - min(b.min.Y for b in pb), 2),
                     round(max(b.max.Z for b in pb), 2)],
            "min_corner": [round(min(b.min.X for b in pb), 2),
                           round(min(b.min.Y for b in pb), 2),
                           round(min(b.min.Z for b in pb), 2)],
        }
        report = {
            "font": font_key, "label": label, "kind": "分体立体字",
            "text": p["text"], "gap_mm": PLATE_GAP,
            "chars": [rep for _b, rep in bodies],
            "plate": {"3mf": plate_3mf.name, **plate_bbox},
            "plate_3mf_failures": verify_3mf_multi(
                plate_3mf, [(name, f) for name, f in plate_faces]),
        }
        report["slice"] = slice_plate(plate_3mf, HERE / f"{plate_name}-sliced.3mf")
        (HERE / f"{plate_name}-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2))
        print(f"{font_key}: " + ", ".join(
            f"{c['name']} {c['size'][0]}x{c['size'][1]}x{c['size'][2]} "
            f"solids={c['solids']} bridges={c['bridges_internal']} "
            f"fail={len(c['mesh_failures'])}" for c in report["chars"]))
        print(f"  plate {plate_bbox['size']} mm, 3mf_fail={len(report['plate_3mf_failures'])}, "
              f"slice={report['slice']}")


if __name__ == "__main__":
    main()
