from model_paths import MODELS_DIR
from pathlib import Path
import cadquery as cq,json
R=MODELS_DIR;w=cq.Shape.importBrep(str(R/'wide_hub.brep'));n=cq.Shape.importBrep(str(R/'narrow_hub.brep')).rotate((0,0,0),(1,0,0),180).translate((0,0,67.4));out=[]
for a in range(0,91,10):
 x=w.intersect(n.rotate((0,0,0),(0,0,1),a));rec={'angle_deg':a,'volume_mm3':x.Volume(),'regions':[]}
 for sol in x.Solids():
  b=sol.BoundingBox();rec['regions'].append({'volume_mm3':sol.Volume(),'bbox':[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]})
 out.append(rec);print(a,x.Volume(),flush=True)
(R/'clocking_checks.json').write_text(json.dumps(out,indent=2))
