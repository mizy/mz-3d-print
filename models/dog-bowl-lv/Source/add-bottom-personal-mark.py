"""Add user's original sprout/cube mark and name to underside; preserve 4 solids."""
import cadquery as cq, re,json,xml.etree.ElementTree as ET,hashlib
from pathlib import Path
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--input',type=Path,required=True,help='Unmarked STEP from Git e020f32')
parser.add_argument('--output-dir',type=Path,required=True)
args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[3]
SRC=args.input
SVG=ROOT/'models/mark-miaozhuang-three-variants/miaozhuang-logo.svg'
OUT=args.output_dir; OUT.mkdir(parents=True,exist_ok=True); DEPTH=.4; WIDTH=24
parts=cq.importers.importStep(str(SRC)).val().Solids(); assert len(parts)==4
base=parts[0]; assert abs(base.BoundingBox().zmax-2)<1e-6
# Original polygon vector, exactly preserving every vertex and interior leaf opening.
scale=WIDTH/(410-27)
cutters=[]
for el in ET.parse(SVG).getroot():
 if not el.tag.endswith('path'):continue
 wires=[]
 for sub in re.findall(r'M\s*([^Z]+)Z',el.attrib['d']):
  nums=[float(n) for n in re.findall(r'-?\d+(?:\.\d+)?',sub)]
  # Original SVG y down becomes model y up when seen from the underside.
  pts=[cq.Vector((nums[i]-218.5)*scale,(nums[i+1]-285)*scale-7,-.01) for i in range(0,len(nums),2)]
  wires.append(cq.Wire.makePolygon(pts,close=True))
 face=cq.Face.makeFromWires(wires[0],wires[1:]); assert face.isValid()
 cutters.append(cq.Solid.extrudeLinear(wires[0],wires[1:],cq.Vector(0,0,DEPTH+.01)))
# Chinese name from the source asset's title/README; viewed readable from below.
name=cq.Workplane('XY').text('苗壮',9,DEPTH+.01,fontPath='/System/Library/Fonts/STHeiti Medium.ttc',combine=False).val()
b=name.BoundingBox(); name=name.translate((-(b.xmin+b.xmax)/2,-(b.ymin+b.ymax)/2,0)).rotate((0,0,0),(1,0,0),180).translate((0,16,DEPTH))
cutters+=name.Solids()
cut=cq.Compound.makeCompound(cutters)
# All cutter volume above z=0 must be fully inside original bottom.
inside=cut.intersect(base).Volume()
expected=sum(c.Volume() for c in cutters)*DEPTH/(DEPTH+.01)
assert abs(inside-expected)<1e-4,(inside,expected)
new=base.cut(cut); assert new.isValid() and len(new.Solids())==1
parts[0]=new
colors=[(.988,.925,.839),(.725,.851,.922),(.988,.925,.839),(.988,.925,.839)]
names=['ivory_bottom_personal_mark','light_blue_body','ivory_rim','ivory_logo_with_tenons']
a=cq.Assembly(name='LV_bowl_and_separate_tenon_logo')
for n,s,c in zip(names,parts,colors):a.add(s,name=n,color=cq.Color(*c))
f=OUT/'LV_bowl_and_logo.step';a.save(str(f))
r=cq.importers.importStep(str(f)).val();assert len(r.Solids())==4 and all(s.isValid() for s in r.Solids())
report={'source_step':str(SRC),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'personal_vector':str(SVG),'name':'苗壮','engraving_depth_mm':DEPTH,'logo_width_mm':WIDTH,'logo_height_mm':512*scale,'font_size_mm':9,'minimum_remaining_bottom_thickness_mm':1.6,'solids':4,'all_valid':True,'removed_volume_mm3':base.Volume()-new.Volume(),'unchanged_other_solid_volumes_mm3':[s.Volume() for s in parts[1:]],'output_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
(OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
cq.exporters.export(new,str(OUT/'bottom-preview.svg'),opt={'projectionDir':(0,0,-1),'showHidden':False,'width':900,'height':900,'marginLeft':30,'marginTop':30,'strokeWidth':.3})
print(json.dumps(report,ensure_ascii=False,indent=2))
