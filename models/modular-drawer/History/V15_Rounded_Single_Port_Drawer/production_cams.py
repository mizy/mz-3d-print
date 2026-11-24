"""V15 matched single-service-face cam stations in the FRONT full scale and FOUR compact REAR stations."""
from pathlib import Path
import json,itertools,math
import FreeCAD as A,Part
from coupon_exact_core import get
V=A.Vector;X,Y,Z=V(1,0,0),V(0,1,0),V(0,0,1)
def B(x0,y0,z0,x1,y1,z1):return Part.makeBox(x1-x0,y1-y0,z1-z0,V(x0,y0,z0))
def S(q):
 s=q.removeSplitter();assert s.isValid() and len(s.Solids)==1,(s.isValid(),len(s.Solids));return s.Solids[0]
def M(q,x=0,y=0,z=0):return q.translated(V(x,y,z))
def C(q,a):
 x,y=q.BoundBox,a.BoundBox
 if any(min(getattr(x,k+'Max'),getattr(y,k+'Max'))<max(getattr(x,k+'Min'),getattr(y,k+'Min'))+1.e-7 for k in 'XYZ'):return 0.
 return q.common(a).Volume
def cyl(p,r,l,ax):return Part.makeCylinder(r,l,p,ax)
def leftRight(q,w):
 b=q.optimalBoundingBox()
 matrix=A.Matrix();matrix.A11=-1;matrix.A14=w
 r=q.copy();r.transformShape(matrix,True,True)
 c=r.optimalBoundingBox()
 assert max(abs(i-j) for i,j in zip((c.XMin,c.YMin,c.ZMin,c.XMax,c.YMax,c.ZMax),(w-b.XMax,b.YMin,b.ZMin,w-b.XMin,b.YMax,b.ZMax)))<1e-5
 return r
def integrate(q,w,d,h,source):
 m=get(source);sf=.47;origC=V(25.55,8,5)
 lf,rf,fo,back=q[:4]; y=d-3.20
 # Front stock is the exact replacement solid from the main-body front coupon.
 cx=WEND=32.25
 front_core=fo.common(B(cx,-.01,-.01,w-cx,16.01,9.82))
 fo=S(front_core.multiFuse([m['beam'],leftRight(m['beam'],w)]))
 zlow=5.;zhigh=h-5.
 # Unlike the standalone coupon, the real side pier crosses the vertical drop path.
 # Open the same T-shaped retaining section toward the frame end, UNDER the bearing surface.
 # The metal/printed rod is fed along Y before bringing the side boards toward the beams.
 front_cuts=[B(10.54,-.08,2.36,13.24,10.76,7.64),
             B(13.23,-.08,2.62,17.51,10.38,7.38)]
 lf=S(lf.cut(front_cuts))
 rf=S(rf.cut([leftRight(a,w) for a in front_cuts]))
 info=[];rr=[{'key':'front','scale':1.,'x':25.55,'y':8.,'z':5.,'register':17.3},
  {'key':'rear_lower','scale':sf,'x':17.30+8.25*sf,'y':y,'z':zlow,'register':17.30},
  {'key':'rear_upper','scale':sf,'x':13.65+8.25*sf,'y':y,'z':zhigh,'register':13.65}]
 ports=[]
 backRestore=[];backCuts=[];sideRestore=[];sideCuts=[]
 for num,station in enumerate(rr):
  cx,cy,cz=[station[k] for k in ('x','y','z')];cp=V(cx,cy,cz);scale=station['scale']
  if num==0: tf=lambda s:s
  else:
   # Compact rear is a true analytic 0.47 scale of the same functional module,
   # then extended tool bores and rod loading routes adapt to the 6.50-mm web.
   tf=lambda s:s.scaled(scale,origC).translated(cp-origC)
   x_old=22.30 if num==1 else 18.65
   xstart=station['register']
   backRestore.extend([cyl(V(x_old,d-5.6232,cz),2.0117,5.6232,Y),
    cyl(V(xstart,cy,cz),1.1845,3.4,X)])
   seat_y=cy+(1.70-8)*scale
   backCuts.extend([cyl(V(cx,seat_y,cz),4.28*scale,d-seat_y+.11,Y),
      tf(cyl(V(17.26,8,5),2.38,5.01,X))])
   if num==1:sideRestore.append(cyl(V(11.199,cy,cz),1.1601,17.30-11.199,X))
   else:sideRestore.append(cyl(V(7.30,cy,cz),1.1601,13.65-7.30,X))
   # Accessible axial Y-end opening with a continuous floor and continuous rail/top.
   for x0,x1,y0,y1,z0,z1 in [(10.54,13.24,5.24,10.76,2.36,7.64),(13.23,17.51,5.62,10.38,2.62,7.38)]:
    bb=tf(B(x0,y0,z0,x1,y1,z1)).optimalBoundingBox()
    sideCuts.append(B(bb.XMin,bb.YMin,bb.ZMin,bb.XMax,d+.15,bb.ZMax))
  mapped={name:tf(m[name]) for name in ('openCam','rod','mainTool','oppositeTool')}
  for hand in (0,1):
   p=V(cx if not hand else w-cx,cy,cz)
   pieces={k:(leftRight(s,w) if hand else s) for k,s in mapped.items()}
   info.append(dict(station=station['key'],hand=hand,pivot=p,ratio=scale,register=station['register'] if not hand else w-station['register'],**pieces))
 for hand,part in enumerate((lf,rf)):
  restore=[leftRight(v,w) if hand else v for v in sideRestore]
  cut=[leftRight(v,w) if hand else v for v in sideCuts]
  s=S(S(part.multiFuse(restore)).cut(cut))
  if hand:rf=s
  else:lf=s
 back=S(S(back.multiFuse(backRestore+[leftRight(x,w) for x in backRestore])).cut(backCuts+[leftRight(x,w) for x in backCuts]))
 q=q[:];q[:4]=[lf,rf,fo,back];q[4:10]=[t['rod'] for t in info]
 def turn(i,s,degs):
  a=info[i]
  return s.rotated(a['pivot'],Y,(-degs if a['hand'] else degs))
 q[10:16]=[turn(i,b['openCam'],84) for i,b in enumerate(info)]
 print('six production cam seats rebuilt',flush=True)
 return q,info,turn

