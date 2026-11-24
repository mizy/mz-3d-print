from pathlib import Path
import trimesh,numpy as np,json
root=Path(__file__).resolve().parents[1];out=root/'HeightLayerTrial/AssemblyCheck';out.mkdir(exist_ok=True)
def clean(m):
 m.merge_vertices(digits_vertex=4);m.update_faces(m.unique_faces());m.update_faces(m.nondegenerate_faces());m.remove_unreferenced_vertices();return m
body=clean(trimesh.load(root/'HeightLayerTrial/BODY_ALL_SINGLE_COLOR.stl',force='mesh'))
# Undo known print transform: X=x, Y=12.7-z, Z=y-ymin.
ymin=-13.804631233215331
v=body.vertices.copy();body.vertices=np.c_[v[:,0],v[:,2]+ymin,12.7-v[:,1]]
b=trimesh.load(root/'Reference/Button.stl',force='mesh');R=np.array([[1,0,0],[0,0,1],[0,-1,0]]);b.vertices=b.vertices@R
res={'coordinate_system':'original author body axes; press direction -Z, not print Z','pose_basis':'button broad cap up, circular actuator down; hole-axis centered X=33.25 or 74.35 and Y=-6.9, NOT verified seated rest position','scan':'button cap maximum Z from 7 to 16 mm, 0.25 mm steps; two positions; rigid parts','samples':{}}
for label,x in [('left',33.25),('right',74.35)]:
 rows=[]
 for h in np.arange(7,16.001,.25):
  q=b.copy();q.vertices+=np.array([x-q.bounds[:,0].mean(),-6.9-q.bounds[:,1].mean(),h-q.bounds[1,2]])
  inter=trimesh.boolean.intersection([body,q],engine='manifold');volume=float(abs(inter.volume)) if len(inter.faces) else 0.
  rows.append({'cap_top_z_mm':float(h),'intersection_mm3':volume})
  if h in [9.25,10,12.75,14]:q.export(out/f'{label}_button_capZ{h:.2f}_ANALYSIS_ONLY.stl')
 res['samples'][label]=rows;print(label,rows,flush=True)
body.export(out/'body_original_axes_ANALYSIS_ONLY.stl');(out/'press_scan.json').write_text(json.dumps(res,indent=2))
