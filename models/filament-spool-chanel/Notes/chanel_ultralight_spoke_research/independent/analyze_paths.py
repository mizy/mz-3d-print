import json,re,math,sys,collections
from pathlib import Path
D=Path(__file__).parent
stage=sys.argv[1];out={}
for part in ['wide','narrow']:
 p=D/('slice_'+stage)/part
 if not (p/'result.json').exists():continue
 result=json.loads((p/'result.json').read_text());plate=result['sliced_plates'][0]
 feat='';z=None;data={};x=y=0.
 for line in (p/'plate_1.gcode').open():
  if line.startswith('; FEATURE:'):feat=line.split(':')[1].strip()
  if line.startswith('; Z_HEIGHT:'):z=float(line.split(':')[1])
  code=line.split(';')[0].strip()
  if not re.match(r'G[0123] ',code):continue
  v={k:float(n) for k,n in re.findall(r'([XYEIJ])(-?(?:\d+(?:\.\d*)?|\.\d+))',code)}
  xx,yy=v.get('X',x),v.get('Y',y)
  if z is not None and feat in ['Support','Support interface','Bridge','Overhang wall'] and v.get('E',0)>0 and any(k in v for k in ['X','Y','I','J']):
   a=data.setdefault(feat,{'g':0.,'segments':0,'by_z':{},'endpoint_radius_min':1e9,'endpoint_radius_max':0})
   mass=v['E']*math.pi*.875**2*1.27/1000;a['g']+=mass;a['segments']+=1;a['by_z'][str(z)]=a['by_z'].get(str(z),0)+mass
   for px,py in [(x,y),(xx,yy)]:
    r=math.hypot(px-120.424375,py-126.75143);a['endpoint_radius_min']=min(a['endpoint_radius_min'],r);a['endpoint_radius_max']=max(a['endpoint_radius_max'],r)
  x,y=xx,yy
 out[part]={'total_g':plate['filaments'][0]['total_used_g'],'returncode':result['return_code'],'warning':plate['warning_message'],'features':data}
(D/('paths_'+stage+'.json')).write_text(json.dumps(out,indent=2))
print(json.dumps({p:{'total_g':q['total_g'],'warning':q['warning'],'features':{f:{k:v for k,v in a.items() if k!='by_z'} for f,a in q['features'].items()}}for p,q in out.items()},indent=2))
