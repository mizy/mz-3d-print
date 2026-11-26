"""Cut one rounded window in each side wall of the V18 drawer, for a weight trial.

Window: 120 mm (Y) x 45 mm (Z), R8 corners, in each 1 mm side wall.
Keeps 30 mm above the Z10 rail, 11 mm below the rim, and >=55 mm to the
front/rear corners.  Exports STEP + STL and prints the volume delta.
"""

import FreeCAD
import MeshPart
import Part

SRC = "/Users/mizy/projects/mz-3d-print/models/modular-drawer/V18_Single_Head_T_Rod_Drawer/Print_Parts/04_Drawer.step"
OUT_STEP = "/Users/mizy/projects/mz-3d-print/models/modular-drawer/V18_Single_Head_T_Rod_Drawer/Notes/drawer_print_prep/drawer_windowed.step"
OUT_STL = "/Users/mizy/projects/mz-3d-print/models/modular-drawer/V18_Single_Head_T_Rod_Drawer/Notes/drawer_print_prep/drawer_windowed.stl"

WINDOW_Y = 120.0
WINDOW_Z = 45.0
RADIUS = 8.0
Y0, Z0 = 55.0, 30.0


def cutter(x0):
    box = Part.makeBox(6.0, WINDOW_Y, WINDOW_Z)
    long_edges = [e for e in box.Edges if abs(e.tangentAt(0).x) > 0.99]
    box = box.makeFillet(RADIUS, long_edges)
    return box.translate(FreeCAD.Vector(x0, Y0, Z0))


shape = Part.Shape()
shape.read(SRC)
before = shape.Volume

shape = shape.cut(cutter(-3.0))
shape = shape.cut(cutter(141.0))
after = shape.Volume

shape.exportStep(OUT_STEP)
mesh = MeshPart.meshFromShape(
    Shape=shape, LinearDeflection=0.05, AngularDeflection=0.3, Relative=False
)
mesh.write(OUT_STL)

print("volume_before_mm3", round(before, 1))
print("volume_after_mm3", round(after, 1))
print("removed_mm3", round(before - after, 1))
print("solids", len(shape.Solids), "shells", len(shape.Shells))
print("bbox", shape.BoundBox)
