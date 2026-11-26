"""V18 A leaf vein, analytic BRep Boolean, dimensions in mm. FreeCAD Python module required."""
import argparse,hashlib,json,math,re
from pathlib import Path
import FreeCAD as A, Part, Import
V=A.Vector
DEFAULT=dict(window_y=[22.0,204.0],window_z=[18.0,65.0],
 lower=[[24,50,22,40,.52],[55,81,20,42,.56],[86,114,19,41,.45],[119,146,20,42,.48],[151,177,19,40,.52],[182,202,23,41,.37]],
 upper=[[25,50,42.5,62,.58],[54,80,44.5,63,.55],[84,113,43.5,65,.46],[118,145,44.5,64,.51],[150,177,42.5,62,.53],[181,202,43.5,64,.41]],
 root_blend_mm=1.0,apex_blend_mm=.58,width_factor=.83)
BASE_SHA='4fab31b0c8a9abac78bae99e9d4ee4634a2a545abd49272ac800f2d9df6a380b'
p=argparse.ArgumentParser();p.add_argument('base',type=Path);p.add_argument('out',type=Path);p.add_argument('--config',type=Path);args=p.parse_args()
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
assert sha(args.base)==BASE_SHA,"Use pinned V18 single drawer STEP"
f0=Part.read(str(args.base));assert f0.isValid() and len(f0.Solids)==1
base=f0.Solids[0]; b=base.optimalBoundingBox(False,False)
assert abs(b.XLength-144.10)<.002 and abs(b.YLength-230)<.002 and abs(b.ZLength-86)<.002,(b.XLength,b.YLength,b.ZLength)
cfg=DEFAULT if not args.config else json.loads(args.config.read_text());out=args.out;out.mkdir(parents=True,exist_ok=False)
def L(p1,p2):return Part.makeLine(p1,p2)
def P(v):return V(-.45,v[0]+b.YMin,v[1]+b.ZMin)
def wire(rec):
 st,ed,low,top,u=rec
 center=(st+ed)/2.;ph=(ed-st)*cfg.get("width_factor",1.0)/2.
 st,ed=center-ph,center+ph;w=ed-st;h=top-low
 # Each aperture splits from the central oblique spine; varied skew, shoulders and narrow apex.
 a=[(st+.20*w,low),(st+.72*w,low+.12*h),(ed,low+.37*h),
    (st+u*w,top),(st+.10*w,low+.54*h),(st,low+.26*h)]
 a=list(map(P,a)); edges=[]; rounded=[]
 for j,z in enumerate(a):
  d=cfg['apex_blend_mm'] if j==3 else cfg['root_blend_mm']
  u=z-a[j-1];u.normalize();v=a[(j+1)%len(a)]-z;v.normalize()
  s=z-u*d;e=z+v*d
  bz=Part.BezierCurve();bz.setPoles([s,z,e])
  rounded.append((s,e,bz.toShape()))
 for i,(s,e,q) in enumerate(rounded):
  edges.extend((q,L(e,rounded[(i+1)%len(rounded)][0])))
 return Part.Wire(edges)
data=[];faces=[];cut=[]
for band in ('lower','upper'):
 for rec in cfg[band]:
  profile=wire(rec);f=Part.Face(profile);faces.append(f)
  assert f.isValid() and f.Area>60
  q=f.extrude(V(2.4,0,0));r=q.translated(V(b.XMax-.95,0,0));cut.extend((q,r))
  assert b.XMax>140
  pre=[base.common(v).Volume for v in (q,r)]
  assert min(pre)>20 and abs(pre[0]-pre[1])<.10 and abs(pre[0]/f.Area-.96)<.01,(rec,pre,f.Area)
  for v in (q,r):
   assert v.BoundBox.YMin>=b.YMin+cfg['window_y'][0]-.0002 and v.BoundBox.YMax<=b.YMin+cfg['window_y'][1]+.0002
   assert v.BoundBox.ZMin>=b.ZMin+cfg['window_z'][0]-.0002 and v.BoundBox.ZMax<=b.ZMin+cfg['window_z'][1]+.0002
  data.append(dict(band=band,coordinates_y0_y1_z0_z1_and_skew=rec,area_mm2=f.Area,removed_each_side_mm3=pre))
