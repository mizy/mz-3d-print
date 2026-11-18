from pathlib import Path
import json,zipfile,hashlib,shutil
D=Path('/tmp/chanel_100g');out={'slicer':'BambuStudio 02.09.01.70','material':'Current Jucoole PETG+; density1.27 g/cm3','source_geometry':'v5 native defaults and weight_trials_v5 independent candidates; not v6','constant_settings':{'nozzle_diameter':.4,'outer_wall_line_width':.42,'inner_wall_line_width':.45,'layer_height':.2,'wall_loops':2,'bottom_shell_layers':3,'bottom_shell_thickness':0,'ensure_vertical_shell_thickness':'enabled','wall_generator':'classic','top_surface_line_width':.42,'internal_solid_infill_line_width':.42,'sparse_infill_line_width':.45,'initial_layer_line_width':.5,'support_line_width':.42,'enable_support':True,'support_type':'tree(auto)','brim_type':'auto_brim','brim_width':5,'detect_thin_wall':False,'minimum_sparse_infill_area':15},'presets':{'baseline':{'top_shell_layers':5,'top_shell_thickness':1,'sparse_infill_density':'10%'},'low':{'top_shell_layers':3,'top_shell_thickness':.6,'sparse_infill_density':'5%'}},'results':{}}
for geom in ['default_retess','R38_5','R38_5_skin04','original_lower_skin04']:
 out['results'][geom]={}
 for preset in ['baseline','low']:
  row={}
  for part in ['wide','narrow']:
   if geom=='default_retess':dd=D/({'wide':'wide_retess','narrow':'narrow_baseline'}[part] if preset=='baseline' else {'wide':'wide_retess_low','narrow':'narrow_top3_sparse5'}[part])
   else:dd=D/(geom+'_'+part+'_'+preset)
   j=json.load(open(dd/'result.json'));g=dd/'plate_1.gcode';z=zipfile.ZipFile(dd/('sliced.3mf'));c=json.loads(z.read('Metadata/project_settings.config'))
   row[part]={'grams_total':j['sliced_plates'][0]['filaments'][0]['total_used_g'],'return_code':j['return_code'],'gcode_sha256':hashlib.sha256(g.read_bytes()).hexdigest(),'bbox':j['sliced_plates'][0]['objects'][0]['bbox'],'observed_settings':{k:c[k] for k in ['top_shell_layers','top_shell_thickness','bottom_shell_layers','sparse_infill_density','wall_loops','ensure_vertical_shell_thickness']}}
  row['combined_grams']=sum(row[p]['grams_total'] for p in ['wide','narrow']);out['results'][geom][preset]=row
out['user_mesh_reference']={'wide_original_grams':61.83735656738281,'wide_independent_retess_grams':62.24199295043945,'difference_grams':.4046363830566406,'note':'Actual Bambu imported mesh differs from CadQuery tessellation; use same retessellation baseline for geometry comparisons, not claim all deltas are geometry-only against screenshot.'}
out['candidate_dimensions']={'R38_5':{'hub_lower_inner_radius':38.5,'lower_wall_wide':2.35,'lower_wall_narrow':2.15,'skin':.6},'R38_5_skin04':{'hub_lower_inner_radius':38.5,'lower_wall_wide':2.35,'lower_wall_narrow':2.15,'skin':.4,'rib_height_above_skin':2.8,'rib_total_height':3.2,'foot_min_height':1.4}}
out['candidate_dimensions']['original_lower_skin04']={'hub_lower_inner_radius':36.8,'lower_wall_wide':4.05,'lower_wall_narrow':3.85,'skin':.4,'rib_height_above_skin':2.8,'rib_total_height':3.2,'foot_min_height':1.4}
out['limitations']=['Estimates from two separately sliced halves, not weighed prints.','No strength/load/physical-fit validation.','0.4mm flange skin is only two nominal0.2mm layers and is more vulnerable to tearing/warping/lateral bending.','5% infill and3top layers are low-material test settings, not a proven load-safe preset.','Thinner lower hub can replace sparse infill with dense gap-fill; lower BRep volume is not a guarantee of lower sliced mass.','Original default model/UI settings unchanged; temporary3MF files are test containers, not user deliverables.']
(D/'final_weight_comparison.json').write_text(json.dumps(out,indent=2))
print({g:{p:row['combined_grams'] for p,row in rr.items()} for g,rr in out['results'].items()})
