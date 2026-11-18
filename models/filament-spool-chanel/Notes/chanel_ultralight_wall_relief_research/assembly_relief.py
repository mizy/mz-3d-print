import cadquery as cq,json
from pathlib import Path
D=Path(__file__).parent;w=cq.importers.importBrep(str(D/'relief/wide.brep')).val();n=cq.importers.importBrep(str(D/'relief/narrow.brep')).val();r=[]
for H,t in [(70,51),(66.4,8),(66.4,3),(66.4,0),(66.5,8)]:
 x=n.rotate((0,0,0),(1,0,0),180).rotate((0,0,0),(0,0,1),t).translate((0,0,H));v=w.intersect(x).Volume();r.append({'H':H,'theta':t,'rigid_overlap_mm3':v});print(r[-1],flush=True)
(D/'relief_assembly_checks.json').write_text(json.dumps(r,indent=2))
