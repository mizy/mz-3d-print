import cadquery as cq,trimesh,json
from pathlib import Path
r=Path(__file__).parent
for folder in ['lv','chanel']:
 p=r/folder/'parts'
 if not p.exists():continue
 rows=[]
 for f in p.glob('*.stl'):
  m=trimesh.load(f,force='mesh');s=cq.importers.importStep(str(f.with_suffix('.step'))).val();bb=s.BoundingBox()
  rows.append(dict(name=f.stem,cad_valid=s.isValid(),solids=len(s.Solids()),watertight=bool(m.is_watertight),mesh_positive=bool(m.volume>0),volume_mm3=float(m.volume),PLA_solid_equivalent_g=float(m.volume*.00124),bounds_mm=[[bb.xmin,bb.ymin,bb.zmin],[bb.xmax,bb.ymax,bb.zmax]]))
 (r/folder/'validation.json').write_text(json.dumps(rows,indent=2));print(folder,rows,flush=True)
