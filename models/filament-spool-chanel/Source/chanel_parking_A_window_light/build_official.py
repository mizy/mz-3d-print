"""Build independent official-reference baseline from editable native CAD parameters.
No STL is loaded by this generator. It refuses incomplete hub implementations.
"""
import argparse,json,time,hashlib
from pathlib import Path
import cadquery as cq
import official_flange as F,official_hub as H,official_key as K
R=Path(__file__).resolve().parent
SHARED={'bore_radius':'shaft_bore_radius','bore_entry_chamfer':'entry_chamfer','support_top':'support_top','wide_outer_tube_radius':'wide_outer_tube_outer_radius','narrow_outer_tube_radius':'narrow_outer_tube_outer_radius','wide_inner_tube_outer':'wide_inner_tube_outer_radius','narrow_inner_tube_outer':'narrow_inner_tube_outer_radius','wide_outer_tube_inner':'wide_outer_tube_inner_radius','narrow_outer_tube_inner':'narrow_outer_tube_inner_radius'}
def defaults():return {'flange':{k:v for k,v in F.DEFAULT.items() if k not in SHARED},'hub':dict(H.DEFAULTS),'key':dict(K.DEFAULTS)}
def load(path):
 p=json.loads(Path(path).read_text());d=defaults()
 if set(p)!=set(d):raise ValueError('Expected flange, hub and key groups')
 for group in d:
  if set(p[group])!=set(d[group]):raise ValueError(f'{group}: unknown or missing parameter {set(p[group])^set(d[group])}')
 h=p['hub'];f=dict(p['flange'])
 if h['hub_radial_scale']!=1 or h['hub_axial_scale']!=1:raise ValueError('Whole-hub scaling not yet linked to flange/key; edit explicit dimensions instead')
 f.update({fk:h[hk] for fk,hk in SHARED.items()});F.validate(f)
 # Locating key dimensions remain explicit, but cannot lose overlap with adjusted hub.
 if not p['key']['radial_overlap_start']<h['wide_outer_tube_outer_radius']<p['key']['outer_tip_radius']:raise ValueError('Key must overlap wide tube and protrude outward')
 if p['key']['bottom_z']!=f['plate_thickness']:raise ValueError('Key bottom must match plate thickness')
 return p,f

def build(config,out):
 p,f=load(config);out=Path(out);out.mkdir(parents=True,exist_ok=True);report={'config':p,'effective_flange':f,'parts':{},'status':'official-reference reconstruction, not physical certification'};start=time.time();assembly=cq.Assembly(name='OFFICIAL_REFERENCE_NATIVE_BASELINE')
 for part,sign in [('wide',-1),('narrow',1)]:
  hub=H.build_hub(part,p['hub']);flange=F.build_flange(part,f);body=flange.fuse(hub,*([K.build_key(p['key'])] if part=='wide' else [])).clean()
  if not body.isValid() or len(body.Solids())!=1:raise ValueError(f'{part}: invalid/disconnected fused solid')
  body.exportBrep(str(out/f'{part}.brep'));b=body.BoundingBox();report['parts'][part]={'valid':True,'solids':1,'faces':len(body.Faces()),'volume_mm3':body.Volume(),'bbox':[b.xlen,b.ylen,b.zlen]};assembly.add(body,name=part,loc=cq.Location(cq.Vector(sign*(f['outer_radius']+10),0,0)));print(part,report['parts'][part],flush=True)
 step=out/'BAMBU_OFFICIAL_REFERENCE_NATIVE_BASELINE.step';assembly.export(str(step),mode='default',write_pcurves=False);s=cq.importers.importStep(str(step)).val();assert s.isValid() and len(s.Solids())==2
 report.update(step={'bytes':step.stat().st_size,'sha256':hashlib.sha256(step.read_bytes()).hexdigest(),'valid':True,'solids':2},seconds=time.time()-start);(out/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,default=R/'parameters.json');ap.add_argument('--output',type=Path,default=R/'build_output');ap.add_argument('--write-defaults',action='store_true');a=ap.parse_args()
 if a.write_defaults:a.config.write_text(json.dumps(defaults(),indent=2))
 else:build(a.config,a.output)
