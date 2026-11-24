"""Four unbroken native-Bezier LV cutouts between eight uninterrupted structural spokes."""
import math,cadquery as cq
from official_flange import build_flange as official_flange
from lv_motif import motif
DEFAULTS={'core_keep_radius':44.5,'skin_thickness':1.2,'rib_width':5.,'rib_total_height':3.6,'rib_count':8,'rim_width':5.,'hole_pad_radius':3.1,'motif_size':12.,'local_bridge_width':1.4,'rim_overlap':.8,'rim_bond_inner_margin':.4,'hub_overlap':.5,'hub_bond_width':1.5,'bond_height':1.6,'motif_rings':[{'radius':53.,'count':16},{'radius':70.,'count':24},{'radius':86.,'count':32}]}
def build_light_flange(part,f,p=None):
 p=dict(DEFAULTS if p is None else p)
 if set(p)!=set(DEFAULTS):raise ValueError('Missing/unknown lightweight parameter')
 if not 1.2<=p['skin_thickness']<p['rib_total_height']<=f['rim_height'] or p['rib_width']<4 or p['rim_width']<5:raise ValueError('Unsupported skin/rib/rim combination')
 if not .5<=p['rim_overlap']<=1.2 or not .3<=p['rim_bond_inner_margin']<=1 or not .4<=p['hub_overlap']<=1 or not 1<=p['hub_bond_width']<=2 or not p['skin_thickness']<=p['bond_height']<=2:raise ValueError('Unsupported continuous bond parameters')
 if p['rib_count']!=8 or not 10<=p['motif_size']<=14 or not 1<=p['local_bridge_width']<=1.6:raise ValueError('Unsupported motif layout')
 ro=f['outer_radius'];ri=ro-p['rim_width'];inner=p['core_keep_radius'];plateouter=ri-1;skin=p['skin_thickness'];total=p['rib_total_height'];h=f['rim_height'];ch=f['rim_outer_chamfer']
 if not f['boss_at_plate']<=inner<plateouter-35:raise ValueError('Core preservation / logo region invalid')
 source=official_flange(part,f);core=source.intersect(cq.Solid.makeCylinder(inner,max(h,f['boss_step_height']+f['wide_boss_chamfer'])+.1))
 plate=cq.Workplane('XY').circle(ri+p['rim_overlap']).circle(inner-p['hub_overlap']).extrude(skin).val();start=inner;end=ro-2.5
 ribs=[cq.Workplane('XY').box(end-start,p['rib_width'],total,centered=(True,True,False)).translate(((start+end)/2,0,0)).val().rotate((0,0,0),(0,0,1),i*45) for i in range(8)]
 cuts=[];names=['logo','pointed','diamond','circle'];tools={n:motif(n,p['motif_size'],total+1,p['local_bridge_width']) for n in names}
 # Clip cutters to clear-of-rib region, then reject clipped motifs instead of cutting bars through them.
 protector=cq.Compound.makeCompound([cq.Workplane('XY').box(end-start,p['rib_width']+2,total+2,centered=(True,True,False)).translate(((start+end)/2,0,-.2)).val().rotate((0,0,0),(0,0,1),i*45) for i in range(8)])
 for rowidx,row in enumerate(p['motif_rings']):
  rad=row['radius'];count=row['count']
  if not inner+7<rad<plateouter-6 or count<8:raise ValueError('Motif ring crosses protected regions')
  for i in range(count):
   a=2*math.pi*(i+.5)/count;n=names[(i+rowidx)%4];m=tools[n].translate((rad*math.cos(a),rad*math.sin(a),0))
   if m.intersect(protector).Volume()>1e-6:continue
   cuts.append(m)
 if len(cuts)<16:raise ValueError('Insufficient safe motifs')
 plate=plate.cut(*cuts).fuse(*ribs).clean()
 ring=cq.Workplane('XZ').polyline([(ri,0),(ro-ch,0),(ro,ch),(ro,h-ch),(ro-ch,h),(ri,h)]).close().revolve(360,(0,0),(0,1)).val()
 a=math.sqrt(f['line_hole_pitch_radius']**2-f['line_hole_offset']**2);b=f['line_hole_offset'];holes=[];pads=[]
 for sx in [-1,1]:
  for sy in [-1,1]:
   x,y=(sx*a,sy*b) if part=='wide' else (sx*b,sy*a);pads.append(cq.Solid.makeCylinder(p['hole_pad_radius'],h,cq.Vector(x,y,0)));holes.append(cq.Solid.makeCylinder(f['line_hole_radius'],h+.2,cq.Vector(x,y,-.1)))
 ring=ring.fuse(*pads).cut(*holes)
 outer_bond=cq.Workplane('XY').circle(ri+p['rim_overlap']).circle(plateouter-p['rim_bond_inner_margin']).extrude(p['bond_height']).val()
 inner_bond=cq.Workplane('XY').circle(inner+p['hub_bond_width']).circle(inner-p['hub_overlap']).extrude(p['bond_height']).val()
 s=core.fuse(plate,ring,outer_bond,inner_bond).cut(*holes).clean()
 if not s.isValid() or len(s.Solids())!=1:raise ValueError('LV flange invalid/disconnected island')
 return s
