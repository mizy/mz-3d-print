"""Low-material wall diameter + two M3 coupling-seat coupon, no hose sample."""
from pathlib import Path
import json
import build123d as b
import trimesh

out=Path(__file__).resolve().parent
def tube(od,inner,z,h):
    align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN)
    return b.Pos(0,0,z)*b.Cylinder(od/2,h,align=align)-b.Pos(0,0,z-1)*b.Cylinder(inner/2,h+2,align=align)
def box(x,y,z,center):
    return b.Pos(*center)*b.Box(x,y,z)

# Production wall and seat cross sections; only axial separation is shortened.
shape=tube(56.4,51.4,0,3)
flange=tube(68,51.4,3,2)
neck=tube(59.8,55,5,8)
for sign in (-1,1):
    sector=box(12,16,20,(sign*30,0,7))
    shape+=flange&sector
    shape+=neck&sector
    shape+=box(7,12,8,(sign*31,0,9))
    hole=b.Pos(sign*31,0,9)*b.Rot(90,0,0)*b.Cylinder(1.7,30)
    shape-=hole
parts=[('wall_coupling_A',shape&box(120,60,40,(0,30.1,10))),
       ('wall_coupling_B',shape&box(120,60,40,(0,-30.1,10)))]
report={}
for name,part in parts:
    assert part.is_valid and len(part.solids())==1
    bore=b.Pos(0,0,6)*b.Cylinder(25.5,20)
    assert (part&bore).volume<1e-6
    b.export_stl(part,out/(name+'.stl'),tolerance=0.04,angular_tolerance=0.08)
    mesh=trimesh.load(out/(name+'.stl'),force='mesh')
    assert mesh.is_watertight and mesh.is_winding_consistent
    report[name]=dict(valid=True,watertight=True,volume_mm3=part.volume,
                     estimated_PETG_g=part.volume/1000*1.25)
report['total_estimated_PETG_g']=sum(x['estimated_PETG_g'] for x in report.values())
assert (parts[0][1]&parts[1][1]).volume<1e-6
(out/'checks_and_mass.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
