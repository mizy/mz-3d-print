"""One continuous rectangular paddle and integral keyed axle; retains the exact in-frame V13 root."""
import itertools
import FreeCAD as A, Part
from production_cams import S,M,C,B,leftRight
V=A.Vector
def apply_rectangle(a,w,d,h):
 y=d/2;z=h-2.17
 root=a[16].common(B(6,y-5,z-6,13.65,y+5,z+6))
 hub=Part.makeCylinder(1.5,23.10-13.63,V(13.63,y,z),V(1,0,0))
 blade=B(16.2,y-1.0,z-3.28,23.55,y+1.0,z-.40)
 left=S(root.multiFuse([hub,blade]))
 stops=[left,leftRight(left,w)]
 seat=a[:2];piv=V(0,y,z);tangent=V(1,0,0)
 R=lambda q,k:q.rotated(piv,tangent,k)
 report=[]
 for j,v in enumerate(stops):
  sr=seat[j];sg=-1 if j else 1
  f=lambda shape,dx:M(shape,x=sg*dx)
  working=max(C(f(R(v,ang),dx),sr) for ang,dx in itertools.product(range(0,91,6),(-.08,0.,.145)))
  service=max(C(R(v,ang),sr) for ang in range(0,121))
  path=max(C(f(R(v,120),dx),sr) for dx in (0,.05,.2,.34,.48,.66,.9,1.2,1.55,1.8,2.,2.2,2.5,3,3.5,4.2,5,6))
  block=min(C(f(R(v,n),.45),sr) for n in range(0,91,5))
  original_witness=C(R(a[16+j],-5),sr)
  hard=C(R(v,-5),sr)
  assert max(working,service,path)<.0006 and block>.03 and abs(original_witness-hard)<.0005,(working,service,path,block,original_witness,hard)
  upper=C(R(v,120),sr.translated(V(0,0,h)))
  report.append(dict(hand=j,pivot_yz_mm=[y,z],working_axial_play_check_mm3=working,service_sweep_mm3=service,
    axial_service_slide_mm3=path,locked_axial_capture_min_mm3=block,hard_stop_witness_mm3=hard,service_stack_overlap_mm3=upper))
 a=a[:];a[16:18]=stops
 return a,dict(tab_span_x_mm=[16.20,23.55],tab_length_mm=7.35,tab_thickness_along_Y_mm=2.0,
  tab_radial_height_mm=2.88,plan_geometry='one continuous rectangle, circular hub, integral keyed axle',test=report)
