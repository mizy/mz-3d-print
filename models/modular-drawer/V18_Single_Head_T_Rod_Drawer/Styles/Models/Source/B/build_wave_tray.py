#!/usr/bin/env python3
"""User-approved V18 B: kept-closed side walls and crescent pull, precise BRep only."""
import argparse,json,hashlib,math
from pathlib import Path
import FreeCAD as App,Part,Import
V=App.Vector
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def box(x,y,z,a,b,c):return Part.makeBox(a,b,c,V(x,y,z))
def B(s):return s.optimalBoundingBox(False,False)
def close(v,t,e=1e-5):return abs(v-t)<=e
def bez(points):
 c=Part.BezierCurve();c.setPoles(points);return c.toShape()
def line(a,b):return Part.makeLine(a,b)
def compound(f):return f.removeSplitter()
def cut_piece(edge,profile_start,profile_end,extrusion,up_z=100.):
 a=V(profile_end.x,profile_end.y,up_z);b=V(profile_start.x,profile_start.y,up_z)
 return Part.Face(Part.Wire(edge+[line(profile_end,a),line(a,b),line(b,profile_start)])).extrude(extrusion)
def export(s,path):
 doc=App.newDocument('V18_Wave')
 try:
  po=doc.addObject('Part::Feature','Wave_Grip_Drawer');po.Label='V18 B Wave Grip Drawer';po.Shape=s
  doc.recompute();Import.export([po],str(path))
 finally:App.closeDocument(doc.Name)
 assert path.is_file()
def delta(a,b):return a.cut(b).Volume+b.cut(a).Volume
def xform(s,name):
 return tuple(getattr(s,name+k) for k in ('Min','Max','Length'))
def evaluate(e,axis,t):
 lo,hi=e.FirstParameter,e.LastParameter
 for _ in range(45):
  m=(lo+hi)/2
  if getattr(e.valueAt(m),axis)<t:lo=m
  else:hi=m
 return e.valueAt((lo+hi)/2).z
