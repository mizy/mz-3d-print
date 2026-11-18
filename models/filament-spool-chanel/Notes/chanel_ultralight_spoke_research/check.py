import cadquery as cq,json
from pathlib import Path
D=Path(__file__).parent;rows=[]
for part in ['wide','narrow']:
 old=cq.importers.importBrep('/tmp/chanel_selfsupport_roof/prototype/'+part+'.brep').val();new=cq.importers.importBrep(str(D/'spoke'/(part+'.brep'))).val()
 for name,mask in [('core',cq.Solid.makeCylinder(44.5,45)),('hub',cq.Solid.makeCylinder(44.5,41,cq.Vector(0,0,4))),('rim',cq.Workplane('XY').circle(101).circle(95).extrude(5).val())]:
  a=old.intersect(mask);b=new.intersect(mask);rows.append({'part':part,'region':name,'removed_mm3':a.cut(b).Volume(),'added_mm3':b.cut(a).Volume()})
 print(part,rows[-3:],flush=True)
(D/'protected_regions.json').write_text(json.dumps(rows,indent=2))
