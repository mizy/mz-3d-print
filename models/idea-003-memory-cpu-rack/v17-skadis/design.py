from pathlib import Path
import json, math
import numpy as np
import manifold3d as md
import trimesh
import pyvista as pv
O=Path(__file__).parent; M=md.Manifold

def box(d,p):return M.cube(d).translate(p)
def world(s):return s.rotate((-15,0,0))
def mesh(s):
 a=s.to_mesh();t=trimesh.Trimesh(np.asarray(a.vert_properties)[:,:3],a.tri_verts,process=False)
 t.merge_vertices(digits_vertex=5);t.update_faces(t.nondegenerate_faces());t.remove_unreferenced_vertices();return t
# SKADIS-target interface: 5 x 15 mm capsule, 40 mm lattice + (20,20) offset.
# Nominal 5 mm around slots; 2.4 mm backing skin elsewhere. Physical compatibility unverified.
def capsule(w,h,depth):
 return box((w,depth,h-w),(-w/2,0,-(h-w)/2))+M.cylinder(depth,w/2,circular_segments=48).rotate((-90,0,0)).translate((0,0,-(h-w)/2))+M.cylinder(depth,w/2,circular_segments=48).rotate((-90,0,0)).translate((0,0,(h-w)/2))
board=box((240,2.4,242),(0,0,-8))+box((240,5,16),(0,0,-8))
slot_centers=[]
for row,z in enumerate(range(18,225,20)):
 for x in range(12+(row%2)*20,237,40):
  if x+4.5>240:continue
  board+=capsule(9,19,5).translate((x,0,z))
  slot_centers.append((x,z))
for x,z in slot_centers:board-=capsule(5,15,7).translate((x,-1,z))
# Shallow rear hex recesses keep slot pads and root intact; never perforate the skin.
board_before_recess=board.volume()
board_pockets=[]
for row,z in enumerate(np.arange(16,226,10.392305)):
 for x in np.arange(9+(row%2)*6,232,12):
  distance=min(math.hypot(x-sx,max(abs(z-sz)-5,0))-2.5 for sx,sz in slot_centers)
  if distance<9:continue
  depth=2.4
  board-=M.cylinder(7,4.5,circular_segments=6).rotate((-90,0,0)).translate((x,-1,z))
  board_pockets.append({'x':float(x),'z':float(z),'depth_mm':depth,'through':True})
# One universal tray printed seven times: 44 mm clear width, solid bottom, side stops.
tray=box((47.6,14,2),(-23.8,-14,0))
tray+=box((47.6,2,12),(-23.8,-2,0))
tray+=box((47.6,2,6),(-23.8,-14,0))
for x in (-23.8,22):tray+=box((1.8,14,8),(x,-14,0))
for x in (-20,20):
 tray+=box((2.8,5.4,3),(x-1.4,0,2.95))
 tray+=box((3.8,1.6,8),(x-1.9,5.4,.5))
# Insert raised 4.26 mm, then lower. Rear heads catch the circular-hole lower edge.
locations=[('RAM'+str(i+1),x,8+(i%2)*20,42,133.35,8) for i,x in enumerate((32,92,152,212))]
locations += [('CPU'+str(i+1),x,188,40,40,5) for i,x in enumerate((52,132,212))]
parts=[('board',world(board))]
for name,x,z,*_ in locations:parts.append(('tray_'+name,world(tray.translate((x,0,z)))))
# Two identical desk feet. Angled blind slots seat the board bottom, with 0.2 mm side clearance.
foot=box((18,132,3),(-9,-70,-12))+box((18,20,18),(-9,-8,-12))
slot=world(box((20,5.4,26),(-10,-.2,-8)))
foot-=slot
# Full-width 3 mm front panel seated directly on two extended 18 mm wide feet.
for y in (-66,-14):foot+=M.cylinder(4,2,circular_segments=32).translate((0,y,-9))
raw=trimesh.load_mesh(O/'assets/relief.stl')
relief=M(md.Mesh(np.asarray(raw.vertices,dtype=np.float32),np.asarray(raw.faces,dtype=np.uint32)))
# Preserve the whole original 120 x 48 mm relief rectangle, including its background.
badge=box((240,64,3),(0,-72,-9))
badge+=relief.translate((60,-64,-8.65))
background_centers=[]
for row,y in enumerate((-60,-40,-20)):
 for x in range(12+(row%2)*20,237,40):
  if x+4.5>59 and x-4.5<181 and y+9.5>-65 and y-9.5<-15:continue
  if any(abs(x-px)<8 and abs(y-py)<13 for px in (16,224) for py in (-66,-14)):continue
  # Thickened slot pads on top, same 5 mm interface as the upright board.
  badge+=capsule(9,19,5).rotate((90,0,0)).translate((x,y,-9))
  badge-=capsule(5,15,8).rotate((90,0,0)).translate((x,y,-10))
  background_centers.append([x,y])
