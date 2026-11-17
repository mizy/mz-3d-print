import json,sys,time
from pathlib import Path
import cadquery as cq
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent/'deps'))
import trimesh
p=Path(sys.argv[1]);t=time.time();report=json.loads(Path(str(p)+'.validation.json').read_text());m=trimesh.load(report['source'],force='mesh',process=Path(report['source']).suffix.lower()!='.obj')
print('REIMPORT',str(p),flush=True);r=cq.importers.importStep(str(p)).val();print('CHECK',flush=True);vol=r.Volume();b=r.BoundingBox();bb=np.array([[b.xmin,b.ymin,b.zmin],[b.xmax,b.ymax,b.zmax]])
report.update(valid=r.isValid(),solids=len(r.Solids()),step_volume_mm3=vol,volume_difference_mm3=float(vol-m.volume),step_bounds_mm=bb.tolist(),max_bounds_difference_mm=float(np.max(np.abs(bb-m.bounds))),validation_elapsed_s=time.time()-t)
assert report['valid'] and report['solids']==1 and abs(vol-m.volume)<max(1e-4,abs(m.volume)*1e-8) and report['max_bounds_difference_mm']<1e-5,report
report['validated']=True;Path(str(p)+'.validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
