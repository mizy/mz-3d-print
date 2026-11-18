"""Official STL reverse-engineering work in progress.
Native central tubes, four bridges, locks and shallow marker grooves.
Must combine with official flange and separate locating key; validate complete output.
Coordinates: official wide z=33.7-X, narrow z=X+33.7; x=source Y; wide y=-source Z, narrow y=source Z (proper rotations).
"""
import cadquery as cq
import math
DEFAULTS={
 'hub_radial_scale':1.0,'hub_axial_scale':1.0,
 'shaft_bore_radius':27.5,'entry_chamfer':.8,
 'support_top':2.7,'bridge_width':1.2,
 'wide_bore_radius':31.4,'wide_inner_tube_outer_radius':33.3,
 'wide_transition_start':3.7,'wide_transition_fillet':1.5,
 'wide_inner_tube_top':37.25,'wide_inner_tube_outer_chamfer':.5,'wide_bridge_top':25.7,
 'wide_outer_tube_inner_radius':39.,'wide_outer_tube_outer_radius':40.85,
 'wide_outer_tube_top':40.7,'wide_outer_chamfer':1.1,
 'narrow_inner_tube_outer_radius':29.7,'narrow_inner_tube_top':34.1,
 'narrow_bridge_top':20.7,'narrow_outer_tube_inner_radius':37.7,
 'narrow_outer_tube_outer_radius':40.65,'narrow_outer_shoulder_z':25.7,
 'narrow_outer_shoulder_radius':39.65,'narrow_neck_radius':38.9,
 'narrow_neck_chamfer_z':27.1,'narrow_neck_top_radius':38.4,
 'narrow_outer_tube_top':27.9,
}
from narrow_lock import DEFAULTS as NARROW_LOCK_DEFAULTS
DEFAULTS.update(NARROW_LOCK_DEFAULTS)
from wide_lock import DEFAULTS as WIDE_LOCK_DEFAULTS
from wide_marker import DEFAULTS as WIDE_MARKER_DEFAULTS
DEFAULTS.update(WIDE_LOCK_DEFAULTS)
DEFAULTS.update(WIDE_MARKER_DEFAULTS)
IMPLEMENTATION_STATUS='TOLERANCE_BASED_COMPLETE_HUB_PENDING_FULL_ASSEMBLY_VALIDATION_KEY_IS_SEPARATE'
def _params(p):
 d=DEFAULTS.copy();d.update(p or {});return d

def _revolve(points,p):
 k=p['hub_radial_scale'];az=p['hub_axial_scale']
 return cq.Workplane('XZ').polyline([(r*k,z*az) for r,z in points]).close().revolve(360,(0,0),(0,1)).val()

def inner_tube(part,p=None):
 p=_params(p);k=p['hub_radial_scale'];az=p['hub_axial_scale'];r=p['shaft_bore_radius'];z0=p['support_top'];ro=p[part+'_inner_tube_outer_radius'];zt=p[part+'_inner_tube_top']
 if part=='narrow':
  c=p['entry_chamfer'];return _revolve([(r,z0),(ro,z0),(ro,zt),(r+c,zt),(r,zt-c)],p)
 ri=p['wide_bore_radius'];f=p['wide_transition_fillet'];zs=p['wide_transition_start']
 # 45 degree line tangent to circular meridional fillet, then vertical bore.
 zc=zs+(ri-r)+f*(math.sqrt(2)-1);rc=ri-f
 a=(rc+f/math.sqrt(2),zc-f/math.sqrt(2));mid=(rc+f*math.cos(math.pi/8),zc-f*math.sin(math.pi/8))
 # Anisotropic scaling turns the circular fillet into an ellipse. First build nominal then scale shape.
 wp=cq.Workplane('XZ').moveTo(r,z0).lineTo(r,zs).lineTo(*a).threePointArc(mid,(ri,zc)).lineTo(ri,zt).lineTo(ro,zt).lineTo(ro,z0).close()
 sh=wp.revolve(360,(0,0),(0,1)).val()
 if k==az:return sh.scale(k)
 return sh.transformGeometry(cq.Matrix([[k,0,0,0],[0,k,0,0],[0,0,az,0],[0,0,0,1]]))

def outer_tube(part,p=None):
 p=_params(p);z=p['support_top'];ri=p[part+'_outer_tube_inner_radius'];ro=p[part+'_outer_tube_outer_radius']
 if part=='wide':
  top=p['wide_outer_tube_top'];c=p['wide_outer_chamfer'];pts=[(ri,z),(ro,z),(ro,top-c),(ro-c,top),(ri,top)]
 else:
  top=p['narrow_outer_tube_top'];shoulder=p['narrow_outer_shoulder_z'];pts=[(ri,z),(ro,z),(ro,shoulder-1),(p['narrow_outer_shoulder_radius'],shoulder),(p['narrow_neck_radius'],shoulder),(p['narrow_neck_radius'],p['narrow_neck_chamfer_z']),(p['narrow_neck_top_radius'],top),(ri,top)]
 return _revolve(pts,p)

def bridges(part,p=None):
 p=_params(p);k=p['hub_radial_scale'];az=p['hub_axial_scale'];ri=p[part+'_inner_tube_outer_radius'];ro=p[part+'_outer_tube_inner_radius'];z=p['support_top'];h=p[part+'_bridge_top']-z
 return [cq.Workplane('XY').box((ro-ri+.02)*k,p['bridge_width']*k,h*az,centered=(True,True,False)).translate(((ri+ro)*k/2,0,z*az)).val().rotate((0,0,0),(0,0,1),a) for a in [0,90,180,270]]

def build_hub_base(part,p=None):
 """WIP base; intentionally not named build_hub to prevent accidental final integration."""
 if part not in ('wide','narrow'):raise ValueError(part)
 return inner_tube(part,p).fuse(outer_tube(part,p),*bridges(part,p)).clean()

def build_hub(part,p=None):
 q=_params(p)
 if part=='narrow':
  from narrow_lock import build_narrow_lock
  lock=build_narrow_lock(q)
  inside=inner_tube(part,q).fuse(*lock.Solids()).clean()
  return inside.fuse(outer_tube(part,q),*bridges(part,q)).clean()
 from wide_lock import build_wide_lock
 from wide_marker import build_wide_markers
 inside=inner_tube(part,q).fuse(build_wide_lock(q)).clean()
 ro=q['wide_inner_tube_outer_radius'];zt=q['wide_inner_tube_top'];c=q['wide_inner_tube_outer_chamfer']
 envelope=_revolve([(0,q['support_top']),(ro,q['support_top']),(ro,zt-c),(ro-c,zt),(0,zt)],q)
 inside=inside.intersect(envelope).cut(*build_wide_markers(q).Solids()).clean()
 return inside.fuse(outer_tube(part,q),*bridges(part,q)).clean()
