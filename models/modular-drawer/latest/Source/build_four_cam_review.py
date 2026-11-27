import sys,json,hashlib,math
from pathlib import Path
from report_geometry import inspect,meshes,views,to_view,mouth_circles
root=Path(sys.argv[1]);step=root/'STEP'; qa=root/'QA'
pref={
 'assembly':('00_Four_Cam_Closed_Assembly','单格 · 闭合总成',19),
 'side':('01_Universal_Side_Panel','01 通用侧板',1),'front':('02_Front_Beam','02 前梁',1),
 'rear':('03_Rear_Board_Four_Cam','03 后板 · 四颗偏心轮',1),
 'rod':('04_Rear_Upper_Straight_Rod','04 后上直拉杆',1),'cam':('05_Rear_Upper_Cam_11p2mm','05 后上偏心轮 · 11.2 mm',1),
 'coupon':('06_Rear_Upper_Cam_Fit_Coupon','06 后上锁位 · 四件小样',4),
 'paddle':('08_Drawer_Stop_Paddle','08 限位拨片（左右镜像）',1),
 'lowercam':('09_Lower_Cam_11p2mm','09 下偏心轮 · 11.2 mm（镜像配向）',1),
 'lowerrod':('10_Lower_Straight_Rod','10 下直拉杆（镜像配向）',1),
 'drawer':('27_Cinnamoroll_Corner_Relief_Drawer','27 大耳狗低侧拉篮 · 后角避让',1),
 'two_bay':('00_Two_Bay_Horizontal_Frame_Check','两格 · 共用中侧板骨架',35),
 'expansion':('07_Right_Bay_Frame_Expansion_17_Parts','右格 · 补打 17 件',17)
}
memo={'side':'原侧板保持，不改承托滑轨、接层尺寸或固定槽。右侧用同一通用板。','front':'两端偏心轮从抽屉侧安装，不改变原梁。','rear':'外背 Y245 平齐；上轮从背面装，下轮从内侧装。下口仍为原版。','rod':'两端分别卡入侧板槽及偏心轮。后上使用与下方同规格的直拉杆。','cam':'Ø8.2 × 11.2 mm，背面一字槽；左右按配向装入。','paddle':'本轮无变化，保留原装配与操作方式。','lowercam':'前梁左右各一，后板下方左右各一。','lowerrod':'前梁和后板下方沿用已确认尺寸。','drawer':'两处后上角向内收，底板、滑轨边、前口和整体外廓均保留。'}
spec={
 'side':[('side','前下拉杆接口','下直拉杆，前梁锁座配对。',(22.35,13,5)),('side','后下拉杆接口','下直拉杆，后板下锁座配对。',(22.35,237,5)),('side','后上拉杆接口','沿用侧板槽；装后上直拉杆。',(22.19,234.24,92)),('side','抽屉承托唇','与对侧托轨分担抽屉载荷，印件装配时应同时齐平。',(25.3,118,9.8)),('side','限位拨片轴位','与原限位拨片配用。',(23,125,96.5)),('side_top','前叠层接口','凸榫 Y33–45，叠层配对底槽。',(20.3,39,102.7)),('side_top','后叠层接口','凸榫 Y205–217，叠层配对底槽。',(20.3,211,102.7))],
 'front':[('rear_end','左下轮座','抽屉侧插入轮，原直拉杆从端部进入。',(37.2,21,5)),('rear_end','右下轮座','同规格，镜像配向。',(158.1,21,5))],
 'rear':[('rear_end','后上锁①','背面孔 Ø8.56 mm；座深 11.65 mm，轮 Ø8.20 × 11.20 mm，端面退入 0.25 mm。',(37.2,245,92)),('rear_end','后上锁②','同轴径同深度、镜像配向。',(158.1,245,92)),('front','后下锁③','由抽屉侧装轮，保持原设计。',(37.2,229,5)),('front','后下锁④','由抽屉侧装轮，保持原设计。',(158.1,229,5)),('side','向内加厚位置','局部最厚 12.65 mm，原直壁 6.20 mm；抽屉侧让位。',(37.2,232.35,92))],
 'rod':[('side','固定端','先装偏心轮，再由侧板原槽推入拉杆。',(22.35,238.45,92))],
 'cam':[('rear_end','一字操作槽','后上轮的装入口与操作孔是同一个孔。',(37.2,244.75,92))],
 'paddle':[],
 'lowercam':[],
 'lowerrod':[],
 'drawer':[('top','左后角避让','后上角最多向内让位 6.45 mm。',(19.2,223.55,86)),('top','右后角避让','与左后角对称，底部和中间深度不改。',(124.9,223.55,86))]
}
parts={};panels=[];trays=[];files={}
def nam(n):return step/(n+'.step')
for k,(n,title,ct) in pref.items():
 f=nam(n);q,a=inspect(f,{},'assembly' if ct>1 else k);assert a['nSolids']==ct
 part=parts[k]=dict(a,title=title,**meshes(q,a['bounds'],.18))
 files[n]=a['sha256']
 if ct>1:
  if k!='assembly':trays.append(dict(id=k,title=title,mesh=k))
  continue
 axes=['side','side_top','rear_end'] if k=='side' else ['front','top','side']
 if k in ('rear','front','cam'):axes+=['rear_end']
 vv=views(q,axes,include_tangent=k in ('rear','drawer'))
 anchors=[]
 for ax,name,txt,pt in spec[k]:
  v=next(t for t in vv if t['key']==ax); at=to_view(pt,v)
  assert all(-.001<=a<=z+.001 for a,z in zip(at,v['extent'])),(k,ax,name,at,v['extent'])
  anchors.append(dict(view=ax,name=name,text=txt,at=at,units='mm',placement='bottom' if '下' in name or '承托' in name else 'top'))
 if k=='rear':
  expected=[(37.2,245.,92.,4.28),(158.1,245.,92.,4.28)]
  assert mouth_circles(q,245.,4.28)==expected
  assert mouth_circles(q,229.,4.28)==[(37.2,229.,5.,4.28),(158.1,229.,5.,4.28)]
  # HLR may incorrectly classify one of two identical buried circular edges
  # as visible. Verify both pockets are blind from their opposite faces and
  # render the exact analytic circles in a common visibility class.
  lower=mouth_circles(q,229.,4.28)
  import FreeCAD as A
  V=A.Vector
  for x,y,z,r in expected:
   assert q.isInside(V(x,232.85,z),.0001,True)
  for x,y,z,r in lower:
   assert q.isInside(V(x,244.05,z),.0001,True)
  for key,vis,hid in [('rear_end',expected,lower),('front',lower,expected)]:
   ax=next(v for v in vv if v['key']==key)
   def proj(g):return [[*to_view(t[:3],ax),t[3]] for t in g]
   visible=proj(vis); hidden=proj(hid); known=[*visible,*hidden]
   def matching(a,b,r):return any(max(abs(a-x),abs(b-y),abs(r-rad))<.025 for x,y,rad in known)
   for i,layer in enumerate(ax['layers']):
    ax['layers'][i]=[poly for poly in layer if not (len(poly)>1 and any(all(abs(math.hypot(a-x,b-y)-rad)<.023 for a,b in poly) for x,y,rad in known))]
   ax['visible_full_circles']=[abc for abc in ax['visible_full_circles'] if not matching(*abc)]+visible
   ax['hidden_full_circles']=hidden
 if k=='front':
  assert mouth_circles(q,21.,4.28)==[(37.2,21.,5.,4.28),(158.1,21.,5.,4.28)]
 panels.append(dict(id=k,title=title,mesh=k,views=vv,anchor=anchors,extent=a['extent'],memo=memo[k]))
