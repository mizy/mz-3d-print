import cadquery as cq
from pathlib import Path
R=Path(__file__).parent
for name in ['blue_body_with_inverted_T_clip','whole_bowl_AMS']:
 s=cq.importers.importStep(str(R/'parts'/f'{name}.step')).val()
 cq.exporters.export(s,str(R/'parts'/f'{name}.stl'),tolerance=.02,angularTolerance=.08)
 print(name,flush=True)
