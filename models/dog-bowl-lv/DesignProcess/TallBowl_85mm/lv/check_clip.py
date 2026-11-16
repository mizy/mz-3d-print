import cadquery as cq,json
from pathlib import Path
r=Path(__file__).parent
s=cq.importers.importStep(str(r/'parts/clip_fit_coupon.step')).val()
b=s.BoundingBox()
base=cq.Workplane('XY').box(200,200,.1,centered=(True,True,False)).translate((0,0,0)).val()
area=s.intersect(base).Volume()/.1
out={'tongue_dimensions_mm':[b.xlen,b.ylen,b.zlen],'z_min':b.zmin,'bed_contact_area_mm2':area,'bar_on_bed':abs(area-70*8.5)<1,'mating_fit_tested':False,'sliced':False}
(r/'clip_validation.json').write_text(json.dumps(out,indent=2)); print(out)
