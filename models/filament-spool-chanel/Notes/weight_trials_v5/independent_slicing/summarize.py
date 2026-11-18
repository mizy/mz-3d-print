from pathlib import Path
import json,re,math,collections,hashlib
D=Path('/tmp/chanel_100g');out={'source':'v5 defaults; wide exact user autosave mesh, narrow from v5 native BRep independently tessellated (.01,.1 CadQuery relative deflection)','slicer':'BambuStudio 02.09.01.70','material':'User current Jucoole PETG+; density1.27 g/cm3, diameter1.75mm','constant_settings':{'layer_height':.2,'walls':2,'bottom_shell_layers':3,'bottom_shell_thickness':0,'ensure_vertical_shell_thickness':'enabled','minimum_sparse_infill_area':15},'variants':{}}
for n in ['baseline','top4','top3','top3_sparse5']:
 row={}
 for part in ['wide','narrow']:
  dd=Path('/tmp/chanel_shell_ab/on') if n=='baseline' and part=='wide' else D/(part+'_'+n);r=json.load(open(dd/'result.json'));g=dd/'plate_1.gcode';role='';tot=collections.Counter()
  for l in g.open():
   if l.startswith('; FEATURE: '):role=l.strip()[11:]
   if re.match(r'^G[123] ',l) and re.search(r' [XY]',l):
    e=re.search(r' E([-+.0-9]+)',l)
    if e and float(e[1])>0:tot[role]+=float(e[1])*math.pi*(1.75/2)**2*1.27/1000
  row[part]={'total_g':r['sliced_plates'][0]['filaments'][0]['total_used_g'],'slicer_return_code':r['return_code'],'role_g':dict(tot),'gcode_sha256':hashlib.sha256(g.read_bytes()).hexdigest()}
 row['combined_total_g']=sum(row[p]['total_g'] for p in ['wide','narrow']);out['variants'][n]=row
out['limitations']=['Slicer estimates, not weighed prints.','Not load-tested; lowering infill/layers does not establish safe load.','No UI or default project changes.','Temporary 3MF is internal test container only, not a user deliverable.']
(D/'paired_settings_results.json').write_text(json.dumps(out,indent=2));print({k:v['combined_total_g'] for k,v in out['variants'].items()})
