"""Export the current 17-part STEP as one unsliced P1S PETG plate."""
import sys, hashlib, json, zipfile, uuid, itertools
from pathlib import Path
from collections import Counter
from xml.etree import ElementTree as E
from xml.sax.saxutils import quoteattr
import FreeCAD as A, Part, MeshPart
d,out,old=map(Path,sys.argv[1:4])
s=d/'STEP'; proof=json.loads((d/'QA/expansion-fit.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for stem,h in proof['hashes'].items():assert sha(s/(stem+'.step'))==h
assembly=Part.read(str(s/'00_Two_Bay_Horizontal_Frame_Check.step'))
closed=Part.read(str(s/'00_Four_Cam_Closed_Assembly.step'))
kit=Part.read(str(s/'07_Right_Bay_Frame_Expansion_17_Parts.step'))
basket=Part.read(str(s/'27_Cinnamoroll_Corner_Relief_Drawer.step')).Solids[0]
assert all(x.isValid() for x in (assembly,closed,kit,basket))
p=kit.Solids
assert len(p)==17 and len(assembly.Solids)==35
V=A.Vector
def collision(x,y):
 a,b=x.BoundBox,y.BoundBox
 if any(min(getattr(a,k+'Max'),getattr(b,k+'Max'))-max(getattr(a,k+'Min'),getattr(b,k+'Min'))<1e-6 for k in 'XYZ'):return 0
 return x.common(y).Volume
b=basket.translated(V(25.6+154.7,8,10))
assert abs(b.Volume-closed.Solids[14].Volume)<0.002
# Same published low-side basket placed in the new bay; not an input to print layout.
peak=0
for disp in [0,-.1,-.3,-.6,-1,-2,-3,-4,-5,-6,-7,-8,-9,-10,-12,-16,-22,-30,-45,-60,-85,-100,-110.5]:
 q=b.translated(V(0,disp,0))
 peak=max(peak,max(collision(q,part) for part in assembly.Solids))
assert peak<.001,peak
print('PASS actual low-side basket, 23 positions, peak overlap',peak,flush=True)
names=['01 右外侧板','02 前梁','03 后板','04 左限位拨片','05 右限位拨片','06 前左拉杆','07 前右拉杆','08 后左下拉杆','09 后右下拉杆','10 前左偏心轮','11 前右偏心轮','12 后左下偏心轮','13 后右下偏心轮','14 后左上拉杆','15 后右上拉杆','16 后左上偏心轮','17 后右上偏心轮']
# XY centering, bed contact left at Z=0. Frame panels upright as designed.
# Front beam puts its wider face down; paddles and blades on broad faces, rods transverse, cams axis vertical.
poses=[((0,0,1),90,128,190),((1,0,0),90,128,142),((0,0,1),0,128,108)]
poses += [((1,0,0),90,45,70),((1,0,0),90,71,70)]
poses += [((0,0,1),0,x,70) for x in (99,128,157,186)]
poses += [((1,0,0),90,x,35) for x in (44,68,92,116)]
poses += [((0,0,1),0,x,35) for x in (145,172)]
poses += [((1,0,0),90,x,35) for x in (198,220)]
NS="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
PN="http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
BAMBU="http://schemas.bambulab.com/package/2021"
REL="http://schemas.openxmlformats.org/package/2006/relationships"
MODREL="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
identity='1 0 0 0 1 0 0 0 1'
mat='1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1'
fmt=lambda x:f'{x:.6f}'.rstrip('0').rstrip('.') or '0'
xmlhead='<?xml version="1.0" encoding="UTF-8"?>'
def uid(label):return str(uuid.uuid5(uuid.NAMESPACE_URL,'mizy/right-bay-print/'+label))
def meta(k,v):return f'<metadata key={quoteattr(str(k))} value={quoteattr(str(v))}/>'
rows=[]; allbounds=[]; models={}; resources=[]; build=[]; objects=[]; instances=[]; ass=[]; rels=[]
for n,(shape,name,(axis,angle,cx,cy)) in enumerate(zip(p,names,poses),1):
 shape=shape.copy()
 if angle:shape.rotate(V(),V(*axis),angle)
 box=shape.optimalBoundingBox(False,False)
 shape.translate(V(-(box.XMin+box.XMax)/2,-(box.YMin+box.YMax)/2,-box.ZMin))
 mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.035,AngularDeflection=.12,Relative=False)
 verts,fs=mesh.Topology
 # Merge identical seam coordinates across analytic surfaces without modifying face winding.
 v=[]; indices={}; mp=[]
 for q in verts:
  pt=tuple(round(float(t),6)+0.0 for t in (q.x,q.y,q.z))
  if pt not in indices:indices[pt]=len(v);v.append(pt)
  mp.append(indices[pt])
 f=[tuple(mp[i] for i in face) for face in fs]
 assert all(len(set(t))==3 for t in f),(n,'degenerate')
 edges=Counter()
 dirs=Counter()
 for a,j,k in f:
  for x,y in ((a,j),(j,k),(k,a)):
   edges[tuple(sorted((x,y)))]+=1
   dirs[(x,y)]+=1
 assert all(z==2 for z in edges.values()) and all(z==1 for z in dirs.values()),(n,Counter(edges.values()),Counter(dirs.values()))
 signs=[]
 for i,j,k in f:
  a,j,k=v[i],v[j],v[k]
  signs.append(a[0]*(j[1]*k[2]-j[2]*k[1])+a[1]*(j[2]*k[0]-j[0]*k[2])+a[2]*(j[0]*k[1]-j[1]*k[0]))
 vol=sum(signs)/6
 assert abs(vol-shape.Volume)<max(.8,shape.Volume*.01),(n,vol,shape.Volume)
 floor=min(q[2] for q in v)
 v=[(x,y,round(z-floor,6)) for x,y,z in v]
 xyz=[(min(q[k] for q in v),max(q[k] for q in v)) for k in range(3)]
 bounds=(xyz[0][0]+cx,xyz[1][0]+cy,xyz[0][1]+cx,xyz[1][1]+cy)
 assert bounds[0]>=7.5 and bounds[1]>=7.5 and bounds[2]<=248.5 and bounds[3]<=248.5
 assert bounds[0]>=18+5 or bounds[1]>=28+5
 assert abs(xyz[2][0])<.00001,(n,xyz)
 allbounds.append(bounds)
 rows.append((name,len(v),len(f),round(vol,3),bounds,xyz[2][1]))
 leaf=f'/3D/Objects/object_{n}.model'; label=quoteattr(name)
 models[leaf[1:]]=f'{xmlhead}<model unit="millimeter" xmlns="{NS}" xmlns:p="{PN}" requiredextensions="p"><resources><object id="{n}" type="model" name={label} p:UUID="{uid(f"mesh/{n}")}"><mesh><vertices>'+''.join(f'<vertex x="{fmt(x)}" y="{fmt(y)}" z="{fmt(z)}"/>' for x,y,z in v)+'</vertices><triangles>'+''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a,b,c in f)+'</triangles></mesh></object></resources></model>'
 u=uid(f'part/{n}')
 resources.append(f'<object id="{n}" type="model" name={label} p:UUID="{u}"><components><component p:path="{leaf}" objectid="{n}" p:UUID="{uid(f"component/{n}")}"/></components></object>')
 rels.append(f'<Relationship Target="{leaf}" Id="rel{n}" Type="{MODREL}"/>')
 tr=f'{identity} {cx} {cy} 0'
 build.append(f'<item objectid="{n}" p:UUID="{uid(f"item/{n}")}" transform="{tr}" printable="1"/>')
 objects.append(f'<object id="{n}">'+meta('name',name)+f'<metadata face_count="{len(f)}"/><part id="{n}" subtype="normal_part">'+meta('name',name)+meta('matrix',mat)+f'<mesh_stat face_count="{len(f)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/></part></object>')
 instances.append('<model_instance>'+meta('object_id',n)+meta('instance_id',0)+meta('identify_id',100+n)+'</model_instance>')
 ass.append(f'<assemble_item object_id="{n}" instance_id="0" transform="{tr}" offset="0 0 0"/><assemble_item object_id="{n}" volume_id="0" transform="{identity} 0 0 0"/>')
