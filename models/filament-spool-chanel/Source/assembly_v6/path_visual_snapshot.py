import json,numpy as np,matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from pathlib import Path
font_manager.fontManager.addfont('/System/Library/Fonts/STHeiti Light.ttc');plt.rcParams['font.family']=font_manager.FontProperties(fname='/System/Library/Fonts/STHeiti Light.ttc').get_name()
D=Path('/tmp/chanel_assembly_v6');P=Path('/Users/miaozhuang/Projects/mz-3d-print/models/filament-spool-chanel/Design/assembly_v6');P.mkdir(exist_ok=True)
d=json.load(open(D/'radial_scan.json'));H=d['H_stop'];fig,(a,b)=plt.subplots(1,2,figsize=(13,7),gridspec_kw={'width_ratios':[1.4,1]},facecolor='#f4f7fb');fig.suptitle('V6 数字装配｜路径与检查结果',fontsize=22,fontweight='bold',x=.06,ha='left')
for r in d['results']:
 q=[x for x in r['scan'] if x['theta_deg']<=65];a.scatter([x['theta_deg'] for x in q],[r['H']]*len(q),c=['#1b9e77' if x['min_radial_clearance_mm']>=0 else '#e3b0ac' for x in q],s=17,marker='s')
a.plot([51,51,10],[71.4,H,H],color='#2155b6',lw=2.8,zorder=4);a.annotate('',(51,H+.8),(51,H+3.2),arrowprops={'arrowstyle':'->','color':'#2155b6','lw':2.8});a.annotate('',(12,H),(43,H),arrowprops={'arrowstyle':'->','color':'#2155b6','lw':2.8});a.scatter([10],[H],s=100,c='#2155b6',zorder=5);a.text(8,H+.35,'10° 保留区',fontsize=12,color='#2155b6');a.set_xlim(0,65);a.set_ylim(H-.3,71.6);a.set_xlabel('窄片旋转角 θ（度）',fontsize=12);a.set_ylabel('两片基面距离 H（mm）',fontsize=12);a.set_title('离散姿态径向筛查（不是连续扫掠体证明）',loc='left',fontsize=12);a.grid(alpha=.18);a.text(2,71.15,'绿：采样包络非负\n粉：采样包络发生重叠',fontsize=11,va='top',bbox={'facecolor':'white','edgecolor':'none','alpha':.9})
b.axis('off');b.text(0,.96,'正确朝向与路线',fontsize=17,fontweight='bold',va='top');b.text(0,.85,'窄片翻转 180°，对齐两片筒轴\n51° 对准入口，沿轴向插入\n落座：H = 66.430114 mm\n再向减角方向旋至 10°',fontsize=14,linespacing=1.8,va='top');b.text(0,.51,'已核实',fontsize=17,fontweight='bold',va='top');b.text(0,.42,'• 组装 STEP 回读：2 个有效实体\n• 入口 / 落座：完整模型交叠体积为 0\n• 保持 10° 外拔 0.1 mm：发生干涉\n• 路径采样：185 个姿态\n• 最低采样径向余量：约 0.130 mm',fontsize=12.5,linespacing=1.8,va='top');fig.text(.06,.055,'10° 位于轴向保留区，不是精确硬止挡或弹性卡嗒认证。采样径向余量不是三维全局最短间隙。\n这是数字装配候选；仍需打印试配，原 v6 配合尺寸改变的限制继续适用。',fontsize=12,color='#475569');fig.subplots_adjust(top=.86,bottom=.2,left=.08,right=.97,wspace=.25)
out=P/'CHANEL_v6_assembly_path_checks.png';fig.savefig(out,dpi=160);print(out)
