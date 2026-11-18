from pathlib import Path
import zipfile,json,subprocess,concurrent.futures,sys
D=Path('/tmp/chanel_100g');variants={'baseline':{},'top4':{'top_shell_layers':'4','top_shell_thickness':'0.8'},'top3':{'top_shell_layers':'3','top_shell_thickness':'0.6'},'top3_sparse5':{'top_shell_layers':'3','top_shell_thickness':'0.6','sparse_infill_density':'5%'}}
def job(part,name,changes):
 src=Path('/tmp/chanel_shell_ab/on.3mf') if part=='wide' else D/'narrow_base.3mf';tag=part+'_'+name;file=D/(tag+'.3mf')
 with zipfile.ZipFile(src) as z,zipfile.ZipFile(file,'w',zipfile.ZIP_DEFLATED) as o:
  for n in z.namelist():
   b=z.read(n)
   if n=='Metadata/project_settings.config':c=json.loads(b);c.update(changes);b=json.dumps(c).encode()
   o.writestr(n,b)
 with (D/(tag+'.log')).open('w') as log:
  r=subprocess.run(['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio','--datadir',str(D/(tag+'_data')),'--slice','1','--orient','0','--arrange','0','--outputdir',str(D/tag),'--export-3mf','sliced.3mf',str(file)],stdout=log,stderr=log)
 print(tag,r.returncode,flush=True)
 if r.returncode==0:
  j=json.load(open(D/tag/'result.json'));print(tag,j['sliced_plates'][0]['filaments'],flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
 list(ex.map(lambda a:job(*a),[(p,n,c) for p in sys.argv[1:] for n,c in variants.items() if not(p=='wide' and n=='baseline')]))
