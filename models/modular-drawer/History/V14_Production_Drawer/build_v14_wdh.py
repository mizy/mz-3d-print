"""V13 geometry kernel: W/D/H independent, exact approved seed, no geometric scaling."""
from pathlib import Path
import argparse,sys,re,itertools,math,json
from hashlib import sha256
import FreeCAD as A,Part,Import
from one_piece_stop import SERVICE_ANGLE,key_witness
from production_cams import integrate as integrate_cams, validate as verify_cams
from production_paddle import apply_rectangle
V=A.Vector
root=Path(__file__).resolve().parent
stamp='1a7d8aa004562a9c7a2381ca5e61b5a7fbb0422da0cfc0f64fa0c584431b806e'
def sha(p):return sha256(p.read_bytes()).hexdigest()
def box(x,y,z,dx,dy,dz):return Part.makeBox(dx,dy,dz,V(x,y,z))
def move(obj,axis='x',shift=0):
 v=[0,0,0];v['xyz'.index(axis)]=shift
 return obj.translated(V(*v))
def solid(a):
 s=a.removeSplitter()
 assert s.isValid() and len(s.Solids)==1,(len(s.Solids),s.isValid())
 return s.Solids[0]
def sec(obj,axis,x):
 k={'x':(V(x,-5,-5),V(1,0,0),V(0,1,0)), 'y':(V(-5,x,120),V(0,1,0),V(1,0,0)), 'z':(V(-5,-5,x),V(0,0,1),V(1,0,0))}
 return obj.common(Part.makePlane(285,265,*k[axis]))
def crop(axis,lo,hi):
 a=[-10.,-10.,-10.];b=[280.,280.,130.];i='xyz'.index(axis)
 a[i]=lo;b[i]=hi
 return box(*a,*(e-s for s,e in zip(a,b)))
def axisvec(axis,d):
 q=[0,0,0];q['xyz'.index(axis)]=d;return V(*q)
def area_delta(a,b):return a.cut(b).Area+b.cut(a).Area
def vol_diff(a,b):return a.cut(b).Volume+b.cut(a).Volume
def near(a,b,tol=.0006):assert abs(a-b)<tol,(a,b)
def stretch(q,axis,x,delta):
 if not delta:return q
 # For shrinkage validate the ENTIRE selected strip via cross sections before removing it.
 lo,hi=(x+delta/2,x-delta/2) if delta<0 else (x,x)
 s=sec(q,axis,lo)
 samples=([lo+(hi-lo)*k/6 for k in range(7)] if delta<0 else [x-.2,x+.2])
 err=max(area_delta(s,move(sec(q,axis,y),axis,lo-y)) for y in samples)
 assert err<.0006,(axis,x,delta,err)
 first=q.common(crop(axis,-10,lo)); last=move(q.common(crop(axis,hi,280)),axis,delta)
 fill=[s.extrude(axisvec(axis,delta))] if delta>0 else []
 return solid(first.multiFuse([last]+fill))
def win(x,dx,y,wd,z0,zs,za,r=1.):
 rad=wd/2;ang=math.atan(rad/(za-zs));d=r/math.tan(ang);t=d*math.sin(ang);z=za-d*math.cos(ang);apex=za-r/math.sin(ang)+r
 a,b,j,k,tr,tl=[V(x,y+s,h) for s,h in ((-rad,z0),(rad,z0),(rad,zs),(-rad,zs),(t,z),(-t,z))]
 e=[Part.makeLine(a,b),Part.makeLine(b,j),Part.makeLine(j,tr),Part.Arc(tr,V(x,y,apex),tl).toShape(),Part.makeLine(tl,k),Part.makeLine(k,a)]
 return Part.Face(Part.Wire(e)).extrude(V(dx,0,0))
def comp(a,b):
 x,y=a.BoundBox,b.BoundBox
 if any(min(getattr(x,k+'Max'),getattr(y,k+'Max'))<max(getattr(x,k+'Min'),getattr(y,k+'Min'))+1e-7 for k in 'XYZ'):return 0.
 return a.common(b).Volume
def maxo(a,b):return max(comp(a,b1) for b1 in b)
def guard(w,d,h):
 for name,a,lo,hi in [('W',w,180,240),('D',d,180,240),('H',h,48,80)]:
  if type(a) not in (int,float) or int(a)!=a or int(a)%2 or not(lo<=a<=hi):
   raise ValueError(f'{name}: use an even integer from {lo} to {hi} mm, got {a!r}')
 return int(w),int(d),int(h)
