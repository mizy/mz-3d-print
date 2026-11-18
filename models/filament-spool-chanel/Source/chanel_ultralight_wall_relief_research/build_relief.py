import argparse,json,hashlib,time
from pathlib import Path
import cadquery as cq
from build_official import load,R
import official_hub as H,official_key as K
from light_flange import build_light_flange,DEFAULTS
from parking_slot import apply_slots
from hub_windows import apply_windows
from center_relief import apply_relief

def build(config,out):
 q=json.loads(Path(config).read_text());p,f=load(Path(config).parent/q['baseline_parameters']);l=q['light_flange'];out=Path(out);out.mkdir(parents=True,exist_ok=True);assembly=cq.Assembly(name='OFFICIAL_DERIVED_LIGHT_CHANEL');report={'parameters':q,'baseline_parameters':p,'parts':{},'limitations':['No mechanical or physical assembly certification.','Mass must be resliced; old105g figure is not transferable.','Nominal mating surfaces retained, but guide/column wall and support-floor thickness reduced; stiffness is not preserved.']}
 for part,sign in [('wide',-1),('narrow',1)]:
  s=apply_slots(build_light_flange(part,f,l),part,f,q['parking_slots']).fuse(H.build_hub(part,p['hub']),*([K.build_key(p['key'])] if part=='wide' else [])).clean();s=apply_windows(s,part,q['hub_windows'],p['hub']);s=apply_relief(s,part,q['center_relief'],p['hub']);assert s.isValid() and len(s.Solids())==1;s.exportBrep(str(out/f'{part}.brep'));b=s.BoundingBox();report['parts'][part]={'valid':True,'solids':1,'faces':len(s.Faces()),'volume_mm3':s.Volume(),'bbox_mm':[b.xlen,b.ylen,b.zlen]};assembly.add(s,name=part,loc=cq.Location(cq.Vector(sign*(f['outer_radius']+10),0,0)));print(part,report['parts'][part],flush=True)
 step=out/'CHANEL_ULTRALIGHT_WALL_RELIEF_RESEARCH.step';assembly.export(str(step),mode='default',write_pcurves=False);back=cq.importers.importStep(str(step)).val();assert back.isValid() and len(back.Solids())==2;report['step']={'valid':True,'solids':2,'bytes':step.stat().st_size,'sha256':hashlib.sha256(step.read_bytes()).hexdigest()};(out/'validation.json').write_text(json.dumps(report,indent=2));print(report['step'],flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,default=R/'relief.json');ap.add_argument('--output',type=Path,default=R/'light_output');a=ap.parse_args();build(a.config,a.output)
