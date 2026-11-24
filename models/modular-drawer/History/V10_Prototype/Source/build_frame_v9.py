#!/usr/bin/env python3
"""Independent V9 CAD source. FreeCAD/Part/Import. No slicer or old artifacts required."""
import argparse,json,hashlib,math
from pathlib import Path
import FreeCAD as App, Part, Import
from brep_tools import V,box,cyl,prism,rounded,sub,union,move,web_yz,web_xz
ROOT=Path(__file__).resolve().parent
X,Y,Z=V(1,0,0),V(0,1,0),V(0,0,1)
def solid(s):
    assert s.isValid() and len(s.Solids)==1,(s.isValid(),len(s.Solids))
    return s.Solids[0]
def r(s,o,ax,angle):
    q=s.copy();q.rotate(o,ax,angle);return q
def mx(s,w):return s.mirror(V(w/2,0,0),X)
def my(s,d):return s.mirror(V(0,d/2,0),Y)
def cap(x,y,z,rad,travel,h):
    if travel==0:return cyl(x,y,z,rad,h)
    return union([box(x-rad,y-travel,z,rad*2,travel*2,h),cyl(x,y-travel,z,rad,h),cyl(x,y+travel,z,rad,h)])
def radial(x,y,z,rad,length,yrel=0):
    q=cyl(x,y,z,rad,length,(1,0,0))
    if yrel:q=union([move(q,y=yrel),move(q,y=-yrel),box(x,y-yrel,z-rad,length,2*yrel,2*rad)])
    return q
def keyway(x,y,z,yrel=0.):
    """Left face local handedness: opening where +X goes into part."""
    return union([radial(x-.16,y,z,1.42,5.30+.16,yrel),
        radial(x+.82,y,z,2.42,1.30,yrel),
        box(x-.15,y-2.35-yrel,z-.62,2.27,4.7+2*yrel,1.24)])
def lock_geom(rot=0,extension=0):
    # PETG lock, insertion lug aligned Y, rotates 90° to prevent axial back-out.
    q=union([radial(-1.75,0,0,2.4,1.75),radial(-.08,0,0,1.11,5.15),
             box(1.05,-2.15,-.38,.78,4.30,.76)])
    # Visible slot aligns with the lugs, so user can tell inserted from locked.
    q=q.cut(box(-1.8,-1.91,-.28,.64,3.82,.56)).removeSplitter()
    return move(r(solid(q),V(),X,rot),x=extension)
def locked_at(face,y,z,from_right=True,rot=90,backout=0):
    q=lock_geom(rot)
    if from_right:q=r(q,V(),Z,180)
    return move(q,x=face+(backout if from_right else -backout),y=y,z=z)
def shelf(section,L,D):
    return prism([(x,0,z) for x,z in section],(0,D,0))
