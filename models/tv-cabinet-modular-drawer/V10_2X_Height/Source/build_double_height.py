"""V10 2x height, exact STEP; standard archive never modified."""
from pathlib import Path
import argparse,hashlib,json,math,shutil,os,sys
import FreeCAD as A,Part
R=Path(__file__).resolve().parent
STANDARD=Path(os.environ.get('V10_STANDARD_DIR',R.parent.parent/'V10_Prototype')).resolve()
sys.path.insert(0,str(STANDARD/'Source'))
from build_frame_v9 import *
import build_v10 as V10

def crossparts(p,cen,inside):
    W,D,H,top=[p[k] for k in ('width_mm','depth_mm','stack_pitch_mm','profile_low_tie_top_mm')]
    # Low beam front face and load pad; main body below the V5-style transverse rib. Both tongues arrive from outside Y.
    seat=box(inside-3.19,.18,1.18,3.40,15.52,4.42)
    ft=union([box(inside+.14,0,0,W-2*(inside+.14),16,top),seat,mx(seat,W)])
    # Front and rear use EXACT same square face; structural brace stands behind tray y<=193.
    rev=my(seat,D)
    a,b=inside+.14,W-inside-.14
    y=D-5.70
    rear=union([box(a,y,0,b-a,5.70,5.85),box(a,y,H-5.65,b-a,5.70,5.65),
        box(a,y,4.9,13.8,5.7,H-9.7),box(b-13.8,y,4.9,13.8,5.7,H-9.7),
        web_xz(y,a+10,8,b-10,H-8,p.get("rear_diagonal_width_mm",7.3),5.7),web_xz(y,a+10,H-8,b-10,8,p.get("rear_diagonal_width_mm",7.3),5.7),
        box(W/2-10.5,y,H/2-7.2,21,5.7,14.4),rev,mx(rev,W)])
    for name,s,yy in (('front',ft,10.),('rear',rear,D-10.)):
        q=keyway(inside,yy,3.35)
        s=solid(sub(s,[q.mirror(V(inside,0,0),X),mx(q.mirror(V(inside,0,0),X),W)]))
        if name=='front':
            ft=solid(s.cut(box(inside-.01,7.1,.80,W-2*(inside-.01),5.8,8.)).removeSplitter())
        else:
            void=box(inside-.01,D-12.9,.84,7.0,5.8,5.9)
            rear=solid(sub(s,[void,mx(void,W)]))
    # Optional wide anchors are holes through rear shoulder only; hardware not supplied/rated.
    hh=p["drawer_wall_top_z_mm"]+p["drawer_upper_play_mm"]
    axisrel=[box(a-.01,y-.02,6.20,p["bilateral_ledge_extension_mm"]+.2,5.75,4.05),box(a-.01,y-.02,hh-.1,2.82,5.75,3.0)]
    rear=solid(sub(rear,[cyl(x,y-.10,24,1.8,6.,(0,1,0)) for x in (a+6.7,b-6.7)]+axisrel+[mx(q,W) for q in axisrel]))
    return ft,rear

# Only the tall carrier's vertical datum differs from the shared clearance policy.
def scyl(x,y,z,rad,t):return cyl(x,y,z,rad,t,(1,0,0))

