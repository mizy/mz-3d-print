"""Verify V14 final exported BRep occurrences and structural support against the approved seed."""
from pathlib import Path
import json,sys,itertools
import FreeCAD as A,Part
from production_cams import C,B
V=A.Vector
p=Path(sys.argv[1]);seed=Path(sys.argv[2]);o=Part.read(str(seed)).Solids
def rd(name,n):
 s=Part.read(str(p/name))
 assert len(s.Solids)==n and s.isValid(),name
 return s
mod=rd('Reference/V14_Modular_Closed.step',19);u=rd('Reference/V14_Modular_Open.step',19)
mono=rd('Reference/V14_One_Piece_Closed.step',4);v=rd('Reference/V14_One_Piece_Open.step',4)
f=rd('Print_Parts/One_Piece_Frame.step',1)
def sig(q):
 return sorted((type(f.Surface).__name__,round(f.Area,4),tuple(round(a,4) for a in (f.CenterOfMass.x,f.CenterOfMass.y,f.CenterOfMass.z))) for f in q.Faces)
def bb(q):
 b=q.optimalBoundingBox();return [round(k,5) for k in (b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax)]
r=mod.Solids;rm=mono.Solids
assert sig(r[-1])==sig(o[-1])==sig(rm[-1])
assert sig(rm[0])==sig(f.Solids[0])
for k,a,b in [(0,r[16],rm[1]),(1,r[17],rm[2])]:
 assert len(a.Solids)==1 and sig(a)==sig(b)
 assert len(rd('Print_Parts/'+('Left' if k==0 else 'Right')+'_Integrated_Rectangular_Paddle.step',1).Solids)==1
for s,t in [(mod,u),(mono,v)]:
 assert all(sig(x)==sig(y) for x,y in zip(s.Solids[:-1],t.Solids[:-1]))
 assert sig(s.Solids[-1].translated(V(0,-90.5,0)))==sig(t.Solids[-1])
assert bb(mod)==bb(mono)==[0.,0.,0.,180.,200.,52.]
assert bb(f)==[0.,0.,0.,180.,200.,52.]
camdata=[]
for i,(x,y,z,r0) in enumerate(((25.55,8,5,4.1),(154.45,8,5,4.1),(21.1775,196.8,5,1.927),(158.8225,196.8,5,1.927),(17.5275,196.8,47,1.927),(162.4725,196.8,47,1.927))):
 q=r[10+i].optimalBoundingBox()
 assert max(abs(a-b) for a,b in zip((q.XMin,q.ZMin,q.XMax,q.ZMax),(x-r0,z-r0,x+r0,z+r0)))<.0002
 camdata.append(dict(position=[x,y,z],radius_mm=r0,true_analytic_cylinders=sum(type(f.Surface).__name__=='Cylinder' for f in r[10+i].Faces)))
rails=[]
for i,(x0,x1) in enumerate(((13.651,17.299),(162.701,166.349))):
 for z in (0,10):
  clip=B(x0,-.01,z-.00002,x1,200.01,z+.00002)
  a=o[i].common(clip);b=r[i].common(clip)
  dv=a.cut(b).Volume+b.cut(a).Volume;assert dv<.00032
  rails.append(dv)
phase=dict(printed_part_counts=[19,4,1],cam_occurrences=camdata,drawer_exact_same= True,side_tracks_near_bed_and_top_geometric_residuals_mm3=rails)
(p/'Independent_BRep_Readback.json').write_text(json.dumps(phase,indent=2)+'\n')
print(json.dumps(phase),flush=True)
