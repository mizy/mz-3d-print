"""P1S 排风三通：Φ60 软管 + Φ30 空调管，共用墙上 55–57 的洞。

坐标系（打印姿态，+Z 朝上）：
    z=0        软管插座口，立在热床上
    z=0..30    Φ66.4 软管插座（软管套在外侧）
    z=30..35   45° 收口，从 66.4 收到 56.2
    z=35..35+W 穿墙短管 Φ56.2
    z≈10       45° 空调管支口（Φ36/Φ32），装上墙翻面后变成朝下 45°

所有尺寸在 DIM 里，改完重跑本脚本即可。输出 exhaust_tee.stl / .3mf。
"""
import manifold3d as mf
import numpy as np
import trimesh

DIM = {
    "wall_t": 25.0,       # 插进墙洞的短管长度（洞本身就是风道，不必贯穿整面墙）
    "hole_d": 57.0,       # 墙洞直径
    "clearance": 0.4,     # 穿墙管与洞的单边间隙
    "wall": 2.0,          # 件壁厚
    "duct_id": 62.4,      # 软管插座内径（软管外径 62 时）
    "duct_len": 50.0,     # 软管插座长度（45° 支口要在这一段内出墙）
    "taper": 5.0,         # 收口高度（≈45°）
    "ac_d": 32.0,         # 空调管穿孔（管 30 + 余量）
    "ac_stub_len": 48.0,  # 支口长度
    "ac_angle": 45.0,     # 支口与主轴夹角
}

SEG = 96
SLICE = 0.5


def cyl(r, h, z=0.0):
    return mf.CrossSection.circle(r, SEG).extrude(h).translate([0, 0, z])


def tapered(z0, z1, r0, r1):
    """Solid of revolution from (z0, r0) to (z1, r1), built as thin discs."""
    out = mf.Manifold()
    z = z0
    while z < z1 - 1e-9:
        h = min(SLICE, z1 - z)
        r = r0 + (r1 - r0) * ((z - z0) + h / 2) / (z1 - z0)
        out += cyl(r, h, z)
        z += h
    return out


def build(dim=DIM):
    od_barrel = dim["hole_d"] - 2 * dim["clearance"]
    id_barrel = od_barrel - 2 * dim["wall"]
    od_socket = dim["duct_id"] + 2 * dim["wall"]

    r_ob, r_ib = od_barrel / 2, id_barrel / 2
    r_os, r_is = od_socket / 2, dim["duct_id"] / 2

    z_mid = dim["duct_len"]
    z_top = z_mid + dim["taper"]

    outer = cyl(r_os, z_mid)
    outer += tapered(z_mid, z_top, r_os, r_ob)
    outer += cyl(r_ob, dim["wall_t"], z_top)

    inner = cyl(r_is, z_mid - 0.5)
    inner += tapered(z_mid - 0.5, z_top, r_is, r_ib)
    inner += cyl(r_ib, dim["wall_t"] + 2, z_top)

    stub_shell = cyl(dim["ac_d"] / 2 + dim["wall"], dim["ac_stub_len"])
    stub_bore = cyl(dim["ac_d"] / 2, dim["ac_stub_len"] + 4)
    z0 = 16.0  # 支口中心高度：最低点 3.3mm 离床，末端 49.9mm 仍在插座段内
    stub_shell = stub_shell.rotate([0, dim["ac_angle"], 0]).translate([0, 0, z0])
    stub_bore = stub_bore.rotate([0, dim["ac_angle"], 0]).translate([0, 0, z0])

    return (outer + stub_shell) - inner - stub_bore


def main():
    part = build()
    mesh = part.to_mesh()
    tri = trimesh.Trimesh(
        np.asarray(mesh.vert_properties, dtype=np.float64),
        np.asarray(mesh.tri_verts, dtype=np.int64),
        process=True,
    )
    print("material volume cm3:", round(part.volume() / 1000, 1))
    print("bounds:", tri.bounds.round(1).tolist())
    print("size:", tri.extents.round(1).tolist())

    faces_down = tri.face_normals[:, 2] < -0.85
    centers = tri.triangles_center
    over = faces_down & (centers[:, 2] > 1.0)
    print("downward horizontal faces above bed:", int(over.sum()))

    tri.export("exhaust_tee.stl")
    tri.export("exhaust_tee.3mf")
    print("wrote exhaust_tee.stl / exhaust_tee.3mf")


if __name__ == "__main__":
    main()
