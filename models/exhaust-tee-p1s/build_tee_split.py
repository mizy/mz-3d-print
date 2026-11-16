"""P1S 排风三通 V3：Φ60 墙口 / Φ60 软管口 / Φ40 侧支口，对开两瓣 + 搭接止口 + 卡钩。

主人 2026-11-01 三句要求：
  1. 三个口：6cm / 4cm / 6cm
  2. 能拆成两半、并且能卡上（不是三个筒糊一起）
  3. Φ40 小口要像树枝一样从侧边长出来，不能顶在头上

坐标系（本身就是打印姿态，+Z 朝上，热床 z=0）：
    z 0..22   穿墙锥管 Φ57.8 → Φ59.4（按 Φ60 洞，单边 0.3–1.1 间隙），内孔 Φ51.4
    z 22..24  压墙裙边 Φ68（压在墙洞外沿，把洞边整体盖住，打泡棉胶）
    z 24..29.8  裙边 45° 收坡回 Φ59.8（消除 5.8mm 水平悬垂，不用支撑）
    z 29.8..90  主管 Φ59.8 / 内孔 Φ55
    z 90..116 软管插口 Φ59.8（Φ60 软管套外面，卡箍锁）
    分型面   y=0（XZ 平面；主轴与支口轴线都在这个面内 → 支口被完整剖开）
    支口     主轴 z=46 处、与主轴成 60° 斜出，外径 Φ47 / 内孔 Φ42

分型面竖直 + 主轴竖直 = 两瓣都只有竖直墙，免支撑。
所有尺寸只在 DIM / LATCHES / LATCH 里改，重跑本脚本；main() 判据不过就退出码 1。
"""
import json
import math
import os
import sys

import manifold3d as mf
import numpy as np
import trimesh

DIM = {
    "bore": 55.0,          # 主通道内径
    "wall": 2.4,           # 主管壁厚 → 外径 59.8
    "insert_od_tip": 57.8,   # 穿墙短管前端外径：按 Φ60 洞取，单边留 0.5 便于导入
    "insert_od_face": 59.4,  # 穿墙短管靠墙面外径：Φ60 洞单边 0.3 间隙
    "insert_id": 51.4,       # 穿墙段内径（比主管小 3.6，换 2.5 壁厚）
    "insert_len": 22.0,      # 穿墙段长度；z=22 就是墙面
    "wall_flange_od": 68.0,  # 压墙裙边外径：盖住 Φ55–57 洞边，单边多出 5.5–6.5
    "wall_flange_len": 2.0,  # 裙边厚度（贴墙的密封面，打泡棉胶）
    "skirt_draft": 5.8,      # 裙边室内侧 45° 收坡长度（径向多出多少就收多少，免支撑）
    "pipe_d": 30.0,          # 空调管外径（照片里那根）
    "pipe_notch_clear": 0.8, # 卡口单边让量 → 卡口直径 = pipe_d + clear
    "pipe_ear_x": 48.0,      # 管中心到主轴的距离（卡口靠这个定位）
    "pipe_ear_r": 20.0,      # 侧耳外半径
    "barrel_len": 60.0,
    "spigot_len": 26.0,
    "branch_bore": 42.0,   # Φ40 线束 + 1mm/边
    "branch_wall": 2.5,
    "branch_angle": 60.0,  # 与主轴夹角；打印时= 水平上翘 30°，最差悬垂 30°
    "branch_root_z": 46.0,
    "branch_len": 58.0,
    "lap_depth": 1.2,      # 搭接止口插入深度
    "lap_clear": 0.25,     # 止口单边间隙（0.15 打完常卡，按评审放大）
    "fit_clear": 0.25,     # 卡钩与凸块间隙
    "seg": 128,
}

# 卡钩位置（z 区间）。+X 缝要让开支口根部，所以只有下方一个。
LATCHES = [
    {"seam": +1, "z0": 28.0, "z1": 38.0},
    {"seam": -1, "z0": 32.0, "z1": 44.0},
    {"seam": -1, "z0": 62.0, "z1": 74.0},
]

