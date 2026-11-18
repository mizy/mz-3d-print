import cadquery as cq,json,math
from pathlib import Path
D=Path(__file__).parent;B=Path('/tmp/chanel_official_native/light_output');report=[]
for part in ['wide','narrow']:
 old=cq.importers.importBrep(str(B/f'{part}.brep')).val();new=cq.importers.importBrep(str(D/'output'/f'{part}.brep')).val()
 tests=[('official_core',cq.Solid.makeCylinder(44.4,50)),('rolling_track',cq.Solid.makeCylinder(101,4).cut(cq.Solid.makeCylinder(99.6,4)))]
 for i in range(8):tests.append((f'rib{i}',cq.Workplane('XY').box(53,4,3.2,centered=(False,True,False)).translate((44.5,0,0)).val().rotate((0,0,0),(0,0,1),i*45)))
 for name,mask in tests:
  a=old.intersect(mask);b=new.intersect(mask);lost=a.cut(b).Volume();added=b.cut(a).Volume();r={'part':part,'region':name,'lost_mm3':lost,'added_mm3':added};report.append(r);print(r,flush=True);assert lost<1e-4,(part,name,lost)
(D/'protected_regions.json').write_text(json.dumps(report,indent=2))
