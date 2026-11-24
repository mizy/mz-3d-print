"""V13 one-piece .36-mm diametric-clearance keyed paddle. Analytic BRep, no elastic assembly dependency."""
import itertools,math
import FreeCAD as A,Part
V=A.Vector
def B(x,y,z,dx,dy,dz):return Part.makeBox(dx,dy,dz,V(x,y,z))
def S(q):
 r=q.removeSplitter();assert r.isValid() and len(r.Solids)==1,(r.isValid(),len(r.Solids))
 return r.Solids[0]
def c(a,b):
 x,y=a.BoundBox,b.BoundBox
 if any(min(getattr(x,k+'Max'),getattr(y,k+'Max'))<max(getattr(x,k+'Min'),getattr(y,k+'Min'))+1e-7 for k in 'XYZ'):return 0.
 return a.common(b).Volume
SERVICE_ANGLE=120
def key_witness(w,d,h,side,paddle):
 px=w/2; y=d/2;z=h-2.17; a=V(0,y,z)
 cx=lambda x,l,r:Part.makeCylinder(r,l,V(x,y,z),V(1,0,0))
 spin=lambda q,ang:q.rotated(a,V(1,0,0),ang)
 mf=lambda q:q.mirror(V(px,0,0),V(1,0,0))
 # Material fills the old transverse axle bore and creates a positive overlap into the hub.
 # An integral single tang lives in the external part of the little blind thrust chamber.
 stem=cx(8.53,3.01,1.00)
 fill=cx(11.31,21.90-11.31,1.11)
 lug=B(8.53,y+.72,z-.46,.82,.76,.92)
 left_moving=S(paddle[0].multiFuse([stem,fill,lug]))
 right_moving=mf(left_moving)
 # Journal plus private annular thrust chamber, and an axial key path cut at one angular orientation.
 # Clear the old blind Ø1.58 pilot entirely where the shaft turns.
 move_J=cx(8.40,11.37-8.40,1.18)
 chamber=cx(8.43,9.52-8.43,1.70)
 slot_blank=B(8.42,y+.56,z-.64,3.02,1.12,1.28)
 passage=spin(slot_blank,SERVICE_ANGLE)
 # The extra angle is serviced only on rear upper side of existing cavity. The frontal hard shoulder stays untouched.
 pocket=B(11.14,y+.48,z+1.03,2.53,3.19,1.18)
 cutting=[move_J,chamber,passage,pocket]
 left=S(side[0].cut(cutting));right=S(side[1].cut([mf(move_J),mf(chamber),spin(mf(slot_blank),SERVICE_ANGLE),mf(pocket)]))
 for j,old,new in zip((0,1),side,(left,right)):
  shoulder=old.common(spin(paddle[j],-5))
  lost=shoulder.cut(new).Volume
  print('hard shoulder ROI material lost mm3:',lost,flush=True)
  assert lost<.0005,lost
 seats=[left,right]; stops=[left_moving,right_moving]
 insertion=[]
 for i,j in enumerate((1,-1)):
  r=spin(stops[i],SERVICE_ANGLE)
  residuals=[]
  for u in (0,.05,.15,.25,.4,.6,.85,1.05,1.35,1.6,2,2.35,2.75,3,3.5,4.25,5,6):
   a0=r.translated(V(j*u,0,0));v=c(a0,seats[i]);residuals.append(v)
   if v>.0005:print('axial path failure',i,u,v,a0.common(seats[i]).optimalBoundingBox(),flush=True)
  insertion.append(max(residuals))
 print("insertion geometrical interference",insertion,flush=True)
 assert max(insertion)<.0005,insertion
 rotation=[max(c(spin(s,n),o) for n in range(SERVICE_ANGLE+1)) for s,o in zip(stops,seats)]
 print("service rotation geometrical interference",rotation,flush=True)
 assert max(rotation)<.0006,rotation
 block=[]
 for i,j in enumerate((1,-1)):
  for n in range(0,91,5):
   tau=spin(stops[i],n)
   val=c(tau.translated(V(j*.45,0,0)),seats[i])
   block.append(val);assert val>.03,(i,n,val)
 shoulder=[c(spin(s,-5),o) for s,o in zip(stops,seats)]
 assert min(shoulder)>.20,shoulder
 # Geometric take-up from seated depth, not a strength or endurance result.
 hard_capture=[c(s.translated(V(j*.28,0,0)),o) for j,s,o in zip((1,-1),stops,seats)]
 assert min(hard_capture)>.01,hard_capture
 return seats,stops,dict(pivot_mm=[y,z],normal_rot_range_deg=[0,90],service_angle_deg=SERVICE_ANGLE,
   axle_radius_mm=1.,journal_radius_mm=1.18,capture_chamber_radius_mm=1.70,min_nominal_roof_mm=.47,
   insertion_rigid_sampled_overlap_mm3=insertion,rotation_path_0_to_120_overlap_mm3=rotation,
   min_axial_interference_with_forced_extraction_mm3=min(block),axial_test_applied_pull_mm=.45,
   approx_normal_seated_axial_take_up_mm=.17,hard_back_shoulder_at_minus5deg_overlap_mm3=shoulder)
