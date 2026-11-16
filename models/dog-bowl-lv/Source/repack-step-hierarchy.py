import cadquery as cq,json,hashlib
from pathlib import Path
from OCP.XCAFApp import XCAFApp_Application
from OCP.XCAFDoc import XCAFDoc_DocumentTool,XCAFDoc_ColorType
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.TopLoc import TopLoc_Location
from OCP.XSControl import XSControl_WorkSession
from OCP.Interface import Interface_Static
from OCP.STEPCAFControl import STEPCAFControl_Writer,STEPCAFControl_Reader
from OCP.STEPControl import STEPControl_AsIs
from OCP.IFSelect import IFSelect_RetDone
from OCP.Quantity import Quantity_Color,Quantity_TOC_RGB
from OCP.TDF import TDF_Label,TDF_LabelSequence
P=Path('/private/tmp/lv-hierarchy');SRC=Path('/Users/miaozhuang/projects/mz-3d-print/models/dog-bowl-lv/Models/LV_bowl_and_logo.step')
s=cq.importers.importStep(str(SRC)).val().Solids();assert len(s)==4
app=XCAFApp_Application.GetApplication_s();doc=TDocStd_Document(TCollection_ExtendedString('XmlOcaf'));app.InitDocument(doc)
t=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main());t.SetAutoNaming_s(False);ct=XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
def lab(name,shape=None,color=None):
 l=t.NewShape()
 if shape is not None:t.SetShape(l,cq.Compound.makeCompound([shape]).wrapped)
 TDataStd_Name.Set_s(l,TCollection_ExtendedString(name))
 if color:ct.SetColor(l,Quantity_Color(*color,Quantity_TOC_RGB),XCAFDoc_ColorType.XCAFDoc_ColorSurf)
 return l
root=lab('LV_bowl_and_logo');bowl=lab('Bowl');t.AddComponent(root,bowl,TopLoc_Location())
cols=[(.988,.925,.839),(.725,.851,.922),(.988,.925,.839),(.988,.925,.839)]
ns=['ivory_bottom_personal_mark','light_blue_body','ivory_rim','Logo_with_tenons']
for i,(n,o,c) in enumerate(zip(ns,s,cols)):
 child=lab(n,o,c);t.AddComponent(bowl if i<3 else root,child,TopLoc_Location())
t.UpdateAssemblies();w=STEPCAFControl_Writer(XSControl_WorkSession(),False);Interface_Static.SetCVal_s("write.step.schema","AP214IS");w.SetColorMode(True);w.SetNameMode(True);w.Transfer(doc,STEPControl_AsIs);assert w.Write(str(P/'LV_bowl_and_logo.step'))==IFSelect_RetDone
# Read XCAF actual tree, not filename or expected input structure.
def tree(path):
 d=TDocStd_Document(TCollection_ExtendedString('XmlOcaf'));app.InitDocument(d);r=STEPCAFControl_Reader();assert r.ReadFile(str(path))==IFSelect_RetDone;r.Transfer(d)
 st=XCAFDoc_DocumentTool.ShapeTool_s(d.Main());co=XCAFDoc_DocumentTool.ColorTool_s(d.Main());free=TDF_LabelSequence();st.GetFreeShapes(free)
 def node(l):
  if st.IsReference_s(l):
   ref=TDF_Label();st.GetReferredShape_s(l,ref);l=ref
  n=TDataStd_Name();name=n.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(),n) else '?'
  children=TDF_LabelSequence();st.GetComponents_s(l,children)
  c=Quantity_Color();colored=any(co.GetColor_s(l,k,c) for k in [XCAFDoc_ColorType.XCAFDoc_ColorGen,XCAFDoc_ColorType.XCAFDoc_ColorSurf,XCAFDoc_ColorType.XCAFDoc_ColorCurv])
  facecols=[]
  shape=cq.Shape.cast(st.GetShape_s(l))
  for face in shape.Faces():
   fc=Quantity_Color()
   if co.GetColor(face.wrapped,XCAFDoc_ColorType.XCAFDoc_ColorSurf,fc):facecols.append([fc.Red(),fc.Green(),fc.Blue()])
  return {'face_colors':sorted(set(tuple(c) for c in facecols)), 'name':name,'assembly':st.IsAssembly_s(l),'color':[c.Red(),c.Green(),c.Blue()] if colored else None,'children':[node(children.Value(i)) for i in range(1,children.Length()+1)]}
 return [node(free.Value(i)) for i in range(1,free.Length()+1)]
report={'before_original':tree(Path('/private/tmp/lv-tenon-step/LV_bowl_and_logo.step')),'before_marked':tree(SRC),'new':tree(P/'LV_bowl_and_logo.step')}
rt=cq.importers.importStep(str(P/'LV_bowl_and_logo.step')).val().Solids();assert len(rt)==4
report['geometry']=[{'valid':a.isValid(),'volume_mm3':a.Volume(),'source_volume_mm3':b.Volume(),'volume_difference_mm3':a.Volume()-b.Volume()} for a,b in zip(rt,s)]
assert all(x['valid'] and abs(x['volume_difference_mm3'])<1e-5 for x in report['geometry'])
(P/'hierarchy-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