def build_upper_rocker(p,src):
 y,z,drop,half,rad=(p[k] for k in ('hinge_y_mm','hinge_z_mm','wing_drop_mm','wing_y_half_mm','axle_radius_mm'))
 dz=z-43.6
 # BRep local rocker: outer tang transfers both rotation directions into frame / index key;
 # inner finger bears above side rim and intercepts rear fascia without tray flange.
 outer=box(12.45,y-1.07,z-6.66,3.40,2.14,6.66)
 # Offset the side-rim hold-down forward so the stop first hits the broader reinforced inboard face.
 arm=union([box(15.24,y-half,z-drop,3.60,half+.15,7.50),
            box(18.50,y-half,z-drop,2.60,2*half,7.50)])
 neck=scyl(12.45,y,z,2.43,8.65)
 toe=box(12.45,y+1.0,z-6.66,2.68,.60,3.55)
 rotor=solid(sub(union([outer,arm,neck,toe]),[scyl(12.42,y,z,1.73,8.75)]))
 def rot(t):return r(rotor,V(0,y,z),X,t)
 # Local frame post has no new outside extent. Pocket and key socket carry loads behind drawer envelope.
 post=box(4.2,y-5.30,34.68+dz,11,16.0,11.1)
 carrier=solid(union([src,post]))
 gate=box(12.28,y-1.24,34.55+dz,3.08,10.02,12.2)
 hub=scyl(12.26,y,z,2.58,3.10)
 bore=scyl(4.03,y,z,1.76,11.36)
 # Same key transfers from LOCK seat against the rotor tang to PARK seat beneath rotated arm.
 def key(mode):
  ky,kz=(y+1.77,z-6.34) if mode=='lock' else (y+5.33,z-3.77)
  return solid(box(10.23,ky,kz,4.94,2.08,2.60).cut(box(14.19,ky+.46,kz+.72,1.15,1.14,1.17)))
 def slit(mode):
  f=key(mode).BoundBox;return box(f.XMin-.18,f.YMin-.10,f.ZMin-.10,5.18,2.28,2.80)
 # End cap accessibility: a low-degree rotation is blocked by keyed tang, not by friction.
 carrier=solid(sub(carrier,[gate,hub,bore,slit('lock'),slit('park')]))
 # Remove the transverse axle by pulling its flat split clip from Y-front first. No front-entry travel pins.
 axle=solid(union([scyl(3.33,y,z,rad,0.37),scyl(3.68,y,z,1.25,0.75),
        scyl(4.35,y,z,rad,16.90),scyl(21.102,y,z,2.72,1.10)]))
 clip=solid(sub(scyl(3.73,y,z,2.85,.45),[scyl(3.60,y,z,1.33,.82),box(3.60,y-3.1,z-1.22,.82,3.12,2.44)]))
 return locals()

