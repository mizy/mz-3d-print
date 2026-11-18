import trimesh,numpy as np,json
from pathlib import Path
out={}
for part in ['wide','narrow']:
 m=trimesh.load('/Users/miaozhuang/Downloads/bambulab_spool_'+part+'.stl');v=m.vertices.copy();m.vertices=np.c_[v[:,1],v[:,2],m.bounds[1,0]-v[:,0] if part=='wide' else v[:,0]-m.bounds[0,0]];rows=[]
 for z in [0.05,.2,.4,1,2,2.3,2.5,2.65,2.7,2.75,2.8,2.9,3,3.1,3.2,3.4,3.55]:
  s=trimesh.intersections.mesh_plane(m,[0,0,1],[0,0,z]);a=s[:,0,:2];d=s[:,1,:2]-a;u=np.array([2**-.5,2**-.5]);den=u[0]*d[:,1]-u[1]*d[:,0];g=abs(den)>1e-12;t=np.full(len(a),np.nan);r=t.copy();t[g]=(a[g,0]*u[1]-a[g,1]*u[0])/den[g];r[g]=(a[g,0]*d[g,1]-a[g,1]*d[g,0])/den[g];ok=g&(t>=-1e-7)&(t<=1+1e-7)&(r>0);rows.append([z,sorted(set(np.round(r[ok],5)))])
 out[part]=rows
Path('/tmp/chanel_official_native/radial.json').write_text(json.dumps(out,indent=2));print(out)
