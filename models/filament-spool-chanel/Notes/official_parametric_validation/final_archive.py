from pathlib import Path
import json,shutil,hashlib,zipfile
P=Path('/Users/miaozhuang/Projects/mz-3d-print/models/filament-spool-chanel'); T=Path('/tmp/chanel_official_native');R=Path('/tmp/chanel_official_reproduce')
N=P/'Notes/official_parametric_validation';N.mkdir(parents=True,exist_ok=True)
L=P/'Notes/chanel_official_light_validation';L.mkdir(parents=True,exist_ok=True)
manifest={};repro={}
for stage,old,folder,name,note in [('baseline','build_output','OfficialBaseline','BAMBU_OFFICIAL_REFERENCE_NATIVE_BASELINE.step',N),('light','light_output','ChanelLight','BAMBU_OFFICIAL_DERIVED_LIGHT_CHANEL.step',L)]:
 a=json.loads((T/old/'validation.json').read_text());b=json.loads((R/stage/'validation.json').read_text());checks={}
 for k in ['wide','narrow']:
  av=a['parts'][k];bv=b['parts'][k];delta=abs(av['volume_mm3']-bv['volume_mm3']);assert delta<1e-5 and av['faces']==bv['faces'] and bv['valid'] and bv['solids']==1
  checks[k]={'volume_delta_mm3':delta,'faces':bv['faces'],'valid':bv['valid']}
 assert b['step']['valid'] and b['step']['solids']==2
 repro[stage]=checks; dest=P/'Models'/folder/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/stage/name,dest)
 manifest[str(dest.relative_to(P))]={'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
 shutil.copy2(R/stage/'validation.json',note/'source_regenerated_validation.json')
 for f in ['slice_reports.json','mesh_reports.json']:shutil.copy2(T/f'slice_{stage}'/f,note/f)
for f in ['flange_section_validation.json','key_validation.json','narrow_full_sections.json','wide_nominal_full_sections.json','assembly_path.json','assembly_poses.json','assembly_scan.json','parameters_variant_full.json','hub_parameter_native_tests.json','narrow_lock_validation.json','wide_marker_validation.json','check_light_preserved.py','pack_and_slice.py']:
 if (T/f).exists():shutil.copy2(T/f,N/f)
for f in ['light_preserved_regions.json','light_parameters_variant.json']:shutil.copy2(T/f,L/f)
for dirname,dest in [('variant_full',N),('light_variant',L)]:
 for f in ['validation.json','mesh_validation.json']:shutil.copy2(T/dirname/f,dest/('parameter_variant_'+f))
(N/'source_reproduction.json').write_text(json.dumps(repro,indent=2))
(P/'Design').mkdir(exist_ok=True);shutil.copy2(T/'official_and_light_preview.png',P/'Design/official_and_light_preview.png')
Z=P/'Source/BAMBU_official_and_CHANEL_parametric_sources.zip'
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED) as z:
 for dirname in ['official_baseline','chanel_official_light']:
  for f in sorted((P/'Source'/dirname).rglob('*')):
   if f.is_file() and '__pycache__' not in f.parts:z.write(f,f.relative_to(P/'Source'))