def make(config,out):
 q=json.loads(config.read_text());base=config.parent/q['baseline_step'];assert sha(base)==q['baseline_sha256'],'Not the exact V18 source'
 src=Part.read(str(base));assert src.isValid() and len(src.Solids)==1
 src=src.Solids[0];W,D,H=q['expected_drawer_bbox_mm'];b=B(src)
 assert all(close(k,v) for k,v in zip((b.XLength,b.YLength,b.ZLength),[W,D,H]))
 assert all(close(k,0) for k in (b.XMin,b.YMin,b.ZMin))
 xmid=W/2; h0=q['front_side_join_z_mm'];hf=q['front_grip_shoulder_z_mm'];hb=q['front_grip_floor_z_mm'];s=q['front_grip_half_span_mm']
 left=xmid-s; L=q['front_corner_flat_width_mm'];K=q['front_corner_blend_end_x_mm'];assert 0<L<K<left<xmid
 # Left crescent edge transitions to central floor through tangent-matched cubic Bezier spans.
 # All dimensions derived from span, depth and explicit calibrated normalized positions.
 rise=hf-hb
 c1=[(left,hf),(left+s*.1815,hf),(left+s*.1815,hb+rise*4./13.),(left+s*.4841,hb+rise*1.25/13.)]
 _,h2=c1[-1];x2=c1[-1][0];m=(h2-c1[-2][1])/(x2-c1[-2][0])
 C2=x2+(hb-h2)/m
 c2=[c1[-1],(C2,hb),(xmid-s*.183,hb),(xmid,hb)]
 y=-.5; F=lambda x,z:V(x,y,z); leftBlend=[(L,h0),(L+(K-L)*.31,h0),(K-(K-L)*.34,hf),(K,hf)]
 refl=lambda p:[(W-x,z) for x,z in reversed(p)]
 chain=[[(-.6,h0),(L,h0)],leftBlend,[(K,hf),(left,hf)],c1,c2,refl(c2),refl(c1),refl([(K,hf),(left,hf)]),refl(leftBlend),refl([(-.6,h0),(L,h0)])]
 e=[bez([F(*p)for p in seg]) if len(seg)==4 else line(F(*seg[0]),F(*seg[1])) for seg in chain]
 cutter_front=cut_piece(e,F(*chain[0][0]),F(*chain[-1][-1]),V(0,q['front_boolean_stop_y_mm']-y,0))
 # Sidewalls rise only into the legacy side top, and blend with flat tangency at both ends.
 # The two left/right cuts cover the original trimmed wall and rounded front periphery.
 a=q['side_front_hold_y_mm'];end=q['side_taper_rejoins_at_y_mm'];rear=q['rear_preservation_start_y_mm'];side_z=q['side_original_top_z_mm']
 assert q['front_boolean_stop_y_mm']<=a<end<rear<D and q['side_wall_mask_width_mm']<L
 x=-.5;U=lambda y,z:V(x,y,z)
 s0=U(-.6,h0);s1=U(a,h0);s2=U(end,side_z)
 taper=bez([s1,U(a+(end-a)*.31,h0),U(end-(end-a)*.39,side_z),s2])
 side_a=cut_piece([line(s0,s1),taper],s0,s2,V(q['side_wall_mask_width_mm']-x,0,0))
 mat=App.Matrix();mat.A11=-1.;mat.A14=W
 side_b=side_a.copy();side_b.transformShape(mat,True,True)
 sh=src.cut([cutter_front,side_a,side_b]).removeSplitter();assert sh.isValid() and len(sh.Solids)==1
 bb=B(sh);assert all(close(p,r) for p,r in zip((bb.XLength,bb.YLength,bb.ZLength),(W,D,H)))
 bottom_mask=box(-1,-1,-1,W+2,D+2,hb)
 rear_mask=box(-1,rear,-1,W+2,D+1-rear,H+2)
 above=box(-1,-1,hb-.1,W+2,D+2,H-hb+1)
 added=sh.cut(src).Volume
 lower=delta(sh.common(bottom_mask),src.common(bottom_mask)); aft=delta(sh.common(rear_mask),src.common(rear_mask));removed=src.cut(sh)
 outside=removed.cut(cutter_front.fuse([side_a,side_b])).Volume
 assert max(added,lower,aft,outside)<.0002,(added,lower,aft,outside)
 # Confirm the old U is fully replaced: 131 front profile probes against the new continuous exact edge.
 samples=[]
 for k in range(131):
  xx=left+(2*s)*k/130
  i=next(i for i in (3,4,5,6) if min(z[0] for z in chain[i])-1e-7<=xx<=max(z[0] for z in chain[i])+1e-7)
  pred=evaluate(e[i],'x',xx)
  hit=sh.common(box(xx-.002,.55,0,.004,.20,H+1)).BoundBox.ZMax
  samples.append([round(xx,4),pred,hit,abs(pred-hit)])
 worst=max(row[-1]for row in samples);assert worst<.11,worst
 # Both side walls are continuous, monotonically rising and meet their original top.
 yz=[]
 for k in range(41):
  yy=a+(end-a)*k/40.;z=evaluate(taper,'y',yy)
  pair=[sh.common(box(xx,yy-.002,0,.36,.004,H+1)).BoundBox.ZMax for xx in (0,W-.36)]
  yz.append([yy,z,*pair])
 assert max(abs(x[1]-s) for x in yz for s in x[2:])<.07
 out.mkdir(exist_ok=True,parents=True);path=out/'V18_B_Wave_Grip_Drawer.step'
 export(sh,path);bk=Part.read(str(path));assert bk.isValid() and len(bk.Solids)==1
 assert delta(bk,sh)<.0005
 b0=path.read_bytes().upper();assert not any(s in b0 for s in [b'FACETED_BREP',b'TRIANGULATED_FACE_SET',b'TESSELLATED_SHAPE_REPRESENTATION'])
 report=dict(source_baseline_sha256=sha(base),step_sha256=sha(path),step_reimport_valid_solids=1,step_roundtrip_volume_difference_mm3=delta(bk,sh),step_has_faceted_entities=False,
  bbox_mm=[W,D,H],source_volume_mm3=src.Volume,new_volume_mm3=sh.Volume,removed_volume_mm3=removed.Volume,
  added_volume_mm3=added,delta_below_grip_mm3=lower,unchanged_floor_and_slide_lands=True,delta_rear_region_mm3=aft,rear_region_start_y_mm=rear,
  delta_outside_exact_top_cutters_mm3=outside,front_grip_width_mm=2*s,front_grip_approx_depth_mm=hf-hb,front_grip_centre_x_mm=xmid,
  front_topology_contour_probe_max_deviation_mm=worst,analytic_profile_type='closed bounded BRep; exact tangent piecewise Bezier curves on ruled trimming surfaces',
  side_front_top_mm=h0,side_legacy_top_mm=side_z,side_geometry_probe_count=len(yz)*2,
  limitations=['Closed side walls; no perforating windows','No slicer, physical print, ergonomic validation, load, or anti-lift certification','Functional rear CAD contact geometry unchanged in measured region; final installed tray should be checked empty.'])
 (out/'V18_B_Wave_Validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 if (out/'Wave_Drawer.FCStd').exists(): (out/'Wave_Drawer.FCStd').unlink()
 doc=App.newDocument('V18WaveEditable')
 try:
  for name,label,shape,vis in [('Baseline','V18 exact baseline',src,False),('FrontCurveCutter','Parametric Bezier wave cutter',cutter_front,False),('SideCurveLeft','Left gradual side cutter',side_a,False),('SideCurveRight','Right gradual side cutter',side_b,False),('WaveDrawer','V18 B finished closed drawer',sh,True)]:
   p=doc.addObject('Part::Feature',name);p.Label=label;p.Shape=shape;p.Visibility=vis
  table=doc.addObject('Spreadsheet::Sheet','RegenerationInputs')
  table.set('A1','Parameter input source: edit wave_params.json and rerun build_wave_tray.py')
  for i,(k,v) in enumerate(q.items(),2):
   table.set(f'A{i}',k);table.set(f'B{i}',str(v))
  doc.recompute();doc.saveAs(str(out/'Wave_Drawer.FCStd'))
 finally:App.closeDocument(doc.Name)
 print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,default=R/'wave_params.json');ap.add_argument('--out',type=Path,default=R);a=ap.parse_args();make(a.config,a.out)