def make(op):
 q=json.loads((R/'double_height.json').read_text());p=json.loads((R/'frame_v9_parameters.json').read_text());v=json.loads((STANDARD/'Source/v10_parameters.json').read_text());B=STANDARD/'STEP'
 def grab(pref):return Part.read(str(next(B.glob(pref+'*.step'))))
 orig=list(grab('00_V10_').Solids);assert len(orig)==17
 H=q['stack_pitch_mm'];dz=H-p['stack_pitch_mm'];assert dz>0;keyx=15.2
 p['stack_pitch_mm']=H;p['drawer_wall_top_z_mm']+=dz;p['drawer_rear_top_z_mm']+=dz;p['rear_diagonal_width_mm']=q['rear_diagonal_width_mm']
 side,(cen,ins),ys=panel(p)
 h=p['drawer_wall_top_z_mm']+p['drawer_upper_play_mm']
 cuts=union([box(-.1,-.1,h-.00001,4.3,200.2,4.9),box(ins,-.1,h-.00001,4.4,200.2,4.9)])
 side=solid(side.cut(cuts).removeSplitter())
 v['hinge_z_mm']+=dz
 b=build_upper_rocker(v,side);left=b['carrier'];right=mx(left,180.)
 def both(s):return [s,mx(s,180.)]
 # The rocker, pin/clip and selector geometry is identical; installed Z changes only.
 oldkey=[10,11,12,13,14,15]
 for s,i in zip(both(b['clip'])+both(b['rot'](0))+both(b['key']('lock')),oldkey):
  assert V10.sdiff(move(s,z=-dz),orig[i])<.0002,(i,V10.sdiff(move(s,z=-dz),orig[i]))
 oldtray=grab('08');z=q['constant_wall_section_z_mm']
 def lo(zz):return box(-1,-1,-1,182,202,zz+1)
 lower=solid(oldtray.common(lo(z)));upper=solid(oldtray.cut(lo(z)))
 f=next(f for f in lower.Faces if abs(f.BoundBox.ZMin-z)<1e-8 and f.BoundBox.ZLength<1e-8 and len(f.Wires)==2)
 outer,inner=sorted(f.Wires,key=lambda w:Part.Face(w).Area,reverse=True)
 ring=f.extrude(V(0,0,dz))
 def offset(w,x):return w.makeOffset2D(x,0,False,False,False).Wires[0]
 extra=q['wall_inward_extra_mm'];blend=q['wall_transition_mm']
 if extra:
  assert 2*blend<dz and .05<extra<.7
  ship=offset(inner,.04);assert Part.Face(ship).Area<Part.Face(outer).Area
  hollow=offset(inner,-extra);assert Part.Face(hollow).Area<Part.Face(inner).Area
  def sec(w,i):return move(w,z=i)
  core=union([Part.makeLoft([sec(inner,0),sec(hollow,blend)],True,True),Part.Face(sec(hollow,blend)).extrude(V(0,0,dz-2*blend)),Part.makeLoft([sec(hollow,dz-blend),sec(inner,dz)],True,True)])
  liner=Part.Face(ship).extrude(V(0,0,dz)).cut(core)
  ring=solid(union([ring,liner]))
 tray=solid(union([lower,ring,move(upper,z=dz)]))
 glyph_probe=box(29.5,192.92,13.04,53,.08,15.96)
 assert V10.sdiff(move(tray.common(move(glyph_probe,z=dz)),z=-dz),oldtray.common(glyph_probe))<.0002
 assert V10.sdiff(tray.common(lo(z)),lower)<.0002
 assert V10.sdiff(move(tray.cut(lo(z+dz)),z=-dz),upper)<.0002
 # Keep exact original rear lip/low-end assembly interfaces, build a tall X with
 # physically same-size strokes, mounting holes and vertical supporting ends.
 front=grab('09');oldrear=grab('10');_,tall=crossparts(p,cen,ins)
 cut=lo(q['rear_splice_z_mm']);rear=solid(union([oldrear.common(cut),tall.cut(cut)]))
 assert V10.sdiff(rear.common(cut),oldrear.common(cut))<.0002
 base=[left,right,front,rear]+orig[4:8]
 fixed=base+both(b['axle'])+both(b['clip'])
 def layout(a,k):return fixed+[b['rot'](a),r(mx(b['rotor'],180.),V(0,b['y'],b['z']),X,a)]+both(b['key'](k))
 lock=layout(0,'lock');park=layout(90,'park')
 dest=op/'STEP';dest.mkdir(parents=True,exist_ok=True);files={}
 def dump(name,parts):files[name]=V10.export(parts,dest/(name+'.step'))
 def single(name,s):dump(name,[(name,s)])
 for name,part in [('01_V10_2X_Side_Left',left),('01b_V10_2X_Side_Right',right),('08_V10_2X_Signed_Tray',tray),('10_V10_2X_Rear_X_Lip',rear)]:single(name,part)
 # Shared production models stay in the standard directory.
 refs={}
 for pref in ('02_','02b_','03_','04_','05_Mode','05b_','09_'):
  f=next(B.glob(pref+'*.step'));refs[f.stem]={'shared_with_standard':True,'sha256':V10.sha(f)}
 names=['SideL','SideR','FrontLip','RearXTallLip']+[f'StructuralTurnLock{i+1}' for i in range(4)]+['AxleL','AxleR','ClipL','ClipR','RockerL','RockerR','SelectorL','SelectorR']
 dump('00_V10_2X_Locked_Open85_REFERENCE',list(zip(names,lock))+[('SignedTray',move(tray,y=-85))])
 print('READY',flush=True)
 return locals()
