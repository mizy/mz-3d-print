import numpy as np,trimesh,json,xml.etree.ElementTree as E
from pathlib import Path
from shapely.geometry import LineString
from shapely.ops import unary_union
D=Path('/tmp/chanel_105g_preprint');r=E.fromstring((D/'studio_mesh.xml').read_bytes());ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'};m=r.find('.//m:mesh',ns);v=np.array([[float(x.attrib[k]) for k in ['x','y','z']] for x in m.find('m:vertices',ns)]);f=np.array([[int(x.attrib[k]) for k in ['v1','v2','v3']] for x in m.find('m:triangles',ns)]);a=trimesh.Trimesh(v,f,process=False);p=np.load(D/'wide_studio_seam_repaired.npz');b=trimesh.Trimesh(p['vertices'],p['faces'],process=False);rows=[]
for z in [31.275,32.4,32.45,32.6,33.,33.675,34.1,34.5,35.,35.425,35.9,36.1,36.2,36.825,37.225]:
 curves=[]
 for mm in [a,b]:
  seg=trimesh.intersections.mesh_plane(mm,[0,0,1],[0,0,z-20.3575287]);seg=seg[np.linalg.norm(seg[:,:,:2],axis=2).max(axis=1)<32.5];curves.append(unary_union([LineString(s[:,:2]) for s in seg]))
 err=curves[0].hausdorff_distance(curves[1]);rows.append({'z':z,'hausdorff_mm':err});print(z,err,flush=True)
b.export(D/'wide_studio_seam_repaired.stl');c=trimesh.load(D/'wide_studio_seam_repaired.stl',process=True);counts=np.bincount(c.edges_unique_inverse)
out={'section_comparisons':rows,'max_selected_section_difference_mm':max(x['hausdorff_mm'] for x in rows),'repaired_mesh_volume':b.volume,'original_mesh_volume':a.volume,'repaired_body_count':b.body_count,'repaired_watertight':b.is_watertight,'repaired_winding':b.is_winding_consistent,'binary_STL_roundtrip':{'watertight':c.is_watertight,'winding':c.is_winding_consistent,'boundary':int(sum(counts==1)),'nonmanifold':int(sum(counts>2)),'faces':len(c.faces),'volume':c.volume}}
(D/'repair_independent_checks.json').write_text(json.dumps(out,indent=2));print(out,flush=True)