def panel(p):
    W,D,H,T,E,fl=[p[k] for k in ('width_mm','depth_mm','stack_pitch_mm','panel_thickness_mm','bilateral_ledge_extension_mm','ledge_top_z_mm')]
    cen=E+T/2; inside=E+T; lo=E; h=p['drawer_wall_top_z_mm']+p['drawer_upper_play_mm']
    assert W>=120 and D>=160 and H>=h+4.5
    y0,y1=p['stack_locator_offset_mm'],D-p['stack_locator_offset_mm']
    br=solid(union([box(E,0,0,T,D,10.15),box(E,0,h-.23,T,D,H-h+.23),box(E,0,8,T,36,H-16),box(E,D-36,8,T,36,H-16),
                    web_yz(E,31,9.7,D-31,h,7,T),web_yz(E,31,h,D-31,9.7,7,T),
                    shelf([(inside-.16,6.3),(inside+1.9,6.3),(inside+E,8.5),(inside+E,fl),(inside-.16,fl)],D,D),
                    shelf([(lo+.16,6.3),(lo-1.9,6.3),(lo-E,8.5),(lo-E,fl),(lo+.16,fl)],D,D),
                    shelf([(inside-.13,h),(inside+2.65,h),(inside+2.65,h+1.45),(inside-.13,h+2.85)],D,D),
                    shelf([(lo+.13,h),(lo-2.65,h),(lo-2.65,h+1.45),(lo+.13,h+2.85)],D,D)
                    ]+[cyl(cen,cy,H-.4,p['stack_locator_male_OD_mm']/2,p['stack_locator_height_mm']+.4) for cy in (y0,y1)]))
    cuts=[]
    def faceways(cy,cz,rel=0):
        u=keyway(E,cy,cz,rel)
        return [u,mx(u,E+inside)]
    # Square end tongues slide along Y; outer seats are identical, enabling a two-bay reference with shared middle panel.
    sock=box(inside-3.53,-.2,.86,3.67,16.55,5.18)
    cuts +=[sock,mx(sock,E+inside),my(sock,D),mx(my(sock,D),E+inside)]
    for yy in (10.,D-10.): cuts+=faceways(yy,3.35)
    Zpin=p['stack_pin_nominal_height_mm']
    for cy in (y0,y1):
        cuts +=[cap(cen,cy,-.10,4.18,1.60,p['stack_locator_height_mm']+.68),
                radial(E-.25,cy,H+Zpin,1.42,T+.50)]
        cuts+=faceways(cy,Zpin,p['stack_rear_slot_relief_each_end_mm'])
    return solid(sub(br,cuts)), (cen,inside),(y0,y1)
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
        web_xz(y,a+10,8,b-10,H-8,7.3,5.7),web_xz(y,a+10,H-8,b-10,8,7.3,5.7),
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
def bushings(p,x,inside,y):
    H,L,rel=[p[k] for k in ('stack_locator_height_mm','stack_pin_nominal_height_mm','stack_rear_slot_relief_each_end_mm')]
    s=cap(x,y,0,4.01,1.52,H+.12)
    inner=[cap(x,y,-.04,3.21,k,H+.42) for k in (0.,rel)]
    ww=keyway(inside,y,L,rel).mirror(V(inside,0,0),X)
    return [solid(sub(s,[q,ww,mx(ww,2*x)])) for q in inner]
def tray(p,inside):
    W,D,z,fp,top,rt=[p[i] for i in ('width_mm','depth_mm','ledge_top_z_mm','drawer_floor_mm','drawer_wall_top_z_mm','drawer_rear_top_z_mm')]
    X0=inside+p['drawer_side_play_per_side_mm'];w=W-2*X0;y=3.0;l=D-10.0
    # Flush exterior, no polygon outside the walls for floor/rail flanges.
    fr=y; bk=y+l; th=.96; R=3.1; bot=z+fp-.20
    floor=rounded(X0,y,z,w,l,fp,R)
    def tube(t):
        return rounded(X0,fr,bot,w,l,top-bot,R).cut(rounded(X0+t,fr+t,bot-.20,w-2*t,l-2*t,top-bot+.40,R-t))
    def poly(points):return prism([(-1,q,h) for q,h in points],(W+2,0,0))
    slope=bk-20;end=bk-6
    upper=poly([(fr-2,top),(slope,top),(end,rt),(bk+2,rt),(bk+2,top+3),(fr-2,top+3)])
    lower=poly([(fr-2,0),(bk+2,0),(bk+2,rt-2.5),(end,rt-2.5),(slope,top-2.5),(fr-2,top-2.5)])
    wall=tube(th).cut(upper);rim=tube(1.64).cut(lower).cut(upper)
    pad=rounded(W/2-24.5,fr,top-12,49,2.70,12,1.10)
    yy=y+p['drawer_underside_rib_from_front_mm'];depth=p['drawer_underside_rib_depth_mm']
    rib=prism([(X0+7,yy-.80,z-depth),(X0+7,yy+.80,z-depth),(X0+7,yy+1.5,z+.17),(X0+7,yy-1.5,z+.17)],(w-14,0,0))
    raw=union([floor,wall,rim,pad,rib])
    notch=rounded(W/2-19.25,top-9.5,0,38.5,19.9,8.,4.2)
    notch=r(notch,V(),X,90)
    return solid(raw.cut(move(notch,y=fr+6.0)).removeSplitter())