def checks(a):
 def pair(parts):return max(overlap(v,w) for i,v in enumerate(parts) for w in parts[:i])
 eps=.00025
 out={}
 def check(k,v):
  assert max(v)<eps,(k,max(v));out[k]={'samples':len(v),'max_overlap_mm3':max(v)};print(k,out[k],flush=True)
 lock,park,t,b,dz=a['lock'],a['park'],a['tray'],a['b'],a['dz']
 check('working_frames',[pair(lock),pair(park)])
 offsets=[(dx,z) for dx in (-.849,0,.849) for z in (0.,.45)]
 for rev in (False,True):
  T=lambda x:pose(x,200,180,rev)
  ll,pp=list(map(T,lock)),list(map(T,park));s=1 if rev else -1
  tr=T(t)
  check(f'lockrun_{rev}',[fitlist(move(tr,x=x,z=z,y=s*y),ll) for x,z in offsets for y in (0,37,65,85,91.8,92.15)])
  check(f'release_{rev}',[fitlist(move(tr,x=x,z=z,y=s*y),pp) for x,z in offsets for y in (0,30,85,92,94.7,100,125,157,175,194)])
  w=[min(overlap(move(tr,x=x,z=z,y=s*92.75),k) for k in ll[12:14]) for x,z in offsets];assert min(w)>.01,(rev,w)
  out[f'stop_contact_{rev}']={'position_mm':92.75,'min_overlap_mm3':min(w)}
 d=move(t,y=-84)
 check('rotate_after_nudge',[fitlist(b['rot'](ang),[b['carrier'],d,b['axle'],b['clip']]) for ang in range(0,101,5)])
 for mode,ang in [('lock',0),('park',100)]:
  check(f'{mode}_key_path',[fitlist(move(b['key'](mode),x=x),[b['carrier'],d,b['rot'](ang)]) for x in (0,1,2,3,4,6,9)])
 pitch=[overlap(r(move(t,y=-85),V(90,0,10),X,.65),side) for side in lock[12:14]];assert min(pitch)>.04,pitch;out['pitch_contact_0p65deg_mm3']=pitch
 # Stack mating has same part geometry and unchanged assembly datum.
 h=a['H'];p=a['p'];side=b['carrier'];cen,ins,ys=a['cen'],a['ins'],a['ys'];front,_=bushings(p,cen,ins,ys[0]);_,rear=bushings(p,cen,ins,ys[1])
 vert=[move(side,z=h)]
 for j,(y,loc) in enumerate(zip(ys,[front,rear])):
  vert.extend([move(loc,z=h),locked_at(ins,y,h+p['stack_pin_nominal_height_mm'])])
 check('stack_joint_left_with_bushings_and_locks',[pair([side]+vert)])
 a0=a['oldtray'].BoundBox;t0=t.BoundBox
 out['dimensions_mm']=dict(footprint=[180,200],stack_pitch=h,original_stack_pitch=h-dz,frame_z_max=side.BoundBox.ZMax,original_drawer_total_height=a0.ZLength,drawer_total_height=t0.ZLength,drawer_floor_top_z=12.6,drawer_high_side_z=t0.ZMax,ordinary_side_lip_top_z=83.5,ordinary_side_usable_height=83.5-12.6,maximum_end_usable_height=t0.ZMax-12.6,rocker_axis_z=b['z'],x_y_unchanged=[abs(t0.XLength-a0.XLength)<1e-7,abs(t0.YLength-a0.YLength)<1e-7])
 out['scope']='BRep assembly motion samples only; no slicer, FEA, print, hardware validation'
 out['exports']=a['files'];out['shared_files']=a['refs']
 (a['op']/'V10_2X_TEST.json').write_text(json.dumps(out,indent=2))
if __name__=='__main__':
 l=argparse.ArgumentParser();l.add_argument('--out',type=Path,required=True);l.add_argument('--skip-tests',action='store_true');args=l.parse_args();a=make(args.out)
 if not args.skip_tests:checks(a)
