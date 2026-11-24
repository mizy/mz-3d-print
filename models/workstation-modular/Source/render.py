from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
root=Path(__file__).resolve().parents[1]
fig,ax=plt.subplots(figsize=(12,8),facecolor='#f3f4f6');ax.set_facecolor('#f3f4f6')
ax.add_patch(Rectangle((0,0),237.6,127.2,facecolor='#394b60'))
names=['SMALL PARTS','NOZZLE POCKETS','OPEN TRAY','PLIERS / SCRAPER','GLUE / BOTTLES','PRECISION TOOLS']
heights=[22,12,22,65,50,58];colors=['#f0b567','#d4c3ae','#bdcddd','#c1d6c3','#a8bbc9','#d5b8a0']
for k in range(6):
 x=2.8+(k%3)*78.4;y=2.8+(k//3)*62.4;c=colors[k]
 ax.add_patch(Rectangle((x,y),75.2,59.2,facecolor=c))
 if k!=1:
  div={0:1,3:1,5:3}.get(k,0);w=(75.2-6.4-div*3.2)/(div+1)
  for i in range(div+1):ax.add_patch(Rectangle((x+3.2+i*(w+3.2),y+3.2),w,52.8,facecolor='#f8fafc',edgecolor='#94a3b8',lw=.7))
 else:
  for j in range(3):
   for i in range(5):ax.add_patch(Circle((x+12+i*(75.2-24)/4,y+12+j*(59.2-24)/2),4.25,facecolor='#f8fafc',edgecolor='#94a3b8',lw=.7))
 ax.text(x+37.6,y+31,names[k],ha='center',va='center',fontsize=9,fontweight='bold',bbox=dict(boxstyle='round,pad=.3',fc=c,ec='none'))
 ax.text(x+37.6,y+21,'H '+str(heights[k])+' mm',ha='center',fontsize=9,bbox=dict(boxstyle='round,pad=.2',fc=c,ec='none'))
ax.annotate('',(0,-8),(237.6,-8),arrowprops={'arrowstyle':'<->','color':'#475569'});ax.text(118.8,-15,'237.6 mm',ha='center',color='#475569')
ax.annotate('',(-8,0),(-8,127.2),arrowprops={'arrowstyle':'<->','color':'#475569'});ax.text(-13,63.6,'127.2 mm',ha='center',rotation=90,color='#475569')
ax.set_xlim(-22,250);ax.set_ylim(-23,146);ax.set_aspect('equal');ax.axis('off')
fig.suptitle('MODULAR PRINT WORKSTATION',fontsize=23,color='#253344',y=.94)
fig.text(.5,.875,'TOP VIEW / 6 REMOVABLE MODULES / PARAMETRIC CAD DRAFT',ha='center',fontsize=11,color='#64748b')
fig.text(.1,.08,'Straight-sided locating tray: 0.4 mm clearance per side. No magnets or clips needed.',fontsize=11,color='#334155')
fig.text(.1,.04,'Tool dimensions and physical fit pending. No slicing performed. Not Gridfinity-compatible.',fontsize=10,color='#64748b')
fig.savefig(root/'preview.png',dpi=160,bbox_inches='tight')
