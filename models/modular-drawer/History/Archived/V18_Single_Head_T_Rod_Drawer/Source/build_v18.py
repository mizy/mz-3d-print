"""Geometry-preserving V18 all-single-head redo from its signed V17 precursor.

FreeCAD 1.x Python: build_v18.py V17_closed.step original_H100_seed.step output_dir.
The external STEP's six boards remain identical. All combined cross-rods are replaced
by exact translated original single-head T rods (unaltered cams).
"""
import sys,json,itertools,hashlib
from pathlib import Path
import FreeCAD as A, Part, Import
V=A.Vector;X=V(1,0,0)
f,seed,out=map(Path,sys.argv[1:4])
def H(f):return hashlib.sha256(f.read_bytes()).hexdigest()
assert H(f)=='9433cea9c75cb902a4c53a20f9e940230580c1efe210e3f213ac0dc6cf0c3827'
assert H(seed)=='4d88d167c6d8258db26bfe68b0f4571742502c38bfedd01ab90051dd31256e97'
d=Part.read(str(f));assert d.isValid() and len(d.Solids)==70
p=list(d.Solids)
src=list(Part.read(str(seed)).Solids);assert len(src)==19
def B(x,y,z,x1,y1,z1):return Part.makeBox(x1-x,y1-y,z1-z,V(x,y,z))
def M(s,x=0,y=0,z=0):return s.translated(V(x,y,z))
def C(a,b):
 if any(min(getattr(a.BoundBox,k+'Max'),getattr(b.BoundBox,k+'Max'))<=max(getattr(a.BoundBox,k+'Min'),getattr(b.BoundBox,k+'Min'))+1e-6 for k in 'XYZ'):return 0.0
 return a.common(b).Volume
def one(s):
 s=s.removeSplitter();assert s.isValid() and len(s.Solids)==1
 return s.Solids[0]
def bbox(s):
 b=s.optimalBoundingBox(False,False)
 return [round(getattr(b,k+v),7) for k in 'XYZ' for v in ('Min','Max')]
def topology(s):return tuple(len(v) for v in (s.Faces,s.Edges,s.Vertexes))
def write(path,rows):
 d=A.newDocument('V18_Single_Head_T_Rods')
 try:
  os=[]
  for n,v in rows:
   ob=d.addObject('Part::Feature',n);ob.Label=n
   z=v.copy();pm=z.Placement.toMatrix();z.Placement=A.Placement();z.transformShape(pm,True,True);ob.Shape=z;os.append(ob)
  d.recompute();Import.export(os,str(path))
 finally:A.closeDocument(d.Name)
 data=path.read_bytes()
 wrong=b'LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT($,.METRE.)'
 right=b'LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.)'
 if wrong in data:
  assert right not in data
  path.write_bytes(data.replace(wrong,right))
 assert right in path.read_bytes()
out.mkdir(parents=True,exist_ok=True)
for n in ('Reference','Print_Parts'):(out/n).mkdir(exist_ok=True)
pitch=154.7
a=src[1].common(B(149,-1,-1,163.35,241,103))
b=M(src[0],x=pitch).common(B(163.35,-1,-1,180,241,103))
pristine=one(M(one(a.fuse(b)),x=11.65,y=5.))
v17=p[1]; restore=[]
for label,y,r in (('front',13.,2.36),('rear_lower',241.8,1.17)):
 c=Part.makeCylinder(r,17.34,V(166.33,y,5),X)
 q1=Part.makeCone(r+.22,r,.4,V(166.35,y,5),X)
 q2=Part.makeCone(r+.22,r,.4,V(183.65,y,5),-X)
 fill=pristine.common(one(c.multiFuse([q1,q2])))
 assert C(v17,fill)<.001 and fill.Volume>1.
 restore.append((label,y,r,fill))
