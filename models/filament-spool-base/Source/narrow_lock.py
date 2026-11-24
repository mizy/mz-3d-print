"""Analytic reverse-engineered official narrow bayonet teeth and retention bumps.
No STL/BRep loaded at runtime. Independent verification lives in check_narrow_lock.py.
Returned compound contains 8 separate additions; fuse its Solids() to inner tube.
"""
import math
import cadquery as cq
DEFAULTS={
 'hub_radial_scale':1.,'hub_axial_scale':1.,
 'narrow_inner_tube_outer_radius':29.7,'narrow_inner_tube_top':34.1,
 'narrow_tooth_radius':31.1,'narrow_tooth_fillet':.3,
 'narrow_tooth_fillet_center_z':32.230940108,'narrow_tooth_top_chamfer_start':33.3,
 'narrow_tooth_sector_pairs':[[-16.,24.5],[85.,107.5]],
 'narrow_bump_radius':30.35,'narrow_bump_fillet':1.2,
 'narrow_bump_crown_angles':[28.793708,29.879782],
 'narrow_bump_left_tangent_angle':-9.50818634,
 'narrow_bump_right_tangent_angle':60.231624,
 'narrow_bump_rotations':[0.,83.1,180.,263.1],
 'narrow_bump_ramp_start_z':32.024264812,
}

def _point(c,r,a):
 a=math.radians(a);return(c[0]+r*math.cos(a),c[1]+r*math.sin(a))
def _arc_mid(c,r,a,b):return _point(c,r,(a+b)/2)
def _line_circle(pt,tangent_deg,rr):
 a=math.radians(tangent_deg);d=(math.cos(a),math.sin(a));b=pt[0]*d[0]+pt[1]*d[1];c=pt[0]**2+pt[1]**2-rr**2
 roots=[-b+math.sqrt(b*b-c),-b-math.sqrt(b*b-c)]
 t=min(roots,key=abs);return(pt[0]+t*d[0],pt[1]+t*d[1])
def _scaled(s,p):
 k=p['hub_radial_scale'];az=p['hub_axial_scale']
 if k==az:return s.scale(k)
 return s.transformGeometry(cq.Matrix([[k,0,0,0],[0,k,0,0],[0,0,az,0],[0,0,0,1]]))

def tooth_sector(a,b,p):
 rb=p['narrow_inner_tube_outer_radius'];rt=p['narrow_tooth_radius'];f=p['narrow_tooth_fillet'];zc=p['narrow_tooth_fillet_center_z'];rc=rt-f
 r_t=rc+f*.5;z_t=zc-f*math.sqrt(3)/2;zb=z_t-(r_t-rb)/math.sqrt(3)
 zch=p['narrow_tooth_top_chamfer_start'];zt=p['narrow_inner_tube_top'];r_top=rt-(zt-zch)
 if not (rb<r_top<=rt and zb<zc<zch<zt):raise ValueError('invalid tooth radial/axial profile')
 # Slight overlap with base tube is deliberate and internal only.
 w=cq.Workplane('XZ').moveTo(rb-.02,zb).lineTo(rb,zb).lineTo(r_t,z_t).threePointArc((rc+f*math.cos(math.pi/6),zc-f*.5),(rt,zc)).lineTo(rt,zch).lineTo(r_top,zt).lineTo(rb-.02,zt).close()
 return w.revolve(b-a,(0,0),(0,1)).val().rotate((0,0,0),(0,0,1),a)

def retention_bump(p):
 rb=p['narrow_inner_tube_outer_radius'];rt=p['narrow_bump_radius'];f=p['narrow_bump_fillet'];aa,bb=p['narrow_bump_crown_angles'];la=p['narrow_bump_left_tangent_angle'];ra=p['narrow_bump_right_tangent_angle'];z0=p['narrow_bump_ramp_start_z'];zt=p['narrow_inner_tube_top']
 c1=_point((0,0),rt-f,aa);c2=_point((0,0),rt-f,bb)
 c=_point(c1,f,la);d=_point((0,0),rt,aa);e=_point((0,0),rt,bb);ff=_point(c2,f,ra)
 a=_line_circle(c,la+90,rb-.02);b=_line_circle(ff,ra+90,rb-.02)
 # Closing chord is inside the base tube, so no chord replaces an exposed arc.
 wire=cq.Workplane('XY').moveTo(*a).lineTo(*c).threePointArc(_arc_mid(c1,f,la,aa),d).threePointArc(_point((0,0),rt,(aa+bb)/2),e).threePointArc(_arc_mid(c2,f,bb,ra),ff).lineTo(*b).close()
 prism=wire.extrude(zt-z0).translate((0,0,z0)).val()
 # 45 degree conical ramp clipped against a fixed extruded rounded sketch.
 limiter=cq.Solid.makeCone(rb,rb+(zt-z0),zt-z0,cq.Vector(0,0,z0))
 return prism.intersect(limiter)

def build_narrow_lock(p=None):
 q=DEFAULTS.copy();q.update(p or {});pieces=[]
 for a,b in q['narrow_tooth_sector_pairs']:
  for extra in (0,180):pieces.append(tooth_sector(a+extra,b+extra,q))
 bump=retention_bump(q)
 for a in q['narrow_bump_rotations']:pieces.append(bump.rotate((0,0,0),(0,0,1),a))
 return cq.Compound.makeCompound([_scaled(s,q) for s in pieces])
