"""Verify both travel limit paddles from the delivered STEP, not the CAD build."""
import FreeCAD as A,Part,sys,json,hashlib
from pathlib import Path
V=A.Vector
root=Path(sys.argv[1]);f=root/'STEP'/'00_Four_Cam_Closed_Assembly.step'
shape=Part.read(str(f)); r=shape.Solids
assert shape.isValid() and len(r)==23
def C(a,b):
 ba,bb=a.BoundBox,b.BoundBox
 if any(min(getattr(ba,k+'Max'),getattr(bb,k+'Max'))-max(getattr(ba,k+'Min'),getattr(bb,k+'Min'))<1e-6 for k in 'XYZ'):return 0.
 return a.common(b).Volume
def m(s,a):return s.translated(V(0,-a,0))
def R(s,k):
 t=s.copy();t.rotate(V(0,125,97.83),V(1,0,0),k);return t
chosen=[0,85,100,103,104,104.25,104.5,104.75,105,106,107,108,110.5,115,125,150,175,200,220,240]
on=[];off=[];fixed=[];
for d in chosen:
 tray=m(r[14],d)
 on.append([d,*[round(C(tray,r[i]),7) for i in (4,5)]])
 off.append([d,*[round(C(tray,R(r[i],90)),7) for i in (4,5)]])
 fixed.append([d,round(max(C(tray,r[i]) for i in range(23) if i not in (4,5,14)),7)])
assert all(max(x[1:])<.001 for x in off+fixed)
before=max(row[0] for row in on if row[0]<105 and max(row[1:])<.001)
after=min(row[0] for row in on if min(row[1:])>.001)
assert before<after<=105
for i,side in ((4,0),(5,1)):
 assert max(C(R(r[i],k),r[side]) for k in (0,15,30,45,60,75,90))<.001
res=dict(source_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),pivot_yz_mm=[125,97.83],released_deg=90,nominal_contact_bracket_mm=[before,after],engaged_samples=on,released_samples=off,fixed_frame_samples=fixed,
 limits='Rigid CAD witness only; no force, wear, print tolerance or continuous swept interference claim.')
dest=Path(sys.argv[2]);dest.write_text(json.dumps(res,indent=2)+'\n')
print('PASS travel limit engages on both sides; sampled release and fixed frame travel to 240 mm',before,after)
