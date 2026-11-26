import sys,json,hashlib
from pathlib import Path
from report_geometry import inspect,meshes,views,to_view
step,out,qa=map(Path,sys.argv[1:4]);fit=json.loads(qa.read_text())
files={'assembly':('00_Rear_Key_Closed_Review','后板背插键关合总成'),
 'side':('01_Universal_Side_Panel','原侧板（不改）'),'front':('02_Front_Beam','原前梁（不改）'),
 'rear':('03_Rear_Board_Slide_Key_Review','新后板 · 上口插槽'),
 'key':('04_Rear_Slide_Key','背插双 T 键 × 2'),'blade':('05_Rear_Key_Stop_Blade','止退片 × 2'),'coupon':('06_Rear_Stop_Corner_Fit_Coupon','一角试配小样 · 4 件'),
 'drawer':('27_Cinnamoroll_Honeycomb_Low_Sides','原大耳狗低侧拉篮（不改）')}
ann={
 'side':[('side','复用原上 T 槽','侧板丝毫不改，只把原槽最后 5.88 mm 作为上接头使用。',(13,236.4,92)),('side','后下偏心轮拉杆接口','保留机械紧固。',(13,232,5)),('side','前下偏心轮拉杆接口','前梁和锁件全部沿用。',(13,8,5))],
 'front':[('top','沿用原前梁和两端锁座','本轮不改前梁。',(8.25,8,5))],
 'rear':[('front','左上背插键接收槽','接入原侧板同一个 T 槽，最后从后侧插入。',(1.55,13,92)),('front','右上同款','只换此处两枚上方偏心轮，不改下方机构。',(143.15,13,92)),('front','后下轮座','保留原偏心锁。',(11.9,0,5))],
 'key':[('side','背面取出凹口','从后方挑出插键，孔不高于背面。',(3,5.88,2.45))],
 'blade':[('top','顶面起片槽','从顶部挑起止退片再拆滑键。',(.92,.57,7.35))],
 'drawer':[('front','原前板和凸刻保持','抽屉不用重新开槽，保留低侧与实心底板。',(72.05,-1.18,46))]}
memo={'side':'旧件的后上槽沿用，不切原件。','front':'旧前梁与偏心锁完全保留。','rear':'内侧旧矩形台阶削平至 Y238.80；只保留双 T 的槽口和止退片的装配口。','key':'左右同一款，四个平面导入倒角；背面取键口和止退片凹口保留。','blade':'矩形销身平直，顶面仅保留用于取出的浅槽；落入后挡住插键后退。','drawer':'两侧 78 mm，前后 86 mm，底板 2.8 mm。'}
parts={};panels=[];extra=[]
for k,(stem,title) in files.items():
 f=step/(stem+'.step')
 q,a=inspect(f,{},'assembly' if k=='coupon' else k)
 if stem in fit['files']:assert a['sha256']==fit['files'][stem]
 parts[k]=dict(a,title=title,**meshes(q,a['bounds'],.24))
 if k=='assembly':
  assert len(q.Solids)==19
  continue
 if k=='coupon':
  assert len(q.Solids)==4;extra.append(dict(id=k,title=title,mesh=k));continue
 axes=['side','side_top','rear_end'] if k=='side' else ['front','top','side']
 vv=views(q,axes,include_tangent=k=='drawer')
 anchors=[]
 for axis,name,txt,pt in ann[k]:
  v=next(x for x in vv if x['key']==axis);u=to_view(pt,v)
  assert all(0<=x<=s for x,s in zip(u,v['extent'])),(k,axis,u,v['extent'])
  anchors.append(dict(view=axis,name=name,text=txt,at=u,units='mm'))
 panels.append(dict(id=k,title=title,mesh=k,views=vv,anchor=anchors,extent=a['extent'],memo=memo[k]))
expand=None
exp_path=qa.parent/'expansion-fit.json'
if exp_path.is_file():
 expand=json.loads(exp_path.read_text())
 plate=step.parent/'Print'/'Right_Bay_Frame_P1S_PETG_UNSLICED.3mf'
 if plate.is_file():
  expand['print_3mf']={'path':'Print/'+plate.name,'sha256':hashlib.sha256(plate.read_bytes()).hexdigest()}
 for k,stem,title,n in [
   ('two_bay','00_Two_Bay_Horizontal_Frame_Check','左右两格 · 骨架总装',35),
   ('expansion','07_Right_Bay_Frame_Expansion_17_Parts','新增右格 · 17 件，不含拉篮',17)]:
  f=step/(stem+'.step'); x,ma=inspect(f,{},'assembly')
  assert ma['sha256']==expand['hashes'][stem] and ma['nSolids']==n
  parts[k]=dict(ma,title=title,**meshes(x,ma['bounds'],.24))
  extra.append(dict(id=k,title=title,mesh=k))
meta=dict(build_notes=['只替换上口：新后板及两枚同款滑键、两枚同款止退片。前梁、侧板和拉篮没有尺寸变化。','整屉可完全闭合；零名义间隙、止退片挡肩和开闭行程为 CAD 检查，不是承重或打印验证。'])
data=dict(parts=parts,panels=panels,trays=extra,meta=meta,fit=fit,expansion=expand)
safe=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
base=Path(__file__).parent
html=(base/'rear-key-template.html').read_text().replace('<!-- DATA_SLOT -->',safe).replace('<!-- MZ_VIEWER_SLOT -->',(base/'mz-viewer.runtime.js').read_text())
out.write_text(html);print('PASS page',len(panels),len(html),flush=True)
