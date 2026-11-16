import bpy,json,math,sys
from mathutils import Vector,Matrix,Euler
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SLUGS=['01_Intaglio_Stamp','02_Raised_Logo_Plaque','03_Figurine_Display_Base']
def linear(c):return c/12.92 if c<.04045 else ((c+.055)/1.055)**2.4
def mat(n,c,rough=.3,metal=.04):
 m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=tuple(linear(a) for a in c)+(1,);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal;return m

def model(slug,offset=(0,0,0),tilt=0):
 items=json.loads((ROOT/(slug+'_mesh.json')).read_text());rot=Euler((tilt,0,0)).to_matrix()
 allv=[rot@Vector(v)*.001 for p in items for v in p['vertices']];minz=min(v.z for v in allv)
 for p in items:
  verts=[rot@Vector(v)*.001+Vector((offset[0],offset[1],offset[2]-minz)) for v in p['vertices']]
  me=bpy.data.meshes.new(p['name']);me.from_pydata(verts,[],p['faces']);me.update();o=bpy.data.objects.new(p['name'],me);bpy.context.collection.objects.link(o);o.data.materials.append(mat(p['name'],p['color'],.34 if slug.startswith('01') else .27))
  # Keep edges faithful to CAD. Smooth only cylindrical/conical side triangles.
  if p['name'] in ['Grip','Dark foot','Tapered ivory body','Upper deck','Display platform']:
   for f in me.polygons:
    n=rot.transposed()@f.normal
    f.use_smooth=abs(n.z)<.98
 return allv

def setup(overview=False):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=160;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=16
 scene.render.resolution_x=2800 if overview else 1800;scene.render.resolution_y=1550 if overview else 1600;scene.render.resolution_percentage=100
 scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
 world=bpy.data.worlds.new('Warm studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.82,.86,.91,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35;scene.world=world
 bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.00008));bpy.context.object.data.materials.append(mat('Warm matte ground',(.94,.93,.90),.65,0))
 def light(n,loc,power,size,col):
  ld=bpy.data.lights.new(n,'AREA');ld.energy=power;ld.shape='DISK';ld.size=size;ld.color=col;o=bpy.data.objects.new(n,ld);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
 if overview:
  light('Key',(-.25,-.24,.5),3.5,.35,(1,.95,.88));light('Fill',(.32,.18,.45),1.6,.4,(.84,.91,1));light('Strip',(.05,.30,.45),1.8,.25,(1,1,1))
 else:
  light('Key',(-.16,-.14,.3),.8,.16,(1,.96,.91));light('Fill',(.23,.1,.28),.35,.24,(.84,.91,1));light('Back',(-.02,.21,.35),.45,.15,(1,1,1))
 cd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',cd);bpy.context.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO'
 scene.unit_settings.system='METRIC';scene.unit_settings.length_unit='MILLIMETERS'
 return scene,cam

def camera(cam,loc,target,scale):
 cam.location=loc;z=(cam.location-Vector(target)).normalized();x=Vector((0,1,0)).cross(z).normalized();y=z.cross(x);cam.rotation_euler=Matrix((x,y,z)).transposed().to_euler();cam.data.ortho_scale=scale

for i,slug in enumerate(SLUGS):
 sc,cam=setup();tilt=math.radians(38) if i==0 else 0;model(slug,tilt=tilt)
 if i==0:camera(cam,(.10,-.21,.33),(0,0,.025),.16)
 elif i==1:camera(cam,(.11,-.20,.42),(0,0,.004),.205)
 else:camera(cam,(.13,-.27,.35),(0,0,.009),.235)
 sc.render.filepath=str(ROOT/(slug+'_Preview.png'));bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/(slug+'_Render.blend')));bpy.ops.render.render(write_still=True)
sc,cam=setup(True)
model(SLUGS[0],(-.180,.012,0),math.radians(38));model(SLUGS[1],(-.035,0,0));model(SLUGS[2],(.152,-.003,0))
camera(cam,(.1,-.37,.73),(-.01,0,.015),.56)
sc.render.filepath=str(ROOT/'Miaozhuang_Three_Variants.png');bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Miaozhuang_Three_Variants.blend'));bpy.ops.render.render(write_still=True)
print('ALL RENDERS DONE')
