"""Kirchhoff-Love/Morley linear plate screening. Not actual coil pressure prediction."""
import sys,json
from pathlib import Path
import numpy as np
R=Path(__file__).parent;sys.path.append(str(R/'analysis_deps'))
from skfem import MeshTri,Basis,ElementTriMorley,BilinearForm,LinearForm,asm,condense,solve
from skfem.helpers import dd,ddot,trace
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
z=np.load(R/'fea_mesh.npz');p=z['p'];tri=z['tri'];m=MeshTri(p.T,tri.T);basis=Basis(m,ElementTriMorley(),intorder=4)
E=1995.;nu=.38

def thickness(x):
 r=np.sqrt(x[0]**2+x[1]**2);return np.where((r>97)|((r>40)&((abs(x[0])<1.2)|(abs(x[1])<1.2))),2.,1.)
@BilinearForm
def bend(u,v,w):
 h=thickness(w.x);D=E*h**3/(12*(1-nu**2));return D*((1-nu)*ddot(dd(u),dd(v))+nu*trace(dd(u))*trace(dd(v)))
@LinearForm
def pressure(v,w):
 r=np.sqrt(w.x[0]**2+w.x[1]**2);return ((r>45)&(r<95))*v
A=asm(bend,basis);f=asm(pressure,basis)
# resultant equals sum of loads at vertex displacement DOFs (rotational dofs aren't forces)
force_total=float(f[basis.nodal_dofs[0]].sum());f/=force_total
inner=m.facets_satisfying(lambda x:np.sqrt(x[0]**2+x[1]**2)<38.5,boundaries_only=True);fixed=basis.get_dofs(facets=inner).all()
uvec=solve(*condense(A,f,D=fixed));wvertex=uvec[basis.nodal_dofs[0]]
field=basis.interpolate(uvec);H=field.hess;h=thickness(basis.global_coordinates());D=E*h**3/(12*(1-nu**2));sx=6*D*(H[0,0]+nu*H[1,1])/h**2;sy=6*D*(H[1,1]+nu*H[0,0])/h**2;tau=6*D*(1-nu)*H[0,1]/h**2
vm=np.sqrt(sx*sx-sx*sy+sy*sy+3*tau*tau)
res={'model':'Kirchhoff-Love Morley thin plate; inner edge fully clamped, outer edge free; variable 1/2 mm thickness; isotropic Eflex1995MPa, nu0.38','nodes':len(p),'triangles':len(tri),'dofs':int(basis.N),'loaded_area_mm2':force_total,'unit_axial_force_N':1,'max_abs_deflection_mm_per_N':float(abs(wvertex).max()),'peak_surface_von_mises_MPa_per_N':float(vm.max()),'p99_surface_von_mises_MPa_per_N':float(np.percentile(vm,99)),'force_sweep':[],'limits':['No actual winding tension/coil side pressure known; forces below are independent sensitivity cases, not derived from1kg mass.','Fully clamped core may underestimate displacement compared with real flexible lock.','No geometric nonlinearity, anisotropy, creep, failure/contact, or detailed rounded rib-root stress.','One bending mesh only; not a convergence-certified peak.']}
for force in [1,5,10]:res['force_sweep'].append({'total_axial_force_N':force,'max_abs_deflection_mm_linear':float(abs(wvertex).max()*force),'peak_surface_von_mises_MPa_linear':float(vm.max()*force),'large_deflection_warning':bool(abs(wvertex).max()*force>1)})
(R/'axial_plate_results.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2),flush=True)
fig,ax=plt.subplots(figsize=(7,6));im=ax.tripcolor(p[:,0],p[:,1],tri,wvertex,shading='gouraud',cmap='viridis');ax.set_aspect('equal');fig.colorbar(im,ax=ax,label='mm at 1 N total axial force');ax.set_title('Axial plate SCREENING | inner edge clamped\nNot a predicted full-coil side pressure');fig.tight_layout();fig.savefig(R/'axial_plate_screening.png',dpi=160)
