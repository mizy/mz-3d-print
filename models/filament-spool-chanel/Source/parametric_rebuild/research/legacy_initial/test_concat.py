from fit_wire import *
from OCP.Geom import Geom_TrimmedCurve
from OCP.GeomConvert import GeomConvert_CompCurveToBSplineCurve
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge

def single(w):
 acc=GeomConvert_CompCurveToBSplineCurve()
 for e in w.Edges():
  a=e._geomAdaptor();c=Geom_TrimmedCurve(a.Curve().Curve(),a.FirstParameter(),a.LastParameter())
  assert acc.Add(c,1e-6,True,True,2)
 return cq.Wire.assembleEdges([cq.Edge(BRepBuilderAPI_MakeEdge(acc.BSplineCurve()).Edge())])
if __name__=='__main__':
 d=json.load(open('/tmp/chanel-interface-input/profiles.json'))
 for part in ['wide','narrow']:
  ws=[]
  for s in d[part]['sections']:
   z=s['z']
   if part=='wide' and z>37:continue
   if part=='narrow' and z<28:continue
   loop=min(s['loops'],key=lambda l:l['mean_r']) if part=='wide' else max(s['loops'],key=lambda l:l['mean_r'])
   w,r=fit_wire(loop['points_xy'],z);ws.append(single(w))
  try:
   loft=cq.Solid.makeLoft(ws,ruled=True);print('LOFT',part,loft.isValid(),len(loft.Faces()),flush=True);cq.exporters.export(loft,f'/tmp/chanel-interface-input/{part}_singlecurve_loft_test.step')
  except Exception as e:print(type(e),str(e),flush=True)