def overlap(a,b):
    q=a.BoundBox;v=b.BoundBox
    if any(min(getattr(q,k+'Max'),getattr(v,k+'Max'))-max(getattr(q,k+'Min'),getattr(v,k+'Min'))<1e-7 for k in 'XYZ'):return 0.
    return sum(x.common(z).Volume for x in a.Solids for z in b.Solids)
def fitlist(q,c):return max([overlap(q,z) for z in c] or [0.])
def pose(q,D,W,rev):
    return r(q,V(W/2,D/2,0),Z,180) if rev else q
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def export(seq,path):
    d=App.newDocument('Manufacturing')
    try:
        obs=[]
        for n,s in seq:
            obj=d.addObject('Part::Feature',n);obj.Shape=s;obs.append(obj)
        d.recompute();Import.export(obs,str(path))
    finally:App.closeDocument(d.Name)
    rs=Part.read(str(path)); assert rs.isValid() and len(rs.Solids)==len(seq),(path,rs.isValid(),len(rs.Solids),len(seq))
    return {'bodies':len(rs.Solids),'sha256':sha(path)}
def make(p,op):
    W,D,H=p['width_mm'],p['depth_mm'],p['stack_pitch_mm']; side, (cen,ins), loc=panel(p)
    right=mx(side,W);ft,rb=crossparts(p,cen,ins);d=tray(p,ins)
    f0,_=bushings(p,cen,ins,loc[0]);_,rs=bushings(p,cen,ins,loc[1]);pinz=p['stack_pin_nominal_height_mm']
    one=[('Side_L',side),('Side_R',right),('Front_Tie',ft),('Rear_X',rb)]
    parts=one+[('Tray',d)]
    barpins=[]
    for yy in (10.,D-10.):
        barpins.extend([locked_at(ins,yy,3.35),locked_at(W-ins,yy,3.35,False)])
    parts += [(f'Beam_Lock_{i+1}',k) for i,k in enumerate(barpins)]
    step=op/'STEP';step.mkdir(exist_ok=True,parents=True)
    smp=op/'Fit_samples';smp.mkdir(exist_ok=True)
    files={}
    for n,q in [('01_reversible_side_panel',side),('02_low_front_crossbeam',ft),
                ('03_removable_rear_X_brace',rb),('04_V9_drawer_no_bottom_flange',d),
                ('05_transverse_turn_lock_print_trial',lock_geom()),('06_front_round_locator_insert',f0),
                ('07_rear_float_locator_insert',rs)]:
        q=move(q,y=-loc[0] if n.startswith('06') else -loc[1]) # locators are printed centered in Y 
        files[n]=export([(n[3:],q)],step/(n+'.step'))
    files['00_closed']=export(parts,step/'00_closed_assembly_REFERENCE.step')
    openpose=[(n,move(q,y=-85.) if n=='Tray' else q) for n,q in parts]
    files['00b_open']=export(openpose,step/'00b_open_85mm_assembly_REFERENCE.step')
    vertical=[]
    for i,(yy,s) in enumerate(zip(loc,(f0,rs))):
        vertical += [(f'Locator_Insert_L_{i}', move(s,z=H)),(f'Locator_Insert_R_{i}',move(mx(s,W),z=H))]
        vertical += [(f'Stack_Lock_L_{i}', locked_at(ins,yy,H+pinz)),(f'Stack_Lock_R_{i}', locked_at(W-ins,yy,H+pinz,False))]
    upper=[(n+'_Upper',move(s,z=H)) for n,s in parts]
    files['00c_stack']=export(parts+upper+vertical,step/'00c_two_stack_assembly_REFERENCE.step')
    dx=W-2*cen
    extend=[(n+'_Bay2',move(q,x=dx)) for n,q in parts if n!='Side_L']
    files['00d_shared_panel']=export(parts+extend,step/'00d_two_bays_shared_middle_panel_REFERENCE.step')
    # Coupon retains real block edge and screwless lock recess at beam station.
    sidecut=solid(side.common(box(0,0,-.05,ins+.1,20,10.4)))
    jointcut=solid(ft.common(box(ins-4.0,-.1,-.05,16.,16.4,7.0)))
    files['coupon_seat']=export([('Side_Seat_Coupon',sidecut)],smp/'01_side_seat_coupon.step')
    files['coupon_tongue']=export([('Beam_Tongue_Coupon',jointcut)],smp/'02_beam_tongue_coupon.step')
    files['coupon_key']=export([('Key',lock_geom())],smp/'03_lock_coupon_actual_size.step')
    return locals()
