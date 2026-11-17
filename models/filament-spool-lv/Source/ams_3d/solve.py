import sys,json,time
from pathlib import Path
import os
CODE=Path(__file__).resolve().parent;R=Path(os.environ.get('AMS_OUTPUT',str(CODE/'work'))).resolve();R.mkdir(parents=True,exist_ok=True);pass
import numpy as np
from skfem import MeshTet,Basis,ElementTetP1,ElementVector,asm,LinearForm
from skfem.models.elasticity import linear_elasticity,lame_parameters
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import cg
import pyamg
h=float(sys.argv[1]);angle=float(sys.argv[2]);load=float(sys.argv[3]) if len(sys.argv)>3 else 4.905
z=np.load(R/f'mesh_{h:g}.npz');p=z['p'];t=z['t'];mesh=MeshTet(p.T,t.T);basis=Basis(mesh,ElementVector(ElementTetP1()));E=3349.;nu=.38
print('assemble',len(p),len(t),flush=True);K=asm(linear_elasticity(*lame_parameters(E,nu)),basis).tocsr();n=len(p)
# Volume selfweight; density 1.37e-6 kg/mm3.
@LinearForm
def gravity(v,w):return -1.37e-6*9.81*v[1]
f=asm(gravity,basis)
# Resultant vertical paper-core load on upper external cylinder face band, area-weighted.
fac=mesh.facets[:,mesh.boundary_facets()].T;mid=p[fac].mean(axis=1);rad=np.linalg.norm(mid[:,:2],axis=1)
chosen=(rad>39.85)&(rad<40.1)&(mid[:,2]>2)&(mid[:,2]<30)&(mid[:,1]>20)
ff=fac[chosen];area=np.linalg.norm(np.cross(p[ff[:,1]]-p[ff[:,0]],p[ff[:,2]]-p[ff[:,0]]),axis=1)/2
assert len(ff)>0
for j in range(3):np.add.at(f,3*ff[:,j]+1,-load*area/(3*area.sum()))
# Two assumed roller patches at +/-angle from downward vertical, ±2deg angular half-width.
r=np.linalg.norm(p[:,:2],axis=1);a=np.degrees(np.arctan2(p[:,0],-p[:,1]));support=(r>99.9)&(np.abs(np.abs(a)-angle)<2.)
ids=np.where(support)[0];assert len(ids)>3
# Rotate each support's xy basis to radial/tangential; eliminate radial DOF only.
rows=[];cols=[];values=[]
for i in range(n):
 if support[i]:
  nx,ny=p[i,:2]/r[i];rows.extend([3*i,3*i,3*i+1,3*i+1,3*i+2]);cols.extend([3*i,3*i+1,3*i,3*i+1,3*i+2]);values.extend([nx,-ny,ny,nx,1])
 else:
  rows.extend([3*i,3*i+1,3*i+2]);cols.extend([3*i,3*i+1,3*i+2]);values.extend([1,1,1])
Q=coo_matrix((values,(rows,cols)),shape=K.shape).tocsr();A=(Q.T@K@Q).tocsr();b=Q.T@f
# Ideal mirror symmetry at the far core end (uz=0), plus one tangential gauge for rigid roll rotation. This assumes a continuous symmetric hub, NOT the actual bayonet.
pin=ids[np.argmin(p[ids,2])];fixed=np.unique(np.r_[3*ids,3*pin+1,3*np.where(p[:,2]>33.49)[0]+2]);free=np.setdiff1d(np.arange(3*n),fixed);Af=A[free][:,free];bf=b[free]
print('AMG',Af.shape,flush=True);modes=np.zeros((3*n,6)); modes[0::3,0]=1; modes[1::3,1]=1; modes[2::3,2]=1; modes[1::3,3]=-p[:,2]; modes[2::3,3]=p[:,1]; modes[0::3,4]=p[:,2]; modes[2::3,4]=-p[:,0]; modes[0::3,5]=-p[:,1]; modes[1::3,5]=p[:,0]; ml=pyamg.smoothed_aggregation_solver(Af,B=(Q.T@modes)[free],max_coarse=200);its=[0]
def cb(x):
 its[0]+=1
 if its[0]%100==0: print("iteration",its[0],flush=True)
