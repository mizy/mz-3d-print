import FreeCAD as A,Part,sys,json
from pathlib import Path
from step_units import ensure_mm
V=A.Vector
r=Part.read(sys.argv[1]).Solids
out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
def b(x,y,z,u,v,w):return Part.makeBox(u-x,v-y,w-z,V(x,y,z))
def m(s,x=0,y=0,z=0):return s.translated(V(x,y,z))
def c(a,b):
 if not a.BoundBox.intersect(b.BoundBox):return 0.
 return a.common(b).Volume
def one(s):
 s=s.removeSplitter()
 assert s.isValid() and len(s.Solids)==1,(s.isValid(),len(s.Solids))
 return s.Solids[0]
def mir(s):return s.mirror(V(97.65,0,0),V(1,0,0))
def ring(x,y,rad): return Part.Wire([Part.makeCircle(rad,V(x,y,92),V(1,0,0))])
def loft(x,y,u,v,rad):return Part.makeLoft([ring(x,y,rad),ring(u,v,rad)],True,True)
def cyl(x,y,rad,length):return Part.makeCylinder(rad,length,V(x,y,92),V(1,0,0))
side=r[0]; yc=238.45; xc=37.2; zc=92.; outer=245.0
def rot(s,a):
 t=s.copy();t.rotate(V(xc,yc,zc),V(0,1,0),a);return t
def prism(x,width,yz):
 pts=[V(x,y,z) for y,z in yz]
 return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(width,0,0))
rod=m(r[8],y=1.45,z=87)
cam=one(m(r[12],y=1.45,z=87).cut(b(xc-.62,243.78,zc-2.7,xc+.62,244.81,zc+2.7)))
fill=b(25.3,238.8,89.1,28.43,245.0,100.0)
rear=one(r[3].fuse([fill,mir(fill)]))
trim=[b(24.9,244.45,89.1,25.3,245.1,95),b(25.29,245,89.1,28.43,245.1,95)]
rear=one(rear.cut(trim+[mir(s) for s in trim]))
pad=prism(25.3,18.7,[(239.05,79.2),(232.35,85.9),(232.35,100),(240,100),(240,79.2)])
rear=one(rear.fuse([pad,mir(pad)]))
seat=Part.makeCylinder(4.28,11.75,V(xc,233.35,zc),V(0,1,0))
entry=cyl(25.24,yc,2.40,8.57)
rear=one(rear.cut([p for k in (seat,entry) for p in (k,mir(k))]))
# A matching stepped return wall keeps the two relieved corners enclosed, with
# 0.80 mm nominated face clearance and an approximately 0.96 mm replacement wall.
core=prism(24.5,20.3,[(240,77.45),(231.55,85.9),(231.55,97),(240.5,97),(240.5,77.45)])
grow=prism(24.45,21.31,[(240,76.092355),(230.59,85.502355),(230.59,97),(240.5,97),(240.5,76.092355)])
patch=grow.cut(core).common(b(25.60,230,76,45.77,238,96))
old=r[14]
basket=one(old.cut([core,mir(core)]).fuse([patch,mir(patch)]))
print('drawer_material',old.Volume,basket.Volume,'patch',patch.Volume,basket.BoundBox,flush=True)
print('static',[(n,round(c(a,b),7)) for n,a,b in [('side/rod',side,rod),('side/rear',side,rear),('rear/rod',rear,rod),('rear/cam',rear,cam),('rod/cam',rod,cam),('drawer/rear',basket,rear)]],flush=True)
def sample(vals,fn):
 return [[t,*[round(x,7) for x in fn(t)]] for t in vals]
