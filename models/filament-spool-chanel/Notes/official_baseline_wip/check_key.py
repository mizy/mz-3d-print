exec(open('/tmp/chanel_official_native/check_flange.py').read().split('report={};mask=')[0])
from shapely.geometry import box
m=trimesh.load('/Users/miaozhuang/Downloads/bambulab_spool_wide.stl');v=m.vertices.copy();m.vertices=np.c_[v[:,1],-v[:,2],m.bounds[1,0]-v[:,0]];s=build_key();v,f=s.tessellate(.001,.01);q=trimesh.Trimesh([[a.x,a.y,a.z] for a in v],f,process=True);mask=box(-3,-45,3,-41.5);rows=[]
for z in [2.6,3.2,4,5,6,6.9,7.1,7.4,7.6,7.75]:
 a=area(m,z).intersection(mask);b=area(q,z).intersection(mask);rows.append({'z':z,'hausdorff_mm':a.boundary.hausdorff_distance(b.boundary),'symmetric_difference_mm2':a.symmetric_difference(b).area})
print(rows);(D/'key_validation.json').write_text(json.dumps(rows,indent=2))
