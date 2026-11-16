from pathlib import Path
import json,math
import numpy as np
import trimesh
import manifold3d as md
import pyvista as pv
from trimesh.exchange.threemf import export_3MF
O=Path(__file__).parent;D=O/'print-plates';D.mkdir(exist_ok=True)
source={n:trimesh.load_mesh(O/(n+'.stl')) for n in ['board','relief_badge','desk_foot','universal_tray']}
plates=[('01_board',[('board',source['board'],5,4)]),('02_relief_feet_trays',[('relief_badge',source['relief_badge'],5,10),('desk_foot_1',source['desk_foot'],10,90),('desk_foot_2',source['desk_foot'],40,90)]+[(f'tray_{i+1}',source['universal_tray'],70+(i%3)*57.6,90+(i//3)*33) for i in range(7)])]
# Optional low-cost two-hole fit coupon taken from the actual printed board geometry.
m=source['board'];solid=md.Manifold(md.Mesh(np.asarray(m.vertices,dtype=np.float32),np.asarray(m.faces,dtype=np.uint32)))
c=solid^md.Manifold.cube((60,24,7)).translate((2,204,-1));a=c.to_mesh();coupon=trimesh.Trimesh(np.asarray(a.vert_properties)[:,:3],a.tri_verts,process=True);coupon.apply_translation(-coupon.bounds[0]);coupon.export(D/'fit_coupon.stl')
plates.insert(0,('00_optional_fit_test',[('two_hole_coupon',coupon,60,90),('one_test_tray',source['universal_tray'],130,90)]))
report={'bed_assumption_mm':[250,250],'format':'3MF geometry only; no printer, filament, supports or slicing profile','plates':[]}
pl=pv.Plotter(off_screen=True,window_size=(1500,850),shape=(1,2),border=False)
for index,(name,objects) in enumerate(plates):
 scene=trimesh.Scene();scene.units='mm';entry={'file':name+'.3mf','objects':[],'solid_volume_cm3':0}
 for label,original,x,y in objects:
  t=original.copy();t.apply_translation(np.array([x,y,0])-t.bounds[0]);t.units='mm'
  assert t.bounds[0,0]>=0 and t.bounds[0,1]>=0 and t.bounds[1,0]<=250 and t.bounds[1,1]<=250
  for old in entry['objects']:
   b=np.asarray(old['bounds_mm']);assert not (min(t.bounds[1,0],b[1,0])>max(t.bounds[0,0],b[0,0]) and min(t.bounds[1,1],b[1,1])>max(t.bounds[0,1],b[0,1])),(label,old['name'])
  scene.add_geometry(t,node_name=label,geom_name=label);entry['objects'].append({'name':label,'bounds_mm':t.bounds.tolist()});entry['solid_volume_cm3']+=t.volume/1000
  if index:
   pl.subplot(0,index-1);color='#83a4ad' if label=='board' else '#d7b983' if label=='relief_badge' else '#607b8a' if label.startswith('desk') else '#b4cdb0'
   pl.add_mesh(pv.PolyData(t.vertices,np.column_stack((np.full(len(t.faces),3),t.faces)).ravel()),color=color,lighting=True,ambient=0.25)
   center=t.bounds.mean(axis=0);pl.add_point_labels([[center[0],center[1],25]],[label.replace('_',' ')],font_size=11,show_points=False,always_visible=True,shape_opacity=.8)
 (D/(name+'.3mf')).write_bytes(export_3MF(scene))
 restored=trimesh.load_scene(D/(name+'.3mf'));assert len(restored.graph.nodes_geometry)==len(objects);assert np.allclose(restored.bounds,scene.bounds,atol=1e-4)
 entry['readback_object_count']=len(restored.graph.nodes_geometry);report['plates'].append(entry)
 if index:
  pl.subplot(0,index-1);pl.set_background('#f4f6fa');pl.add_mesh(pv.lines_from_points(np.array([[0,0,0],[250,0,0],[250,250,0],[0,250,0],[0,0,0]])),color='#40535e',line_width=2)
  pl.add_text('Plate 1: board' if index==1 else 'Plate 2: relief + 2 feet + 7 trays',font_size=14,color='#243743');pl.camera_position=[(125,125,700),(125,125,0),(0,1,0)];pl.enable_parallel_projection();pl.camera.parallel_scale=146
pl.screenshot(str(D/'plate-layout.png'));pl.close()
(D/'layout.json').write_text(json.dumps(report,indent=2));print(json.dumps({'readback_counts':[p['readback_object_count'] for p in report['plates']],'optional_test_solid_volume_cm3':report['plates'][0]['solid_volume_cm3'],'layout':str(D/'plate-layout.png')},indent=2))
(D/'打印说明.txt').write_text("""V17 SKADIS目标接口分盘：按250×250mm有效打印范围。
01_board：240×242mm立板1件，摆在X5/Y4，四周余量很小，需核对实际机型禁打区和裙边。
02_relief_feet_trays：240×64mm浮雕前板1件、桌脚2件、独立托架7件。
00_optional_fit_test：真实模型截取两长圆孔的60×24mm小板＋托架1件。先试打接口，验证宜家实物配合；合格托架可计入7件总量。
3MF只含毫米单位几何和排布，无打印机配置、支撑设置或G-code。对象独立，按层打印；逐件打印避让未验证。
托架后挂头有局部悬空；设置局部支撑并逐层检查。浮雕板底部深凹槽形成桥接，先检查切片，不直接承诺免支撑。
参考起点：0.4mm喷嘴，立板0.20mm层高，浮雕盘0.16mm层高，3圈墙、顶底4层、20%填充。具体设置以你的设备和材料为准。
立板挂孔局部5mm厚，其余2.4mm；不是均匀5mm板，宽背座配件可能需要额外平面支撑。SKADIS兼容性未经过宜家实物验证。
托架仍为重力落位，防抬锁片未完成，拿物件时需按住托架。所有文件仍属于试制设计。
""")
