"""Verified right-hand bay, reusing exactly one current center side."""
import FreeCAD as A,Part,Import,sys,hashlib,json
from pathlib import Path
from itertools import combinations
from step_units import ensure_mm
V=A.Vector; d,out=map(Path,sys.argv[1:3]);out.mkdir(exist_ok=True)
base=d/'00_Four_Cam_Closed_Assembly.step'
seed=Part.read(str(base));p=seed.Solids
assert seed.isValid() and len(p)==19
def bb(q):
 b=q.optimalBoundingBox(False,False)
 return [round(getattr(b,k+t),6) for k in 'XYZ' for t in ('Min','Max')]
def m(q,x=0,y=0,z=0):return q.translated(V(x,y,z))
def c(a,b):
 aa,ab=a.BoundBox,b.BoundBox
 if any(min(getattr(aa,k+'Max'),getattr(ab,k+'Max'))<=max(getattr(aa,k+'Min'),getattr(ab,k+'Min'))+1e-6 for k in 'XYZ'):return 0.
 return a.common(b).Volume
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pitch=154.7
twin=m(p[0],x=pitch)
assert max(p[1].cut(twin).Volume,twin.cut(p[1]).Volume)<.001
label=['左外侧板','共用中侧板','前梁','后板','左限位拨片','右限位拨片','前左拉杆','前右拉杆','后下左拉杆','后下右拉杆','前左偏心轮','前右偏心轮','后下左偏心轮','后下右偏心轮','拉篮','后上左拉杆','后上右拉杆','后上左偏心轮','后上右偏心轮']
left={i:p[i] for i in range(19) if i!=14}
extra={i:m(p[i],x=pitch) for i in range(1,19) if i!=14}
lrows=[('Left bay - '+label[i],q) for i,q in left.items()]
erows=[('New right outer side' if i==1 else 'Right bay - '+label[i],q) for i,q in extra.items()]
rows=[*lrows,*erows]
assert len(lrows)==18 and len(erows)==17 and len(rows)==35
overall=bb(Part.makeCompound([q for _,q in rows]))
size=[round(overall[i+1]-overall[i],4) for i in (0,2,4)]
assert size==[326.7,240.,102.7],size
pair_vol=max(c(a,b) for (_,a),(_,b) in combinations(rows,2));assert pair_vol<.001,pair_vol
print('PASS 35 stationary frame solids, 17 supplied parts',size,pair_vol,flush=True)

# The left bay stays fully assembled. Join the new front and rear toward its
# already shared panel, with the lower cams in the new bay not fitted yet.
kept=list(left.values());moving=[]
for dx in [0,.05,.12,.2,.3,.5,.8,1,1.5,2,3,5,8,12,16,22]:
 joins=[max(c(m(extra[i],x=dx),q) for q in [*kept,extra[j]]) for i,j in [(2,6),(3,8)]]
 free=max(c(m(extra[i],x=dx),q) for i in [1,7,9] for q in [*kept,extra[2],extra[3],extra[6],extra[8]])
 assert max(joins+[free])<.001,(dx,joins,free)
 moving.append([dx,*[round(j,7) for j in joins],round(free,7)])
print('PASS independent second bay beam and side approach',flush=True)
cam_samp=[]
# Install the upper cams from the back before inserting the two upper rods from the sides.
for y in [0,.1,.3,.5,1,2,3,4,6,8,10,12,15]:
 peak=max(c(m(extra[i],y=y),q) for i in (17,18) for q in [*kept,*[r for k,r in extra.items() if k not in (15,16,17,18)]])
 assert peak<.001,(y,peak)
 cam_samp.append([y,round(peak,7)])
# The same unmodified basket is used only as a virtual inspection gauge in each bay;
# neither downloadable frame file contains a basket.
travel=[]
for y in [0,-.1,-.3,-.6,-1,-2,-3,-4,-5,-6,-7,-8,-9,-10,-12,-16,-22,-30,-45,-60,-85,-100,-110.5]:
 t0,t1=m(p[14],y=y),m(p[14],x=pitch,y=y)
 v0=max(c(t0,r) for _,r in rows);v1=max(c(t1,r) for _,r in rows);cross=c(t0,t1)
 assert max(v0,v1,cross)<.001,(y,v0,v1,cross)
 travel.append([y,round(v0,7),round(v1,7),round(cross,7)])
print('PASS both revised basket travel envelopes and upper cam access',flush=True)

def export(stem,rs):
 f=out/(stem+'.step');doc=A.newDocument('Current_Drawer_Expansion');obs=[]
 for name,s in rs:
  o=doc.addObject('Part::Feature','Part');o.Label=name;o.Shape=s;obs.append(o)
 doc.recompute();Import.export(obs,str(f));A.closeDocument(doc.Name);ensure_mm(f,Part.makeCompound([q for _,q in rs]))
 r=Part.read(str(f))
 assert r.isValid() and len(r.Solids)==len(rs)
 assert max(abs(x.Volume-q.Volume) for x,(_,q) in zip(r.Solids,rs))<.002
 return f,r
two,rr=export('00_Two_Bay_Horizontal_Frame_Check',rows)
# The additional set preserves location relative to itself but uses a handy local origin.
eb=bb(Part.makeCompound([q for _,q in erows]))
kit,kr=export('07_Right_Bay_Frame_Expansion_17_Parts',[(n,m(q,-eb[0],-eb[2],-eb[4])) for n,q in erows])
assert bb(rr)==overall
assert max(c(a,b) for a,b in combinations(rr.Solids,2))<.001
assert max(c(a,b) for a,b in combinations(kr.Solids,2))<.001
for x in [0,pitch]:
 for off in [0,-.3,-12,-110.5]:
  assert max(c(m(p[14],x=x,y=off),r) for r in rr.Solids)<.001
result=dict(source_sha256=sha(base),hashes={f.stem:sha(f) for f in [two,kit]},
 new_parts_count=len(erows),two_bay_parts_count=len(rows),part_counts={'outer_side':1,'front_beam':1,'rear_board':1,'drawer_stop_paddles':2,'lower_cam_rods':4,'lower_cams':4,'upper_cam_rods':2,'upper_cams':2},
 overall_XYZ_mm=size,center_pitch_mm=pitch,basket_count_in_outputs=0,static_overlap_mm3=round(pair_vol,7),assembly_approach_samples_mm=moving,
 upper_cam_insertion_samples_mm=cam_samp,trays_both_guide_samples_mm=travel,
 limits='名义 CAD 静态及采样配合，不验旧版、不确认打印松紧和承重；未切片。')
(out/'expansion-fit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('PASS final independently selectable STEP set, read back current expansion',flush=True)
