"""Experimental open-spoke flange. Original rolling ring/A surfaces and central core retained.
No strength certification. Four thin double-C plaques are decoration, not primary load paths.
"""
import math,cadquery as cq
from flange_previous import DEFAULTS as BASE_DEFAULTS
from official_flange import build_flange as official_flange
from light_motif import double_c
DEFAULTS={**BASE_DEFAULTS,"plaque_width":20.,"plaque_height":14.,"plaque_logo_scale":1.,"plaque_count":4}

def build_light_flange(part,f,p=None):
 p=dict(DEFAULTS if p is None else p)
 if set(p)!=set(DEFAULTS):raise ValueError("Unknown/missing open spoke parameter")
 if p["plaque_count"]!=4 or p["plaque_width"]<18 or p["plaque_height"]<12:raise ValueError("Unsupported plaque")
 # Exact native core/ring and all four inward-projecting hole pads; no mesh/BRep donor.
 inner=p['core_keep_radius'];ro=f['outer_radius'];ri=ro-p['rim_width'];h=f['rim_height'];skin=p['skin_thickness'];total=p['rib_total_height']
 core=official_flange(part,f).intersect(cq.Solid.makeCylinder(inner,h+1))
 ch=f['rim_outer_chamfer'];ring=cq.Workplane('XZ').polyline([(ri,0),(ro-ch,0),(ro,ch),(ro,h-ch),(ro-ch,h),(ri,h)]).close().revolve(360,(0,0),(0,1)).val()
 a=math.sqrt(f['line_hole_pitch_radius']**2-f['line_hole_offset']**2);b=f['line_hole_offset'];pads=[];holes=[]
 for sx in [-1,1]:
  for sy in [-1,1]:
   x,y=(sx*a,sy*b) if part=='wide' else (sx*b,sy*a);pads.append(cq.Solid.makeCylinder(p['hole_pad_radius'],h,cq.Vector(x,y,0)));holes.append(cq.Solid.makeCylinder(f['line_hole_radius'],h+.2,cq.Vector(x,y,-.1)))
 ring=ring.fuse(*pads).cut(*holes).clean()
 ribs=[]
 for i in range(p['rib_count']):
  a=i*360/p['rib_count'];r=cq.Workplane('XY').box(ro-2.5-inner+.6,p['rib_width'],total,centered=(True,True,False)).translate(((inner-.6+ro-2.5)/2,0,0)).val().rotate((0,0,0),(0,0,1),a);ribs.append(r)
 # Four complete small plaques integrated into the cardinal primary spokes.
 plaques=[];rad=(inner+ri)/2
 for a in [0,90,180,270]:
  t=math.radians(a);plate=cq.Workplane('XY').rect(p["plaque_width"],p["plaque_height"]).extrude(skin).val().cut(double_c(p["plaque_logo_scale"],skin+2));plate=plate.translate((rad*math.cos(t),rad*math.sin(t),0));plaques.append(plate)
 s=core.fuse(ring,*ribs,*plaques).clean()
 if not s.isValid() or len(s.Solids())!=1:raise ValueError('Open spoke flange invalid/disconnected')
 return s
