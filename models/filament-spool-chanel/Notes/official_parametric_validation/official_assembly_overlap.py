from pathlib import Path
import numpy as np,trimesh,json,time
from shapely.geometry import LineString
from shapely.ops import unary_union,polygonize
from shapely import affinity
D=Path('/tmp/chanel_official_native/mesh_audit')
meshes={}
for p in ['wide','narrow']:
 m=trimesh.load('/tmp/chanel_official_wiki/'+p+'.stl',process=False);v=m.vertices.copy();m.vertices=np.c_[v[:,1],-v[:,2] if p=='wide' else v[:,2],33.70000076293945-v[:,0] if p=='wide' else v[:,0]+33.70000076293945];meshes[p]=m
cache={}
def section(part,z):
 key=(part,round(z,8))
 if key in cache:return cache[key]
 m=meshes[part];seg=trimesh.intersections.mesh_plane(m,[0,0,1],[0,0,z]);ss=np.round(seg[:,:,:2],8)
 if len(ss)==0:return None
 ls=unary_union([LineString(s) for s in ss]);polys=list(polygonize(ls));good=[]
 a=ss[:,0];b=ss[:,1]
 for poly in polys:
  pt=poly.representative_point();x,y=pt.x,pt.y;mask=(a[:,1]>y)!=(b[:,1]>y)
  aa=a[mask];bb=b[mask];xx=aa[:,0]+(y-aa[:,1])*(bb[:,0]-aa[:,0])/(bb[:,1]-aa[:,1]);count=sum(xx>x)
  if count%2:good.append(poly)
 shape=unary_union(good)
 # Degree diagnostics before polygonizing detect missing mesh section loops.
 _,ii=np.unique(ss.reshape(-1,2),axis=0,return_inverse=True);non2=int(sum(np.bincount(ii)!=2))
 cache[key]=(shape,non2,len(polys));return cache[key]
results=[]
for H,theta in [(66.4,3),(66.4,8),(70.,45),(70.,48),(68.,45),(68.,48),(66.4,48)]:
 for step in [.1,.05]:
  lo=max(0,H-34.10000076294);hi=min(40.70000076294,H);N=int(np.ceil((hi-lo)/step));dz=(hi-lo)/N;rows=[];bad=[]
  for z in lo+(np.arange(N)+.5)*dz:
   w=section('wide',float(z));n=section('narrow',float(H-z))
   if w is None or n is None:continue
   ng=affinity.rotate(affinity.scale(n[0],xfact=1,yfact=-1,origin=(0,0)),theta,origin=(0,0));inter=w[0].intersection(ng);area=inter.area
   if w[1] or n[1]:bad.append([float(z),w[1],n[1]])
   if area>1e-10:rows.append({'z':float(z),'area':area,'bounds':list(inter.bounds)})
  out={'H':H,'theta':theta,'target_step':step,'actual_dz':dz,'sample_count':N,'overlap_volume_estimate_mm3':sum(r['area'] for r in rows)*dz,'positive_section_count':len(rows),'max_section_area':max([r['area'] for r in rows] or [0]),'nonclosed_sections':bad,'positive_sections':rows};results.append(out);print({k:v for k,v in out.items() if k not in ['positive_sections','nonclosed_sections']},'bad',len(bad),flush=True)
  (D/'official_assembly_overlap.json').write_text(json.dumps({'method':'Official original STL only; right-handed canonical then narrow Rx180 Rztheta Z+H. Horizontal mesh-plane section; rounded8 polygonize, material selected via ray crossing parity; midpoint integration, no 3D mesh boolean. Two step sizes provide convergence evidence only, no guaranteed global bound or elastic safety.','results':results},indent=2))
