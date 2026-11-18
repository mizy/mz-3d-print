import sys,time,json,cadquery as cq
from pathlib import Path
R=Path('/Users/miaozhuang/Projects/mz-3d-print/models/filament-spool-chanel/Source/parametric_rebuild');sys.path.insert(0,str(R));from structural_body import structural_body
D=Path('/tmp/chanel-interface-input/adaptive');center=(.0015810415,-.0274228517)
lock=cq.Shape.importBrep(str(D/'narrow_sewn_lock_tool.brep'));print('LOCK',lock.isValid(),len(lock.Solids()),flush=True)
base=cq.Solid.makeCylinder(29.7,30.8001-23.95,cq.Vector(*center,23.95));inner=cq.Solid.makeCylinder(27.5,12.,cq.Vector(*center,23.9))
print('PIPE FUSE',flush=True);pipe=lock.fuse(base).cut(inner).clean();print('PIPE',pipe.isValid(),len(pipe.Solids()),len(pipe.Faces()),flush=True);assert pipe.isValid() and len(pipe.Solids())==1;pipe.exportBrep(str(D/'narrow_pipe.brep'))
body=structural_body('narrow');print('BODY',body.isValid(),flush=True);full=body.fuse(pipe).clean();print('FULL',full.isValid(),len(full.Solids()),len(full.Faces()),full.Volume(),flush=True);assert full.isValid() and len(full.Solids())==1
full.exportBrep(str(D/'narrow_complete.brep'));full.exportStep(str(D/'narrow_complete.step'),write_pcurves=False)
print('EXPORTED',flush=True)
