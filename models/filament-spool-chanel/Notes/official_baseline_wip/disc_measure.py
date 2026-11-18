import trimesh,numpy as np,json
from shapely.ops import polygonize,unary_union
from shapely.geometry import LineString
from pathlib import Path
D=Path('/tmp/chanel_official_native');out={}
for part in ['wide','narrow']:
 m=trimesh.load('/Users/miaozhuang/Downloads/bambulab_spool_'+part+'.stl');v=m.vertices.copy();m.vertices=np.c_[v[:,1],v[:,2],m.bounds[1,0]-v[:,0] if part=='wide' else v[:,0]-m.bounds[0,0]];rows=[]
 for z in [.2,1,2.8,3.4]:
  segments=trimesh.intersections.mesh_plane(m,[0,0,1],[0,0,z]);polys=list(polygonize(unary_union([LineString(np.round(a[:,:2],7)) for a in segments])));loops=[]
  for a in [np.asarray(p.exterior.coords) for p in polys]:
   b=a[:,:2];center=(b.max(axis=0)+b.min(axis=0))/2;bb=b.max(axis=0)-b.min(axis=0);rad=np.linalg.norm(b,axis=1)
   loops.append({'bbox_center':center.tolist(),'bbox_size':bb.tolist(),'radius_range':[rad.min(),rad.max()],'vertices':len(b)})
  rows.append({'z':z,'loops':loops})
 out[part]=rows
(D/'disc_measurements.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
