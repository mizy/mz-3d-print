from pathlib import Path
import sys,json,hashlib
R=Path(__file__).parent;sys.path.insert(0,str(R/'deps'))
import trimesh,numpy as np
out={}
for k,n in [('wide','obj_1_料盘反面.stl'),('narrow','obj_2_料盘正面.stl')]:
 p=R/'input'/n;m=trimesh.load(p);origin=np.r_[(m.bounds[0,:2]+m.bounds[1,:2])/2,m.bounds[0,2]];m.apply_translation(-origin)
 e,c=np.unique(m.edges_sorted,axis=0,return_counts=True)
 out[k]={'source':n,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'translation_to_origin_mm':(-origin).tolist(),'faces':len(m.faces),'vertices':len(m.vertices),'bounds_mm':m.bounds.tolist(),'watertight':bool(m.is_watertight),'edge_incidence':dict(zip(map(str,*[np.unique(c)]),map(int,np.unique(c,return_counts=True)[1]))),'degenerate_faces':int((~m.nondegenerate_faces(height=1e-8)).sum()),'duplicate_faces':int((~m.unique_faces()).sum())}
 m.export(R/f'official_{k}_normalized_RAW.stl');print(k,out[k],flush=True)
(R/'source_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
