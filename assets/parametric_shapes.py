"""Reusable star and crescent, dimensions in mm. Requires CadQuery 2.x.
Run: python parametric_shapes.py --shape star --diameter 30 --thickness 3
Outputs one STEP plus a matching silhouette SVG. No project-specific mount.
"""
import argparse,math
from pathlib import Path
import cadquery as cq

def build(shape='star',diameter=30,thickness=3,points=5,inner_ratio=.46,cut_ratio=.92,offset_ratio=.42):
    assert diameter>0 and thickness>0
    r=diameter/2
    if shape=='star':
        assert 3<=points<=32 and .1<=inner_ratio<=.9
        pts=[((r if i%2==0 else r*inner_ratio)*math.cos(math.pi/2+i*math.pi/points),(r if i%2==0 else r*inner_ratio)*math.sin(math.pi/2+i*math.pi/points)) for i in range(points*2)]
        s=cq.Workplane('XY').polyline(pts).close().extrude(thickness).val()
        graphic='<polygon points="'+ ' '.join(f'{x},{-y}' for x,y in pts)+'"/>'
    else:
        assert .5<=cut_ratio<=1.2 and .15<=offset_ratio<=.8 and abs(1-cut_ratio)<offset_ratio<1+cut_ratio
        s=cq.Workplane('XY').circle(r).extrude(thickness).cut(cq.Workplane('XY').center(r*offset_ratio,0).circle(r*cut_ratio).extrude(thickness)).val()
        graphic=f'<defs><mask id="cut"><rect x="{-r}" y="{-r}" width="{diameter}" height="{diameter}" fill="white"/><circle cx="{r*offset_ratio}" cy="0" r="{r*cut_ratio}" fill="black"/></mask></defs><circle r="{r}" mask="url(#cut)"/>'
    assert s.isValid() and len(s.Solids())==1
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-r*1.15} {-r*1.15} {diameter*1.15} {diameter*1.15}" fill="#202622">{graphic}</svg>'
    return s,svg

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--shape',choices=['star','moon'],default='star');p.add_argument('--diameter',type=float,default=30);p.add_argument('--thickness',type=float,default=3);p.add_argument('--points',type=int,default=5);p.add_argument('--inner-ratio',type=float,default=.46);p.add_argument('--cut-ratio',type=float,default=.92);p.add_argument('--offset-ratio',type=float,default=.42);p.add_argument('--output',type=Path,default=Path(__file__).parent);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    s,svg=build(a.shape,a.diameter,a.thickness,a.points,a.inner_ratio,a.cut_ratio,a.offset_ratio)
    cq.exporters.export(s,str(a.output/(a.shape+'.step')));(a.output/(a.shape+'.svg')).write_text(svg)
    print(a.shape,'valid=',s.isValid(),'solids=',len(s.Solids()),'volume_mm3=',round(s.Volume(),3))
