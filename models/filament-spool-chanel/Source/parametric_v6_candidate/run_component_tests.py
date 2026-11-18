import sys,json,copy,time,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R))
from config import load,derived
from body import *
from motif import double_c
p=load();out={'source_hashes':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in R.glob('*.py')},'tests':[]};D=R/'test_output';D.mkdir(exist_ok=True)
def record(name,ok,details):
 out['tests'].append(dict(name=name,pass_test=bool(ok),details=details));(D/'components.json').write_text(json.dumps(out,indent=2));print(name,ok,details,flush=True)
def dims(s):
 b=s.BoundingBox();return [b.xlen,b.ylen,b.zlen]
# Logo XY scale must not scale Z. Depth must exceed thick rib top.
base=double_c(1,8);bd=dims(base)
for scale in [.8,1.1]:
 s=double_c(scale,8);dd=dims(s);record('logo_'+str(scale),s.isValid() and abs(dd[0]/bd[0]-scale)<1e-6 and abs(dd[1]/bd[1]-scale)<1e-6 and abs(dd[2]-bd[2])<1e-6,{'bbox':dd,'volume':s.Volume(),'expected_xy_scale':scale,'z_invariant':bd[2]})
# Each radius/width/height produces independently expected ring bbox and drilled area.
for name,changes in [('rim_default',{}),('rim_diameter',{'rolling_outer_radius':102.013}),('rim_width',{'rim_radial_width':6.5}),('rim_height',{'rim_height':5})]:
 q=copy.deepcopy(p);q.update(changes);s=rolling_rim(q);dd=dims(s);sec=cq.Workplane('XY').newObject([s]).section(q['rim_height']/2).val();loops=sec.Wires();record(name,s.isValid() and len(s.Solids())==1 and abs(dd[0]-2*q['rolling_outer_radius'])<1e-5 and abs(dd[2]-q['rim_height'])<1e-5 and len(loops)==10,{'bbox':dd,'section_loops':len(loops),'volume':s.Volume(),'derived':derived(q)})
# Sleeve thickening must preserve mating faces: wide inside R39, narrow neck outside R38.898.
for part,z,r in [('wide',30,39),('narrow',26,38.898)]:
 vals=[]
 for extra in [0,.4]:
  q=copy.deepcopy(p);q['sleeve_wall_extra']=extra;s=outer_tube(part,q);sec=cq.Workplane('XY').newObject([s]).section(z).val();radii=sorted([e.radius() for e in sec.Edges() if e.geomType()=='CIRCLE']);vals.append(radii)
 record('sleeve_fit_'+part,any(abs(a-r)<1e-6 for a in vals[0]) and any(abs(a-r)<1e-6 for a in vals[1]),{'radii_before_after':vals,'protected_radius':r})
for name,changes in [('negative_skin',{'skin_thickness':-.1}),('unknown_key',{'unused_x':1}),('too_thin_core',{'hub_lower_inner_radius':40}),('fractional_ribs',{'rib_count':8.5})]:
 q=copy.deepcopy(p);q.update(changes);f=D/(name+'.json');f.write_text(json.dumps(q));error=None
 try:load(f)
 except Exception as e:error=str(e)
 record(name,error is not None,error)
# Observed volume response for bore and hub changes; no full-build claim.
base=lower_core('narrow',p)
for name,changes,sign in [('lower_bore',{'hub_lower_inner_radius':36},1),('hub_outer',{'hub_outer_radius':41.5},1),('shaft_bore',{'shaft_bore_radius':27.8},-1)]:
 q=copy.deepcopy(p);q.update(changes);s=lower_core('narrow',q);dv=s.Volume()-base.Volume();record(name,s.isValid() and len(s.Solids())==1 and dv*sign>0,{'volume_change_mm3':dv,'bbox':dims(s)})
print('DONE',flush=True)

assert all(row['pass_test'] for row in out['tests']), 'Component regression failed'
