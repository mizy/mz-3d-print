import cadquery as cq,numpy as np,trimesh,json,time
from pathlib import Path
from scipy.ndimage import minimum_filter1d,maximum_filter1d
D=Path('/tmp/chanel_assembly_v6');t=time.time();H=66.430113973
centers={'wide':[-.0273430863,.0010603425],'narrow':[.0015810415,-.0274228517]}
# Dense radial envelope from real v6 native pipe tessellation, not the original source approximation.
N=3600;angles=np.arange(N)*2*np.pi/N
for part in ['wide','narrow']:
 if (D/f'{part}_radial.npz').exists():continue
 path=D/f'{part}_pipe_mesh.npz'
 if not path.exists():
  s=cq.importers.importBrep('/tmp/chanel_compact_v6/'+part+'_analytic_base.brep').val();v,f=s.tessellate(.003,.03);v=np.array([[x.x,x.y,x.z] for x in v]);f=np.array(f);np.savez_compressed(path,vertices=v,faces=f);print('mesh',part,len(v),len(f),flush=True)
 a=np.load(path);m=trimesh.Trimesh(a['vertices'],a['faces'],process=False)
 zs=np.arange(21.95 if part=='wide' else 23.95,37.2649566101 if part=='wide' else 34.1129523682,.025)+.00013
 radii=[]; zz=m.vertices[:,2]; tri_z=zz[m.faces]; zmin=tri_z.min(axis=1);zmax=tri_z.max(axis=1)
 for zi,z in enumerate(zs):
  ids=np.flatnonzero((zmin<=z)&(zmax>=z))
  seg=trimesh.intersections.mesh_plane(m,[0,0,1],[0,0,float(z)],local_faces=ids,cached_dots=zz-z)[:,:,:2]-centers[part]
  r=np.linalg.norm(seg,axis=2)
  good=np.max(r,axis=1)<32.5 if part=='wide' else np.min(r,axis=1)>28.8
  seg=seg[good];r=r[good]
  # Collect exact edge/ray intersections, preserving radial segment extrema.
  rr=np.full(N,np.inf if part=='wide' else -np.inf)
  for q,rad in zip(seg,r):
   aa=np.arctan2(q[:,1],q[:,0]);delta=(aa[1]-aa[0]+np.pi)%(2*np.pi)-np.pi
   lo=min(aa[0],aa[0]+delta);hi=max(aa[0],aa[0]+delta)
   inds=np.arange(int(np.ceil(lo*N/(2*np.pi)-1e-8)),int(np.floor(hi*N/(2*np.pi)+1e-8))+1)
   if not len(inds):continue
   theta=inds*2*np.pi/N;direc=np.column_stack([np.cos(theta),np.sin(theta)]);edge=q[1]-q[0]
   den=direc[:,0]*edge[1]-direc[:,1]*edge[0]
   dist=(q[0,0]*edge[1]-q[0,1]*edge[0])/den
   if part=='wide':np.minimum.at(rr,inds%N,dist)
   else:np.maximum.at(rr,inds%N,dist)
  if not np.isfinite(rr).all():
   missing=np.flatnonzero(~np.isfinite(rr))
   if len(missing)>5:raise RuntimeError((part,z,len(missing)))
   print('SEAM_RAY_FILL',part,z,missing.tolist(),flush=True)
   for index in missing:
    neighbours=rr[np.array([index-1,index+1])%N];neighbours=neighbours[np.isfinite(neighbours)]
    if not len(neighbours):raise RuntimeError('No seam neighbours')
    rr[index]=np.min(neighbours) if part=='wide' else np.max(neighbours)
  radii.append(rr)
  if zi%100==0:print('progress',part,zi,'of',len(zs),'time',time.time()-t,flush=True)
 radii=np.array(radii);np.savez_compressed(D/f'{part}_radial.npz',z=zs,r=radii);print('profiles',part,len(zs),'time',time.time()-t,flush=True)
w=np.load(D/'wide_radial.npz');n=np.load(D/'narrow_radial.npz');report=[]
# Across entire axial overlap, interpolate dense .025mm height profiles; angular grid .1deg.
for height in [H,H+.1,H+.25,H+.5,H+1,H+1.5,H+2,H+3,H+4,H+5,H+6]:
 zw=np.arange(max(w['z'][0],height-n['z'][-1]),min(w['z'][-1],height-n['z'][0]),.025)
 if not len(zw):continue
 wi=np.clip(np.searchsorted(w['z'],zw)-1,0,len(w['z'])-2);wf=(zw-w['z'][wi])/(w['z'][wi+1]-w['z'][wi]);wr=w['r'][wi]*(1-wf[:,None])+w['r'][wi+1]*wf[:,None]
 zn=height-zw;ni=np.clip(np.searchsorted(n['z'],zn)-1,0,len(n['z'])-2);nf=(zn-n['z'][ni])/(n['z'][ni+1]-n['z'][ni]);nr=n['r'][ni]*(1-nf[:,None])+n['r'][ni+1]*nf[:,None]
 nr=nr[:,(-np.arange(N))%N] # Rx180 reflects angle
 vals=[]
 for shift in range(0,1800,5):
  clearance=wr-np.roll(nr,shift,axis=1);ix=np.unravel_index(np.argmin(clearance),clearance.shape);vals.append({'theta_deg':shift/10,'min_radial_clearance_mm':float(clearance[ix]),'worst_z':float(zw[ix[0]]),'worst_angle_deg':ix[1]/10})
 best=max(vals,key=lambda x:x['min_radial_clearance_mm']);row={'H':height,'best':best,'sampled_nonnegative_angles':[x['theta_deg'] for x in vals if x['min_radial_clearance_mm']>=0],'scan':vals};report.append(row);print('SCAN',height,best,'free',len(row['sampled_nonnegative_angles']),flush=True)
(D/'radial_scan.json').write_text(json.dumps({'H_stop':H,'angular_grid_deg':.1,'pose_rotation_step_deg':.5,'height_profile_step_mm':.025,'relative_deflection_parameter':.003,'angular_deflection_radians':.03,'results':report},indent=2));print('DONE',time.time()-t,flush=True)
