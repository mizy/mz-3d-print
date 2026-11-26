"""Nominal rigid local beam release: own outer access is freed, neighboring bay stays assembled.

Assumes the tested bay is unloaded and its drawer removed. No return in this script
is a load, torque, flex, fatigue or print-test result. Checks Y-axis rotation of cams
and X-directed withdrawal as discrete poses; it does not model the entire surrounding cabinet.
"""
import sys,itertools,json,hashlib
from pathlib import Path
import FreeCAD as A,Part
V=A.Vector; Y=V(0,1,0)
f=Path(sys.argv[1]); p=list(Part.read(str(f)).Solids)
assert len(p)==74
def M(s,d):return s.translated(V(d,0,0))
def bs(s):
 c=s.BoundBox
 return tuple((getattr(c,k+'Min'),getattr(c,k+'Max')) for k in 'XYZ')
def k(s):return (s,bs(s))
def C(a,b):
 if any(min(q[1],w[1])<=max(q[0],w[0])+1.e-6 for q,w in zip(a[1],b[1])):return 0.
 return a[0].common(b[0]).Volume
def piv(s):
 cs=[f.Surface for f in s.Faces if type(f.Surface).__name__=='Cylinder' and abs(f.Surface.Axis.y)>.999]
 c=max(cs,key=lambda v:v.Radius)
 return c.Center
left_cams={9,11,13,24,26,28}
angles=(0,3,6,12,18,24,30,36,42,48,54,60,66,72,78,84)
travel=(0,.10,.25,.5,1,1.5,2,2.4,3.5,4.5,6,8,10,12)
cases=[
 ('left_front',3,(9,10),(5,33),(33,),-1,18),
 ('right_front',18,(24,25),(34,20),(34,),+1,3),
 ('left_rear',4,(11,12,13,14),(6,35,7,8),(35,8),-1,19),
 ('right_rear',19,(26,27,28,29),(36,21,22,23),(36,22),+1,4)]
results=[]
for title,beam,camids,own_rods,inner,sign,neighbor in cases:
 params={i:(piv(p[i]),-1 if i in left_cams else 1) for i in camids}
 def orient(i,a):
  axis,s=params[i];return p[i].rotated(axis,Y,s*a)
 # Both of the same bay's ends are set open, all original solid positions used for opening.
 # Keep the opposite bay in its original STEP locked position for every sample.
 neighbor_group=list(range(18,33))+[34,36,2] if sign<0 else list(range(3,18))+[33,35,0]
 fixed_before_open=[k(p[i]) for i in set([0,1,2,beam,*own_rods,*neighbor_group])]
 rotation=0.
 for i,a in itertools.product(camids,angles):
  rot=k(orient(i,a))
  rotation=max(rotation,*[C(rot,t) for t in fixed_before_open])
 open_moving=[p[beam],*[orient(i,84) for i in camids]]
 # Free/drop the tested bay outer board and its own outer rods as required for X withdrawal.
 # Keep its center rods, shared board, and the WHOLE other bay identically seated and locked.
 fixed=[k(p[i]) for i in set([1,*inner,*neighbor_group])]
 motion=0.
 for q,x in itertools.product(open_moving,travel):
  pose=k(M(q,x*sign))
  motion=max(motion,*[C(pose,t) for t in fixed])
 blocked=[]
 for i,j in zip((camids[1],camids[3]) if sign<0 and len(camids)==4 else (camids[0],camids[2]) if len(camids)==4 else (camids[1],) if sign<0 else (camids[0],),inner):
  # Relative between the head and its own closed eccentric while beam is pulled away.
  arr=max(C(k(M(p[i],sign*d)),k(p[j])) for d in (.5,1,1.5,2,2.4,3,4))
  blocked.append(arr)
 res=dict(case=title,neighbor_beam_fixed_locked_solid_index=neighbor,own_open_rotation_sample_count=len(angles),rotating_cam_count=len(camids),
  cam_rotation_sampled_overlap_mm3=rotation,outer_board_cleared_before_withdrawal=True,open_beam_X_withdrawal_poses=len(travel),
  open_beam_X_withdrawal_end_mm=sign*travel[-1],open_beam_X_withdrawal_overlap_mm3=motion,closed_move_positive_block_witnesses_mm3=blocked)
 print(json.dumps(res),flush=True)
 assert max(rotation,motion)<.001 and min(blocked)>.002,(title,res)
 results.append(res)
if len(sys.argv)>2:
 Path(sys.argv[2]).write_text(json.dumps(dict(step_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),scope=__doc__,samples=results),ensure_ascii=False,indent=2)+'\n')
