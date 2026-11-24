"""Tall staggered polygonal arch windows, native analytic BRep. No slicing."""
import cadquery as cq,math
DEFAULTS={'enabled':True,'count':8,'outer_phase_deg':0.,'inner_phase_deg':22.5,'half_angle_deg':10.,'bottom':5.5,'inner_bottom':6.,'wide_outer_top':36.,'narrow_outer_top':23.2,'inner_top':28.,'roof_angle_deg':50.,'bottom_corner':1.5,'wide_inner_wall':4.,'narrow_inner_wall':4.,'outer_wall':4.,'thick_top':19.5,'taper_top':22.5}
def revolved(pts):return cq.Workplane('XZ').polyline(pts).close().revolve(360,(0,0),(0,1)).val()
def arch_cut(ri,ro,bottom,top,halfangle,angle,corner):
 hw=ri*math.sin(math.radians(halfangle));rise=hw*math.tan(math.radians(angle))
 if top-bottom<=rise+corner+.5:raise ValueError('Not enough height for a tall arch')
 pts=[(-hw+corner,bottom),(hw-corner,bottom),(hw,bottom+corner),(hw,top-rise),(0,top),(-hw,top-rise),(-hw,bottom+corner)]
 tool=cq.Workplane('YZ').polyline(pts).close().extrude(ro+1).val()
 return tool.intersect(cq.Solid.makeCylinder(ro,60)).cut(cq.Solid.makeCylinder(ri,60))
def apply_windows(s,part,p,hub=None):
 if set(p)!=set(DEFAULTS):raise ValueError('Unknown/missing arch parameters')
 if not p['enabled']:return s
 if p['count']!=8 or not 0<p['half_angle_deg']<11.25:raise ValueError('8 staggered sectors must not overlap radially')
 if p['outer_phase_deg']!=0 or p['inner_phase_deg']!=22.5:raise ValueError('Keep validated stagger and marker positions')
 h=hub;zi=p['thick_top'];zt=p['taper_top'];z0=h['support_top'];bore=h['wide_bore_radius'] if part=='wide' else h['shaft_bore_radius']
 oi=h[part+'_inner_tube_outer_radius'];oo=h[part+'_outer_tube_inner_radius'];ro=h[part+'_outer_tube_outer_radius'];ni=bore+p[part+'_inner_wall'];no=ro-p['outer_wall']
 if not oi<ni<no<oo or zt>23 or ni-oi>zt-zi or oo-no>zt-zi:raise ValueError('Invalid thickening or taper')
 if p['inner_top']>28 or p[part+'_outer_top']>(36 if part=='wide' else 23.2):raise ValueError('Do not enter mating zones')
 ia=revolved([(oi-.05,z0),(ni,z0),(ni,zi),(oi,zt),(oi-.05,zt)])
 oa=revolved([(no,z0),(oo+.05,z0),(oo+.05,zt),(oo,zt),(no,zi)])
 out=s.fuse(ia,oa).clean()
 # Cut only one shell. The cardinal bridges retain their radial volume and
 # lower/upper attachment bands; no broad membrane obscures these tall windows.
 outer=arch_cut(no-.01,ro+.1,p['bottom'],p[part+'_outer_top'],p['half_angle_deg'],p['roof_angle_deg'],p['bottom_corner'])
 inner=arch_cut(bore-.01,ni+.02,p['inner_bottom'],p['inner_top'],p['half_angle_deg'],p['roof_angle_deg'],p['bottom_corner'])
 out=out.cut(*[outer.rotate((0,0,0),(0,0,1),i*45) for i in range(8)],*[inner.rotate((0,0,0),(0,0,1),22.5+i*45) for i in range(8)]).clean()
 if not out.isValid() or len(out.Solids())!=1:raise ValueError('Invalid/disconnected arch result')
 return out
