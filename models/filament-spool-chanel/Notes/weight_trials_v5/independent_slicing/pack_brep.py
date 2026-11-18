from pathlib import Path
import cadquery as cq,zipfile,xml.etree.ElementTree as E,json,sys
D=Path('/tmp/chanel_100g');P=Path(sys.argv[1]);tag=sys.argv[2];s=cq.importers.importBrep(str(P)).val();v,t=s.tessellate(.01,.1);print(len(v),len(t),flush=True)
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';E.register_namespace('',ns)
r=E.Element('{'+ns+'}model',{'unit':'millimeter'});res=E.SubElement(r,'{'+ns+'}resources');obj=E.SubElement(res,'{'+ns+'}object',{'id':'65537','type':'model'});mesh=E.SubElement(obj,'{'+ns+'}mesh');vs=E.SubElement(mesh,'{'+ns+'}vertices');ts=E.SubElement(mesh,'{'+ns+'}triangles')
for a in v:E.SubElement(vs,'{'+ns+'}vertex',{'x':str(a.x),'y':str(a.y),'z':str(a.z)})
for a,b,c in t:E.SubElement(ts,'{'+ns+'}triangle',{'v1':str(a),'v2':str(b),'v3':str(c)})
xml=E.tostring(r,encoding='utf-8',xml_declaration=True)
with zipfile.ZipFile('/tmp/chanel_shell_ab/on.3mf') as src,zipfile.ZipFile(D/(tag+'_base.3mf'),'w',zipfile.ZIP_DEFLATED) as dst:
 for n in src.namelist():
  b=src.read(n)
  if n=='3D/Objects/object_1.model':b=xml
  elif n=='3D/3dmodel.model':b=b.replace(b'120.424375 126.75143 20.3575287',b'120.424375 126.75143 0')
  elif n=='Metadata/model_settings.config':b=b.replace(b'wide_half',b'narrow_half')
  dst.writestr(n,b)
(D/(tag+'_geometry.json')).write_text(json.dumps({'source':str(P),'volume_mm3':s.Volume(),'valid':s.isValid(),'vertices':len(v),'triangles':len(t),'tessellation':'CadQuery .01/.1 relative deflection, not absolute error guarantee'},indent=2))