for x in (16,224):
 for y in (-66,-14):badge-=M.cylinder(8,2.2,circular_segments=32).translate((x,y,-10))
badge_before_recess=badge.volume()
badge_pockets=[]
for row,y in enumerate(np.arange(-63,-16,10.392305)):
 for x in np.arange(35+(row%2)*6,208,12):
  if any(math.hypot(x-sx,max(abs(y-sy)-5,0))-2.5<9 for sx,sy in background_centers):continue
  through=(x+4.5<58 or x-4.5>182)
  depth=3 if through else 1.2
  badge-=M.cylinder(8 if through else depth+.1,4.5,circular_segments=6).translate((x,y,-9.1))
  badge_pockets.append({'x':float(x),'y':float(y),'depth_mm':depth,'through':bool(through)})
badge=badge.simplify(.001)
parts.append(('relief_badge',badge))
for x in (16,224):parts.append(('foot_'+str(x),foot.translate((x,0,0))))
rows=[]
for name,s in [('board',world(board)),('universal_tray',tray),('desk_foot',foot),('relief_badge',badge)]:
 t=mesh(s);printable=t.copy()
 if name=='board':printable.apply_transform(trimesh.transformations.rotation_matrix(math.radians(105),(1,0,0)))
 printable.apply_translation(-printable.bounds[0]);printable.vertices=np.asarray(printable.vertices,dtype=np.float32);printable.merge_vertices(digits_vertex=5);printable.update_faces(printable.nondegenerate_faces());printable.remove_unreferenced_vertices();printable.export(O/(name+'.stl'))
 rows.append({'part':name,'quantity':{'board':1,'universal_tray':7,'desk_foot':2,'relief_badge':1}[name],'volume_cm3_each':t.volume/1000,'watertight':bool(t.is_watertight),'components':len(t.split(only_watertight=False)),'print_dimensions_mm':printable.extents.tolist()})
# Check settled assembly, nominal objects, and hook insertion sweep against board.
inter=[]
for i,(na,a) in enumerate(parts):
 for nb,b in parts[i+1:]:
  v=(a^b).volume()
  if v>1e-4:inter.append({'parts':[na,nb],'volume_mm3':v})
fit=[];objects=[]
for name,x,z,w,h,d in locations:
 obj=world(box((w,d,h),(x-w/2,-2.03-d,z+2)))
 objects.append((name,obj));fit.append({'item':name,'interferences':{n:round((obj^s).volume(),5) for n,s in parts if (obj^s).volume()>1e-4}})
# Only hooks cross board; rear upper entry accepts the heads before descent.
sweep=[]
for dz in np.linspace(0,5.5,23):
 s=tray.translate((32,0,8+dz));v=(s^board).volume()
 if v>1e-4:sweep.append({'lift_mm':float(dz),'collision_mm3':v})
for dy in np.linspace(-8,0,17):
 s=tray.translate((32,float(dy),13.5));v=(s^board).volume()
 if v>1e-4:sweep.append({'entry_y_mm':float(dy),'collision_mm3':v})
pl=pv.Plotter(off_screen=True,window_size=(1500,950),shape=(1,2),border=False)
scene=trimesh.Scene();allm=[]
for name,s in parts:
 t=mesh(s);scene.add_geometry(t,node_name=name);allm.append(t)
 for pane in (0,1):
  pl.subplot(0,pane);pl.set_background('#f4f6fa');pm=pv.PolyData(t.vertices,np.column_stack((np.full(len(t.faces),3),t.faces)).ravel());pl.add_mesh(pm,color='#789da3' if name=='board' else '#d4ab73' if name.startswith('tray') else '#d5b987' if name=='relief_badge' else '#526f7c')
