from pathlib import Path
import sys,json,re,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parent/'deps'))
import trimesh,numpy as np
R=Path(__file__).parent;out={}
for k in ['wide','narrow']:
 p=R/f'CHANEL_SOURCE21_{k}.step';src=R/f'CHANEL_SOURCE21_{k}_FROZEN.obj';m=trimesh.load(src,process=False);points={};faces=[]
 for line in p.open():
  if '=CARTESIAN_POINT' in line:
   idx=int(line.split('=')[0][1:]);points[idx]=[float(x) for x in line.split('(',2)[2].split(')')[0].split(',')]
  elif '=POLY_LOOP' in line:faces.append([int(x[1:]) for x in line.split('(',2)[2].split(')')[0].split(',')])
 tri=np.array([[points[j] for j in f] for f in faces]);ref=np.asarray(m.vertices)[np.asarray(m.faces)]
 assert tri.shape==ref.shape and np.array_equal(tri,ref)
 out[k]={'triangles':len(faces),'all_triangle_coordinates_bitwise_equal_float64':True,'geometry_serialization_error_mm':0,'step_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'limitation':'Geometry serialization only; CAD-kernel reimport is checked separately.'}
 print(k,out[k],flush=True)
(R/'STEP_SERIALIZATION_VALIDATION.json').write_text(json.dumps(out,indent=2))
