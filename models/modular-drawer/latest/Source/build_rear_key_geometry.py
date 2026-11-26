"""Rear-only conversion: zero-nominal rear socket and flush cross-gates, original factory side slots."""
import FreeCAD as A,Part,Import,sys,hashlib,json
from pathlib import Path
from step_units import ensure_mm
V=A.Vector;d,out=map(Path,sys.argv[1:3]);out.mkdir(exist_ok=True)
src=d/'00_One_Bay_Close_Clearance_Assembly.step'
p=Part.read(str(src)).Solids;assert len(p)==15
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def B(x,y,z,u,v,w):return Part.makeBox(u-x,v-y,w-z,V(x,y,z))
def bb(q):
 b=q.optimalBoundingBox(False,False);return [round(getattr(b,k+j),6) for k in 'XYZ' for j in ('Min','Max')]
def c(a,b):
 aa,bc=a.BoundBox,b.BoundBox
 if any(min(getattr(aa,k+'Max'),getattr(bc,k+'Max'))<=max(getattr(aa,k+'Min'),getattr(bc,k+'Min'))+1e-6 for k in 'XYZ'):return 0.
 return a.common(b).Volume
def one(s):s=s.removeSplitter();assert s.isValid() and len(s.Solids)==1;return s.Solids[0]
def mir(s,x=97.65):return s.mirror(V(x,0,0),V(1,0,0))
def m(s,x=0,y=0,z=0):return s.translated(V(x,y,z))
def wire(points,y):
 v=[V(x,y,z) for x,z in points];return Part.makePolygon(v+v[:1])
def extrusion(points,y,ye):return Part.Face(wire(points,y)).extrude(V(0,ye-y,0))
# Exact installed side groove cross-section sampled from the dated latest STEP at
# multiple Y stations. Only use its uniform rear segment; the front pocket is not altered.
# T heads 22.35..24.72 and 25.88..28.25. Reuse the measured support shoulders.
x0=25.3
half=[(25.3,89.83),(24.72,89.83),(24.72,89.55),(22.37,89.55),(22.37,94.45),(24.72,94.45),(24.72,94.17),(25.3,94.17)]
cross=half+[(2*x0-x,z) for x,z in reversed(half[1:-1])]
face_y=239.12
# Four planar ramps, instead of the old loft clipped by the T profile.
# They only subtract at the entry end and do not move the fitted shoulders.
w=extrusion(cross,face_y,245)
def prism_yz(points,x,l):
 v=[V(x,y,z) for y,z in points];return Part.Face(Part.makePolygon(v+v[:1])).extrude(V(l,0,0))
def prism_yx(points,z,l):
 v=[V(x,y,z) for y,x in points];return Part.Face(Part.makePolygon(v+v[:1])).extrude(V(0,0,l))
f=face_y;f1=f+.42
bevels=[
 prism_yz([(f-.02,94.15),(f1,94.45),(f-.02,95.0)],21,9),
 prism_yz([(f-.02,89.85),(f1,89.55),(f-.02,89.0)],21,9),
 prism_yx([(f-.02,22.62),(f1,22.37),(f-.02,22.0)],89,6),
 prism_yx([(f-.02,27.98),(f1,28.23),(f-.02,28.6)],89,6)]
