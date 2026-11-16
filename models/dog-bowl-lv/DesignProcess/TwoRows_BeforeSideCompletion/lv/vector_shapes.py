import fitz,cadquery as cq
from svgpathtools import parse_path,Line,CubicBezier,QuadraticBezier
from shapely.geometry import Polygon
from pathlib import Path
D=fitz.open(str(Path(__file__).parent/'source.ai'))[0].get_drawings()
IDS={'LV':[95,96],'diamond':[93],'pointed':[92],'circle':[97]}
def raw(d):
 out=[];last=None
 for it in d['items']:
  typ=it[0]
  if typ in ['c','l']:
   p=it[1]
   if last is None or abs(last-p)>1e-5:
    if last is not None:out.append('Z')
    out.append(f'M{p.x},{p.y}')
   if typ=='c':out.append('C'+' '.join(f'{p.x},{p.y}' for p in it[2:]));last=it[4]
   else:out.append(f'L{it[2].x},{it[2].y}');last=it[2]
  elif typ=='re':
   if last is not None:out.append('Z')
   r=it[1];out.append(f'M{r.x0},{r.y0} H{r.x1} V{r.y1} H{r.x0} Z');last=None
 if last is not None:out.append('Z')
 return ' '.join(out)
def symbol(kind,height,depth):
 ds=[D[i] for i in IDS[kind]];bb=fitz.Rect(ds[0]['rect'])
 for d in ds[1:]:bb |= d['rect']
 sc=height/bb.height;cx=(bb.x0+bb.x1)/2;cy=(bb.y0+bb.y1)/2
 def pt(p):return cq.Vector((p.real-cx)*sc,0,(cy-p.imag)*sc)
 solids=[]
 for d in ds:
  loops=parse_path(raw(d)).continuous_subpaths();wires=[];polys=[]
  for loop in loops:
   edges=[];samples=[]
   for seg in loop:
    if abs(seg.end-seg.start)<1e-10:continue
    if isinstance(seg,Line):edges.append(cq.Edge.makeLine(pt(seg.start),pt(seg.end)))
    elif isinstance(seg,CubicBezier):edges.append(cq.Edge.makeBezier([pt(seg.start),pt(seg.control1),pt(seg.control2),pt(seg.end)]))
    else:raise TypeError(type(seg))
    samples += [(seg.point(t/20).real,seg.point(t/20).imag) for t in range(20)]
   wires.append(cq.Wire.assembleEdges(edges));polys.append(Polygon(samples))
  parents=[]
  for i,p in enumerate(polys):
   candidates=[j for j,q in enumerate(polys) if j!=i and q.area>p.area and q.contains(p.representative_point())]
   parents.append(min(candidates,key=lambda j:polys[j].area) if candidates else None)
  def level(i):return 0 if parents[i] is None else 1+level(parents[i])
  for i,w in enumerate(wires):
   if level(i)%2==0:
    holes=[wires[j] for j in range(len(wires)) if parents[j]==i]
    solids.append(cq.Solid.extrudeLinear(w,holes,cq.Vector(0,-depth,0)))
 result=solids[0].fuse(*solids[1:]).clean() if len(solids)>1 else solids[0]
 assert result.isValid(),kind
 return result
if __name__=='__main__':
 for k in IDS:
  s=symbol(k,7,1.6);print(k,s.isValid(),len(s.Solids()),s.Volume(),flush=True)
