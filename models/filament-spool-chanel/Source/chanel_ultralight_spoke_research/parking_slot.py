"""Two inward-opening, tangential filament parking channels. Not an operating guide.
Original four holes retained; two gain a connected shallow channel, two remain untouched.
No change to radial rolling surface or bed plane. Clip retention requires physical test.
"""
import math,cadquery as cq
DEFAULTS={'enabled':True,'channel_length':10.,'channel_diameter':2.1,'channel_center_z':2.15,'throat_width':1.7,'top_mouth_width':2.1,'selected_sx':1,'radial_offset':0.9}
def apply_slots(shape,part,f,p):
 if set(p)!=set(DEFAULTS):raise ValueError('Unknown/missing parking slot parameter')
 if not p['enabled']:return shape
 L=p['channel_length'];d=p['channel_diameter'];z=p['channel_center_z'];w=p['throat_width'];h=f['rim_height'];ro=f['outer_radius']
 if not 6<=L<=12 or not 1.9<=d<=2.4 or not 1.6<=w<=d or not w<=p['top_mouth_width']<=d or z-d/2<.9 or z+d/2>=h or p['selected_sx'] not in [-1,1]:raise ValueError('Unsupported parking dimensions')
 if not .85<=p['radial_offset']<=1.0:raise ValueError('Slot inner-wall margin requires radial offset .85..1.0')
 a=math.sqrt(f['line_hole_pitch_radius']**2-f['line_hole_offset']**2);b=f['line_hole_offset'];cutters=[]
 for sy in [-1,1]:
  x,y=(p['selected_sx']*a,sy*b) if part=='wide' else (p['selected_sx']*b,sy*a)
  # tangent points away from the near symmetry axis; rounded blind end.
  theta=math.atan2(y,x);x+=p['radial_offset']*math.cos(theta);y+=p['radial_offset']*math.sin(theta);tx,ty=-math.sin(theta)*sy,math.cos(theta)*sy
  start=cq.Vector(x,y,z);end=cq.Vector(x+L*tx,y+L*ty,z)
  assert math.hypot(end.x,end.y)+d/2<ro-.5
  tube=cq.Solid.makeCylinder(d/2,L,start,cq.Vector(tx,ty,0)).fuse(cq.Solid.makeSphere(d/2,end))
  # Open neck: modest undercut at mid-height, flared top entrance, no external protrusion.
  ang=math.degrees(math.atan2(ty,tx));cx=x+L*tx/2;cy=y+L*ty/2
  wires=[]
  for zz,ww in [(z,w),(h-.25,w),(h+.05,p['top_mouth_width'])]:
   wires.append(cq.Workplane('XY').workplane(offset=zz).center(cx,cy).slot2D(L+ww,ww,ang).val())
  neck=cq.Solid.makeLoft(wires,ruled=True);cutters.append(tube.fuse(neck))
 s=shape.cut(*cutters).clean()
 if not s.isValid() or len(s.Solids())!=1:raise ValueError('Parking slots disconnected/invalid')
 return s
