from pathlib import Path
import sys,json
R=Path(__file__).resolve().parent
sys.path[:0]=[str(R/'deps'),str(R/'deps')]
import trimesh,numpy as np
from shapely.geometry import Polygon
features=json.loads((R/'features.json').read_text());audit=json.loads((R/'source_audit.json').read_text())
out={}
for k in ['wide','narrow']:
 src=trimesh.load(R/f'official_{k}_stitched.stl');new=trimesh.load(R/f'CHANEL_SOURCE21_{k}_FROZEN.obj',process=False)
 d=[]
 for z in [.01,.1,.3,.59,1.5,2.9]:
  ss=[]
  for m in [src,new]:
   sec=m.section(plane_origin=[0,0,z],plane_normal=[0,0,1]);ps=[Polygon(q[:,:2]) for q in sec.discrete];ss.append([p for p in ps if .1<p.area<15])
  if any(not ps for ps in ss):
   print(k,z,"no isolated hole loops",[len(ps) for ps in ss],flush=True);continue
  for i,h in enumerate(features[audit[k]['source']]['retention_holes_z1_5']):
   xy=np.array(h['center_xy_mm']);a,b=[min(ps,key=lambda p:np.linalg.norm(np.array(p.centroid.coords)[0]-xy)) for ps in ss]
   assert all(np.linalg.norm(np.array(p.centroid.coords)[0]-xy)<.2 for p in [a,b])
   d.append({'z':z,'hole':i+1,'source_area':a.area,'new_area':b.area,'symmetric_difference_mm2':a.symmetric_difference(b).area,'boundary_hausdorff_mm':a.boundary.hausdorff_distance(b.boundary)})
 out[k]=d
(R/'hole_profiles.json').write_text(json.dumps(out,indent=2))
for k,v in out.items(): print(k,'max area diff',max(x['symmetric_difference_mm2'] for x in v),'max boundary distance',max(x['boundary_hausdorff_mm'] for x in v))
