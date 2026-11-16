import bpy,bmesh,os
p=os.path.dirname(os.path.abspath(__file__)); bpy.ops.wm.open_mainfile(filepath=os.path.join(p,'chanel_concept.blend'))
for obj in bpy.context.scene.objects:
 if obj.type!='MESH' or obj.name in ('Plane',): continue
 bm=bmesh.new();bm.from_mesh(obj.data)
 bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5); print('boundary before',sum(e.is_boundary for e in bm.edges)); bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0); print('boundary after',sum(e.is_boundary for e in bm.edges)); print(obj.name,'verts',len(bm.verts),'edges_nonmanifold',sum(not e.is_manifold for e in bm.edges),'faces',len(bm.faces),'volume',bm.calc_volume(signed=True),flush=True)
 bm.free()
