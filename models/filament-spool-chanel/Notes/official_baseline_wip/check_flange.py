from official_flange import *
from official_key import build_key
import trimesh,numpy as np,json
from shapely.geometry import LineString,Point
from shapely.ops import unary_union,polygonize
from pathlib import Path
D=Path(__file__).parent
def area(m,z):
 seg=trimesh.intersections.mesh_plane(m,[0,0,1],[0,0,z]);polys=list(polygonize(unary_union([LineString(np.round(s[:,:2],7)) for s in seg])));# Choose material by parity of nested boundaries using symmetric difference.
 boundaries=[]
 for po in polys:
  boundaries.append(po.exterior)
 shapes=[]
 # polygonize returns each bounded region; test odd ray incidence on original segment soup.
 for po in polys:
  pt=po.representative_point();x,y=pt.x,pt.y;hits=0
  for s in seg:
   a,b=s[:,:2]
   if (a[1]>y)!=(b[1]>y):
    xx=a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1]);hits+=xx>x
  if hits%2:shapes.append(po)
 return unary_union(shapes)
report={};mask=Point(0,0).buffer(110,quad_segs=256).difference(Point(0,0).buffer(45,quad_segs=256))
for part in ['wide','narrow']:
 ref=trimesh.load('/Users/miaozhuang/Downloads/bambulab_spool_'+part+'.stl');v=ref.vertices.copy();ref.vertices=np.c_[v[:,1],-v[:,2] if part=='wide' else v[:,2],ref.bounds[1,0]-v[:,0] if part=='wide' else v[:,0]-ref.bounds[0,0]];s=build_flange(part);s=s.fuse(build_key()).clean() if part=='wide' else s;v,f=s.tessellate(.001,.02);m=trimesh.Trimesh([[a.x,a.y,a.z] for a in v],f,process=True);rows=[]
 for z in [.2,1.,2.4,2.6,2.8,3.2,3.4]:
  a=area(ref,z).intersection(mask);b=area(m,z).intersection(mask);rows.append({'z':z,'symmetric_difference_mm2':a.symmetric_difference(b).area,'boundary_hausdorff_mm':a.boundary.hausdorff_distance(b.boundary),'official_area':a.area,'CAD_area':b.area})
 innerrows=[]
 for z in [.2,1.,2.4,2.6]:
  clip=Point(0,0).buffer(45,quad_segs=256);a=area(ref,z).intersection(clip);b=area(m,z).intersection(clip);innerrows.append({'z':z,'symmetric_difference_mm2':a.symmetric_difference(b).area,'boundary_hausdorff_mm':a.boundary.hausdorff_distance(b.boundary)})
 report[part]={'outer':rows,'support_base':innerrows};print(part,report[part],flush=True)
variants=[]
for name,changes in [('outer_plus1',{'outer_radius':101.,'rim_inner_at_plate':92.7,'rim_inner_top':93.8,'line_hole_pitch_radius':97.}),('hole_plus02',{'line_hole_radius':1.95}),('bore_plus02',{'bore_radius':27.7})]:
 p={**DEFAULT,**changes};s=build_flange('wide',p);variants.append({'name':name,'changes':changes,'valid':s.isValid(),'solids':len(s.Solids()),'volume':s.Volume(),'bbox_x':s.BoundingBox().xlen})
report['variants']=variants;report['passed']=all(row['boundary_hausdorff_mm']<.02 for part in ['wide','narrow'] for group in ['outer','support_base'] for row in report[part][group]);assert report['passed'], 'Flange section regression exceeded .02mm';(D/'flange_section_validation.json').write_text(json.dumps(report,indent=2))
