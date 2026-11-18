from pathlib import Path
import numpy as np,xml.etree.ElementTree as E,trimesh,json
from scipy.spatial import cKDTree
D=Path('/tmp/chanel_105g_preprint');r=E.fromstring((D/'studio_mesh.xml').read_bytes());ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'};o=r.find('.//m:object',ns);m=o.find('m:mesh',ns);V=np.array([[float(x.attrib[k]) for k in ['x','y','z']] for x in m.find('m:vertices',ns)]);F=np.array([[int(x.attrib[k]) for k in ['v1','v2','v3']] for x in m.find('m:triangles',ns)])
def edges(f):
 ee=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);u,c=np.unique(ee,axis=0,return_counts=True);return u[c==1],int(np.sum(c>2))
def stats(v,f):
 e,n=edges(f);m=trimesh.Trimesh(v,f,process=False);return {'faces':len(f),'boundary':len(e),'nonmanifold':n,'volume':float(m.volume),'winding_consistent':bool(m.is_winding_consistent),'watertight':bool(m.is_watertight),'bounds':m.bounds.tolist()}
base=stats(V,F);print('BASE',base,flush=True);results=[]
for tol in [1e-7,5e-7,1e-6,2e-6,3e-6,5e-6,1e-5]:
 v=V.copy();f=F.copy();e,_=edges(f);ids=np.unique(e);parent=np.arange(len(v));maxdist=0;merges=0;splits=0;deleted=0
 def root(i):
  while parent[i]!=i:i=parent[i]
  return i
 for ii,jj in cKDTree(v[ids]).query_pairs(tol):
  a,b=root(ids[ii]),root(ids[jj])
  if a!=b:parent[max(a,b)]=min(a,b);merges+=1
 remap=np.array([root(i) for i in range(len(v))]);maxdist=float(np.linalg.norm(v-v[remap],axis=1).max());f=remap[f]
 keep=(f[:,0]!=f[:,1])&(f[:,1]!=f[:,2])&(f[:,0]!=f[:,2]);deleted=int(np.sum(~keep));f=f[keep]
 for iteration in range(5):
  e,n=edges(f)
  if len(e)==0:break
  ids=np.unique(e);work={};maxoff=0
  for a,b in e:
   dv=v[b]-v[a];den=dv@dv
   if den==0:continue
   t=((v[ids]-v[a])@dv)/den;dist=np.linalg.norm(v[ids]-(v[a]+t[:,None]*dv),axis=1);ok=(t>1e-8)&(t<1-1e-8)&(dist<=tol)&(ids!=a)&(ids!=b)
   if ok.any():
    cand=ids[ok][np.argsort(t[ok])];work[(a,b)]=cand;maxoff=max(maxoff,float(dist[ok].max()))
  if not work:break
  ff=[]
  for tri in f:
   done=False
   for j in range(3):
    a,b,c=int(tri[j]),int(tri[(j+1)%3]),int(tri[(j+2)%3]);key=tuple(sorted([a,b]))
    if key in work:
     seq=work[key] if a<b else work[key][::-1];chain=[a,*seq,b]
     ff.extend([[x,y,c] for x,y in zip(chain[:-1],chain[1:])]);splits+=len(seq);done=True;break
   if not done:ff.append(tri)
  f=np.array(ff);print('ITER',tol,iteration,len(e),'split',splits,flush=True)
 row={'tolerance_mm':tol,'merged_boundary_vertices':merges,'max_vertex_displacement_mm':maxdist,'deleted_collapsed_faces':deleted,'added_triangles':splits,'after':stats(v,f)};results.append(row);print('RESULT',row,flush=True)
 if row['after']['watertight'] and row['after']['winding_consistent'] and row['after']['nonmanifold']==0:
  np.savez_compressed(D/'wide_studio_seam_repaired.npz',vertices=v,faces=f);row['selected']=True;break
(D/'local_seam_repair_report.json').write_text(json.dumps({'baseline':base,'trials':results,'method':'Only boundary vertex welding at stated tolerance, deletion of triangles collapsed by these welds, splitting boundary-adjacent faces at existing near-collinear boundary vertices; no global smoothing, no arbitrary hole fill. Source STEP unchanged.'},indent=2))
