import cadquery as cq,time,json
from pathlib import Path
D=Path('/tmp/chanel_compact_v6');t=time.time();s=cq.importers.importBrep('/tmp/chanel-interface-input/adaptive/narrow_pipe_sewn.brep').val();print('original',len(s.Faces()),s.Volume(),flush=True)
c=(.0015810415,-.0274228517);z0=23.95;hi=34.1129523682
r=29.7
mask=cq.Solid.makeCylinder(r,hi-z0+2,cq.Vector(*c,z0-1));base=cq.Workplane('XY').center(*c).circle(r).circle(27.5).extrude(hi-z0).translate((0,0,z0)).val()
print('cut start',flush=True);teeth=s.cut(mask);print('cut end',len(teeth.Faces()),len(teeth.Solids()),time.time()-t,flush=True)
print('fuse start',flush=True);out=base.fuse(teeth).clean();print('RESULT',out.isValid(),len(out.Solids()),len(out.Faces()),out.Volume(),time.time()-t,flush=True);out.exportBrep(str(D/'narrow_exact_nominal_base.brep'))
