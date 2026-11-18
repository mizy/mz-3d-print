import sys,json,numpy as np
from pathlib import Path
sys.path.insert(0,'/Users/miaozhuang/Projects/mz-3d-print/models/filament-spool-chanel/Source/parametric_rebuild/research');from reference_mesh import load,profile
wm,nm=load('wide'),load('narrow');cw=np.array([-.0273430863,.0010603425]);cn=np.array([.0015810415,-.0274228517]);angs=np.arange(0,360,.25);ph=np.deg2rad(angs)
def radius(m,z,part,c):
 a=profile(m,z,part)-c;t=np.mod(np.rad2deg(np.arctan2(a[:,1],a[:,0])),360);r=np.linalg.norm(a,axis=1);ix=np.argsort(t);return np.interp(angs,t[ix],r[ix],period=360)
out=[]
for H in [71.,70.,69.,68.,67.,66.430113973]:
 Z=np.arange(max(30.85,H-37.20),min(34.08,H-30.85)+.001,.1);worst=np.full(180,-1e3)
 for zn in Z:
  w=radius(wm,H-zn,'wide',cw);n=radius(nm,zn,'narrow',cn)
  for th in range(180):worst[th]=max(worst[th],np.max(n[np.mod((th*4-np.arange(1440)),1440)]-w))
 row={'H':H,'sampled_z_count':len(Z),'angles_penetration_under_0_01':[int(x) for x in np.flatnonzero(worst<.01)],'minimum_radial_penetration_mm':float(worst.min()),'best_angle':int(worst.argmin()),'worst_penetration_by_degree':worst.tolist()};out.append(row);print({k:v for k,v in row.items() if k!='worst_penetration_by_degree'},flush=True)
Path('/tmp/chanel_parameter_audit/assembly/retention_probe.json').write_text(json.dumps({'method':'Original frozen mesh polar-vertex interpolation approximate radial screening; .25 degree polar grid, 1 degree rotation, .1 mm height sample; not exact CAD collision proof','results':out},indent=2))
