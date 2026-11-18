import cadquery as cq,trimesh,numpy as np,json
from pathlib import Path
D=Path(__file__).parent;s=cq.importers.importStep(str(D/'variant_prototype/CHANEL_PARKING_A_SELF_SUPPORT_ROOF_TRIAL.step')).val();rows=[]
for b in s.Solids():
 v,f=b.tessellate(.01,.1);m=trimesh.Trimesh([[p.x,p.y,p.z] for p in v],f,process=True);c=np.bincount(m.edges_unique_inverse);r={'valid':b.isValid(),'faces':len(b.Faces()),'boundary_edges':int(sum(c==1)),'nonmanifold':int(sum(c>2)),'watertight':m.is_watertight};rows.append(r);print(r,flush=True);assert r['valid'] and r['watertight'] and not r['nonmanifold']
(D/'variant_mesh.json').write_text(json.dumps(rows,indent=2))
