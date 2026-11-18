import cadquery as cq,numpy as np,matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from pathlib import Path
D=Path(__file__).parent;F=Path('/Users/miaozhuang/Projects/mz-3d-print/models/filament-spool-chanel/Models/ChanelLight/CHANEL_PARKING_A_WINDOW_LIGHT_TRIAL.step');sh=cq.importers.importStep(str(F)).val();sol=sorted(sh.Solids(),key=lambda s:s.BoundingBox().center.x);data=[]
for s in sol:
 s=s.translate((-s.BoundingBox().center.x,-s.BoundingBox().center.y,-s.BoundingBox().zmin));v,f=s.tessellate(.07,.2);data.append((np.array([[p.x,p.y,p.z] for p in v]),np.array(f)))
font_manager.fontManager.addfont('/System/Library/Fonts/STHeiti Light.ttc');plt.rcParams['font.family']=font_manager.FontProperties(fname='/System/Library/Fonts/STHeiti Light.ttc').get_name();fig=plt.figure(figsize=(15,6.6),facecolor='white')
for i,(h,a,title) in enumerate([(72,51,'① 同轴插入姿态\nH=72 mm，θ=51°'),(66.4,8,'② 落座后进入保留区\nH=66.4 mm，θ=8°'),(66.4,0,'③ 名义止退位置\nθ=0°仍有刚性交叠')]):
 ax=fig.add_subplot(1,3,i+1,projection='3d')
 for j,(v0,f) in enumerate(data):
  v=v0.copy()
  if j:
   v[:,1:]*=-1;theta=np.radians(a);rot=np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]]);v[:,:2]=v[:,:2]@rot.T;v[:,2]+=h
  tri=v[f];tri=tri[tri.mean(axis=1)[:,1]>=0] # remove front half for inspection, not a manufactured cut
  n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12);L=np.array([-.4,-.5,1]);L=L/np.linalg.norm(L);base=np.array([.75,.54,.28] if not j else [.25,.52,.73]);color=base*(.5+.5*np.abs(n@L))[:,None];ax.add_collection3d(Poly3DCollection(tri,facecolors=color,edgecolors='none'))
 ax.plot([0,0],[0,0],[-5,85],color='#555555',linestyle='--',lw=.8);ax.set(xlim=(-101,101),ylim=(-2,101),zlim=(-3,83));ax.set_box_aspect([202,103,86]);ax.view_init(18,-90);ax.set_axis_off();ax.set_title(title,fontsize=15,pad=10)
fig.suptitle('最新开窗版 · 实际 STEP 数字装配剖视',fontsize=21,y=.97);fig.text(.5,.09,'为观察内部，图中仅显示后半；不是修改模型。金色宽片、蓝色窄片。纸芯未虚构：缺少真实尺寸。',ha='center',fontsize=12);fig.text(.5,.035,'仅检查离散刚体姿态；固定轴向止退路径有交叠，弹性越障与实际锁紧能力尚未验证。',ha='center',fontsize=12,color='#944a32');fig.subplots_adjust(top=.78,bottom=.17,wspace=.05);fig.savefig(D/'assembly_cutaway.png',dpi=160)
