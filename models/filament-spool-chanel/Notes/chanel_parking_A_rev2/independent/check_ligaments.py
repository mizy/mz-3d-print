import cadquery as cq,math,json
p='/tmp/chanel_parking_light/revised_output/CHANEL_OFFICIAL_LIGHT_PARKING_A_TRIAL.step';s=max(cq.importers.importStep(p).val().Solids(),key=lambda s:s.BoundingBox().zlen);s=s.translate((-s.BoundingBox().center.x,-s.BoundingBox().center.y,0));a=math.sqrt(96**2-15**2);ur=(a/96,15/96);ut=(-ur[1],ur[0]);out=[]
for t,z in [(3.5,2.15),(4,2.15),(5,2.15),(8,2.15),(10,2.15),(4,3.55),(10,3.55)]:
 def point(x):return cq.Vector(x*ur[0]+t*ut[0],x*ur[1]+t*ut[1],z)
 line=cq.Edge.makeLine(point(94),point(101));common=s.intersect(line);intervals=[]
 for e in common.Edges():
  q=[e.startPoint(),e.endPoint()];xx=sorted(v.x*ur[0]+v.y*ur[1] for v in q);intervals.append(xx)
 row={'tangent_distance_mm':t,'height_mm':z,'material_intervals_along_radial_coordinate_mm':sorted(intervals),'interval_widths_mm':[b-a for a,b in sorted(intervals)]};out.append(row);print(row,flush=True)
open('/tmp/chanel_parking_review/revised_ligament_samples.json','w').write(json.dumps(out,indent=2))
