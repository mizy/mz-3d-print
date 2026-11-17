from pathlib import Path
import sys,json
R=Path(__file__).parent;sys.path.insert(0,str(R/'deps'))
import trimesh,numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
out={}
for k in ['wide','narrow']:
 m=trimesh.load(R/f'official_{k}_clean.stl');v0=m.volume;splits=[]
 for it in range(500):
  edges,inv,count=np.unique(m.edges_sorted,axis=0,return_inverse=True,return_counts=True);bad=edges[count!=2]
  if len(bad)==0:break
  assert np.all(count[count!=2]==1),(k,'non-boundary defect')
  bv=np.unique(bad);ii=np.searchsorted(bv,bad);gg=coo_matrix((np.ones(len(ii)),(ii[:,0],ii[:,1])),shape=(len(bv),len(bv)));_,labels=connected_components(gg,directed=False);best=None
  for edge in bad:
   a,b=m.vertices[edge];d=b-a;dd=d@d
   if dd<1e-15:continue
   candidate=bv[(labels==labels[np.searchsorted(bv,edge[0])]) & ~np.isin(bv,edge)];v=m.vertices[candidate];t=(v-a)@d/dd;dist=np.linalg.norm(v-(a+t[:,None]*d),axis=1);ok=(t>1e-8)&(t<1-1e-8)&(dist<.0000001)
   if not ok.any():continue
   ids=np.where(ok)[0];q=ids[np.argmin(dist[ids])]
   if best is None or dist[q]<best[0]:best=(float(dist[q]),edge,int(candidate[q]))
  if best is None:print('UNRESOLVED',k,it,len(bad),flush=True);break
  err,edge,c=best
  fid=np.where(np.sum(np.isin(m.faces,edge),axis=1)==2)[0];assert len(fid)==1,(k,edge,fid)
  fi=int(fid[0]);face=m.faces[fi].copy()
  for j in range(3):
   a,b,d=int(face[j]),int(face[(j+1)%3]),int(face[(j+2)%3])
   if {a,b}==set(edge.tolist()):break
  faces=m.faces.copy();faces[fi]=[a,c,d];faces=np.vstack([faces,[c,b,d]])
  m=trimesh.Trimesh(vertices=m.vertices.copy(),faces=faces,process=False);splits.append(err)
  if it%25==0:print('SPLIT',k,it,len(bad),err,flush=True)
 edges,cnt=np.unique(m.edges_sorted,axis=0,return_counts=True)
 report={'split_count':len(splits),'max_perpendicular_error_mm':max(splits,default=0),'volume_delta_mm3':float(m.volume-v0),'watertight':bool(m.is_watertight),'non_two_edges':int((cnt!=2).sum()),'degenerate_faces':int((~m.nondegenerate_faces(height=1e-8)).sum()),'faces':len(m.faces)}
 m.export(R/f'official_{k}_stitched.stl');out[k]=report;print('DONE',k,report,flush=True)
(R/'stitch_audit.json').write_text(json.dumps(out,indent=2))
