from pathlib import Path
import sys,json
R=Path(__file__).parent;sys.path.insert(0,str(R/'deps'))
import trimesh,numpy as np
out={}
for k in ['wide','narrow']:
 m=trimesh.load(R/f'official_{k}_normalized_RAW.stl');v0=m.volume;f0=len(m.faces)
 m.update_faces(m.nondegenerate_faces(height=1e-8));m.update_faces(m.unique_faces());m.remove_unreferenced_vertices()
 e,c=np.unique(m.edges_sorted,axis=0,return_counts=True);print(k,'CLEAN',len(m.faces),m.is_watertight,np.unique(c,return_counts=True),flush=True)
 m.export(R/f'official_{k}_clean.stl');out[k]={'before_faces':f0,'after_faces':len(m.faces),'volume_delta_mm3':float(m.volume-v0),'volume_mm3':float(m.volume),'watertight':bool(m.is_watertight),'non_two_edges':int((c!=2).sum())}
(R/'repair_audit.json').write_text(json.dumps(out,indent=2))
