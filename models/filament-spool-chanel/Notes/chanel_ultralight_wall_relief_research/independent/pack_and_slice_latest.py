import cadquery as cq,numpy as np,trimesh,json,zipfile,xml.etree.ElementTree as E,subprocess,sys
from pathlib import Path
D=Path(__file__).parent;stage=sys.argv[1];step=Path(sys.argv[2]);out=D/('slice_'+stage);out.mkdir(exist_ok=True);ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';E.register_namespace('',ns);solids=sorted(cq.importers.importStep(str(step)).val().Solids(),key=lambda s:s.BoundingBox().center.x);reports=[]
for part,s in zip(['wide','narrow'],solids):
 s=s.translate((-s.BoundingBox().center.x,-s.BoundingBox().center.y,-s.BoundingBox().zmin));v,f=s.tessellate(.005,.05);m=trimesh.Trimesh([[a.x,a.y,a.z] for a in v],f,process=True);cnt=np.bincount(m.edges_unique_inverse);r={'part':part,'vertices':len(m.vertices),'triangles':len(m.faces),'boundary_edges':int(sum(cnt==1)),'nonmanifold_edges':int(sum(cnt>2)),'watertight':m.is_watertight,'solid_valid':s.isValid()};reports.append(r);(out/'mesh_reports.json').write_text(json.dumps(reports,indent=2));print(r,flush=True)
 if not m.is_watertight or any(cnt>2):raise RuntimeError('Refuse slicing non-closed mesh')
 model=E.Element('{'+ns+'}model',unit='millimeter');res=E.SubElement(model,'{'+ns+'}resources');ob=E.SubElement(res,'{'+ns+'}object',id='65537',type='model');mesh=E.SubElement(ob,'{'+ns+'}mesh');vs=E.SubElement(mesh,'{'+ns+'}vertices');ts=E.SubElement(mesh,'{'+ns+'}triangles')
 for x,y,z in m.vertices:E.SubElement(vs,'{'+ns+'}vertex',x=str(x),y=str(y),z=str(z))
 for a,b,c in m.faces:E.SubElement(ts,'{'+ns+'}triangle',v1=str(a),v2=str(b),v3=str(c))
 xml=E.tostring(model,encoding='utf-8',xml_declaration=True);p=out/f'{part}.3mf'
 with zipfile.ZipFile('/tmp/chanel_60g_review/latest_user_settings_single_plate.3mf') as src,zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as dst:
  for n in src.namelist():
   b=xml if n=='3D/Objects/object_1.model' else src.read(n)
   if n=='Metadata/project_settings.config' and len(sys.argv)>3 and sys.argv[3] in ['no_support','auto_support']:
    settings=json.loads(b);settings['enable_support']='1' if sys.argv[3]=='auto_support' else '0';b=json.dumps(settings).encode()
   if n=='Metadata/model_settings.config':b=b.replace(b'original_lower_skin04_wide',(stage+'_'+part).encode())
   dst.writestr(n,b)
 target=out/part;target.mkdir(exist_ok=True)
 with open(out/f'{part}.log','w') as f:result=subprocess.run(['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio','--datadir',str(out/('data_'+part)),'--orient','0','--arrange','0','--slice','1','--outputdir',str(target),'--export-3mf','sliced.3mf',str(p)],stdout=f,stderr=f)
 r['slice_returncode']=result.returncode
 if (target/'result.json').exists():r['result']=json.loads((target/'result.json').read_text())
 (out/'slice_reports.json').write_text(json.dumps(reports,indent=2));print(part,'SLICED',result.returncode,flush=True)
