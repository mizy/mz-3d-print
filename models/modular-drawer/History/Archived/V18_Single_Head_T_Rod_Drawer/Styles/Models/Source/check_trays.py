"""Independent read-back of tested tray alternatives, dimensions in mm. No slicer/strength test."""
import argparse,hashlib,json,math
from pathlib import Path
import FreeCAD as A,Part
V=A.Vector
p=argparse.ArgumentParser()
p.add_argument('baseline',type=Path)
p.add_argument('registry',type=Path)
p.add_argument('output',type=Path)
args=p.parse_args()
def h(q):return hashlib.sha256(q.read_bytes()).hexdigest()
def bb(s):
 b=s.optimalBoundingBox(False,False)
 return [round(getattr(b,f'{k}{s}'),6) for k in 'XYZ' for s in ('Min','Max')]
def box(x0,x1,y0,y1,z0,z1):return Part.makeBox(x1-x0,y1-y0,z1-z0,V(x0,y0,z0))
assert h(args.baseline)=='4fab31b0c8a9abac78bae99e9d4ee4634a2a545abd49272ac800f2d9df6a380b'
base=Part.read(str(args.baseline));assert base.isValid() and len(base.Solids)==1
assert bb(base)==[0,144.1,0,230,0,86],bb(base)
reports=[]
for c in json.loads(args.registry.read_text()):
 q=Path(c['file']);assert h(q)==c['sha256']
 raw=Part.read(str(q))
 n=c.get('solids',1);assert raw.isValid() and len(raw.Solids)==n,(q,n,len(raw.Solids))
 # Optional insert is audited separately unless the main exported file is deliberately compound.
 s=raw.Solids[c.get('tray_index',0)]
 assert max(abs(x-y) for x,y in zip(bb(s),bb(base)))<.001,(q,bb(s))
 rm=base.cut(s);ad=s.cut(base)
 v0=base.Volume;v=s.Volume;minus,plus=rm.Volume,ad.Volume
 assert abs(v+minus-plus-v0)<c.get("volume_balance_absolute_tol_mm3",.005),(q,minus,plus,v,v0)
 if c.get('cut_only',True):assert plus<.003,(q,'not a pure subtraction',plus)
 boxes=[box(*a) for a in c['edit_boxes_x1x2y1y2z1z2']]
 protect=boxes[0].multiFuse(boxes[1:]) if len(boxes)>1 else boxes[0]
 mo=rm.cut(protect).Volume
 po=ad.cut(protect).Volume
 assert max(mo,po)<.01,(q,'difference outside approved local alteration zone',mo,po)
 no_bottom=box(-.1,144.2,-.1,230.1,-.1,c.get('protected_bottom_mm',2.59))
 no_rear=box(-.1,144.2,c.get('protected_rear_start_mm',218.),230.1,-.1,86.1)
 for name,r in [('floor',no_bottom),('rear',no_rear)]:
  vals=[rm.common(r).Volume,ad.common(r).Volume]
  assert max(vals)<.003,(q,name,vals)
 note=dict(name=c['name'],file=q.name,sha256=h(q),valid_solids=n,bounds_mm=bb(s),volume_mm3=v,
  baseline_volume_mm3=v0,removed_mm3=minus,added_mm3=plus,volume_partition_residual_mm3=v+minus-plus-v0,symmetric_difference_outside_edit_boxes_mm3=[mo,po],
  base_support_floor_and_rear_stop_changed_mm3=0.,pure_removal_of_sealed_original=plus<.003)
 if plus<.003:note['assembly_note']='Outside protected shell, tray CAD has no material addition; the original signed tray operating envelopes cannot gain rigid-body collision from removal alone. This is not an opening/strength print test.'
 else:note['assembly_note']='Material added; use variant-specific continuous travel/assembly checks to qualify.'
 for pth in c.get('optional_insert_paths',[]):
  f=Path(pth['file']);assert h(f)==pth['sha256'];sr=Part.read(str(f));assert sr.isValid()
  note.setdefault('optional_parts',[]).append(dict(file=f.name,sha256=h(f),valid_solids=len(sr.Solids),bounds_mm=bb(sr)))
 print(json.dumps(note,ensure_ascii=False),flush=True);reports.append(note)
args.output.write_text(json.dumps(dict(baseline_sha256=h(args.baseline),baseline_bbox_mm=bb(base),variants=reports),ensure_ascii=False,indent=2)+'\n')
