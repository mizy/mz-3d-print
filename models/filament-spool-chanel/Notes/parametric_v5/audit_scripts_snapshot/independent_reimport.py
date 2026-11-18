import cadquery as cq,json,hashlib,time
from pathlib import Path
p=Path('/tmp/chanel_parameter_audit/thick_variant/CHANEL_SOURCE21_parametric_v5.step');t=time.time();s=cq.importers.importStep(str(p)).val();parts=sorted(s.Solids(),key=lambda q:q.Center().x);r={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'valid':s.isValid(),'solids':len(parts),'parts':[]}
for q in parts:
 b=q.BoundingBox();r['parts'].append({'valid':q.isValid(),'volume':q.Volume(),'bounds_size':[b.xlen,b.ylen,b.zlen],'faces':len(q.Faces())})
r['seconds']=time.time()-t;Path('/tmp/chanel_parameter_audit/independent_step_readback.json').write_text(json.dumps(r,indent=2));print(r,flush=True)
