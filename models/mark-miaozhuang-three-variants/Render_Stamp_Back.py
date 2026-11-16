import bpy
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'01_Intaglio_Stamp_Render.blend'))
s=bpy.context.scene;cam=s.camera;cam.location=(.15,.22,.20);target=Vector((0,0,.032));z=(cam.location-target).normalized();x=Vector((0,1,0)).cross(z).normalized();y=z.cross(x);cam.rotation_euler=Matrix((x,y,z)).transposed().to_euler();cam.data.ortho_scale=.155
s.render.resolution_x=1200;s.render.resolution_y=1100;s.cycles.samples=80;s.render.threads=8;s.render.filepath=str(ROOT/'01_Intaglio_Stamp_Back.png');bpy.ops.render.render(write_still=True)
