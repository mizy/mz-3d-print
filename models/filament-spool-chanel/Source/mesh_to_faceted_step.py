"""Write exact mesh geometry as ISO 10303 FACETED_BREP with planar faces.
Not tessellated visualization: STEP imports as a closed BRep solid. No vertex
movement or triangle reduction. Validate CAD kernel re-import before delivery.
"""
from pathlib import Path
import sys,json,time,hashlib,argparse
sys.path.insert(0,str(Path(__file__).resolve().parent/'deps'))
import numpy as np,trimesh

def num(v):
 s=format(float(v),'.17g').replace('e','E')
 if '.' not in s and 'E' not in s:s+='.'
 return s

def convert(src,dest,validate=True):
 t=time.time();m=trimesh.load(src,force='mesh',process=Path(src).suffix.lower()!='.obj')
 assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
 _,cnt=np.unique(m.edges_sorted,axis=0,return_counts=True);assert (cnt==2).all() and m.nondegenerate_faces(height=1e-10).all()
 v=np.asarray(m.vertices);f=np.asarray(m.faces);norm=np.asarray(m.face_normals);base=100+len(v)
 with open(dest,'w') as o:
  o.write("""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Exact mesh-derived faceted BRep, millimetres'),'2;1');
FILE_NAME('Spool half','2026-11-17T00:00:00',(''),(''),'Mesh-to-STEP','ISO 10303-214','');
FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));
ENDSEC;
DATA;
#1=APPLICATION_PROTOCOL_DEFINITION('international standard','automotive_design',2000,#2);
#2=APPLICATION_CONTEXT('core data for automotive mechanical design processes');
#3=SHAPE_DEFINITION_REPRESENTATION(#4,#10);
#4=PRODUCT_DEFINITION_SHAPE('','',#5);
#5=PRODUCT_DEFINITION('design','',#6,#9);
#6=PRODUCT_DEFINITION_FORMATION('','',#7);
#7=PRODUCT('Spool half','Spool half','',(#8));
#8=PRODUCT_CONTEXT('',#2,'mechanical');
#9=PRODUCT_DEFINITION_CONTEXT('part definition',#2,'design');
#10=FACETED_BREP_SHAPE_REPRESENTATION('',(#11,#15),#20);
#11=AXIS2_PLACEMENT_3D('',#12,#13,#14);
#12=CARTESIAN_POINT('',(0.,0.,0.));
#13=DIRECTION('',(0.,0.,1.));
#14=DIRECTION('',(1.,0.,0.));
#15=FACETED_BREP('Spool half',#16);
#20=(GEOMETRIC_REPRESENTATION_CONTEXT(3) GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#24)) GLOBAL_UNIT_ASSIGNED_CONTEXT((#21,#22,#23)) REPRESENTATION_CONTEXT('Context','3D'));
#21=(LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.));
#22=(NAMED_UNIT(*) PLANE_ANGLE_UNIT() SI_UNIT($,.RADIAN.));
#23=(NAMED_UNIT(*) SI_UNIT($,.STERADIAN.) SOLID_ANGLE_UNIT());
#24=UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-08),#21,'distance_accuracy_value','');
""")
  for i,p in enumerate(v):o.write(f"#{100+i}=CARTESIAN_POINT('',({','.join(map(num,p))}));\n")
  for i,tri in enumerate(f):
   a=base+7*i;x=v[tri[1]]-v[tri[0]]
   o.write(f"#{a}=FACE_SURFACE('',(#{a+1}),#{a+3},.T.);\n#{a+1}=FACE_OUTER_BOUND('',#{a+2},.T.);\n#{a+2}=POLY_LOOP('',({','.join('#'+str(100+j) for j in tri)}));\n#{a+3}=PLANE('',#{a+4});\n#{a+4}=AXIS2_PLACEMENT_3D('',#{100+tri[0]},#{a+5},#{a+6});\n#{a+5}=DIRECTION('',({','.join(map(num,norm[i]))}));\n#{a+6}=DIRECTION('',({','.join(map(num,x))}));\n")
  o.write("#16=CLOSED_SHELL('',(")
  for i in range(len(f)):
   if i:o.write(',')
   if i%20==0:o.write('\n')
   o.write('#'+str(base+7*i))
  o.write('));\nENDSEC;\nEND-ISO-10303-21;\n')
 report={'source':str(src),'output':str(dest),'mesh_faces':len(f),'mesh_vertices':len(v),'mesh_volume_mm3':float(m.volume),'vertex_relocation_mm':0,'representation':'FACETED_BREP, planar FACE_SURFACE, POLY_LOOP; not visualization-only tessellation','step_bytes':Path(dest).stat().st_size,'export_elapsed_s':time.time()-t,'source_sha256':hashlib.sha256(Path(src).read_bytes()).hexdigest()}
 print('EXPORTED',json.dumps(report),flush=True)
 if validate:
  import cadquery as cq
  print('REIMPORTING',flush=True);r=cq.importers.importStep(str(dest)).val();print('CHECKING',flush=True)
  vol=r.Volume();b=r.BoundingBox();bb=np.array([[b.xmin,b.ymin,b.zmin],[b.xmax,b.ymax,b.zmax]]);report.update(step_bounds_mm=bb.tolist(),max_bounds_difference_mm=float(np.max(np.abs(bb-m.bounds))),valid=r.isValid(),solids=len(r.Solids()),step_volume_mm3=vol,volume_difference_mm3=float(vol-m.volume),elapsed_s=time.time()-t)
  assert report['valid'] and report['solids']==1 and report['max_bounds_difference_mm']<1e-5 and abs(vol-m.volume)<max(1e-4,abs(m.volume)*1e-8),report
 Path(str(dest)+'.validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True);return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('dest');p.add_argument('--no-validate',action='store_true');a=p.parse_args();convert(a.source,a.dest,not a.no_validate)