LATCH = {
    "tab_out": 4.9,      # 钩爪外表面高出 OD 的量
    "tab_thick": 2.25,   # 钩爪径向厚度
    "hook_up": 0.55,     # 钩齿内表面离 OD
    "bump_h": 2.4,       # 对方凸块高度
    "s_root": (12.0, 16.0),
    "s_tab": (13.0, -13.0),
    "s_ramp": -9.6,      # 导入斜面下端点（弧长）
    "s_hook": -7.3,      # 止退面
    "s_bump": (-6.8, -2.5),
}


# ---------- 几何小工具 ----------

def disc(r, h, z=0.0, seg=None):
    return mf.CrossSection.circle(r, seg or DIM["seg"]).extrude(h).translate([0, 0, z])


def box(x0, x1, y0, y1, z0, z1):
    return mf.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def inter(a, b):
    return a - (a - b)


def rotated_tube(z0, length, r, seg=None):
    """沿 +Z 建管，绕 Y 转 branch_angle 度 → 主轴在 XZ 平面内的斜支口。"""
    return (
        mf.CrossSection.circle(r, seg or DIM["seg"])
        .extrude(length)
        .rotate([0, DIM["branch_angle"], 0])
        .translate([0, 0, z0])
    )


def polar_solid(vertices, r_ref, z0, z1):
    """(弧长 s, 半径 r) 顶点折线 → 沿 Z 挤出的柱状件。s 用 r_ref 处弧长换算角度。

    manifold 的 CrossSection 对绕向挑食：被拒的轮廓会静默变成空集（num_contour=0），
    所以两个绕向都试，并用鞋带面积核对，防止出「体积几乎为 0」的假件。
    """
    # 长边必须打断：极坐标下的直边映射到 XY 是一条弦，弦会切进内侧造成自交
    verts = []
    for i, (s0, r0) in enumerate(vertices):
        s1, r1 = vertices[(i + 1) % len(vertices)]
        n = max(1, int(math.ceil(math.hypot(s1 - s0, r1 - r0) / 0.6)))
        for k in range(n):
            t = k / n
            verts.append((s0 + (s1 - s0) * t, r0 + (r1 - r0) * t))

    pts = []
    for (s, r) in verts:
        a = s / r_ref
        pts.append((r * math.cos(a), r * math.sin(a)))

    n = len(pts)
    shoelace = 0.5 * abs(sum(pts[i][0] * pts[(i + 1) % n][1]
                             - pts[(i + 1) % n][0] * pts[i][1] for i in range(n)))
    for cand in (pts, list(reversed(pts))):
        cs = mf.CrossSection([cand])
        if cs.num_contour() == 1 and abs(cs.area() - shoelace) < 0.05 * shoelace + 0.5:
            return cs.extrude(z1 - z0).translate([0, 0, z0])
    raise ValueError(f"轮廓被拒或面积不符: {vertices}")


def mirror_x(solid):
    return solid.mirror([1, 0, 0])


# ---------- 主体 ----------

def frustum(r_bottom, r_top, z0, height):
    """真锥面（manifold 原生圆台）。比叠圆盘好在没有水平台阶，不会凭空造出悬垂。"""
    return mf.Manifold.cylinder(height, r_bottom, r_top, DIM["seg"]).translate([0, 0, z0])