def validate(q,info,turn,d,quick=False):
 frame=q[:4]; rods=q[4:10];openC=[a['openCam'] for a in info];locked=q[10:16]
 # Separate all rods, open cams before closing both side boards along X.
 shift=(0,.12,.40,.75,1.25,2.,3.,4.,5.,7.,9.,12.,16.,20.)
 angular=range(0,85,4 if quick else 2)
 exact_tol=.001
 def maxsum(p,arr):return max([0.]+[C(p,a) for a in arr])
 def spin(i,degree,shape=None):return turn(i,info[i]['openCam'] if shape is None else shape,degree)
 results=[]
 for i,s in enumerate(info):
  name=s['station'];j=s['hand'];direction=-1 if j else 1;k=0 if i<2 else 1
  receiver=frame[2+k]; seat=frame[j]; a=s['ratio']
  row=dict(station=name,hand='R' if j else 'L',ratio=a,pivot_mm=[s['pivot'].x,s['pivot'].y,s['pivot'].z])
  tube=[*frame,*rods[:i],*rods[i+1:],*locked[:i],*locked[i+1:]]
  row['rotor_entry_with_side_rods_off_mm3']=max(maxsum(M(openC[i],y=u),frame[2:]) for u in shift)
  row['rod_insertion_from_open_frame_end_mm3']=max(C(M(rods[i],y=(-u if i<2 else u)),seat) for u in shift)
  row['lock_unlocked_full_sweep_mm3']=max(maxsum(spin(i,n),tube+[rods[i]]) for n in angular)
  row['hard_seating_witness_mm3']=min(C(M(spin(i,n),y=-.04*a),receiver) for n in (0,42,84))
  row['wrong_face_entry_blocked_mm3']=C(M(openC[i],y=-2.3*a),receiver)
  row['locked_axial_removal_witness_mm3']=min(C(M(locked[i],y=v*a),rods[i]) for v in (.7,1.0))
  row['locked_rod_backout_mm3']=C(M(rods[i],x=-direction*2.4*a),locked[i])
  row['open_rod_release_mm3']=C(M(rods[i],x=-direction*2.4*a),openC[i])
  row['rod_captured_by_side_keyway_mm3']=C(M(rods[i],x=direction*.40*a),seat)
  path=[]
  # Both real blades incl. handles: reposition/remove DRAWER before working on rear (the local insertion path is through its empty bay).
  # Compact rear inner tool uses a longer thin shank so its oversized handle does not enter frame stock at the low rear shelf.
  for k,sign in (('mainTool',1.),):
   tool=s[k]
   if k=='oppositeTool' and i>=2:
    pp=s['pivot'];sy=pp.y+(1.63-8)*a
    origTip=tool.common(B(pp.x-3.,sy-.12,pp.z-2.,pp.x+3.,sy+1.5,pp.z+2.))
    shank=cyl(V(pp.x,sy,pp.z),2.17*a,10.,-Y)
    grip=cyl(V(pp.x,sy-9.9,pp.z),4.4*a,5.2,-Y)
    tool=S(origTip.multiFuse([shank,grip]))
   toolPath=max(maxsum(M(spin(i,n,tool),y=sign*u),tube+[rods[i],spin(i,n)]) for n in (0,42,84) for u in shift)
   toolTurn=max(maxsum(spin(i,n,tool),tube+[rods[i],spin(i,n)]) for n in angular)
   couple=min(C(spin(i,t,tool),openC[i]) for t in (-6,6))
   path.append(dict(face=k,insertion_removal_max_mm3=toolPath,rotation_max_mm3=toolTurn,mismatched_angle_drive_witness_mm3=couple))
  row['tools']=path
  yy=s['pivot'].y+(1.70-8)*a
  row['service_face']='positive_Y_only'
  cap=cyl(V(s['pivot'].x,yy-.20*a,s['pivot'].z),2.10*a,.16*a,Y)
  row['closed_opposite_housing_port_material_fraction']=C(cap,receiver)/cap.Volume
  rear_face=cyl(V(s['pivot'].x,yy+.12*a,s['pivot'].z),.66*a,.36*a,Y)
  row['closed_opposite_rotor_face_material_fraction']=C(rear_face,locked[i])/rear_face.Volume
  assert min(row['closed_opposite_housing_port_material_fraction'],row['closed_opposite_rotor_face_material_fraction'])>.999
  print('station witness',json.dumps(row),flush=True)
  clear=[row[k] for k in ('rotor_entry_with_side_rods_off_mm3','rod_insertion_from_open_frame_end_mm3','lock_unlocked_full_sweep_mm3','open_rod_release_mm3')]
  clear +=[p[v] for p in path for v in ('insertion_removal_max_mm3','rotation_max_mm3')]
  assert max(clear)<exact_tol,(i,clear)
  for k0,lim in [('hard_seating_witness_mm3',.08),('wrong_face_entry_blocked_mm3',.8),
     ('locked_axial_removal_witness_mm3',.007),('locked_rod_backout_mm3',.007),('rod_captured_by_side_keyway_mm3',.003)]:
   assert row[k0]>lim,(i,k0,row[k0])
  assert min(p['mismatched_angle_drive_witness_mm3'] for p in path)>.0006
  results.append(row)
 close=[]
 for j,direction in ((0,1),(1,-1)):
  mov=[frame[j]]+[rods[i] for i in (j,j+2,j+4)]
  fixed=frame[2:]+openC+[frame[1-j]]+[rods[i] for i in (1-j,3-j,5-j)]
  close.append(max(maxsum(M(q,x=-direction*u),fixed) for u in shift for q in mov))
 assert max(close)<.0008,close
 return dict(stations=results,all_three_stations_per_side_simultaneous_closure_max_mm3=close,
   tooling_note='Large-mouth cam insertion first, feed each rod along Y from the nearest open side board end, slide free side panels toward beams with cams open, then close each. Front services only from the empty drawer bay. Rear services only outside the back; allow tool/hand room before installing the cabinet.')
