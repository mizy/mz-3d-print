import sys,cadquery as cq,json
from pathlib import Path
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
from reference_mesh import load,profile
from fit_wire import fit_wire
from paired_edges import pair_loft
D=Path('/tmp/chanel-interface-input/adaptive');p=json.load(open(D/'narrow_progress.json'))['parts'];low=23.95;join=p[0]['z0'];high=p[-1]['z1'];center=(.0015810415,-.0274228517)
def circle(r,z):return cq.Wire.makeCircle(r,cq.Vector(*center,z),cq.Vector(0,0,1))
m=load('narrow');first=fit_wire(profile(m,join,'narrow'),join,tol=.006)[0];last=fit_wire(profile(m,high,'narrow'),high,tol=.006)[0]
base=pair_loft(circle(29.7,low),first);print('BASE',base.isValid(),flush=True);faces=[]
for i in range(len(p)):
 s=cq.Shape.importBrep(str(D/f'narrow_{i:04d}.brep'));faces.extend(f for f in s.Faces() if f.BoundingBox().zlen>1e-5)
faces.extend(f for f in base.Faces() if f.BoundingBox().zlen>1e-5)
inner=cq.Solid.makeCylinder(27.5,high-low,cq.Vector(*center,low));faces.extend(f.reverse() for f in inner.Faces() if f.geomType()=='CYLINDER')
faces.append(cq.Face.makeFromWires(last,[circle(27.5,high)]));faces.append(cq.Face.makeFromWires(circle(29.7,low),[circle(27.5,low)]).reverse())
sew=BRepBuilderAPI_Sewing(1e-6,True,True,True,False)
for f in faces:sew.Add(f.wrapped)
print('SEWING',len(faces),flush=True);sew.Perform();s=cq.Shape.cast(sew.SewedShape());print('SHELLS',len(s.Shells()),flush=True);assert len(s.Shells())==1
sol=cq.Solid.makeSolid(s.Shells()[0]).fix();print('PIPE',sol.isValid(),sol.Volume(),len(sol.Faces()),flush=True);sol.exportBrep(str(D/'narrow_pipe_sewn.brep'));sol.exportStep(str(D/'narrow_pipe_sewn.step'),write_pcurves=False)