def build_solid(dim=DIM):
    r_od = (dim["bore"] + 2 * dim["wall"]) / 2
    r_bore = dim["bore"] / 2
    r_tip = dim["insert_od_tip"] / 2
    r_face = dim["insert_od_face"] / 2
    r_ins_i = dim["insert_id"] / 2
    r_flange = dim["wall_flange_od"] / 2
    z1 = dim["insert_len"]
    z_f = z1 + dim["wall_flange_len"]
    z_d = z_f + dim["skirt_draft"]
    z3 = z_d + dim["barrel_len"]
    z4 = z3 + dim["spigot_len"]
    lap = 0.05

    outer = frustum(r_tip - 1.0, r_face, 0.0, z1 + lap)   # 穿墙锥段 Φ52.6 → Φ56.4
    outer += disc(r_flange, dim["wall_flange_len"] + 2 * lap, z1 - lap)   # 压墙裙边 Φ68
    outer += frustum(r_flange, r_od, z_f - lap, dim["skirt_draft"] + 2 * lap)  # 45° 收坡
    outer += disc(r_od, dim["barrel_len"] + lap, z_d - lap)           # 主管 Φ59.8
    outer += disc(r_od, dim["spigot_len"] - 1.2 + lap, z3 - lap)
    outer += disc(r_od - 1.2, 0.6, z3 + dim["spigot_len"] - 1.2)   # 端头 45° 倒角
    outer += disc(r_od - 2.0, 0.6, z3 + dim["spigot_len"] - 0.6)

    flare = r_bore - r_ins_i
    inner = disc(r_ins_i, z1)
    inner += disc(r_ins_i + flare * 0.25, 0.5, z1)
    inner += disc(r_ins_i + flare * 0.75, 0.5, z1 + 0.5)
    inner += disc(r_bore, z4 - z1 - 1.0, z1 + 1.0)
    inner += disc(r_bore + 0.9, 1.0, z4 - 1.0)

    branch_od = (dim["branch_bore"] + 2 * dim["branch_wall"]) / 2
    branch_bore = dim["branch_bore"] / 2

    stub = rotated_tube(dim["branch_root_z"], dim["branch_len"], branch_od)
    stub += rotated_tube(dim["branch_root_z"], dim["branch_len"] - 1.2, branch_od - 1.0)
    # 支口根部补强 + 下侧撑料：60° 斜出的支口下表面和主管之间本来是一块开口楔形，
    # 看着像缺壁，受力也在那儿集中。用一圈锥面填进去，底部切平在墙面之上（z=24），
    # 不让它戳出压墙面。
    collar = (
        mf.Manifold.cylinder(16.0, branch_od + 2.6, branch_od, dim["seg"])
        .rotate([0, dim["branch_angle"], 0])
        .translate([0, 0, dim["branch_root_z"]])
    )
    collar = collar - box(-400, 400, -400, 400, -400, z_f)
    stub += collar
    stub_bore = rotated_tube(dim["branch_root_z"] - 6.0, dim["branch_len"] + 8.0, branch_bore)

    solid = (outer + stub) - inner - stub_bore

    # 空调管半圆卡口：法兰 +X 侧长一个耳朵，耳上开一个通孔当卡口。
    # 分型面正好过管心，所以两瓣各占半个圆，合拢时把它夹住，不用穿管。
    ear_x = dim["pipe_ear_x"]
    notch_r = (dim["pipe_d"] + dim["pipe_notch_clear"]) / 2
    ear = mf.Manifold.cylinder(
        dim["wall_flange_len"], dim["pipe_ear_r"], dim["pipe_ear_r"], dim["seg"]
    ).translate([ear_x, 0, z1])
    cradle = mf.Manifold.cylinder(
        dim["wall_flange_len"] + 4.0, notch_r, notch_r, dim["seg"]
    ).translate([ear_x, 0, z1 - 2.0])
    return (solid + ear) - cradle


# ---------- 分瓣：搭接止口 ----------

def split_halves(solid, dim=DIM):
    big = 400.0
    # 用原生半空间切分，不要用 inter(solid, box)：后者等于 solid-(solid-box)，
    # 大件上会切出几十块碎片外壳。
    a_side, b_side = solid.split_by_plane([0.0, 1.0, 0.0], 0.0)

    d, c = dim["lap_depth"], dim["lap_clear"]
    # +X 缝 A 出舌、-X 缝 B 出舌：交错，合上自动对位，接缝变成 Z 形折道
    tongue_r = inter(solid, box(25.0, big, -d, 0.0, -big, big))
    tongue_l = inter(solid, box(-big, -25.0, 0.0, d, -big, big))
    groove_r = inter(solid, box(25.0, big, -(d + c), c, -big, big))
    groove_l = inter(solid, box(-big, -25.0, -c, d + c, -big, big))

    a = (a_side + tongue_r) - groove_l
    b = (b_side + tongue_l) - groove_r
    return a, b


# ---------- 卡钩 ----------

