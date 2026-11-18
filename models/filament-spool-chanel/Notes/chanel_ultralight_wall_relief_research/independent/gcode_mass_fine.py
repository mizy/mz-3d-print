import re,math,json,collections
from pathlib import Path
out={}
for part in ('wide','narrow'):
 p=Path('/tmp/chanel_roof_review/slice_roof_auto')/part/'plate_1.gcode'
 x=y=0.;z=None;feature='Custom';mass=collections.defaultdict(float);byh=collections.defaultdict(float);byf=collections.defaultdict(float)
 for line in p.open():
  if line.startswith('; Z_HEIGHT:'):z=float(line.split(':')[1])
  if line.startswith('; FEATURE:'):feature=line.split(':')[1].strip()
  code=line.split(';')[0].strip();m=re.match(r'G([0123])\s',code)
  if not m:continue
  v={k:float(n) for k,n in re.findall(r'([XYEIJ])(-?(?:\d+(?:\.\d*)?|\.\d+))',code)};xx=v.get('X',x);yy=v.get('Y',y)
  if z is not None and feature!='Custom' and v.get('E',0)>0 and ('X'in v or 'Y'in v or 'I'in v):
   amount=v['E']*math.pi*(1.75/2)**2*1.27/1000
   byh[str(round(z,3))]+=amount;byf[feature]+=amount
   pts=[]
   if int(m[1]) in (2,3) and ('I'in v or 'J'in v):
    cx=x+v.get('I',0);cy=y+v.get('J',0);a=math.atan2(y-cy,x-cx);b=math.atan2(yy-cy,xx-cx);da=(b-a)%(2*math.pi)
    if int(m[1])==2:da= -((a-b)%(2*math.pi))
    rad=math.hypot(x-cx,y-cy);pts=[(cx+rad*math.cos(a+da*(i+.5)/20),cy+rad*math.sin(a+da*(i+.5)/20)) for i in range(20)]
   else:pts=[(x+(xx-x)*(i+.5)/20,y+(yy-y)*(i+.5)/20) for i in range(20)]
   for px,py in pts:
    r=math.hypot(px-120.424375,py-126.75143)
    region='rolling_ring_R95plus' if r>95 else ('flange_R44.5to95' if r>44.5 else ('outer_tube_R37plus' if r>37 else ('inner_tube_R26to34' if 26<r<34 else 'bridge_other')))
    band='0-3.6' if z<=3.6001 else '3.6-8' if z<=8.0001 else '8-20' if z<=20.0001 else '20-26' if z<=26.0001 else '26-top'
    mass[band+' | '+region]+=amount/20
  x,y=xx,yy
 out[part]={'total_deposition_g':sum(byh.values()),'by_height_region_g':dict(mass),'by_feature_g':dict(byf),'layer_mass_g':dict(byh)}
Path('/tmp/chanel_60g_review/gcode_mass_fine.json').write_text(json.dumps(out,indent=2))
for p,d in out.items():print(p,d['total_deposition_g'],json.dumps(d['by_height_region_g'],indent=2),d['by_feature_g'])
