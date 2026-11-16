import cadquery as cq
from pathlib import Path
p=Path(__file__).parent/'parts'
s=cq.importers.importStep(str(p/'ivory_glue_logo.step')).val().rotate((0,0,0),(1,0,0),90)
b=s.BoundingBox();s=s.translate((-(b.xmin+b.xmax)/2,-(b.ymin+b.ymax)/2,-b.zmin))
cq.exporters.export(s,str(p/'ivory_logo_print_flat.step'));cq.exporters.export(s,str(p/'ivory_logo_print_flat.stl'),tolerance=.02,angularTolerance=.08)
# 2 mm high bed-contact footprint fit gauge: tongue width/depth and actual rear spacing.
b=cq.importers.importStep(str(p/'blue_body_with_inverted_T_clip.step')).val()
g=b.intersect(cq.Workplane('XY').box(300,300,2,centered=(True,True,False)).val())
cq.exporters.export(g,str(p/'footprint_2mm_gauge.step'));cq.exporters.export(g,str(p/'footprint_2mm_gauge.stl'),tolerance=.02,angularTolerance=.08)
print('flat logo and 2mm gauge exported')
