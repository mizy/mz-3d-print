"""Native rounded rectangular windows between four official bridges.
Preserves uninterrupted inner guide tube; exterior sleeve support is intentionally reduced.
Not physically strength certified. Paper-core / filament snagging needs actual testing.
"""
import cadquery as cq,math
DEFAULTS={'enabled':True,'count':4,'phase_deg':45.,'width':38.,'corner_radius':2.,'radial_start':33.5,'radial_depth':14.,'wide_bottom':4.5,'wide_top':22.,'narrow_bottom':4.5,'narrow_top':19.5}
def apply_windows(s,part,p,hub=None):
 if set(p)!=set(DEFAULTS):raise ValueError('Missing/unknown window parameters')
 if not p['enabled']:return s
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
 cuts=[tool.rotate((0,0,0),(0,0,1),p['phase_deg']+i*360/p['count']) for i in range(p['count'])]
 out=s.cut(*cuts).clean()
 if not out.isValid() or len(out.Solids())!=1:raise ValueError('Windowed solid invalid/disconnected')
 return out
