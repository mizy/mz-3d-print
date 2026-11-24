"""Two shallow triangular internal marks on the official wide tube.
A fitted wrapped-triangle ceiling is represented by a small native loft;
exact cylinder and 45-degree cone bound the pocket. No runtime mesh loading.
This is a tolerance-based reconstruction, not an exact planar-prism feature.
"""
import math
import cadquery as cq
DEFAULTS={
 'hub_radial_scale':1.,'hub_axial_scale':1.,'wide_bore_radius':31.4,
 'wide_marker_depth':.35,'wide_marker_base_z':17.7,
 'wide_marker_inner_apex_z':21.89478,
 'wide_marker_angular_slope':26.26, # mm/radian, measured boundary fit
 'wide_marker_bevel_height_ratio':1.30338,
 'wide_marker_centers_deg':[42.,222.],
 'wide_marker_loft_stations':7,
}

def _scale(s,p):
 k=p['hub_radial_scale'];az=p['hub_axial_scale']
 if k==az:return s.scale(k)
 return s.transformGeometry(cq.Matrix([[k,0,0,0],[0,k,0,0],[0,0,az,0],[0,0,0,1]]))

def build_wide_markers(p=None):
 q=DEFAULTS.copy();q.update(p or {});r=q['wide_bore_radius'];d=q['wide_marker_depth'];zb=q['wide_marker_base_z'];zt=q['wide_marker_inner_apex_z'];slope=q['wide_marker_angular_slope'];bevel=q['wide_marker_bevel_height_ratio'];n=q['wide_marker_loft_stations']
 if not (d>0 and zt>zb and slope>0 and n>=3):raise ValueError('invalid marker parameters')
 # Loft covers a little more than the exposed pocket; exact clipping follows.
 amin=(zt-zb+.5)/slope;ri=r-.2;ro=r+d+.2;floor=zb-1.5
 pieces=[]
 for sign in [-1,1]:
  wires=[]
  for i in range(n):
   angle=sign*amin*i/(n-1)
   def top(rr):return zt-bevel*(rr-r)-slope*abs(angle)
   w=cq.Workplane('XZ').polyline([(ri,floor),(ro,floor),(ro,top(ro)),(ri,top(ri))]).close().val().rotate((0,0,0),(0,0,1),math.degrees(angle));wires.append(w)
  pieces.append(cq.Solid.makeLoft(wires,ruled=False))
 ceiling=pieces[0].fuse(pieces[1]);h=zt-zb+1
 radius_limit=cq.Solid.makeCylinder(r+d,h,cq.Vector(0,0,zb))
 bottom_cone=cq.Solid.makeCone(r,r+h,h,cq.Vector(0,0,zb))
 pocket=ceiling.intersect(radius_limit).intersect(bottom_cone).clean()
 return cq.Compound.makeCompound([_scale(pocket.rotate((0,0,0),(0,0,1),a),q) for a in q['wide_marker_centers_deg']])
