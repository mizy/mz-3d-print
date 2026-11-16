import bpy,bmesh,os
p=os.path.dirname(os.path.abspath(__file__)); bpy.ops.wm.open_mainfile(filepath=os.path.join(p,'chanel_concept.blend'))
for obj in bpy.context.scene.objects:
 if obj.type!='MESH' or obj.name in ('Plane',): continue
 bm=bmesh.new();bm.from_mesh(obj.data)
 print(obj.name,'verts',len(bm.verts),'edges_nonmanifold',sum(not e.is_manifold for e in bm.edges),'faces',len(bm.faces),'volume',bm.calc_volume(signed=True),flush=True)
 bm.free()
