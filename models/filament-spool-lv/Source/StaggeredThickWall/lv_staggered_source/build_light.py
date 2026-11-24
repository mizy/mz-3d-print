import argparse,json,hashlib,time
from pathlib import Path
import cadquery as cq
from build_official import load
R=Path(__file__).resolve().parent
import official_hub as H,official_key as K
from model_paths import MODELS_DIR
from light_flange import build_light_flange,DEFAULTS
from parking_slot import apply_slots
from hub_windows import apply_windows

def build(config,out):
 q=json.loads(Path(config).read_text());p,f=load(Path(config).parent/q['baseline_parameters']);l=q['light_flange'];out=Path(out);out.mkdir(parents=True,exist_ok=True);assembly=cq.Assembly(name='OFFICIAL_DERIVED_LIGHT_LV');report={'parameters':q,'baseline_parameters':p,'parts':{},'limitations':['No mechanical or physical assembly certification.','Mass must be resliced; old105g figure is not transferable.','Bores, exterior spool diameters and upper mating zones preserved; lower tubes thickened and staggered openings added.']}
 for part,sign in [('wide',-1),('narrow',1)]:
  raw_hub=H.build_hub(part,p['hub']);checked_hub=apply_windows(raw_hub,part,q['hub_windows'],p['hub']);checked_hub.exportBrep(str(out/f'{part}_hub.brep'))
  s=apply_slots(build_light_flange(part,f,l),part,f,q['parking_slots']).fuse(raw_hub,*([K.build_key(p['key'])] if part=='wide' else [])).clean();s=apply_windows(s,part,q['hub_windows'],p['hub']);s=s.intersect(cq.Solid.makeCylinder(f['outer_radius']+1,8).fuse(cq.Solid.makeCylinder(p['hub'][part+'_outer_tube_outer_radius'],60))).clean();assert s.isValid() and len(s.Solids())==1;s.exportBrep(str(out/f'{part}.brep'));b=s.BoundingBox();report['parts'][part]={'valid':True,'solids':1,'faces':len(s.Faces()),'volume_mm3':s.Volume(),'bbox_mm':[b.xlen,b.ylen,b.zlen]};step=out/f'LV_OPEN_ARCH_A_{part}.step';cq.exporters.export(s,str(step),opt={'write_pcurves':False});back=cq.importers.importStep(str(step)).val();assert back.isValid() and len(back.Solids())==1;report['parts'][part]['step_bytes']=step.stat().st_size;print(part,report['parts'][part],flush=True)
 (out/'validation.json').write_text(json.dumps(report,indent=2));print('Both separate STEP exports complete',flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,default=R/'light_parameters.json');ap.add_argument('--output',type=Path,default=MODELS_DIR);a=ap.parse_args();build(a.config,a.output)
