"""V17 挂头自支撑修正：把托架后挂头从 z=0.5 延到 z=0，去掉必须开支撑的那处悬空。

背景
----
`design.py` 里挂头是 `box((3.8,1.6,8),(x-1.9,5.4,0.5))` —— 底面离床 0.5mm，
切片器判成 floating regions，只能开支撑打（小样实测 +23s）。

改法
----
挂头底面落到 z=0（顶面仍 8.5），托架整体挂位抬高 0.5mm，其余尺寸一个没动：
  - 挂头 3.8 x 1.6，z 0 -> 8.5
  - 挂柱 2.8 x 5.4 x 3，z 2.95 -> 5.95（不变，仍是后壁到挂头之间的桥）
  - 底 2.0 / 后壁 2.0 / 前挡 2.0 / 侧壁 1.8（不变）

用法
----
  /tmp/v17env/bin/python fix_hook.py
产出：universal_tray-hookfix.stl、print-plates/00_fit_test-hookfix.3mf
"""
from pathlib import Path

import manifold3d as md
import numpy as np
import trimesh
from trimesh.exchange.threemf import export_3MF

M = md.Manifold
O = Path(__file__).parent
D = O / "print-plates"

TRAY_W, TRAY_D = 47.6, 14.0
BOTTOM, WALL, SIDE = 2.0, 2.0, 1.8
HOOK_BOTTOM, HOOK_TOP = 0.0, 8.5      # 原来 HOOK_BOTTOM=0.5
POST_Z = 2.95


def box(d, p):
    return M.cube(d).translate(p)


def build_tray(hook_bottom: float = HOOK_BOTTOM) -> md.Manifold:
    t = box((TRAY_W, TRAY_D, BOTTOM), (-TRAY_W / 2, -TRAY_D, 0))
    t += box((TRAY_W, WALL, 12), (-TRAY_W / 2, -2, 0))
    t += box((TRAY_W, WALL, 6), (-TRAY_W / 2, -TRAY_D, 0))
    for x in (-TRAY_W / 2, TRAY_W / 2 - 1.8):
        t += box((SIDE, TRAY_D, 8), (x, -TRAY_D, 0))
    for x in (-20, 20):
        t += box((2.8, 5.4, 3), (x - 1.4, 0, POST_Z))
        t += box((3.8, 1.6, HOOK_TOP - hook_bottom), (x - 1.9, 5.4, hook_bottom))
    return t


def to_trimesh(s: md.Manifold) -> trimesh.Trimesh:
    a = s.to_mesh()
    t = trimesh.Trimesh(np.asarray(a.vert_properties)[:, :3], a.tri_verts, process=True)
    t.merge_vertices(digits_vertex=5)
    t.update_faces(t.nondegenerate_faces())
    t.remove_unreferenced_vertices()
    return t


def main() -> None:
    old = to_trimesh(build_tray(0.5))
    new = to_trimesh(build_tray(HOOK_BOTTOM))
    assert new.is_watertight, "修完的托架不水密"
    print(f"托架体积 {old.volume / 1000:.2f} -> {new.volume / 1000:.2f} cm3 "
          f"(+{(new.volume - old.volume) / 1000:.3f})")
    print(f"包围盒 {np.round(old.extents, 2)} -> {np.round(new.extents, 2)}")
    print(f"最低点 z: {old.bounds[0][2]:.2f} -> {new.bounds[0][2]:.2f}")
    new.export(O / "universal_tray-hookfix.stl")

    # 小样盘：60x24 双孔试片（从裁短后的立板截取）+ 修正后的托架
    board = trimesh.load_mesh(O / "board-232.stl")
    solid = M(md.Mesh(np.asarray(board.vertices, dtype=np.float32),
                      np.asarray(board.faces, dtype=np.uint32)))
    c = solid ^ M.cube((60, 24, 7)).translate((2, 204, -1))
    coupon = to_trimesh(c)
    coupon.apply_translation(-coupon.bounds[0])

    scene = trimesh.Scene()
    scene.units = "mm"
    for label, mesh, x, y in (("two_hole_coupon", coupon, 60, 90),
                              ("one_test_tray", new, 130, 90)):
        t = mesh.copy()
        t.apply_translation(np.array([x, y, 0]) - t.bounds[0])
        scene.add_geometry(t, node_name=label, geom_name=label)
    out = D / "00_fit_test-hookfix.3mf"
    out.write_bytes(export_3MF(scene))
    back = trimesh.load_scene(out)
    print(f"写出 {out.name}  对象 {len(back.graph.nodes_geometry)}  "
          f"体积 {back.volume / 1000:.2f} cm3  包围盒 {np.round(back.bounds, 1).tolist()}")


if __name__ == "__main__":
    main()
