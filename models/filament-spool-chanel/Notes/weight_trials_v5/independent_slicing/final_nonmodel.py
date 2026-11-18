from pathlib import Path
import json,re,math,collections
D=Path('/tmp/chanel_100g');out={}
for part in ['wide','narrow']:
 dd=D/('original_lower_skin04_'+part+'_low');tot=collections.Counter();role=''
 for l in open(dd/'plate_1.gcode'):
  if l.startswith('; FEATURE: '):role=l.strip()[11:]
  if re.match(r'^G[123] ',l) and re.search(r' [XY]',l):
   e=re.search(r' E([-+.0-9]+)',l)
   if e and float(e[1])>0:tot[role]+=float(e[1])*math.pi*(1.75/2)**2*1.27/1000
 total=json.load(open(dd/'result.json'))['sliced_plates'][0]['filaments'][0]['total_used_g'];support=sum(v for k,v in tot.items() if k.startswith('Support'));out[part]={'total_g':total,'support_estimate_g':support,'total_minus_support_g':total-support,'extrusion_role_estimates_g':dict(tot)}
out['combined_total_g']=sum(out[p]['total_g'] for p in ['wide','narrow']);out['combined_support_g']=sum(out[p]['support_estimate_g'] for p in ['wide','narrow']);out['combined_minus_support_g']=out['combined_total_g']-out['combined_support_g'];out['note']='Approximate support estimate from Gcode role extrusion. Total minus support still may include custom/purge paths and is not a measured finished-part weight. Machine purging/calibration waste may not be fully represented by slicer totals.'
(D/'final_candidate_support_breakdown.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
