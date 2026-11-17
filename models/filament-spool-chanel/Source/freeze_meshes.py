from pathlib import Path
import sys,json,hashlib,numpy as np
R=Path(__file__).parent;sys.path.insert(0,str(R/'deps'))
import trimesh,manifold3d as md
out={}
for k in ['wide','narrow']:
 p=R/f'CHANEL_SOURCE21_{k}.obj';src=trimesh.load(p,process=False);c=src.split(only_watertight=False,repair=False);keep=[x for x in c if abs(x.volume)>1e-7];assert len(keep)==1
 m=keep[0];assert m.is_watertight and m.is_winding_consistent
 mm=md.Manifold(md.Mesh64(np.array(m.vertices,dtype=np.float64,order='C',copy=True),np.array(m.faces,dtype=np.uint64,order='C',copy=True)));assert str(mm.status())=='Error.NoError'
 mm=mm.simplify(1e-6);q=mm.to_mesh64();v=trimesh.Trimesh(q.vert_properties,q.tri_verts,process=False)
 e,n=np.unique(v.edges_sorted,axis=0,return_counts=True);assert (n==2).all() and v.is_watertight and v.is_winding_consistent and len(v.split(only_watertight=False,repair=False))==1
 f=R/f'CHANEL_SOURCE21_{k}_FROZEN.obj';v.export(f,digits=15);vr=trimesh.load(f,process=False);assert vr.is_watertight
 out[k]={'volume_mm3':float(v.volume),'solid_mass_g_at_density1_37':float(v.volume*.00137),'volume_delta_cleanup_mm3':float(v.volume-src.volume),'removed_zero_volume_components':len(c)-1,'simplification_tolerance_mm':1e-6,'min_triangle_area_mm2':float(v.area_faces.min()),'faces':len(v.faces),'non_two_face_edges':int((n!=2).sum()),'components':1,'bounds_mm':v.bounds.tolist(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()};print(k,out[k],flush=True)
out['total_solid_mass_g']=sum(v['solid_mass_g_at_density1_37'] for v in out.values());(R/'FROZEN_VALIDATION.json').write_text(json.dumps(out,indent=2))
