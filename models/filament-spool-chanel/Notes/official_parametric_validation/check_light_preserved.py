import cadquery as cq,json,math
from pathlib import Path
D=Path(__file__).parent;rows=[]
for part in ['wide','narrow']:
 a=cq.importers.importBrep(str(D/'build_output'/f'{part}.brep')).val();b=cq.importers.importBrep(str(D/'light_output'/f'{part}.brep')).val();regions={'central_r44_4':cq.Solid.makeCylinder(44.4,45,cq.Vector(0,0,-.1)),'rolling_outer_r99_6':cq.Workplane('XY').circle(101).circle(99.6).extrude(4).translate((0,0,-.1)).val()}
 x=math.sqrt(96**2-15**2)
 for sx in [-1,1]:
  for sy in [-1,1]:
   xx,yy=(sx*x,sy*15) if part=='wide' else (sx*15,sy*x);regions[f'hole_{sx}_{sy}']=cq.Solid.makeCylinder(2.1,4,cq.Vector(xx,yy,-.1))
 for key,mask in regions.items():
  aa=a.intersect(mask);bb=b.intersect(mask);v=abs(aa.cut(bb).Volume())+abs(bb.cut(aa).Volume());row={'part':part,'region':key,'symmetric_difference_mm3':v,'reference_volume':aa.Volume(),'light_volume':bb.Volume()};rows.append(row);print(row,flush=True)
assert max(r['symmetric_difference_mm3'] for r in rows)<.0001
(D/'light_preserved_regions.json').write_text(json.dumps(rows,indent=2))