panel=one(v17.multiFuse([x[3] for x in restore]))
vp=sum(x[3].Volume for x in restore)
assert abs(panel.Volume-v17.Volume-vp)<.002
assert bbox(panel)==bbox(v17)
side_name='01_V18_Universal_Bilateral_Side_T_Rod'
sfilepath=out/'Print_Parts'/f'{side_name}.step'
rb=bbox(panel); norm=M(panel,-rb[0],-rb[2],-rb[4])
assert bbox(norm)==[0.,17.3,0.,240.,0.,102.7],bbox(norm)
write(sfilepath,[(side_name,norm)])
re=Part.read(str(sfilepath))
assert re.isValid() and len(re.Solids)==1 and bbox(re)==bbox(norm),bbox(re)
rbp=M(re,rb[0],rb[2],rb[4])
assert abs(re.Volume-panel.Volume)<.002 and abs(C(re,norm)-norm.Volume)<.002
holes=[]
for label,y,r,fill in restore:
 check=Part.makeCylinder(.25,.5,V(174.75,y,5),X)
 assert C(v17,check)<.001 and C(rbp,check)>check.Volume-.001,(label,y)
 holes.append(dict(label=label,axis_Y0_Z0_mm=[y,5],previous_open_diameter_mm=2*r,
  exact_stock_added_mm3=fill.Volume,restored_bounds_xyz_mm=bbox(fill),
  original_axis_air_in_v17_mm3=check.Volume-C(v17,check),retained_axis_air_in_v18_mm3=max(0,check.Volume-C(rbp,check))))
for label,li,ri,ys in (('front',5,20,-1),('rear_lower',6,21,1)):
 locR=M(p[li],x=pitch);locL=M(p[ri],x=-pitch)
 for rod,way in ((locR,1),(locL,-1)):
  assert max(C(M(rod,y=ys*u),rbp) for u in (0.,.3,2,6,16,24))<.001,(label,way)
  assert C(M(rod,x=way*(.4 if label=='front' else .188)),rbp)>.02,(label,way)
sjson={'side_verified':str(sfilepath),'file_size':sfilepath.stat().st_size,'sha256':H(sfilepath),'bbox_mm':[17.3,240.0,102.7],
 'unchanged_gap_mm':.60,'paddle_unchanged_diametric_mm':2.0,'signed_input':H(f),'removed_previous_shared_through_paths':holes}
print('VERIFIED_SIDE_READY',json.dumps(sjson),flush=True)
(out.parent/'side_ready.json').write_text(json.dumps(sjson,indent=2)+'\n')
if '--side-only' in sys.argv[4:]:raise SystemExit(0)
q=[('front',M(p[20],x=-pitch),M(p[5],x=pitch),p[10],p[24],-1,.4,2.4),
 ('rear_lower',M(p[21],x=-pitch),M(p[6],x=pitch),p[12],p[26],1,.188,2.4*.47)]
rod_witness=[]
for name,left,right,camL,camR,dy,dx,rel in q:
 reports=[]
 for hand,sg,r,other,cam in [('L',-1,left,right,camL),('R',1,right,left,camR)]:
  path=[0.,.1,.3,.7,1.25,2,3,4,6,8,12,16,24]
  panel_o=max(C(M(r,y=dy*u),panel) for u in path)
  rod_o=max(C(M(r,y=dy*u),other) for u in path)
  ov=C(r,cam); seat=C(M(r,x=sg*dx),panel); lock=C(M(r,x=-sg*rel),cam)
  assert max(panel_o,rod_o,ov)<.001 and min(seat,lock)>.01
  reports.append(dict(hand=hand,t_slot_sampled_poses=len(path),panel_overlap_mm3=panel_o,other_inserted_rod_overlap_mm3=rod_o,
   nominal_locked_cam_overlap_mm3=ov,t_shoulder_backout_if_forced_mm3=seat,locked_cam_rod_backout_if_forced_mm3=lock))
 rod_witness.append(dict(station=name,min_X_separation_between_rods_mm=bbox(right)[0]-bbox(left)[1],side_checks=reports))
base_names=['Left_Outer_Side','True_Shared_Double_Rail','Right_Outer_Side']
std=['Front_Beam','Rear_X','Front_Outside_Single_Rod','Rear_Lower_Outside_Single_Rod','Rear_Upper_Single_Rod_Left','Rear_Upper_Single_Rod_Right',
 'Front_Cam_Left','Front_Cam_Right','Rear_Lower_Cam_Left','Rear_Lower_Cam_Right','Rear_Upper_Cam_Left','Rear_Upper_Cam_Right','Outer_Paddle','Center_Paddle','Drawer']
seq=base_names+[k+v for k in ('BayL_','BayR_') for v in std]+['BayL_Front_Inner_Right_T_Rod','BayR_Front_Inner_Left_T_Rod','BayL_Rear_Lower_Inner_Right_T_Rod','BayR_Rear_Lower_Inner_Left_T_Rod']
table=[]
for tier in (0,1):
 names=[('Lower_' if not tier else 'Upper_')+n for n in seq]
 row=[M(panel,x=(i-1)*pitch,z=tier*100.) if i in (0,1,2) else p[tier*35+i] for i in range(33)]
 row.extend(M(r,z=tier*100.) for g in q for r in g[1:3])
 assert len(row)==len(names)==37
 table.extend(zip(names,row))
