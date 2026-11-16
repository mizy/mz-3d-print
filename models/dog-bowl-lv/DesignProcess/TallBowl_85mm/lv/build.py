"""Photo-derived high bowl concept; mm. Only clip envelope measured by owner.
D outline is estimated; clip neck, slots and engagement remain assumptions.
Run with Python, cadquery, svgpathtools, trimesh installed.
"""
import cadquery as cq, math, json
from pathlib import Path
from svgpathtools import svg2paths
R=Path(__file__).parent; O=R/'parts';O.mkdir(exist_ok=True)
WIDTH=160.; REAR=55.; FRONT_CENTER=-10.; HEIGHT=85.; WALL=3.2; BASE=4.; RIM_HEIGHT=6.
CLIP_WIDTH=70.; CLIP_HEIGHT=30.; CLIP_DEPTH=8.5; CLIP_NECK=18.; CLIP_BAR=8.5; CLIP_Z=0.; CLIP_GAP=3.
BLUE='#afcddd';IVORY='#f2e0c4'
def outline(off=0,z=0):
 r=WIDTH/2-off;back=REAR-off; corner=8.
 return cq.Workplane('XY',origin=(0,0,z)).moveTo(-r,FRONT_CENTER).lineTo(-r,back-corner).radiusArc((-r+corner,back),corner).lineTo(r-corner,back).radiusArc((r,back-corner),corner).lineTo(r,FRONT_CENTER).threePointArc((0,FRONT_CENTER-r),(-r,FRONT_CENTER)).close().val()
def solid(off,z,h):return cq.Solid.extrudeLinear(outline(off,z),[],cq.Vector(0,0,h))
def box(w,d,h,x,y,z):return cq.Workplane('XY').box(w,d,h,centered=(True,True,False)).translate((x,y,z)).val()
outer=solid(0,0,HEIGHT)
inner=solid(WALL,BASE,HEIGHT)
try:inner=cq.Workplane(obj=inner).edges('<Z').fillet(5).val()
except:pass
bowl=outer.cut(inner)
# True recessed motifs, repeated tangent to curved front and flat side panels.
def disk(r):return cq.Workplane('XZ').circle(r).extrude(2).val()
def leaf(r=5):return cq.Workplane('XZ').moveTo(0,0).spline([(1.65,r*.48),(1.25,r*.78),(0,r)],includeCurrent=True).spline([(-1.25,r*.78),(-1.65,r*.48),(0,0)],includeCurrent=True).close().extrude(2).val()
f=disk(.8)
for angle in [0,90,180,270]:f=f.fuse(leaf().rotate((0,0,0),(0,1,0),angle))
f=f.cut(disk(.8))
pts=[]
for a in range(4):
 for j in range(20):
  t=j/20;u=1-t;x=3*u*u*t*1.2+3*u*t*t*3.2+t**3*6.5;z=u**3*6.5+3*u*u*t*3.2+3*u*t*t*1.2
  ang=math.radians(a*90);pts.append((x*math.cos(ang)+z*math.sin(ang),-x*math.sin(ang)+z*math.cos(ang)))
d=cq.Workplane('XZ').polyline(pts).close().extrude(2).val().cut(f.scale(.85)).fuse(disk(.65))
# Actual LV vector for separate glue-on emblem and small engraved repeating letters.
paths=svg2paths(str(R/'LV_Monogram.svg'))[0];ps=[]
for seg in paths[0]:
 for j in range(6):
  p=seg.point(j/6);ps.append(((p.real-840)/1679*24,(832-p.imag)/1664*24))
ps=[p for i,p in enumerate(ps) if i==0 or math.dist(p,ps[i-1])>.01]
lv=cq.Workplane('XZ').polyline(ps).close().extrude(2.5).val()
cutters=[]
for row,z in enumerate([18,39,60]):
 for k in range(9):
  angle=-80+k*20+(0 if row%2==0 else 10)
  if angle>85 or (abs(angle)<15 and row==1):continue
  mot=[f,d,f,lv.scale(.45)][(k+row)%4]
  # 0.9 recess at tangent center; remains <1.2 deep across motif.
  c=mot.translate((0,-79.1,z)).rotate((0,0,0),(0,0,1),angle).translate((0,FRONT_CENTER,0));cutters.append(c)
 for side in [-1,1]:
  for j,y in enumerate([4,29]):
   mot=[f,d][(j+row)%2];c=mot.translate((0,-79.1,z)).rotate((0,0,0),(0,0,1),side*90).translate((0,y,0));cutters.append(c)
print('cutting',len(cutters),flush=True);bowl=bowl.cut(*cutters).clean()
# Lower rear vertical INVERTED T clip: X length70, Z height30, Y width8.5.
# Neck/bar proportions and mating gaps are estimates, not measured.
def clip(z=0):
 q=box(CLIP_WIDTH,CLIP_DEPTH,CLIP_BAR,0,CLIP_DEPTH/2,z).fuse(box(CLIP_NECK,CLIP_DEPTH,CLIP_HEIGHT-CLIP_BAR+1,0,CLIP_DEPTH/2,z+CLIP_BAR-1))
 return q.clean()
cp=clip(CLIP_Z).translate((0,REAR+CLIP_GAP,0))
# Root overlap guarantees a connected lower rear mount; not a certified load path.
root=box(CLIP_NECK,CLIP_GAP+3,CLIP_HEIGHT-CLIP_BAR,0,REAR+(CLIP_GAP-1)/2,CLIP_Z)
body=bowl.intersect(box(400,400,HEIGHT-RIM_HEIGHT,0,0,0)).fuse(cp).fuse(root).clean()
rim=bowl.intersect(box(400,400,RIM_HEIGHT,0,0,HEIGHT-RIM_HEIGHT)).clean()
combined=body.fuse(rim).clean()
# Flat-backed logo stays separate with a shallow glue gap.
logo=lv.translate((0,-90.1,39)).clean() # flat-backed glue emblem; 0.1mm nominal center glue gap
parts=[]
def export(name,s,color):
 assert s.isValid(),name
 assert len(s.Solids())==1,(name,len(s.Solids()))
 cq.exporters.export(s,str(O/(name+'.step')));cq.exporters.export(s,str(O/(name+'.stl')),tolerance=.04,angularTolerance=.1)
 parts.append(dict(name=name,file='parts/'+name+'.stl',color=color,volume_mm3=s.Volume()))
export('blue_body_with_inverted_T_clip',body,BLUE);export('ivory_top_layers',rim,IVORY);export('ivory_glue_logo',logo,IVORY)
cq.exporters.export(combined,str(O/'whole_bowl_AMS.stl'),tolerance=.04,angularTolerance=.1)
cq.exporters.export(combined,str(O/'whole_bowl_AMS.step'))
test=clip();cq.exporters.export(test,str(O/'clip_fit_coupon.stl'));cq.exporters.export(test,str(O/'clip_fit_coupon.step'))
a=cq.Assembly(name='photo_based_high_bowl')
for p,s in zip(parts,[body,rim,logo]):
 c=p['color'];a.add(s,name=p['name'],color=cq.Color(*[int(c[i:i+2],16)/255 for i in (1,3,5)]))
a.save(str(R/'high_bowl_assembly.step'))
(R/'manifest.json').write_text(json.dumps(parts,indent=2))
print('done',flush=True)