def validate(c):
    p,W,D,H,ins,cen,loc=[c[k] for k in ('p','W','D','H','ins','cen','loc')]
    side,rt,ft,rb,d,pinz=[c[k] for k in ('side','right','ft','rb','d','pinz')]
    one=[q for _,q in c['one']]; parts=c['parts'];bush=(c['f0'],c['rs'])
    results={'V9_parameters_mm':p,'exported_STEP':c['files']}
    def maxpairs(ss):
        return max([overlap(q,v) for i,(_,q) in enumerate(ss) for _,v in ss[:i]] or [0.])
    def assertclear(label,vals,tol=.0002):
        if max(vals)>tol:raise ValueError((label,[round(v,6) for v in vals]))
        results[label]={'poses':len(vals),'max_interference_mm3':round(max(vals),8)}
    assertclear('single_closed_solids', [maxpairs(parts)])
    # Top/bottom asymmetry intentional, X & Y reflect in actual reversible panel.
    for label,q in [('same_side_mirror_X',mx(side,2*cen)),('same_side_mirror_Y',my(side,D))]:
        assertclear(label,[side.cut(q).Volume+q.cut(side).Volume])
    assertclear('front_tongue_inserted_from_front',[fitlist(move(ft,y=-y),[side,rt,rb]) for y in (20,15,12,10,6,3,1,.2,0)])
    assertclear('rear_tongue_inserted_from_rear',[fitlist(move(rb,y=y),[side,rt,ft]) for y in (20,15,12,10,6,3,1,.2,0)])
    def locking_moves(keycases,n):
        direct=[]; turns=[]; back=[]
        for x,y,z,fr,targets,held in keycases:
            direct += [fitlist(locked_at(x,y,z,fr,0,t),targets) for t in (8,6,4,3,2,1.3,.9,.5,.2,0)]
            turns += [fitlist(locked_at(x,y,z,fr,angle),targets) for angle in range(0,91,15)]
            back.append(fitlist(locked_at(x,y,z,fr,90,.61),held))
        assertclear(n+'_insert_keyed',direct);assertclear(n+'_rotate90',turns)
        assert min(back)>.05,(n,back)
        results[n+'_locked_attempted_0p61mm_axial_pull_overlap_mm3']=[round(x,5) for x in back]
    lockcases=[]
    for yy in (10.,D-10.):
        lockcases.extend([(ins,yy,3.35,True,one,one),(W-ins,yy,3.35,False,one,one)])
    locking_moves(lockcases,'crosspiece_locks')
    results['crossbeam_locked_attempted_disconnect_0p9mm_overlap_mm3']=[round(fitlist(move(ft,y=-.9),c['barpins'][:2]),6),round(fitlist(move(rb,y=.9),c['barpins'][2:]),6)]
    assert min(results['crossbeam_locked_attempted_disconnect_0p9mm_overlap_mm3'])>.10
    for reverse in (False,True):
        fix=[pose(q,D,W,reverse) for n,q in parts if n!='Tray']
        # Test symmetry by physically reversing which end receives cross-pieces/notch; sign flips in reverse.
        s=-1 if reverse else 1
        floatx=p['drawer_side_play_per_side_mm'];floatz=p['drawer_upper_play_mm']
        ys=(0,10,30,45,52,66,75,85,93,100,120,150,177,190,193,194)
        assertclear('no_flange_tray_sweep_input_'+('reverse' if reverse else 'normal'),
                   [fitlist(move(pose(d,D,W,reverse),x=dx,y=-s*y,z=zz),fix)
                    for y in ys for dx in (-floatx,0,floatx) for zz in (0,floatz)])
        lifted=[fitlist(move(pose(d,D,W,reverse),x=dx,y=-s*y,z=floatz+.22),fix)
                    for y in (0,47,85) for dx in (-floatx,0,floatx)]
        assert min(lifted)>.1,lifted
        results['keeper_contact_at_0p87_lift_'+('reverse' if reverse else 'normal')]=min(lifted)
    upper=[(n+'_Upper',move(q,z=H)) for n,q in parts]
    assertclear('stack_installed_all_beyond_intended_face_contacts',[maxpairs(parts+upper+c['vertical'])])
    lowerbare=[side,rt,ft,rb]
    upperbare=[move(q,z=H) for q in lowerbare]+[move(q,z=H) for q in (bush[0],bush[1],mx(bush[0],W),mx(bush[1],W))]
    assertclear('vertical_stack_insertion_before_transverse_locks',
                [max(fitlist(move(q,z=v),lowerbare) for q in upperbare) for v in (18,12,8,6,4,2,1,.2,0)])
    stackcases=[]
    for yy in loc:
        stackcases.extend([(ins,yy,H+pinz,True,lowerbare+upperbare,[upperbare[0]]),
                         (W-ins,yy,H+pinz,False,lowerbare+upperbare,[upperbare[1]])])
    locking_moves(stackcases,'stack_locks')
    # Local rear datum offset: compare each centered upper bushing to the lower locator and test its real slotted lock passage.
    oy=loc[1]; mk=side.common(box(cen-3.1,oy-3.1,H,6.2,6.2,6.0))
    vals=[];vary=(-1.15,0,1.15)
    for e in vary:
        cm=move(mk,y=e)
        assert overlap(cm,upperbare[0])+overlap(cm,move(bush[1],z=H))<.0002
        vals.extend([fitlist(locked_at(ins,oy+e,H+pinz,True,0,t),[upperbare[0],move(bush[1],z=H),cm]) for t in (0,.6,2.,4.)])
    assertclear('rear_slot_local_allowable_alignment_test',vals)
    results['rear_socket_same_lock_test_offsets_mm']=vary
    assertclear('adjacent_bays_one_shared_panel',[maxpairs(parts+c['extend'])])
    results['measured']={'floor_solid_thickness_mm':p['drawer_floor_mm'],
        'drawer_bbox_xyz_mm':[d.BoundBox.XLength,d.BoundBox.YLength,d.BoundBox.ZLength],
        'low_tie_to_drawer_rib_nominal_vertical_mm':10.-p['drawer_underside_rib_depth_mm']-p['profile_low_tie_top_mm'],
        'drawer_side_play_nominal_each_mm':p['drawer_side_play_per_side_mm'],
        'bearing_nominal_overlap_mm':p['bilateral_ledge_extension_mm']-p['drawer_side_play_per_side_mm'],
        'upper_lip_nominal_overlap_mm':2.65-p['drawer_side_play_per_side_mm'],
        'drawer_solid_CAD_PLA_mass_g':d.Volume*.00124,
        'frame_geom_front_to_back_clearance_to_closed_drawer_back_mm':1.30,
        'frame_ext_xyz_including_stacking_pegs_mm':[W,D,H+p['stack_locator_height_mm']],
        'stack_pitch_mm':H,'optional_drawer_travel_stop_modeled':False,
        'no_slicer_or_physical_test':True}
    return results
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--params',type=Path,default=ROOT/'frame_v9_parameters.json');ap.add_argument('--out',type=Path,default=ROOT);ap.add_argument('--skip-validation',action='store_true');ns=ap.parse_args()
    cfg=json.loads(ns.params.read_text());c=make(cfg,ns.out)
    print('STEPs written',flush=True)
    if not ns.skip_validation:
        stats=validate(c); (ns.out/'Validation_V9.json').write_text(json.dumps(stats,indent=2,ensure_ascii=False))
        print(json.dumps(stats,ensure_ascii=False),flush=True)
