import json,math,re,hashlib
from pathlib import Path
D=Path(__file__).parent;out={}
for stage in ['short_v2','long_v2','long_wide_v3']:
 sd=D/('slice_'+stage)
 if not (sd/'narrow/result.json').exists(): continue
 step=Path('/tmp/chanel_parking_100g')/stage/'CHANEL_PARKING_A_100G_WINDOWS_TRIAL.step'
 row={'step_sha256':hashlib.sha256(step.read_bytes()).hexdigest(),'step_bytes':step.stat().st_size,'mesh':json.loads((sd/'mesh_reports.json').read_text()),'parts':{}}
 for part in ['wide','narrow']:
  res=json.loads((sd/part/'result.json').read_text());plate=res['sliced_plates'][0];e={};zs={};z=None;feature=''
  for line in (sd/part/'plate_1.gcode').open():
   if line.startswith('; Z_HEIGHT:'):z=float(line.split(':')[1])
   if line.startswith('; FEATURE:'):feature=line.split(':')[1].strip()
   if z is None or feature not in ['Support','Support interface']:continue
   if re.match(r'G[123] ',line) and re.search('[XY]',line):
    m=re.search(r' E(-?[\d.]+)',line)
    if m and float(m[1])>0:e[feature]=e.get(feature,0)+float(m[1])*math.pi*.875**2*1.27/1000;zs[z]=True
  row['parts'][part]={'g':plate['filaments'][0]['total_used_g'],'return_code':res['return_code'],'warning':plate['warning_message'],'support_deposition_g':e,'support_height_range':[min(zs),max(zs)] if zs else None,'seconds':plate['total_predication']}
 row['total_g']=sum(p['g'] for p in row['parts'].values());row['saving_g']=119.1411018371582-row['total_g'];out[stage]=row
(D/'FINAL_RESULTS.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
