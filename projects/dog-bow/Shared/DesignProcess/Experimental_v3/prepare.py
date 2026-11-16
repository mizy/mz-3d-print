from pathlib import Path

base = Path('/Users/miaozhuang/Documents/dog-bowl-concepts')
s = (base/'v2/build.py').read_text()
s = s.replace("O='/Users/miaozhuang/Documents/dog-bowl-concepts/v2/'", "O='/Users/miaozhuang/Documents/dog-bowl-concepts/v3/'")
s = s.replace("brown=material('Chocolate brown',(.105,.042,.019))", "brown=material('Cream',(.70,.58,.42))")
s = s.replace("black=material('Charcoal black',(.026,.021,.021))", "black=material('Ivory',(.70,.58,.42))")
s = s.replace("emboss=material('Warm brown relief',(.30,.135,.056))", "emboss=material('Ivory relief',(.70,.58,.42))")
s = s.replace("gold=material('Muted brass',(.54,.31,.085),.58)", "gold=material('Black emblem',(.018,.012,.009))")
s = s.replace("u=(x+z)/17;v=(x-z)/17", "u=(x+z)/24;v=(x-z)/24")
s = s.replace("sin(pi*(x+z)/17)*sin(pi*(x-z)/17)", "sin(pi*(x+z)/24)*sin(pi*(x-z)/24)")
s = s.replace("y-=1.0*wave*fade", "y-=2.1*wave*fade")
s = s.replace("y-=wave*min(1,(z-7)/4,(56-z)/4)", "y-=2.1*wave*min(1,(z-7)/4,(56-z)/4)")
start=s.index('patterns=[]')
end=s.index('# visualize rear connector placeholders', start)
s=s[:start]+'''patterns=[]
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
''' + s[end:]
s=s.replace("'dog_bowl_v2.blend'", "'dog_bowl_v3.blend'")
s=s.replace("'dog_bowls_v2.png'", "'dog_bowls_v3.png'")
(base/'v3/build.py').write_text(s)
