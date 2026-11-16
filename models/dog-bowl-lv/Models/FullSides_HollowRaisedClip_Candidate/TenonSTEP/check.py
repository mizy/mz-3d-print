import cadquery as cq,json
from pathlib import Path
p=Path(__file__).resolve().parent;b=cq.importers.importStep(str(p/'LV_bowl_multibody.step')).val();l=cq.importers.importStep(str(p/'LV_logo_tenon_assembly_position.step')).val()
r={}
for dz in [0,.375,.75,1.125,1.5]:r['slide_z_'+str(dz)]=b.intersect(l.translate((0,0,dz))).Volume()
r['pull_out_seated_0.5mm_interference']=b.intersect(l.translate((0,-.5,0))).Volume()
for dy in [-.5,-1,-2,-3]:r['entry_y_'+str(dy)]=b.intersect(l.translate((0,dy,1.5))).Volume()
(p/'motion_check.json').write_text(json.dumps(r,indent=2));print(r)