for i,j in itertools.combinations(range(len(allbounds)),2):
 a,b=allbounds[i],allbounds[j]
 assert max(b[0]-a[2],a[0]-b[2],b[1]-a[3],a[1]-b[3])>=8,(i,j)
with zipfile.ZipFile(old) as z:
 cfg=json.loads(z.read('Metadata/project_settings.config'))
 content=z.read('[Content_Types].xml')
 root_rels=z.read('_rels/.rels')
assert cfg['printer_settings_id']=='Bambu Lab P1S 0.4 nozzle' and cfg['filament_settings_id']==['Generic PETG']
cfg.update(enable_prime_tower='0',enable_support='0',print_sequence='by layer')
main=f'{xmlhead}<model unit="millimeter" xmlns="{NS}" xmlns:BambuStudio="{BAMBU}" xmlns:p="{PN}" requiredextensions="p"><metadata name="Application">BambuStudio-02.09.01.70</metadata><metadata name="BambuStudio:3mfVersion">1</metadata><metadata name="Title">Right Bay Frame Expansion</metadata><resources>'+''.join(resources)+'</resources><build>'+''.join(build)+'</build></model>'
plate='<plate>'+meta('plater_id',1)+meta('plater_name','01 右格骨架＋配件')+meta('locked','false')+meta('gcode_file','')+''.join(instances)+'</plate>'
settings=xmlhead+'<config>'+''.join(objects)+plate+'<assemble>'+''.join(ass)+'</assemble></config>'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
 for pth,data in {**models,'3D/3dmodel.model':main,'3D/_rels/3dmodel.model.rels':xmlhead+f'<Relationships xmlns="{REL}">'+''.join(rels)+'</Relationships>','[Content_Types].xml':content,'_rels/.rels':root_rels,'Metadata/model_settings.config':settings,'Metadata/project_settings.config':json.dumps(cfg,ensure_ascii=False,indent=2)}.items():z.writestr(pth,data)
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 assert not any('gcode' in f for f in z.namelist())
 root=E.fromstring(z.read('3D/3dmodel.model')); conf=E.fromstring(z.read('Metadata/model_settings.config'))
 seq=list(map(str,range(1,18)))
 assert [o.attrib['id'] for o in root.findall('.//{*}object')]==seq
 assert [o.attrib['objectid'] for o in root.findall('.//{*}item')]==seq
 assert [o.attrib['id'] for o in conf.findall('object')]==seq
 assert [o.attrib['value'] for o in conf.findall(".//model_instance/metadata[@key='object_id']")]==seq
 assert Counter(o.attrib['object_id'] for o in conf.findall('.//assemble_item'))==Counter({i:2 for i in seq})
 for r in root.findall('.//{*}component'):
  n=r.attrib['objectid']; src=r.attrib[f'{{{PN}}}path'][1:];o=E.fromstring(z.read(src)).find('.//{*}object');assert o.attrib['id']==n
print('PASS ZIP, all object and assembly references, 17 independently editable watertight objects, 1 plate, no gcode',flush=True)
for row in rows:print(row)
print('OUTPUT',out,out.stat().st_size,sha(out),flush=True)
