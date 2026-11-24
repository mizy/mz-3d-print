"""Original parametric workstation organizer. Analytic BREP, not mesh-converted STEP."""
from pathlib import Path
import json
from OCP.gp import gp_Pnt, gp_Vec, gp_Trsf
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.STEPControl import STEPControl_Writer, STEPControl_Reader, STEPControl_AsIs
from OCP.IFSelect import IFSelect_RetDone
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.TopoDS import TopoDS_Compound
from OCP.BRep import BRep_Builder
ROOT=Path(__file__).resolve().parents[1]
p=json.loads((ROOT/'Source/parameters.json').read_text())
out=ROOT/'Models'; out.mkdir(exist_ok=True)
cx,cy=p['cell_x'],p['cell_y']; wall=p['base_web']; gap=p['clearance_per_side']; floor=p['floor']; bw=p['bin_wall']
ix,iy=cx-2*gap,cy-2*gap

def box(x,y,z,dx,dy,dz):return BRepPrimAPI_MakeBox(gp_Pnt(x,y,z),dx,dy,dz).Shape()
def move(s,x,y,z):
 t=gp_Trsf();t.SetTranslation(gp_Vec(x,y,z));return BRepBuilderAPI_Transform(s,t,True).Shape()
def cut(s,t):return BRepAlgoAPI_Cut(s,t).Shape()
def fuse(s,t):return BRepAlgoAPI_Fuse(s,t).Shape()
def cup(h,dividers=0):
 s=box(0,0,0,ix,iy,h)
 w=(ix-2*bw-dividers*bw)/(dividers+1)
 for i in range(dividers+1):s=cut(s,box(bw+i*(w+bw),bw,floor,w,iy-2*bw,h))
 return s
# 3x2 removable modules, generous straight-sided sockets; no proprietary interface.
W=3*cx+4*wall;D=2*cy+3*wall
base=box(0,0,0,W,D,p['base_height'])
for row in range(2):
 for col in range(3):base=cut(base,box(wall+col*(cx+wall),wall+row*(cy+wall),floor,cx,cy,p['base_height']))
nozzle=box(0,0,0,ix,iy,p['nozzle_block_height'])
for j in range(3):
 for i in range(5):
  cyl=BRepPrimAPI_MakeCylinder(p['nozzle_pocket_d']/2,p['nozzle_block_height']).Shape()
  nozzle=cut(nozzle,move(cyl,12+i*(ix-24)/4,12+j*(iy-24)/2,floor))
shapes={'01_base':base,'02_small_parts':cup(22,1),'03_nozzle_pockets':nozzle,'04_open_tray':cup(22),'05_tool_cup':cup(65,1),'06_glue_cup':cup(50),'07_precision_tools':cup(58,3)}
report={}
def export(name,s):
 assert BRepCheck_Analyzer(s).IsValid(), name
 e=TopExp_Explorer(s,TopAbs_SOLID);n=0
 while e.More():n+=1;e.Next()
 assert n==1,(name,n)
 writer=STEPControl_Writer();writer.Transfer(s,STEPControl_AsIs);assert writer.Write(str(out/(name+'.step')))==IFSelect_RetDone
 reader=STEPControl_Reader();assert reader.ReadFile(str(out/(name+'.step')))==IFSelect_RetDone;reader.TransferRoots();assert BRepCheck_Analyzer(reader.OneShape()).IsValid()
 b=Bnd_Box();BRepBndLib.Add_s(s,b);bounds=b.Get();props=GProp_GProps();BRepGProp.VolumeProperties_s(s,props)
 report[name]={'valid':True,'solids':n,'bbox_mm':[round(bounds[k+3]-bounds[k],3) for k in range(3)],'solid_volume_mm3':round(props.Mass(),2)}
for name,s in shapes.items():export(name,s)
compound=TopoDS_Compound();builder=BRep_Builder();builder.MakeCompound(compound);builder.Add(compound,base)
for k,(name,s) in enumerate(list(shapes.items())[1:]):
 row=k//3;col=k%3;builder.Add(compound,move(s,wall+col*(cx+wall)+gap,wall+row*(cy+wall)+gap,floor))
w=STEPControl_Writer();w.Transfer(compound,STEPControl_AsIs);w.Write(str(out/'ASSEMBLY_REFERENCE_NOT_FOR_SINGLE_PART_PRINT.step'))
(ROOT/'validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