manifest[str(Z.relative_to(P))]={'bytes':Z.stat().st_size,'sha256':hashlib.sha256(Z.read_bytes()).hexdigest()}
(N/'DELIVERY_MANIFEST.json').write_text(json.dumps(manifest,indent=2))
report='''# 官方参数化基准与轻量双 C 派生：完成记录

两版本分别保留，各 STEP 包含可独立选择的宽、窄两实体。来源为官方 Wiki STL 附件的原生 CAD 逆向重建，不是厂商原生 CAD、标注公差图或三角面封装 STEP。STEP 不含参数特征树；可编辑 JSON、Python 和少量弧线/平面草图数据在 Source 两个独立目录中。

## 验证结果
- 从最终保存的两套源码独立运行再生；回读均 2 个有效实体，逐件面数与体积和审查版一致（报告 source_reproduction.json）。
- 基准 Ø200，宽高40.7 / 窄高34.1 mm，每半4个 Ø3.5 线孔；恢复完整内导管、四桥、外口 Ø55 及倒角、锁口、定位键与标记。
- 基准对官方网格全件离散截面：宽36层最大约0.028921 mm，窄22层最大0.011490 mm。不是全表面误差上界；浅标记采用少量原生曲面近似。
- 两版本最终 STEP 直接三角化：均0开放边、0非流形；双件分别 CLI 切片成功，无返回的 warning_message。源模型没有网格补洞。R31.4近重合拟合圆造成的旧薄片面已在原生草图修正。
- 实际变参验证：基准外径/线孔位置及孔径/轴孔/桥宽/宽筒孔组合、轻量logo缩放/盘皮/筋宽组合，均2有效实体且网格闭合。仅这些组合通过，不代表任意参数范围；全局筒缩放目前明确拒绝，防止假联动。
- 派生版完整中心、滚动外缘和4孔局部与基准布尔差为0，12个保护区检查通过。
- 同一 PETG+、0.4喷嘴、0.2层、2墙、顶3层0.6、底3层、5%填充及原自动支撑配置：基准总耗材168.122345 g；轻量总耗材119.632122 g。包含切片器计入的支撑等路径，不是称重，也不承诺全部机器启动耗材。旧105g重量不能套用于恢复官方结构后的方案。

## 装配和打印限制
- 正确对轴翻转后，H=66.4 mm，51°插入并旋到8°的离散路径采样无刚性交叠；8°是保留区而非最终止退扣验证。
- 接近最终止退位置存在刚性交叠：3°约4.205 mm³，0°约0.369 mm³。官方原 STL 独立积分也有约4.197/0.364 mm³，不能归因于重建独有，也不能因此推断弹性越障安全。
- 尚未实物试配、承载测试、可靠性认证或有限元强度分析。0.4 mm盘皮在0.2层高下仅2层，必须先试打/试配，再验证装满料盘受力。
- 官方页面提示打印料盘仅作临时/应急用途，不应使用它烘干耗材。
- 可下载的 spacing shim 尚未参数化或验证，未宣称包含；附件数量与安装要求未确证。
- 未操作用户当前 Studio，未发送打印。干燥盒保持独立。

## 旧方案
Models/CHANEL_105g_KEEP_CORE.step 及旧修复网格仍作为历史原件留存，但中心导向结构错误，不再是当前入口，不建议打印。此次不覆盖或删除旧文件。
'''
(N/'README.md').write_text(report);(L/'README.md').write_text(report)
(P/'README.md').write_text(report+'\n## 当前文件\n'+''.join('- '+k+'\n' for k in manifest)+'\n源码：Source/official_baseline 和 Source/chanel_official_light；各目录 README 给出已实际执行的再生命令。\n')
meta=json.loads((P/'MODEL.json').read_text());meta.update(title='官方参数化料盘基准 + 轻量双 C',summary='完整官方筒结构、Ø200盘与每半4孔；原生参数化源可再生。轻量版同配置切片约119.63g；未实物配合或强度认证。',cover='Design/official_and_light_preview.png',downloads=list(manifest),downloadGroups=[{'prefix':'Models/OfficialBaseline/','label':'官方附件逆向基准','note':'单 STEP 双实体，原生参数化源码配套。'},{'prefix':'Models/ChanelLight/','label':'轻量双 C 派生','note':'恢复官方中心结构，约119.63g切片总耗材，不是旧105g。'},{'prefix':'Source/','label':'参数化源码','note':'独立再生验证通过，STEP 本身不含特征树。'}]);(P/'MODEL.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
print(json.dumps(manifest,indent=2));print('SOURCE REPRODUCTION',repro)
