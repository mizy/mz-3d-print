"""Native arc/line section loft with independent held-out sections, never tessellated CAD."""
from pathlib import Path
import sys,json,time,math
import numpy as np,cadquery as cq
from fit_wire import fit_wire
from paired_edges import pair_loft
from reference_mesh import load,profile
from shapely.geometry import LineString,MultiLineString
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.gp import gp_Pln,gp_Pnt,gp_Dir
D=Path('/tmp/chanel-interface-input/adaptive');D.mkdir(exist_ok=True)
part=sys.argv[1];mesh=load(part);cache={};adjustments=[];results=[];parts=[]
TOL=.03

def get(z):
 key=round(z,9)
 if key in cache:return cache[key]
 last=None
 for shift in [0,1e-7,-1e-7,1e-6,-1e-6]:
  try:xy=profile(mesh,z+shift,part);break
  except Exception as e:last=e
 else:raise last
 if shift:adjustments.append({'requested_z':z,'sampled_z':z+shift})
 w,_=fit_wire(xy,z,tol=.006)
 cache[key]=(w,LineString(xy));return cache[key]

def error(s,z):
 op=BRepAlgoAPI_Section(s.wrapped,gp_Pln(gp_Pnt(0,0,z),gp_Dir(0,0,1)),False);op.Build();cross=cq.Shape.cast(op.Shape());lines=[]
 for e in cross.Edges():
  pts=e.sample(max(8,int(e.Length()/.02)+1))[0];lines.append([(p.x,p.y) for p in pts])
 if not lines:return 999.
 ref=get(z)[1];return MultiLineString(lines).hausdorff_distance(ref)

def build(a,b,depth=0):
 start=time.time();mid=(a+b)/2
 try:
  s=pair_loft(get(a)[0],get(b)[0]);valid=s.isValid();err=error(s,mid) if valid else 999.
 except Exception as e:
  valid=False;err=999.;print('ERROR',part,a,b,str(e),flush=True)
 if not valid or err>TOL:
  print('SPLIT',part,a,b,valid,err,flush=True)
  if depth>=6 or b-a<.006:raise RuntimeError(f'Unvalidated segment {a}..{b}: {err}')
  build(a,mid,depth+1);build(mid,b,depth+1);return
 idx=len(parts);s.exportBrep(str(D/f'{part}_{idx:04d}.brep'));parts.append(s);results.append({'z0':a,'z1':b,'midpoint_error_mm':err,'faces':len(s.Faces())});print('PASS',part,a,b,err,len(s.Faces()),time.time()-start,flush=True)
 (D/f'{part}_progress.json').write_text(json.dumps({'parts':results,'sampling_offsets':adjustments},indent=2))

start,end=(30.,37.2650566101-.0001) if part=='wide' else (30.8,34.1130523682-.0001)
progress=D/f'{part}_progress.json'
if progress.exists():
 prev=json.loads(progress.read_text());results=prev['parts'];adjustments=prev['sampling_offsets'];parts=[cq.Shape.importBrep(str(D/f'{part}_{i:04d}.brep')) for i in range(len(results))];start=results[-1]['z1'];print('RESUME',part,start,len(parts),flush=True)
levels=list(np.arange(start,end,.2))+[end]
for a,b in zip(levels,levels[1:]):build(float(a),float(b))
print('ALL_SEGMENTS_VALID',len(parts),sum(len(s.Faces()) for s in parts),flush=True)
# Preserve experimental validated components first; fuse is a distinct verification stage.
compound=cq.Compound.makeCompound(parts);compound.exportBrep(str(D/f'{part}_validated_segments.brep'))
print('FUSING',flush=True);fused=parts[0].fuse(*parts[1:]).clean();print('FUSED',fused.isValid(),len(fused.Solids()),len(fused.Faces()),flush=True)
assert fused.isValid() and len(fused.Solids())==1
fused.exportBrep(str(D/f'{part}_lock_tool.brep'));fused.exportStep(str(D/f'{part}_lock_tool.step'),write_pcurves=False)
(D/f'{part}_validation.json').write_text(json.dumps({'tolerance_mm':TOL,'max_midpoint_error_mm':max(r['midpoint_error_mm'] for r in results),'parts':results,'sampling_offsets':adjustments,'fused_valid':fused.isValid(),'solids':len(fused.Solids())},indent=2))
