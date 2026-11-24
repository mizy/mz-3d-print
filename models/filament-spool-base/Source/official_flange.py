"""Native revolved official-style flange, four line holes and underside label groove.
No STL is imported here. Dimensions inferred from official STL, not certified drawings.
"""
import cadquery as cq,math
DEFAULT={'outer_radius':100.,'plate_thickness':2.5,'rim_height':3.6,'rim_outer_chamfer':.4,'rim_inner_at_plate':91.7,'rim_inner_top':92.8,'line_hole_radius':1.75,'line_hole_pitch_radius':96.,'line_hole_offset':15.,'bore_radius':27.5,'bore_entry_chamfer':.8,'support_top':2.7,'boss_at_plate':44.4,'boss_step_radius':43.9,'boss_step_height':3.,'wide_outer_tube_radius':40.85,'narrow_outer_tube_radius':40.65,'wide_inner_tube_outer':33.3,'narrow_inner_tube_outer':29.7,'wide_outer_tube_inner':39.,'narrow_outer_tube_inner':37.7,'wide_boss_chamfer':.5,'label_center_x':69.,'label_length':46.,'label_width':20.,'label_groove_width':.4,'label_groove_depth':.4,'boss_notch_halfwidth':9.3,'boss_notch_draft':1.,'narrow_notch_normal_angle_deg':54.}
def validate(p):
 if set(p)!=set(DEFAULT):raise ValueError('Unknown or missing flange parameters')
 if not all(isinstance(v,(int,float)) and math.isfinite(v) and v>0 for v in p.values()):raise ValueError('Positive finite dimensions required')
 if not p['bore_radius']<p['narrow_inner_tube_outer']<p['narrow_outer_tube_inner']<p['boss_step_radius']<p['rim_inner_at_plate']<p['rim_inner_top']<p['outer_radius']:raise ValueError('Radial order violated')
 if not p['plate_thickness']<p['support_top']<p['boss_step_height']<p['rim_height']:raise ValueError('Axial order violated')
 if p['line_hole_pitch_radius']+p['line_hole_radius']>=p['outer_radius']-p['rim_outer_chamfer']:raise ValueError('Line hole breaches outer rolling edge')
 if p['line_hole_offset']>=p['line_hole_pitch_radius']:raise ValueError('Invalid hole offset')
def build_flange(part,p=None):
 p=dict(DEFAULT if p is None else p);validate(p)
 if part not in ('wide','narrow'):raise ValueError(part)
 ro=p[f'{part}_outer_tube_radius'];ri=p['bore_radius'];ch=p['rim_outer_chamfer'];h=p['rim_height'];s=p['boss_step_height'];top=s+(p['wide_boss_chamfer'] if part=='wide' else 0)
 profile=[(ri+p['bore_entry_chamfer'],0),(p['outer_radius']-ch,0),(p['outer_radius'],ch),(p['outer_radius'],h-ch),(p['outer_radius']-ch,h),(p['rim_inner_top'],h),(p['rim_inner_at_plate'],p['plate_thickness']),(p['boss_at_plate'],p['plate_thickness']),(p['boss_step_radius'],s)]
 if part=='wide':profile.extend([(ro+p['wide_boss_chamfer'],s),(ro,top)])
 else:profile.append((ro,s))
 profile.extend([(ri,top),(ri,p['bore_entry_chamfer'])]);body=cq.Workplane('XZ').polyline(profile).close().revolve(360,(0,0),(0,1)).val()
 # Annular cavity starts above the source's 2.7mm solid support floor.
 cavity=cq.Workplane('XY').circle(p[f'{part}_outer_tube_inner']).circle(p[f'{part}_inner_tube_outer']).extrude(top-p['support_top']+.1).translate((0,0,p['support_top'])).val();body=body.cut(cavity)
 a=math.sqrt(p['line_hole_pitch_radius']**2-p['line_hole_offset']**2);b=p['line_hole_offset'];holes=[]
 for sx in [-1,1]:
  for sy in [-1,1]:
   x,y=(sx*a,sy*b) if part=='wide' else (sx*b,sy*a)
   holes.append(cq.Solid.makeCylinder(p['line_hole_radius'],h+.2,cq.Vector(x,y,-.1)))
 body=body.cut(*holes)
 # Official boss is interrupted, not a complete circular raised flange.
 def cut_wire(z):
  b=p['boss_notch_halfwidth']+(z-p['plate_thickness'])*p['boss_notch_draft']
  if part=='wide':pts=[(-b,-60),(b,-60),(b,0),(-b,0)]
  else:
   a=math.radians(p['narrow_notch_normal_angle_deg']);c,t=math.cos(a),math.sin(a)
   pts=[(b,100),(-100,100),(-100,(-b+100*c)/t),(b,(-b-c*b)/t)]
  return cq.Workplane('XY').workplane(offset=z).polyline(pts).close().val()
 notch=cq.Solid.makeLoft([cut_wire(p['plate_thickness']),cut_wire(top+.01)],ruled=True)
 if part=='wide':protect=cq.Solid.makeCylinder(ro,top-p['plate_thickness']+.03,cq.Vector(0,0,p['plate_thickness']-.01))
 else:protect=cq.Solid.makeCone(ro+(s-p['plate_thickness']),ro-.01,top-p['plate_thickness']+.01,cq.Vector(0,0,p['plate_thickness']))
 notch=notch.cut(protect).intersect(cq.Solid.makeCylinder(p['boss_at_plate']+.1,top-p['plate_thickness']+.03,cq.Vector(0,0,p['plate_thickness']-.01)));body=body.cut(notch)
 if part=='narrow':body=body.cut(notch.rotate((0,0,0),(0,0,1),180))
 if part=='narrow':
  def capsule(length,width):return cq.Workplane('XY').center(p['label_center_x'],0).slot2D(length,width).extrude(p['label_groove_depth']+.1).translate((0,0,-.1)).val()
  outer=capsule(p['label_length']+2*p['label_groove_width'],p['label_width']+2*p['label_groove_width']);inner=capsule(p['label_length'],p['label_width']);body=body.cut(outer.cut(inner))
 body=body.clean()
 if not body.isValid() or len(body.Solids())!=1:raise ValueError('Invalid/disconnected official flange')
 return body