def latch_polys(dim=DIM):
    r_od = (dim["bore"] + 2 * dim["wall"]) / 2
    o = LATCH["tab_out"]
    hook_up = LATCH["hook_up"]
    bump_h = LATCH["bump_h"]
    tab_in = r_od + bump_h + dim["fit_clear"]
    sa, sb = LATCH["s_tab"]
    root_a, root_b = LATCH["s_root"]
    s_ramp, s_hook = LATCH["s_ramp"], LATCH["s_hook"]
    b0, b1 = LATCH["s_bump"]

    hook = [
        (sa, r_od + o),
        (sb, r_od + o),
        (sb, r_od + o - 0.8),          # 端头小立面
        (s_ramp, r_od + hook_up),      # 45° 导入斜面
        (s_hook, r_od + hook_up),      # 钩齿底面
        (s_hook, tab_in),              # 止退面（径向台阶）
        (sa, tab_in),
    ]
    root = [
        (root_a, r_od - 0.6),
        (root_b, r_od - 0.6),
        (root_b, r_od + o),
        (root_a, r_od + o),
    ]
    bump = [
        (b0, r_od - 0.6),
        (b1, r_od - 0.6),
        (b1, r_od + bump_h),
        (b0, r_od + bump_h - 0.6),     # 前缘 45° 倒角
    ]
    return hook, root, bump


def latch_prism(vertices, r_ref, r_od, z0, z1, chamfer=4.5, slices=7):
    """底部做 45° 收坡（每层台阶只占 chamfer/slices 高）：凸出体不能有悬空的水平底面。

    每层必须只从自己的 z_a 长到下一层，不能一路顶到 z1——那样最内缩的一层会把整个
    高度都盖住，坡就白做了，而且会和对面凸块整段重叠。
    """
    if chamfer <= 0:
        return polar_solid(vertices, r_ref, z0, z1)
    out = mf.Manifold()
    step = chamfer / slices
    for k in range(slices):
        t = (k + 1) / slices
        z_a = z0 + chamfer - step * (k + 1)
        z_b = z0 + chamfer - step * k
        verts = [(s, r_od + (r - r_od) * t) for (s, r) in vertices]
        out += polar_solid(verts, r_ref, z_a, z_b)
    out += polar_solid(vertices, r_ref, z0 + chamfer, z1)
    return out


def apply_latches(a, b, dim=DIM):
    hook, root, bump = latch_polys(dim)
    r_od = (dim["bore"] + 2 * dim["wall"]) / 2
    a_extra = mf.Manifold()
    b_extra = mf.Manifold()
    for lat in LATCHES:
        z0, z1 = lat["z0"], lat["z1"]
        # 不做底部收坡：阶梯收坡会在卡钩区留下 160+ 条 4 面共边的碎面（布尔近共面），
        # 网格不再水密。卡钩底面很小（三个共 ~300mm² 悬垂），交给切片加支撑更省事。
        hk = latch_prism(hook, r_od, r_od, z0, z1, chamfer=0.0)
        hk += latch_prism(root, r_od, r_od, z0, z1, chamfer=0.0)
        bp = latch_prism(bump, r_od, r_od, z0, z1, chamfer=0.0)
        if lat["seam"] < 0:
            hk, bp = mirror_x(hk), mirror_x(bp)
        a_extra += hk
        b_extra += bp
    return a + a_extra, b + b_extra


def drop_slivers(m):
    """CSG 会留下体积为零的退化碎片；不清理它们会让网格出现几十个"身体"和假缝隙。"""
    keep = [p for p in m.decompose() if p.volume() > 1.0]
    out = mf.Manifold()
    for p in keep:
        out += p
    return out


def build_halves():
    solid = build_solid()
    a, b = split_halves(solid)
    a, b = apply_latches(a, b)
    return solid, drop_slivers(a), drop_slivers(b)


# ---------- 判据 ----------

