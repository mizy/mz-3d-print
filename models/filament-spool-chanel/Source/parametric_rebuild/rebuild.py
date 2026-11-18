"""Full native reconstruction from dimensions and editable arc/line controls.
Writes build_output, not the approved Models file. Revalidate after parameter edits.
"""
import json,time,cadquery as cq
from pathlib import Path
from build import build_flange,PARAMS
from build_lock_pipes import build_pipe
from structural_body import structural_body
R=Path(__file__).resolve().parent;O=R/'build_output';O.mkdir(exist_ok=True)
flange=build_flange();flange.exportStep(str(R/'flange_native_rebuilt.step'),write_pcurves=False)
controls=json.loads((R/'native_lock_sections.json').read_text());shapes={}
for part in ['wide','narrow']:
 pipe=build_pipe(part,controls);body=structural_body(part);extra=[]
 if part=='wide':
  c=(-.02734375,.000549315,0)
  for a in [0,90,180,270]:
   extra.append(cq.Workplane('XY').box(5.9,1.2,25.7150566-22.,centered=(True,True,False)).translate((36.15+c[0],c[1],22.)).val().rotate(c,(c[0],c[1],1),a))
 s=body.fuse(pipe,*extra);assert s.isValid() and len(s.Solids())==1;shapes[part]=s;s.exportBrep(str(O/f'{part}_complete.brep'));print(part,len(s.Faces()),s.Volume(),flush=True)
a=cq.Assembly(name='CHANEL_parametric_v4')
for part,x in [('wide',-110),('narrow',110)]:a.add(shapes[part],name=part+'_half',loc=cq.Location(cq.Vector(x,0,0)))
p=O/'CHANEL_SOURCE21_parametric_v4.step';a.export(str(p),mode='default',write_pcurves=False)
s=cq.importers.importStep(str(p)).val();assert s.isValid() and len(s.Solids())==2
print('REIMPORT',s.isValid(),len(s.Solids()),p.stat().st_size,flush=True)
