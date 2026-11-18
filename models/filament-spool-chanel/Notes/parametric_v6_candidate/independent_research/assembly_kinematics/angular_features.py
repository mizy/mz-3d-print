import sys,json,numpy as np
from pathlib import Path
from shapely.geometry import LineString,Polygon
sys.path.insert(0,'/Users/miaozhuang/Projects/mz-3d-print/models/filament-spool-chanel/Source/parametric_rebuild/research')
from reference_mesh import load,profile
out={}
for part,zs,c in [('wide',[30.8,31.4,32.5,34.5,35.5,36.5,37.2],[-.0273430863,.0010603425]),('narrow',[30.8,31.475,32.5,33.5,34.08],[.0015810415,-.0274228517])]:
 m=load(part);out[part]=[]
 for z in zs:
  a=profile(m,z,part)-c;line=LineString(a);r=[]
  for t in np.arange(0,360,.5):
   v=np.array([np.cos(np.deg2rad(t)),np.sin(np.deg2rad(t))]);cut=line.intersection(LineString([[0,0],v*35]));r.append(cut.distance(__import__('shapely').geometry.Point(0,0)))
  r=np.array(r);spans={}
  for lim,op in [(31.5,'gt'),(31.3,'lt'),(30.,'gt')]:
   yes=r>lim if op=='gt' else r<lim;starts=np.flatnonzero(yes & ~np.roll(yes,1));ends=np.flatnonzero(yes & ~np.roll(yes,-1));spans[f'{op}{lim}']={'starts':(starts*.5).tolist(),'ends':(ends*.5).tolist(),'all':bool(yes.all())}
  row={'z':z,'rmin':float(r.min()),'rmax':float(r.max()),'angular_spans':spans};out[part].append(row);print(part,z,row,flush=True)
Path('/tmp/chanel_parameter_audit/assembly/angular_features.json').write_text(json.dumps(out,indent=2))
