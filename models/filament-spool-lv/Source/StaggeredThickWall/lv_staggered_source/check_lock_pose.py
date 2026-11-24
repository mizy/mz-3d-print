from model_paths import MODELS_DIR
from pathlib import Path
import cadquery as cq,json
R=MODELS_DIR;w=cq.Shape.importBrep(str(R/'wide_hub.brep'));n=cq.Shape.importBrep(str(R/'narrow_hub.brep')).rotate((0,0,0),(1,0,0),180);out=[]
for a in [40,42,44,46,48,50,52,54]:
 for dz in [0,1,3]:
  x=n.rotate((0,0,0),(0,0,1),a).translate((0,0,67.4+dz));v=w.intersect(x).Volume();out.append({'angle_deg':a,'pull_offset_mm':dz,'interference_mm3':v});print(a,dz,round(v,6),flush=True)
(R/'lock_pose_checks.json').write_text(json.dumps(out,indent=2))
