from model_paths import MODELS_DIR
from pathlib import Path
import cadquery as cq,json,hashlib
R=MODELS_DIR;out={}
for part in ('wide','narrow'):
 p=R/f'LV_OPEN_ARCH_A_{part}.step';s=cq.importers.importStep(str(p)).val();assert s.isValid() and len(s.Solids())==1
 bad=[x for x in ('FACETED_BREP','TRIANGULATED_FACE_SET','TESSELLATED_SHAPE_REPRESENTATION') if x in p.read_text()];assert not bad
 bore=cq.Solid.makeCylinder(27.45,50);v=s.intersect(bore).Volume();assert v<1e-5
 b=s.BoundingBox();out[part]={'valid':True,'solids':1,'mesh_entities':bad,'shaft_54p9mm_interference_mm3':v,'bbox_mm':[b.xlen,b.ylen,b.zlen],'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()};print(part,out[part],flush=True)
(R/'export_checks.json').write_text(json.dumps(out,indent=2))
