import cadquery as cq,trimesh,numpy as np,json,time
from pathlib import Path
p=Path('/Users/miaozhuang/Projects/mz-3d-print/models/filament-spool-chanel/Models/CHANEL_105g_KEEP_CORE.step');D=Path('/tmp/chanel_step_openedge_audit');s=cq.importers.importStep(str(p)).val();print('STEP',s.isValid(),len(s.Solids()),flush=True);r={'valid':s.isValid(),'solids':[]}
for i,b in enumerate(s.Solids()):
 box=b.BoundingBox();x={'valid':b.isValid(),'shells':len(b.Shells()),'bbox':[box.xlen,box.ylen,box.zlen],'center':[box.center.x,box.center.y,box.center.z],'volume':b.Volume(),'faces':len(b.Faces())};print('BREP',i,x,flush=True)
 v,f=b.tessellate(.01,.1);m=trimesh.Trimesh(vertices=np.array([[z.x,z.y,z.z] for z in v]),faces=np.array(f),process=True);counts=np.bincount(m.edges_unique_inverse);x.update(mesh_faces=len(m.faces),watertight=m.is_watertight,boundary_edges=int(np.sum(counts==1)),nonmanifold_edges=int(np.sum(counts>2)),winding=m.is_winding_consistent);print('MESH',i,x,flush=True);m.export(D/f'half_{i}.stl');r['solids'].append(x);(D/'report.json').write_text(json.dumps(r,indent=2))
