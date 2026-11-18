"""Rebuild native lock pipes from editable line/arc section parameters, no mesh import."""
from pathlib import Path
import json,cadquery as cq
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
from native_loft import pair_loft
R=Path(__file__).resolve().parent

def section(row):
 z=row['z'];edges=[]
 for e in row['edges']:
  a=cq.Vector(*e['start'],z);b=cq.Vector(*e['end'],z)
  if e['type']=='LINE':edges.append(cq.Edge.makeLine(a,b))
  else:edges.append(cq.Edge.makeThreePointArc(a,cq.Vector(*e['middle'],z),b))
 return cq.Wire.assembleEdges(edges)

def build_pipe(part,data):
 cfg=data[part];intervals=cfg['intervals'];wires={key:section(row) for key,row in cfg['sections'].items()};lo=21.95 if part=='wide' else 23.95;join=intervals[0]['z0'];hi=intervals[-1]['z1'];center=(-.0273430863,.0010603425) if part=='wide' else (.0015810415,-.0274228517)
 def circle(r,z):return cq.Wire.makeCircle(r,cq.Vector(*center,z),cq.Vector(0,0,1))
 faces=[]
 for interval in intervals:
  s=pair_loft(wires[str(interval['z0'])],wires[str(interval['z1'])]);assert s.isValid()
  for f in s.Faces():
   if f.BoundingBox().zlen>1e-5:faces.append(f.reverse() if part=='wide' else f)
 first=wires[str(join)];last=wires[str(hi)]
 if part=='narrow':
  base=pair_loft(circle(29.7,lo),first);assert base.isValid();faces.extend(f for f in base.Faces() if f.BoundingBox().zlen>1e-5)
  inner=cq.Solid.makeCylinder(27.5,hi-lo,cq.Vector(*center,lo));faces.extend(f.reverse() for f in inner.Faces() if f.geomType()=='CYLINDER')
  faces.extend([cq.Face.makeFromWires(last,[circle(27.5,hi)]),cq.Face.makeFromWires(circle(29.7,lo),[circle(27.5,lo)]).reverse()])
 else:
  floor=22.2650585
  guide=cq.Solid.extrudeLinear(first,[],cq.Vector(0,0,floor-join));base=cq.Solid.makeCylinder(31.39,floor-lo,cq.Vector(*center,lo));bore=guide.fuse(base).clean();assert bore.isValid()
  for f in bore.Faces():
   b=f.BoundingBox()
   if b.zlen<1e-5 and (abs(b.zmin-lo)<1e-5 or abs(b.zmin-join)<1e-5):continue
   faces.append(f.reverse())
  outer=cq.Solid.makeCylinder(33.3,hi-lo,cq.Vector(*center,lo));faces.extend(f for f in outer.Faces() if f.geomType()=='CYLINDER')
  faces.extend([cq.Face.makeFromWires(circle(33.3,hi),[last]),cq.Face.makeFromWires(circle(33.3,lo),[circle(31.39,lo)]).reverse()])
 sew=BRepBuilderAPI_Sewing(1e-6,True,True,True,False)
 for f in faces:sew.Add(f.wrapped)
 sew.Perform();s=cq.Shape.cast(sew.SewedShape());assert len(s.Shells())==1
 s=cq.Solid.makeSolid(s.Shells()[0]).fix();assert s.isValid() and len(s.Solids())==1
 return s
if __name__=='__main__':
 data=json.loads((R/'native_lock_sections.json').read_text());out=R/'build_output';out.mkdir(exist_ok=True)
 for part in ['wide','narrow']:
  s=build_pipe(part,data);s.exportBrep(str(out/f'{part}_native_pipe.brep'));print(part,s.isValid(),s.Volume(),len(s.Faces()),flush=True)
