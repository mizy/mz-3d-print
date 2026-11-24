#!/usr/bin/env python3
"""Prototype selective modifications of verified V9 BRep surfaces in mm. No slicer."""
from pathlib import Path
import argparse,json,sys,hashlib,math,os,re
import FreeCAD as App,Part
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_frame_v9 import lock_geom,locked_at,V,X,Y,Z,box,union,sub,cyl,overlap,solid,fitlist,move,r,mx,pose,export as export_raw,sha
R=Path(__file__).resolve().parent
INPUT=R/'Inputs/V10_Base_Geometry.brep'

def export(seq,path):
 """Reject incorrect physical STEP units; some FreeCAD builds label raw mm as m."""
 res=export_raw(seq,path)
 def item_boxes_match(factor):
  parts=list(Part.read(str(path)).Solids)
  if len(parts)!=len(seq):return False
  for sent,read in zip((sh for _,sh in seq),parts):
   for span in ('XMin','XMax','YMin','YMax','ZMin','ZMax'):
    if abs(getattr(sent.BoundBox,span)*factor-getattr(read.BoundBox,span))>max(.00015,.00015*factor):
     return False
  return True
 if not item_boxes_match(1):
  assert item_boxes_match(1000),(path,'Unexpected STEP physical units; abort')
  blob=path.read_bytes()
  tagged,n=re.subn(rb'(?i)SI_UNIT\s*\(\s*\$\s*,\s*\.METRE\.\s*\)',b'SI_UNIT(.MILLI.,.METRE.)',blob)
  assert n>0,(path,'Incorrect STEP metre units with no known marker; abort')
  path.write_bytes(tagged)
  assert item_boxes_match(1),(path,'STEP dimensional validation failed')
  res['sha256']=sha(path)
 return res

def sdiff(a,b):return a.cut(b).Volume+b.cut(a).Volume
def scyl(x,y,z,rad,t):return cyl(x,y,z,rad,t,(1,0,0))
def build(p,src):
 y,z,drop,half,rad=(p[k] for k in ('hinge_y_mm','hinge_z_mm','wing_drop_mm','wing_y_half_mm','axle_radius_mm'))
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
 post=box(4.2,y-5.30,34.68,11,16.0,11.1)
 carrier=solid(union([src,post]))
 gate=box(12.28,y-1.24,34.55,3.08,10.02,12.2)
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
def repair_tray(old):
 # Local internal corner backing directs stop load into the side/back junction. Does not touch the engraving.
 f=[q for q in old.Faces if q.BoundBox.ZLength<1e-7 and abs(q.BoundBox.ZMin-10.)<1e-7];assert len(f)==1
 lim=f[0].extrude(V(0,0,32.))
 add=[box(16.68,189.1,30.4,5.8,3.15,4.85),box(17.8,191.10,34.2,4.7,1.2,5.42)]
 c=union(add).common(lim);ans=solid(union([old,c,mx(c,180.)]))
 mask=box(-.1,188.95,30.3,180.2,4.25,9.5)
 assert sdiff(ans.cut(mask),old.cut(mask))<.00015
 return ans
def auxiliary_lips(oldfront,oldrear,p):
    z=10.-p['auxiliary_floor_gap_mm']
    fx0,fx1=p['front_auxiliary_span_x_mm'];rx0,rx1=p['rear_auxiliary_span_x_mm']
    fy0,fy1=p['front_auxiliary_flat_y_mm'];ry0,ry1=p['rear_auxiliary_flat_y_mm']
    def w(x0,x1,coords):
        arr=[V(x0,y,h) for y,h in coords]
        return Part.Face(Part.makePolygon(arr+[arr[0]])).extrude(V(x1-x0,0,0))
    lipf=w(fx0,fx1,[(1.1,5.82),(1.1,z-1.6),(fy0,z),(fy1,z),(6.9,z-1.5),(6.9,5.82)])
    lipr=w(rx0,rx1,[(187.8,z-1.35),(ry0,z),(ry1,z),(198.8,z-2.65),(198.8,1.05),(194.6,1.05)])
    assert oldfront.common(lipf).Volume>10 and oldrear.common(lipr).Volume>10
    fg=solid(union([oldfront,lipf]));rg=solid(union([oldrear,lipr]))
    assert oldfront.cut(fg).Volume<.0002 and oldrear.cut(rg).Volume<.0002
    return fg,rg,lipf,lipr
