"""Rebuild native lock pipes from editable line/arc section parameters, no mesh import."""
from pathlib import Path
import json,cadquery as cq
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
from native_loft import pair_loft
from config import derived
from copy import deepcopy
R=Path(__file__).resolve().parent

def section(row):
 z=row['z'];edges=[]
 for e in row['edges']:
  a=cq.Vector(*e['start'],z);b=cq.Vector(*e['end'],z)
  if e['type']=='LINE':edges.append(cq.Edge.makeLine(a,b))
  else:edges.append(cq.Edge.makeThreePointArc(a,cq.Vector(*e['middle'],z),b))
 return cq.Wire.assembleEdges(edges)

def transform_controls(data,p):
 d=derived(p);result=deepcopy(data)
 for part,cfg in result.items():
  center=(-.0273430863,.0010603425) if part=='wide' else (.0015810415,-.0274228517)
  sections={}
  for row in cfg['sections'].values():
   row['z']*=d['az']
   for edge in row['edges']:
    for name in ['start','middle','end']:
     if name in edge:edge[name]=[center[i]+(edge[name][i]-center[i])*d['k'] for i in range(2)]
   sections[str(row['z'])]=row
  cfg['sections']=sections
  for interval in cfg['intervals']:
   interval['z0']*=d['az'];interval['z1']*=d['az']
 return result

def build_pipe(part,data,p):
 d=derived(p);k=d['k'];az=d['az'];data=transform_controls(data,p)
 cfg=data[part];intervals=cfg['intervals'];wires={key:section(row) for key,row in cfg['sections'].items()};lo=(21.95 if part=='wide' else 23.95)*az;join=intervals[0]['z0'];hi=intervals[-1]['z1'];center=(-.0273430863,.0010603425) if part=='wide' else (.0015810415,-.0274228517)
 def circle(r,z):return cq.Wire.makeCircle(r,cq.Vector(*center,z),cq.Vector(0,0,1))
 faces=[]
 for interval in intervals:
  s=pair_loft(wires[str(interval['z0'])],wires[str(interval['z1'])]);assert s.isValid()
  for f in s.Faces():
   if f.BoundingBox().zlen>1e-5:faces.append(f.reverse() if part=='wide' else f)
 first=wires[str(join)];last=wires[str(hi)]
 if part=='narrow':
  base=pair_loft(circle(29.7*k,lo),first);assert base.isValid();faces.extend(f for f in base.Faces() if f.BoundingBox().zlen>1e-5)
  inner=cq.Solid.makeCylinder(p['shaft_bore_radius'],hi-lo,cq.Vector(*center,lo));faces.extend(f.reverse() for f in inner.Faces() if f.geomType()=='CYLINDER')
  faces.extend([cq.Face.makeFromWires(last,[circle(p['shaft_bore_radius'],hi)]),cq.Face.makeFromWires(circle(29.7*k,lo),[circle(p['shaft_bore_radius'],lo)]).reverse()])
 else:
  floor=22.2650585*az
  guide=cq.Solid.extrudeLinear(first,[],cq.Vector(0,0,floor-join));base=cq.Solid.makeCylinder(31.39*k,floor-lo,cq.Vector(*center,lo));bore=guide.fuse(base).clean();assert bore.isValid()
  for f in bore.Faces():
   b=f.BoundingBox()
   if b.zlen<1e-5 and (abs(b.zmin-lo)<1e-5 or abs(b.zmin-join)<1e-5):continue
   faces.append(f.reverse())
  outer=cq.Solid.makeCylinder(31.4*k+p['wide_lock_wall_thickness'],hi-lo,cq.Vector(*center,lo));faces.extend(f for f in outer.Faces() if f.geomType()=='CYLINDER')
  faces.extend([cq.Face.makeFromWires(circle(31.4*k+p['wide_lock_wall_thickness'],hi),[last]),cq.Face.makeFromWires(circle(31.4*k+p['wide_lock_wall_thickness'],lo),[circle(31.39*k,lo)]).reverse()])
 sew=BRepBuilderAPI_Sewing(1e-6,True,True,True,False)
 for f in faces:sew.Add(f.wrapped)
 sew.Perform();s=cq.Shape.cast(sew.SewedShape());assert len(s.Shells())==1
 s=cq.Solid.makeSolid(s.Shells()[0]).fix();assert s.isValid() and len(s.Solids())==1
 return s
