exec(open('/tmp/chanel_official_native/assembly_check.py').read().split('for h,a in')[0])
for h,angles in [(70,range(40,56)),(68,range(44,54)),(71,range(44,54)),(66.4,[-2,-1,-.5,0,.5,1,2,3,4,5,6,7,8])]:
 for a in angles:
  c=w.intersect(place(h,a));sol=c.Solids();row={'H':h,'angle':a,'valid':c.isValid(),'volume':sum(s.Volume() for s in sol),'overlap_bbox':[[s.BoundingBox().xmin,s.BoundingBox().xmax,s.BoundingBox().ymin,s.BoundingBox().ymax,s.BoundingBox().zmin,s.BoundingBox().zmax] for s in sol]};rows.append(row);print(row,flush=True);(D/'assembly_scan.json').write_text(json.dumps(rows,indent=2))
