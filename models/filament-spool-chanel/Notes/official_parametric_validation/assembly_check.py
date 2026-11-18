import cadquery as cq,json,time
from pathlib import Path
D=Path(__file__).parent;w=cq.importers.importBrep(str(D/'wide_nominal_full.brep')).val();n=cq.importers.importBrep(str(D/'narrow_full.brep')).val();rows=[]
def place(h,a):return n.rotate((0,0,0),(1,0,0),180).rotate((0,0,0),(0,0,1),a).translate((0,0,h))
for h,a in [(72,45),(70,45),(68,45),(66.4,45),(66.4,30),(66.4,15),(66.4,8),(66.4,5),(66.4,3),(66.4,1),(66.4,0),(66.5,0),(66.3,0)]:
 t=time.time();c=w.intersect(place(h,a));row={'H':h,'angle':a,'valid':c.isValid(),'volume':sum(s.Volume() for s in c.Solids()),'seconds':time.time()-t};rows.append(row);print(row,flush=True);(D/'assembly_poses.json').write_text(json.dumps(rows,indent=2))
