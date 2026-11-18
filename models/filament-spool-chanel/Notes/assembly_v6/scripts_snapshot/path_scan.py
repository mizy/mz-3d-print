import numpy as np,json
from pathlib import Path
D=Path('/tmp/chanel_assembly_v6');w=np.load(D/'wide_radial.npz');n=np.load(D/'narrow_radial.npz');H=66.430113973;N=w['r'].shape[1]
def clearance(h,theta):
 zw=np.arange(max(w['z'][0],h-n['z'][-1]),min(w['z'][-1],h-n['z'][0]),.025)
 if not len(zw):return None
 def interp(d,z):
  i=np.clip(np.searchsorted(d['z'],z)-1,0,len(d['z'])-2);f=(z-d['z'][i])/(d['z'][i+1]-d['z'][i]);return d['r'][i]*(1-f[:,None])+d['r'][i+1]*f[:,None]
 a=interp(w,zw);b=interp(n,h-zw)[:,(-np.arange(N))%N];return float((a-np.roll(b,round(theta/.1),axis=1)).min())
rows=[]
for h in np.r_[np.arange(71.5,H,-.05),H]:rows.append({'phase':'axial_insertion','H':float(h),'theta_deg':51.,'minimum_sampled_radial_clearance_mm':clearance(h,51)})
for theta in np.arange(50.5,9.9,-.5):rows.append({'phase':'seated_rotation','H':H,'theta_deg':float(theta),'minimum_sampled_radial_clearance_mm':clearance(H,theta)})
valid=[r['minimum_sampled_radial_clearance_mm'] for r in rows if r['minimum_sampled_radial_clearance_mm'] is not None];report={'method':'Actual v6 native pipe tessellation .003 relative deflection/.03rad angular; sections .025mm; radial rays .1deg; axial pose step .05mm; rotation pose step .5deg. Positive sampled radial envelope does not prove continuous 3D path clearance.','pose_count':len(rows),'minimum_sampled_radial_clearance_mm':min(valid),'all_sampled_envelopes_nonnegative':min(valid)>=0,'poses':rows};(D/'path_radial_validation.json').write_text(json.dumps(report,indent=2));print(report['pose_count'],min(valid),flush=True)