def write_stage(config,out,emit_all=True):
 p=json.loads(config.read_text());dest=out/'STEP';dest.mkdir(exist_ok=True,parents=True);cou=out/'Trial';cou.mkdir(exist_ok=True)
 seed=list(Part.read(str(INPUT)).Solids);assert len(seed)==4
 source,oldfront,oldrear,t=seed;tray=repair_tray(t)
 b=build(p,source);L=b['carrier'];right=mx(L,180.)
 def both(q):return [q,mx(q,180.)]
 front,rear,lipf,lipr=auxiliary_lips(oldfront,oldrear,p)
 xl,xr=p['frame_turn_lock_mount_x_mm'];py=p['frame_turn_lock_station_y_mm'];pz=p['frame_turn_lock_axis_z_mm']
 pins=[locked_at(x,yy,pz,left) for yy in py for x,left in ((xl,True),(xr,False))]
 base=[L,right,front,rear]+pins
 fixed=base+both(b['axle'])+both(b['clip'])
 def layout(angle,key_mode):
     rr=r(mx(b['rotor'],180.),V(0,b['y'],b['z']),X,angle)
     return fixed+[b['rot'](angle),rr]+(both(b['key'](key_mode)) if key_mode else [])
 ks=layout(0,'lock');ps=layout(90,'park')
 names=['LeftSide','RightSide','LowBeam','LightX']+[f'StructuralFrameLock{i+1}' for i in range(4)]+['AxleL','AxleR','ClipL','ClipR','KeeperL','KeeperR','SelectorKeyL','SelectorKeyR']
 files={}
 def w(n,sh,folder=dest):
    items=sh if type(sh)==list else [(n[3:],sh)]
    files[n+'.step']=export(items,folder/(n+'.step'))
 w('01_V10_Left_Frame_Side_Local_Keepers',L)
 w('01b_V10_Right_Frame_Side_Local_Keepers',right)
 w('09_V10_Front_Beam_Auxiliary_Floor_Lip',front)
 w('10_V10_Light_Rear_X_Auxiliary_Floor_Lip',rear)
 w('02_V10_Left_Transverse_Keeper',b['rot'](0))
 w('02b_V10_Right_Transverse_Keeper',mx(b['rot'](0),180.))
 w('03_Captive_Lever_Axle_Print_Two',b['axle'])
 w('04_Axle_C_Clip_Print_Two',b['clip'])
 w('05_Mode_Selector_Key_Print_Two',b['key']('lock'))
 w('05b_V10_Structural_Frame_Turn_Lock_Print_Four',lock_geom())
 w('08_Signed_Flat_Tray_Local_Inner_Rear_Backers',tray)
 w('00_V10_Locked_Tray_Open_85mm_REFERENCE',list(zip(names,ks))+[('Signed_Tray_Open_85',move(tray,y=-85))])
 pp=lambda n,i,j:solid(union(list(n.common(box(-1,i,-1,30,j-i,58)).Solids)+[box(4.20,i+.1,5.0,3.4,3.8,40.0)]))
 w('11_Left_Keeper_Housing_27mm',pp(L,p['hinge_y_mm']-8,p['hinge_y_mm']+19),cou)
 print('BODY_EXPORTS_READY',flush=True)
 return locals()
