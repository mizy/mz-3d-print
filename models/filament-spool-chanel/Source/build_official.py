from pathlib import Path
import sys,math,json
R=Path(__file__).parent;sys.path.insert(0,str(R/'deps'));sys.path.insert(0,str(R))
import trimesh,numpy as np,cadquery as cq,manifold3d as md
from functools import reduce
from chanel_motif import double_c

def cyl(r,z0,z1,n=360):
 m=trimesh.creation.cylinder(radius=r,height=z1-z0,sections=n);m.apply_translation([0,0,(z0+z1)/2]);return m
def cadmesh(s,name):
 cq.exporters.export(s,str(R/f'{name}.step'));cq.exporters.export(s,str(R/f'{name}.stl'),tolerance=.025,angularTolerance=.08);return trimesh.load(R/f'{name}.stl')
def mf(m):
 v=md.Manifold(md.Mesh64(vert_properties=np.array(m.vertices,dtype=np.float64,order="C",copy=True),tri_verts=np.array(m.faces,dtype=np.uint64,order="C",copy=True)));assert str(v.status())=='Error.NoError',v.status();return v
def tm(m):
 q=m.to_mesh64();return trimesh.Trimesh(q.vert_properties,q.tri_verts,process=False)
def union(*m):return tm(reduce(lambda a,b:a+b,map(mf,m)))
def diff(a,b):return tm(mf(a)-mf(b))
def inter(a,b):return tm(mf(a)^mf(b))
# Source rim retained outside r94. Preserve 8 actual holes and their full-height bosses.
holes=[(sx*a,sy*b) for a,b in [(94.608,15),(15,94.608)] for sx in [-1,1] for sy in [-1,1]]
relief=cyl(98.8,-1,5)
for x,y in holes:
 boss=cyl(3.1,-2,6,64);boss.apply_translation([x,y,0]);relief=diff(relief,boss)
for a in range(0,360,45):
 bridge=trimesh.creation.box([7,2.4,4]);bridge.apply_translation([96,0,1]);bridge.apply_transform(trimesh.transformations.rotation_matrix(math.radians(a),[0,0,1]));relief=diff(relief,bridge)
# Shared lightweight flange, same original double-C geometry, moderately enlarged 10%.
plate=cq.Workplane('XY').circle(94.0).circle(43.7).extrude(.6).val()
for a in range(0,360,45):
 rib=cq.Workplane('XY').box(54,4.0,2.6,centered=(True,True,False)).translate((70.5,0,.6)).val().rotate((0,0,0),(0,0,1),a)
 plate=plate.fuse(rib)
cut=[];motif=double_c().scale(1.1)
for rad,n in [(53,16),(70,24),(87,32)]:
 for i in range(n):
  a=2*math.pi*(i+.5)/n;cut.append((motif.scale(1/1.1) if rad==87 else motif).translate((rad*math.cos(a),rad*math.sin(a),0)))
plate=plate.cut(*cut).clean()
# No annular slots and no added interior rings; preserve continuous thin skin.
print('plate',plate.isValid(),len(plate.Solids()),[(p.Volume(),p.Center().toTuple()) for p in plate.Solids()],flush=True)
assert plate.isValid() and len(plate.Solids())==1
pm=cadmesh(plate,'flange_native');out={'source':'user-provided Bambu spool2.1 STL; provenance URL unverified','flange_skin_mm':.6,'flange_ribs':8,'rib_width_mm':4.0,'rib_total_height_mm':3.2,'interior_load_rings':False,'rolling_rim_inner_radius_mm':95.0,'lower_core_inner_radius_mm':36.8,'double_c_count_per_face':72,'parts':{}}
for k,r_top in [('wide',33.35),('narrow',29.75)]:
 source=trimesh.load(R/f'official_{k}_stitched.stl')
 parts=source.split(); assert all(p.is_volume for p in parts); source=union(*parts)
 hub=inter(source,cyl(44,-1,60));rim=union(diff(diff(source,cyl(93.8,-1,60)),relief),diff(source,cyl(95.0,-1,60)))
 print(k,'source fused',source.volume,'hub',hub.volume,'rim',rim.volume,flush=True)
 # Preserve all exterior geometry and original inner interfaces at/above z24.
 top_z=22.0 if k=='wide' else 24.0
 inner=39.5 if k=='wide' else 39.4
 hub=diff(hub,cyl(inner,-1,top_z))
 # Shallow root ledge relief retains 1.4 mm continuous foot and protects +Y locating-key foundation.
 ledge=diff(cyl(44,1.4,3.1),cyl(42,1.3,3.2))
 keybase=trimesh.creation.box([8,12,5]);keybase.apply_translation([0,42,2]);ledge=diff(ledge,keybase)
 hub=diff(hub,ledge)
 # Continuous sloped diaphragm replacing the four internal ribs below z24.
 z0=top_z-(39.9-r_top)
 shoulder=cq.Workplane('XZ').polyline([(39.9,z0),(r_top,top_z),(r_top-1.7,top_z),(r_top-1.7,top_z-3),(36.8,z0-1.3)]).close().revolve(360,(0,0),(0,1)).val()
 sm=cadmesh(shoulder,f'shoulder_native_{k}');core_add=diff(cyl(39.7,.6,z0+.1),cyl(36.8,.5,z0+.2));m=union(hub,rim,pm,sm,core_add)
 if k=='wide':
  protected_key=trimesh.creation.box([6,3,8.1]);protected_key.apply_translation([0,42.5,4]);protected_key=inter(protected_key,cyl(43.9,-.1,8.1))
  m=union(diff(m,protected_key),inter(source,protected_key))
 m.export(R/f'CHANEL_SOURCE21_{k}.obj',digits=15);m.export(R/f'CHANEL_SOURCE21_{k}.stl');v=trimesh.load(R/f'CHANEL_SOURCE21_{k}.obj',process=False)
 _,counts=np.unique(v.edges_sorted,axis=0,return_counts=True)
 out['parts'][k]={'volume_mm3':float(v.volume),'solid_mass_g_density_1_37':float(v.volume*.00137),'watertight':bool(v.is_watertight),'non_two_edges':int((counts!=2).sum()),'degenerate_faces':int((~v.nondegenerate_faces(height=1e-8)).sum()),'components':len(v.split(only_watertight=False,repair=False)),'faces':len(v.faces),'bounds_mm':v.bounds.tolist(),'shoulder_start_z_mm':z0}
 print(k,out['parts'][k],flush=True)
out['total_solid_mass_g']=sum(p['solid_mass_g_density_1_37'] for p in out['parts'].values());(R/'design_validation.json').write_text(json.dumps(out,indent=2))
