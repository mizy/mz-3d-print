import cadquery as cq,numpy as np,matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from pathlib import Path
D=Path(__file__).parent;font_manager.fontManager.addfont('/System/Library/Fonts/STHeiti Light.ttc');plt.rcParams['font.family']=font_manager.FontProperties(fname='/System/Library/Fonts/STHeiti Light.ttc').get_name();fig=plt.figure(figsize=(13,6.8),facecolor='white');m=cq.Solid.makeCylinder(45,45)
for i,part in enumerate(['wide','narrow']):
 old=cq.importers.importBrep('/tmp/chanel_parking_100g/long_wide_v3/'+part+'.brep').val().intersect(m);new=cq.importers.importBrep(str(D/'prototype'/(part+'.brep'))).val().intersect(m);added=new.cut(old);ax=fig.add_subplot(1,2,i+1,projection='3d')
 for s,base in [(old,[.76,.57,.34]),(added,[.15,.53,.75])]:
  v,f=s.tessellate(.04,.15);v=np.array([[p.x,p.y,p.z] for p in v]);tri=v[np.array(f)];tri=tri[tri.mean(axis=1)[:,1]>=0];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12);L=np.array([-.3,-.5,1]);L=L/np.linalg.norm(L);col=np.array(base)*(.5+.5*np.abs(n@L))[:,None];ax.add_collection3d(Poly3DCollection(tri,facecolors=col,edgecolors='none'))
 ax.set(xlim=(-46,46),ylim=(-1,46),zlim=(0,43));ax.set_box_aspect([92,47,43]);ax.view_init(26,-90);ax.set_axis_off();ax.set_title(('宽半' if part=='wide' else '窄半')+' · 内导管连接窗顶',fontsize=18)
fig.suptitle('模型内薄斜膜 + 径向 50°斜顶（实际 CAD 半剖）',fontsize=20);fig.text(.5,.12,'蓝色为新增的一体模型材料，不是可拆支撑；竖向厚 1.1 mm，法向厚约 0.71 mm。',ha='center',fontsize=13);fig.text(.5,.07,'原完整内导管、卡口和纸芯外筒包络保留。图为中心局部剖示，原打印模型未切开。',ha='center',fontsize=12);fig.text(.5,.025,'该工艺复切未生成独立支撑；仍有少量桥接路径，实物打印与结构强度尚未验证。',ha='center',fontsize=12,color='#944a32');fig.subplots_adjust(bottom=.19,top=.83,wspace=.04);fig.savefig(D/'selfsupport_roof_preview.png',dpi=170)
