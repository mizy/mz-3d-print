"""Analytic load-bearing body; nominal fits to reference mesh, not triangle conversion."""
from build import *

def annulus(ro,ri,z0,z1):
 return cq.Workplane('XY').circle(ro).circle(ri).extrude(z1-z0).translate((0,0,z0)).val()

def rolling_rim():
 # Source bottom/top shell mismatch ~.015 mm is intentionally replaced by a clean revolved section.
 ring=annulus(100.013,95.,0.,3.615)
 holes=[(sx*a,sy*b) for a,b in [(94.608,15),(15,94.608)] for sx in [-1,1] for sy in [-1,1]]
 bosses=[cq.Solid.makeCylinder(3.1,3.615,cq.Vector(x,y,0)) for x,y in holes]
 ring=ring.fuse(*bosses)
 cuts=[cq.Solid.makeCylinder(1.7071,4.,cq.Vector(x,y,-.1)) for x,y in holes]
 return ring.cut(*cuts).clean()

def lower_core(part):
 ro=40.85 if part=='wide' else 40.65
 top,rt=(22.,33.35) if part=='wide' else (24.,29.75)
 z0=top-(39.9-rt)
 # Preserve the thickened lower wall and the continuous sloping diaphragm.
 wall=annulus(ro,36.8,.6,z0+.1)
 foot=annulus(44.,39.5 if part=='wide' else 39.4,0,1.4)
 wall=wall.fuse(foot,build_shoulder(part)).clean()
 # Source +Y locating key, tapered in X and rounded toward its crown.
 if part=='wide':
  zs=[1.4,4.,5.,6.,7.,7.7,7.8,7.815]
  widths=[3.6,3.5981,3.3879,3.1777,2.8949,1.4432,1.0553,.7]
  wires=[cq.Workplane('XY').workplane(offset=z).center(-.02735,(40.4+43.70056)/2).rect(w,43.70056-40.4).val() for z,w in zip(zs,widths)]
  key=cq.Solid.makeLoft(wires,ruled=True);wall=wall.fuse(key).clean()
 return wall

def outer_tube(part):
 if part=='wide':
  profile=[(40.848,15.35),(40.848,39.61506),(39.75,40.715057373),(39.,40.715057373),(39.,22.),(39.5,22.),(39.5,15.35)]
  center=(-.0273430863,.0010603425,0)
 else:
  profile=[(40.648,13.75),(40.648,24.71305),(39.65,25.7150566),(38.898,25.7150566),(38.898,27.11506),(38.40,27.9150562),(37.698,27.9150562),(37.698,24.),(39.4,24.),(39.4,13.75)]
  # Source outer cylinder was measured in the same normalized bbox frame.
  center=(.0015810415,-.0274228517,0)
 return cq.Workplane('XZ').polyline(profile).close().revolve(360,(0,0),(0,1)).val().translate(center)

def structural_body(part):
 plate=cq.importers.importStep(str(R/'flange_native_rebuilt.step')).val()
 result=plate.fuse(rolling_rim(),lower_core(part),outer_tube(part)).clean()
 return result