prior=R/f'symmetric_result_h{h:g}_a{angle:g}_f{load:g}.npz';initial=(Q.T@np.load(prior)['u'].reshape(-1))[free] if prior.exists() else None
uf,info=cg(Af,bf,x0=initial,M=ml.aspreconditioner(),rtol=1e-8,atol=1e-10,maxiter=2000,callback=cb)
v=np.zeros(3*n);v[free]=uf;u=(Q@v).reshape(-1,3);reaction=(A@v-b)[3*ids];res=np.linalg.norm((A@v-b)[free]);print('solved',info,its,res,flush=True)
# Compression-only active-set correction within candidate contact patches.
active=ids.copy(); contact_iterations=0
for contact_iterations in range(1,7):
 raw=A@v-b
 tension=active[raw[3*active]>1e-7]
 released=np.setdiff1d(ids,active)
 penetrate=released[v[3*released]>1e-8]
 if len(tension)==0 and len(penetrate)==0:break
 active=np.union1d(np.setdiff1d(active,tension),penetrate)
 fixed=np.unique(np.r_[3*active,3*pin+1,3*np.where(p[:,2]>33.49)[0]+2]);free=np.setdiff1d(np.arange(3*n),fixed);Af=A[free][:,free];bf=b[free]
 ml=pyamg.smoothed_aggregation_solver(Af,B=(Q.T@modes)[free],max_coarse=200)
 uf,info=cg(Af,bf,x0=v[free],M=ml.aspreconditioner(),rtol=1e-8,atol=1e-10,maxiter=2000,callback=cb)
 v=np.zeros(3*n);v[free]=uf
 print('contact',contact_iterations,len(active),info,flush=True)
u=(Q@v).reshape(-1,3);reaction=(A@v-b)[3*active];res=np.linalg.norm((A@v-b)[free])
released=np.setdiff1d(ids,active)
penetration=float(max(0.,v[3*released].max())) if len(released) else 0.
contact_converged=bool(info==0 and res<1e-7 and np.all(reaction<=1e-7) and penetration<=1e-8)
ids=active
# Tetra P1 constant strain/stress; not stress-convergence proof.
field=basis.interpolate(u.reshape(-1));g=field.grad.mean(axis=-1);eps=(g+g.swapaxes(0,1))/2;lam,mu=lame_parameters(E,nu);stress=2*mu*eps+lam*np.eye(3)[:,:,None]*np.trace(eps,axis1=0,axis2=1)[None,None,:];dev=stress-np.eye(3)[:,:,None]*np.trace(stress,axis1=0,axis2=1)[None,None,:]/3;vm=np.sqrt(1.5*np.sum(dev*dev,axis=(0,1)))
result={'mesh_h_mm':h,'angle_deg':angle,'coil_load_per_half_N':load,'total_vertical_load_N':float(-f[1::3].sum()),'nodes':n,'tetrahedra':len(t),'support_nodes':len(ids),'cg_info':int(info),'iterations':its[0],'free_residual_N':float(res),'max_displacement_mm':float(np.linalg.norm(u,axis=1).max()),'max_axial_displacement_mm':float(abs(u[:,2]).max()),'peak_von_mises_MPa':float(vm.max()),'p99_von_mises_MPa':float(np.percentile(vm,99)),'normal_reaction_min_N':float(reaction.min()),'normal_reaction_max_N':float(reaction.max()),'tensile_support_nodes':int(sum(reaction>1e-6)),'contact_converged':contact_converged,'contact_iterations':contact_iterations,'max_released_radial_penetration_mm':float(max(0.,v[3*released].max())) if len(released) else 0.,'note':'Compression-only active-set over assumed radial patches; convergence must check reaction sign and released-node penetration. Mirror-symmetric half-spool with ideal hub continuity; no actual lock contact.'}
name=f'contact_result_h{h:g}_a{angle:g}_f{load:g}';(R/(name+'.json')).write_text(json.dumps(result,indent=2));np.savez_compressed(R/(name+'.npz'),p=p,t=t,u=u,vm=vm,support=ids,load_faces=ff);print(json.dumps(result),flush=True)

if not contact_converged: raise RuntimeError("Contact/linear solve did not pass final checks; results are NOT validated")
