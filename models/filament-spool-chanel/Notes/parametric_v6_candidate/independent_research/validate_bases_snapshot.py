import sys,json,time
import cadquery as cq,numpy as np
from pathlib import Path
from shapely.geometry import LineString
from shapely.ops import unary_union
sys.path.insert(0,'/tmp/chanel-interface-input');from reference_mesh import load,profile
D=Path('/tmp/chanel_compact_v6');report={}
for part in ['narrow','wide']:
 p=D/f'{part}_analytic_base.brep'
 if not p.exists():continue
 s=cq.importers.importBrep(str(p)).val();m=load(part);rows=[]
 zs=list(np.arange(30.825,34.1,.05))+[24.1,27,30,30.8,34.1128] if part=='narrow' else list(np.arange(30.625,37.24,.05))+[22.1,22.5,24,28,30,37.2648]
 for z in sorted(zs):
  ref=LineString(profile(m,float(z),part));sec=cq.Workplane('XY').newObject([s]).section(float(z)).val();lines=[]
  for e in sec.Edges():
   pts=e.sample(max(3,int(e.Length()/.02)+2))[0];a=np.array([[v.x,v.y] for v in pts]);r=np.linalg.norm(a,axis=1)
   if (part=='wide' and r.max()<32.5) or (part=='narrow' and r.min()>28.8 and r.max()<32):lines.append(LineString(a))
  curve=unary_union(lines);err=curve.hausdorff_distance(ref);rows.append({'z':float(z),'error_mm':err});print(part,z,err,flush=True)
 report[part]={'max_error_mm':max(x['error_mm'] for x in rows),'sections':rows,'valid':s.isValid(),'faces':len(s.Faces()),'solids':len(s.Solids())};(D/'base_validation.json').write_text(json.dumps(report,indent=2))
print('DONE',json.dumps({k:{a:b for a,b in v.items() if a!='sections'} for k,v in report.items()}),flush=True)
