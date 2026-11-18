from pathlib import Path
import json,numpy as np,trimesh,cadquery as cq,hashlib
D=Path('/tmp/chanel_hole_comparison');P=Path('/Users/miaozhuang/Projects/mz-3d-print/models/filament-spool-chanel/Models/CHANEL_105g_KEEP_CORE.step')
Z=[.2,.8,1.5,2,5,10,12,13,14,15,16,18,19.5,21,22.1,23,24.1,25,27,30,32.5,34,36,37.1,38,40]
ang=np.arange(0,360,.5)*np.pi/180;U=np.column_stack([np.cos(ang),np.sin(ang)])
def rays(seg):
 a=seg[:,0,:2];d=seg[:,1,:2]-a;cross=U[:,0,None]*d[None,:,1]-U[:,1,None]*d[None,:,0];num=a[:,0]*d[:,1]-a[:,1]*d[:,0]
 with np.errstate(divide='ignore',invalid='ignore'):
  rr=num[None,:]/cross;tt=(a[None,:,0]*U[:,1,None]-a[None,:,1]*U[:,0,None])/cross
 good=(rr>0)&(tt>=-1e-8)&(tt<=1+1e-8);rr=np.where(good,rr,np.inf);r=rr.min(axis=1);r=r[np.isfinite(r)]
 return {'r_min':float(r.min()),'r_max':float(r.max()),'r_median':float(np.median(r)),'ray_count':len(r)} if len(r) else None
out={'method':'z measured from outside flange bottom z=0, bbox XY centered as project source normalization. First positive boundary intersection along720 angular rays. Values are geometric measurements, not manufacturer standards.','original_stl':{},'current_step':{}}
for part,name in [('wide','obj_1_料盘反面.stl'),('narrow','obj_2_料盘正面.stl')]:
 p=Path('/Users/miaozhuang/Downloads/bambuLab_spool2.1_stls')/name;m=trimesh.load(p,process=False);origin=np.r_[(m.bounds[0,:2]+m.bounds[1,:2])/2,m.bounds[0,2]];m.apply_translation(-origin);rows=[]
 for z in Z:
  if z>=m.bounds[1,2]:continue
  seg=trimesh.intersections.mesh_plane(m,[0,0,1],[0,0,z]);row={'z':z,'hole':rays(seg)};rows.append(row)
 out['original_stl'][part]={'filename':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'origin':origin.tolist(),'bounds':m.bounds.tolist(),'sections':rows};print('ORIGINAL',part,rows,flush=True)
(D/'measurements_partial.json').write_text(json.dumps(out,indent=2))
s=cq.importers.importStep(str(P)).val();out['step_sha256']=hashlib.sha256(P.read_bytes()).hexdigest()
for ss in s.Solids():
 bb=ss.BoundingBox();part='wide' if bb.zmax>40 else 'narrow';shift=-110.013 if part=='wide' else 110.013;ss=ss.translate((-shift,0,0));rows=[]
 for z in Z:
  if z>=bb.zmax:continue
  sec=cq.Workplane('XY').newObject([ss]).section(z).val();segments=[]
  for e in sec.Edges():
   pts=e.sample(max(3,int(e.Length()/.04)+2))[0];a=np.array([[v.x,v.y,v.z] for v in pts]);segments.extend(np.stack([a[:-1],a[1:]],axis=1))
  row={'z':z,'hole':rays(np.array(segments))};rows.append(row);print('STEP',part,row,flush=True)
 out['current_step'][part]={'sections':rows,'valid':ss.isValid(),'height':bb.zmax}
(D/'measurements.json').write_text(json.dumps(out,indent=2))