def create(w,d,h):
 w,d,h=guard(w,d,h); wx,dd,hh=w-180,d-200,h-52
 seed=root/'Seed'/'V13_W180_D200_H52_Approved.step'
 assert sha(seed)==stamp
 original=list(Part.read(str(seed)).Solids);assert len(original)==21
 a=original[:]
 side_count=4 if d<232 else 6
 width=min(34,2*math.floor((d-34-10*(side_count-1))/(2*side_count)))
 c0=17+width/2
 centers=[c0+i*(d-2*c0)/(side_count-1) for i in range(side_count)]
 rear_count=3 if w<228 else 5
 rear_centers=[49.30,w/2,w-49.30]
 rear_widths=[33.20,34.00,33.20]
 if dd or hh:
  for i in (0,1):
   f=(lambda s:s) if i==0 else (lambda s:s.mirror(V(90,0,0),V(1,0,0)))
   patches=[f(win(3.65,10,y,34,12,28,46)) for y in (34,78,122,166)]
   fresh=[f(win(3.55,10.2,y,width,12,28+hh,46+hh)) for y in centers]
   # Heal the original arch profiles to make a contiguous neutral pad, lengthen only blank areas,
   # then cut exact new arch profiles. The center stop carrier moves with the unchanged profile.
   q=solid(a[i].multiFuse(patches))
   q=stretch(stretch(q,'y',52,dd/2),'y',148+dd/2,dd/2)
   q=stretch(q,'z',34,hh)
   a[i]=solid(q.cut(fresh))
  a[3]=move(stretch(a[3],'z',22,hh),'y',dd)
  for i in (6,7,8,9,12,13,14,15):
   a[i]=move(a[i],'y',dd)
   if i in (8,9,14,15):a[i]=move(a[i],'z',hh)
  for i in range(16,20):a[i]=move(move(a[i],'y',dd/2),'z',hh)
  a[-1]=stretch(stretch(a[-1],'y',100,dd),'z',34,hh)
 if wx:
  a[1]=move(a[1],'x',wx)
  for i in range(5,20,2):a[i]=move(a[i],'x',wx)
  a[2]=stretch(a[2],'x',90,wx)
  a[3]=stretch(stretch(a[3],'x',70.50,wx/2),'x',109.50+wx/2,wx/2)
  a[-1]=stretch(stretch(a[-1],'x',42,wx/2),'x',138+wx/2,wx/2)
 if rear_count==5:
  old_holes=[]; yD=d
  rear_outer=[f for f in a[3].Faces if abs(f.BoundBox.YMin-yD)<.00003 and abs(f.BoundBox.YMax-yD)<.00003]
  f=max(rear_outer,key=lambda f:f.Area)
  for rw in f.Wires:
   k=rw.optimalBoundingBox()
   if 32<k.XLength<36 and k.ZMin>10.05 and k.ZMin<10.3 and k.ZLength>24:old_holes.append(rw)
  assert len(old_holes)==3,[str(x.BoundBox) for x in f.Wires]
  a[3]=solid(a[3].multiFuse([Part.Face(u).extrude(V(0,-6.5,0)) for u in old_holes]))
  rw=2*math.floor((w-100)/10); m=30+rw/2
  rear_centers=[m+i*(w-2*m)/4 for i in range(5)]
  rear_widths=[rw]*5
  cuts=[win(d-6.57,6.64,x,rw,12,28+hh,46+hh).mirror(V(0,0,0),V(1,-1,0)) for x in rear_centers]
  a[3]=solid(a[3].cut(cuts))
 # Independently check the same three or five through-openings at every depth plane, not merely a projected hole.
 rear_holes=[]
 for yy in (d-6.499,d-4.,d-2.,d-.001):
  items=[]
  for s0 in sec(a[3],'y',yy).Faces:
   for wire in s0.Wires:
    bb=wire.optimalBoundingBox()
    if 22<=bb.XLength<=36 and 10<bb.ZMin<=12.001 and bb.ZLength>24:
     items.append([bb.XMin,bb.XMax,bb.ZMin,bb.ZMax])
  items.sort()
  assert len(items)==rear_count,(rear_count,yy,items)
  for t,m,rw in zip(items,rear_centers,rear_widths):
   near((t[0]+t[1])/2,m);near(t[1]-t[0],rw)
  rear_holes.append(items)
 for r in rear_holes[1:]:
  for q,b in zip(r,rear_holes[0]):
   assert max(abs(v-t) for v,t in zip(q,b))<.0006
 seats,moving,retainer=key_witness(w,d,h,a[:2],a[18:20])
 a[:2]=seats
 a=a[:16]+moving+[a[-1]]
 original=original[:16]+original[18:]
 print('Integrated stops and aperture geometry',w,d,h,side_count,rear_count,flush=True)
 asc=Part.makeCompound(a).optimalBoundingBox()
 assert all(abs(x-y)<.0001 for x,y in zip((asc.XLength,asc.YLength,asc.ZLength),(w,d,h)))
 t=a[-1].optimalBoundingBox()
 assert all(abs(x-y)<.0001 for x,y in zip((t.XLength,t.YLength,t.ZLength),(w-27.9,d-10,h-14)))
 # Certified geometric dimensions of this ruler template: width, outer guide, Z0 rail depth.
 lip=a[0].common(box(13.651,0.,-.00001,3.648,d,10.00002)).optimalBoundingBox()
 back=a[3].common(box(17.31,189.1001+dd,-.00001,w-34.62,4.4298,9.80002)).optimalBoundingBox()
 near(lip.ZMin,0);near(lip.ZMax,10);near(back.ZMin,0);near(back.ZMax,9.8)
 sideholes=[]
 for i,x in ((0,8.65),(1,w-8.65)):
  bb=sorted([[k.BoundBox.YMin,k.BoundBox.YMax,k.BoundBox.ZMin,k.BoundBox.ZMax] for f in sec(a[i],'x',x).Faces for k in f.Wires
             if abs(k.BoundBox.ZMin-12)<1e-4 and abs(k.BoundBox.YLength-width)<1e-4])
  assert len(bb)==side_count,bb
  for y,b in zip(centers,bb):near(y,(b[0]+b[1])/2)
  sideholes.append(bb)
 return a,original,dict(W=w,D=d,H=h,assembly_solids=19,side_aperture_count=side_count,rear_aperture_count=rear_count,rear_arch_centers_x_mm=rear_centers,rear_arch_widths_mm=rear_widths,rear_through_arch_section_bounds_mm=rear_holes,paddle=retainer,side_arch_centers_y_mm=centers,side_arch_width_mm=width,side_arches_exact_section_bounds_mm=sideholes,
   guide_mm=w-27.3,drawer_dims_mm=[w-27.9,d-10,h-14],side_walls_mm=.96,bottom_mm=2.6,
   side_lip_Z_mm=[0,10],rear_lip_Z_mm=[0,9.8],side_clearance_mm=.60,side_lip_projection_mm=3.65)
