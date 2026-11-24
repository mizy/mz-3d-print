"""Height-layered mesh trial, no slicing. Print coordinates: X=x, Y=-z, Z=y-ymin."""
from pathlib import Path
import json,trimesh,numpy as np,zipfile,xml.etree.ElementTree as ET
from shapely.geometry import Polygon
root=Path(__file__).resolve().parents[1];out=root/'HeightLayerTrial';out.mkdir(exist_ok=True)
params={'color_change_height_mm':14.6,'cyan_cap_thickness_mm':0.4,'gray_overlap_mm':0.15}
parameter_file=root/'Source/height_parameters.json'
if parameter_file.exists(): params.update(json.loads(parameter_file.read_text()))
else: parameter_file.write_text(json.dumps(params,indent=2)+'\n')
def clean(m):
 m.merge_vertices(digits_vertex=4);m.update_faces(m.unique_faces());m.update_faces(m.nondegenerate_faces());m.remove_unreferenced_vertices();return m
src=trimesh.load(root/'Reference/Strap Body.stl',force='mesh');parts=src.split();assert len(parts)==2
base=clean(trimesh.boolean.union(list(parts),engine='manifold'))
poly=[(15,5),(20,8.5),(34,8.5),(39,7.6),(63,7.6),(68,8.5),(83,8.5),(88,5),(80,4.4),(22,4.4)]
stripe=[(20,5),(31,5),(37,6),(64,6),(70,5),(83,5),(81,5.8),(70,5.8),(64,6.8),(37,6.8),(31,5.8),(21,5.8)]
def prism(poly,y,d):
 m=trimesh.creation.extrude_polygon(Polygon(poly),d,engine='earcut');v=m.vertices.copy();m.vertices=np.c_[v[:,0],y+v[:,2],v[:,1]]
 if m.volume<0:m.invert()
 return m
h=params['color_change_height_mm']+float(base.bounds[0,1]);cap=params['cyan_cap_thickness_mm'];overlap=params['gray_overlap_mm']
assert h>0.3, 'Color change height must remain above base outer side'
assert Polygon(stripe).difference(Polygon(poly)).area<1e-8
armor=prism(poly,-overlap,h+overlap);cyan=prism(stripe,h,cap)
gray=clean(trimesh.boolean.union([base,armor],engine='manifold'));body=clean(trimesh.boolean.union([gray,cyan],engine='manifold'))
assert gray.is_watertight and cyan.is_watertight and body.is_watertight and len(body.split())==1
# The opposite original side is the bed-facing side. No adornments below it.
ymin=float(body.bounds[0,1])
def orient(m):
 q=m.copy();v=q.vertices.copy();q.vertices=np.c_[v[:,0],-v[:,2]+12.7,v[:,1]-ymin];return q
gray,cyan,body=map(orient,[gray,cyan,body])
assert abs(gray.bounds[1,2]-cyan.bounds[0,2])<1e-6
for name,m in [('BODY_ALL_SINGLE_COLOR',body),('BODY_GRAY_TO_HEIGHT',gray),('CYAN_TOP_LAYERS',cyan)]:
 m.export(out/(name+'.stl'));r=clean(trimesh.load(out/(name+'.stl'),force='mesh'));assert r.is_watertight
 if name=='BODY_ALL_SINGLE_COLOR':assert len(r.split())==1
button=trimesh.load(root/'Reference/Button.stl',force='mesh');button.vertices-=button.bounds[0];button.export(out/'BUTTON_PRINT_TWO.stl')
# Geometry-only 3MF with basematerial assignments, no slicing settings or toolpaths.
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',ns)
def E(t,**attrs):return ET.Element('{'+ns+'}'+t,{k:str(v) for k,v in attrs.items()})
model=E('model',unit='millimeter');res=E('resources');model.append(res);materials=E('basematerials',id=1);res.append(materials)
for name,c in [('Graphite','#414650FF'),('Cyan','#14C3D7FF')]:materials.append(E('base',name=name,displaycolor=c))
for oid,m,col in [(2,gray,0),(3,cyan,1)]:
 obj=E('object',id=oid,type='model',pid=1,pindex=col,name=['','', 'BODY_GRAY','CYAN_TOP'][oid]);res.append(obj);mesh=E('mesh');obj.append(mesh);verts=E('vertices');tris=E('triangles');mesh.extend([verts,tris])
 for v in m.vertices:verts.append(E('vertex',x=f'{v[0]:.8f}',y=f'{v[1]:.8f}',z=f'{v[2]:.8f}'))
 for f in m.faces:tris.append(E('triangle',v1=int(f[0]),v2=int(f[1]),v3=int(f[2])))
obj=E('object',id=4,type='model',name='HEIGHT_LAYERED_BODY');res.append(obj);comps=E('components');obj.append(comps)
for oid in [2,3]:comps.append(E('component',objectid=oid))
build=E('build');build.append(E('item',objectid=4));model.append(build)
with zipfile.ZipFile(out/'BODY_HEIGHT_COLORS_GEOMETRY_ONLY.3mf','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
 z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
 z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
report={'mesh_only':True,'slicing_performed':False,'body_closed_single_connected':True,'gray_z_mm':gray.bounds[:,2].tolist(),'cyan_z_mm':cyan.bounds[:,2].tolist(),'coplanar_bond_area_mm2':float(Polygon(stripe).area),'cyan_projection_outside_armor_mm2':0.0,'body_extents_mm':body.extents.tolist(),'body_volume_mm3':float(body.volume),'nominal_color_transitions':1,'color_transition_note':'geometry permits one change, actual layer assignment must be checked by user','functional_geometry':'original mesh retained; decoration only original x=15..88,z=4.4..8.5 on right external side; no rail/button/LED edits','button_and_controller_fit_tested':False}
(out/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,indent=2))
