import bpy, math, bmesh, os
from mathutils import Vector
from math import sin,cos,pi
O='/Users/miaozhuang/Documents/dog-bowl-concepts/v3/'
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
def material(n,c,metal=0):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=.34
 return m
brown=material('Cream',(.70,.58,.42)); emboss=material('Ivory relief',(.70,.58,.42)); black=material('Ivory',(.70,.58,.42)); gold=material('Black emblem',(.018,.012,.009)); trim=material('Ivory edge',(.62,.46,.30)); floor=material('Background',(.69,.66,.63))
def radial(z):return 57.0+18.0*(max(0,min(60,z))/60)**.65
def front_y(x,z):
 r=radial(z);return -r*max(.001,1-(abs(x)/r)**3.4)**(1/3.4)
def shell(cx,kind):
 N=240; rings=[]
 # loft outer: fine radial and vertical resolution for actual quilt relief
 rings.append((0,35,'base'))
 for k in range(1,121):
  z=k*.5;rings.append((z,radial(z),'out'))
 # rounded top rim and inside wall; each ring connects as one closed surface
 rings += [(60,72,'rim')]
 for k in range(119,9,-1):
  z=k*.5;rings.append((z,radial(z)-3,'inner'))
 rings += [(4.5,48,'inner'),(4,35,'inner')]
 verts=[]; faces=[]; p=2/3.4
 for z,r,part in rings:
  for i in range(N):
   a=2*pi*i/N;c=cos(a);s=sin(a);x=r*math.copysign(abs(c)**p,c);y=r*math.copysign(abs(s)**p,s)
   if part=='out' and kind=='chanel' and y<0 and 7<z<56:
    # raised cushion cells separated by shallow continuous diamond seams
    u=(x+z)/24;v=(x-z)/24
    wave=(abs(sin(pi*u)*sin(pi*v)))**.48
    fade=min(1,(z-7)/4,(56-z)/4)*min(1,max(0,-y/15))
    y-=2.1*wave*fade
   verts.append((cx+x,y,z))
 for j in range(len(rings)-1):
  for i in range(N):
   a=j*N+i;b=j*N+(i+1)%N;faces.append((a,b,b+N,a+N))
 faces.append(tuple(reversed(range(N)))); faces.append(tuple((len(rings)-1)*N+i for i in range(N)))
 me=bpy.data.meshes.new(kind+' body');me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(kind+' body',me);bpy.context.collection.objects.link(ob);ob.data.materials.append(brown if kind=='lv' else black)
 for f in me.polygons:f.use_smooth=True
 return ob
# actual curved relief, with each vertex projected onto analytically defined front skin
# base extrudes into wall by .28 mm, outer face extends .65 mm; all ornaments intersect shell
def warp_mesh(obj,cx,mirror=False):
 bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=obj;obj.select_set(True)
 bpy.ops.object.convert(target='MESH')
 bm=bmesh.new();bm.from_mesh(obj.data)
 bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=3,use_grid_fill=True)
 bm.to_mesh(obj.data);bm.free();obj.data.update()
 # local XY is front design plane; local Z is relief height, created at origin
 for v in obj.data.vertices:
  x=(-v.co.x if mirror else v.co.x)+obj.location.x-cx; z=v.co.y+obj.location.z
  y=front_y(x,z)
  if cx>0 and 7<z<56:
   wave=(abs(sin(pi*(x+z)/24)*sin(pi*(x-z)/24)))**.48
   y-=2.1*wave*min(1,(z-7)/4,(56-z)/4)*min(1,max(0,-y/15))
  v.co=Vector((cx+x,y-v.co.z-.05,z))
 obj.location=(0,0,0)
 return obj
def lettering(body,cx,x,z,size,mat,font=None,mirror=False):
 cu=bpy.data.curves.new('Raised '+body,'FONT');cu.body=body;cu.align_x='CENTER';cu.align_y='CENTER';cu.size=size;cu.extrude=.48;cu.bevel_depth=.03;cu.resolution_u=8
 if font:cu.font=font
 ob=bpy.data.objects.new('Relief '+body,cu);bpy.context.collection.objects.link(ob);ob.location=(cx+x,0,z);cu.materials.append(mat);return warp_mesh(ob,cx,mirror)
def flower(cx,x,z,sz,mat,diamond=False):
 # star and four-lobed flower polygons, physical relief not shader
 n=64;pts=[]
 for i in range(n):
  a=2*pi*i/n
  r=sz*(.70+.30*cos(4*a)) if not diamond else sz/(abs(cos(a))+abs(sin(a)))
  pts.append((r*cos(a),r*sin(a),0))
 me=bpy.data.meshes.new('flower');me.from_pydata(pts,[],[tuple(range(n))]);me.update();ob=bpy.data.objects.new('Monogram motif',me);bpy.context.collection.objects.link(ob);ob.location=(cx+x,0,z)
 # flat face solidified before projection, base overlap .28 mm
 bpy.context.view_layer.objects.active=ob;ob.select_set(True);mod=ob.modifiers.new('Emboss thickness','SOLIDIFY');mod.thickness=.9;mod.offset=.38;bpy.ops.object.modifier_apply(modifier=mod.name);ob.select_set(False);ob.data.materials.append(mat);return warp_mesh(ob,cx)
