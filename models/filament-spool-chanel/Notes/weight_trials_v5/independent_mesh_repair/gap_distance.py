import zipfile,xml.etree.ElementTree as E,numpy as np,json
from pathlib import Path
D=Path('/tmp/chanel_105g_preprint');r=E.fromstring((D/'studio_mesh.xml').read_bytes());ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'};o=r.find('.//m:object',ns);m=o.find('m:mesh',ns);v=np.array([[float(x.attrib[k]) for k in ['x','y','z']] for x in m.find('m:vertices',ns)]);f=np.array([[int(x.attrib[k]) for k in ['v1','v2','v3']] for x in m.find('m:triangles',ns)]);e=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);ue,c=np.unique(e,axis=0,return_counts=True);be=ue[c==1];seg=v[be];a=seg[:,0];d=seg[:,1]-a;den=(d*d).sum(axis=1);res=[]
for i,(aa,dd) in enumerate(zip(a,d)):
 errs=[]
 for t in [.25,.5,.75]:
  p=aa+t*dd;u=np.clip(((p-a)*d).sum(axis=1)/den,0,1);dist=np.linalg.norm(p-(a+u[:,None]*d),axis=1);dist[i]=np.inf;errs.append(float(dist.min()))
 res.append(max(errs))
out={'edges':len(be),'max_sampled_distance_to_other_boundary_segment_mm':max(res),'median_mm':float(np.median(res)),'details_mm':res,'note':'Sampled proximity of boundary segments, not a manifold repair or dimensional guarantee.'};(D/'boundary_gap_proximity.json').write_text(json.dumps(out,indent=2));print(out)