h=base.cut(cut).removeSplitter()
box=h.optimalBoundingBox(False,False)
assert h.isValid() and len(h.Solids)==1
def bb(a):return [getattr(a,k) for k in ('XMin','XMax','YMin','YMax','ZMin','ZMax')]
assert max(abs(u-v) for u,v in zip(bb(box),bb(b)))<.002
diff=base.Volume-h.Volume-sum(sum(o['removed_each_side_mm3']) for o in data)
print('volume and diff',base.Volume,h.Volume,diff,flush=True)
assert abs(diff)<.25,diff
min_gap=min(a.distToShape(b)[0] for i,a in enumerate(faces) for b in faces[:i]);assert min_gap>2.2,min_gap
area=sum(f.Area for f in faces)
coverage=area/(math.prod(s[1]-s[0] for s in (cfg['window_y'],cfg['window_z'])))
if not args.config:assert .30<=coverage<=.35,coverage
# Exact protected regions: front fascia/handle, rear-corner keepers, floor/rail and entire upper rim.
changed=[]
for label,y0,z0,y1,z1 in (('front_Y0_22',-1,-1,22,87),('rear_Y204_230',204,-1,231,87),
 ('bottom_Z0_18',-1,-1,231,18),('top_Z65_86',-1,65,231,87)):
 test=Part.makeBox(146,y1-y0,z1-z0,V(-1,b.YMin+y0,b.ZMin+z0))
 diff=abs(h.common(test).Volume-base.common(test).Volume)
 assert diff<.001,(label,diff)
 changed.append((label,diff))
f=out/'04_Drawer_A_Leaf_Vein.step'
doc=A.newDocument('V18_Leaf_Vein')
try:
 ob=doc.addObject('Part::Feature','V18_Drawer_Leaf_Vein');ob.Label='V18 Drawer A Leaf Vein';ob.Shape=h
 doc.recompute();Import.export([ob],str(f))
finally:A.closeDocument(doc.Name)
def read_level():
 x=Part.read(str(f));return x,x.optimalBoundingBox(False,False)
x,xx=read_level()
if abs(xx.XLength/box.XLength-1000)<.002:
 t,n=re.subn(rb'(?i)SI_UNIT\s*\(\s*\$\s*,\s*\.METRE\.\s*\)',b'SI_UNIT(.MILLI.,.METRE.)',f.read_bytes());assert n
 f.write_bytes(t);x,xx=read_level()
assert len(x.Solids)==1 and x.isValid() and max(abs(u-v) for u,v in zip(bb(xx),bb(box)))<.002
assert abs(x.Volume-h.Volume)<.12,(x.Volume,h.Volume)
report=dict(seed_sha256=BASE_SHA,step_sha256=sha(f),openings_per_side=len(data),window_mm=[cfg['window_y'],cfg['window_z']],
 profile_opening_area_per_side_mm2=area,area_fraction_of_design_window=coverage,min_exact_ligament_between_cutouts_mm=min_gap,
 existing_side_t_mm=.96,body_size_mm=[box.XLength,box.YLength,box.ZLength],solid_readback_count=len(x.Solids),
 removed_mm3=base.Volume-h.Volume,base_mm3=base.Volume,new_mm3=h.Volume,
 volume_fraction_removed=(base.Volume-h.Volume)/base.Volume,petg_solid_equiv_grams_saved=(base.Volume-h.Volume)*.00127,
 preserved_regions_volume_difference_mm3=changed,apertures=data)
(out/'Leaf_Vein_Validation.json').write_text(json.dumps(report,indent=2)+'\n')
(out/'Leaf_Vein_Parameters.json').write_text(json.dumps(cfg,indent=2)+'\n')
paths=[]
for ff in faces:
 pnts=[]
 for e in ff.OuterWire.OrderedEdges:
  pnts += e.discretize(9)
 paths.append('M '+' L '.join(f'{v.y-b.YMin:.3f},{86-v.z+b.ZMin:.3f}' for v in pnts)+' Z')
(out/'Leaf_Vein_Side_Profiles.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 230 86"><rect width="230" height="86" fill="#217466" rx="1.4"/><path d="'+' '.join(paths)+'" fill="#e6f0e7"/></svg>\n')
print(f,flush=True);print(json.dumps({k:v for k,v in report.items() if k!='apertures'}),flush=True)
