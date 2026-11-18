import cadquery as cq,json,time
from pathlib import Path
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
D=Path('/tmp/chanel_assembly_v6');H=66.430113973;cw=(-.0273430863,.0010603425);cn=(.0015810415,-.0274228517)
w=cq.importers.importBrep('/tmp/chanel_compact_v6/wide_analytic_base.brep').val();n=cq.importers.importBrep('/tmp/chanel_compact_v6/narrow_analytic_base.brep').val();rows=[]
for h,theta in [(H,40),(H,30),(H,20),(H+2,51),(H+4,51)]:
 t=time.time();s=n.translate((-cn[0],-cn[1],0)).rotate((0,0,0),(1,0,0),180).rotate((0,0,0),(0,0,1),theta).translate((cw[0],cw[1],h));common=w.intersect(s);vol=sum(x.Volume() for x in common.Solids());print('INTERSECTION_DONE',h,theta,'volume',vol,'elapsed',time.time()-t,flush=True)
 row={'H':h,'theta_deg':theta,'intersection_valid':common.isValid(),'intersection_solids':len(common.Solids()),'intersection_volume_mm3':vol,'minimum_surface_distance_mm':None,'elapsed_seconds':time.time()-t};rows.append(row);print(row,flush=True);(D/'exact_pipe_path_poses.json').write_text(json.dumps(rows,indent=2))
