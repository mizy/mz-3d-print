"""Exact coupon lineage, but V15 uses only the one-sided beam and rotor. No print pose."""
from pathlib import Path
from hashlib import sha256
import FreeCAD as A, Part
V=A.Vector
def one(s):
 s=s.removeSplitter();assert s.isValid() and len(s.Solids)==1
 return s.Solids[0]
def bb(x0,y0,z0,x1,y1,z1):return Part.makeBox(x1-x0,y1-y0,z1-z0,V(x0,y0,z0))
def C(a,b):return a.common(b).Volume
def get(source):
 S=list(Part.read(str(source)).Solids);assert len(S)==7
 base,beam,oldCam,oldRod,oldTool,rotSeat,pad=S
 X,Y,Z=V(1,0,0),V(0,1,0),V(0,0,1)
 camP=V(25.55,8.,5.)
 def cyl(r,L,x,y,z,axis):return Part.makeCylinder(r,L,V(x,y,z),axis)
 def tx(s,a):return s.rotated(camP,Y,a)
 # Only the previously published seven-part coupon changes here.
 # Old handle screw slot from Y=1.70..2.79 is rebuilt to its true circular end.
 # Insert from Y+; slot in large exposed rotor face at Y=12.90.
 rodEnd=20.45
 rod_r=2.20; guide_r=2.38
 headStart=24.15
 rodOriginal=one(oldRod.multiFuse([cyl(rod_r,23.40-13.02,13.02,8,5,X),cyl(2.23,24.60-headStart,headStart,8,5,X)]))
 rod=one(rodOriginal.cut(cyl(2.24,headStart-rodEnd,rodEnd,8,5,X).cut(cyl(1.35,headStart-rodEnd+.04,rodEnd-.02,8,5,X))))
 base=one(base.cut(bb(13.23,8-guide_r,5-guide_r,17.51,8+guide_r,10.18)))
 portFill=cyl(2.57,1.29,25.55,0,5,Y)
 housingBore=cyl(4.28,14.90,25.55,1.26,5,Y)
 annulus=cyl(2.77,4.98,17.30,8,5,X).cut(housingBore)
 axial_seat=cyl(4.28,.46,25.55,1.24,5,Y)
 beamOriginal=one(beam.multiFuse([portFill,annulus,axial_seat]).cut(cyl(guide_r,5.01,17.26,8,5,X)))
 smallAccess=cyl(2.38,1.90,25.55,-.10,5,Y)
 beamN=one(beamOriginal.cut(smallAccess))
 # Fill old slot before subtracting swept guide allowance. Guide relief is limited to
 # the locking end; the original pocket that receives the head is left intact.
 raw=one(oldCam.fuse(cyl(4.1,1.17,25.55,1.70,5,Y)))
 working=range(0,85,4)
 # Conservative 0.14 mm radial added relief on the thick section, plus tiny axial margin.
 new_sweep_seed=cyl(rod_r+.14,23.40+.12-21.19,21.19,8,5,X)
 sweep=[tx(new_sweep_seed,84-a) for a in working]
 cutter=sweep[0].multiFuse(sweep[1:]).removeSplitter()
 # Slot in LOCKED orientation is the rotation of the same previously tested
 # 4.50 x 1.18 drive profile, mirrored axially to the exposed rear face.
 slot=tx(bb(23.30,11.72,4.41,27.80,12.95,5.59),84)
 slotOpposite=tx(bb(23.30,1.65,4.41,27.80,2.88,5.59),84)
 camOriginal=one(raw.cut([cutter,slot]))
 cam=one(camOriginal.cut(slotOpposite))
 assert abs(C(slot,slotOpposite))<1.e-6
 assert abs(C(camOriginal,slotOpposite)-(camOriginal.Volume-cam.Volume))<.001
 assert abs(C(beamOriginal,smallAccess)-(beamOriginal.Volume-beamN.Volume))<.001
 # Slot floors at 2.88/11.72, and shaft material at center around both
 # floors. Verify continuous outer tangential ligaments in addition to nominal floor spacing.
 outerWeb=tx(cyl(.24,8.84,28.67,2.88,5,Y),84)
 assert C(cam,outerWeb)>.98*outerWeb.Volume, (C(cam,outerWeb),outerWeb.Volume)
 for y in (2.88,11.70):
   witness=tx(cyl(.24,.020,25.55,y,5,Y),84)
   assert C(cam,witness)>.99*witness.Volume,(y,C(cam,witness),witness.Volume)
 def R(d):return tx(cam,d-84)
 # Build a true companion blade and short hand handle for the shared service opening.
 # Original 4.08 x 0.86 flat tip is left at 0.20–0.25 clearance; the stem begins after the rotor face.
 tool=one(cyl(2.17,8.02,25.55,12.97,5,Y).multiFuse([
     bb(23.51,12.06,4.57,27.59,13.08,5.43),cyl(4.4,12,25.55,20.,5,Y)]))
 def T(d):return tx(tool,d)
 frontTool=one(cyl(2.17,8.02,25.55,1.63,5,-Y).multiFuse([
     bb(23.51,1.52,4.57,27.59,2.54,5.43),cyl(4.4,12,25.55,-5.40,5,-Y)]))
 def U(d):return tx(frontTool,d)
 # Old pad actual pivot is Y=23, Z=49.83. Add a fingertip lobe inboard, not on the teeth.
 padOriginal=one(pad.fuse(cyl(1.41,2.45,21.10,23,49.83,X)))
 def wing(x0,x1):
  points=[(x0,46.66),(x0,45.47),(x0+.28,45.15),(x1-1.40,45.15),(x1,46.55),(x1,46.66)]
  w=Part.makePolygon([V(x,22.1,z) for x,z in points+[points[0]]])
  return Part.Face(w).extrude(V(0,1.80,0))
 padN=one(padOriginal.multiFuse([wing(13.66,16.00),wing(19.80,21.90)]))
 padPivot=V(0,23,49.83)
 def P(d):return padN.rotated(padPivot,X,d)
 def O(d):return pad.rotated(padPivot,X,d)
 return dict(oldBase=S[0],oldBeam=S[1],base=base,beam=beamOriginal,lockedCam=camOriginal,openCam=tx(camOriginal,-84),rod=rod,
  mainTool=tool,oppositeTool=frontTool,originalPad=pad,newPad=padN)
