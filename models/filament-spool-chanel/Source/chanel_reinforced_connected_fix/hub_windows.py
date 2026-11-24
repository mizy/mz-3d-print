"""Native windows with radial inclined roofs and thin conical supporting membranes.
Preserves uninterrupted inner guide tube; exterior sleeve support is intentionally reduced.
Not physically strength certified. Paper-core / filament snagging needs actual testing.
"""
import cadquery as cq,math
DEFAULTS={'enabled':True,'count':4,'phase_deg':45.,'width':38.,'corner_radius':2.,'radial_start':33.5,'radial_depth':14.,'wide_bottom':4.5,'wide_top':22.,'narrow_bottom':4.5,'narrow_top':19.5,'roof_angle_deg':50.,'web_vertical_thickness':1.1,'web_half_angle_deg':36.,'web_join_overlap':.2}
def apply_windows(s,part,p,hub=None):
 if set(p)!=set(DEFAULTS):raise ValueError('Missing/unknown window parameters')
 if not p['enabled']:return s
 if hub is None:
  from official_hub import DEFAULTS as hub
 angle=p['roof_angle_deg'];th=p['web_vertical_thickness'];half=p['web_half_angle_deg'];ov=p['web_join_overlap']
 if not 45<=angle<=55 or not .9<=th<=1.4 or not 34<=half<=38 or not .15<=ov<=.3:raise ValueError('Unsupported roof/membrane parameters')
 if p['count']!=4 or p['phase_deg']!=45.:raise ValueError('Windows must remain between four original cardinal bridges')
 if hub is not None:
  if p['radial_start']<hub[part+'_inner_tube_outer_radius']+.199999:raise ValueError('Window protection radius must track inner guide outer radius plus .2mm')
  if p['radial_start']>=hub[part+'_outer_tube_inner_radius']-.2:raise ValueError('Protection cylinder must remain inside outer sleeve cavity')
  limit=hub['wide_outer_tube_top']-5.7 if part=='wide' else hub['narrow_outer_shoulder_z']-3.7
  if p[part+'_top']>limit+1e-6 or p[part+'_bottom']<hub['support_top']+1.3:raise ValueError('Window violates upper-interface/root preservation margin')
  if p['radial_start']+p['radial_depth']<hub[part+'_outer_tube_outer_radius']+1:raise ValueError('Window cutter must cross outer wall')
 w=p['width'];r=p['corner_radius'];bottom=p[part+'_bottom'];top=p[part+'_top'];a=p['radial_start'];depth=p['radial_depth']
 if not 20<=w<=42 or not 1.5<=r<=3 or not 4<=bottom<top or top>(35 if part=='wide' else 22) or a<33.5 or a>35 or a+depth<42 or 2*r>=min(w,top-bottom):raise ValueError('Unsupported window geometry/functional exclusion')
 tool=cq.Workplane('YZ').center(0,(bottom+top)/2).rect(w,top-bottom).extrude(a+depth).edges('|X').fillet(r).val()
 tool=tool.cut(cq.Solid.makeCylinder(a,top-bottom+2,cq.Vector(0,0,bottom-1)))
 ro=hub[part+'_outer_tube_outer_radius'];ri=hub[part+'_inner_tube_outer_radius'];outer_inner=hub[part+'_outer_tube_inner_radius'];slope=math.tan(math.radians(angle))
 def roof_z(rad):return top-(ro-rad)*slope
 if roof_z(ri-ov)<hub['support_top']+.5:raise ValueError('Roof root too low for retained support region')
 if half<math.degrees(math.asin((w/2)/outer_inner))+1.:raise ValueError('Web sector must cover complete window inner edge')
 below=cq.Workplane('XZ').polyline([(ri-ov,bottom-.5),(ro+.5,bottom-.5),(ro+.5,roof_z(ro+.5)),(ri-ov,roof_z(ri-ov))]).close().revolve(360,(0,0),(0,1)).val()
 tool=tool.intersect(below)
 cuts=[tool.rotate((0,0,0),(0,0,1),p['phase_deg']+i*360/p['count']) for i in range(p['count'])]
 out=s.cut(*cuts).clean()
 cone=below.translate((0,0,th)).cut(below).intersect(cq.Solid.makeCylinder(outer_inner+.3,top+th+1))
 R=ro*2;ang=math.radians(half);wedge=cq.Workplane('XY').polyline([(0,0),(R*math.cos(ang),-R*math.sin(ang)),(R*math.cos(ang),R*math.sin(ang))]).close().extrude(top+th+1).val()
 segment=cone.intersect(wedge);webs=[segment.rotate((0,0,0),(0,0,1),p['phase_deg']+i*360/p['count']) for i in range(p['count'])]
 out=out.fuse(*webs).clean()
 if not out.isValid() or len(out.Solids())!=1:raise ValueError('Windowed solid invalid/disconnected')
 return out
