"""Strict lib3mf import and archive checks; does not open a slicer."""
import json,sys,zipfile,xml.etree.ElementTree as E
import lib3mf
p=sys.argv[1]
w=lib3mf.get_wrapper()
model=w.CreateModel()
reader=model.QueryReader('3mf')
reader.SetStrictModeActive(True)
with open(p,'rb') as f:reader.ReadFromBuffer(f.read())
items=model.GetBuildItems().Count()
assert items==21 and reader.GetWarningCount()==0,(items,reader.GetWarningCount())
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None and not any('gcode' in q.lower() for q in z.namelist())
 for q in z.namelist():
  if q.startswith('3D/Objects/') and q.endswith('.model'):
   assert E.fromstring(z.read(q)).find('{*}build') is not None,q
 a=E.fromstring(z.read('Metadata/model_settings.config'))
 assert len(a.findall('plate'))==1 and len(a.findall('object'))==21
 keys={n.attrib['key'] for o in a.findall('object') for n in o.findall('.//metadata') if 'key' in n.attrib}
 assert keys=={'name','matrix'}
 d=json.loads(z.read('Metadata/project_settings.config'))
 assert d['printer_settings_id']=='Bambu Lab P1S 0.4 nozzle'
 assert d['filament_settings_id']==['Generic PETG']
 assert tuple(d[k] for k in ('sparse_infill_density','sparse_infill_pattern','wall_loops','layer_height'))==('10%','gyroid','2','0.2')
print('PASS strict lib3mf',w.GetLibraryVersion(),'21 pieces, 0 warnings; one unsliced plate with global P1S/PETG profile.')
