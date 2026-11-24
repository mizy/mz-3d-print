"""Small native fillets on user-visible exterior edges, not rail or mating interfaces."""
import FreeCAD as A,Part
from production_cams import S,B
V=A.Vector
def bbox(q,opt=True):
 b=q.optimalBoundingBox() if opt else q.BoundBox
 return (b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax)
def vd(a,b):return a.cut(b).Volume+b.cut(a).Volume
def same_bounds(a,b):
 assert max(abs(x-y) for x,y in zip(bbox(a),bbox(b)))<.0005
def origin_edge(x0,x1):
 return abs(x0-x1)<.00005
def apply(a,w,d,h):
 q=a[:];report=[]
 for i in (0,1):
  p=a[i]
  xs=(0,3.65) if i==0 else (w,w-3.65)
  ee=[]
  for e in p.Edges:
   x0,x1,y0,y1,z0,z1=bbox(e,False)
   if origin_edge(x0,x1) and min(abs(x0-t) for t in xs)<.0001 and z1-z0>8 and (max(abs(y0),abs(y1))<.0001 or max(abs(y0-d),abs(y1-d))<.0001):
    ee.append(e)
  assert len(ee)==4,len(ee)
  n=S(p.makeFillet(1.,ee));same_bounds(p,n)
  clips=(B(13.65,-.01,-.001,17.3,d+.01,10.001) if i==0 else B(w-17.3,-.01,-.001,w-13.65,d+.01,10.001))
  delta=vd(p.common(clips),n.common(clips));assert delta<.0005,delta
  report.append(dict(physical_edges=len(ee),radius_mm=1.,unchanged_rail_solid_region_difference_mm3=delta))
  q[i]=n
 t=a[-1];esh=[]
 for e in t.Edges:
  x0,x1,y0,y1,z0,z1=bbox(e,False)
  if max(abs(y0-3.),abs(y1-3.))<.00005 and z0>h-13.501 and e.Length>1.2:esh.append(e)
 assert len(esh)==7,len(esh)
 n=S(t.makeFillet(.45,esh));same_bounds(t,n)
 # The bounding boxes of trimmed NURBS corners can overbound. Verify actual solid outside the fillet zone.
 roi=B(4,2.999,h-14.1,w-4,6.45,h+1)
 outer_t=t.cut(roi);outer_n=n.cut(roi)
 delta=vd(outer_t,outer_n)
 assert delta<.0008,delta
 assert n.cut(t).Volume<.0008
 q[-1]=n
 return q,dict(frame_outside_end_corner_fillets=report,drawer_seven_face_side_top_and_U_edges_radius_mm=.45,
  drawer_untouched_region_difference_mm3=delta,outer_envelope_unchanged=True)
