"""H100 direct stack, all six vertical members one exact double-sided interchangeable SKU."""
import FreeCAD as A,Part,Import,itertools,json,sys,math,gc
from pathlib import Path
V=A.Vector;X=V(1,0,0)
seed,raw,out=map(Path,sys.argv[1:4])
q=list(Part.read(str(seed)).Solids);assert len(q)==76
source=list(Part.read(str(raw)).Solids);assert len(source)==19
out.mkdir(exist_ok=False,parents=True)
for key in ('Reference','Print_Parts'): (out/key).mkdir()
def C(a,b):
 a0,b0=a.BoundBox,b.BoundBox
 if any(min(getattr(a0,k+'Max'),getattr(b0,k+'Max'))<=max(getattr(a0,k+'Min'),getattr(b0,k+'Min'))+1e-6 for k in 'XYZ'):return 0.
 return a.common(b).Volume
def mx(a,parts): return max([0.]+[C(a,b) for b in parts])
def M(s,x=0,y=0,z=0):return s.translated(V(x,y,z))
def B(x0,y0,z0,dx,dy,dz):return Part.makeBox(dx,dy,dz,V(x0,y0,z0))
def cyl(x,y,z,r,h):return Part.makeCylinder(r,h,V(x,y,z))
def one(a):
 a=a.removeSplitter();assert a.isValid() and len(a.Solids)==1,(a.isValid(),len(a.Solids));return a.Solids[0]
def bounds(a):
 b=a.optimalBoundingBox(False,False);return [round(getattr(b,k),7) for k in ('XMin','XMax','YMin','YMax','ZMin','ZMax')]
def sha(p):
 import hashlib
 return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,parts):
 d=A.newDocument('H100FlushStack')
 try:
  objs=[]
  for n,v in parts:
   o=d.addObject('Part::Feature',n);o.Label=n;s=v.copy();pm=s.Placement.toMatrix();s.Placement=A.Placement();s.transformShape(pm,True,True);o.Shape=s;objs.append(o)
  d.recompute();Import.export(objs,str(p))
 finally:A.closeDocument(d.Name)
 assert p.is_file()
def capsule(x,y,along,rad,rise,z=-.03,height=3.255):
 if along=='X':
  return one(cyl(x-rise,y,z,rad,height).multiFuse([cyl(x+rise,y,z,rad,height),B(x-rise,y-rad,z,2*rise,2*rad,height)]))
 return one(cyl(x,y-rise,z,rad,height).multiFuse([cyl(x,y+rise,z,rad,height),B(x-rad,y-rise,z,2*rad,2*rise,height)]))
def relief(a,b):
 # Open to the drawer bay. Only the last 1.20 mm of the base thickness is removed.
 # Longitudinal ends have drafted ramps (as viewed from Y).
 fy=[(123.00,-.02),(124.25,1.20),(129.65,1.20),(130.90,-.02)]
 wire=Part.makePolygon([V(a,y,z) for y,z in fy+[fy[0]]])
 return Part.Face(wire).extrude(V(b-a,0,0))
# True 10 mm shared central wall, with left and right OEM details via each exact half.
pitch=154.70;split=163.35;x0=11.65;y0=5.
l=source[1].common(B(149,-1,-1,split-149,242,104))
r=M(source[0],pitch).common(B(split,-1,-1,180-split,242,104))
old=one(M(one(l.fuse(r)),x0,y0))
bb0=bounds(old);assert max(abs(a-b) for a,b in zip(bb0,[166.35,183.65,5.,245.,0.,100.]))<.00001,bb0
sites=[(13.,2.36,2.23,33),(241.8,1.17,2.23*.47,34)]
xo,xe=bb0[:2]
defs=[]
for y,rr,head,_ in sites:
 # Chamfer is strictly under rail, and does not touch either outer Y-fed T-stop.
 defs+=[Part.makeCylinder(rr,xe-xo+.04,V(xo-.02,y,5),X),
        Part.makeCone(rr+.22,rr,.40,V(xo,y,5),X),
        Part.makeCone(rr+.22,rr,.40,V(xe,y,5),-X)]
core=one(old.cut(defs))
for z in (0,10):
 slab=B(xo-.1,4.9,z-.001,xe-xo+.2,240.2,.002)
 assert abs(old.common(slab).Volume-core.common(slab).Volume)<.00015
def rrbox(x,y,ta,tb,rr=2.8,z=-.025,dz=3.25):
 parts=[cyl(x+dx,y+dy,z,rr,dz) for dx,dy in itertools.product((-ta,ta),(-tb,tb))]
 if ta>0:parts.append(B(x-ta,y-tb-rr,z,2*ta,2*(tb+rr),dz))
 if tb>0:parts.append(B(x-ta-rr,y-tb,z,2*(ta+rr),2*tb,dz))
 return one(parts[0].multiFuse(parts[1:]))
