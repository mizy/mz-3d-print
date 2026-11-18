import numpy as np,trimesh,json
from pathlib import Path
out={}
for part in ['wide','narrow']:
 m=trimesh.load('/tmp/chanel_official_wiki/'+part+'.stl',process=False);v=m.vertices.copy();m.vertices=np.c_[v[:,1],v[:,2],33.70000076293945-v[:,0] if part=='wide' else v[:,0]+33.70000076293945]
 # analytic breakpoints from vertex heights on central radius
 r=np.linalg.norm(m.vertices[:,:2],axis=1); zs=np.unique(np.round(m.vertices[(r<35)&(r>26),2],5)); print(part,'vertexZ',zs.tolist())
 rows=[]
 for z in sorted(set([.05,.2,.4,.6,.8,1.,1.2,1.4,1.6,2.,2.2,2.4,2.6,3.,3.2,3.6,3.7,3.8,4.,5.,6.,7.,7.5,7.6,7.7,7.8,8.,10.,12.,14.,18.,21.9,22.1,23.9,24.1,32.,33.,33.2,33.4,33.6,33.8,34.])):
  if z>=m.bounds[1,2]:continue
  s=trimesh.intersections.mesh_plane(m,[0,0,1],[0,0,z]);a=s[:,0,:2];d=s[:,1,:2]-a;rr=[]
  for deg in [22.5,45,67.5]:
   u=np.array([np.cos(np.deg2rad(deg)),np.sin(np.deg2rad(deg))]);c=u[0]*d[:,1]-u[1]*d[:,0]
   with np.errstate(divide='ignore',invalid='ignore'):t=(a[:,0]*u[1]-a[:,1]*u[0])/c;r0=(a[:,0]*d[:,1]-a[:,1]*d[:,0])/c
   vals=sorted(set(np.round(r0[(t>=0)&(t<=1)&(r0>0)&(r0<45)],5)))
   rr.append(vals)
  rows.append({'z':z,'radii_22_45_67':rr})
 out[part]={'central_vertex_heights':zs.tolist(),'sections':rows}
Path('/tmp/chanel_official_wiki/bands.json').write_text(json.dumps(out,indent=2))