bar=one(w.cut(bevels))
assert all(isinstance(q.Surface,Part.Plane) for q in bar.Faces)
# 1.4 mm rear pull recess within the rear-board half, behind the external datum.
bar=one(bar.cut(B(24.56,244.32,91.30,26.04,245.01,92.70)))
# Left/right symmetric tail cuts only, preserving the full forward load shoulders.
engage=B(25.96,242.70,92.65,28.39,244.24,94.70)
bar=one(bar.cut([engage,mir(engage,25.3)]))
bars=[bar,mir(bar)]
# Exact CAD mating on the rear half. Do not widen or cut the already printed side slot.
half_void=[(25.29,89.83),(25.88,89.83),(25.88,89.55),(28.23,89.55),(28.23,94.45),(25.88,94.45),(25.88,94.17),(25.29,94.17)]
cut=extrusion(half_void,face_y,245.10)
# Mouth flare starts 0.55 mm from the rear plane; working section stays zero nominal.
cx,cz=26.7,92.
flare=[(cx+(x-cx)*1.10,cz+(z-cz)*1.09) for x,z in half_void]
mouth=Part.makeLoft([wire(half_void,244.45),wire(flare,245.05)],True,False)
# Separate removable transverse stop. It is fitted after inserting the main key,
# and is outside the drawer sweep. Stop slot has assembly clearance; it is not
# the requested tight double-T guide and does not carry the crosswise joint load.
drop=B(26.03,242.76,92.74,28.08,244.10,100.06)
blade=one(B(26.13,242.86,92.65,27.98,244.0,100).cut(B(26.63,242.85,99.37,27.48,244.04,100.02)))
blades=[blade,mir(blade)]
# Seat the stop by its floor; its top aligns with the rear panel.
base=p[3]
rear=one(base.multiFuse([B(25.3,238.8,96.79,46,245,100),B(149.3,238.8,96.79,170,245,100)]).cut([cut,mir(cut),mouth,mir(mouth),drop,mir(drop)]))
# The key under the stop is a full-height support surface outside the slide-head
# shoulder; lid / gate remains separately removable.
# The historical inside face was Y238.50; the pad beside it was Y238.80.
# Set their whole connected broad inner face to the second datum. Start at the
# natural Z9.8 lower fitting shoulder, so no extra ledge or altered lower fit.
before_flat=rear
shave=B(25.29,238.499,9.8,170.01,238.8,100.01)
rear=one(rear.cut(shave))
gone=before_flat.cut(rear).Volume
assert 1000<gone<1700,gone
assert rear.cut(before_flat).Volume<.001
def same(a,b):return max(a.cut(b).Volume,b.cut(a).Volume)
for check in [B(25,228,0,171,246,9.8),B(25,239.12,9.8,171,246,101)]:
 assert same(before_flat.common(check),rear.common(check))<.001
assert not any(f.Area>1 and abs(bb(f)[2]-238.5)<1e-5 and abs(bb(f)[3]-238.5)<1e-5 and bb(f)[5]>9.801 for f in rear.Faces)
assert any(f.Area>5000 and abs(bb(f)[2]-238.8)<1e-5 and abs(bb(f)[3]-238.8)<1e-5 for f in rear.Faces)
print('FLAT inside Y238.80 removing',round(gone,4),'mm³; lower mechanism and upper channels retained',flush=True)
zones=[B(25.29,238.79,86.99,46.01,245.01,100.01),B(149.29,238.79,86.99,170.01,245.01,100.01)]
zone=Part.makeCompound(zones+[shave])
pres=[rear.cut(base).cut(zone).Volume,base.cut(rear).cut(zone).Volume]
assert max(pres)<.001,pres
assert bb(rear)==bb(base), (bb(rear),bb(base))
assert c(rear,p[-1])<.001
def exp(stem,rows):
 f=out/(stem+'.step'); doc=A.newDocument('Key_Review'); obs=[]
 for name,s in rows:
  o=doc.addObject('Part::Feature','Part');o.Label=name;o.Shape=s;obs.append(o)
 doc.recompute();Import.export(obs,str(f));A.closeDocument(doc.Name);ensure_mm(f,Part.makeCompound([s for _,s in rows]))
 r=Part.read(str(f));assert r.isValid() and len(r.Solids)==len(rows)
 assert bb(r)==bb(Part.makeCompound([s for _,s in rows]));return f
def normal(q):v=bb(q);return m(q,-v[0],-v[2],-v[4])
names=['Left side (unchanged)','Right side (unchanged)','Front beam (unchanged)','Rear board - upper sliding keys','Paddle A','Paddle B','Front lower rod A','Front lower rod B','Rear lower rod A','Rear lower rod B','Front lower cam A','Front lower cam B','Rear lower cam A','Rear lower cam B','Drawer (unchanged)']
rows=[(n,rear if j==3 else p[j]) for j,n in enumerate(names)]
geometry=rows+[('Rear left sliding key',bar),('Rear right sliding key',bars[1]),('Rear stop blade left',blades[0]),('Rear stop blade right',blades[1])]
a=exp('00_Rear_Key_Closed_Review',geometry)
rfile=exp('03_Rear_Board_Slide_Key_Review',[('Rear board upper slot only',normal(rear))])
kl=exp('04_Rear_Slide_Key',[('Same reversible key, two copies',normal(bar))])
stopfile=exp('05_Rear_Key_Stop_Blade',[('Same stop blade, two copies',normal(blade))])
u,v=normal(bar),normal(bars[1]);assert max(u.cut(v).Volume,v.cut(u).Volume)<1e-5
r=Part.read(str(a)).Solids
coupons=exp('06_Rear_Stop_Corner_Fit_Coupon',[
 ('unchanged side segment',one(r[0].common(B(15.3,238.5,86.5,25.3,245,100)))),
 ('rear mating segment',one(r[3].common(B(25.3,238.5,86.5,41,245,100)))),
 ('test key',r[15]),('test stop blade',r[17])])
