import math
import cadquery as cq
from shapely.geometry import Point,Polygon,box,LineString
from shapely.affinity import translate
from shapely.ops import unary_union,nearest_points

def double_c(xy_scale=1., height=10.):
    # Original geometric interpretation, not an official vector or licensed product.
    outer=Point(0,0).buffer(5.5,quad_segs=40);inner=Point(0,0).buffer(3.8,quad_segs=40)
    ring=outer.difference(inner)
    wedge=Polygon([(0,0),(-12,-8),(-12,8)])
    left=translate(ring.difference(wedge),xoff=-2.7)
    right=translate(ring.difference(Polygon([(0,0),(12,8),(12,-8)])),xoff=2.7)
    cut=unary_union([left,right]); material=box(-12,-9,12,9).difference(cut)
    components=list(material.geoms) if hasattr(material,'geoms') else [material];outer_material=max(components,key=lambda p:p.area)
    ties=[]
    for p in components:
        if p is outer_material:continue
        a,b=nearest_points(p,outer_material)
        dx,dy=b.x-a.x,b.y-a.y;length=math.hypot(dx,dy)
        tie=LineString([(a.x-dx/length*.3,a.y-dy/length*.3),(b.x+dx/length*.3,b.y+dy/length*.3)]).buffer(.45,cap_style=2)
        ties.append(tie)
    if ties:cut=cut.difference(unary_union(ties))
    assert box(-12,-9,12,9).difference(cut).geom_type=='Polygon'
    s=xy_scale
    left=cq.Workplane('XY').circle(5.5*s).circle(3.8*s).extrude(height).translate((-2.7*s,0,-.5)).val()
    right=cq.Workplane('XY').circle(5.5*s).circle(3.8*s).extrude(height).translate((2.7*s,0,-.5)).val()
    w1=cq.Workplane('XY').polyline([(0,0),(-12*s,-8*s),(-12*s,8*s)]).close().extrude(height+2).translate((-2.7*s,0,-1)).val()
    w2=cq.Workplane('XY').polyline([(0,0),(12*s,8*s),(12*s,-8*s)]).close().extrude(height+2).translate((2.7*s,0,-1)).val()
    raw=left.cut(w1).fuse(right.cut(w2))
    for tie in ties:
        tab=cq.Workplane('XY').polyline([(x*s,y*s) for x,y in list(tie.exterior.coords)[:-1]]).close().extrude(height+2).translate((0,0,-1)).val()
        raw=raw.cut(tab)
    return raw.clean()
