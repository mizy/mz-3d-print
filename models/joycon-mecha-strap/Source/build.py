"""Preserve CC BY source functional solids; only add separate external styling."""
from pathlib import Path
import json,hashlib
from OCP.STEPControl import STEPControl_Reader,STEPControl_Writer,STEPControl_AsIs
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID
from OCP.TopoDS import TopoDS_Compound
from OCP.BRep import BRep_Builder
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon,BRepBuilderAPI_MakeFace,BRepBuilderAPI_Transform
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut,BRepAlgoAPI_Common
from OCP.gp import gp_Pnt,gp_Vec,gp_Trsf
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.StlAPI import StlAPI_Writer
root=Path(__file__).resolve().parents[1];p=json.loads((root/'Source/parameters.json').read_text());ref=root/'Reference/Joy Con Strap.step'
r=STEPControl_Reader();r.ReadFile(str(ref));r.TransferRoots();e=TopExp_Explorer(r.OneShape(),TopAbs_SOLID);solids=[]
while e.More():solids.append(e.Current());e.Next()
assert len(solids)==4
# Source STL has body components matching STEP solids 3 and 2; solid 1 is a duplicate earlier body.
parts=[('reference_outer_body_UNCHANGED',solids[3]),('reference_rail_component_UNCHANGED',solids[2])]
def volume(s):
 q=GProp_GProps();BRepGProp.VolumeProperties_s(s,q);return q.Mass()
def prism(poly,y,d):
 q=BRepBuilderAPI_MakePolygon()
 for x,z in poly:q.Add(gp_Pnt(x,y,z))
 q.Close();return BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(q.Wire()).Face(),gp_Vec(0,d,0)).Shape()
# Cosmetic facets only outside the original side flats; bottom rail and top buttons/LED untouched.
for side,y,d in [('left',-13.8-p['panel_outset'],p['panel_outset']+p['bond_overlap']),('right',p['panel_outset'],-p['panel_outset']-p['bond_overlap'])]:
 panel=prism([(15,5),(20,8.5),(34,8.5),(39,7.6),(63,7.6),(68,8.5),(83,8.5),(88,5),(80,4.4),(22,4.4)],y,d)
 strip=prism([(20,5),(31,5),(37,6),(64,6),(70,5),(83,5),(81,5.8),(70,5.8),(64,6.8),(37,6.8),(31,5.8),(21,5.8)],y,d)
 panel=BRepAlgoAPI_Cut(panel,strip).Shape()
 parts.extend([(side+'_graphite_armor',panel),(side+'_cyan_inlay',strip)])
# Preserve STEP button geometry; display two print parts away from the body, not guessed seated positions.
for i,x in enumerate([-65,-42]):
 t=gp_Trsf();t.SetTranslation(gp_Vec(x,30,-23.11));parts.append((f'button_{i+1}_UNCHANGED_UNSEATED',BRepBuilderAPI_Transform(solids[0],t,True).Shape()))
comp=TopoDS_Compound();b=BRep_Builder();b.MakeCompound(comp);checks=[]
for name,s in parts:
 assert BRepCheck_Analyzer(s).IsValid(),name
 b.Add(comp,s);checks.append({'part':name,'valid':True,'volume_mm3':volume(s)})
w=STEPControl_Writer();w.Transfer(comp,STEPControl_AsIs);path=root/'Models/JOYCON_MECHA_REFERENCE_TRIAL.step';w.Write(str(path));rr=STEPControl_Reader();rr.ReadFile(str(path));rr.TransferRoots();assert BRepCheck_Analyzer(rr.OneShape()).IsValid()
# exact source objects reused, no subtraction or functional-dimensional edits
report={'status':'reference-based trial, NOT verified fit or retention','source_sha256':hashlib.sha256(ref.read_bytes()).hexdigest(),'body_source_solid_indices':[3,2],'button_source_solid_index':0,'functional_geometry_unchanged':True,'parts':checks,'source_body_components_not_fused':True,'button_positions':'separate print parts, not seated simulation','slicing_performed':False}
(root/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
# Analysis-only meshes stay outside project; not STEP source geometry.
for i,(name,s) in enumerate(parts):
 BRepMesh_IncrementalMesh(s,.06,False,.3,True);ww=StlAPI_Writer();ww.Write(s,f'/tmp/joycon-reference/final_{i}.stl')
