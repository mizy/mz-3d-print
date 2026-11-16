import cadquery as cq,json
from pathlib import Path
R=Path(__file__).parent; out={}
for typ,body,top,logo in [('lv','blue_body_with_inverted_T_clip','ivory_top_layers','ivory_glue_logo'),('chanel','cream_body_inverted_clip','black_top_layers','black_glue_CC')]:
 p=R/typ/'parts';s=[cq.importers.importStep(str(p/(x+'.step'))).val() for x in [body,top,logo]]
 out[typ]={'body_top_overlap_volume_mm3':s[0].intersect(s[1]).Volume(),'body_logo_overlap_volume_mm3':s[0].intersect(s[2]).Volume(),'valid_solids':[x.isValid() for x in s]}
 print(typ,out[typ],flush=True)
(R/'interface_validation.json').write_text(json.dumps(out,indent=2))
