import cadquery as cq,numpy as np,matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from pathlib import Path
D=Path(__file__).parent;font_manager.fontManager.addfont('/System/Library/Fonts/STHeiti Light.ttc');plt.rcParams['font.family']=font_manager.FontProperties(fname='/System/Library/Fonts/STHeiti Light.ttc').get_name()
s=cq.importers.importBrep(str(D/'output/wide.brep')).val();fig=plt.figure(figsize=(12,6),facecolor='white')
for i in range(2):
 body=s if i==0 else s.intersect(cq.Workplane('XY').box(18,25,5,centered=False).translate((83,8,-.1)).val())
 v,f=body.tessellate(.015,.1);v=np.array([[p.x,p.y,p.z] for p in v]);tri=v[np.array(f)];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n=n/np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12);light=np.array([-.3,-.4,1.]);light/=np.linalg.norm(light);sh=.45+.55*np.abs(n@light);color=np.array([.76,.57,.34])*sh[:,None];ax=fig.add_subplot(1,2,i+1,projection='3d');ax.add_collection3d(Poly3DCollection(tri,facecolors=color,edgecolors='none'))
 if i==0:ax.set(xlim=(-101,101),ylim=(-101,101),zlim=(0,45));ax.set_box_aspect([202,202,45]);ax.view_init(65,-65);ax.set_title('原生 CAD 候选 · 宽半')
 else:ax.set(xlim=(83,101),ylim=(8,33),zlim=(0,5));ax.set_box_aspect([18,25,5]);ax.view_init(65,-50);ax.set_title('A 停线槽局部 · 原孔连浅槽')
 ax.set_axis_off()
fig.suptitle('完整官方中心保留；扩大筋间镂空，旧主筋材料不减',fontsize=16)
fig.text(.5,.04,'槽用于停放线尾，运行 AMS 前释放。低矮无外凸不等于无挂丝或夹持可靠；需打印小样试夹。',ha='center',fontsize=12,color='#944a32');fig.subplots_adjust(bottom=.14,top=.85);fig.savefig(D/'parking_A_preview.png',dpi=170)
