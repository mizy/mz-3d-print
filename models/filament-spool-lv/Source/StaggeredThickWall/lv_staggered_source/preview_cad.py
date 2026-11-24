from model_paths import MODELS_DIR
from pathlib import Path
import cadquery as cq,numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
R=MODELS_DIR
fig=plt.figure(figsize=(14,7),facecolor='#f4f6fa')
for idx,part in enumerate(('wide','narrow')):
 ax=fig.add_subplot(1,2,idx+1,projection='3d');s=cq.Shape.importBrep(str(R/(part+'_hub.brep')))
 # Remove one quadrant for illustration only; deliverable remains complete.
 s=s.cut(cq.Workplane('XY').box(50,50,60,centered=(False,False,False)).translate((0,-50,0)).val())
 v,t=s.tessellate(.15,.15);v=np.array([[p.x,p.y,p.z] for p in v]);tri=v[np.array(t)]
 normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-9);light=np.array([.3,-.5,1]);light/=np.linalg.norm(light);shade=.45+.55*np.abs(normals@light);centers=tri.mean(axis=1);rad=np.sqrt(centers[:,0]**2+centers[:,1]**2);base=np.where((rad>36.4)[:,None],np.array([.2,.5,.8]),np.array([.85,.54,.22]));colors=np.clip(shade[:,None]*base+.12,0,1)
 ax.add_collection3d(Poly3DCollection(tri,facecolors=colors,edgecolors='none'))
 ax.set(xlim=(-43,43),ylim=(-43,43),zlim=(0,43));ax.set_box_aspect((86,86,43));ax.view_init(20,45);ax.set_axis_off();ax.set_title(part.upper()+' | CAD cutaway',fontsize=15)
fig.suptitle('LV tall open arches | 22.5-degree stagger | no broad roof membrane',fontsize=18)
fig.text(.5,.035,'CAD cutaway: blue outer shell, amber inner shell; one connected solid per half. No slicing.',ha='center',fontsize=11)
fig.savefig(R/'LV_OPEN_ARCH_CUTAWAY.png',dpi=150,bbox_inches='tight');plt.close(fig)
