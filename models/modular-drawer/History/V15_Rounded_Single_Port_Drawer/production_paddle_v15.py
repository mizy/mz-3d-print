"""V15 rounded single paddle; exact keep-out geometry and integral keyed shaft from V14."""
import itertools, math
import FreeCAD as A, Part
from production_cams import S,M,C,B,leftRight
V=A.Vector
def _blend(x,y,z,t,scale=1.,off=0.):
    # Molded YZ section. One curved tangent flank connects the round shoulder
    # to a real planar small stop face. At t=0 the seven edges are exact arcs
    # of the original shaft circle; full body has a 1.56-mm-wide flat tip.
    r=1.50
    angles=[-152.,-133.,-113.,-67.,-47.,-28.]
    ring=[(r*math.cos(math.radians(u)),r*math.sin(math.radians(u))) for u in angles]
    targets=[ring[0],(-1.,-1.62),(-1.,-3.06),(-.78,-3.28),(.78,-3.28),(1.,-3.06),(1.,-1.62),ring[5]]
    # Resample underside circle with eight equivalent arc-break points:
    aa=[-152.,-139.,-125.,-113.,-67.,-55.,-41.,-28.]
    circ=[(r*math.cos(math.radians(u)),r*math.sin(math.radians(u))) for u in aa]
    def P(u):return V(x,y+scale*u[0],z+off+scale*u[1])
    def blend(a,b):return ((1-t)*a[0]+t*b[0],(1-t)*a[1]+t*b[1])
    q=[blend(a,b) for a,b in zip(circ,targets)]
    # An endpoint tangency to the major circular shoulder is part of both shape versions.
    def bez(left,stop):
        start=q[0] if left else q[-1]
        amb=aa[0] if left else aa[-1]
        theta=math.radians(amb)
        # Radius tangent orientation points down and inward from each side.
        tangent=(math.sin(theta),-math.cos(theta)) if not left else (-math.sin(theta),math.cos(theta))
        a=(start[0]+tangent[0]*.58,start[1]+tangent[1]*.58)
        b=(stop[0],stop[1]+.44)
        e=Part.BezierCurve();e.setPoles([P(start),P(a),P(b),P(stop)])
        return e.toShape()
    top=Part.Arc(P(q[-1]),P((0,r)),P(q[0])).toShape()
    def arc_part(i):
        mid=math.radians((aa[i]+aa[i+1])/2)
        return Part.Arc(P(q[i]),P((r*math.cos(mid),r*math.sin(mid))),P(q[i+1])).toShape()
    if t<=1e-9:return Part.Wire([top]+[arc_part(i) for i in range(7)])
    left_curve=bez(True,q[1]);right_curve=bez(False,q[-2]);right_curve.reverse()
    def curve_round(i,target):
        mid=math.radians((aa[i]+aa[i+1])/2)
        return Part.Arc(P(q[i]),P(blend((r*math.cos(mid),r*math.sin(mid)),target)),P(q[i+1])).toShape()
    L=lambda i:Part.makeLine(P(q[i]),P(q[i+1]))
    k=.22*math.sqrt(.5)
    rim=[top,left_curve,L(1),curve_round(2,(-.78-k,-3.06-k)),L(3),curve_round(4,(.78+k,-3.06-k)),L(5),right_curve]
    return Part.Wire(rim)

def blade_solid(y,z):
    W=lambda x,t,scale=1.,off=0.:_blend(x,y,z,t,scale,off)
    # A root sweep grows out of the frame's round shaft inside the current
    # envelope. The central operative faces are straight; a contraction loft
    # forms the smooth closed tip rather than stacking a sphere onto a slab.
    # Controlled sections approximate the radiused root/nose with no step.
    starts=[W(13.59,0),W(14.25,0),W(15.3,.04),W(16.2,.26),W(16.85,.79),W(17.80,1)]
    flat=Part.Face(W(17.80,1)).extrude(V(4.18,0,0))
    end=[W(21.98,1),W(22.32,1,.988,.016),W(22.74,1,.919,.105),W(23.10,1,.785,.263),
         W(23.40,1,.556,.546),W(23.52,1,.285,.887),W(23.55,1,.10,1.145)]
    root=Part.makeLoft(starts,True,False)
    tip=Part.makeLoft(end,True,False)
    # Fusing exact matching section boundaries keeps one analytic BRep.
    return S(flat.multiFuse([root,tip]))
def apply_rectangle(a,w,d,h):
 y=d/2;z=h-2.17
 root=a[16].common(B(6,y-5,z-6,13.65,y+5,z+6))
 blade=blade_solid(y,z)
 left=S(root.fuse(blade))
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
 return a,dict(tab_span_x_mm=[13.59,23.55],flat_stop_span_x_mm=[17.80,21.98],tab_thickness_along_Y_mm=2.0,
  flank_profile='tangent cubic blend from R1.50 upper shoulder into flat cheeks with R0.22 toe',
  plan_geometry='one molded loft with blended shoulders and softly closed nose, flat stopper face, integral keyed axle',test=report)
