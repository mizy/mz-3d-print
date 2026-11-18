import cadquery as cq,json,math
from pathlib import Path
D=Path(__file__).parent;oldD=Path('/tmp/chanel_parking_100g/long_wide_v3');rows=[];parts={}
for part in ['wide','narrow']:
 a=cq.importers.importBrep(str(oldD/(part+'.brep'))).val();b=cq.importers.importBrep(str(D/'prototype'/(part+'.brep'))).val();parts[part]=b
 ri=33.3 if part=='wide' else 29.7
 masks={'complete_inner_guide':cq.Solid.makeCylinder(ri,45),'full_flange_A_logo_root':cq.Solid.makeCylinder(101,4.4),'full_upper_interface':cq.Solid.makeCylinder(45,50,cq.Vector(0,0,35 if part=='wide' else 22))}
 for i in range(4):masks['bridge'+str(i)]=cq.Workplane('XY').box(44,1.2,45,centered=(False,True,False)).val().rotate((0,0,0),(0,0,1),i*90)
 if part=='wide':masks['key']=cq.Workplane('XY').box(8,12,9,centered=(True,False,False)).translate((0,-46,0)).val()
 for name,m in masks.items():
  x=a.intersect(m);y=b.intersect(m);v=x.cut(y).Volume()+y.cut(x).Volume();r={'part':part,'region':name,'symmetric_difference_mm3':v};rows.append(r);print(r,flush=True);assert v<1e-4
(D/'protected_regions.json').write_text(json.dumps(rows,indent=2));asm=[]
for H,ang in [(72,51),(70,51),(68,51),(66.4,51),(66.4,8),(66.4,3),(66.4,0)]:
 pn=parts['narrow'].rotate((0,0,0),(1,0,0),180).rotate((0,0,0),(0,0,1),ang).translate((0,0,H));v=parts['wide'].intersect(pn);r={'H':H,'theta':ang,'intersection_mm3':sum(s.Volume() for s in v.Solids())};asm.append(r);print(r,flush=True)
(D/'assembly_checks.json').write_text(json.dumps(asm,indent=2))
