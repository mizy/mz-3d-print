"""Export current STEP parts from the independently re-read closed assembly."""
from pathlib import Path
import FreeCAD as A,Part,sys,hashlib,json
from step_units import ensure_mm
root=Path(sys.argv[1]); step=root/'STEP'
path=step/'00_Four_Cam_Closed_Assembly.step';q=Part.read(str(path))
assert q.isValid() and len(q.Solids)==23
p=q.Solids;V=A.Vector
def save(file,s):
 f=step/file;s.exportStep(str(f));ensure_mm(f,s);o=Part.read(str(f))
 assert o.isValid() and len(o.Solids)==len(s.Solids)
 assert abs(o.Volume-s.Volume)<.002
 return hashlib.sha256(f.read_bytes()).hexdigest()
targets={ '01_Universal_Side_Panel.step':p[0], '02_Front_Beam.step':p[2], '03_Rear_Board_Four_Cam.step':p[3], '04_Rear_Upper_Straight_Rod.step':p[15], '05_Rear_Upper_Cam_11p2mm.step':p[17], '08_Drawer_Stop_Paddle.step':p[4], '09_Lower_Cam_11p2mm.step':p[12], '10_Lower_Straight_Rod.step':p[8], '11_Cam_Axial_Keeper_Pin.step':p[19], '27_Cinnamoroll_Corner_Relief_Drawer.step':p[14].translated(V(-25.6,-8,-10))}
proof={f:save(f,s) for f,s in targets.items()}
(root/'QA'/'parts-readback.json').write_text(json.dumps(proof,indent=2)+'\n')
print('Verified',len(proof),'individual BRep STEP files')
