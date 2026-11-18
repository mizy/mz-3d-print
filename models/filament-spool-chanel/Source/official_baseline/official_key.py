"""Wide locating key: drafted side, two R0.5 rounds, bevel and cylindrical outer tip.
Right-handed official wide frame: key on negative Y. No mesh input.
"""
import math,cadquery as cq
DEFAULTS={'bottom_z':2.5,'top_z':7.8,'outer_tip_radius':43.7,'radial_overlap_start':39.5,'bottom_half_width':1.9551043,'side_draft_deg':6.,'shoulder_tangent_z':6.81349945,'bevel_normal_deg':48.,'round_radius':.5}
def build_key(p=None):
 p=dict(DEFAULTS if p is None else p)
 if set(p)!=set(DEFAULTS):raise ValueError('Unknown/missing locating-key parameter')
 if not all(isinstance(v,(int,float)) and math.isfinite(v) and v>0 for v in p.values()):raise ValueError('Key dimensions must be finite positive')
 z0=p['bottom_z'];zt=p['top_z'];r=p['round_radius'];a=math.radians(p['side_draft_deg']);b=math.radians(p['bevel_normal_deg']);zb=p['shoulder_tangent_z'];xb=p['bottom_half_width']-(zb-z0)*math.tan(a);c1=(xb-r*math.cos(a),zb-r*math.sin(a));end1=(c1[0]+r*math.cos(b),c1[1]+r*math.sin(b));c2z=zt-r;end2z=c2z+r*math.sin(b);end2x=end1[0]-(end2z-end1[1])*math.tan(b);c2x=end2x-r*math.cos(b)
 if not z0<zb<end1[1]<end2z<zt or c2x<=0:raise ValueError('Invalid key tangent ordering')
 def arc(c,ang):return (c[0]+r*math.cos(ang),c[1]+r*math.sin(ang))
 mid1=arc(c1,(a+b)/2);mid2=arc((c2x,c2z),(b+math.pi/2)/2)
 wp=cq.Workplane('XZ').moveTo(p['bottom_half_width'],z0).lineTo(xb,zb).threePointArc(mid1,end1).lineTo(end2x,end2z).threePointArc(mid2,(c2x,zt)).lineTo(-c2x,zt).threePointArc((-mid2[0],mid2[1]),(-end2x,end2z)).lineTo(-end1[0],end1[1]).threePointArc((-mid1[0],mid1[1]),(-xb,zb)).lineTo(-p['bottom_half_width'],z0).close()
 sh=wp.extrude(p['outer_tip_radius']-p['radial_overlap_start']+1).translate((0,-p['radial_overlap_start'],0)).val();cyl=cq.Solid.makeCylinder(p['outer_tip_radius'],zt-z0+.02,cq.Vector(0,0,z0-.01));sh=sh.intersect(cyl).clean()
 if not sh.isValid() or len(sh.Solids())!=1:raise ValueError('Invalid locating key')
 return sh
