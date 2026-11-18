"""Feature-based official wide lugs: editable arc/line sketches, cones, planar ramps and R3 fillets. No mesh at runtime."""
import cadquery as cq,json,math
from pathlib import Path
D=Path(__file__).parent
DEFAULTS={'wide_entry_fillet':3.0,'wide_bore_radius':31.4,'wide_inner_tube_top':37.25,'hub_radial_scale':1.0,'hub_axial_scale':1.0}

def _wire(name,z,k=1):
 edges=[]
 for e in json.loads((D/'wide_lock_sketches.json').read_text())[name]['edges']:
  pts=[]
  for x,y in e['pts']:
   r=math.hypot(x,y)
   # Restore the identified nominal bore circle, eliminating tessellation-biased sliver cylinders.
   if abs(r-31.4)<.01:x,y=x*31.4/r,y*31.4/r
   pts.append(cq.Vector(x*k,y*k,z))
  p=pts
  edges.append(cq.Edge.makeLine(p[0],p[-1]) if e['type']=='LINE' else cq.Edge.makeThreePointArc(*p))
 return cq.Wire.assembleEdges(edges)
def _prism(name,z,h,k=1):
 return cq.Solid.extrudeLinear(cq.Wire.makeCircle(33.3*k,cq.Vector(0,0,z),cq.Vector(0,0,1)),[_wire(name,z,k)],cq.Vector(0,0,h))
def _rev(points):return cq.Workplane('XZ').polyline(points).close().revolve(360,(0,0),(0,1)).val()
def _sector(lo,hi):
 pts=[(0,0)]+[(50*math.cos(math.radians(a)),50*math.sin(math.radians(a))) for a in [lo,(lo+hi)/2,hi]]
 return cq.Workplane('XY').polyline(pts).close().extrude(50).val()
def build_wide_lock(p=None):
 q=DEFAULTS.copy();q.update(p or {});p=q
 k=p['hub_radial_scale']*p['wide_bore_radius']/31.4;az=p['hub_axial_scale'];dz=p['wide_inner_tube_top']-37.25
 def prism(name,z,h):return _prism(name,(z+dz)*az,h*az,k)
 def rev(points):return _rev([(r*k,(z+dz)*az) for r,z in points])
 # constant sketches form vertical surfaces; cone profiles impose entry and top chamfers.
 tabs=prism('tabs',30.67,6.58).intersect(rev([(31.4,30.67),(29.9,32.17),(29.9,36.65),(30.5,37.25),(33.3,37.25),(33.3,30.67)]))
 cap_sketch=prism('cap',34.24906,3.00094)
 cap_ring=rev([(31.4,34.24906),(29.9,35.11509),(29.9,36.65),(30.5,37.25),(33.3,37.25),(33.3,34.24906)])
 pieces=[]
 for (lo,hi),plane in zip([(-45,45),(-135,-45),(135,225),(45,135)],json.loads((D/'wide_cap_planes.json').read_text())):
  nx,ny,nz=plane['normal'];n=cq.Vector(nx/k,ny/k,nz/az);length=n.Length;n=n.normalized();distance=(plane['distance']+nz*dz)/length;origin=n.multiply(distance);half=cq.Workplane(cq.Plane(origin=origin,normal=n.multiply(-1))).rect(250,250).extrude(150).val();piece=cap_ring.intersect(half)
  selected=[]
  for e in piece.Edges():
   types=[f.geomType() for f in piece.Faces() if any(ee.isSame(e) for ee in f.Edges())]
   adj=[f for f in piece.Faces() if any(ee.isSame(e) for ee in f.Edges())]
   if sorted(types)==['CONE','PLANE'] and e.Center().z<(35.2+dz)*az and any(f.geomType()=='PLANE' and abs(f.normalAt().dot(n))>.99999 for f in adj):selected.append(e)
  if p and p.get('debug'): print(lo,[(e.geomType(),e.Length(),e.Center().toTuple()) for e in selected],flush=True)
  if p and p.get('wide_entry_fillet',0)>0 and selected:
   piece=piece.fillet(p['wide_entry_fillet'],selected)
  pieces.append(piece.intersect(cap_sketch).intersect(_sector(lo,hi)))
 s=tabs.fuse(*pieces).clean()
 return s
if __name__=='__main__':
 s=build_wide_lock();print(s.isValid(),len(s.Solids()),len(s.Faces()),s.Volume(),flush=True);s.exportBrep(str(D/'wide_lock_WIP.brep'))