hits=[]
for y in [0,.025,.05,.12,.2,.3,.42,.65,.85,1,1.5,2,3,4,5,6,8,10]:
 vals=[max(c(m(k,y=y),q) for q in r[:15]) for k in r[15:17]]
 assert max(vals)<.001,(y,vals)
 hits.append([y,*[round(x,7) for x in vals]])
witness=[]
for index in [0,1]:
 k=r[15+index];side=r[index];rr=r[3];direction=1-2*index
 vols=[c(m(rr,x=direction*.5),k),c(m(side,x=-direction*.5),k),c(m(rr,z=.45),k),c(m(rr,z=-.45),k),c(m(k,y=-.35),rr)]
 assert min(vols)>.001,(index,vols)
 witness.append([round(x,5) for x in vols])
drop_path=[]
for dz in [0,.1,.3,.6,1,2,3.5,5,7.5,9]:
 mmax=max(c(m(b,z=dz),part) for b in r[17:] for part in r[:17])
 assert mmax<.001,(dz,mmax)
 drop_path.append([dz,round(mmax,6)])
positive=[]
for i in (0,1):
 k=r[15+i];b=r[17+i]
 checks=[[dy,round(c(m(k,y=dy),b),6)] for dy in [.1,.16,.2,.3,.5,.8,1]]
 assert checks[0][1]==0 and checks[3][1]>.001,checks
 positive.append(checks)
# Confirm exact CAD fit of the load faces by coincident BRep boundaries
# on a mid-depth section untouched by the slot mouth or transverse catch.
working=extrusion(half_void,240.3,241.9)
u=working.common(r[15]);sideclip=B(25.3,240.3,89,28.5,241.9,95)
wanted=working.common(sideclip).Volume
assert abs(u.common(sideclip).Volume-wanted)<1e-5
draw=[]
for dy in [0,-.1,-.3,-.6,-1,-2,-3,-4,-5,-6,-7,-8,-9,-10,-12,-16,-22,-30,-45,-60,-85,-100,-110.5]:
 v=max(c(m(r[14],y=dy),q) for j,q in enumerate(r) if j!=14)
 assert v<.001,(dy,v);draw.append([dy,round(v,7)])
# Adjacent bay can add a right face key into the untouched center side simultaneously.
assert c(m(r[15],x=154.7),r[16])<.001
static=max(c(q,b) for i,q in enumerate(r) for b in r[i+1:]);assert static<.001
print('FIT keys',hits,'positive restraint X/Z/forward',witness,'drawer samples',draw,'static',static,flush=True)
data=dict(source_sha256=h(src),files={f.stem:h(f) for f in [a,rfile,kl,stopfile,coupons]},bay_size_mm=[172,240,102.7],
 side_front_drawer_original=True,changes_outside_approved_surface_and_rear_upper_zones_mm3=pres,fit_mode='后板零名义间隙滑键，配顶部可拆止退片；侧板与下锁不改。',
 upper_drawer_clearance_mm=.8,key_length_mm=5.88,identical_key_left_right=True,key_rear_Y_mm=245,top_align_Z_mm=100,key_test_access_mm=10,
 inner_rear_face_unified_Y_mm=238.8,removed_legacy_step_mm=.30,shave_volume_mm3=round(gone,4),key_entrance_ramp_planar_faces=True,functional_key_recesses_kept=['rear removal notch','symmetric stop pockets to fit both sides'],blade_prying_recess_kept=True,main_slot_nominal_clearance_mm=0.0,top_stop_blade_drop_samples=drop_path,positive_rear_withdrawal_stop_samples=positive,key_back_to_front_samples=hits,key_positive_lock_xyz_and_stop_witness=witness,drawer_travel_samples=draw,static_max_interference_mm3=static,
 limits='先从背面插键，再从顶部插入止退片。叠装遮住顶部时先装片。零名义间隙不保证实物能插；层纹、磨损、振动及承载须用小样复核。')
(out/'fit.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');print('PASS rear-only keyed frame, unchanged original parts',flush=True)
