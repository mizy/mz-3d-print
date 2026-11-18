import numpy as np,cadquery as cq,math,json
from shapely.geometry import LineString

def fit_wire(xy,z,tol=.012):
 p=np.array(xy)
 if np.linalg.norm(p[0]-p[-1])<1e-7:p=p[:-1]
 # Remove mesh collinearity noise while preserving corners; fitted circle runs replace curved spans.
 p=np.array(LineString(np.vstack((p,p[0]))).simplify(.001,preserve_topology=False).coords)
 # Standardize orientation and seam on +X ray to avoid twisted lofts.
 if np.sum(p[:-1,0]*p[1:,1]-p[1:,0]*p[:-1,1])<0:p=p[::-1].copy()
 for k in range(len(p)-1):
  a,b=p[k],p[k+1]
  if a[1]<=0<b[1]:
   q=a+(b-a)*(-a[1])/(b[1]-a[1])
   if q[0]>0:
    p=np.vstack((q,p[k+1:-1],p[:k+1],q));break
 n=len(p);edges=[];i=0;err=0
 while i<n-1:
  best=(i+1,None,0.)
  for j in range(i+2,n):
   q=p[i:j+1];a,b=q[0],q[-1];delta=b-a;length=np.linalg.norm(delta)
   if length<1e-6:break
   lineerr=np.max(abs((q[:,0]-a[0])*delta[1]-(q[:,1]-a[1])*delta[0]))/length
   projection=((q-a)@delta)/(length*length)
   line_monotonic=(np.min(projection)>=-tol/length and np.max(projection)<=1+tol/length and np.min(np.diff(projection))>=-tol/length)
   if lineerr<tol and line_monotonic:
    best=(j,None,float(lineerr));continue
   mid=q[len(q)//2]
   try:center=np.linalg.solve(2*np.array([mid-a,b-a]),np.array([np.dot(mid,mid)-np.dot(a,a),np.dot(b,b)-np.dot(a,a)]))
   except np.linalg.LinAlgError:break
   rad=np.linalg.norm(a-center);qcheck=np.vstack((q,(q[:-1]+q[1:])/2));dev=np.max(abs(np.linalg.norm(qcheck-center,axis=1)-rad));ang=np.unwrap(np.arctan2(q[:,1]-center[1],q[:,0]-center[0]));sweep=abs(ang[-1]-ang[0])
   angular_diff=np.diff(ang)*np.sign(ang[-1]-ang[0])
   if dev>tol or sweep>math.pi*.8 or rad>1e5 or np.min(angular_diff)<-tol/max(rad,1e-6):break
   best=(j,mid,float(dev))
  j,m,e=best
  if m is None:edge=cq.Edge.makeLine(cq.Vector(*p[i],z),cq.Vector(*p[j],z))
  else:edge=cq.Edge.makeThreePointArc(cq.Vector(*p[i],z),cq.Vector(*m,z),cq.Vector(*p[j],z))
  edges.append(edge);err=max(err,e);i=j
 w=cq.Wire.assembleEdges(edges);return w,{'edges':len(edges),'fit_radial_residual_mm':float(err),'source_points':len(xy)}
if __name__=='__main__':
 d=json.load(open('/tmp/chanel-interface-input/profiles.json'));log={}
 for part in ['wide','narrow']:
  ws=[];log[part]=[]
  for s in d[part]['sections']:
   z=s['z']
   if part=='wide' and z>37:continue
   if part=='narrow' and z<28:continue
   loop=min(s['loops'],key=lambda l:l['mean_r']) if part=='wide' else max(s['loops'],key=lambda l:l['mean_r'])
   w,r=fit_wire(loop['points_xy'],z);ws.append(w);r['z']=z;log[part].append(r);print(part,r,flush=True)
  try:
   loft=cq.Solid.makeLoft(ws,ruled=True);print('LOFT',part,loft.isValid(),len(loft.Faces()),flush=True);cq.exporters.export(loft,f'/tmp/chanel-interface-input/{part}_interface_loft_test.step')
  except Exception as e:print(type(e),str(e),flush=True)
 print(json.dumps(log))
