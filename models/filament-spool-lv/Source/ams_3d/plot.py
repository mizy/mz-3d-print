import numpy as np,sys
from pathlib import Path
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
CODE=Path(__file__).resolve().parent;R=Path(os.environ.get('AMS_OUTPUT',str(CODE/'work'))).resolve();R.mkdir(parents=True,exist_ok=True)
for pth in R.glob('contact_result*.npz'):
 z=np.load(pth);p=z['p'];u=z['u'];s=z['support'];f=z['load_faces'];fig,ax=plt.subplots(1,2,figsize=(11,5));skin=p[:,2]<.01
 im=ax[0].scatter(p[skin,0],p[skin,1],c=np.linalg.norm(u[skin],axis=1),s=1,cmap='viridis');fig.colorbar(im,ax=ax[0],label='displacement mm');ax[0].scatter(p[s,0],p[s,1],s=12,c='red',label='radial support');ax[0].legend();ax[0].set_aspect('equal');ax[0].set_title('Actual perforated flange / deformation magnitude')
 ax[1].scatter(p[::10,2],p[::10,1],s=1,color='gray');ax[1].scatter(p[f].mean(axis=1)[:,2],p[f].mean(axis=1)[:,1],s=1,color='orange',label='core load area');ax[1].scatter(p[s,2],p[s,1],s=12,c='red',label='roller patch');ax[1].set_aspect('equal');ax[1].legend();ax[1].set_xlabel('axial z (mm)');ax[1].set_ylabel('vertical y (mm)');fig.suptitle('3D screening: ideal continuous symmetric hub / NOT lock validation');fig.tight_layout();fig.savefig(pth.with_suffix('.png'),dpi=180);plt.close(fig)
