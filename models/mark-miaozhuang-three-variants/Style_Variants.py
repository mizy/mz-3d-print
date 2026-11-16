import sys
from pathlib import Path
sys.path[:0]=['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod','/usr/share/freecad/Mod/PartDesign','/usr/share/freecad/Mod/Sketcher']
import FreeCAD as App,FreeCADGui as Gui,Part
ROOT=Path(__file__).resolve().parent
Gui.showMainWindow()
import ImportGui
base=(.83,.81,.74);seal=(.59,.26,.18);handle=(.26,.17,.11);dark=(.22,.25,.25);platform=(.73,.75,.68);cols=[(.357,.376,.376),(.188,.204,.220),(.384,.506,.247)]
for slug,n in [('01_Intaglio_Stamp','StampFinal'),('02_Raised_Logo_Plaque','PlaqueFinal'),('03_Figurine_Display_Base','DisplayBaseFinal')]:
 d=App.openDocument(str(ROOT/(slug+'.FCStd')));d.recompute();o=d.getObject(n)
 colors=[]
 for f in o.Shape.Faces:
  p=f.CenterOfMass
  c=seal if slug.startswith('01') else base
  if slug.startswith('01') and p.z<0:c=handle
  if slug.startswith('02') or slug.startswith('03'):
   if slug.startswith('03'):
    if f.BoundBox.ZMax<=3.000001:c=dark
    elif f.BoundBox.ZMin>=15.79999 and (p.x**2+(p.y-19)**2)<2500.00001:c=platform
   for a,co in zip(['Right','Left','Sprout'],cols):
    part=d.getObject('Logo'+a)
    if part.Shape.isInside(p,1e-6,True):c=co
  colors.append(c)
 for ob in d.Objects:
  if hasattr(ob,'ViewObject') and ob.ViewObject:
   try:ob.ViewObject.Visibility=False
   except Exception:pass
 o.ViewObject.ShapeColor=base;o.ViewObject.DiffuseColor=colors;o.ViewObject.Visibility=True;o.ViewObject.DisplayMode='Flat Lines';o.ViewObject.LineColor=(.18,.20,.18);o.ViewObject.LineWidth=1.;o.ViewObject.Deviation=.06
 for a,co in zip(['Right','Left','Sprout'],cols):
  part=d.getObject('Logo'+a)
  if part:
   d.getObject('Logo'+a+'Pad').ViewObject.ShapeColor=co
 Gui.activeDocument().activeView().viewAxonometric();Gui.activeDocument().activeView().fitAll()
 d.recompute();d.save();ImportGui.export([o],str(ROOT/(slug+'.step')))
 print('Styled',slug,flush=True)
 App.closeDocument(d.Name)
