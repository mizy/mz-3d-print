import bpy, bmesh, os
base=os.path.dirname(os.path.abspath(__file__)); kind=os.environ['BOWL_KIND']
bpy.ops.wm.open_mainfile(filepath=os.path.join(base,kind+'_concept.blend'))
names=[kind,'Lock plate','Lock cap','Rivet','Corner guard','LV hallmark','Double C','UNVERIFIED rear connector bridge','UNVERIFIED rear connector stem']
parts=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(o.name==n or o.name.startswith(n+'.') for n in names)]
bpy.ops.object.select_all(action='DESELECT')
for obj in parts:
    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();obj.select_set(True)
body=bpy.data.objects[kind];bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
body.data.remesh_voxel_size=.35
bpy.ops.object.voxel_remesh()
for f in body.data.polygons:f.use_smooth=True
bpy.ops.wm.stl_export(filepath=os.path.join(base,kind+'_voxel_experiment_unverified.stl'),export_selected_objects=True)
print('EXPERIMENT FINISHED',len(body.data.vertices),len(body.data.polygons),flush=True)
