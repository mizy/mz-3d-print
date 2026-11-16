import bpy, math, os
from mathutils import Vector
from math import sin, cos, pi, exp

OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)

def mat(name, color, metal=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=.32
    return m
cream=mat('Ivory',(.74,.62,.47)); leather=mat('Leather',(.30,.12,.035)); brass=mat('Brass',(.69,.42,.12),.55); black=mat('Black',(.015,.012,.01)); ground=mat('Backdrop',(.75,.73,.70))
N=768; NZ=200; P=2/4.0
# Sample a closed rounded-square perimeter and use arc length for continuous quilting.
raw=[(math.copysign(abs(cos(2*pi*i/8192))**P,cos(2*pi*i/8192)),math.copysign(abs(sin(2*pi*i/8192))**P,sin(2*pi*i/8192))) for i in range(8193)]
cumulative=[0.0]
for i in range(1,len(raw)): cumulative.append(cumulative[-1]+math.dist(raw[i-1],raw[i]))
xy=[]; k=0
for i in range(N):
    target=cumulative[-1]*i/N
    while cumulative[k+1]<target: k+=1
    t=(target-cumulative[k])/(cumulative[k+1]-cumulative[k])
    xy.append((raw[k][0]*(1-t)+raw[k+1][0]*t,raw[k][1]*(1-t)+raw[k+1][1]*t))
length=[0.0]
for i in range(1,N): length.append(length[-1]+math.dist(xy[i-1],xy[i])*73)
perimeter=length[-1]+math.dist(xy[-1],xy[0])*73
period=perimeter/24

def profile(z):
    return 60+14*(z/60)**.78

def relief_lv(x,y,z):
    # Repeated four-petal and diamond flower, embedded directly in the outer skin.
    u=x if abs(y)>abs(x) else y
    result=0
    for row in range(3):
        cz=15+row*15; shift=0 if row%2==0 else 12
        for col in range(-3,4):
            dx=u-(col*24+shift); dz=z-cz
            if abs(dx)>7 or abs(dz)>7: continue
            if (col+row)%2:
                # pointed four-lobe outline
                r=math.hypot(dx,dz); angle=math.atan2(dz,dx)
                target=4.5*(.70+.30*math.cos(4*angle))
                value=exp(-((r-target)/.65)**2)*.55 + exp(-(r/1.0)**2)*.4
            else:
                value=0
                for a in (0,pi/2,pi,3*pi/2):
                    ax=dx*cos(a)+dz*sin(a); ay=-dx*sin(a)+dz*cos(a)
                    value=max(value,exp(-(((ax-2.15)/2.0)**2+(ay/.72)**2)*1.8)*.8)
                value=max(value,exp(-(math.hypot(dx,dz)/.9)**2)*.7)
            result=max(result,value)
    return result

def shell(kind):
    verts=[]; faces=[]; matids=[]
    # bottom, outer walls, top, smooth inner walls, and inner floor form one closed mesh.
    rings=[(0,48,'bottom')]+[(60*j/NZ,profile(60*j/NZ),'outer') for j in range(NZ+1)]
    rings += [(60,71,'rim')]+[(60*j/NZ,profile(60*j/NZ)-3.0,'inner') for j in range(NZ-1,11,-1)] + [(3.6,48,'inner')]
    for z,r,part in rings:
        for i,(ux,uy) in enumerate(xy):
            d=0
            if part=='outer':
                if kind=='chanel':
                    fade=min(1,max(0,(z-4)/5),max(0,(59-z)/5))
                    # The period closes exactly around the bowl; quilt stays on its surface.
                    a=pi*(length[i]+z)/period; b=pi*(length[i]-z)/period
                    d=2.8*(abs(sin(a)*sin(b))**1.25)*fade
                else:
                    d=relief_lv(r*ux,r*uy,z)*min(1,max(0,(z-5)/3),max(0,(55-z)/3))
                    # Integrated trunk bands; side bands run continuously around the shell.
                    d+=.9*(exp(-((z-7)/2.6)**6)+exp(-((z-54)/2.6)**6))
                    d+=1.0*exp(-((abs(ux)-abs(uy))/.10)**4)*min(1,z/5,(60-z)/5)
            verts.append(((r+d)*ux,(r+d)*uy,z))
    for j in range(len(rings)-1):
        for i in range(N):
            k=(i+1)%N; faces.append((j*N+i,j*N+k,(j+1)*N+k,(j+1)*N+i))
            z,_,part=rings[j]; ux,uy=xy[i]
            if kind=='lv' and part=='outer' and (abs(z-7)<2.5 or abs(z-54)<2.5 or (abs(abs(ux)-abs(uy))<.08 and 5<z<57)): matids.append(1)
            elif kind=='chanel' and (part=='rim' or (part=='outer' and z==60)) : matids.append(1)
            else: matids.append(0)
    faces.append(tuple(reversed(range(N)))); matids.append(0)
    faces.append(tuple((len(rings)-1)*N+i for i in range(N))); matids.append(0)
    mesh=bpy.data.meshes.new(kind);mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(kind,mesh);bpy.context.collection.objects.link(obj);mesh.materials.append(cream);mesh.materials.append(leather if kind=='lv' else black)
    for f,m in zip(mesh.polygons,matids):f.use_smooth=True;f.material_index=m
    return obj

def box(name,loc,scale,material,bevel=1):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material)
    mod=o.modifiers.new('Rounded','BEVEL');mod.width=bevel;mod.segments=4;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
    return o