x=175.;ys=(27.,223.)
n1=rrbox(x,ys[0],.30,0.)
n2=rrbox(x,ys[1],.30,.65)
pocket=[relief(165.3,172.58),relief(177.42,184.70)]
c1=one(core.cut([n1,n2]+pocket))
pegs=[one(cyl(x,y,99.95,2.50,2.20).fuse(Part.makeCone(2.50,2.10,.55,V(x,y,102.15)))) for y in ys]
uni=one(c1.multiFuse(pegs))
assert max(abs(a-b) for a,b in zip(bounds(uni),[166.35,183.65,5.,245.,0.,102.7]))<.00002
position=[M(uni,dx) for dx in (-pitch,0,pitch)]
s2=M(uni,z=100)
assert C(uni,s2)<.001
bearing=C(uni,M(s2,z=-.01))/.01
assert bearing>2200
print('SSC panel one shape; face contact and all XYZ',bearing,bounds(uni),flush=True)
single=[]
for y,rr,head,i in sites:
 rod=q[i]
 # Direct side-fed dual rod, denser near contacts; both full ends go through for disassembly.
 dr=max(C(M(rod,x=.25*k),uni) for k in range(-130,131))
 assert dr<.001,(y,dr)
 single.append(dict(station_Y_mm=y,pass_bore_mm=2*rr,rod_radius_envelope_mm=head,radial_nominal_allowance_mm=rr-head,
  entrance_lead_axial_radial_mm=[.4,.22],double_rod_through_overlap_mm3=dr,sideSingle=[]))
testCoords=(('left_cell_front_outer',4,5,0,1,0),('right_cell_front_outer',5,20,2,-1,0),
 ('left_cell_rear_low_outer',6,6,0,1,1),('right_cell_rear_low_outer',7,21,2,-1,1),
 ('left_cell_rear_upper_outer',8,7,0,1,2),('right_cell_rear_upper_outer',9,23,2,-1,2),
 ('left_cell_rear_upper_on_middle',9,8,1,-1,2),('right_cell_rear_upper_on_middle',8,22,1,1,2))
sng=[]
for tag,j,i,p,sg,st in testCoords:
 seat=position[p];r=q[i]
 ref=q[p]
 assert C(r,seat)<.0008
 sx=.4 if not st else .4*.47
 hard=C(M(r,x=sg*sx),seat)
 witness_by_deflect=[C(M(r,x=sg*sx,y=dy,z=dz),seat) for dy,dz in ((0.,0.),(-.075,-.075),(.075,.075))]
 prev=C(M(r,x=sg*sx),ref)
 entry=max(C(M(r,y=(-k if not st else k)),seat) for k in (0,.12,.4,.75,1.25,2,3,4,5,7,9,12,16,20))
 assert hard>.025 and entry<.001 and min(witness_by_deflect)>.018,(tag,hard,entry,witness_by_deflect)
 sng.append(dict(location=tag,nominal_hard_capture_overlap_mm3=hard,previous_nominal_capture_mm3=prev,
  shoulder_deflected_overlap_mm3=witness_by_deflect,insertion_along_Y_overlap_mm3=entry))
 print('single-rod capture',tag,hard,prev,flush=True)
rows0=position+q[3:35]
# Same short handed shaft everywhere; only the two actually occupied sockets of the shared panel are populated.
# Existing compact shaft is exact copied geometry already read back in the previous shared edition.
rows0[15]=M(q[31],x=-pitch)
rows0[30]=M(q[16],x=pitch)
rowL=rows0
rowU=[M(p,z=100) for p in rowL]
all_solids=rowL+rowU
assert len(all_solids)==70
sbb=[bounds(s) for s in all_solids]
bx=[(min if i%2==0 else max)(o[i] for o in sbb) for i in range(6)];print('full bounds',bx,flush=True)
assert max(abs(x-y) for x,y in zip(bx,[11.65,338.35,5.,245.,0.,202.7]))<.0005,bx
piv=V(0,125.,97.83)
pid=(15,16,30,31)
# Check both functional faces on one panel with same shortened stop shafts; all six boards get the same tested sockets.
sv=[]
for i,sg in ((16,-1),(31,1)):
 pp=rowL[i]
 work=max(C(M(pp.rotated(piv,X,a),x=sg*dx),uni) for a,dx in itertools.product(range(0,121),(-.08,0,.145)))
 insertion=max(C(M(pp.rotated(piv,X,120),x=sg*u),uni) for u in (0,.05,.15,.25,.4,.6,.85,1.05,1.35,1.6,2.,2.35,2.75,3.,3.5,4.25,5,6,7))
 hard=C(pp.rotated(piv,X,-5),uni)
 capture=min(C(M(pp.rotated(piv,X,a),x=sg*.45),uni) for a in range(0,91,5))
 assert max(work,insertion)<.001 and min(hard,capture)>.02,(i,work,insertion,hard,capture)
 sv.append(dict(side=i,service_spin_collision_mm3=work,service_entry_collision_mm3=insertion,hard_stop_negative_five_deg_mm3=hard,keyed_capture_working_range_mm3=capture))