def test(q):
 p,b,tray,base,ks,ps,files,out=[q[k] for k in ('p','b','tray','base','ks','ps','files','out')]
 res={'geometry_checks':{},'parameter_specification':p,'exports':files}
 eps=.00025
 def clear(k,v):
  x=max(v); print(k,x,flush=True)
  assert x<eps,(k,x)
  res['geometry_checks'][k]={'sample_poses':len(v),'max_overlap_mm3':x}
 def pair(parts):return max(overlap(v,w) for i,v in enumerate(parts) for w in parts[:i])
 clear('working_cad_parts',[pair(ks)]);clear('parked_cad_parts',[pair(ps)])
 a0=180.;off=[-.849,0,.849];zp=[0.,.45]
 for rev in (False,True):
  t=lambda q:pose(q,200.,180.,rev)
  d=t(tray);sig=1 if rev else -1
  locked=[t(s) for s in ks]; parked=[t(s) for s in ps]
  co=[(x*sig*-1,z) if False else (x if not rev else -x,z) for x in off for z in zp]
  clear(f'locked_run_{rev}',[fitlist(move(d,x=x,y=sig*run,z=z),locked) for x,z in co for run in (0,15,37,65,85,91.80,92.15)])
  clear(f'parked_extract_{rev}',[fitlist(move(d,x=x,y=sig*run,z=z),parked) for x,z in co for run in (0,30,85,92.,94.7,100,125,157,175,194)])
  st=[min(overlap(move(d,x=x,y=sig*92.75,z=z),t(k)) for k in ks[12:14]) for x,z in co]
  assert min(st)>.01,('axial_stop',rev,st)
  res['geometry_checks'][f'axial_stop_92p75_{rev}']=min(st)
 dr=move(tray,y=-84.); side=b['carrier'];t=lambda s:mx(s,180.)
 clear('rotation_0_to_100_after_nudge',[fitlist(b['rot'](a),[side,dr,b['axle'],b['clip']]) for a in range(0,101,5)])
 clear('lock_key_yields_to_intentional_x_removal',[fitlist(move(b['key']('lock'),x=x),[side,dr,b['rot'](0)]) for x in (0,1,2,3,4,6,9)])
 clear('park_key_enters_after_swing',[fitlist(move(b['key']('park'),x=x),[side,dr,b['rot'](100)]) for x in (0,1,2,3,4,6,9)])
 for n,shape in [('positive_lift_cannot_swing_locked',overlap(b['rot'](5),b['key']('lock'))),('negative_rotation_stops_on_frame',overlap(b['rot'](-5),side)),('park_key_resists_drop',overlap(b['rot'](85),b['key']('park')))]:
  assert shape>.025,(n,shape);res['geometry_checks'][n]=shape
 # Restrain pitch and roll after opening. This is geometric contact only, no stress/strong part claim.
 a=r(move(tray,y=-85.),V(90,0,10),X,.65)
 pitch_touches=[overlap(a,side) for side in ks[12:14]]
 assert min(pitch_touches)>.04,pitch_touches
 res['geometry_checks']['nose_down_pitch_degrees_0p65_both_lift_contacts_mm3']=pitch_touches
 z0=10.-p['auxiliary_floor_gap_mm']
 fc=next(f for f in tray.Faces if f.BoundBox.ZLength<1e-7 and abs(f.BoundBox.ZMin-10.)<1e-7)
 lf,lr=q['lipf'],q['lipr']
 lc=lambda a: next(f for f in a.Faces if f.BoundBox.ZLength<1e-7 and abs(f.BoundBox.ZMin-z0)<1e-7)
 facing=[]
 for y in (0,2,4,85.,92.15):
   floorproject=move(fc,y=-y,z=z0-10.)
   af=floorproject.common(lc(lf)).Area
   ar=floorproject.common(lc(lr)).Area
   facing.append({'open_mm':y,'front_potential_contact_mm2':af,'rear_potential_contact_mm2':ar})
   assert af>400. if y in (0,2,4,85.,92.15) else True
 assert facing[0]['rear_potential_contact_mm2']>450 and facing[-1]['rear_potential_contact_mm2']<.0002
 # Z offsets represent local floor sag only, not forced movement of supports/rails.
 res['auxiliary_floor_lips']={'top_z_mm':z0,'rail_and_underside_z_mm':10.,
     'nominal_gap_mm':10.-z0,'auxiliary_ridges_nominally_not_preloaded':True,'projected_bearing_faces_at_gap_mm':facing}
 res['scope']='prototype_only; no physical test, FEA capacity, app, slicer, V9 project change'
 (out/'V10_Validation.json').write_text(json.dumps(res,indent=2));return res
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--params',type=Path,default=R/'v10_parameters.json');p.add_argument('--out',type=Path,required=True);p.add_argument('--no-test',action='store_true');a=p.parse_args()
 v=write_stage(a.params,a.out)
 if not a.no_test: print(json.dumps(test(v)),flush=True)
