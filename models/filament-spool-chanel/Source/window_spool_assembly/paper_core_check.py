"""Requires real paper-core measurements. No guessed or nominal cardboard defaults."""
import argparse,json,hashlib
from pathlib import Path
import cadquery as cq
D=Path(__file__).parent
FIELDS=['inner_diameter_mm','outer_diameter_mm','length_mm','notch_width_mm','notch_axial_height_mm','axial_start_mm']
def run(config,spool,out):
 q=json.loads(Path(config).read_text())
 if any(q.get(k) is None for k in FIELDS):raise ValueError('Real paper-core measurements and chosen axial placement are required; template null values are deliberately not guessed.')
 di,do,L,nw,nh,z=[float(q[k]) for k in FIELDS]
 if not 0<di<do or not 0<L or not 0<nw<do or not 0<nh<L:raise ValueError('Invalid measured cardboard geometry')
 body=cq.Workplane('XY').circle(do/2).circle(di/2).extrude(L).translate((0,0,z)).val()
 notch=cq.Workplane('XY').box(nw,do/2+2,nh+.01,centered=(True,False,False)).translate((0,-do/2-1,z-.01)).val();body=body.cut(notch).clean()
 raw=cq.importers.importStep(str(spool)).val();parts=sorted(raw.Solids(),key=lambda s:s.BoundingBox().center.x);assert len(parts)==2 and all(s.isValid() for s in parts);parts=[s.translate((-s.BoundingBox().center.x,-s.BoundingBox().center.y,-s.BoundingBox().zmin)) for s in parts];parts[1]=parts[1].rotate((0,0,0),(1,0,0),180).translate((0,0,66.4));results=[]
 for name,s in zip(['wide','narrow'],parts):
  ov=body.intersect(s);results.append({'part':name,'intersection_mm3':sum(p.Volume() for p in ov.Solids()),'intersection_valid':ov.isValid()})
 out=Path(out);out.mkdir(parents=True,exist_ok=True);asm=cq.Assembly(name='MEASURED_PAPER_CORE_ASSEMBLY');asm.add(parts[0],name='wide');asm.add(parts[1],name='narrow');asm.add(body,name='measured_paper_core');asm.export(str(out/'measured_paper_core_assembly.step'),mode='default',write_pcurves=False)
 report={'measurements_and_placement':q,'source_step_sha256':hashlib.sha256(Path(spool).read_bytes()).hexdigest(),'pose_H_mm':66.4,'pose_theta_deg':0,'intersections':results,'limitations':['Cardboard is idealized rigid concentric tube with one rectangular end notch.','Paper compressibility, wall roughness, distortion and refill loading not modeled.','Only this chosen static placement; insertion and elastic snap not certified.']};(out/'paper_core_results.json').write_text(json.dumps(report,indent=2));print(report)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--measurements',required=True);ap.add_argument('--spool',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();run(a.measurements,a.spool,a.output)
