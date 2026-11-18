import cadquery as cq,numpy as np,json,hashlib,sys,time
from pathlib import Path
from shapely.geometry import LineString
from shapely.ops import unary_union
P=Path('/Users/miaozhuang/Projects/mz-3d-print/models/filament-spool-chanel')
sys.path.insert(0,str(P/'Source/parametric_rebuild/research'))
from reference_mesh import load,profile
src=P/'Source/parametric_v6_candidate/build_output/CHANEL_SOURCE21_parametric_v6_candidate.step'
D=P/'Notes/parametric_v6_candidate/independent_research'
out={'source':str(src),'bytes':src.stat().st_size,'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'method':'Independent final STEP reimport; section CAD edges sampled at <=0.005 mm arc length and compared by symmetric planar Hausdorff to frozen source mesh plane-polygonize reference; 10 selected heights, not all-surface/physical assembly validation.'}
s=cq.importers.importStep(str(src)).val();out['valid']=s.isValid();out['solids']=len(s.Solids());out['faces']=len(s.Faces());assert out['valid'] and out['solids']==2
out['parts']={}
for so in s.Solids():
 bb=so.BoundingBox();part='wide' if bb.zmax>40 else 'narrow';dx=-110.013 if bb.xmin<0 else 110.013
 local=so.translate((-dx,0,0));m=load(part)
 row={'assembly_translation_x':dx,'valid':so.isValid(),'faces':len(so.Faces()),'volume_mm3':so.Volume(),'bbox':[bb.xmin,bb.xmax,bb.ymin,bb.ymax,bb.zmin,bb.zmax],'checks':[]}
 zs=[31.275,31.425,35.425,36.825,37.225] if part=='wide' else [31.475,31.675,32.65,33.375,34.085]
 for z in zs:
  sec=cq.Workplane('XY').newObject([local]).section(z).val();lines=[]
  for e in sec.Edges():
   pts=e.sample(max(3,int(e.Length()/.005)+2))[0];a=np.array([[v.x,v.y] for v in pts]);r=np.linalg.norm(a,axis=1)
   if (part=='wide' and r.max()<32.5) or (part=='narrow' and r.min()>28.8 and r.max()<32):lines.append(LineString(a))
  boundary=unary_union(lines);ref=LineString(profile(m,z,part));assert not boundary.is_empty
  err=boundary.hausdorff_distance(ref);check={'z':z,'hausdorff_mm':err,'cad_selected_edges':len(lines)};row['checks'].append(check);print(part,check,flush=True)
 row['max_sampled_error_mm']=max(c['hausdorff_mm'] for c in row['checks']);out['parts'][part]=row
out['all_selected_sections_within_0_03_mm']=all(r['max_sampled_error_mm']<=.03 for r in out['parts'].values())
(D/'final_export_independent_readback.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2),flush=True)