exp=json.loads((qa/'expansion-fit.json').read_text())
assert all(files[n]==h for n,h in exp['hashes'].items())
f=root/'Print'/'Right_Bay_Frame_P1S_PETG_UNSLICED.3mf';exp['print_3mf']=dict(path='Print/'+f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest())
meta=dict(build_notes=['后板上 2 下 2，共四颗 11.2 mm 偏心轮；前梁两颗原下轮不变。','抽屉原底板、托轨和前口不变；两个后上角最多让位 6.45 mm。','双 T 与薄轮对照留在 History，不属于本版。CAD 配合不是实物承载；未切片。'])
data=dict(parts=parts,panels=panels,trays=trays,meta=meta,fit=json.loads((qa/'four-cam-fit.json').read_text()),expansion=exp)
src=Path(__file__).parent
html=(src/'four-cam-template.html').read_text().replace('<!-- DATA_SLOT -->',json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')).replace('<!-- MZ_VIEWER_SLOT -->',(src/'mz-viewer.runtime.js').read_text().replace('后板背插键 · 关合总成','四偏心轮 · 关合总成'))
(root/'index.html').write_text(html)
print('Re-read',len(parts),'files, checked',sum(len(p['views']) for p in panels),'actual orthographic views with matched BRep bounds, exact cam mouths and rear centers')
