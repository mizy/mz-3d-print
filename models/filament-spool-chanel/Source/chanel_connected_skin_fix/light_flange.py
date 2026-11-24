"""Lightweight decorative derivative of official-reference flange.
Preserves the official central support region, outer rolling envelope and four hole positions.
"""
import math,cadquery as cq
from official_flange import build_flange as official_flange
from light_motif import double_c
DEFAULTS={'core_keep_radius':44.5,'skin_thickness':.4,'rib_width':4.,'rib_total_height':3.2,'rib_count':8,'rim_width':5.,'hole_pad_radius':3.1,'rim_overlap':.8,'rim_bond_inner_margin':.4,'hub_overlap':.5,'hub_bond_width':1.5,'bond_height':.8,'logo_scale':1.,'logo_rings':[{'radius_fraction':.171717171717,'count':16,'relative_scale':.99},{'radius_fraction':.515151515152,'count':24,'relative_scale':.99},{'radius_fraction':.858585858586,'count':32,'relative_scale':.9}]}
def build_light_flange(part,f,p=None):
 p=dict(DEFAULTS if p is None else p)
 if set(p)!=set(DEFAULTS):raise ValueError('Missing/unknown lightweight parameter')
 if not .4<=p['skin_thickness']<p['rib_total_height']<=f['rim_height'] or p['rib_width']<3 or p['rim_width']<4:raise ValueError('Unsupported skin/rib/rim combination')
 if p['rib_count']<8 or int(p['rib_count'])!=p['rib_count']:raise ValueError('rib_count must be integer>=8')
 ro=f['outer_radius'];ri=ro-p['rim_width'];inner=p['core_keep_radius'];plateouter=ri-1;skin=p['skin_thickness'];total=p['rib_total_height'];h=f['rim_height'];ch=f['rim_outer_chamfer']
 if not f['boss_at_plate']<=p['core_keep_radius']<plateouter-35:raise ValueError('Core preservation / logo region invalid')
 if not .5<=p['rim_overlap']<=1.2 or not .3<=p['rim_bond_inner_margin']<=1 or not .4<=p['hub_overlap']<=1 or not 1<=p['hub_bond_width']<=2 or not skin<=p['bond_height']<=1.2:raise ValueError('Bond dimensions out of range')
 source=official_flange(part,f);core=source.intersect(cq.Solid.makeCylinder(p['core_keep_radius'],max(h,f['boss_step_height']+f['wide_boss_chamfer'])+.1))
 # Keep original motif radius formula, but extend actual skin into both load paths.
 plate=cq.Workplane('XY').circle(ri+p['rim_overlap']).circle(inner-p['hub_overlap']).extrude(skin).val();start=inner;end=ro-2.5
 ribs=[cq.Workplane('XY').box(end-start,p['rib_width'],total-skin,centered=(True,True,False)).translate(((start+end)/2,0,skin)).val().rotate((0,0,0),(0,0,1),i*360/p['rib_count']) for i in range(p['rib_count'])];plate=plate.fuse(*ribs)
 cuts=[];original_cuts=[]
 for row in p['logo_rings']:
  if set(row)!={'radius_fraction','count','relative_scale'} or not 0<row['radius_fraction']<1 or not isinstance(row['count'],int) or row['count']<1:raise ValueError('Invalid motif ring')
  rad=inner+row['radius_fraction']*(plateouter-inner);motif=double_c(p['logo_scale']*row['relative_scale'],total+2)
  for i in range(row['count']):
   a=2*math.pi*(i+.5)/row['count'];shift=(rad*math.cos(a),rad*math.sin(a),0);cuts.append(motif.translate(shift));original_cuts.append(double_c(row['relative_scale'],total+2).translate(shift))
 original_plate=plate.cut(*original_cuts).clean()
 protected=original_plate.intersect(cq.Compound.makeCompound([r.translate((0,0,-skin)).fuse(r) for r in ribs]))
 plate=plate.cut(*cuts).fuse(protected).clean()
 ring=cq.Workplane('XZ').polyline([(ri,0),(ro-ch,0),(ro,ch),(ro,h-ch),(ro-ch,h),(ri,h)]).close().revolve(360,(0,0),(0,1)).val()
 a=math.sqrt(f['line_hole_pitch_radius']**2-f['line_hole_offset']**2);b=f['line_hole_offset'];holes=[];pads=[]
 for sx in [-1,1]:
  for sy in [-1,1]:
   x,y=(sx*a,sy*b) if part=='wide' else (sx*b,sy*a);pads.append(cq.Solid.makeCylinder(p['hole_pad_radius'],h,cq.Vector(x,y,0)));holes.append(cq.Solid.makeCylinder(f['line_hole_radius'],h+.2,cq.Vector(x,y,-.1)))
 ring=ring.fuse(*pads).cut(*holes)
 outer_bond=cq.Workplane('XY').circle(ri+p['rim_overlap']).circle(plateouter-p['rim_bond_inner_margin']).extrude(p['bond_height']).val()
 inner_bond=cq.Workplane('XY').circle(inner+p['hub_bond_width']).circle(inner-p['hub_overlap']).extrude(p['bond_height']).val()
 # Bonds added AFTER logo cuts: continuous annular load paths, not isolated spoke contacts.
 s=core.fuse(plate,ring,outer_bond,inner_bond).cut(*holes).clean()
 if not s.isValid() or len(s.Solids())!=1:raise ValueError('Light flange invalid or disconnected')
 return s
