import cadquery as cq,json,sys,time
from pathlib import Path
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
D=Path('/tmp/chanel-interface-input/adaptive');part=sys.argv[1];p=json.load(open(D/f'{part}_progress.json'))['parts'];lo=p[0]['z0'];hi=p[-1]['z1'];sew=BRepBuilderAPI_Sewing(1e-6,True,True,True,False);count=0
for i in range(len(p)):
 s=cq.Shape.importBrep(str(D/f'{part}_{i:04d}.brep'))
 for f in s.Faces():
  b=f.BoundingBox()
  if b.zlen<1e-5 and abs(b.zmin-lo)>1e-5 and abs(b.zmax-hi)>1e-5:continue
  sew.Add(f.wrapped);count+=1
print('SEWING',count,flush=True);sew.Perform();s=cq.Shape.cast(sew.SewedShape());print('SEWED',s.ShapeType(),len(s.Shells()),len(s.Faces()),flush=True)
assert len(s.Shells())==1
sol=cq.Solid.makeSolid(s.Shells()[0]);print('SOLID',sol.isValid(),sol.Volume(),len(sol.Faces()),flush=True);sol=sol.fix();assert sol.isValid();sol.exportBrep(str(D/f'{part}_sewn_lock_tool.brep'));sol.exportStep(str(D/f'{part}_sewn_lock_tool.step'),write_pcurves=False)
print('SAVED',flush=True)
