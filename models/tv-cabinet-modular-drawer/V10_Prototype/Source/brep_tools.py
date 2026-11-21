#!/usr/bin/env python3
# Editable BREP generator. Run with a Python interpreter that can import FreeCAD + Part.
import argparse, json, math
from pathlib import Path
import FreeCAD as App, Part
try: import Import
except ImportError: Import=None
V=App.Vector

def box(x,y,z,a,b,c):
    return Part.makeBox(a,b,c,V(x,y,z))
def cyl(x,y,z,r,h,axis=(0,0,1)):
    return Part.makeCylinder(r,h,V(x,y,z),V(*axis))
def union(seq):
    seq=list(seq)
    return (seq[0].multiFuse(seq[1:]) if len(seq)>1 else seq[0]).removeSplitter()
def sub(s, seq):
    seq=list(seq)
    for cutter in seq:s=s.cut(cutter)
    return s.removeSplitter() if seq else s
def prism(points, d):
    q=[V(*p) for p in points]
    return Part.Face(Part.makePolygon(q+[q[0]])).extrude(V(*d))
def rounded(x,y,z,w,d,h,r):
    # Rounded rectangle, along +Z; exact circular edges.
    a,b=x+w,y+d
    p=lambda xx,yy: V(xx,yy,z)
    s=math.sqrt(.5)
    A,B,C,D,E,F,G,H=[p(*q) for q in [(x+r,y),(a-r,y),(a,y+r),(a,b-r),(a-r,b),(x+r,b),(x,b-r),(x,y+r)]]
    mid=[p(a-r+r*s,y+r-r*s),p(a-r+r*s,b-r+r*s),p(x+r-r*s,b-r+r*s),p(x+r-r*s,y+r-r*s)]
    e=[Part.makeLine(A,B),Part.Arc(B,mid[0],C).toShape(),Part.makeLine(C,D),Part.Arc(D,mid[1],E).toShape(),
       Part.makeLine(E,F),Part.Arc(F,mid[2],G).toShape(),Part.makeLine(G,H),Part.Arc(H,mid[3],A).toShape()]
    return Part.Face(Part.Wire(e)).extrude(V(0,0,h))
def slot_x(x,yy,zz,L,H,length,r=3.5):
    s=rounded(yy-L/2,zz-H/2,0,L,H,length,r)
    s.rotate(V(0,0,0),V(1,1,1),120)  # XY rectangle becomes YZ opening, Z extrusion -> X
    s.translate(V(x,0,0))
    return s
def mirror(s,W):
    return s.mirror(V(W/2,0,0),V(1,0,0))
def move(s,x=0,y=0,z=0):
    a=s.copy(); a.translate(V(x,y,z)); return a
def web_yz(x,a,z1,b,z2,t,sx):
    dy,dz=b-a,z2-z1
    s=math.hypot(dy,dz)
    uy,uz=-dz*t/2/s,dy*t/2/s
    return prism([(x,a+uy,z1+uz),(x,b+uy,z2+uz),(x,b-uy,z2-uz),(x,a-uy,z1-uz)],(sx,0,0))
def web_xz(y,a,z1,b,z2,t,sy):
    dx,dz=b-a,z2-z1
    s=math.hypot(dx,dz); ux,uz=-dz*t/2/s,dx*t/2/s
    return prism([(a+ux,y,z1+uz),(b+ux,y,z2+uz),(b-ux,y,z2-uz),(a-ux,y,z1-uz)],(0,sy,0))

