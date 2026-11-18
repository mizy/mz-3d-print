from pathlib import Path
import zipfile,xml.etree.ElementTree as E,numpy as np,json,subprocess,concurrent.futures,copy
D=Path('/tmp/chanel_105g_preprint');ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';E.register_namespace('',ns);srcroot=E.fromstring((D/'studio_mesh.xml').read_bytes());obj=srcroot.find('.//{'+ns+'}object');data=np.load(D/'wide_studio_seam_repaired.npz')
def build(label):
 root=E.Element('{'+ns+'}model',{'unit':'millimeter'});res=E.SubElement(root,'{'+ns+'}resources');ob=copy.deepcopy(obj);ob.set('id','65537');res.append(ob)
 if label=='repaired':
  mesh=ob.find('{'+ns+'}mesh');mesh.clear();vs=E.SubElement(mesh,'{'+ns+'}vertices');ts=E.SubElement(mesh,'{'+ns+'}triangles')
  for a in data['vertices']:E.SubElement(vs,'{'+ns+'}vertex',dict(zip(['x','y','z'],map(str,a))))
  for f in data['faces']:E.SubElement(ts,'{'+ns+'}triangle',dict(zip(['v1','v2','v3'],map(str,f))))
 p=D/(label+'.3mf')
 with zipfile.ZipFile('/tmp/chanel_shell_ab/on.3mf') as z,zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as w:
  for n in z.namelist():
   b=z.read(n)
   if n=='3D/Objects/object_1.model':b=E.tostring(root,encoding='utf-8',xml_declaration=True)
   if n=='Metadata/project_settings.config':cfg=json.loads(b);cfg.update(top_shell_layers='3',top_shell_thickness='0.6',sparse_infill_density='5%');b=json.dumps(cfg).encode()
   if n=='Metadata/model_settings.config':b=b.replace(b'CHANEL_parametric_v5',('CHANEL_105g_'+label).encode())
   w.writestr(n,b)
 with open(D/(label+'_slice.log'),'w') as log:
  r=subprocess.run(['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio','--datadir',str(D/(label+'_data')),'--slice','1','--orient','0','--arrange','0','--outputdir',str(D/label),'--export-3mf','sliced.3mf',str(p)],stdout=log,stderr=log)
 print(label,r.returncode,flush=True)
 if r.returncode==0:print(label,json.load(open(D/label/'result.json'))['sliced_plates'][0]['filaments'],flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(build,['original','repaired']))
