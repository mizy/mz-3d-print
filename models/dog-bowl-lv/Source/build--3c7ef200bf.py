import cadquery as cq,math,json
from pathlib import Path
P=Path('/Users/miaozhuang/projects/mz-3d-print/models/dog-bowl-lv/Models/FullSides_HollowRaisedClip_Candidate/lv/parts');O=Path('/private/tmp/lv-tenon-step')
def load(n):return cq.importers.importStep(str(P/(n+'.step'))).val()
blue=load('blue_middle_z2_28');bottom=load('ivory_bottom_z0_2');top=load('ivory_top_z28_30');logo=load('ivory_glue_logo')
# Extend the original unmodified LV outline backward, then conform its back to radius80.15.
logo=logo.fuse(logo.translate((0,.85,0))).clean()
inside=cq.Solid.makeCylinder(80.15,40,cq.Vector(0,-10,-5),cq.Vector(0,0,1))
logo=logo.cut(inside).clean()
points=[(-3.,10.),(-5.,20.)];holes=[];pegs=[];travel=1.5
for x,z in points:
 ys=-10-math.sqrt(80**2-x*x)
 def cyl(r,y,h,zz):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,zz),cq.Vector(0,1,0))
 neck=cyl(.75,ys-.45,1.45,z);head=cyl(1.05,ys+.9,.5,z)
 pegs.append(neck.fuse(head))
 # External entry pocket at z+1.5; lower retention shoulder blocks outward withdrawal.
 entry=cyl(1.25,ys-.6,2.45,z+travel)
 neckslot=cyl(.95,ys-.6,2.45,z).fuse(cyl(.95,ys-.6,2.45,z+travel)).fuse(cq.Workplane('XY').box(1.9,2.45,travel,centered=(True,False,False)).translate((x,ys-.6,z)).val())
 cavity=cyl(1.25,ys+.7,1.15,z).fuse(cyl(1.25,ys+.7,1.15,z+travel)).fuse(cq.Workplane('XY').box(2.5,1.15,travel,centered=(True,False,False)).translate((x,ys+.7,z)).val())
 holes.append(entry.fuse(neckslot).fuse(cavity))
logo=logo.fuse(*pegs).clean();blue=blue.cut(*holes).clean()
parts=[('ivory_bottom',bottom,(.988,.925,.839)),('light_blue_body',blue,(.725,.851,.922)),('ivory_rim',top,(.988,.925,.839))]
a=cq.Assembly(name='LV_bowl_keyhole_tenon_candidate')
report={}
for n,s,c in parts:
 assert s.isValid() and len(s.Solids())==1,(n,s.isValid(),len(s.Solids()))
 a.add(s,name=n,color=cq.Color(*c));report[n]={'solids':len(s.Solids()),'volume':s.Volume()}
a.save(str(O/'LV_bowl_multibody.step'))
assert logo.isValid() and len(logo.Solids())==1,('logo',logo.isValid(),len(logo.Solids()))
cq.exporters.export(logo,str(O/'LV_logo_tenon_assembly_position.step'))
flat=logo.rotate((0,0,0),(1,0,0),90);bb=flat.BoundingBox();flat=flat.translate((-(bb.xmin+bb.xmax)/2,-(bb.ymin+bb.ymax)/2,-bb.zmin));cq.exporters.export(flat,str(O/'LV_logo_tenon.step'))
# Actual local bowl front-wall piece with both pockets and same curved interface.
clipbox=cq.Workplane('XY').box(18,9,24,centered=(True,True,False)).translate((-3,-89,3)).val()
coupon=blue.intersect(clipbox).clean();assert coupon.isValid();cq.exporters.export(coupon,str(O/'LV_logo_socket_test.step'))
report.update(logo_solids=len(logo.Solids()),interference_mm3=blue.intersect(logo).Volume(),clearance_radial_mm=.2,travel_down_mm=travel,min_nominal_remaining_wall_mm=1.35,peg_positions_x_z=points)
re=cq.importers.importStep(str(O/'LV_bowl_multibody.step')).val();report['roundtrip_solids']=len(re.Solids());assert len(re.Solids())==3
(O/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
