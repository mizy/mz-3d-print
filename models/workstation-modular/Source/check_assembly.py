import runpy,json
from pathlib import Path
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
v=runpy.run_path(str(Path(__file__).with_name('build.py')))
shapes=v['shapes'];placed=[shapes['01_base']]
for k,s in enumerate(list(shapes.values())[1:]):placed.append(v['move'](s,v['wall']+v['gap']+(k%3)*(v['cx']+v['wall']),v['wall']+v['gap']+(k//3)*(v['cy']+v['wall']),v['floor']))
maximum=0
for i,s in enumerate(placed):
 for t in placed[i+1:]:
  p=GProp_GProps();BRepGProp.VolumeProperties_s(BRepAlgoAPI_Common(s,t).Shape(),p);maximum=max(maximum,abs(p.Mass()))
assert maximum<1e-5, maximum
r=v['ROOT']/'assembly_validation.json';r.write_text(json.dumps({'pairwise_max_intersection_mm3':maximum,'design_clearance_each_side_mm':.4,'physical_fit_verified':False},indent=2));print('PAIRWISE OK',maximum)