assert len(table)==74
fclosed=out/'Reference/V18_H100_2x2_Universal_Closed.step'
fopen=out/'Reference/V18_H100_2x2_Universal_Open.step'
write(fclosed,table)
print('CLOSED_EXPORTED',H(fclosed),flush=True)
assert table[69][0]=='Upper_BayR_Drawer',table[69][0]
open_table=[(n,M(s,y=-110.5) if j==69 else s) for j,(n,s) in enumerate(table)]
write(fopen,open_table)
print('OPEN_EXPORTED',H(fopen),flush=True)
rcls=Part.read(str(fclosed));ropn=Part.read(str(fopen))
assert rcls.isValid() and ropn.isValid() and len(rcls.Solids)==len(ropn.Solids)==74
assert bbox(rcls)==bbox(d),[bbox(rcls),bbox(d)]
unchanged=0; checked=0; zmax=0.
changes={0,1,2,33,34,35,36,37,38,39,70,71,72,73}
def cv(a,b):
 aa,bb=a
 cc,dd=b
 return any(v<=w+1.e-6 for v,w in ((bb,cc),(dd,aa)))
def overlap(a,b):
 ab=a[1];bb=b[1]
 if any(cv((ab[i],ab[i+1]),(bb[i],bb[i+1])) for i in (0,2,4)):return 0.0
 return a[0].common(b[0]).Volume
for pose,candidate,raw in (('closed',rcls,table),('open',ropn,open_table)):
 ps=list(candidate.Solids); cache=[(s,bbox(s)) for s in ps]
 for j,(s,(_,expect)) in enumerate(zip(ps,raw)):
  assert max(abs(x-y) for x,y in zip(cache[j][1],bbox(expect)))<.001,(pose,j)
  assert abs(s.Volume-expect.Volume)<.002 and topology(s)==topology(expect),(pose,j)
  if j in changes:
   for k,b in enumerate(cache):
    if k==j or k in changes and k<j:continue
    x=overlap(cache[j],b)
    checked+=1;zmax=max(x,zmax)
    assert x<.001,(pose,j,k,x)
  elif pose=='closed':unchanged+=1
 assert all(abs(ps[j].Volume-panel.Volume)<.002 for j in (0,1,2,37,38,39))
assert unchanged==60
audit=dict(version='V18',side=sjson,total_solids_closed_open=[74,74],unchanged_physical_instances_vs_V17=unchanged,
 modified_if_new_or_universal_pieces=len(changes),only_open_body_index_69_motion_Y_mm=-110.5,
 frame_outer_dimensions_mm=[326.7,240,202.7],n_print_skus=18,single_independent_bay_piece_count=19,
 shared_heads=0, single_head_T_rod_qty=24, anti_drop_paddles_qty=8, cams_qty=24, independent_t_slot_tests=rod_witness,
 max_nonintentional_overlap_changed_pairs_mm3=zmax,checked_changed_body_pair_candidates_in_two_poses=checked,
 unchanged_from_V17=['six identical side boards, print pose unchanged','side stack locators 5.80×5.40 front / 5.80×6.90 rear, Ø5 peg',
 '2.00 Ø journal / 2.00 shaft, 0.60 total drawer side gap, 120° service before stacking, 90° released drawer removal',
 'all existing beams, tray, cam, single rods and paddle STEP bytes; same finished outer dimensions'],
 exact_step_hashes={x.relative_to(out).as_posix():H(x) for x in (sfilepath,fclosed,fopen)})
(out/'Geometry_Validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
reb=dict(separate_valid_solids=[74,74,1],printed_side_bbox_mm=[17.3,240,102.7],pair_candidates=checked,changed_pair_overlap_mm3=zmax,
 nominal_dimensions_mm=[326.7,240,202.7],unchanged_inherited_placed_instances=unchanged,only_moved_open_drawer=69,
 first_src_file_sha256=H(f),second_src_file_sha256=H(seed),step_hashes=audit['exact_step_hashes'])
(out/'Independent_Readback.json').write_text(json.dumps(reb,ensure_ascii=False,indent=2)+'\n')
print('V18_CAD_DONE',json.dumps(reb,ensure_ascii=False),flush=True)