open_cam=rot(cam,-80)
turn=sample(list(range(-90,11,5)),lambda a:(c(rod,rot(cam,a)),c(rear,rot(cam,a))))
print('turn',turn,flush=True)
pull=sample([0,-.025,-.05,-.1,-.2,-.3,-.6,-1,-2,-3,-4,-5,-6,-8,-10,-13],lambda x:(c(m(rod,x=x),open_cam),c(m(rod,x=x),rear),c(m(rod,x=x),rot(cam,10))))
print('pull',pull,flush=True)
insert=sample([0,.2,.5,1,2,3,4,5,6,8,10,12],lambda y:(c(m(rod,y=y),side),c(m(open_cam,y=y),rear)))
print('insert',insert,flush=True)
base=r[:15]; full=base[:3]+[rear]+base[4:14]+[basket,rod,m(r[9],y=1.45,z=87),cam,mir(cam)]
right_rod=full[16]
right_cam=full[18]
right_locked=right_cam.copy()
right_locked.rotate(V(158.1,238.45,92),V(0,1,0),-10)
assert c(m(right_rod,x=.6),right_locked)>.15
assert abs(right_rod.BoundBox.ZMin-rod.BoundBox.ZMin)<1e-6
static=max(c(a,b) for i,a in enumerate(full) for b in full[i+1:])
print('max-static',static,flush=True)
travel=[0,-.1,-.3,-.6,-1,-2,-3,-4,-5,-6,-7,-8,-9,-10,-12,-16,-22,-30,-45,-60,-85,-100,-110.5]
drawer=sample(travel,lambda d:(max(c(m(basket,y=d),p) for p in full if p is not basket),))
print('drawer',drawer,flush=True)
assert max(row[1] for row in drawer)<.001
assert max(max(row[1:]) for row in turn+insert)<.001
assert max(max(row[1:3]) for row in pull)<.001 and max(row[3] for row in pull)>.02
assert static<.001
zones=Part.makeCompound([b(25.10,232.34,79.0,44.01,245.10,100.01),b(151.29,232.34,79.0,170.2,245.10,100.01)])
assert rear.cut(r[3]).cut(zones).Volume<.001 and r[3].cut(rear).cut(zones).Volume<.001
assert abs(rear.optimalBoundingBox(False,False).YMax-245)<1e-5
assert abs(basket.optimalBoundingBox(False,False).YMax-old.optimalBoundingBox(False,False).YMax)<1e-5
assert basket.common(b(10,0,0,185,245,75)).cut(old).Volume<.001
assert old.common(b(10,0,0,185,245,75)).cut(basket).Volume<.001
def save(s,name,count):
 f=out/name;s.exportStep(str(f));ensure_mm(f,s)
 chk=Part.read(str(f));assert chk.isValid() and len(chk.Solids)==count
save(Part.makeCompound(full),'00_Four_Cam_Closed_Assembly.step',19)
qc=Part.read(str(out/'00_Four_Cam_Closed_Assembly.step'))
assert abs(qc.BoundBox.YLength-240)<1e-5 and qc.BoundBox.ZMax<102.701
assert abs(qc.Solids[16].BoundBox.ZMin-89.54)<1e-5
save(Part.makeCompound([one(side.common(b(15,229,77,25.3,245.1,100.1))),one(rear.common(b(25.27,231.5,77,45,245.1,100.1))),rod,cam]),'06_Rear_Upper_Cam_Fit_Coupon.step',4)
metrics=dict(cad_sample_count=len(drawer),travel_mm=110.5,nominal_clearance_mm=.8,local_thickness_mm=outer-232.35,cam_diameter_mm=8.2,cam_thickness_mm=11.2,rear_wall_nominal_mm=6.2,front_floor_mm=1.0,recess_mm=.25,slot_depth_mm=.97,rod_axis_shift_mm=1.45,outward_mm=outer-245,overall_depth_mm=outer-5,drawer_corner_depth_loss_mm=6.45,drawer_material_delta_mm3=(basket.Volume-old.Volume),cabinet_nominal_depth_mm=250,volume_delta_mm3=rear.Volume-r[3].Volume,checked_lock_angle_deg=10,drawer_samples=drawer,turn_samples=turn,lock_samples=pull,assembly_samples=insert,max_static_overlap_mm3=static)
(out.parent/'QA'/'four-cam-fit.json').write_text(json.dumps(metrics,indent=2)+'\n')
print('FIT',metrics,flush=True)
