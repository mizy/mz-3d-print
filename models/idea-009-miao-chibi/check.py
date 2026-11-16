#!/usr/bin/env python3
"""idea-009 苗白菜 Q 版手办自检：把「能不能打」逐条算出来，全过才有意义开打。

只读 model.scad / model.py / 同目录 STL+3MF，不改任何文件。用法: python3 check.py

  A 参数对账：STL 包围盒 = 参数推出来的期望包围盒（差 > 1.5mm 就是画的和算的不是一份）
  B 部件连通：部件表里每件必须与上游件在 z 上重叠 >= 1mm（否则是悬浮件）
  C 单一实体：STL 面片按共享边连起来只允许 1 个连通块（头发/叶子掉件会在这里现形）
  D 打印机容积：外廓 <= 250x250x250（主人给的硬上限）
  E 最薄件：白菜叶 >= 1.6mm（0.4 喷嘴 4 条线）
  F 悬垂面：法线朝下且比 45° 更陡的面积占比 < 10%（贴床那一面不算）
  G 材料/时长：调 cost.mjs 的 shell 口径，质量不得超 150g（140mm 单件的常识上限）
  H 水密/格式：调 check_model.py 复核水密、绕序、体积、STL<->3MF 一致
  I 左右镜像：顶点集合在 x -> -x 下必须完全相同（叶子/眼睛有没有歪）
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import model as M  # noqa: E402

SCRIPTS = Path.home() / ".cah-data/skills/shared/3d-print-ideas/scripts"
sys.path.insert(0, str(SCRIPTS))
from check_model import read_stl  # noqa: E402

STL = HERE / "miao-chibi.stl"
THREE = HERE / "miao-chibi.3mf"
PRINTER_MAX = 250.0
MIN_OVERLAP = 1.0
MIN_FEATURE = 1.6
STEEP_NZ = -0.707
OVERHANG_BUDGET = 0.10
MAX_PRINT_G = 150.0

fails, total = [], 0


def check(ok, label, detail):
    global total
    total += 1
    print(("  ok  " if ok else " FAIL ") + label + "  " + detail)
    if not ok:
        fails.append(label)


def face_components(tris):
    """面片按共享边并查集：返回连通块个数（顶点按 1e-4 取整当同一顶点）。"""
    key, ids = {}, np.zeros(tris.shape[:2], dtype=np.int64)
    for fi in range(tris.shape[0]):
        for vi in range(3):
            ids[fi, vi] = key.setdefault(tuple(np.round(tris[fi, vi], 4)), len(key))
    parent = list(range(tris.shape[0]))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    owner = {}
    for fi in range(tris.shape[0]):
        a, b, c = ids[fi]
        for e in ((min(a, b), max(a, b)), (min(b, c), max(b, c)), (min(c, a), max(c, a))):
            other = owner.setdefault(e, fi)
            if other != fi:
                ra, rb = find(fi), find(other)
                if ra != rb:
                    parent[ra] = rb
    return len({find(i) for i in range(tris.shape[0])})


if not STL.exists():
    raise SystemExit(f"没有 {STL.name}，先跑 scad_build.py")

fmt, n, tris, _ = read_stl(STL)
v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
cr = np.cross(v1 - v0, v2 - v0)
nrm = np.linalg.norm(cr, axis=1)
area = 0.5 * nrm
nz = np.divide(cr[:, 2], nrm, out=np.zeros(n), where=nrm > 0)
lo, hi = tris[:, :, 2].min(axis=1), tris[:, :, 2].max(axis=1)
bbox = tris.reshape(-1, 3).max(axis=0) - tris.reshape(-1, 3).min(axis=0)
zmin = tris[:, :, 2].min()
vol = abs(np.einsum("ij,ij->i", v0, np.cross(v1, v2)).sum() / 6)

print(f"输入 {STL.name}（{fmt}，{n} 面）+ {THREE.name}")
print(f"实测 包围盒 [{bbox[0]:.2f} {bbox[1]:.2f} {bbox[2]:.2f}] mm  体积 {vol/1000:.2f} cm³  表面积 {area.sum()/100:.1f} cm²\n")

print("A 参数对账（STL 包围盒 vs model.py 期望）")
for ax, name, want in ((0, "X", M.BBOX_X), (1, "Y", M.BBOX_Y), (2, "Z", M.BBOX_Z)):
    check(abs(bbox[ax] - want) <= 1.5, f"{name} 外廓 = 期望", f"实测 {bbox[ax]:.2f} / 期望 {want:.2f} mm")
check(abs(zmin) <= 0.01, "底面贴床 z=0", f"最低点 z={zmin:.4f}")

print("\nB 部件连通（z 区间必须与上游件重叠 >= 1mm）")
for name, z0, z1, up in M.PARTS:
    if up is None:
        check(z0 <= 0.01, f"{name} 从 z=0 起", f"z {z0:.2f}..{z1:.2f}")
        continue
    uz0, uz1 = next((p[1], p[2]) for p in M.PARTS if p[0] == up)
    ov = min(z1, uz1) - max(z0, uz0)
    check(ov >= MIN_OVERLAP, f"{name} 与{up}重叠 {ov:.2f}mm", f"z {z0:.2f}..{z1:.2f} vs {up} {uz0:.2f}..{uz1:.2f}")

print("\nC 单一实体")
comp = face_components(tris)
check(comp == 1, "连通块 = 1", f"实测 {comp} 块（>1 说明有悬浮/掉件）")

print("\nD 打印机容积（<= 250x250x250）")
for ax, name, want in ((0, "X", M.BBOX_X), (1, "Y", M.BBOX_Y), (2, "Z", M.BBOX_Z)):
    check(bbox[ax] <= PRINTER_MAX, f"{name} <= {PRINTER_MAX:.0f}", f"{bbox[ax]:.2f} mm")

print("\nE 最薄实体件")
check(M.MIN_FEATURE_MM >= MIN_FEATURE, "白菜叶厚度 >= 1.6mm", f"{M.MIN_FEATURE_MM:.2f} mm（0.4 喷嘴约 {M.MIN_FEATURE_MM/0.42:.1f} 条线）")

print("\nF 悬垂面（法线朝下且陡于 45°，贴床面不计）")
steep = (nz < STEEP_NZ) & (lo > 0.05)
frac = area[steep].sum() / area.sum()
check(frac < OVERHANG_BUDGET, f"陡下向面积占比 < {OVERHANG_BUDGET:.0%}", f"实测 {frac:.2%}（{area[steep].sum()/100:.1f} cm²）")
band = np.zeros(8)
for i in np.where(steep)[0]:
    band[min(7, int(lo[i] // 20))] += area[i]
print("      按高度分布: " + "  ".join(f"{i*20}-{i*20+20}mm {band[i]/100:.1f}cm²" for i in range(8) if band[i] > 1))

print("\nG 材料与时长（cost.mjs shell 口径，PLA）")
r = subprocess.run(["node", str(SCRIPTS / "cost.mjs"), str(STL), "--material", "PLA", "--json"],
                   capture_output=True, text=True)
cj = json.loads(r.stdout)["totals"]
check(cj["massPrintG"] <= MAX_PRINT_G, f"预计用料 <= {MAX_PRINT_G:.0f}g",
      f"{cj['massPrintG']:.1f} g / 满打 {cj['massSolidG']:.1f} g，约 {cj['printHours']:.1f} h，{cj['totalCost']:.2f} 元")
check(cj["massPrintG"] > 0, "cost.mjs 出数", f"shell 口径 wallLoops={json.loads(r.stdout)['params']['wallLoops']} infill={json.loads(r.stdout)['params']['infillPct']}%")

print("\nH 水密 / 格式（check_model.py）")
r = subprocess.run(["python3", str(SCRIPTS / "check_model.py"), str(STL), "--3mf", str(THREE), "--material", "PLA"],
                   capture_output=True, text=True)
for line in r.stdout.strip().splitlines():
    print("      " + line.strip())
check(r.returncode == 0 and "全过" in r.stdout, "check_model 全过", f"exit={r.returncode}")

print("\nI 左右镜像对称（顶点级，0.001mm 网格；面集不比，CGAL 三角化对角线不保证对称）")
q = np.rint(tris.reshape(-1, 3) * 1000).astype(np.int64)
vs = {tuple(r) for r in q}
qm = q.copy()
qm[:, 0] *= -1
vsm = {tuple(r) for r in qm}
check(vs == vsm, "顶点集合镜像一致", f"{len(vs)} 顶点，不对称 {len(vs ^ vsm)}")

print(f"\n{'PASS' if not fails else 'FAIL'}  {total - len(fails)}/{total} 项通过"
      + ("" if not fails else "  挂: " + "; ".join(fails)))
sys.exit(0 if not fails else 1)
