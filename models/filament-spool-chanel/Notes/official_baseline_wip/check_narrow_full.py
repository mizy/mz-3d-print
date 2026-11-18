exec(open('/tmp/chanel_official_native/check_flange.py').read().split('report={};mask=')[0])
import official_hub as H
s=build_flange('narrow').fuse(H.build_hub('narrow')).clean();print('NARROW',s.isValid(),len(s.Solids()),len(s.Faces()),s.Volume(),flush=True);s.exportBrep(str(D/'narrow_full.brep'));s.exportStep(str(D/'narrow_full.step'),write_pcurves=False);back=cq.importers.importStep(str(D/'narrow_full.step')).val();assert back.isValid() and len(back.Solids())==1;v,f=back.tessellate(.002,.025);m=trimesh.Trimesh([[a.x,a.y,a.z] for a in v],f,process=True);ref=trimesh.load('/Users/miaozhuang/Downloads/bambulab_spool_narrow.stl');v=ref.vertices.copy();ref.vertices=np.c_[v[:,1],v[:,2],v[:,0]-ref.bounds[0,0]];rows=[]
for z in [.2,1.,2.6,2.8,3.2,5,10,16,20.5,21,22.5,24.5,25.8,27.5,29,31,31.5,32,32.5,33,33.5,34]:
 a=area(ref,z);b=area(m,z);row={'z':z,'symmetric_difference_mm2':a.symmetric_difference(b).area,'hausdorff_mm':a.boundary.hausdorff_distance(b.boundary),'reference_area':a.area,'CAD_area':b.area};rows.append(row);print(row,flush=True)
assert max(row['hausdorff_mm'] for row in rows)<.02, 'Narrow full section regression exceeded .02mm'
(D/'narrow_full_sections.json').write_text(json.dumps({'solid_valid':True,'faces':len(back.Faces()),'rows':rows,'mesh_watertight':m.is_watertight,'source_STL_volume':ref.volume,'CAD_volume':s.Volume()},indent=2))
