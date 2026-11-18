"""Usage: python rebuild.py --config parameters.json --output build_output
Never modifies the selected configuration or existing v4 deliverables.
"""
import argparse,json,time,hashlib
from pathlib import Path
import cadquery as cq
from config import load,derived,DEFAULT
from body import build_flange,structural_body,bridges
from lock import build_pipe
R=Path(__file__).resolve().parent

def build(p,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);start=time.time();d=derived(p)
 (out/'effective_parameters.json').write_text(json.dumps(p,indent=2))
 flange=build_flange(p);flange.exportBrep(str(out/'flange.brep'));print('FLANGE',flange.Volume(),flush=True)
 controls=json.loads((R/'native_lock_sections.json').read_text());shapes={};report={'parameters':p,'derived':d,'parts':{},'limitations':['CAD validity is not a strength/load certification.','Changed lock dimensions do not retain source-spool compatibility.','Print-fit and physical load tests remain required.','STEP contains geometry, not a feature-history parameter tree.']}
 for part in ['wide','narrow']:
  pipe=build_pipe(part,controls,p);print('PIPE',part,len(pipe.Faces()),flush=True)
  body=structural_body(part,p,flange);extra=bridges(p) if part=='wide' else []
  s=body.fuse(pipe,*extra)
  if not s.isValid() or len(s.Solids())!=1:raise ValueError(f'{part}: not one valid fused solid')
  shapes[part]=s;s.exportBrep(str(out/f'{part}_complete.brep'))
  b=s.BoundingBox();report['parts'][part]={'valid':s.isValid(),'solid_count':len(s.Solids()),'face_count':len(s.Faces()),'volume_mm3':s.Volume(),'bbox_mm':[b.xlen,b.ylen,b.zlen]}
  print('PART',part,report['parts'][part],flush=True)
 assembly=cq.Assembly(name='CHANEL_WEIGHT_TRIAL_V5');offset=p['rolling_outer_radius']+10
 for part,x in [('wide',-offset),('narrow',offset)]:assembly.add(shapes[part],name=part+'_half',loc=cq.Location(cq.Vector(x,0,0)))
 path=out/'CHANEL_V5_WEIGHT_TRIAL.step';assembly.export(str(path),mode='default',write_pcurves=False)
 imported=cq.importers.importStep(str(path)).val()
 if not imported.isValid() or len(imported.Solids())!=2:raise ValueError('Export/reimport failed two-solid validation')
 report['step']={'valid':True,'solid_count':2,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'reimport_volumes_mm3':[s.Volume() for s in imported.Solids()]}
 report['elapsed_seconds']=time.time()-start
 (out/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
 return report
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,default=DEFAULT);parser.add_argument('--output',type=Path,default=R/'build_output');args=parser.parse_args();build(load(args.config),args.output)