print('both seats passed',sv,flush=True)
serv=[]
for i in pid:
 pp=rowL[i]
 sg=1 if i in (15,31) else -1
 work=max(mx(M(pp.rotated(piv,X,a),x=sg*dx),rowU) for a,dx in itertools.product(range(0,121,2),(-.08,0,.145)))
 path=max(mx(M(pp.rotated(piv,X,120),x=sg*dx),rowU) for dx in (0,.05,.15,.25,.4,.6,.85,1.05,1.35,1.6,2.,2.35,2.75,3.,3.5,4.25,5,6,7))
 assert max(work,path)<.001,(i,work,path)
 serv.append(dict(part_index=i,max_upper_overlap_through_0_to_120_deg_mm3=work,upper_overlap_for_120_deg_axial_service_travel_mm3=path))
print('stacked service passed',flush=True)
pairs=max(C(a,b) for i,a in enumerate(all_solids) for b in all_solids[:i]);assert pairs<.001,pairs
# Verified drop starts above all pegs. At partial dilation the actual six receiving holes remain independent.
stacking=[]
for u,topb in enumerate(position):
 for qz in (0,.05,.15,.3,.55,.8,1.2,1.7,2.1,2.6,3.,4.,6.,10.,16.):
  stacking.append(mx(M(topb,z=qz+100),rowL))
assert max(stacking)<.001
ns=['Left_Outer_Side','True_Shared_Double_Rail','Right_Outer_Side']
rn=['Front_Beam','Rear_X','Front_Outside_Single_Rod','Rear_Lower_Outside_Single_Rod','Rear_Upper_Single_Rod_Left','Rear_Upper_Single_Rod_Right',
 'Front_Cam_Left','Front_Cam_Right','Rear_Lower_Cam_Left','Rear_Lower_Cam_Right','Rear_Upper_Cam_Left','Rear_Upper_Cam_Right','Outer_Paddle','Center_Paddle','Drawer']
seq=ns+[k+v for k in ('BayL_','BayR_') for v in rn]+['Shared_Front_Dual_Rod','Shared_Rear_Lower_Dual_Rod']
rows=[(tier+n,v) for tier,rs in (('Lower_',rowL),('Upper_',rowU)) for n,v in zip(seq,rs)]
report=dict(closed_outer_bounds_mm=bx,nominal_envelope_including_top_peg_mm=[326.7,240,202.7],two_level_modules_height_mm=[100,100],
 n_assembly_solids=70,panels_per_tier=3,sideboard_SKUs=1,sideboard_qty=6,standalone_stack_connector_qty=0,
 actual_bearing_stack_plane_z_mm=100,left_and_right_bilateral_lower_rail_mm_each=3.65,nominal_guide_gap_total=.60,upper_top_pins_visible=True,
 all_6_front_socket_xy_mm=[6.2,5.6],all_6_rear_socket_xy_mm=[6.2,6.9],female_socket_depth_mm=3.225,
 pin_diameter_mm=5.,pin_peak_height_mm=2.7,pin_lead_in_axial_mm=.55,pin_tip_diameter_mm=4.20,nominal_pin_bottom_headroom_mm=.525,
 single_panel_contact_area_mm2=bearing,stack_drop_max_overlap_mm3=max(stacking),closed_pair_max_overlap_mm3=pairs,lower_paddle_service=serv,
 bilateral_paddle_test_on_one_SKU=sv,common_double_rod_test=single,retained_single_rod_T_lock_test=sng)
ref=out/'Reference'
p=ref/'H100_2x2_Universal_Bilateral_Closed.step'
write(p,rows)
print('closed export',p,sha(p),flush=True)
r=Part.read(str(p))
assert r.isValid() and len(r.Solids)==70 and max(abs(a-b) for part,(_,s) in zip(r.Solids,rows) for a,b in zip(bounds(part),bounds(s)))<.002
del r;gc.collect()
report['closed_step_sha256']=sha(p)
(out/'Geometry_Validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('CLOSED STEP VERIFIED',p,report['closed_step_sha256'],flush=True)
open_rows=[(n,M(v,y=-110.5) if n=='Upper_BayR_Drawer' else v) for n,v in rows]
write(ref/'H100_2x2_Universal_Bilateral_Open.step',open_rows)
work=[('01_Universal_Bilateral_Side_Double_Rails',uni,6),
 ('05_Short_Paddle_Left_Any_Panel',rowL[15],4),('06_Short_Paddle_Right_Any_Panel',rowL[16],4)]
dct={}
for n,v,qty in work:
 b=bounds(v);f=out/'Print_Parts'/(n+'.step');write(f,[(n,M(v,-b[0],-b[2],-b[4]))])
 s=Part.read(str(f));assert s.isValid() and len(s.Solids)==1 and abs(s.Volume-v.Volume)<.002
 dct[n]=dict(qty=qty,bbox_mm=[b[1]-b[0],b[3]-b[2],b[5]-b[4]],sha256=sha(f))
(out/'New_Parts_Schedule.json').write_text(json.dumps(dct,indent=2)+'\n')
print('open and universal parts exported',flush=True)
