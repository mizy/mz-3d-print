"""V17: relocate only the radius of the existing double-sided paddle journal lands."""
import FreeCAD as A, Part
V=A.Vector
def tighten_journal(panel,diameter=2.0):
 if not (2.0<=diameter<=2.36):raise ValueError("paddle journal diameter must be 2.00–2.36 mm")
 if diameter==2.36:return panel.copy(), dict(diameter_mm=diameter,added_volume_mm3=0.0)
 X=V(1,0,0); P=V(0,125.,97.83)
 def B(x,x1,y,y1,z,z1):return Part.makeBox(x1-x,y1-y,z1-z,V(x,y,z))
 def cyl(x,x1,r):return Part.makeCylinder(r,x1-x,V(x,P.y,P.z),X)
 def C(a,b):return a.common(b).Volume
 spans=[]
 for f in panel.Faces:
  g=f.Surface
  if type(g).__name__=='Cylinder' and abs(g.Radius-1.18)<1e-6 and abs(g.Axis.x)>.999:
   bb=f.BoundBox
   if 172.49<=bb.XMin<=bb.XMax<=177.51 and 123.7<bb.YMin<bb.YMax<126.3:
    spans.append((round(bb.XMin,6),round(bb.XMax,6)))
 assert sorted(set(spans))==[(172.5,174.13),(175.87,177.5)],spans
 # Fixed original service air cuts translated to canonical H100 global Y/Z.
 keep=[B(171,179,P.y+.56,P.y+1.68,P.z-.64,P.z+.64).rotated(P,X,120),
       B(171,179,P.y+.48,P.y+3.67,P.z+1.03,P.z+2.21),
       cyl(174.13,175.87,1.70)]
 r=diameter/2.
 stock=[cyl(x,x1,1.205).cut(cyl(x-.01,x1+.01,r)).cut(keep) for x,x1 in sorted(set(spans))]
 side=panel.multiFuse(stock).removeSplitter()
 assert side.isValid() and len(side.Solids)==1
 side=side.Solids[0]
 add=side.cut(panel); loss=panel.cut(side).Volume
 q=max(C(add,k) for k in keep)
 assert loss<.0005 and q<.0005 and add.Volume>.001,(q,loss,add.Volume)
 lands=[]
 for f in side.Faces:
  g=f.Surface
  if type(g).__name__=='Cylinder' and abs(g.Radius-r)<1e-6 and abs(g.Axis.x)>.999:
   bb=f.BoundBox
   if 172.49<=bb.XMin<=bb.XMax<=177.51 and 123.7<bb.YMin<bb.YMax<126.3:
    lands.append((round(bb.XMin,6),round(bb.XMax,6),round(f.Area,6)))
 assert len(lands)==2,lands
 return side,dict(diameter_mm=diameter,shaft_diameter_mm=2.,diametral_clearance_mm=diameter-2,
  added_volume_mm3=add.Volume,unintended_removed_volume_mm3=loss,added_material_in_release_keepouts_mm3=q,
  measured_cylindrical_lands=[dict(x_from_to_mm=[a,b],face_area_mm2=c) for a,b,c in sorted(lands)])
