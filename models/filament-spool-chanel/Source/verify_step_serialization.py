from pathlib import Path
import sys,json,re,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parent/'deps'))
import trimesh,numpy as np
out={}
for k in ['wide','narrow']:
 p=Path(__file__).parent/f'CHANEL_SOURCE21_{k}.step';src=p.with_name(f'CHANEL_SOURCE21_{k}_FROZEN.obj');m=trimesh.load(src,process=False);nv=len(m.vertices);nf=len(m.faces);pv=[];ff=[]
 for line in p.open():
  if '=CARTESIAN_POINT' in line:
   idx=int(line.split('=')[0][1:])
   if idx>=100:
    assert idx==100+len(pv);pv.append([float(x) for x in line.split('(',2)[2].split(')')[0].split(',')])
  elif '=POLY_LOOP' in line:
   ff.append([int(x[1:])-100 for x in line.split('(',2)[2].split(')')[0].split(',')])
 assert len(pv)==nv and len(ff)==nf
 assert np.array_equal(np.array(pv),np.asarray(m.vertices)) and np.array_equal(np.array(ff),np.asarray(m.faces))
 out[k]={'vertices':nv,'triangles':nf,'step_coordinates_bitwise_equal_to_loaded_OBJ_float64':True,'triangle_indices_identical':True,'coordinate_serialization_error_mm':0,'step_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'limitation':'This verifies geometry serialization, not CAD-kernel reimport or physical fit.'}
 print(k,out[k],flush=True)
(Path(__file__).parent/'STEP_SERIALIZATION_VALIDATION.json').write_text(json.dumps(out,indent=2))
