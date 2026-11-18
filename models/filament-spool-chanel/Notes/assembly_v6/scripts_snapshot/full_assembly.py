import cadquery as cq,json,hashlib,time
from pathlib import Path
P=Path('/Users/miaozhuang/Projects/mz-3d-print/models/filament-spool-chanel');D=Path('/tmp/chanel_assembly_v6');O=P/'Models/Assembly';O.mkdir(exist_ok=True)
src=P/'Models/Review/CHANEL_SOURCE21_v6_FIT_CHANGED_CANDIDATE.step';s=cq.importers.importStep(str(src)).val();parts=sorted(s.Solids(),key=lambda x:x.Center().x);w=parts[0].translate((110.013,0,0));n=parts[1].translate((-110.013,0,0))
H=66.430113973;cw=(-.0273430863,.0010603425);cn=(.0015810415,-.0274228517)
def place(h,a):return n.translate((-cn[0],-cn[1],0)).rotate((0,0,0),(1,0,0),180).rotate((0,0,0),(0,0,1),a).translate((cw[0],cw[1],h))
report={'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'wide_axis_xy':cw,'narrow_axis_xy':cn,'transform':'translate(-narrow_axis), Rx(180deg), Rz(theta), translate(wide_axis,H)','H_stop_mm':H,'chosen_theta_deg':10,'checks':[]}
for h,a in [(H,10),(H,51),(H+2,51),(H+.1,10)]:
 t=time.time();ns=place(h,a);common=w.intersect(ns);v=sum(x.Volume() for x in common.Solids());row={'H':h,'theta_deg':a,'intersection_valid':common.isValid(),'intersection_solid_count':len(common.Solids()),'intersection_volume_mm3':v,'elapsed_seconds':time.time()-t};report['checks'].append(row);print(row,flush=True)
 if h==H and a==10:
  if not common.isValid() or v>1e-6:raise RuntimeError('Chosen full assembly has volume interference')
  assembly=cq.Assembly(name='V6_DIGITAL_LOCK_ZONE_NOT_PHYSICAL_CERTIFICATION');assembly.add(w,name='Wide_half',color=cq.Color(.2,.6,.85));assembly.add(ns,name='Narrow_half',color=cq.Color(.95,.55,.22));path=O/'CHANEL_v6_ASSEMBLY_LOCK_ZONE_10deg.step';assembly.export(str(path),mode='default',write_pcurves=False);back=cq.importers.importStep(str(path)).val();assert back.isValid() and len(back.Solids())==2
  report['assembly_file']={'path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'reimport_valid':True,'reimport_solids':2};print('EXPORTED',report['assembly_file'],flush=True)
  w.exportBrep(str(D/'assembly_wide.brep'));ns.exportBrep(str(D/'assembly_narrow.brep'))
 (D/'full_assembly_validation.json').write_text(json.dumps(report,indent=2))
print('DONE',flush=True)
