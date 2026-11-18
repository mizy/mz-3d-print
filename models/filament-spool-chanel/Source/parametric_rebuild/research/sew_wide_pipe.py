import sys,cadquery as cq,json
from pathlib import Path
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
from reference_mesh import load,profile
from fit_wire import fit_wire
D=Path('/tmp/chanel-interface-input/adaptive');p=json.load(open(D/'wide_progress.json'))['parts'];low=21.95;join=p[0]['z0'];high=p[-1]['z1'];floor=22.2650585;center=(-.0273430863,.0010603425)
def circle(r,z):return cq.Wire.makeCircle(r,cq.Vector(*center,z),cq.Vector(0,0,1))
m=load('wide');first=fit_wire(profile(m,join,'wide'),join,tol=.006)[0];last=fit_wire(profile(m,high,'wide'),high,tol=.006)[0]
guide=cq.Solid.extrudeLinear(first,[],cq.Vector(0,0,floor-join));base=cq.Solid.makeCylinder(31.39,floor-low,cq.Vector(*center,low));bottom_bore=guide.fuse(base).clean();print('LOWER BORE',bottom_bore.isValid(),len(bottom_bore.Solids()),flush=True);assert bottom_bore.isValid()
faces=[]
for i in range(len(p)):
 s=cq.Shape.importBrep(str(D/f'wide_{i:04d}.brep'));faces.extend(f.reverse() for f in s.Faces() if f.BoundingBox().zlen>1e-5)
for f in bottom_bore.Faces():
 b=f.BoundingBox()
 if b.zlen<1e-5 and (abs(b.zmin-low)<1e-5 or abs(b.zmin-join)<1e-5):continue
 faces.append(f.reverse())
outer=cq.Solid.makeCylinder(33.3,high-low,cq.Vector(*center,low));faces.extend(f for f in outer.Faces() if f.geomType()=='CYLINDER')
faces.append(cq.Face.makeFromWires(circle(33.3,high),[last]));faces.append(cq.Face.makeFromWires(circle(33.3,low),[circle(31.39,low)]).reverse())
sew=BRepBuilderAPI_Sewing(1e-6,True,True,True,False)
for f in faces:sew.Add(f.wrapped)
print('SEWING',len(faces),flush=True);sew.Perform();s=cq.Shape.cast(sew.SewedShape());print('SHELLS',len(s.Shells()),flush=True);assert len(s.Shells())==1
sol=cq.Solid.makeSolid(s.Shells()[0]).fix();print('PIPE',sol.isValid(),sol.Volume(),len(sol.Faces()),flush=True);sol.exportBrep(str(D/'wide_pipe_sewn.brep'));sol.exportStep(str(D/'wide_pipe_sewn.step'),write_pcurves=False)
