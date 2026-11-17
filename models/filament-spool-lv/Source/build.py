import cadquery as cq, math,json
from pathlib import Path
from svgpathtools import svg2paths
R=Path(__file__).parent
# Provisional original bayonet interface: NOT a verified Bambu refill interface.
D=200; WIDTH=67; CORE_R=40; PLATE=1.0

def ring(ro,ri,h,z=0):return cq.Workplane('XY').circle(ro).circle(ri).extrude(h).translate((0,0,z)).val()
def box(x,y,z,cx=0,cy=0,cz=0):return cq.Workplane('XY').box(x,y,z,centered=(True,True,False)).translate((cx,cy,cz)).val()
paths=svg2paths(str(R/'LV_Monogram.svg'))[0];ps=[]
for seg in paths[0]:
 for j in range(2):
  p=seg.point(j/2);ps.append(((p.real-840)/1679*12,(832-p.imag)/1664*12))
ps=[p for i,p in enumerate(ps) if i==0 or math.dist(p,ps[i-1])>.005]
lv=cq.Workplane('XY').polyline(ps).close().extrude(3).translate((0,0,-.5)).val()
# stencil bridges connect potential islands to plate, 1.2mm wide
lv=lv.cut(box(18,1.2,4,0,0,-1))
def petal():return cq.Workplane('XY').moveTo(0,1).threePointArc((1.7,2.8),(0,4.5)).threePointArc((-1.7,2.8),(0,1)).close().extrude(3).translate((0,0,-.5)).val()
flower=[petal().rotate((0,0,0),(0,0,1),a) for a in [0,90,180,270]]
cut=[]
for rad,n in [(50,16),(67,24),(85,28)]:
 for i in range(n):
  a=2*math.pi*(i+.5)/n;x=rad*math.cos(a);y=rad*math.sin(a)
  if min(abs(x),abs(y))<7:continue
  motifs=[lv] if i%2==0 else flower
  for m in motifs:cut.append(m.translate((x,y,0)))
plate=ring(100,38.4,PLATE)
# perimeter 3mm band rises only 1mm above the skin; four shallow ribs
plate=plate.fuse(ring(100,97,1,1))
for a in [0,90,180,270]:plate=plate.fuse(box(60,2.4,1,68,0,1).rotate((0,0,0),(0,0,1),a))
# Four paired 2.4mm filament retaining holes per flange, inside rolling rim.
for angle in [45,135,225,315]:
 a=math.radians(angle)
 for offset in [-2.8,2.8]:
  x=93*math.cos(a)-offset*math.sin(a);y=93*math.sin(a)+offset*math.cos(a)
  cut.append(cq.Workplane('XY').center(x,y).circle(1.2).extrude(4).translate((0,0,-.5)).val())
plate=plate.clean()
print('plate solids',len(plate.Solids()),'volume',plate.Volume(),flush=True)
# female wide half: 32.5mm body above plate, with 3 L-shaped entry slots
female=plate.fuse(ring(40,38.4,32.5,1))
# Male narrow half has stepped inner spigot. Mating clearance 0.30mm radial.
male=plate.fuse(ring(40,38.4,31.5,1)).fuse(ring(40,36.5,1.5,31)).fuse(ring(38.1,36.5,7,32.5))
# locked overlap 7mm; assembled plate inner separation 65mm => overall67
for a in [0,120,240]:
 tab=box(3.0,5,1.6,38.3,0,35.2).rotate((0,0,0),(0,0,1),a)
 male=male.fuse(tab)
 # female half local z: tab at locked z29.8 ; axial entry open at top
 entry=box(6,5.7,6,39,0,28).rotate((0,0,0),(0,0,1),a)
 # clearance twist sector path approximated by swept arc cut using ring wedge
 pts=[(0,0)]+[(44*math.cos(math.radians(t)),44*math.sin(math.radians(t))) for t in range(-5,26,2)]+[(0,0)]
 wedge=cq.Workplane('XY').polyline(pts).close().extrude(2.2).translate((0,0,30.0)).val().intersect(ring(43,37,2.2,30.0)).rotate((0,0,0),(0,0,1),a)
 female=female.cut(entry,wedge)
parts={}
for name,s in [('A_wide_PROTOTYPE',female),('A_narrow_PROTOTYPE',male)]:
 print('cutting',name,flush=True)
 s=s.cut(*cut).clean();assert s.isValid(),name;assert len(s.Solids())==1,(name,len(s.Solids()))
 cq.exporters.export(s,str(R/(name+'.step')));cq.exporters.export(s,str(R/(name+'.stl')),tolerance=.05,angularTolerance=.12)
 b=s.BoundingBox()
 if 'wide' in name:female=s
 else:male=s
 parts[name]={'volume_mm3':s.Volume(),'solid_count':len(s.Solids()),'valid_brep':s.isValid(),'bbox_mm':[b.xlen,b.ylen,b.zlen]}
# assembly transform of narrow part: outside faces z0 and67. male tabs rotate into female slots
assembled=male.rotate((0,0,0),(1,0,0),180).translate((0,0,67)).rotate((0,0,0),(0,0,1),12)
inter=female.intersect(assembled)
parts['assembly']={'overlap_mm3':inter.Volume(),'nominal_width_mm':67,'estimated_solid_mass_g_at_1_37':(male.Volume()+female.Volume())*.00137,'warning':'Not slicer mass. Provisional core diameter and original lock, no official refill compatibility validation. No locking detent yet; do not load filament.'}
a=cq.Assembly();a.add(female,name='wide');a.add(assembled,name='narrow');a.save(str(R/'A_assembly_PROTOTYPE.step'))
(R/'validation.json').write_text(json.dumps(parts,indent=2))
print(json.dumps(parts,indent=2),flush=True)
