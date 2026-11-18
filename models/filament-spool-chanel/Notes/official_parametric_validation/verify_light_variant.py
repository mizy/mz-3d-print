import cadquery as cq,numpy as np,trimesh,json
from pathlib import Path
D=Path(__file__).parent;step=D/'light_variant/BAMBU_OFFICIAL_DERIVED_LIGHT_CHANEL.step';s=cq.importers.importStep(str(step)).val();rows=[]
for i,b in enumerate(sorted(s.Solids(),key=lambda x:x.BoundingBox().center.x)):
 v,f=b.tessellate(.005,.05);m=trimesh.Trimesh([[x.x,x.y,x.z] for x in v],f,process=True);cnt=np.bincount(m.edges_unique_inverse);r={'part':['wide','narrow'][i],'valid':b.isValid(),'faces':len(b.Faces()),'width':b.BoundingBox().xlen,'boundary_edges':int(sum(cnt==1)),'nonmanifold':int(sum(cnt>2)),'watertight':m.is_watertight};assert r['valid'] and r['watertight'] and r['width']>199.99;rows.append(r);print(r,flush=True)
(D/'light_variant/mesh_validation.json').write_text(json.dumps(rows,indent=2))
