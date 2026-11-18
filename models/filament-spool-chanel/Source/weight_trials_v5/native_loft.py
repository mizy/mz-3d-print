import cadquery as cq,numpy as np
from OCP.BRepTools import BRepTools_WireExplorer
from OCP.TopAbs import TopAbs_REVERSED
from OCP.Geom import Geom_TrimmedCurve
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections

def ordered(w):
 out=[];ex=BRepTools_WireExplorer(w.wrapped)
 while ex.More():
  e=cq.Edge(ex.Current());a=e._geomAdaptor();c=Geom_TrimmedCurve(a.Curve().Curve(),a.FirstParameter(),a.LastParameter())
  if e.wrapped.Orientation()==TopAbs_REVERSED:c.Reverse()
  out.append(cq.Edge(BRepBuilderAPI_MakeEdge(c).Edge()));ex.Next()
 return out

def pair_loft(w1,w2):
 lists=[ordered(w1),ordered(w2)];cums=[np.r_[0,np.cumsum([e.Length() for e in es])] for es in lists];cums=[cs/cs[-1] for cs in cums]
 knots=np.unique(np.r_[*cums]);knots=np.array([k for i,k in enumerate(knots) if i==0 or k-knots[i-1]>1e-13]);knots[-1]=1.;ws=[]
 for es,cs in zip(lists,cums):
  edges=[]
  for lo,hi in zip(knots,knots[1:]):
   if (hi-lo)*max(sum(e.Length() for e in ls) for ls in lists)<1e-7:continue
   i=min(len(es)-1,np.searchsorted(cs,(lo+hi)/2,side='right')-1);a=max(0.,(lo-cs[i])/(cs[i+1]-cs[i]));b=min(1.,(hi-cs[i])/(cs[i+1]-cs[i]));e=es[i]
   try:edges.append(e.trim(e.paramAt(a),e.paramAt(b)))
   except Exception:
    print('TRIM_FAILURE',lo,hi,i,a,b,e.Length(),e.paramAt(a),e.paramAt(b),flush=True);raise
  ws.append(cq.Wire.assembleEdges(edges))
 b=BRepOffsetAPI_ThruSections(True,True,1e-6);b.CheckCompatibility(False)
 for w in ws:b.AddWire(w.wrapped)
 b.Build();return cq.Shape.cast(b.Shape())
