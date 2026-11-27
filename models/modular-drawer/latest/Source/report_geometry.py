#!/usr/bin/env python3
"""Build a self-contained Chinese review HTML from released analytic STEP sources.
Use Python with FreeCAD/Part/TechDraw importable. No STEP is generated/changed here.
"""
import argparse, array, base64, hashlib,json,math,re,sys
from pathlib import Path
import FreeCAD as A
import Part,TechDraw as T
V=A.Vector
AXES={
 'front':((1,0,0),(0,0,1),(0,-1,0)),
 'top':((1,0,0),(0,1,0),(0,0,1)),
 'side':((0,1,0),(0,0,1),(1,0,0)),
 'side_top':((0,1,0),(-1,0,0),(0,0,1)),
 'rear_end':((-1,0,0),(0,0,1),(0,1,0)),
}
TITLES={
 'front':('正视 · 前端','−Y 观察｜X 向右，Z 向上'),
 'top':('俯视','+Z 观察｜X 向右，Y 向上'),
 'side':('侧视','+X 观察｜Y 向右，Z 向上，前端在左'),
 'side_top':('俯视','+Z 观察｜Y 向右，−X 向上，前端在左'),
 'rear_end':('后端视图','+Y 观察｜−X 向右，Z 向上'),
}
def bbox(q):
 b=q.optimalBoundingBox(False,False)
 return [round(getattr(b,a+s),6) for a in 'XYZ' for s in ('Min','Max')]
def size(bb):return [round(bb[i+1]-bb[i],5) for i in (0,2,4)]
def kind(bb):
 x,y,z=size(bb)
 if x>80 and y>130 and z>45:return 'drawer'
 if 7<x<35 and y>150 and z>50:return 'side'
 if x>65 and y<30 and z>45:return 'rear'
 if x>65 and y<40 and z<20:return 'front'
 return 'hardware'
def discover(folder,cfg,key,prefix):
 n=cfg.get('files',{}).get(key)
 paths=[folder/n] if n else sorted(folder.glob(prefix+'*.step'))
 if len(paths)!=1 or not paths[0].is_file():
  raise ValueError(f'{key}: expected exact relative filename or unique {prefix}*.step: {paths!r}')
 if not paths[0].resolve().is_relative_to(folder.resolve()):raise ValueError('STEP outside input directory')
 return paths[0]
def inspect(path,cfg,key):
 sha=hashlib.sha256(path.read_bytes()).hexdigest()
 expect=cfg.get('sha256',{}).get(key)
 if expect is not None and expect!=sha:raise ValueError(f'{key}: STEP hash mismatch')
 q=Part.read(str(path))
 n=len(q.Solids)
 if not q.isValid() or n<1 or key not in ('assembly','assembly_ready') and n!=1:raise ValueError(f'{key}: invalid STEP or wrong solid count: {n}')
 obj=dict(name=path.name,sha256=sha,bounds=bbox(q),nSolids=n)
 obj['extent']=size(obj['bounds'])
 url=cfg.get('hrefs',{}).get(key)
 if url is not None:
  if not re.fullmatch(r'(?:[\w .\-]+/)*[\w .\-]+\.step',url,re.I):raise ValueError('STEP href must be simple relative package path')
  obj['href']=url
 return q,obj
CHORD=.005
PROJECTION_TOL=.012
def close2(a,b,d=PROJECTION_TOL):
 return max(abs(x-y) for x,y in zip(a,b))<=d
def mouth_circles(q,y,rad):
 loc=[]
 for e in q.Edges:
  c=e.Curve
  if isinstance(c,Part.Circle) and abs(abs(c.Axis.y)-1)<.000001 and abs(c.Center.y-y)<.00001 and abs(c.Radius-rad)<.00001 and abs(e.Length-2*math.pi*c.Radius)<.00001:
   loc.append([round(c.Center.x,6),round(c.Center.y,6),round(c.Center.z,6),round(c.Radius,6)])
 return sorted({tuple(x) for x in loc})
def to_view(point,v):
 rows=AXES[v['key']]
 return [round(sum(x*k for x,k in zip(point,row))-o,6) for row,o in zip(rows,v['origin'])]
