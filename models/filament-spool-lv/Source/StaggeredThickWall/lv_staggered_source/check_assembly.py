from model_paths import MODELS_DIR
"""CAD-only nominal fit comparison. No slicing, FEA or physical certification."""
from pathlib import Path
import json,math,cadquery as cq
import official_hub as H
R=Path(__file__).resolve().parent;O=MODELS_DIR;p=json.loads((R/'parameters.json').read_text());h=p['hub'];q=json.loads((R/'light_parameters.json').read_text())['hub_windows']
new={part:cq.Shape.importBrep(str(O/(part+'_hub.brep'))) for part in ('wide','narrow')};old={part:H.build_hub(part,h) for part in ('wide','narrow')}
report={'checks':{},'limits':['Nominal CAD fit only, not physical fit or strength certification.','Actual paper-core inner diameter and refill width not supplied; compatibility cannot be certified.','Insertion sampled at axial offsets and original clocking; elastic latch behavior not simulated.']}
for part in new:
 s=new[part];ref=old[part];c={'valid':s.isValid(),'solids':len(s.Solids())};assert c['valid'] and c['solids']==1
 zone=cq.Solid.makeCylinder(35.8,30,cq.Vector(0,0,29)).fuse(cq.Solid.makeCylinder(44,30,cq.Vector(0,0,37.5 if part=='wide' else 24.3)).cut(cq.Solid.makeCylinder(35.8,60)));a=s.intersect(zone);b=ref.intersect(zone);d=a.cut(b).Volume()+b.cut(a).Volume();assert d<1e-5;c['upper_interface_difference_mm3']=d
 rinner=(h['wide_bore_radius'] if part=='wide' else h['shaft_bore_radius'])+2;router=h[part+'_outer_tube_outer_radius']-2
 probes=[]
 for kind,angles,r,other,z in [('outer',[45*i for i in range(8)],router,rinner,10),('inner',[22.5+45*i for i in range(8)],rinner,router,14)]:
  for angle in angles:
   t=math.radians(angle)
   def probe(rad):return cq.Solid.makeCylinder(.05,.1,cq.Vector(rad*math.cos(t),rad*math.sin(t),z))
   a=probe(r);b=probe(other);empty=a.intersect(s).Volume()/a.Volume();solid=b.intersect(s).Volume()/b.Volume();assert empty<1e-6 and solid>.999
   probes.append({'layer':kind,'angle':angle,'opening_material_fraction':empty,'opposite_wall_material_fraction':solid})
 c['window_probes']=probes;report['checks'][part]=c;print(part,'interface and 16 stagger probes PASS',flush=True)
def placed(s,offset=0,twist=0):return s.rotate((0,0,0),(1,0,0),180).rotate((0,0,0),(0,0,1),twist).translate((0,0,67.4+offset))
report['assembly']={'outer_face_separation_mm':67.4,'nominal_minimum_shaft_bore_mm':55.,'nominal_wide_barrel_outer_diameter_mm':81.7,'nominal_narrow_barrel_outer_diameter_mm':81.3,'maximum_barrel_diameter_excluding_key_mm':81.7,'coil_space_between_3p6mm_rib_envelopes_mm':60.2,'samples':[]}
for offset in [0,2,5,10]:
 for twist in ([0,44,50] if offset==0 else [50]):
  n=placed(new['narrow'],offset,twist);o=placed(old['narrow'],offset,twist)
  v=new['wide'].intersect(n).Volume();v0=old['wide'].intersect(o).Volume();assert abs(v-v0)<1e-4
  report['assembly']['samples'].append({'axial_offset_mm':offset,'twist_deg':twist,'baseline_interference_mm3':v0,'new_interference_mm3':v,'new_minus_baseline_mm3':v-v0});print('fit',offset,twist,v0,v,flush=True)
shaft=cq.Solid.makeCylinder(27.45,67.4);overlap=shaft.intersect(new['wide']).Volume()+shaft.intersect(placed(new['narrow'])).Volume();assert overlap<1e-5;report['assembly']['shaft_54p9mm_interference_mm3']=overlap
(O/'assembly_checks.json').write_text(json.dumps(report,indent=2));print('CAD fit checks complete',flush=True)