for name,s in objects:
 t=mesh(s);pl.subplot(0,1);pl.add_mesh(pv.PolyData(t.vertices,np.column_stack((np.full(len(t.faces),3),t.faces)).ravel()),color='#679977' if name.startswith('RAM') else '#c2c5c8')
for pane,title in [(0,'V17 SKADIS-target slots + hexagonal perforations'),(1,'Nominal fit: 4 RAM sticks + 3 CPUs')]:
 pl.subplot(0,pane);pl.add_text(title,font_size=12,color='#243743');pl.camera_position=[(355,-410,275),(104,5,85),(0,0,1)];pl.enable_parallel_projection();pl.reset_camera()
pl.screenshot(str(O/'design.png'));pl.close()
scene.export(O/'assembly.glb');trimesh.util.concatenate(allm).export(O/'assembly.stl')
total=sum(r['quantity']*r['volume_cm3_each'] for r in rows)
r={'status':'prototype; fit and print validation required','parts':rows,'total_volume_cm3':total,'assembly_interferences':inter,'nominal_fit':fit,'hook_vertical_insertion_sweep':sweep,'slot_mm':[5,15],'lattice_mm':[40,40],'alternate_offset_mm':[20,20],'slot_interface_thickness_mm':5,'backing_skin_mm':2.4,'hook_drop_mm':5.5,'slot_centers_mm':slot_centers,'relief_background_holes':len(background_centers),'relief_solid_rectangle_mm':[120,48],'front_panel_mm':[240,64,3],'support_rail_width_mm':18,'relief_hole_margin_mm':1,'recesses':{'board_count':len(board_pockets),'front_panel_count':len(badge_pockets),'hex_max_span_mm':9,'nominal_hex_gap_mm':3,'board_regions':'through holes outside slot pads','front_panel_min_skin_under_relief_mm':1.8,'removed_volume_cm3':(board_before_recess-board.volume()+badge_before_recess-badge.volume())/1000,'board_pockets':board_pockets,'front_panel_pockets':badge_pockets},'hardware':'Front panel rests on both extended feet with four round locating posts; tray hooks remain gravity seated without positive anti-lift locks.','limitations':['SKADIS compatibility target based on published measurements; no IKEA product fit test','Raised slot pads provide 5 mm locally, rather than a uniform 5 mm board; some accessories may require additional flat contact area','No slicer or physical fit test','Nominal cuboids do not represent CPU pins or RAM surface components','Foot-slot fit and tipping stability require physical validation','All-tray layout must be evaluated with actual item dimensions','Hold the tray while removing objects: no positive anti-lift lock','Hook undersides need slicer support evaluation']}
(O/'design.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))

close=pv.Plotter(off_screen=True,window_size=(1200,650));close.set_background('#f4f6fa')
t=mesh(badge);close.add_mesh(pv.PolyData(t.vertices,np.column_stack((np.full(len(t.faces),3),t.faces)).ravel()),color='#d5b987',smooth_shading=False)
close.camera_position=[(104,-145,180),(104,-40,-7),(0,0,1)];close.enable_parallel_projection();close.reset_camera();close.screenshot(str(O/'relief-detail.png'));close.close()

rear=pv.Plotter(off_screen=True,window_size=(1500,850),shape=(1,2),border=False)
for pane,solid,title in [(0,world(board),'Rear: 9 mm hexagonal through holes'),(1,badge,'Underside: 1.2 mm recesses below relief')]:
 rear.subplot(0,pane);rear.set_background('#f4f6fa');t=mesh(solid);rear.add_mesh(pv.PolyData(t.vertices,np.column_stack((np.full(len(t.faces),3),t.faces)).ravel()),color='#83a4ad' if pane==0 else '#d5b987',smooth_shading=False);rear.add_text(title,font_size=13,color='#243743')
 rear.camera_position=[(350,400,250),(120,20,95),(0,0,1)] if pane==0 else [(120,-140,-200),(120,-40,-7),(0,1,0)];rear.enable_parallel_projection();rear.reset_camera()
rear.screenshot(str(O/'recess-detail.png'));rear.close()
