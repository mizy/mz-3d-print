"""Dimension-driven native sketches and revolutions. No source mesh is loaded."""
import math
import cadquery as cq
from config import derived
from motif import double_c

def annulus(ro,ri,z0,z1):
 return cq.Workplane('XY').circle(ro).circle(ri).extrude(z1-z0).translate((0,0,z0)).val()

def build_flange(p):
 d=derived(p);skin=p['skin_thickness'];height=p['rib_height_above_skin']
 plate=annulus(d['plate_outer'],d['plate_inner'],0,skin)
 ribs=[];length=d['rib_end']-d['rib_start'];mid=(d['rib_end']+d['rib_start'])/2
 for i in range(p['rib_count']):
  ribs.append(cq.Workplane('XY').box(length,p['rib_width'],height,centered=(True,True,False)).translate((mid,0,skin)).val().rotate((0,0,0),(0,0,1),360*i/p['rib_count']))
 plate=plate.fuse(*ribs);cuts=[]
 for row in p['logo_rings']:
  rad=d['plate_inner']+row['fraction']*(d['plate_outer']-d['plate_inner']);n=row['count']
  motif=double_c(p['logo_scale']*row['relative_scale'],skin+height+1.)
  for i in range(n):
   a=2*math.pi*(i+.5)/n;cuts.append(motif.translate((rad*math.cos(a),rad*math.sin(a),0)))
 plate=plate.cut(*cuts).clean()
 if not plate.isValid() or len(plate.Solids())!=1:raise ValueError('Logo/skin/rib combination disconnected flange or produced invalid solid')
 return plate

def rolling_rim(p):
 d=derived(p);ri=d['rim_inner'];h=p['rim_height'];ring=annulus(p['rolling_outer_radius'],ri,0,h)
 # Hole centres move radially with inner rim, preserving angle and their offset into the rim.
 oldrad=math.hypot(94.608,15);scale=(ri+(oldrad-95))/oldrad
 holes=[(sx*a*scale,sy*b*scale) for a,b in [(94.608,15),(15,94.608)] for sx in [-1,1] for sy in [-1,1]]
 ring=ring.fuse(*[cq.Solid.makeCylinder(3.1,h,cq.Vector(x,y,0)) for x,y in holes])
 return ring.cut(*[cq.Solid.makeCylinder(1.7071,h+.4,cq.Vector(x,y,-.2)) for x,y in holes]).clean()

def shoulder_dimensions(part,p):
 d=derived(p);k=d['k'];top=22 if part=='wide' else 24
 rt=(31.4*k+p['wide_lock_wall_thickness']+.05*k) if part=='wide' else 29.75*k
 zi=top-((39.9+d['od'])-rt)
 inner=31.65*k if part=='wide' else p['shaft_bore_radius']+.55*k
 return top,rt,zi,inner

def build_shoulder(part,p):
 d=derived(p);top,rt,z0,inner=shoulder_dimensions(part,p);az=d['az'];od=d['od']
 profile=[(39.9+od,z0),(rt,top),(inner,top),(inner,top-3),(p['hub_lower_inner_radius'],z0-1.3)]
 return cq.Workplane('XZ').polyline([(r,z*az) for r,z in profile]).close().revolve(360,(0,0),(0,1)).val()

def lower_core(part,p):
 d=derived(p);od=d['od'];az=d['az'];top,rt,z0,inner=shoulder_dimensions(part,p)
 ro=p['hub_outer_radius']-(0 if part=='wide' else .2)
 wall=annulus(ro,p['hub_lower_inner_radius'],p['skin_thickness'],(z0+.1)*az)
 foot=annulus(44+od,(39.5 if part=='wide' else 39.4)+od,0,max(1.4,1.4+(p['skin_thickness']-.6)))
 wall=wall.fuse(foot,build_shoulder(part,p)).clean()
 if part=='wide':
  zs=[1.4,4.,5.,6.,7.,7.7,7.8,7.815];widths=[3.6,3.5981,3.3879,3.1777,2.8949,1.4432,1.0553,.7]
  wires=[cq.Workplane('XY').workplane(offset=z*az).center(-.02735,(40.4+43.70056)/2+od).rect(w,43.70056-40.4).val() for z,w in zip(zs,widths)]
  wall=wall.fuse(cq.Solid.makeLoft(wires,ruled=True)).clean()
 return wall

def outer_tube(part,p):
 d=derived(p);od=d['od'];extra=p['sleeve_wall_extra'];az=d['az'];bottom=shoulder_dimensions(part,p)[2]-.1
 if part=='wide':
  profile=[(40.848+od+extra,bottom),(40.848+od+extra,39.61506),(39.75+od+extra,40.715057373),(39.+od,40.715057373),(39.+od,22.),(39.5+od,22.),(39.5+od,bottom)]
  center=(-.0273430863,.0010603425,0)
 else:
  profile=[(40.648+od,bottom),(40.648+od,24.71305),(39.65+od,25.7150566),(38.898+od,25.7150566),(38.898+od,27.11506),(38.40+od,27.9150562),(37.698+od-extra,27.9150562),(37.698+od-extra,24.),(39.4+od-extra,24.),(39.4+od-extra,bottom)]
  center=(.0015810415,-.0274228517,0)
 return cq.Workplane('XZ').polyline([(r,z*az) for r,z in profile]).close().revolve(360,(0,0),(0,1)).val().translate(center)

def structural_body(part,p,flange=None):
 if flange is None:flange=build_flange(p)
 return flange.fuse(rolling_rim(p),lower_core(part,p),outer_tube(part,p)).clean()

def bridges(p):
 d=derived(p);c=(-.02734375,.000549315,0);r0=31.4*d['k']+p['wide_lock_wall_thickness']-.1;r1=39+d['od']+.1
 return [cq.Workplane('XY').box(r1-r0,p['bridge_width'],(25.7150566-22)*d['az'],centered=(True,True,False)).translate(((r0+r1)/2+c[0],c[1],22*d['az'])).val().rotate(c,(c[0],c[1],1),a) for a in [0,90,180,270]]
