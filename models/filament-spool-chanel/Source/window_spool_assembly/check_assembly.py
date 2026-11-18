import cadquery as cq,json,hashlib,time,math,numpy as np
from pathlib import Path
D=Path(__file__).parent;P=Path('/Users/miaozhuang/Projects/mz-3d-print/models/filament-spool-chanel');F=P/'Models/ChanelLight/CHANEL_PARKING_A_WINDOW_LIGHT_TRIAL.step';sha=hashlib.sha256(F.read_bytes()).hexdigest();raw=cq.importers.importStep(str(F)).val();sol=sorted(raw.Solids(),key=lambda s:s.BoundingBox().center.x);assert len(sol)==2 and all(s.isValid() for s in sol)
w,n=[s.translate((-s.BoundingBox().center.x,-s.BoundingBox().center.y,-s.BoundingBox().zmin)) for s in sol]
# Canonical reference uses proper rotations, not a reflection.
def place(h,a):return n.rotate((0,0,0),(1,0,0),180).rotate((0,0,0),(0,0,1),a).translate((0,0,h))
report={'source':str(F),'source_sha256':sha,'transform':'narrow = Rz(theta) Rx(180deg) local_narrow + (0,0,H); wide remains local','H_seated_mm':66.4,'poses':[],'limitations':['Discrete rigid-body poses, not continuous swept-volume or elastic contact analysis.','0 degree is nominal beyond-detent pose with expected official-source rigid overlap, not physical lock certification.','Cardboard dimensions must be supported by evidence; none invented.']}
poses=[]
for h in np.round(np.arange(72,66.399,-.2),6):poses.append(('insert',float(h),51.))
for a in list(range(51,7,-1)):poses.append(('rotate_clear',66.4,float(a)))
for a in np.arange(7.75,-.001,-.25):poses.append(('detent',66.4,float(a)))
poses += [('retention_pull',66.5,8.),('retention_pull',67.,8.),('wrong_entry',70.,45.),('axial_overtravel',66.3,8.)]
for phase,h,a in poses:
 t=time.time();pn=place(h,a);overlap=w.intersect(pn);ss=overlap.Solids();v=sum(s.Volume() for s in ss);row={'phase':phase,'H_mm':h,'angle_deg':a,'intersection_valid':overlap.isValid(),'intersection_solids':len(ss),'intersection_mm3':v,'seconds':time.time()-t}
 if v>1e-6:
  row['centroids_mm']=[[s.Center().x,s.Center().y,s.Center().z] for s in ss]
 report['poses'].append(row);print(row,flush=True);(D/'assembly_results.json').write_text(json.dumps(report,indent=2))
for a,name in [(51,'ENTRY_ORIENTATION_SEATED_51'),(8,'RETAINED_PREDETENT_8'),(0,'NOMINAL_LOCK_0_RIGID_OVERLAP')]:
 asm=cq.Assembly(name=name);asm.add(w,name='wide',color=cq.Color(.65,.49,.3));asm.add(place(66.4,a),name='narrow',color=cq.Color(.3,.55,.7));f=D/(name+'.step');asm.export(str(f),mode='default',write_pcurves=False);b=cq.importers.importStep(str(f)).val();assert b.isValid() and len(b.Solids())==2
 ov=w.intersect(place(66.4,a));
 if ov.Solids():ov.exportBrep(str(D/('interference_'+str(a)+'.brep')))
report['summary']={'clear_path_max_intersection_mm3':max(r['intersection_mm3'] for r in report['poses'] if r['phase'] in ['insert','rotate_clear']),'detent_max':max((r for r in report['poses'] if r['phase']=='detent'),key=lambda r:r['intersection_mm3'])};(D/'assembly_results.json').write_text(json.dumps(report,indent=2));print(report['summary'],flush=True)
w.exportBrep(str(D/'wide_local.brep'));n.exportBrep(str(D/'narrow_local.brep'))