def validate(a,original,s,quick=False):
 a0=a[:-1];tray=a[-1];w,d,h=[s[k] for k in 'WDH'];dd=d-200;hh=h-52
 def spin(p,angle):return p.rotated(V(0,100+dd/2,49.83+hh),V(1,0,0),angle)
 park=a[:16]+[spin(p,90) for p in a[16:18]]
 def pose(y,x=0,z=0):return tray.translated(V(x,-y,z))
 for i,q in enumerate(a):
  for j,p in enumerate(a[:i]):near(comp(q,p),comp(original[i],original[j]),.0007)
 start,rewind,full=90.5+dd/2,83.5+dd/2,194+dd
 ys=(0,.7,3.2,11.,23.5,.5*start,.75*start,.94*start,start) if not quick else (0.,.5*start,start)
 xs=(-.30,0,.30);zs=(0,.30)
 ypar=ys+(start+2,start+12,full*.65,full*.78,full*.88,full-4,full) if not quick else ys+(full*.8,full)
 w0=max(maxo(pose(y,x,z),a0) for x,y,z in itertools.product(xs,ys,zs))
 wp=max(maxo(pose(y,x,z),park) for x,y,z in itertools.product(xs,ypar,zs))
 angles=list(range(0,91,3 if not quick else 15))
 wr=max(maxo(spin(s,ang),a[:16]+[pose(rewind)]) for s,ang in itertools.product(a[16:18],angles))
 assert max(w0,wp,wr)<.001,(w0,wp,wr)
 hits=[]
 for x,z in itertools.product(xs,zs):
  lo,hi=start,start+.55
  assert maxo(pose(lo,x,z),a[16:18])<.0002
  assert maxo(pose(hi,x,z),a[16:18])>.025
  for j in range(8):
   m=(lo+hi)/2
   if maxo(pose(m,x,z),a[16:18])>.00005:hi=m
   else:lo=m
  hits.append([x,z,lo,hi])
 toe=[comp(pose(92.15+dd/2,0,.30),r) for r in a[16:18]]
 assert min(toe)>1,toe
 tool=[]
 for x,y,z,r,len0 in [(25.55,-25,5,2.25,26.665),(22.30,199.786+dd,5,1.45,24.214),(18.65,199.786+dd,47+hh,1.45,24.214)]:
  for xx in (x,w-x):
   tool.append(maxo(Part.makeCylinder(r,len0,V(xx,y,z),V(0,1,0)),a0))
 assert max(tool)<.0004,tool
 f=solid(a[0].multiFuse(a[1:4]));assert f.isValid() and len(f.Solids)==1
 near(f.optimalBoundingBox().ZMin,0);assert all(obj.cut(f).Volume<.0007 for obj in a[:4])
 assert f.cut(a[:4]).Volume<.0007
 s.update(open_pose_mm=start,earliest_limiter_mm=min(row[2] for row in hits),latest_limiter_mm=max(row[3] for row in hits),release_turn_after_pushback_mm=rewind,full_extraction_checked_mm=full,
  draw_working_release_and_swing_counts=[6*len(ys),6*len(ypar),2*len(angles)],CAD_non_intentional_overlap_mm3=[w0,wp,wr],tool_corridors_mm3=tool,
  one_piece_true_solid_count=1,limiter_actual_intersection_witness_mm3=toe,limiter_brackets_mm=hits)
 return f,pose(start)
