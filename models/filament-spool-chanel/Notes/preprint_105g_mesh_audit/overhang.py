from pathlib import Path
import re,json,math,collections
D=Path('/tmp/chanel_step_openedge_audit');out={}
for i in [0,1]:
 x=y=z=0.;feature='';groups=collections.defaultdict(list)
 for line in (D/f'studio_slice_{i}/plate_1.gcode').read_text().splitlines():
  if line.startswith('; FEATURE:'):feature=line.split(':',1)[1].strip()
  if line.startswith('; Z_HEIGHT:'):z=float(line.split(':')[1])
  if re.match(r'^G[123] ',line):
   vals={a:float(b) for a,b in re.findall(r'([XYE])(-?[0-9.]+)',line)};x=vals.get('X',x);y=vals.get('Y',y)
   if vals.get('E',0)>0 and feature in ['Overhang wall','Bridge','Support','Support interface']:groups[(feature,round(z,3))].append([x-120.424375,y-126.75143])
 rows=[]
 for (f,z),vs in groups.items():
  rs=[math.hypot(*a) for a in vs];rows.append({'feature':f,'z':z,'points':len(vs),'radius_min':min(rs),'radius_max':max(rs)})
 out[str(i)]=rows
 print('HALF',i)
 for r in rows:
  if r['feature']=='Overhang wall':print(r)
(D/'overhang_paths.json').write_text(json.dumps(out,indent=2))
