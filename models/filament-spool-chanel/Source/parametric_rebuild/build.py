"""Native analytic CAD reconstruction. Run using Python with cadquery and shapely.
All dimensions millimetres. Interface reconstruction is separate and must be validated.
Never substitutes the legacy mesh-derived originals.
"""
from pathlib import Path
import sys,math,json,time
import cadquery as cq
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parent))
from chanel_motif import double_c
PARAMS={'flange_radius':94.,'flange_inner_radius':43.7,'skin':.6,'rib_length':54.,'rib_width':4.,'rib_height_above_skin':2.6,'rib_center_radius':70.5,'rib_count':8,'motif_rings':[(53,16),(70,24),(87,32)],'rim_inner_radius':95.,'rim_outer_radius':100.,'core_lower_inner_radius':36.8,'core_add_outer_radius':39.7}
def build_flange():
 p=PARAMS
 plate=cq.Workplane('XY').circle(p['flange_radius']).circle(p['flange_inner_radius']).extrude(p['skin']).val()
 ribs=[]
 for i in range(p['rib_count']):
  ribs.append(cq.Workplane('XY').box(p['rib_length'],p['rib_width'],p['rib_height_above_skin'],centered=(True,True,False)).translate((p['rib_center_radius'],0,p['skin'])).val().rotate((0,0,0),(0,0,1),360*i/p['rib_count']))
 plate=plate.fuse(*ribs)
 motif=double_c().scale(1.1);cut=[]
 for rad,n in p['motif_rings']:
  for i in range(n):
   a=2*math.pi*(i+.5)/n
   cut.append((motif.scale(1/1.1) if rad==87 else motif).translate((rad*math.cos(a),rad*math.sin(a),0)))
 plate=plate.cut(*cut).clean()
 assert plate.isValid() and len(plate.Solids())==1
 return plate

def build_shoulder(part):
 top_z,r_top=(22.,33.35) if part=='wide' else (24.,29.75)
 z0=top_z-(39.9-r_top)
 return cq.Workplane('XZ').polyline([(39.9,z0),(r_top,top_z),(r_top-1.7,top_z),(r_top-1.7,top_z-3),(36.8,z0-1.3)]).close().revolve(360,(0,0),(0,1)).val()
if __name__=='__main__':
 t=time.time();s=build_flange();cq.exporters.export(s,str(R/'flange_native_rebuilt.step'))
 report={'part':'flange only, not finished spool','valid':s.isValid(),'solids':len(s.Solids()),'faces':len(s.Faces()),'volume_mm3':s.Volume(),'elapsed_seconds':time.time()-t}
 (R/'parameters.json').write_text(json.dumps(PARAMS,indent=2));(R/'flange_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
 for part in ['wide','narrow']:cq.exporters.export(build_shoulder(part),str(R/f'shoulder_native_{part}.step'))
