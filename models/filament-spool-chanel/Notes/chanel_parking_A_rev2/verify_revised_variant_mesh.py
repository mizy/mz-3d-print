import cadquery as cq,trimesh,numpy as np,json
from pathlib import Path
D=Path(__file__).parent;shape=cq.importers.importStep(str(D/'revised_variant/CHANEL_OFFICIAL_LIGHT_PARKING_A_TRIAL.step')).val();rows=[]
for s in shape.Solids():
 v,f=s.tessellate(.01,.1);m=trimesh.Trimesh([[p.x,p.y,p.z] for p in v],f,process=True);count=np.bincount(m.edges_unique_inverse);r={'valid':s.isValid(),'faces':len(s.Faces()),'boundary_edges':int(sum(count==1)),'nonmanifold':int(sum(count>2)),'watertight':m.is_watertight};rows.append(r);print(r,flush=True);assert r['valid'] and r['watertight'] and not r['nonmanifold']
(D/'revised_variant_mesh.json').write_text(json.dumps(rows,indent=2))
