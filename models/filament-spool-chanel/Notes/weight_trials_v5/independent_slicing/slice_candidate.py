from pathlib import Path
import zipfile,json,subprocess,concurrent.futures,sys
D=Path('/tmp/chanel_100g')
def job(tag,preset):
 changes={} if preset=='baseline' else {'top_shell_layers':'3','top_shell_thickness':'0.6','sparse_infill_density':'5%'};name=tag+'_'+preset;p=D/(name+'.3mf')
 with zipfile.ZipFile(D/(tag+'_base.3mf')) as z,zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as w:
  for n in z.namelist():
   b=z.read(n)
   if n=='Metadata/project_settings.config':d=json.loads(b);d.update(changes);b=json.dumps(d).encode()
   if n=='Metadata/model_settings.config':b=b.replace(b'CHANEL_parametric_v5',tag.encode()).replace(b'narrow_half',tag.encode())
   w.writestr(n,b)
 with open(D/(name+'.log'),'w') as f:r=subprocess.run(['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio','--datadir',str(D/(name+'_data')),'--slice','1','--orient','0','--arrange','0','--outputdir',str(D/name),'--export-3mf','sliced.3mf',str(p)],stdout=f,stderr=f)
 print(name,r.returncode,flush=True)
 if r.returncode==0:print(name,json.load(open(D/name/'result.json'))['sliced_plates'][0]['filaments'],flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(lambda x:job(*x),[(t,p) for t in sys.argv[1:] for p in ['low','baseline']]))
