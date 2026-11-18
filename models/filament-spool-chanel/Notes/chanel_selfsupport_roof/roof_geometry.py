import cadquery as cq,math,json
from OCP.BRepAdaptor import BRepAdaptor_Surface
from pathlib import Path
D=Path(__file__).parent;rows=[]
for part in ['wide','narrow']:
 s=cq.importers.importBrep(str(D/'prototype'/(part+'.brep'))).val()
 for i,f in enumerate(s.Faces()):
  if f.geomType()=='CONE':
   c=BRepAdaptor_Surface(f.wrapped).Cone();a=math.degrees(c.SemiAngle());z=f.Center().z
   if abs(a-40)<.001:
    rows.append({'part':part,'face_index':i,'cone_semi_angle_deg':a,'slope_from_horizontal_deg':90-a,'area_mm2':f.Area(),'center_z_mm':z,'normal_z_sample':f.normalAt().z})
(D/'roof_analytic_faces.json').write_text(json.dumps(rows,indent=2));print('roof conical faces',len(rows));print(rows[:3])
