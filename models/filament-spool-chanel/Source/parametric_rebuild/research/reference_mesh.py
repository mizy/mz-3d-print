"""Read exact existing faceted STEP only as measurement reference; never export mesh as CAD."""
from pathlib import Path
import numpy as np,trimesh,re,json,hashlib
from shapely.geometry import LineString
from shapely.ops import polygonize,unary_union
D=Path('/tmp/chanel-interface-input');R=Path('/Users/miaozhuang/Projects/mz-3d-print/models/filament-spool-chanel/Models')
def load(part):
 path=D/f'{part}_reference_mesh.npz'
 if not path.exists():
  src=R/f'CHANEL_SOURCE21_{part}.step';points={};faces=[]
  for line in src.open():
   if '=CARTESIAN_POINT' in line:
    id=int(line[1:line.index('=')]);points[id]=[float(x) for x in line.split('(',2)[2].split(')')[0].split(',')]
   elif '=POLY_LOOP' in line:faces.append([int(x) for x in re.findall(r'#(\d+)',line.split('=',1)[1])])
  ids=sorted(points);idx={id:i for i,id in enumerate(ids)};v=np.array([points[i] for i in ids]);f=np.array([[idx[i] for i in face] for face in faces]);np.savez_compressed(path,vertices=v,faces=f)
 d=np.load(path);return trimesh.Trimesh(vertices=d['vertices'],faces=d['faces'],process=False)
def profile(mesh,z,part):
 lines=trimesh.intersections.mesh_plane(mesh,[0,0,1],[0,0,z]);rounded=np.round(lines[:,:,:2],8)
 polys=list(polygonize(unary_union([LineString(seg) for seg in rounded])));
 if not polys:raise ValueError(f'no polygons at {z}')
 # polygonize includes both annular material and filled hole polygons; inspect all boundaries, dedupe exact loops.
 loops=[]
 for p in polys:
  for ring in [p.exterior,*p.interiors]:
   a=np.array(ring.coords);rad=np.linalg.norm(a,axis=1);mean=rad.mean()
   if part=='wide' and mean<33.4:loops.append((mean,a))
   elif part=='narrow' and 28.8<mean<33.4:loops.append((mean,a))
 if not loops:raise ValueError(f'no lock loop {part} {z}')
 return min(loops,key=lambda x:x[0])[1] if part=='wide' else max(loops,key=lambda x:x[0])[1]
if __name__=='__main__':
 for part in ['wide','narrow']:
  m=load(part);print(part,len(m.vertices),len(m.faces),len(profile(m,32.2,part)),flush=True)
