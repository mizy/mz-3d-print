import cadquery as cq, math,json
from pathlib import Path
from surface_helpers import directface
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
from OCP.BRepLib import BRepLib
R=Path(__file__).parent; O=R/'parts';O.mkdir(exist_ok=True)
H=81.;W=160.; GAP=3.; WIDTH=70.;DEPTH=8.5;CH=30.;NECK=18.;BAR=8.5
lengths=[80*math.pi,57,4*math.pi,144,4*math.pi,57];P=sum(lengths);PERIOD=P/22

def base(seg,t):
 if seg==0:
  a=math.pi+t*math.pi;return 80*math.cos(a),-10+80*math.sin(a),math.cos(a),math.sin(a)
 if seg==1:return 80,-10+57*t,1,0
 if seg==2:
  a=t*math.pi/2;return 72+8*math.cos(a),47+8*math.sin(a),math.cos(a),math.sin(a)
 if seg==3:return 72-144*t,55,0,1
 if seg==4:
  a=math.pi/2+t*math.pi/2;return -72+8*math.cos(a),47+8*math.sin(a),math.cos(a),math.sin(a)
 return -80,47-57*t,-1,0

def point(seg,t,z):
 x,y,nx,ny=base(seg,t); s=sum(lengths[:seg])+lengths[seg]*t
 q=abs(math.sin(math.pi*(s+z)/PERIOD)*math.sin(math.pi*(s-z)/PERIOD))
 fade=max(0,min(1,z/6,(H-z)/6));fade=fade*fade*(3-2*fade)
 # Preserve exact rear mounting plane, soften corner transitions.
 rearfade=max(0,min(1,(50-y)/12))
 bulge=3.1*q**.48*fade*rearfade
 return cq.Vector(x+nx*bulge,y+ny*bulge,z)

def outline(off=0,z=0):
 r=80-off;back=55-off;c=8
 return cq.Workplane('XY',origin=(0,0,z)).moveTo(-r,-10).lineTo(-r,back-c).radiusArc((-r+c,back),c).lineTo(r-c,back).radiusArc((r,back-c),c).lineTo(r,-10).threePointArc((0,-10-r),(-r,-10)).close().val()
def solid(off,z,h):return cq.Solid.extrudeLinear(outline(off,z),[],cq.Vector(0,0,h))
def box(w,d,h,x,y,z):return cq.Workplane('XY').box(w,d,h,centered=(True,True,False)).translate((x,y,z)).val()
faces=[]
for seg,L in enumerate(lengths):
 nu=max(20,int(L));nv=102
 faces.append(directface([[point(seg,i/nu,H*j/(nv-1)) for j in range(nv)] for i in range(nu+1)]));print('face',seg,flush=True)
faces.extend([cq.Face.makeFromWires(outline(0,0)),cq.Face.makeFromWires(outline(0,H))])
sew=BRepBuilderAPI_Sewing(.06)
for f in faces:sew.Add(f.wrapped)
sew.Perform();ss=cq.Shape.cast(sew.SewedShape()); outer=cq.Solid.makeSolid(ss if isinstance(ss,cq.Shell) else ss.Shells()[0]).fix();BRepLib.OrientClosedSolid_s(outer.wrapped)
print('outer',outer.isValid(),outer.Volume(),flush=True)
inner=solid(3.2,4,90)
try:inner=cq.Workplane(obj=inner).edges('<Z').fillet(4).val()
except:pass
body=outer.cut(inner).clean(); print('hollow',body.isValid(),len(body.Solids()),flush=True)
# Inverted T: the entire 70mm wide bar starts at Z=0.
def clip():return box(WIDTH,DEPTH,BAR,0,DEPTH/2,0).fuse(box(NECK,DEPTH,CH-BAR+1,0,DEPTH/2,BAR-1)).clean()
cp=clip().translate((0,55+GAP,0))
root=box(NECK,GAP+3,CH,0,55+(GAP-1)/2,0)
body=body.fuse(cp).fuse(root).clean()
rim=solid(0,H,4).cut(solid(3.2,H,5)).clean()
whole=body.fuse(rim).clean()
# Existing round interlocking C geometry, adapted to the curved D front.
cc=cq.importers.importStep(str(R/'source'/'base_CC.step')).val().translate((0,-24.2,0))
# Align to local decorated surface and trim rear against outer volume.
cc=cc.translate((0,-1.5,0)).cut(outer).clean()
print('cc',cc.isValid(),len(cc.Solids()),cc.Volume(),flush=True)
parts=[]
for name,s,col in [('cream_body_inverted_clip',body,'#f2e4cd'),('black_top_layers',rim,'#242424'),('black_glue_CC',cc,'#242424')]:
 assert s.isValid() and len(s.Solids())==1,(name,s.isValid(),len(s.Solids()))
 cq.exporters.export(s,str(O/(name+'.step')));cq.exporters.export(s,str(O/(name+'.stl')),tolerance=.1,angularTolerance=.25)
 parts.append(dict(name=name,file='parts/'+name+'.stl',color=col,volume_mm3=s.Volume()))
for name,s in [('whole_bowl_AMS',whole),('clip_fit_coupon',clip())]:
 cq.exporters.export(s,str(O/(name+'.step')));cq.exporters.export(s,str(O/(name+'.stl')),tolerance=.1,angularTolerance=.25)
a=cq.Assembly(name='chanel_D_bowl')
for p,s in zip(parts,[body,rim,cc]):
 c=p['color'];a.add(s,name=p['name'],color=cq.Color(*[int(c[i:i+2],16)/255 for i in (1,3,5)]))
a.save(str(R/'chanel_bowl_assembly.step'))
(R/'manifest.json').write_text(json.dumps(parts,indent=2))
(R/'parameters.json').write_text(json.dumps(dict(width=160,depth=145,height=85,clip_length=70,clip_height=30,clip_width=8.5,clip_gap_provisional=3,clip_bar_at_z=0,wall=3.2,base=4,top_black_start_z=81),indent=2))
print('done',flush=True)
flat=cc.rotate((0,0,0),(1,0,0),90); b=flat.BoundingBox();flat=flat.translate((-(b.xmin+b.xmax)/2,-(b.ymin+b.ymax)/2,-b.zmin))
cq.exporters.export(flat,str(O/'black_glue_CC_print_flat.step'));cq.exporters.export(flat,str(O/'black_glue_CC_print_flat.stl'),tolerance=.1,angularTolerance=.25)
# Requires trimesh; removes zero-area tessellation triangles from the small CC parts.
exec((R/'finalize_meshes.py').read_text())
