"""Verified right-hand bay, reusing exactly one current center side."""
import FreeCAD as A,Part,Import,sys,hashlib,json
from pathlib import Path
from itertools import combinations
from step_units import ensure_mm
from axial_cam_keepers import pin as make_keeper, X0, X_MAG, STATIONS
V=A.Vector; d,out=map(Path,sys.argv[1:3]);out.mkdir(exist_ok=True)
base=d/'00_Four_Cam_Closed_Assembly.step'
seed=Part.read(str(base));p=seed.Solids
assert seed.isValid() and len(p)==23
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
label=['左外侧板','共用中侧板','前梁','后板','左限位拨片','右限位拨片','前左拉杆','前右拉杆','后下左拉杆','后下右拉杆','前左偏心轮','前右偏心轮','后下左偏心轮','后下右偏心轮','拉篮','后上左拉杆','后上右拉杆','后上左偏心轮','后上右偏心轮','前左止退针','前右止退针','后左止退针','后右止退针']
left={i:p[i] for i in range(23) if i!=14}
extra={i:m(p[i],x=pitch) for i in range(1,23) if i!=14}
lrows=[('Left bay - '+label[i],q) for i,q in left.items()]
erows=[('New right outer side' if i==1 else 'Right bay - '+label[i],q) for i,q in extra.items()]
rows=[*lrows,*erows]
assert len(lrows)==22 and len(erows)==21 and len(rows)==43
overall=bb(Part.makeCompound([q for _,q in rows]))
size=[round(overall[i+1]-overall[i],4) for i in (0,2,4)]
assert size==[326.7,240.,102.7],size
left_order=list(left)
extra_order=list(extra)
positions={**{('left',j):i for i,j in enumerate(left_order)},**{('extra',j):i+len(left) for i,j in enumerate(extra_order)}}
pair_ids=[(('left',0),('left',19)),(('left',0),('left',21)),(('left',1),('left',20)),(('left',1),('left',22)),(('left',1),('extra',19)),(('left',1),('extra',21)),(('extra',1),('extra',20)),(('extra',1),('extra',22))]
allowed={tuple(sorted(positions[k] for k in q)) for q in pair_ids}
def interference(shapes,allowed):
    score=0.; collars=[]
    for (i,a),(j,b) in combinations(enumerate(shapes),2):
        v=c(a,b)
        if (i,j) in allowed:
            assert .001<v<.5,('collar',i,j,v)
            collars.append([i,j,round(v,7)])
        else:score=max(score,v)
    assert score<.001,score
    return score,collars
pair_vol,collars=interference([q for _,q in rows],allowed)
print('PASS 43 stationary frame solids, 21 supplied parts and eight deliberate collar contacts',size,pair_vol,flush=True)
# Left bay stays assembled; slide the second bay's preassembled front or
# rear group into the fixed center side and new exterior side, without pins.
beam_paths={}; locked_paths={}
for name,grp,sign in [('front',(2,6,7,10,11),-1),('rear',(3,8,9,12,13,15,16,17,18),1)]:
 group=[extra[i] for i in grp]; obstacles=[q for _,q in lrows]+[q for i,q in extra.items() if i not in (*grp,19,20,21,22)]
 vals=[[a,round(max(c(m(t,y=sign*a),r) for t in group for r in obstacles),7)] for a in [0,.25,.5,1,2,3,5,8,10,12,14,17,20]]
 assert max(v[1] for v in vals)<.001,(name,vals)
 beam_paths[name]=vals
 pin_ids=(19,20) if name=='front' else (21,22)
 held=[[a,round(max(c(m(t,y=sign*a),extra[j]) for t in group for j in pin_ids),7)] for a in (0,.2,.28,.35,.5,1,2)]
 assert held[0][1]<.001 and held[4][1]>.001,(name,held)
 locked_paths[name]=held
print('PASS complete second-bay beam insertions with lockwheel and rods in situ',flush=True)
keeper_axes=[(x+pitch,y,z,d) for y,z,d in STATIONS for x in (X0+X_MAG,195.3-(X0+X_MAG))]
keeper_paths=[];tool_access=[]
for j,(x,y,z,di) in enumerate(keeper_axes):
    q=make_keeper(x,y,z,di,press=False); uid=positions[('extra',19+j)]
    v=[[h,round(max(c(m(q,z=-di*h),s) for i,(_,s) in enumerate(rows) if i!=uid),7)]for h in [0,.3,1,2,4,6,9,12,14]]
    assert max(a[1] for a in v)<.001,(j,v)
    keeper_paths.append(v)
    # Flat 0.8 × 0.55 mm tool envelope enters relief from the near end.
    ry=y+1.65 if di<0 else y-1.65
    maxz=z-.34 if di<0 else z+.89
    t=Part.makeBox(.8,5,.55,V(x-.4,ry if di<0 else ry-5,maxz-.55))
    tv=max(c(t,s) for i,(_,s) in enumerate(rows) if i!=uid)
    assert tv<.001,(j,tv)
    tool_access.append(round(tv,7))
# The same unmodified basket is used only as a virtual inspection gauge in each bay;
# neither downloadable frame file contains a basket.
travel=[]
for y in [0,-.1,-.3,-.6,-1,-2,-3,-4,-5,-6,-7,-8,-9,-10,-12,-16,-22,-30,-45,-60,-85,-100,-110.5]:
 t0,t1=m(p[14],y=y),m(p[14],x=pitch,y=y)
 v0=max(c(t0,r) for _,r in rows);v1=max(c(t1,r) for _,r in rows);cross=c(t0,t1)
 assert max(v0,v1,cross)<.001,(y,v0,v1,cross)
 travel.append([y,round(v0,7),round(v1,7),round(cross,7)])
print('PASS both revised basket travel envelopes and all keeper access',flush=True)

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
kit,kr=export('07_Right_Bay_Frame_Expansion_21_Parts',[(n,m(q,-eb[0],-eb[2],-eb[4])) for n,q in erows])
assert bb(rr)==overall
interference(rr.Solids,allowed)
rallow={tuple(sorted((extra_order.index(1),extra_order.index(k)))) for k in (20,22)}
interference(kr.Solids,rallow)
for x in [0,pitch]:
 for off in [0,-.3,-12,-110.5]:
  assert max(c(m(p[14],x=x,y=off),r) for r in rr.Solids)<.001
result=dict(source_sha256=sha(base),hashes={f.stem:sha(f) for f in [two,kit]},
 new_parts_count=len(erows),two_bay_parts_count=len(rows),part_counts={'outer_side':1,'front_beam':1,'rear_board':1,'drawer_stop_paddles':2,'lower_cam_rods':4,'lower_cams':4,'upper_cam_rods':2,'upper_cams':2,'axial_keeper_pins':4},
 overall_XYZ_mm=size,center_pitch_mm=pitch,basket_count_in_outputs=0,static_overlap_mm3=round(pair_vol,7),beam_insertion_samples_mm=beam_paths,
 keeper_insertion_samples_mm=keeper_paths,locked_axial_samples_mm=locked_paths,pry_tool_nominal_overlap_mm3=tool_access,designed_collar_pairs_mm3=collars,trays_both_guide_samples_mm=travel,
 limits='名义 CAD 静态及采样配合，不验旧版、不确认打印松紧和承重；未切片。')
(out/'expansion-fit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('PASS final independently selectable STEP set, read back current expansion',flush=True)
