from pathlib import Path
import struct, numpy as np,json
R=Path(__file__).parent;report={}
for p in R.glob('*PROTOTYPE.stl'):
 data=p.read_bytes();n=struct.unpack('<I',data[80:84])[0]
 f=np.frombuffer(data[84:],dtype=np.dtype([('n','<f4',3),('v','<f4',(3,3)),('a','<u2')]),count=n)['v'].astype(float)
 v,ix=np.unique(np.round(f.reshape(-1,3),6),axis=0,return_inverse=True);t=ix.reshape(-1,3)
 edges=np.sort(np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]),axis=1);e,c=np.unique(edges,axis=0,return_counts=True)
 report[p.name]={'triangles':n,'vertices':len(v),'boundary_edges':int(sum(c==1)),'nonmanifold_edges':int(sum(c>2)),'bbox_mm':(v.max(axis=0)-v.min(axis=0)).tolist(),'self_intersection_test':'not run'}
(R/'mesh_validation.json').write_text(json.dumps(report,indent=2));print(report)
