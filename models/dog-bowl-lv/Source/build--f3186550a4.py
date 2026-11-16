"""30mm low bowl with approved two-row original-vector engraving; mm. Only clip envelope measured by owner.
D outline is estimated; clip neck, slots and engagement remain assumptions.
Run with Python, cadquery, svgpathtools, trimesh installed.
"""
import cadquery as cq, math, json
from pathlib import Path
from svgpathtools import svg2paths
R=Path(__file__).parent; O=R/'parts';O.mkdir(exist_ok=True)
WIDTH=160.; REAR=55.; FRONT_CENTER=-10.; HEIGHT=30.; WALL=3.2; BASE=4.; RIM_HEIGHT=2.
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
# Exact third-party cubic Bezier curves, no outline simplification.
from vector_shapes import symbol
motifs={k:symbol(k,7,1.6) for k in ['LV','diamond','pointed','circle']}
lv=symbol('LV',18,2.5)
cutters=[];pattern=[]
layout=json.loads((R/'approved_layout.json').read_text())
for p in layout['motifs']:
 x=p['x_mm']-80;angle=math.degrees(math.asin(x/80));z=HEIGHT-p['from_top_mm']
 c=motifs[p['type']].translate((0,-79.2,z)).rotate((0,0,0),(0,0,1),angle).translate((0,FRONT_CENTER,0))
 cutters.append(c);pattern.append(dict(surface='front',angle=angle,z=z,type=p['type'],design_x=x))
# Fill the former front-to-side transition gap and extend both flat sides.
# Original front twelve positions stay unchanged.
for side in [-1,1]:
 for row,z in enumerate([9,21]):
  k=['pointed','circle','diamond','LV'][row+(0 if side<0 else 2)]
  angle=side*77
  cutters.append(motifs[k].translate((0,-79.2,z)).rotate((0,0,0),(0,0,1),angle).translate((0,FRONT_CENTER,0)))
  pattern.append(dict(surface='transition',angle=angle,z=z,type=k))
  for j,y in enumerate([-5,11,27,43] if row==0 else [-1,15,31,43]):
   k=['LV','diamond','pointed','circle'][(row+j+(0 if side<0 else 2))%4]
   cutters.append(motifs[k].translate((0,-79.2,z)).rotate((0,0,0),(0,0,1),side*90).translate((0,y,0)))
   pattern.append(dict(surface='side',side=side,y=y,z=z,type=k))
(R/'pattern_layout.json').write_text(json.dumps({'source':'third-party AI, original Bezier curves','nominal_recess_mm':.8,'height_mm':7,'placements':pattern},indent=2))
print('cutting',len(cutters),flush=True)
for c in cutters:bowl=bowl.cut(c).clean()
# Lower rear vertical INVERTED T clip: X length70, Z height30, Y width8.5.
# Neck/bar proportions and mating gaps are estimates, not measured.
def clip(z=0):
 q=box(CLIP_WIDTH,CLIP_DEPTH,CLIP_BAR,0,CLIP_DEPTH/2,z).fuse(box(CLIP_NECK,CLIP_DEPTH,CLIP_HEIGHT-CLIP_BAR+1,0,CLIP_DEPTH/2,z+CLIP_BAR-1))
 return q.clean()
cp=clip(CLIP_Z).translate((0,REAR+CLIP_GAP,0))
# Root overlap guarantees a connected lower rear mount; not a certified load path.
root=box(CLIP_NECK,CLIP_GAP+3,CLIP_HEIGHT,0,REAR+(CLIP_GAP-1)/2,CLIP_Z)
combined=bowl.fuse(cp).fuse(root).clean()
bottom=combined.intersect(box(400,400,2,0,0,0)).clean()
body=combined.intersect(box(400,400,26,0,0,2)).clean()
rim=combined.intersect(box(400,400,2,0,0,28)).clean()
# Flat-backed logo stays separate with a shallow glue gap.
logo=lv.translate((0,-90.1,15)).clean() # flat-backed glue emblem; 0.1mm nominal center glue gap
parts=[]
def export(name,s,color):
 assert s.isValid(),name
 assert len(s.Solids())==1,(name,len(s.Solids()))
 cq.exporters.export(s,str(O/(name+'.step')));cq.exporters.export(s,str(O/(name+'.stl')),tolerance=.02,angularTolerance=.08)
 parts.append(dict(name=name,file='parts/'+name+'.stl',color=color,volume_mm3=s.Volume()))
export('ivory_bottom_z0_2',bottom,IVORY);export('blue_middle_z2_28',body,BLUE);export('ivory_top_z28_30',rim,IVORY);export('ivory_glue_logo',logo,IVORY)
cq.exporters.export(combined,str(O/'whole_bowl_AMS.stl'),tolerance=.02,angularTolerance=.08)
cq.exporters.export(combined,str(O/'whole_bowl_AMS.step'))
test=clip();cq.exporters.export(test,str(O/'clip_fit_coupon.stl'));cq.exporters.export(test,str(O/'clip_fit_coupon.step'))
a=cq.Assembly(name='lv_vector_two_row_low_bowl')
for p,s in zip(parts,[bottom,body,rim,logo]):
 c=p['color'];a.add(s,name=p['name'],color=cq.Color(*[int(c[i:i+2],16)/255 for i in (1,3,5)]))
a.save(str(R/'bowl_30mm_assembly.step'))
(R/'manifest.json').write_text(json.dumps(parts,indent=2))
print('done',flush=True)

flat=logo.rotate((0,0,0),(1,0,0),90);bb=flat.BoundingBox();flat=flat.translate((-(bb.xmin+bb.xmax)/2,-(bb.ymin+bb.ymax)/2,-bb.zmin))
for ext in ['step','stl']:cq.exporters.export(flat,str(O/('ivory_logo_print_flat.'+ext)),tolerance=.02,angularTolerance=.08)
