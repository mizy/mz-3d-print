import bpy,json,os,sys,math
from mathutils import Vector
R=os.path.dirname(__file__); mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'perspective'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=False;s.render.resolution_x=1000;s.render.resolution_y=800;s.render.resolution_percentage=100
s.world.color=(.8,.8,.8);s.view_settings.view_transform='AgX'
def mat(h):
 rgb=[int(h[i:i+2],16)/255 for i in (1,3,5)];rgb=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
 m=bpy.data.materials.new(h);m.diffuse_color=(*rgb,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=.42;return m
for p in json.load(open(R+'/manifest.json')):
 bpy.ops.wm.stl_import(filepath=R+'/'+p['file']);o=bpy.context.object;o.data.materials.append(mat(p['color']))
 for f in o.data.polygons:f.use_smooth=True
 mod=o.modifiers.new('Sharp','EDGE_SPLIT');mod.split_angle=.6
bpy.ops.mesh.primitive_plane_add(size=3000,location=(0,0,-.6));bpy.context.object.data.materials.append(mat('#eeeeeb'))
def area(loc,pow,size):
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=pow;o.data.size=size;o.rotation_euler=(Vector((0,0,30))-o.location).to_track_quat('-Z','Y').to_euler()
area((-200,-250,400),1500000,300);area((250,-50,280),600000,300);area((0,300,400),1200000,250)
look=(0,0,12) if mode!='clip' else (0,55,18)
loc={'perspective':(230,-360,180),'rear':(210,350,180),'front':(0,-400,15),'side':(400,0,15),'top':(0,0,450),'back':(0,400,15),'clip':(130,240,100)}[mode]
if mode=='top':look=(0,0,0)
bpy.ops.object.camera_add(location=loc);cam=bpy.context.object;cam.rotation_euler=(Vector(look)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=215 if mode!='clip' else 120;cam.data.clip_end=10000;s.camera=cam
s.render.image_settings.file_format='PNG';s.render.filepath=R+'/'+mode+'.png';bpy.ops.render.render(write_still=True)
