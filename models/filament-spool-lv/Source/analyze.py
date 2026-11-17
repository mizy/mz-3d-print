"""Reproducible screening only: 2D small-strain isotropic plane-stress surrogate.
Not a 3D FDM strength certification. mm, N, MPa. Requires cadquery, triangle,
shapely, numpy, scipy, matplotlib. See engineering_report.md for limitations.
"""
import sys,json,math
from pathlib import Path
import cadquery as cq,numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
R=Path(__file__).parent;sys.path.append(str(R/'analysis_deps'))
import triangle
from shapely.geometry import Polygon
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
source=R/'A_wide_PROTOTYPE.step'
s=cq.importers.importStep(str(source)).val();face=[f for f in s.Faces() if abs(f.Center().z)<1e-5 and abs(f.normalAt().z)>.99][0]
wires=[face.outerWire()]+face.innerWires();verts=[];segs=[];marks=[];holes=[]
for i,w in enumerate(wires):
 pts,_=w.sample(.015);p=np.array([[v.x,v.y] for v in pts]);p=p[np.r_[True,np.linalg.norm(np.diff(p,axis=0),axis=1)>1e-7]]
 if np.linalg.norm(p[0]-p[-1])<1e-7:p=p[:-1]
 poly=Polygon(p)
 marker=1 if i==0 else (2 if poly.area>1000 else 3)
 if i:holes.append(list(poly.representative_point().coords)[0])
 n=len(verts);verts.extend(p.tolist());segs.extend([[n+j,n+(j+1)%len(p)] for j in range(len(p))]);marks.extend([marker]*len(p))
base={'vertices':verts,'segments':segs,'segment_markers':marks,'holes':holes}
results=[]
for mesharea in [5,2]:
 tr=triangle.triangulate(base,f'pq25a{mesharea}');p=tr['vertices'];tri=tr['triangles'];vm=tr['vertex_markers'].ravel();n=len(p)
 xy=p[tri];x=xy[:,:,0];y=xy[:,:,1];a=.5*((x[:,1]-x[:,0])*(y[:,2]-y[:,0])-(x[:,2]-x[:,0])*(y[:,1]-y[:,0]));assert np.all(a>0)
 b=np.column_stack([y[:,1]-y[:,2],y[:,2]-y[:,0],y[:,0]-y[:,1]])/(2*a[:,None]);c=np.column_stack([x[:,2]-x[:,1],x[:,0]-x[:,2],x[:,1]-x[:,0]])/(2*a[:,None])
 B=np.zeros((len(tri),3,6));B[:,0,0::2]=b;B[:,1,1::2]=c;B[:,2,0::2]=c;B[:,2,1::2]=b
 cent=xy.mean(axis=1);rad=np.linalg.norm(cent,axis=1);t=np.ones(len(tri));t[(rad>97)|((rad>40)&((abs(cent[:,0])<1.2)|(abs(cent[:,1])<1.2)))]=2
 E=3349.;nu=.38;D=E/(1-nu**2)*np.array([[1,nu,0],[nu,1,0],[0,0,(1-nu)/2]])
 ke=np.einsum('eji,jk,ekl->eil',B,D,B)*(a*t)[:,None,None];dof=(tri[:,:,None]*2+np.arange(2)).reshape(-1,6)
 K=coo_matrix((ke.ravel(),(np.repeat(dof,6,axis=1).ravel(),np.tile(dof,(1,6)).ravel())),shape=(2*n,2*n)).tocsr()
 supports=np.where((vm==1)&(abs(p[:,0])>=44)&(abs(p[:,0])<=56)&(p[:,1]<-75))[0];assert len(supports)>2
 pin=supports[np.argmin(p[supports,0])];fixed=np.r_[2*supports+1,2*pin];free=np.setdiff1d(np.arange(2*n),fixed)
 core=np.where(vm==2)[0];force=np.zeros(2*n);force[2*core+1]=-5.45/len(core)
 u=np.zeros(2*n);u[free]=spsolve(K[free][:,free],force[free]);stress=np.einsum('ij,ejk,ek->ei',D,B,u[dof]);sx,sy,tau=stress.T;von=np.sqrt(sx*sx-sx*sy+sy*sy+3*tau*tau);disp=np.linalg.norm(u.reshape(-1,2),axis=1)
 reaction=K@u-force;equilibrium=float(reaction[2*supports+1].sum());residual=float(np.linalg.norm((K@u-force)[free]));away=np.min(np.linalg.norm(cent[:,None,:]-p[supports][None,:,:],axis=2),axis=1)>5
 result={'max_triangle_area_mm2':mesharea,'nodes':n,'elements':len(tri),'area_mm2':float(a.sum()),'load_per_flange_N':5.45,'support_y_reaction_N':equilibrium,'free_residual_norm_N':residual,'max_inplane_displacement_mm':float(disp.max()),'max_von_mises_MPa':float(von.max()),'p99_von_mises_MPa':float(np.percentile(von,99)),'max_stress_excluding_5mm_support_zone_MPa':float(von[away].max()),'material_E_MPa':E,'poisson_assumption':nu,'support_nodes':len(supports),'core_load_nodes':len(core)}
 results.append(result);print(result,flush=True)
 if mesharea==2:
  np.savez(R/'fea_mesh.npz',p=p,tri=tri)
  fig,axs=plt.subplots(1,2,figsize=(12,5),constrained_layout=True)
  for ax,val,label in [(axs[0],von,'Plane stress von Mises (MPa)'),(axs[1],disp[tri].mean(axis=1),'In-plane displacement (mm)')]:
   im=ax.tripcolor(p[:,0],p[:,1],tri,facecolors=val,shading='flat',cmap='viridis');ax.scatter(p[supports,0],p[supports,1],s=8,c='red');ax.set_aspect('equal');ax.set_title(label);ax.set_xlabel('mm');fig.colorbar(im,ax=ax)
  fig.suptitle('1 kg coil + spool / two flanges: 5.45 N each | SCREENING, not safety proof');fig.savefig(R/'plane_stress_screening.png',dpi=160);plt.close(fig)
# Off-axis misuse screening: four cantilever T-ribs without plate load sharing.
def tsection():
 A1=10*1;A2=2.4*1;yc=(A1*.5+A2*1.5)/(A1+A2);I=10/12+A1*(.5-yc)**2+2.4/12+A2*(1.5-yc)**2;return yc,I
neutral,I=tsection();F=9.81/4;L=58;Eflex=1995
beam={'model':'four independent 58mm cantilevers, each 10x1mm skin +2.4x1mm top rib; NOT full plate FEA','load_total_N':9.81,'load_each_N':F,'I_mm4':I,'nominal_bending_stress_MPa':F*L*max(neutral,2-neutral)/I,'linear_tip_deflection_mm':F*L**3/(3*Eflex*I),'warning':'Large predicted displacement invalidates small-deflection assumptions; shows plate flexibility/load-sharing sensitivity, not actual spool deflection.'}
(R/'analysis_results.json').write_text(json.dumps({'plane_stress_mesh_study':results,'off_axis_beam_screening':beam},indent=2));print(beam)
