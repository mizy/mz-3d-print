import sys,json,math
from pathlib import Path
sys.path[:0]=['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod']
import FreeCAD as App,Part
ROOT=Path(__file__).resolve().parent
specs=[('01_Intaglio_Stamp','StampFinal',{'LogoWidth':54,'RecessDepth':1.5},[70,54*512/383+16,40]),('02_Raised_Logo_Plaque','PlaqueFinal',{'LogoWidth':99,'ReliefHeight':6.5},[123,99*512/383+24,11.5]),('03_Figurine_Display_Base','DisplayBaseFinal',{'BaseDiameter':176,'PlatformDiameter':110,'BodyHeight':13.5},[176,176,20.5])]
reports=[]
for slug,n,params,want in specs:
 d=App.openDocument(str(ROOT/(slug+'.FCStd')));d.recompute();o=d.getObject(n);s=o.Shape
 imported=Part.Shape();imported.read(str(ROOT/(slug+'.step')))
 report={'file':slug,'source_valid':s.isValid(),'source_solid_count':len(s.Solids),'source_closed':s.isClosed(),'step_valid':imported.isValid(),'step_solid_count':len(imported.Solids),'step_closed':imported.isClosed(),'step_volume_relative_error':abs(imported.Volume-s.Volume)/s.Volume,'step_size_mm':[imported.BoundBox.XLength,imported.BoundBox.YLength,imported.BoundBox.ZLength]}
 assert s.isValid() and len(s.Solids)==1 and s.isClosed()
 assert imported.isValid() and len(imported.Solids)==1 and imported.isClosed()
 assert report['step_volume_relative_error']<1e-8
 olds={}
 for alias,val in params.items():
  cell=d.Parameters.getCellFromAlias(alias);olds[cell]=d.Parameters.getContents(cell);d.Parameters.set(cell,str(val)+' mm')
 d.recompute();b=o.Shape.optimalBoundingBox();actual=[b.XLength,b.YLength,b.ZLength]
 report['parameter_change_test']={'changes_mm':params,'expected_size_mm':want,'actual_size_mm':actual,'valid':o.Shape.isValid(),'solids':len(o.Shape.Solids)}
 assert o.Shape.isValid() and len(o.Shape.Solids)==1
 print(slug,actual,want,flush=True)
 assert all(abs(a-e)<.01 for a,e in zip(actual,want))
 for cell,val in olds.items():d.Parameters.set(cell,val)
 d.recompute()
 report['restored_valid']=o.Shape.isValid()
 if slug.startswith('01'):
  report['actual_cavity_volume_mm3']=d.StampPlate.Shape.Volume-d.RecessedPlate.Shape.Volume
  report['expected_cavity_volume_mm3']=sum(d.getObject('Mirrored'+a).Shape.Volume for a in ['Right','Left','Sprout'])/1.4*1.2
  report['horizontal_mirror_checked']=d.MirroredRightContour.Geometry[0].StartPoint.x==-27.5
  assert abs(report['actual_cavity_volume_mm3']-report['expected_cavity_volume_mm3'])<1e-5
 if slug.startswith('03'):
  report['logo_platform_intersection_mm3']=sum(d.FigurePlatform.Shape.common(d.getObject('Logo'+a).Shape).Volume for a in ['Right','Left','Sprout'])
  assert abs(report['logo_platform_intersection_mm3'])<1e-7
 reports.append(report);App.closeDocument(d.Name)
(ROOT/'validation_report.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2))
print(json.dumps(reports,ensure_ascii=False,indent=2))
