from pathlib import Path
import zipfile,xml.etree.ElementTree as E,numpy as np,json,hashlib
D=Path('/tmp/chanel_repaired_dual');p=D/'output/CHANEL_105g_REPAIRED_MESH_TWO_PLATES.3mf';j=json.loads((D/'output/result.json').read_text());rows=[]
for s in j['sliced_plates']:rows.append({'plate':s['id'],'objects':s['objects'],'grams':s['filaments'][0]['total_used_g'],'warning':s.get('warning_message')})
assert j['return_code']==0 and len(rows)==2 and all(len(x['objects'])==1 for x in rows)
ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'};meshes=[]
with zipfile.ZipFile(p) as z:
 for n in z.namelist():
  if n.startswith('3D/Objects/') and n.endswith('.model'):
   r=E.fromstring(z.read(n))
   for ob in r.findall('.//m:object',ns):
    m=ob.find('m:mesh',ns)
    if m is None:continue
    v=np.array([[float(e.get(k)) for k in ['x','y','z']] for e in m.find('m:vertices',ns)]);f=np.array([[int(e.get(k)) for k in ['v1','v2','v3']] for e in m.find('m:triangles',ns)]);ed=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);_,c=np.unique(ed,axis=0,return_counts=True);row={'file':n,'vertices':len(v),'faces':len(f),'boundary':int(sum(c==1)),'nonmanifold':int(sum(c>2))};assert row['boundary']==0 and row['nonmanifold']==0;meshes.append(row)
assert len(meshes)==2
report={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'plates':rows,'meshes':meshes,'total_g':sum(x['grams'] for x in rows),'source_step_unchanged':True,'not_parametric_step':True,'warning_unresolved':True};(D/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
