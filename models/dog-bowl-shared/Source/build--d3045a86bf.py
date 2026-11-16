import bpy, math
from mathutils import Vector
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
out='/Users/miaozhuang/Documents/dog-bowl-concepts/'
def mat(n,c,metal=0):
 m=bpy.data.materials.new(n); m.diffuse_color=(*c,1); m.use_nodes=True; p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*c,1); p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=.32; return m
brown=mat('LV brown',(.16,.067,.034)); cream=mat('Cream',(.72,.55,.37)); black=mat('Chanel black',(.035,.03,.028)); gold=mat('Gold',(.65,.39,.10),.65); white=mat('Backdrop',(.76,.72,.68))
def bowl(cx,m):
 N=128; verts=[]; faces=[]
 # Each ring is (height, half width); 3mm rim and bottom, 150 mm nominal width
 rings=[(0,32),(2,48),(8,56),(20,64),(40,70),(60,75),(60,72),(40,67),(20,61),(8,53),(4,44),(3,30)]
 for z,r in rings:
  for i in range(N):
   t=2*math.pi*i/N; c=math.cos(t); s=math.sin(t); e=2/2.6
   verts.append((cx+r*math.copysign(abs(c)**e,c),r*math.copysign(abs(s)**e,s),z))
 for j in range(len(rings)-1):
  for i in range(N): a=j*N+i;b=j*N+(i+1)%N;faces.append((a,b,b+N,a+N))
 faces.append(tuple(reversed(tuple(range(N))))); faces.append(tuple((len(rings)-1)*N+i for i in range(N)))
 mesh=bpy.data.meshes.new('bowl shell');mesh.from_pydata(verts,[],faces);mesh.update(); obj=bpy.data.objects.new('Bowl shell',mesh);bpy.context.collection.objects.link(obj);obj.data.materials.append(m)
 for p in mesh.polygons:p.use_smooth=True
 # mounting block conceptual, not a verified clip
 bpy.ops.mesh.primitive_cube_add(size=1,location=(cx,74,43)); o=bpy.context.object;o.name='Mount placeholder 70x8.5x30';o.dimensions=(70,8.5,30);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);mod=o.modifiers.new('Rounded','BEVEL');mod.width=2;mod.segments=3;o.modifiers.new('Normals','WEIGHTED_NORMAL')
def text(body,x,y,z,size,material):
 bpy.ops.object.text_add(location=(x,y,z),rotation=(math.pi/2,0,0));o=bpy.context.object;o.data.body=body;o.data.align_x='CENTER';o.data.align_y='CENTER';o.data.size=size;o.data.extrude=.6;o.data.bevel_depth=.15;o.data.materials.append(material)
def line(a,b,r,m):
 d=Vector(b)-Vector(a); mid=(Vector(a)+Vector(b))/2;bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=r,depth=d.length,location=mid);o=bpy.context.object;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();o.data.materials.append(m)
bowl(-92,brown);bowl(92,black)
# simplified relief decoration, placed at front; this remains a concept preview
text('LV',-92,-72.2,34,22,cream)
for dx in [-48,-25,25,48]:
 for z in [20,43]:
  y=-math.sqrt(max(0,1-(abs(dx)/78)**3))*70
  for ang in [0,math.pi/2]:
   x=-92+dx; line((x-4*math.cos(ang),y-1,z-4*math.sin(ang)),(x+4*math.cos(ang),y-1,z+4*math.sin(ang)),1.0,cream)
# visible front quilt diamonds on near-flat central front
for dx in range(-48,49,16):
 for z in (20,36,52):
  x=92+dx;y=-70*math.sqrt(max(0.2,1-(abs(dx)/83)**3))-0.4
  for a,b in [((x-7,y,z),(x,y-1,z+7)),((x,y-1,z+7),(x+7,y,z)),((x+7,y,z),(x,y-1,z-7)),((x,y-1,z-7),(x-7,y,z))]:line(a,b,.65,cream)
text('CC',92,-73,35,20,gold)
# backdrop
bpy.ops.mesh.primitive_plane_add(size=2000,location=(0,0,-1));bpy.context.object.data.materials.append(white)
world=bpy.context.scene.world; world.color=(.35,.35,.35)
def area(loc,power,size):
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,25))-o.location).to_track_quat('-Z','Y').to_euler()
area((0,-200,300),1800000,250);area((-200,80,180),900000,200)
bpy.ops.object.camera_add(location=(0,-440,290));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,24))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=400;bpy.context.scene.camera=cam
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=24;s.render.resolution_x=1600;s.render.resolution_y=900;s.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=out+'dog_bowl_concepts.blend');s.render.filepath=out+'dog_bowl_preview.png';bpy.ops.render.render(write_still=True)
