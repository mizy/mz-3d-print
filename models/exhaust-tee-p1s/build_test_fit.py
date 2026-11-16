"""P1S 排风三通 · 穿墙试套（两瓣）—— 只回答一个问题：Φ54.2 能不能塞进 55–57 的墙洞。

和主件的关系：这是独立试件，不进正式模型。判据三条，缺一不算过：
  能进       沿实际装配路径合拢后推入到裙边贴墙
  能到位     裙边平贴墙面，单边翘起 ≤ 1mm（观测值，不当合格线）
  能取出     不借工具、不破坏地退出；只能进不能退说明已经轻微干涉

几何（打印姿态，+Z 朝上，热床 z=0）：
    z 0..22   穿墙段 Φ54.2 / 内孔 Φ49.4（壁 2.4），前端 1×45° 倒角
    z 22..24  模拟裙边 Φ68 × 2（真实裙边位置）
    z 24..32  手柄段 Φ54.2，外壁四个方位 0/90/180/270 各一道 0.6 深浅槽
    分型面    y=0，对开两瓣；不装卡钩（卡钩是独立变量），胶带/扎带临时捆住

用法：改 DIM 里的 od 就是另一个待验证外径，重跑即可。
"""
import json
import os
import sys

import manifold3d as mf
import numpy as np
import trimesh

DIM = {
    "od": 54.2,            # 待验证的穿墙段外径
    "id": 49.4,            # = od - 2*wall
    "wall": 2.4,
    "insert_len": 22.0,    # 墙上洞深，裙边贴墙时正好走完
    "flange_od": 68.0,     # 与主件一致的模拟裙边
    "flange_len": 2.0,
    "handle_len": 8.0,     # 裙边之外的手柄段
    "tip_chamfer": 1.0,    # 前端 1×45°
    "mark_depth": 0.6,     # 方位浅槽深度（不能影响外径判读）
    "mark_len": 4.0,
    "mark_z0": 26.0,
    "seg": 128,
}


def disc(r, h, z=0.0):
    return mf.CrossSection.circle(r, DIM["seg"]).extrude(h).translate([0, 0, z])


def box(x0, x1, y0, y1, z0, z1):
    return mf.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def inter(a, b):
    return a - (a - b)


def build_sleeve():
    d = DIM
    r_od = d["od"] / 2
    r_id = d["id"] / 2
    z_flange = d["insert_len"]
    z_end = z_flange + d["flange_len"] + d["handle_len"]
    tip = d["tip_chamfer"]

    # 相邻圆柱重叠 0.05：正好贴合会留下重合面，合并后变成非流形网格
    lap = 0.05
    outer = disc(r_od - tip, tip)                      # 前端倒角锥
    outer += disc(r_od, z_flange - tip, tip)           # 穿墙段
    outer += disc(d["flange_od"] / 2, d["flange_len"] + lap, z_flange - lap)
    outer += disc(r_od, z_end - z_flange - d["flange_len"] + lap,
                  z_flange + d["flange_len"] - lap)

    inner = disc(r_id, z_end + 2).translate([0, 0, -1])
    solid = outer - inner

    # 手柄段四个方位浅槽：只削外壁 0.6，不改变 Φ54.2 的判读基准
    for angle in (0.0, 90.0, 180.0, 270.0):
        notch = box(r_od - d["mark_depth"], r_od + 1.0, -1.2, 1.2,
                    d["mark_z0"], d["mark_z0"] + d["mark_len"])
        solid = solid - notch.rotate([0, 0, angle])
    return solid


def split_halves(solid):
    big = 400.0
    a = inter(solid, box(-big, big, 0.0, big, -big, big))
    b = inter(solid, box(-big, big, -big, 0.0, -big, big))
    return a, b


def to_trimesh(solid):
    m = solid.to_mesh()
    return trimesh.Trimesh(
        np.asarray(m.vert_properties, dtype=np.float64),
        np.asarray(m.vert_triangles if hasattr(m, "vert_triangles") else m.tri_verts,
                   dtype=np.int64),
        process=True,
    )


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    d = DIM
    solid = build_sleeve()
    a, b = split_halves(solid)
    bb = solid.bounding_box()
    z_end = d["insert_len"] + d["flange_len"] + d["handle_len"]

    rep = {
        "od_mm": d["od"],
        "id_mm": d["id"],
        "wall_mm": round((d["od"] - d["id"]) / 2, 2),
        "insert_len_mm": d["insert_len"],
        "total_len_mm": z_end,
        "flange_od_mm": d["flange_od"],
        "bbox_mm": [round(v, 2) for v in (np.array(bb[3:]) - np.array(bb[:3]))],
        "volume_cm3": round(solid.volume() / 1000, 2),
        "half_volume_cm3": round(a.volume() / 1000, 2),
        "watertight": bool(a.status() == mf.Error.NoError and b.status() == mf.Error.NoError),
        "interference_cm3": round(inter(a, b).volume() / 1000, 4),
    }
    print(json.dumps(rep, ensure_ascii=False, indent=2))

    fails = []
    if abs(rep["bbox_mm"][0] - d["flange_od"]) > 0.2:
        fails.append("X 向尺寸不等于裙边外径")
    if abs(rep["bbox_mm"][1] - d["flange_od"]) > 0.2:
        fails.append("Y 向尺寸不等于裙边外径")
    if abs(rep["bbox_mm"][2] - z_end) > 0.2:
        fails.append("总长不符")
    if rep["interference_cm3"] > 0.001:
        fails.append("两瓣干涉")
    if not rep["watertight"]:
        fails.append("网格不水密")
    if fails:
        print("CHECK FAIL:", fails)
        sys.exit(1)

    tri_a, tri_b = to_trimesh(a), to_trimesh(b)
    tri_a.export(os.path.join(here, "test-fit-half-A.stl"))
    tri_b.export(os.path.join(here, "test-fit-half-B.stl"))

    gap = 12.0
    off_b = (tri_a.bounds[1][0] + gap) - tri_b.bounds[0][0]
    tb = tri_b.copy()
    tb.apply_translation([off_b, 0, 0])
    scene = trimesh.Scene([tri_a, tb])
    scene.export(os.path.join(here, "tee-test-fit.3mf"))

    asm = tri_a + tri_b
    asm.export(os.path.join(here, "tee-test-fit-assembled.stl"))

    with open(os.path.join(here, "test-fit-report.json"), "w") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    print("wrote test-fit-half-A/B.stl, tee-test-fit.3mf, assembled stl, report")


if __name__ == "__main__":
    main()
