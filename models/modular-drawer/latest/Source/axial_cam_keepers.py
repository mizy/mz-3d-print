"""Straight removable axial keeper pins for the front and rear drop-in beams.

Rear pins enter from the side-plate top, front pins from its underside. After
a beam+rod group is seated from the end, the pins positively retain the T feet
along Y; keyed cams still provide the lateral lock. No added external depth.
"""
import FreeCAD as A,Part
V=A.Vector
# Origin is the pin axis at each side panel's lower/upper planar entry.
# left universal panel mirrors about x=20.3, right side is translated 154.7 mm.
X0=20.3; X_MAG=2.9; FRONT=8.85; REAR=242.60
STATIONS=((FRONT,0,1),(REAR,100,-1))
def c(a,b):
 if not a.BoundBox.intersect(b.BoundBox):return 0.
 return a.common(b).Volume
def once(s):
 s=s.removeSplitter()
 assert s.isValid() and len(s.Solids)==1
 return s.Solids[0]
def cylinder(x,y,z,r,l,d):
 return Part.makeCylinder(r,l,V(x,y,z),V(0,0,d))
def pin(x,y,z,d,press=True):
 # The 2.8 mm shear section spans the slot and is supported by the wall
 # both above and below. A small head sits 0.08 mm below its entry surface.
 z0=z+.08*d
 head=cylinder(x,y,z0,1.59,1.38,d)
 shank=cylinder(x,y,z+1.36*d,1.4,10.25,d)
 nose=Part.makeCone(1.4,1.06,.41,V(x,y,z+11.60*d),V(0,0,d))
 pieces=[shank,nose]
 if press:
  # Local friction collar prevents the bottom-entry keeper dropping out.
  # The load-bearing shaft remains 2.8 mm; only the near-cap collar presses.
  pieces.extend([Part.makeCone(1.38,1.51,.24,V(x,y,z+1.60*d),V(0,0,d)),
   cylinder(x,y,z+1.83*d,1.51,.32,d),
   Part.makeCone(1.51,1.38,.24,V(x,y,z+2.14*d),V(0,0,d))])
 return once(head.fuse(pieces))
def bore(x,y,z,d):
 shaft=cylinder(x,y,z-.02*d,1.47,12.18,d)
 cap=cylinder(x,y,z-.03*d,1.67,1.56,d)
 # Mating access relief at the entry surface, open to the nearest end.
 # Apply tool only after turning cams off and unloading the joint.
 y0,y1=sorted((y,245.08 if d<0 else 4.92))
 z0,z1=sorted((z-.03*d,z+1.57*d))
 pry=Part.makeBox(1.05,y1-y0,z1-z0,V(x-.525,y0,z0))
 return shaft.fuse([cap,pry]).removeSplitter()
def build(side_left,side_right):
 grooves=[bore(X0+s*X_MAG,*q) for s in [-1,1] for q in STATIONS]
 left=once(side_left.cut(grooves))
 right=once(side_right.cut([s.translated(V(154.7,0,0)) for s in grooves]))
 assert max(left.cut(side_left).Volume,right.cut(side_right).Volume)<.001
 pin_rows=[(x,y,z,d) for y,z,d in STATIONS for x in (X0+X_MAG,195.3-(X0+X_MAG))]
 pins=[pin(*q) for q in pin_rows]
 for a,b in zip([left,right,left,right],pins):
  assert .001<c(a,b)<.5
 return left,right,pins,pin_rows
def verify(r,pin_rows):
 pins=r[19:23]
 pairs={'front':((2,6,7,10,11),(19,20),-1),'rear':((3,8,9,12,13,15,16,17,18),(21,22),1)}
 fit={}
 allowed={(0,19),(1,20),(0,21),(1,22)}
 seat_contact=[[j,k,round(c(r[j],r[k]),7)] for j,k in sorted(allowed)]
 assert all(.001<row[2]<.5 for row in seat_contact),seat_contact
 static=max(c(a,b) for j,a in enumerate(r) for k,b in enumerate(r[j+1:],j+1) if (j,k) not in allowed)
 assert static<.001,static
 for name,(grp,ids,sign) in pairs.items():
  def sample(delta,keepers):
   obstacles=[r[0],r[1],*([r[i] for i in ids] if keepers else [])]
   return max(c(r[i].translated(V(0,sign*delta,0)),o) for i in grp for o in obstacles)
  path=[[a,round(sample(a,False),7)]for a in [0,.25,.5,1,2,3,5,8,10,12,14,17,20]]
  assert max(x[1] for x in path)<.001,(name,path)
  locked=[[a,round(sample(a,True),7)]for a in [0,.05,.10,.15,.20,.24,.28,.35,.5,.75,1,2,3]]
  positive=[x for x in locked if x[1]>.001]
  assert positive and positive[0][0]<=.5,(name,locked)
  fit[name]=dict(assembly_without_keepers_mm=path,withdrawal_with_keepers_mm=locked,first_sample_with_pin_contact_mm=positive[0][0])
 pin_path=[]
 for j,(x,y,z,d) in enumerate(pin_rows):
  i=19+j
  nominal_pin=pin(x,y,z,d,press=False)
  path=[[a,round(max(c(nominal_pin.translated(V(0,0,-d*a)),o) for k,o in enumerate(r) if k!=i),7)]for a in [0,.1,.3,.8,1,2,4,6,8,10,12,14]]
  assert max(x[1] for x in path)<.001,(j,path)
  pin_path.append(dict(x=x,y=y,entry_z=z,insertion_path_mm=path))
 return dict(axial_locked_and_unlocked=fit,keeper_paths=pin_path,max_static_non_fit_overlap_mm3=static,designed_collar_contact_mm3=seat_contact,
   nominal_diameters_mm={'printed_shaft':2.8,'receiving_bore':2.94,'friction_collar':3.02,'collar_diametral_interference':.08},entry_note='Front from underside, rear from top. Use both pins, check press collar fit and removal on coupon first.',
   limits='Nominal rigid contact, not load capacity, printed fit, extraction force or damage testing.')
