from pathlib import Path
import cadquery as cq,json,hashlib,time,collections
p=Path('/Users/miaozhuang/Projects/mz-3d-print/models/filament-spool-chanel/Models/CHANEL_SOURCE21_parametric_v4.step');t=time.time();s=cq.importers.importStep(str(p)).val();parts=sorted(s.Solids(),key=lambda x:x.Center().x);report={'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'valid':s.isValid(),'solids':len(parts),'parts':{}}
for k,q,dx in zip(['wide','narrow'],parts,[110,-110]):
 q=q.translate((dx,0,0));b=q.BoundingBox();report['parts'][k]={'valid':q.isValid(),'volume_mm3':q.Volume(),'faces':len(q.Faces()),'surface_types':dict(collections.Counter(f.geomType() for f in q.Faces())),'bounds':[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]};q.exportBrep('/tmp/chanel_parameter_audit/baseline_'+k+'.brep')
report['seconds']=time.time()-t;Path('/tmp/chanel_parameter_audit/baseline.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
