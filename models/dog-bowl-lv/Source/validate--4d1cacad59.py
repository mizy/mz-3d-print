import trimesh,json,cadquery as cq
from pathlib import Path
R=Path(__file__).parent;results=[]
for p in (R/'parts').glob('*.stl'):
 m=trimesh.load(p,force='mesh');m.merge_vertices();m.remove_unreferenced_vertices();m.fix_normals();m.export(p)
 results.append(dict(file=p.name,watertight=bool(m.is_watertight),volume=float(m.volume),bounds=m.bounds.tolist()))
assert all(x['watertight'] and x['volume']>0 for x in results)
(R/'validation.json').write_text(json.dumps(results,indent=2))
print(results)
