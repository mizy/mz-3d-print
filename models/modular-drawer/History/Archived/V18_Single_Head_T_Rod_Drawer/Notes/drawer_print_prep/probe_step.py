import Part

path = "/Users/mizy/projects/mz-3d-print/models/modular-drawer/V18_Single_Head_T_Rod_Drawer/Print_Parts/04_Drawer.step"
shape = Part.Shape()
shape.read(path)
print("solids", len(shape.Solids), "shells", len(shape.Shells))
print("bbox", shape.BoundBox)
print("volume", shape.Volume)