def bbox(b):return tuple(getattr(b.optimalBoundingBox(),q) for q in ('XMin','XMax','YMin','YMax','ZMin','ZMax'))
def dump(out,basename,parts,labels,fcstd=False):
 name='V13CAD';doc=A.newDocument(name);f=out/(basename+'.step')
 try:
  obs=[]
  for s,n in zip(parts,labels):
   o=doc.addObject('Part::Feature',n);o.Label=n;o.Shape=s;obs.append(o)
  doc.recompute()
  if fcstd:doc.saveAs(str(out/(basename+'.FCStd')))
  Import.export(obs,str(f))
 finally:A.closeDocument(doc.Name)
 def ck(mm):
  q=Part.read(str(f));return q.isValid() and len(q.Solids)==len(parts) and all(abs(u-mm*v)<.008*mm for a,b in zip(q.Solids,parts) for u,v in zip(bbox(a),bbox(b)))
 if not ck(1):
  assert ck(1000),f
  blob,nn=re.subn(rb'(?i)SI_UNIT\s*\(\s*\$\s*,\s*\.METRE\.\s*\)',b'SI_UNIT(.MILLI.,.METRE.)',f.read_bytes())
  assert nn;f.write_bytes(blob);assert ck(1),f
 return f
def production_motion(a,f,s,quick):
 # Repeat checks with BOTH final frames, including tool-cam/rod assemblies and not only their plain additive shape.
 t=a[-1];w,d,h=[s[x] for x in 'WDH'];dd=d-200;hh=h-52;r=a[16:18]
 pv=V(0,d/2,h-2.17)
 def rot(p,z):return p.rotated(pv,V(1,0,0),z)
 def pose(y,x=0,z=0):return t.translated(V(x,-y,z))
 opens=s['open_pose_mm'];rewind=s['release_turn_after_pushback_mm'];full=s['full_extraction_checked_mm']
 xs=(-.30,0,.30);zs=(0,.30); y=(0,.7,3.2,11,23.5,.5*opens,.75*opens,.94*opens,opens)
 if quick:y=(0,.5*opens,opens)
 y2=y+(opens+2,opens+12,full*.65,full*.78,full*.88,full-4,full)
 opts={'modular':a[:16],'one_piece':[f]}; result={}
 for name,b in opts.items():
  for i,q in enumerate(b+r):
   assert max([0.]+[comp(q,v) for v in (b+r)[:i]])<.0008,(name,i)
  go=max(maxo(pose(dy,x,z),b+r) for x,z,dy in itertools.product(xs,zs,y))
  park=max(maxo(pose(dy,x,z),b+[rot(p,90) for p in r]) for x,z,dy in itertools.product(xs,zs,y2))
  return_turn=max(maxo(rot(p,n),b+[pose(rewind)]) for n,p in itertools.product(range(0,91,3),r))
  service=max(maxo(rot(p,n),b) for n,p in itertools.product(range(0,121,2),r))
  assert max(go,park,return_turn,service)<.0008,(name,go,park,return_turn,service)
  toe=[comp(pose(92.15+dd/2,0,.3),p) for p in r]
  assert min(toe)>1
  result[name]=dict(work_max_mm3=go,parked_full_extraction_max_mm3=park,pushback_release_max_mm3=return_turn,empty_0_to_120_service_sweep_mm3=service,
   positive_rear_stop_overlap_witness_mm3=toe,posed_check_counts=[len(y)*6,len(y2)*6,62,122])
 return result

