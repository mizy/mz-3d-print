from pathlib import Path
import zipfile,xml.etree.ElementTree as E,json,numpy as np,trimesh,hashlib
D=Path('/tmp/chanel_105g_preprint');src=Path('/private/var/folders/qg/mkcmjftx4gg9q6pg2_xm8hfw0000gn/T/bamboo_model/Wed_Nov_18/11_43_17#52437#57/3D/Objects/object_2.model');z=zipfile.ZipFile(src);xml=z.read(z.namelist()[0]);(D/'studio_mesh.xml').write_bytes(xml);r=E.fromstring(xml);ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'};out={}
for o in r.findall('.//m:object',ns):
 mesh=o.find('m:mesh',ns)
 if mesh is None:continue
 v=np.array([[float(x.attrib[k]) for k in ['x','y','z']] for x in mesh.find('m:vertices',ns)]);f=np.array([[int(x.attrib[k]) for k in ['v1','v2','v3']] for x in mesh.find('m:triangles',ns)]);id=o.attrib['id'];row={'vertices':len(v),'faces':len(f),'bounds':[v.min(axis=0).tolist(),v.max(axis=0).tolist()],'tests':[]}
 for decimals in [None,8,6,5,4]:
  if decimals is None:vv,ff=v,f
  else:vv,inv=np.unique(np.round(v,decimals),axis=0,return_inverse=True);ff=inv[f]
  edges=np.sort(np.concatenate([ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]]]),axis=1);ue,cnt=np.unique(edges,axis=0,return_counts=True);boundary=ue[cnt==1];nonman=ue[cnt>2];pts=vv[boundary];lens=np.linalg.norm(pts[:,1]-pts[:,0],axis=1) if len(pts) else np.zeros(0)
  rr={'weld_decimals':decimals,'boundary_edges':len(boundary),'nonmanifold_edges':len(nonman),'boundary_length_mm':float(lens.sum()),'max_boundary_edge_mm':float(lens.max()) if len(lens) else 0}
  if len(pts):rr['boundary_bbox']=[pts.reshape(-1,3).min(axis=0).tolist(),pts.reshape(-1,3).max(axis=0).tolist()]
  row['tests'].append(rr)
  if decimals==6:
   np.savez_compressed(D/('mesh_'+id+'.npz'),vertices=vv,faces=ff,boundary=boundary)
   row['volume_mm3']=float(trimesh.Trimesh(vv,ff,process=False).volume)
 out[id]=row;print(id,row,flush=True)
(D/'studio_mesh_audit.json').write_text(json.dumps(out,indent=2))
