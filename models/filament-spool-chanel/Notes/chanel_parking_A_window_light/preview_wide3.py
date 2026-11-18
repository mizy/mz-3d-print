import cadquery as cq,numpy as np,matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from pathlib import Path
D=Path(__file__).parent;font_manager.fontManager.addfont('/System/Library/Fonts/STHeiti Light.ttc');plt.rcParams['font.family']=font_manager.FontProperties(fname='/System/Library/Fonts/STHeiti Light.ttc').get_name();fig=plt.figure(figsize=(13,7),facecolor='white')
for i,part in enumerate(['wide','narrow']):
 body=cq.importers.importBrep(str(D/'long_wide_v3'/(part+'.brep'))).val();v,f=body.tessellate(.025,.12);v=np.array([[p.x,p.y,p.z] for p in v]);tri=v[np.array(f)];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12);light=np.array([-.3,-.4,1.]);light/=np.linalg.norm(light);color=np.array([.76,.57,.34])*(.45+.55*np.abs(n@light))[:,None];ax=fig.add_subplot(1,2,i+1,projection='3d');ax.add_collection3d(Poly3DCollection(tri,facecolors=color,edgecolors='none'));ax.set(xlim=(-101,101),ylim=(-101,101),zlim=(0,45));ax.set_box_aspect([202,202,70]);ax.view_init(38,-65);ax.set_title('宽半 · 外筒四个长窗' if i==0 else '窄半 · 外筒四窗',fontsize=18);ax.set_axis_off()
fig.suptitle('A 停线槽 + 香奈儿版：外筒中段减重候选',fontsize=20);fig.text(.5,.09,'内导管、卡口、止挡、四桥、定位键和盘面保持；只削外筒四桥之间的中段。',ha='center',fontsize=13);fig.text(.5,.04,'开窗减少线卷纸芯支承，可能夹入松散线材；旧仿真不能证明本版安全，尚未实物试配/承载。',ha='center',fontsize=12,color='#944a32');fig.subplots_adjust(bottom=.16,top=.84,wspace=.01);fig.savefig(D/'windows_wide3_preview.png',dpi=160)