# Build at separate world positions for rendering
left=-95;right=95
lv=shell(left,'lv'); ch=shell(right,'chanel')
font=bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf')
patterns=[]
# Four petals with pointed ends, arranged on the actual front surface.
def petal(cx,x,z,size,angle):
    pts=[]
    for i in range(32):
        t=2*pi*i/32
        # each petal meets at the center and swells toward its pointed tip
        xx=size*(.50+.50*cos(t)); zz=size*.25*sin(t)*abs(sin(t))**.35
        pts.append((xx*cos(angle)-zz*sin(angle),xx*sin(angle)+zz*cos(angle),0))
    me=bpy.data.meshes.new('petal');me.from_pydata(pts,[],[tuple(range(len(pts)))]);me.update()
    ob=bpy.data.objects.new('four petal',me);bpy.context.collection.objects.link(ob);ob.location=(cx+x,0,z)
    bpy.context.view_layer.objects.active=ob;ob.select_set(True)
    m=ob.modifiers.new('thickness','SOLIDIFY');m.thickness=.9;m.offset=.35;bpy.ops.object.modifier_apply(modifier=m.name);ob.select_set(False)
    ob.data.materials.append(emboss);warp_mesh(ob,cx)
def line(points,mat,radius,name):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=12;cu.bevel_depth=radius;cu.bevel_resolution=3
    sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
    for p,co in zip(sp.points,points):p.co=(*co,1)
    ob=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(ob);ob.data.materials.append(mat);return ob
for x,z in [(-45,18),(-23,31),(0,16),(23,31),(45,18),(-45,45),(-5,44),(39,45)]:
    for a in (0,pi/2,pi,3*pi/2):petal(left,x,z,5.2,a)
# front leather bands and corner accents convey the trunk construction
leather=material('Caramel leather',(.27,.095,.027)); brass=material('Brass',(.65,.38,.09),.5)
for z in (7,54):
    pts=[(left+x,front_y(x,z)-.65,z) for x in range(-52,53)]
    line(pts,leather,2.3,'Trunk horizontal trim')
for x in (-51,51):
    pts=[(left+x,front_y(x,z)-.8,z) for z in range(9,53)]
    line(pts,leather,2.5,'Trunk vertical trim')
# front clasp as a small layered rounded box, shown as a separate visual element
def badge(cx,z,w,h,mat,name):
    bpy.ops.mesh.primitive_cube_add(size=1,location=(cx,front_y(0,z)-1,z));o=bpy.context.object;o.name=name;o.dimensions=(w,2,h)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
    mod=o.modifiers.new('rounded','BEVEL');mod.width=1.8;mod.segments=4;o.modifiers.new('normals','WEIGHTED_NORMAL')
badge(left,38,17,16,brass,'Trunk clasp')
lettering('LV',left,0,39,7,leather,font)
# Curves follow the rim and preserve a clean inner wall.
def rim(cx,mat):
    pts=[]
    for i in range(241):
        a=2*pi*i/240;p=2/3.4
        pts.append((cx+73.5*math.copysign(abs(cos(a))**p,cos(a)),73.5*math.copysign(abs(sin(a))**p,sin(a)),60))
    line(pts,mat,1.15,'rim piping')
rim(left,leather);rim(right,gold)
# Overlapping C-shaped arcs, alternating visibility like the reference emblem.
def arc(cx,x0,flip):
    pts=[]
    for i in range(81):
        a=math.radians(52+256*i/80);x=x0+7*cos(a)*flip;z=31+8*sin(a)
        y=front_y(x,z)-2.8
        pts.append((cx+x,y,z))
    line(pts,gold,1.35,'interlocking C')
arc(right,-3.5,1);arc(right,3.5,-1)
# visualize rear connector placeholders only, not fit geometry
for cx,ma in [(left,brown),(right,black)]:
 bpy.ops.mesh.primitive_cube_add(size=1,location=(cx,74,45));o=bpy.context.object;o.name='UNVERIFIED rear mount placeholder';o.dimensions=(70,8.5,30);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(ma)
 bevel=o.modifiers.new('Rounded corners','BEVEL');bevel.width=2;bevel.segments=3;o.modifiers.new('Normals','WEIGHTED_NORMAL')
# Studio scene
bpy.ops.mesh.primitive_plane_add(size=1500,location=(0,0,-.5));bpy.context.object.data.materials.append(floor)
def area(loc,power,size):
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,26))-o.location).to_track_quat('-Z','Y').to_euler()
area((-160,-260,320),2800000,220);area((220,-100,250),1500000,190);area((0,200,180),1200000,190)
bpy.ops.object.camera_add(location=(0,-480,215));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,24))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=390;bpy.context.scene.camera=cam
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.render.resolution_x=1800;scene.render.resolution_y=1050;scene.render.resolution_percentage=100
scene.world.color=(.3,.3,.3)
bpy.ops.wm.save_as_mainfile(filepath=O+'dog_bowl_v3.blend')
scene.render.filepath=O+'dog_bowls_v3.png';bpy.ops.render.render(write_still=True)
