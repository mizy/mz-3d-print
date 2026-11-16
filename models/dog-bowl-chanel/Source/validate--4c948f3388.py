from pathlib import Path
import cadquery as cq,json,trimesh
R=Path(__file__).parent;out=[]
for p in (R/'parts').glob('*.step'):
 s=cq.importers.importStep(str(p)).val();m=trimesh.load(p.with_suffix('.stl'),force='mesh');b=s.BoundingBox()
 out.append(dict(name=p.stem,cad_valid=s.isValid(),solids=len(s.Solids()),volume=s.Volume(),stl_watertight=bool(m.is_watertight),stl_positive=bool(m.volume>0),bounds=[[b.xmin,b.ymin,b.zmin],[b.xmax,b.ymax,b.zmax]]))
(R/'validation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
