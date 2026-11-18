import cadquery as cq,math,json
base=cq.importers.importBrep('/tmp/chanel_official_native/light_output/wide.brep').val();new=cq.importers.importBrep('/tmp/chanel_parking_light/revised_output/wide.brep').val();a=math.sqrt(96**2-15**2);ang=math.atan2(15,a);ur=(math.cos(ang),math.sin(ang));ut=(-math.sin(ang),math.cos(ang));rows=[]
for t in [4.,5.,8.]:
 center=(97*ur[0]+t*ut[0],97*ur[1]+t*ut[1],0);plane=cq.Plane(origin=center,xDir=(ur[0],ur[1],0),normal=(0,0,1));w=.02
 box=cq.Workplane(plane).box(6,w,3.6,centered=(True,True,False)).val();areas=[s.intersect(box).Volume()/w for s in [base,new]]
 row={'tangent_distance_mm':t,'slab_thickness_mm':w,'old_section_mm2':areas[0],'new_section_mm2':areas[1],'removed_mm2':areas[0]-areas[1],'loss_fraction':1-areas[1]/areas[0],'nominal_inner_ligament_at_channel_midheight_mm':96.9-1.05-math.sqrt(95**2-t**2)};rows.append(row);print(row,flush=True)
open('/tmp/chanel_parking_review/ring_local_sections_revised.json','w').write(json.dumps(rows,indent=2))
