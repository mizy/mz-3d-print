import cadquery as cq,json,numpy as np,collections,re
from pathlib import Path
from shapely.geometry import LineString
from shapely.ops import unary_union
D=Path('/tmp/chanel_parameter_audit');out={}
def boundary(s,z,part):
 ss=cq.Workplane('XY').newObject([s]).section(z).val();lines=[]
 for e in ss.Edges():
  pts=e.sample(max(3,int(e.Length()/.02)+2))[0];a=np.array([[v.x,v.y] for v in pts]);r=np.linalg.norm(a,axis=1)
  if (part=='wide' and r.max()<32.5) or (part=='narrow' and r.min()>28.8 and r.max()<32):lines.append(LineString(a))
 return unary_union(lines)
for part,zs in [('wide',[22.5,30.1,32.225,35.425,37.225]),('narrow',[24.1,31.675,32.65,34.085])]:
 a=cq.importers.importBrep(str(D/f'baseline_{part}.brep')).val();b=cq.importers.importBrep(str(D/f'thick_variant/{part}_complete.brep')).val();rows=[]
 for z in zs:
  x,y=boundary(a,z,part),boundary(b,z,part);err=x.hausdorff_distance(y);assert not x.is_empty and not y.is_empty;rows.append({'z':z,'error_mm':err});print(part,z,err,flush=True)
 out[part]=rows
p=D/'thick_variant/CHANEL_SOURCE21_parametric_v5.step';t=p.read_text();c=collections.Counter(re.findall(r'#\d+\s*=\s*([A-Z][A-Z_0-9]*)\s*\(',t));out['step_types']={k:c[k] for k in ['MANIFOLD_SOLID_BREP','ADVANCED_FACE','FACETED_BREP','CYLINDRICAL_SURFACE','CONICAL_SURFACE','B_SPLINE_SURFACE_WITH_KNOTS']};(D/'thick_variant_independent.json').write_text(json.dumps(out,indent=2));print(out,flush=True)