def tube(name,points,r,material):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=8;cu.bevel_depth=r;cu.bevel_resolution=4;cu.use_fill_caps=True
    sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
    for p,co in zip(sp.points,points):p.co=(*co,1)
    ob=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(ob);cu.materials.append(material)
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
    return ob

def front_y(x,z):
    r=profile(z);return -r*(max(.001,1-(abs(x)/r)**4))**.25

def quilt_front_y(x,z):
    r=profile(z)
    start=N//2
    target=x/r
    lo=start; hi=N
    while hi-lo>1:
        mid=(lo+hi)//2
        if xy[mid][0]<target: lo=mid
        else: hi=mid
    hi%=N
    t=max(0,min(1,(target-xy[lo][0])/(xy[hi][0]-xy[lo][0])))
    uy=xy[lo][1]*(1-t)+xy[hi][1]*t
    distance=length[lo]*(1-t)+length[hi]*t
    fade=min(1,max(0,(z-4)/5),max(0,(59-z)/5))
    d=2.8*abs(sin(pi*(distance+z)/period)*sin(pi*(distance-z)/period))**1.25*fade
    return (r+d)*uy

def decorate(kind):
    obs=[]
    if kind=='lv':
        # Rounded brass corner guards overlap the body and trim.
        for sx in (-1,1):
            for sy in (-1,1):
                for z in (7,54):
                    c=profile(z)*(.5**.25)
                    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,location=(sx*(c+2.0),sy*(c+2.0),z));o=bpy.context.object;o.name='Corner guard';o.scale=(4.0,4.0,4.5);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(brass);obs.append(o)
        # Raised two-level clasp and corner hardware.
        obs.append(box('Lock plate',(0,front_y(0,35)-.35,35),(19,2.5,16),brass,1.8))
        obs.append(box('Lock cap',(0,front_y(0,45)-.4,45),(22,2.5,7),brass,2.7))
        cu=bpy.data.curves.new('LV hallmark','FONT');cu.body='LV';cu.align_x='CENTER';cu.align_y='CENTER';cu.size=5.0;cu.extrude=.25
        o=bpy.data.objects.new('LV hallmark',cu);bpy.context.collection.objects.link(o);o.location=(0,front_y(0,45)-1.75,45);o.rotation_euler=(pi/2,0,0);cu.materials.append(leather)
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');obs.append(o)
        for x in (-7,7):
            for z in (30,40):
                bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=10,radius=1.2,location=(x,front_y(0,35)-1.5,z));o=bpy.context.object;o.name='Rivet';o.data.materials.append(brass);obs.append(o)
    else:
        # C glyphs open outwards and overlap in the center.
        for x0,flip in ((-4,-1),(4,1)):
            points=[]
            for i in range(121):
                a=math.radians(48+264*i/120);x=x0+7*cos(a)*flip;z=32+8*sin(a)
                points.append((x,quilt_front_y(x,z)-.65 - .2*flip*math.sin(a),z))
            obs.append(tube('Double C',points,1.15,black))
    # Approximate reference bracket only; inner dimensions and fit are unknown.
    obs.append(box('UNVERIFIED rear connector bridge',(0,74.1,52),(70,8.5,7),cream,1))
    obs.append(box('UNVERIFIED rear connector stem',(0,73.8,45),(14,8.5,18),cream,1))
    return obs

def save_stl(obj,kind):
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.wm.stl_export(filepath=os.path.join(OUT,kind+'_body_only_unfinished.stl'),export_selected_objects=True)

def scene_render(body,extras,kind):
    bpy.ops.mesh.primitive_plane_add(size=2000,location=(0,0,-.1));plane=bpy.context.object;plane.data.materials.append(ground)
    for loc,power,size in [((-150,-200,240),1800000,140),((160,-50,200),1000000,120),((0,180,220),1400000,150)]:
        bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,25))-o.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add();cam=bpy.context.object;bpy.context.scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=225
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=20;scene.cycles.use_denoising=True;scene.render.resolution_x=1400;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.world.color=(.32,.32,.32)
    for name,loc in ([('front', (205,-300,155))] if os.environ.get('FRONT_ONLY') else [('front', (205,-300,155)),('rear',(-210,260,185)),('top',(0,-65,330))]):
        cam.location=loc;cam.rotation_euler=(Vector((0,0,26))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=os.path.join(OUT,kind+'_'+name+'.png');bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,kind+'_concept.blend'))

kind=os.environ.get('BOWL_KIND','lv'); body=shell(kind);save_stl(body,kind);extras=decorate(kind);scene_render(body,extras,kind)
