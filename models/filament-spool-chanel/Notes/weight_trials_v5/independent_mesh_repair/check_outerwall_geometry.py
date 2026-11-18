import re,json,math,numpy as np
from pathlib import Path
from shapely.geometry import LineString
from shapely.ops import unary_union
D=Path('/tmp/chanel_105g_preprint');zs=[32.4,32.6,33.,33.6,34.,34.2,34.6,35.,35.4,36.,36.2,36.6,37.2];C=np.array([120.424375,124.75143])
def get(label):
 xy=np.array([0.,0.]);layer=None;out={z:[] for z in zs};role=''
 for raw in (D/label/'plate_1.gcode').read_text().splitlines():
  if raw.startswith('; Z_HEIGHT: '):layer=float(raw.split(':')[1])
  if raw.startswith('; FEATURE: '):role=raw.strip()[11:]
  l=raw.split(';')[0];mt=re.match(r'^(G[0123]) ',l)
  if not mt:continue
  fields={k:float(v) for k,v in re.findall(r'([XYEIJP])([-+.0-9]+)',l)};end=np.array([fields.get('X',xy[0]),fields.get('Y',xy[1])]);pts=None
  if layer in out and fields.get('E',0)>0 and ('X'in fields or 'Y'in fields) and role == 'Outer wall':
   if mt[1] in ['G2','G3'] and ('I'in fields or 'J'in fields):
    cen=xy+np.array([fields.get('I',0),fields.get('J',0)]);r=np.linalg.norm(xy-cen);a=math.atan2(*(xy-cen)[::-1]);b=math.atan2(*(end-cen)[::-1]);delta=(b-a)%(2*math.pi)
    if mt[1]=='G2':delta=delta-2*math.pi if delta>0 else -2*math.pi
    th=np.linspace(a,a+delta,max(3,int(abs(delta)*r/.02)+2));pts=cen+np.column_stack([np.cos(th),np.sin(th)])*r;pts[0]=xy;pts[-1]=end
   else:pts=np.array([xy,end])
   rad=np.linalg.norm(pts-C,axis=1)
   if rad.min()>26 and rad.max()<34 and np.linalg.norm(end-xy)>1e-9:out[layer].append(LineString(pts))
  xy=end
 return {z:unary_union(v) for z,v in out.items()}
a,b=get('original'),get('repaired');rows=[]
for z in zs:
 assert not a[z].is_empty and not b[z].is_empty
 row={'z':z,'trace_hausdorff_mm':a[z].hausdorff_distance(b[z]),'original_trace_length_mm':a[z].length,'repaired_trace_length_mm':b[z].length};rows.append(row);print(row,flush=True)
(D/'lock_outerwall_geometry_comparison.json').write_text(json.dumps({'method':'Positive-extrusion G1/G2/G3 traces, radius26..34mm, 13 selected lock layers; arcs sampled at nominal<=.02mm. Commands differ, this checks XY trace geometry, not feedrate/strength.','gcode_filter_axis_xy':[120.424375,124.75143],'axis_note':'Gcode XY location observed from circular outer-sleeve paths; not the project placement coordinates.','checks':rows,'max_selected_trace_distance_mm':max(r['trace_hausdorff_mm'] for r in rows)},indent=2))
