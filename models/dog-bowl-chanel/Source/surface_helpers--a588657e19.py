import cadquery as cq
from OCP.TColgp import TColgp_Array2OfPnt
from OCP.TColStd import TColStd_Array1OfReal,TColStd_Array1OfInteger
from OCP.Geom import Geom_BSplineSurface
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
def directface(points):
 n,m=len(points),len(points[0]);p=TColgp_Array2OfPnt(1,n,1,m)
 for i in range(n):
  for j in range(m):p.SetValue(i+1,j+1,points[i][j].toPnt())
 def knots(n):
  k=TColStd_Array1OfReal(1,n-2);mult=TColStd_Array1OfInteger(1,n-2)
  for i in range(1,n-1):k.SetValue(i,float(i-1));mult.SetValue(i,4 if i in [1,n-2] else 1)
  return k,mult
 uk,um=knots(n);vk,vm=knots(m)
 surface=Geom_BSplineSurface(p,uk,vk,um,vm,3,3)
 return cq.Face(BRepBuilderAPI_MakeFace(surface,1e-6).Face())
