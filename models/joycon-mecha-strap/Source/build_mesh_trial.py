"""Mesh-only trial fallback. NOT parametric BREP. No slicer invocation.
Run: uv run --with trimesh --with manifold3d --with numpy --with shapely --with mapbox-earcut --with networkx python Source/build_mesh_trial.py
"""
from pathlib import Path
import json,trimesh,numpy as np
from shapely.geometry import Polygon
root=Path(__file__).resolve().parents[1]
p=json.loads((root/'Source/parameters.json').read_text());out=root/'MeshTrial';out.mkdir(exist_ok=True)
def clean(m):
 m.merge_vertices(digits_vertex=4);m.update_faces(m.unique_faces());m.update_faces(m.nondegenerate_faces());m.remove_unreferenced_vertices();return m
base_input=trimesh.load(root/'Reference/Strap Body.stl',force='mesh');components=base_input.split()
assert len(components)==2 and all(x.is_watertight for x in components)
base=clean(trimesh.boolean.union(list(components),engine='manifold'))
assert base.is_watertight
poly=[(15,5),(20,8.5),(34,8.5),(39,7.6),(63,7.6),(68,8.5),(83,8.5),(88,5),(80,4.4),(22,4.4)]
stripe=[(20,5),(31,5),(37,6),(64,6),(70,5),(83,5),(81,5.8),(70,5.8),(64,6.8),(37,6.8),(31,5.8),(21,5.8)]
def prism(poly,y,d):
 m=trimesh.creation.extrude_polygon(Polygon(poly),abs(d),engine='earcut');v=m.vertices.copy();m.vertices=np.c_[v[:,0],y+v[:,2]*np.sign(d),v[:,1]]
 if m.volume<0:m.invert()
 return m
panels=[];stripes=[]
for y,d in [(-13.8-p['panel_outset'],p['panel_outset']+p['bond_overlap']),(p['panel_outset'],-p['panel_outset']-p['bond_overlap'])]:
 panels.append(prism(poly,y,d));stripes.append(prism(stripe,y,d))
body=clean(trimesh.boolean.union([base]+panels+stripes,engine='manifold'))
assert body.is_watertight and body.is_winding_consistent and len(body.split())==1
body.export(out/'BODY_SINGLE_SOLID_MESH_TRIAL.stl')
# Keep color bodies as a non-overlapping partition; no slicer/print profile.
cyan=clean(trimesh.boolean.union(stripes,engine='manifold'));gray=clean(trimesh.boolean.difference([body,cyan],engine='manifold'))
for name,m in [('BODY_GRAPHITE_MESH_TRIAL',gray),('INLAYS_CYAN_MESH_TRIAL',cyan)]:
 assert m.is_watertight;m.export(out/(name+'.stl'))
button=trimesh.load(root/'Reference/Button.stl',force='mesh');assert button.is_watertight
# Original button shape only rigidly placed with its longest faces on the plate.
button.vertices-=button.bounds[0];button.export(out/'BUTTON_ORIGINAL_PRINT_TWO.stl')
# Export/reload test at the same 0.0001 mm merge precision.
r=clean(trimesh.load(out/'BODY_SINGLE_SOLID_MESH_TRIAL.stl',force='mesh'))
assert r.is_watertight and len(r.split())==1
report={'status':'mesh topology checked; NOT physical fit verified; NOT parametric STEP','source_components':2,'body_watertight':bool(r.is_watertight),'body_connected_components':len(r.split()),'body_volume_mm3':float(r.volume),'reference_mesh_union_volume_mm3':float(base.volume),'added_exterior_volume_mm3':float(r.volume-base.volume),'body_extents_mm':r.extents.tolist(),'mesh_vertex_merge_digits':4,'maximum_vertex_merge_grid_mm':0.0001,'source_functional_geometry':'original author mesh, no scaling or feature redesign; Boolean union and 0.0001 mm vertex merge','button':'original author mesh, translation only; print two; no travel or spring test','slicing_performed':False,'color_partition_volume_error_mm3':float(gray.volume+cyan.volume-body.volume),'cad_source_unchanged':True}
(out/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
