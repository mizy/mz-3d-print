import bpy,bmesh,os
from mathutils import Vector
base=os.path.dirname(os.path.abspath(__file__)); kind=os.environ['BOWL_KIND'];bpy.ops.wm.open_mainfile(filepath=os.path.join(base,kind+'_concept.blend'))
names=[kind,'Lock plate','Lock cap','Rivet','Corner guard','LV hallmark','Double C','UNVERIFIED rear connector bridge','UNVERIFIED rear connector stem']
for obj in list(bpy.context.scene.objects):
 if obj.type=='MESH' and any(obj.name==n or obj.name.startswith(n+'.') for n in names): bpy.data.objects.remove(obj,do_unlink=True)
bpy.ops.wm.stl_import(filepath=os.path.join(base,kind+'_voxel_experiment_unverified.stl'));obj=bpy.context.object;obj.data.materials.append(bpy.data.materials['Ivory'])
for face in obj.data.polygons:face.use_smooth=True
scene=bpy.context.scene;scene.cycles.samples=16
for name,loc in [('front',(205,-300,155)),('rear',(-210,260,185))]:
 cam=scene.camera;cam.location=loc;cam.rotation_euler=(Vector((0,0,26))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=os.path.join(base,kind+'_voxel_'+name+'.png');bpy.ops.render.render(write_still=True)
