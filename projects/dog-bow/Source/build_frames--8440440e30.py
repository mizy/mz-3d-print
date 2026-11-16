from pathlib import Path
import cadquery as cq,json
R=Path(__file__).parent;src=R.parent/'fit_samples_2026-11-15'
r=78.;rear=53.;fc=-10.;corner=8.
w=cq.Workplane('XY',origin=(0,0,-1)).moveTo(-r,fc).lineTo(-r,rear-corner).radiusArc((-r+corner,rear),corner).lineTo(r-corner,rear).radiusArc((r,rear-corner),corner).lineTo(r,fc).threePointArc((0,fc-r),(-r,fc)).close().extrude(4).val()
slot=cq.Workplane('XY').box(66,4.5,4,centered=(True,True,False)).translate((0,62.25,-1)).val()
out=[]
for name in ['LV','Chanel']:
 s=cq.importers.importStep(str(src/(name+'_footprint_2mm.step'))).val();f=s.cut(w).cut(slot).clean();b=f.BoundingBox();ob=s.BoundingBox()
 assert f.isValid() and len(f.Solids())==1
 for ext in ['step','stl']:cq.exporters.export(f,str(R/(name+'_outline_2mm.'+ext)),tolerance=.02,angularTolerance=.08)
 out.append(dict(name=name,cad_valid=f.isValid(),solids=len(f.Solids()),height_mm=b.zlen,bounds_mm=[b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax],volume_mm3=f.Volume(),original_volume_mm3=s.Volume(),material_reduction_percent=100*(1-f.Volume()/s.Volume()),approx_solid_PLA_grams=f.Volume()/1000*1.24,outer_bounds_unchanged=all(abs(x-y)<.001 for x,y in zip([b.xmin,b.ymin,b.xmax,b.ymax],[ob.xmin,ob.ymin,ob.xmax,ob.ymax]))))
 print(out[-1],flush=True)
(R/'validation.json').write_text(json.dumps(out,indent=2))
