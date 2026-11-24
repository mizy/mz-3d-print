"""Four native CAD motifs, all SVG paths, unobtrusive local island connections.
Approximation <=.002mm at 25 samples for near-line/circle Beziers; all other curves retained.
"""
import math,re,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np,cadquery as cq
from svgpathtools import parse_path,Line,CubicBezier,QuadraticBezier
from shapely.geometry import Polygon,box
from shapely.ops import nearest_points,unary_union

def motif(name,size,height,bridge_width=1.2):
 root=ET.parse(Path(__file__).with_name('lv-'+name+'.svg')).getroot();vb=list(map(float,root.attrib['viewBox'].split()));solids=[];footprints=[]
 for e in [x for x in root.iter() if x.tag.endswith('path')]:
  path=parse_path(e.attrib['d']);a,b,c,d,tx,ty=map(float,re.findall(r'[-+]?(?:\d*\.\d+|\d+)',e.attrib.get('transform','matrix(1,0,0,1,0,0)')))
  def xy(z):return ((a*z.real+c*z.imag+tx-vb[0]-vb[2]/2)*size/max(vb[2:]),-(b*z.real+d*z.imag+ty-vb[1]-vb[3]/2)*size/max(vb[2:]))
  def vec(z):x,y=xy(z);return cq.Vector(x,y,-.1)
  wires=[];polys=[]
  for sp in path.continuous_subpaths():
   edges=[];pts=[]
   for seg in sp:
    pts.extend(xy(seg.point(j/24)) for j in range(24))
    if isinstance(seg,Line):edge=cq.Edge.makeLine(vec(seg.start),vec(seg.end))
    elif isinstance(seg,CubicBezier):
     p0=np.array(xy(seg.start));p1=np.array(xy(seg.end));samples=np.array([xy(seg.point(t)) for t in np.linspace(0,1,25)]);delta=p1-p0;length=np.linalg.norm(delta);errline=max(abs(delta[0]*(s-p0)[1]-delta[1]*(s-p0)[0])/max(length,1e-15) for s in samples)
     if length>1e-6 and errline<.002:edge=cq.Edge.makeLine(vec(seg.start),vec(seg.end))
     else:
      mid=np.array(xy(seg.point(.5)));mat=np.array([2*(mid-p0),2*(p1-p0)]);rhs=np.array([mid@mid-p0@p0,p1@p1-p0@p0])
      try:center=np.linalg.solve(mat,rhs);radius=np.linalg.norm(p0-center);err=max(abs(np.linalg.norm(s-center)-radius) for s in samples)
      except np.linalg.LinAlgError:err=1e10
      if err<.002 and radius<1000:edge=cq.Edge.makeThreePointArc(vec(seg.start),vec(seg.point(.5)),vec(seg.end))
      else:edge=cq.Edge.makeBezier([vec(seg.start),vec(seg.control1),vec(seg.control2),vec(seg.end)])
    elif isinstance(seg,QuadraticBezier):edge=cq.Edge.makeBezier([vec(seg.start),vec(seg.control),vec(seg.end)])
    else:raise ValueError('Unsupported SVG segment')
    if edge.Length()>1e-8:edges.append(edge)
   if abs(sp.end-sp.start)>1e-8:edges.append(cq.Edge.makeLine(vec(sp.end),vec(sp.start)))
   wires.append(cq.Wire.assembleEdges(edges));polys.append(Polygon(pts))
  depths=[sum(j!=i and pj.contains(pi.representative_point()) and pj.area>pi.area for j,pj in enumerate(polys)) for i,pi in enumerate(polys)]
  for i,wire in enumerate(wires):
   if depths[i]%2==0:
    js=[j for j in range(len(wires)) if depths[j]==depths[i]+1 and polys[i].contains(polys[j].representative_point())]
    solids.append(cq.Solid.extrudeLinear(wire,[wires[j] for j in js],cq.Vector(0,0,height+.2)));footprints.append(Polygon(polys[i].exterior.coords,[polys[j].exterior.coords for j in js]))
 raw=solids[0].fuse(*solids[1:]).clean() if len(solids)>1 else solids[0]
 # Locate islands in combined artwork, including the enclosed LV triangle.
 material=box(-size,-size,size,size).difference(unary_union(footprints));pieces=list(material.geoms) if hasattr(material,'geoms') else [material];outer=max(pieces,key=lambda p:p.area);bridges=[]
 for island in pieces:
  if island is outer:continue
  x,y=nearest_points(island,outer);length=math.hypot(y.x-x.x,y.y-x.y)
  tab=cq.Workplane('XY').box(length+.8,bridge_width,height+1,centered=(True,True,False)).translate((0,0,-.3)).val().rotate((0,0,0),(0,0,1),math.degrees(math.atan2(y.y-x.y,y.x-x.x))).translate(((x.x+y.x)/2,(x.y+y.y)/2,0));bridges.append(tab)
  if name in ('circle','diamond'):bridges.append(tab.rotate((0,0,0),(0,0,1),180))
 out=raw.cut(*bridges).clean() if bridges else raw
 if not out.isValid():raise ValueError('Invalid SVG motif')
 return out
