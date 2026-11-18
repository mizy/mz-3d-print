import cadquery as cq,json
from pathlib import Path
D=Path(__file__).parent;rows=[]
for part,ro in [('wide',40.85),('narrow',40.65)]:
 s=cq.importers.importBrep(str(D/'prototype'/(part+'.brep'))).val();mask=cq.Workplane('XY').circle(101).circle(ro+1e-6).extrude(45).translate((0,0,8)).val();cut=s.intersect(mask);v=sum(x.Volume() for x in cut.Solids());r={'part':part,'nominal_outer_radius_mm':ro,'tested_z_min_mm':8,'outside_cylinder_volume_mm3':v,'minimum_new_web_z_mm':(35-(40.85-33.1)*1.19175359259421 if part=='wide' else 22-(40.65-29.5)*1.19175359259421),'note':'Below z8 the new roof adds no material; retained original key/boss verified separately. Upper interface unchanged.'};rows.append(r);print(r,flush=True);assert v<1e-5
(D/'paper_envelope.json').write_text(json.dumps(rows,indent=2))
