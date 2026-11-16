import cadquery as cq,json,itertools
from pathlib import Path
p=Path('/private/tmp/lv-tenon-step')
s=sorted(cq.importers.importStep(str(p/'LV_bowl_multibody.step')).val().Solids(),key=lambda s:s.BoundingBox().zmin)
assert len(s)==3
logo=cq.importers.importStep(str(p/'LV_logo_tenon.step')).val()
logo=logo.translate((110,0,0))
parts=[('ivory_bottom',s[0],(.988,.925,.839)),('light_blue_body',s[1],(.725,.851,.922)),('ivory_rim',s[2],(.988,.925,.839)),('ivory_logo_with_tenons',logo,(.988,.925,.839))]
a=cq.Assembly(name='LV_bowl_and_separate_tenon_logo')
r={'parts':{},'pair_intersections_mm3':{}}
for n,o,c in parts:
 assert o.isValid() and len(o.Solids())==1
 b=o.BoundingBox();r['parts'][n]={'valid':o.isValid(),'solids':len(o.Solids()),'volume_mm3':o.Volume(),'bounds':[b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]}
 a.add(o,name=n,color=cq.Color(*c))
for (n,o,_),(m,q,_) in itertools.combinations(parts,2):
 v=o.intersect(q).Volume();assert v<1e-6,(n,m,v);r['pair_intersections_mm3'][n+' / '+m]=v
f=p/'LV_bowl_and_logo.step';a.save(str(f))
t=cq.importers.importStep(str(f)).val();assert len(t.Solids())==4 and all(x.isValid() for x in t.Solids())
b=t.BoundingBox();r.update(roundtrip_solids=len(t.Solids()),roundtrip_all_valid=True,assembly_size_mm=[b.xlen,b.ylen,b.zlen],colour_rgb_entries=f.read_text().count('COLOUR_RGB'),logo_bowl_x_gap_mm=logo.BoundingBox().xmin-max(x.BoundingBox().xmax for x in s))
assert r['colour_rgb_entries']==2
(p/'combined_validation.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
