from pathlib import Path
import zipfile,xml.etree.ElementTree as E,copy,re
D=Path('/tmp/chanel_repaired_dual')
with zipfile.ZipFile(D/'arranged/raw_export.3mf') as z:f={n:z.read(n) for n in z.namelist()}
s=f['3D/3dmodel.model'].decode();s=s.replace('objectid="4" p:UUID="00000004-b1ec-4553-aec9-835e5b724bb4" transform="1 0 0 0 1 0 0 0 1 120.424375 126.75143','objectid="4" p:UUID="00000004-b1ec-4553-aec9-835e5b724bb4" transform="1 0 0 0 1 0 0 0 1 427.624375 126.75143');f['3D/3dmodel.model']=s.encode()
r=E.fromstring(f['Metadata/model_settings.config']);p=r.find('plate');p2=copy.deepcopy(p);mis=p.findall('model_instance');p.remove(mis[1]);p2.remove(p2.findall('model_instance')[0]);p2.find("metadata[@key='plater_id']").set('value','2');p.find("metadata[@key='plater_name']").set('value','Wide mesh seam repaired');p2.find("metadata[@key='plater_name']").set('value','Narrow original mesh')
for e in p2.findall('metadata'):
 if e.get('value'):e.set('value',e.get('value').replace('_1.','_2.'))
r.insert(list(r).index(p)+1,p2);f['Metadata/model_settings.config']=E.tostring(r,encoding='utf-8',xml_declaration=True)
with zipfile.ZipFile(D/'manual.3mf','w',zipfile.ZIP_DEFLATED) as z:
 for n,b in f.items():z.writestr(n,b)