def views(q,order,include_tangent=False):
 r=[]
 for name in order:
  mat=A.Matrix()
  for i,row in enumerate(AXES[name],1):
   for j,value in enumerate(row,1):setattr(mat,f'A{i}{j}',float(value))
  shape=q.copy();shape.transformShape(mat,True,True)
  # projectEx exposes outline generators that the 4-group project omits.
  # In particular, smooth shaft silhouettes remain part of the actual BRep outline.
  # Group order is sharp, smooth, seam, outline, iso for each visibility class.
  g=T.projectEx(shape,V(0,0,1)); layers=[]; round_samples=[]
  def circle_key(e):
   c=e.Curve
   if not isinstance(c,Part.Circle) or abs(e.Length-2*math.pi*c.Radius)>.00001:return None
   return tuple(round(v,5) for v in (c.Center.x,c.Center.y,c.Radius))
  circles=sorted({k for e in g[0].Edges if (k:=circle_key(e)) is not None})
  show=set(circles)
  for k in (0,5):
   raw=list(g[k].Edges)+list(g[k+3].Edges)+(list(g[k+1].Edges) if include_tangent else [])
   edges=[e for e in raw if e.Length>.008 and not (k==5 and circle_key(e) in show)]
   lines=[]
   for e in edges:
    poly=[[round(v.x,5),round(v.y,5)] for v in e.discretize(Deflection=CHORD)]
    if k==0 and circle_key(e) is not None:round_samples.extend(poly)
    else:lines.append(poly)
   layers.append(lines)
  pts=[p for layer in layers for e in layer for p in e]+round_samples; assert pts,name
  sampled=[min(p[0] for p in pts),max(p[0] for p in pts),min(p[1] for p in pts),max(p[1] for p in pts)]
  # Dimension numbers come from actual transformed BRep extrema, not drawn points.
  b=bbox(shape);assert close2(sampled,b[:4]),(name,sampled,b[:4])
  x0,x1,y0,y1=b[:4]
  r.append(dict(key=name,title=TITLES[name][0],axes=TITLES[name][1],
   extent=[round(x1-x0,5),round(y1-y0,5)],origin=[x0,y0],brep_bounds=b[:4],projected_bounds=sampled,
   visible_full_circles=[[round(x-x0,5),round(y-y0,5),rad] for x,y,rad in circles],
   layers=[[[[round(x-x0,5),round(y-y0,5)] for x,y in edge] for edge in layer] for layer in layers]))
 return r
def bytes64(seq):
 if sys.byteorder!='little': seq.byteswap()
 return base64.b64encode(seq.tobytes()).decode('ascii')
def cinnamoroll_preview(s,min_y,relief):
 # Face-based preview colours from elevations measured in the STEP; one mesh/solid.
 rgb={'body':(255,254,244),'outline':(166,113,76),'eyes':(73,181,225),'cheeks':(248,157,185)}
 top=max(relief.values())
 vertices,triangles,colors=[],[],[]
 for f in s.Faces:
  y=f.CenterOfMass.y
  color=(129,165,178) if y>=-1e-7 else (201,218,225)
  if isinstance(f.Surface,Part.Plane) and y<0 and f.optimalBoundingBox(False,False).YLength<1e-5:
   for name,height in relief.items():
    if abs(y-(min_y+top-height))<1e-5:color=rgb[name]
  vs,ts=f.tessellate(.035 if y<0 else .18)
  count=len(vertices);vertices.extend(vs);colors.extend(color*len(vs))
  triangles.extend(tuple(count+i for i in tr) for tr in ts)
 return vertices,triangles,colors

def meshes(q,bb,deflection,relief=None):
 # Signed int16 at 0.02 mm around scene center. All meshes are visualization only.
 center=[(bb[i]+bb[i+1])/2 for i in (0,2,4)];unit=.02
 packets=[]
 for s in q.Solids:
  colors=None
  if relief:vs,ts,colors=cinnamoroll_preview(s,bb[2],relief)
  else:vs,ts=s.tessellate(deflection)
  if not vs or not ts:raise ValueError('Empty STEP tessellation')
  pv=array.array('h',(round((x-o)/unit) for p in vs for x,o in zip((p.x,p.y,p.z),center)))
  ix=array.array('I',(int(i) for t in ts for i in t))
  packet=dict(v=bytes64(pv),i=bytes64(ix),n=len(ts),kind=kind(bbox(s)))
  if colors:packet['rgb']=base64.b64encode(bytes(colors)).decode('ascii')
  packets.append(packet)
 return dict(meshes=packets,quantum=unit,center=center,deflection=deflection)
