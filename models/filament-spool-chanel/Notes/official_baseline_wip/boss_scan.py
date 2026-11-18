import trimesh,numpy as np,json
from pathlib import Path
out={}
for part in ['wide','narrow']:
 m=trimesh.load('/Users/miaozhuang/Downloads/bambulab_spool_'+part+'.stl');v=m.vertices.copy();m.vertices=np.c_[v[:,1],-v[:,2] if part=='wide' else v[:,2],m.bounds[1,0]-v[:,0] if part=='wide' else v[:,0]-m.bounds[0,0]];rows=[]
 for z in [2.51,2.6,2.8,2.99]:
  seg=trimesh.intersections.mesh_plane(m,[0,0,1],[0,0,z]);a=seg[:,0,:2];d=seg[:,1,:2]-a;rs=[]
  for ang in np.deg2rad(np.arange(0,360,.1)):
   u=np.array([np.cos(ang),np.sin(ang)]);den=u[0]*d[:,1]-u[1]*d[:,0];g=abs(den)>1e-12;t=np.full(len(a),np.nan);r=t.copy();t[g]=(a[g,0]*u[1]-a[g,1]*u[0])/den[g];r[g]=(a[g,0]*d[g,1]-a[g,1]*d[g,0])/den[g];ok=g&(t>=-1e-7)&(t<=1+1e-7)&(r>35)&(r<46);rs.append(max(r[ok]))
  rs=np.array(rs);large=rs>43.8;changes=np.where(large!=np.roll(large,1))[0]*.1;rows.append({'z':z,'outer_r_min':rs.min(),'max':rs.max(),'large_changes_deg':changes.tolist(),'radii':rs.tolist()});print(part,z,rs.min(),rs.max(),changes)
 out[part]=rows
Path('/tmp/chanel_official_native/boss_scan.json').write_text(json.dumps(out,indent=2))
