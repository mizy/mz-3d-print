import bpy, bmesh, os, sys
from mathutils import Vector
path=os.path.dirname(os.path.abspath(__file__))
kind=os.environ['BOWL_KIND']
bpy.ops.wm.open_mainfile(filepath=os.path.join(path,kind+'_concept.blend'))
body=bpy.data.objects[kind]
names=['Lock plate','Lock cap','Rivet','Double C','UNVERIFIED rear connector bridge','UNVERIFIED rear connector stem']
items=[o for o in bpy.context.scene.objects if any(o.name==n or o.name.startswith(n+'.') for n in names)]
for item in items:
    item_name=item.name
    if item_name.startswith('Double C'):
        bm=bmesh.new(); bm.from_mesh(item.data)
        bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(item.data);bm.free()
    bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
    mod=body.modifiers.new('Fuse '+item.name,'BOOLEAN');mod.operation='UNION';mod.solver='MANIFOLD';mod.object=item
    try:
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(item,do_unlink=True)
        print('FUSED',item_name,flush=True)
    except Exception as e:
        print('FUSION ERROR',repr(e),flush=True);sys.exit(1)
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.wm.stl_export(filepath=os.path.join(path,kind+'_candidate_unverified.stl'),export_selected_objects=True)
