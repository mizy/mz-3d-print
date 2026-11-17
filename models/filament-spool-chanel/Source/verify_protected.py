"""Run only against explicitly frozen candidate inputs. No source modification."""
from pathlib import Path
import sys,json,hashlib,argparse
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'deps'),str(ROOT/'deps')]
import trimesh,numpy as np
import manifold3d as md
p=argparse.ArgumentParser();p.add_argument('--wide',required=True);p.add_argument('--narrow',required=True);p.add_argument('--out',required=True);args=p.parse_args()
def cyl(r,z0,z1):
 m=trimesh.creation.cylinder(radius=r,height=z1-z0,sections=360);m.apply_translation([0,0,(z0+z1)/2]);return m
def mf(m):
 out=md.Manifold(md.Mesh64(np.array(m.vertices,dtype=np.float64,order='C',copy=True),np.array(m.faces,dtype=np.uint64,order='C',copy=True)))
 assert out.status()==md.Error.NoError, str(out.status())
 return out
def mesh(m):
 assert m.status()==md.Error.NoError,str(m.status())
 q=m.to_mesh64();return trimesh.Trimesh(vertices=np.asarray(q.vert_properties)[:,:3],faces=np.asarray(q.tri_verts),process=False)
def op(a,b,kind):
 a,b=mf(a),mf(b)
 return mesh(a+b if kind=='union' else a-b if kind=='difference' else a^b)
def union_all(parts):
 out=mf(parts[0])
 for part in parts[1:]:out=out+mf(part)
 return mesh(out)
def volume(m):return float(abs(m.volume)) if len(m.faces) else 0.
def compare(source,new,mask):
 a=op(source,mask,'intersection');b=op(new,mask,'intersection')
 removed=op(a,b,'difference');added=op(b,a,'difference')
 return {'source_region_mm3':volume(a),'candidate_region_mm3':volume(b),'removed_mm3':volume(removed),'added_mm3':volume(added),'added_bounds_mm':added.bounds.tolist() if len(added.faces) else None,'removed_bounds_mm':removed.bounds.tolist() if len(removed.faces) else None}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
features=json.loads((ROOT/'features.json').read_text())
audit=json.loads((ROOT/'source_audit.json').read_text())
result={'method':'Manifold Mesh64/to_mesh64 Boolean difference on repaired source union; finite polygon masks. Numerical volumes are not formal geometric proof; zero result must also be interpreted with import precision.','parts':{}}
for k in ['wide','narrow']:
 srcp=ROOT/f'official_{k}_stitched.stl';newp=Path(getattr(args,k))
 src=trimesh.load(srcp);parts=src.split();assert len(parts)==3 and all(m.is_volume for m in parts)
 src=union_all(parts);new=trimesh.load(newp,process=False)
 z=22.001 if k=='wide' else 24.001;r=39.0 if k=='wide' else 37.6
 d={'source_stitched_sha256':sha(srcp),'candidate_sha256':sha(newp),'candidate_is_volume':bool(new.is_volume),'regions':{}}
 masks={'inner_lock_protection':cyl(r,z,50),'whole_top_protection':cyl(44,z,50),'outside_lower_wall_band':op(cyl(44,3.5,z),cyl(40.1,3.4,z+.1),'difference'),'outside_rolling_band':op(cyl(103,-.1,5),cyl(99.1,-1,6),'difference')}
 if k=='wide':
  m=trimesh.creation.box([6,3,8.1]);m.apply_translation([0,42.5,4]);masks['paper_core_key_and_root_r43_9']=op(m,cyl(43.9,-.1,8.1),'intersection')
 # Feature centers were expressed relative to raw XY box center, same normalization as parent.
 for i,h in enumerate(features[audit[k]['source']]['retention_holes_z1_5']):
  mask=cyl(1.85,-.1,5);mask.apply_translation([*h['center_xy_mm'],0]);masks[f'retention_hole_{i+1}_surround']=mask
 for name,mask in masks.items():
  d['regions'][name]=compare(src,new,mask);print(k,name,d['regions'][name],flush=True)
 result['parts'][k]=d
 Path(args.out).write_text(json.dumps(result,indent=2))
