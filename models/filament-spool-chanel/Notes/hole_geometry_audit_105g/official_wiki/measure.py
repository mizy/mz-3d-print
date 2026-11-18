from pathlib import Path
import numpy as np,trimesh,json,hashlib
exec(Path('/tmp/chanel_hole_comparison/measure.py').read_text().split('out={')[0])
out={}
for part in ['wide','narrow']:
 p=Path('/tmp/chanel_official_wiki')/(part+'.stl'); m=trimesh.load(p,process=False); b=m.bounds.copy(); v=m.vertices.copy(); m.vertices=np.column_stack([v[:,1],v[:,2],33.70000076293945-v[:,0] if part=='wide' else v[:,0]+33.70000076293945])
 user=Path('/Users/miaozhuang/Downloads')/('bambulab_spool_'+part+'.stl')
 rows=[]
 for z in Z:
  if z>=m.bounds[1,2]:continue
  seg=trimesh.intersections.mesh_plane(m,[0,0,1],[0,0,z]);rows.append({'z':z,'hole':rays(seg)})
 out[part]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'user_download_exact_match':user.exists() and user.read_bytes()==p.read_bytes(),'bounds':b.tolist(),'normalized_bounds':m.bounds.tolist(),'faces':len(m.faces),'sections':rows}
 print(part,out[part],flush=True)
Path('/tmp/chanel_official_wiki/measurements.json').write_text(json.dumps(out,indent=2))