def cli():
 p=argparse.ArgumentParser();p.add_argument('--config',type=Path,default=root/'dimensions.json')
 p.add_argument('--out',type=Path,required=True);p.add_argument('--quick-check',action='store_true');p.add_argument('--validation-only',action='store_true')
 args=p.parse_args();o=args.out.resolve(); conf=json.loads(args.config.read_text());w,d,h=guard(*(conf[k] for k in ('outer_width_mm','outer_depth_mm','outer_height_mm')))
 if o.exists() and any(o.iterdir()):raise ValueError('Output directory not empty; choose a new one')
 o.mkdir(exist_ok=True,parents=True)
 a,old,s=create(w,d,h)
 a,report=apply_rectangle(a,w,d,h)
 s['single_rectangular_paddle']=report
 # The fused alternative never needs the screwdriver holes or pull-rods of the modular joint.
 # It retains the earlier flange/exterior cavities and the same updated keyed paddle mechanism.
 fused,open_tray=validate(a,old,s,args.quick_check)
 coupon=root/'Seed'/'V13_Core_Separated_Rod_And_Bit_REFERENCE.step'
 assert sha(coupon)=='941ccb481fb989423d2eda37b2b4086750b04b9c86a870f7bc61249dbde852b7'
 mod,stations,turn=integrate_cams(a,w,d,h,coupon)
 s['cam_verification']=verify_cams(mod,stations,turn,d,quick=True)
 s['finished_both_frames_motion']=production_motion(mod,fused,s,args.quick_check)
 print('Validated V14 both production frame variants',w,d,h,flush=True)
 files={}
 if not args.validation_only:
  names=['Left_Side','Right_Side','Front_Beam','Rear_Beam']+[f'Frame_Hardware_{i:02d}' for i in range(1,13)]+['Left_Integrated_Rectangular_Paddle','Right_Integrated_Rectangular_Paddle','Drawer']
  asm=o/'Reference';pt=o/'Print_Parts';asm.mkdir();pt.mkdir()
  files['closed']=dump(asm,'V14_Modular_Closed',mod,names,True)
  files['open']=dump(asm,'V14_Modular_Open',mod[:-1]+[open_tray],names)
  files['one_piece_closed']=dump(asm,'V14_One_Piece_Closed',[fused]+a[16:19],['One_Piece_Frame']+names[16:])
  files['one_piece_open']=dump(asm,'V14_One_Piece_Open',[fused]+a[16:18]+[open_tray],['One_Piece_Frame']+names[16:])
  files['one_piece']=dump(pt,'One_Piece_Frame',[fused],['One_Piece_Frame'])
  for i in (0,1,2,3,16,17,18):
   part=mod[i];b=part.optimalBoundingBox();part=part.translated(V(-b.XMin,-b.YMin,-b.ZMin))
   files[names[i]]=dump(pt,names[i],[part],[names[i]])
  hardware=[]
  for j,p in enumerate(mod[4:16]):
   b=p.optimalBoundingBox()
   hardware.append(p.translated(V((j%6)*30-b.XMin,(j//6)*24-b.YMin,-b.ZMin)))
  files['all_frame_hardware']=dump(pt,'Modular_Rods_And_Cams_Independent_Bodies',hardware,names[4:16])
 s['files_sha256']={str(path.relative_to(o)):sha(path) for path in files.values()}
 s['seed_sha256']=stamp;s['coupon_seed_sha256']=sha(coupon)
 (o/'Validation.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
 (o/'Dimensions_Used.json').write_text(json.dumps(conf,ensure_ascii=False,indent=2)+'\n')
 print('Done:',o,flush=True)
if __name__=='__main__':cli()
