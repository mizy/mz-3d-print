"""Read and validate every user-facing design dimension; units mm."""
import json, math
from pathlib import Path
DEFAULT=Path(__file__).with_name('parameters.json')
def load(path=DEFAULT):
 p=json.loads(Path(path).read_text())
 expected={'rolling_outer_radius','rim_radial_width','rim_height','skin_thickness','rib_width','rib_height_above_skin','rib_count','logo_scale','logo_rings','hub_outer_radius','hub_lower_inner_radius','sleeve_wall_extra','shaft_bore_radius','lock_reference_bore_radius','lock_axial_scale','wide_lock_wall_thickness','bridge_width'}
 if set(p)!=expected:raise ValueError(f"Missing/unknown parameters: {set(p)^expected}")
 for k,v in p.items():
  if k=='logo_rings':continue
  if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v):raise ValueError(f'{k}: finite number required')
 bounds={'rolling_outer_radius':(90,120),'rim_radial_width':(4,10),'rim_height':(3,8),'skin_thickness':(.6,2.4),'rib_width':(3,8),'rib_height_above_skin':(2,7),'rib_count':(8,16),'logo_scale':(.7,1.1),'hub_outer_radius':(40.85,44),'hub_lower_inner_radius':(34,37.5),'sleeve_wall_extra':(0,1),'shaft_bore_radius':(26,28),'lock_reference_bore_radius':(30.8,32),'lock_axial_scale':(.98,1.05),'wide_lock_wall_thickness':(1.7,2.6),'bridge_width':(1.2,2.5)}
 for k,(lo,hi) in bounds.items():
  if not lo<=p[k]<=hi:raise ValueError(f'{k} must be within [{lo}, {hi}]')
 if p['rib_count']!=int(p['rib_count']):raise ValueError('rib_count must be integer')
 p['rib_count']=int(p['rib_count'])
 rows=p['logo_rings']
 if not isinstance(rows,list) or not rows:raise ValueError('logo_rings must be nonempty list')
 for row in rows:
  if set(row)!={'fraction','count','relative_scale'}:raise ValueError('logo row requires fraction/count/relative_scale')
  if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in row.values()):raise ValueError('logo row values must be finite numbers')
  if not .1<=row['fraction']<=.9 or not .6<=row['relative_scale']<=1.1 or not isinstance(row['count'],int) or not 8<=row['count']<=40:raise ValueError('Invalid logo row values')
 d=derived(p)
 if d['plate_outer']-d['plate_inner']<35:raise ValueError('Insufficient radial space for open flange')
 if p['hub_lower_inner_radius']>p['hub_outer_radius']-3:raise ValueError('Lower hub wall must be at least 3 mm')
 if p['shaft_bore_radius']>29.7*d['k']-1.5:raise ValueError('Narrow lock tube wall must be >=1.5 mm')
 if 31.4*d['k']+p['wide_lock_wall_thickness']>=39+d['od']-2:raise ValueError('Wide lock/sleeve clearance insufficient')
 return p

def derived(p):
 od=p['hub_outer_radius']-40.85;k=p['lock_reference_bore_radius']/31.4
 ri=p['rolling_outer_radius']-p['rim_radial_width'];foot=44+od
 return dict(od=od,k=k,az=p['lock_axial_scale'],rim_inner=ri,plate_outer=ri-1,plate_inner=foot-.3,rib_start=foot-.5,rib_end=ri+2.5)
