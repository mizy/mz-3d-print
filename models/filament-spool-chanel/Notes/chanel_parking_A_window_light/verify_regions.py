import cadquery as cq,json,sys,math
from pathlib import Path
D=Path(__file__).parent;stage=sys.argv[1];report=[]
for part in ['wide','narrow']:
 a=cq.importers.importBrep('/tmp/chanel_parking_light/revised_output/'+part+'.brep').val();b=cq.importers.importBrep(str(D/stage/(part+'.brep'))).val()
 masks={'complete_inner_guide_and_locks':cq.Solid.makeCylinder(33.5,50),'full_flange_parking_A_and_root':cq.Solid.makeCylinder(101,4.4),'upper_outer_interface':cq.Solid.makeCylinder(45,50,cq.Vector(0,0,35 if part=='wide' else 22))}
 for i in range(4):masks['bridge_'+str(i)]=cq.Workplane('XY').box(44,1.2,45,centered=(False,True,False)).val().rotate((0,0,0),(0,0,1),i*90)
 if part=='wide':masks['official_key']=cq.Workplane('XY').box(8,12,9,centered=(True,False,False)).translate((0,-46,0)).val()
 for name,m in masks.items():
  x=a.intersect(m);y=b.intersect(m);v=x.cut(y).Volume()+y.cut(x).Volume();r={'part':part,'region':name,'symmetric_difference_mm3':v};report.append(r);print(r,flush=True);assert abs(v)<1e-4,(part,name,v)
(D/stage/'protected_regions.json').write_text(json.dumps(report,indent=2))