def report(solid, a, b):
    dim = DIM
    z4 = (
        dim["insert_len"]
        + dim["wall_flange_len"]
        + dim["skirt_draft"]
        + dim["barrel_len"]
        + dim["spigot_len"]
    )
    out = {
        "solid_volume_cm3": round(solid.volume() / 1000, 2),
        "a_volume_cm3": round(a.volume() / 1000, 2),
        "b_volume_cm3": round(b.volume() / 1000, 2),
        "watertight": bool(a.status() == mf.Error.NoError
                           and b.status() == mf.Error.NoError),
    }

    main_probe = disc(25.0, z4 + 20).translate([0, 0, -10])
    # 支口探针必须与支口内孔同轴：内孔从 root_z-6 起、长 branch_len+8。
    # 基面取不同 z（例如 root_z-2）会让两条轴错开 4 mm，探针会削到支口内壁，
    # 报出几百 mm³ 的假"堵塞"。这里从内孔底往上 1 mm 开始，末端留 2 mm。
    br_probe = rotated_tube(dim["branch_root_z"] - 5.0, dim["branch_len"] + 6.0, 19.0)
    ins_probe = disc(24.0, dim["insert_len"] + 2)
    out["probe_main_block_mm3"] = round(inter(solid, main_probe).volume(), 2)
    out["probe_branch_block_mm3"] = round(inter(solid, br_probe).volume(), 2)
    out["probe_insert_block_mm3"] = round(inter(solid, ins_probe).volume(), 2)

    out["a_intersect_b_cm3"] = round(inter(a, b).volume() / 1000, 4)
    out["union_extra_cm3"] = round(((a + b).volume() - solid.volume()) / 1000, 4)
    out["union_missing_cm3"] = round((solid - (a + b)).volume() / 1000, 4)

    t = LATCH["tab_thick"]
    arc_len = abs(LATCH["s_tab"][0] - LATCH["s_tab"][1])
    delta = LATCH["bump_h"] - dim["fit_clear"]
    out["latch_arc_mm"] = arc_len
    out["latch_strain_pct"] = round(3 * t * delta / (2 * arc_len ** 2) * 100, 3)

    tri = union_mesh(a, b)
    nz = tri.face_normals[:, 2]
    need = (nz < -math.cos(math.radians(45.0))) & (tri.triangles_center[:, 2] > 0.6)
    out["support_area_mm2"] = round(float(tri.area_faces[need].sum()), 1)
    out["bbox_mm"] = [round(v, 1) for v in (tri.bounds[1] - tri.bounds[0])]
    return out


def union_mesh(a, b):
    m = (a + b).to_mesh()
    return trimesh.Trimesh(
        np.asarray(m.vert_properties, dtype=np.float64),
        np.asarray(m.tri_verts, dtype=np.int64),
        process=True,
    )


def to_trimesh(solid):
    m = solid.to_mesh()
    return trimesh.Trimesh(
        np.asarray(m.vert_properties, dtype=np.float64),
        np.asarray(m.tri_verts, dtype=np.int64),
        process=True,
    )


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    solid, a, b = build_halves()
    rep = report(solid, a, b)
    print(json.dumps(rep, ensure_ascii=False, indent=2))

    fails = []
    if rep["probe_main_block_mm3"] > 0.5:
        fails.append("主通道被堵")
    if rep["probe_branch_block_mm3"] > 0.5:
        fails.append("支口被堵")
    if rep["probe_insert_block_mm3"] > 0.5:
        fails.append("穿墙段被堵")
    if rep["a_intersect_b_cm3"] > 0.05:
        fails.append("两瓣干涉")
    # 止口单边间隙（0.25）本身就让并集少掉约 0.13 cm³，这是设计内的配合量。
    if rep["union_missing_cm3"] > 0.2:
        fails.append("两瓣合起来少了实体")
    if rep["latch_strain_pct"] > 2.0:
        fails.append("卡钩应变过大")
    if not rep["watertight"]:
        fails.append("网格不水密")
    if fails:
        print("CHECK FAIL:", fails)
        sys.exit(1)

    tri_a, tri_b = to_trimesh(a), to_trimesh(b)
    tri_a.export(os.path.join(here, "tee_split_A.stl"))
    tri_b.export(os.path.join(here, "tee_split_B.stl"))

    gap = 12.0
    off_b = (tri_a.bounds[1][0] + gap) - tri_b.bounds[0][0]
    scene = trimesh.Scene()
    scene.add_geometry(tri_a, node_name="A")
    tb = tri_b.copy()
    tb.apply_translation([off_b, 0, 0])
    scene.add_geometry(tb, node_name="B")
    scene.export(os.path.join(here, "exhaust-tee-split.3mf"))

    asm = tri_a + tri_b
    asm.export(os.path.join(here, "exhaust-tee-split-assembled.stl"))

    with open(os.path.join(here, "report.json"), "w") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    print("wrote tee_split_A/B.stl, exhaust-tee-split.3mf, assembled stl, report.json")


if __name__ == "__main__":
    main()
