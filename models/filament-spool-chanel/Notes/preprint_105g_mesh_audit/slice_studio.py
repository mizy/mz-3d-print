from pathlib import Path
import zipfile,xml.etree.ElementTree as E,subprocess,json
D=Path('/tmp/chanel_step_openedge_audit');ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';E.register_namespace('',ns);root=E.parse('/tmp/chanel_105g_preprint/studio_mesh.xml').getroot();rows=[]
for i,ob in enumerate(root.findall('.//{'+ns+'}object')):
 mesh=ob.find('{'+ns+'}mesh')
 if mesh is None:continue
 vs=mesh.find('{'+ns+'}vertices');zmin=min(float(v.attrib['z']) for v in vs)
 for v in vs:v.set('z',str(float(v.attrib['z'])-zmin))
 r=E.Element('{'+ns+'}model',unit='millimeter');res=E.SubElement(r,'{'+ns+'}resources');ob.set('id','65537');res.append(ob);xml=E.tostring(r,encoding='utf-8',xml_declaration=True);p=D/f'studio_half_{i}.3mf'
 with zipfile.ZipFile('/tmp/chanel_100g/original_lower_skin04_wide_low.3mf') as src,zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as dst:
  for n in src.namelist():dst.writestr(n,xml if n=='3D/Objects/object_1.model' else src.read(n))
 out=D/f'studio_slice_{i}'
 with open(D/f'studio_slice_{i}.log','w') as f:q=subprocess.run(['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio','--datadir',str(D/f'studio_data_{i}'),'--slice','1','--orient','0','--arrange','0','--outputdir',str(out),'--export-3mf','sliced.3mf',str(p)],stdout=f,stderr=f)
 row={'half':i,'returncode':q.returncode,'source':'Current Studio XML, translated Z only; original topology unchanged'}
 if (out/'result.json').exists():row['result']=json.loads((out/'result.json').read_text())
 rows.append(row);(D/'studio_slice_results.json').write_text(json.dumps(rows,indent=2));print(row,flush=True)
