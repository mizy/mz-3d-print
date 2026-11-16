"""Re-tessellate CC and remove zero-area STL triangles without altering CAD."""
from pathlib import Path
import cadquery as cq
import trimesh
R=Path(__file__).parent
for name in ['black_glue_CC','black_glue_CC_print_flat']:
 p=R/'parts'/name
 s=cq.importers.importStep(str(p.with_suffix('.step'))).val()
 cq.exporters.export(s,str(p.with_suffix('.stl')),tolerance=.02,angularTolerance=.08)
 m=trimesh.load(str(p.with_suffix('.stl')))
 m.update_faces(m.nondegenerate_faces())
 m.remove_unreferenced_vertices()
 assert m.is_watertight and m.volume>0,name
 m.export(str(p.with_suffix('.stl')))
