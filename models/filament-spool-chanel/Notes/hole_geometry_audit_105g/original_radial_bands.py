import numpy as np,trimesh,json
from pathlib import Path
out={}
for part,name in [('wide','obj_1_料盘反面.stl'),('narrow','obj_2_料盘正面.stl')]:
 m=trimesh.load(Path('/Users/miaozhuang/Downloads/bambuLab_spool2.1_stls')/name,process=False);m.apply_translation(-np.r_[m.bounds[:,:2].mean(axis=0),m.bounds[0,2]]);rows=[]
 for z in [.2,.5,.8,1.,1.4,1.5,2,3,4,5,6,7,8,10,12,14,16,18,20,22,24]:
  seg=trimesh.intersections.mesh_plane(m,[0,0,1],[0,0,z]);a=seg[:,0,:2];d=seg[:,1,:2]-a;row={'z':z,'radii_at_angles':{}}
  for theta in [22.5,45,67.5]:
   u=np.array([np.cos(np.deg2rad(theta)),np.sin(np.deg2rad(theta))]);den=u[0]*d[:,1]-u[1]*d[:,0]
   with np.errstate(divide='ignore',invalid='ignore'):rr=(a[:,0]*d[:,1]-a[:,1]*d[:,0])/den;t=(a[:,0]*u[1]-a[:,1]*u[0])/den
   rr=np.sort(rr[(rr>0)&(rr<45)&(t>=0)&(t<=1)]);uni=[]
   for v in rr:
    if not uni or v-uni[-1]>.03:uni.append(float(v))
   row['radii_at_angles'][str(theta)]=uni
  rows.append(row)
 out[part]=rows;print(part,rows,flush=True)
Path('/tmp/chanel_hole_comparison/original_radial_bands.json').write_text(json.dumps(out,indent=2))
