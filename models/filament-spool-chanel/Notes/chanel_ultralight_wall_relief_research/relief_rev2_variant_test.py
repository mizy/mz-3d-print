import sys,json
from pathlib import Path
import cadquery as cq,numpy as np,trimesh
D=Path(__file__).parent;sys.path.insert(0,'/Users/miaozhuang/Projects/mz-3d-print/models/filament-spool-chanel/Source/chanel_ultralight_wall_relief_research')
from center_relief import apply_relief
q=json.load(open(D/'relief.json'));h=json.load(open(D/'parameters.json'))['hub'];p=q['center_relief'];p.update(wide_guide_wall=1.4,narrow_guide_wall=1.3,outer_column_wall=1.4,floor_thickness=1.2);r={'parameters':p,'parts':{}}
for part in ['wide','narrow']:
 old=cq.importers.importBrep(str(D/'spoke_rev2'/(part+'.brep'))).val();s=apply_relief(old,part,p,h);f=D/('relief_rev2_variant_'+part+'.step');cq.exporters.export(s,str(f));s=cq.importers.importStep(str(f)).val();v,t=s.tessellate(.01,.1);m=trimesh.Trimesh([[x.x,x.y,x.z] for x in v],t,process=True);cnt=np.bincount(m.edges_unique_inverse);r['parts'][part]={'valid':s.isValid(),'solids':len(s.Solids()),'faces':len(s.Faces()),'volume':s.Volume(),'boundary':int(sum(cnt==1)),'nonmanifold':int(sum(cnt>2))};print(part,r['parts'][part],flush=True);(D/'relief_rev2_variant_test.json').write_text(json.dumps(r,indent=2))
