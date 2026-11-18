import cadquery as cq,json,math
from pathlib import Path
D=Path(__file__).parent;rows=[]
for part in ['wide','narrow']:
 old=cq.importers.importBrep(str(D/'spoke'/(part+'.brep'))).val();new=cq.importers.importBrep(str(D/'relief'/(part+'.brep'))).val()
 gi=33.3 if part=='wide' else 29.7;ro=40.85 if part=='wide' else 40.65;top=35 if part=='wide' else 22;tan=math.tan(math.radians(50));r0=gi-.2;r1=ro+.05;z0=top-(ro-r0)*tan;z1=top-(ro-r1)*tan;membrane=cq.Workplane('XZ').polyline([(r0,z0),(r1,z1),(r1,z1+1.1),(r0,z0+1.1)]).close().revolve(360,(0,0),(0,1)).val()
 masks=[('roof_added_material',membrane),('external_flange',cq.Workplane('XY').circle(101).circle(44.5).extrude(5).val()),('inner_lock_region',cq.Solid.makeCylinder(34,25,cq.Vector(0,0,22 if part=='wide' else 24.1))),('outer_sleeve_mating_region',cq.Solid.makeCylinder(45,10,cq.Vector(0,0,35 if part=='wide' else 24.1))),('shaft_entry',cq.Solid.makeCylinder(29.5,3.5)),('guide_mating_skin',cq.Solid.makeCylinder(31.76 if part=='wide' else 27.6,40))]
 for angle in [0,90,180,270]:masks.append(('bridge_'+str(angle),cq.Workplane('XY').box(43,1.2,42,centered=(False,True,False)).val().rotate((0,0,0),(0,0,1),angle)))
 if part=='wide':masks.append(('key',cq.Workplane('XY').box(5,8,9,centered=(True,True,False)).translate((0,-41,0)).val()))
 # Paper exterior contact layer, unchanged even where wall has been thinned internally.
 rr=40.85 if part=='wide' else 40.65
 masks.append(('paper_outer_skin',cq.Workplane('XY').circle(rr+.01).circle(rr-.1).extrude(40).val()))
 for name,mask in masks:
  a=old.intersect(mask);b=new.intersect(mask);row={'part':part,'region':name,'removed_mm3':a.cut(b).Volume(),'added_mm3':b.cut(a).Volume()};rows.append(row);print(row,flush=True);(D/'relief_protected_regions.json').write_text(json.dumps(rows,indent=2))
(D/'relief_protected_regions.json').write_text(json.dumps(rows,indent=2))
