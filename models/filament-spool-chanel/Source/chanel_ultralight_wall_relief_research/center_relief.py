"""Experimental non-mating wall/floor relief. Retains nominal bore and outer paper envelopes.
This intentionally reduces bending/buckling/shaft-support stiffness; not mechanically approved.
"""
import cadquery as cq
DEFAULTS={'enabled':True,'wide_guide_wall':1.25,'narrow_guide_wall':1.1,'outer_column_wall':1.2,'floor_thickness':1.0,'bridge_keep_width':2.0,'wide_guide_z0':9.,'wide_guide_z1':21.5,'narrow_guide_z0':12.,'narrow_guide_z1':24.,'wide_column_z0':5.,'wide_column_z1':31.,'narrow_column_z0':5.,'narrow_column_z1':18.}
def apply_relief(s,part,p,h):
 if set(p)!=set(DEFAULTS):raise ValueError('Unknown/missing relief parameters')
 if not p['enabled']:return s
 if p['wide_guide_wall']<1.25 or p['narrow_guide_wall']<1.1 or p['outer_column_wall']<1.2 or p['floor_thickness']<1 or p['bridge_keep_width']<2:raise ValueError('Below research wall minima')
 gi=h[part+'_inner_tube_outer_radius'];oi=h[part+'_outer_tube_inner_radius'];oo=h[part+'_outer_tube_outer_radius'];bore=h['wide_bore_radius'] if part=='wide' else h['shaft_bore_radius'];target=bore+p[part+'_guide_wall']
 z0=p[part+'_guide_z0'];z1=p[part+'_guide_z1'];delta=gi+.05-target
 if delta<=0 or z1-z0<2*delta or z0<(9 if part=='wide' else 12) or z1>(21.5 if part=='wide' else 24):raise ValueError('Guide relief outside protected band')
 guide=cq.Workplane('XZ').polyline([(gi+.05,z0),(target,z0+delta),(target,z1-delta),(gi+.05,z1)]).close().revolve(360,(0,0),(0,1)).val()
 z0=p[part+'_column_z0'];z1=p[part+'_column_z1'];outer_target=oo-p['outer_column_wall'];delta=outer_target-(oi-.05)
 if z0<5 or z1>(31 if part=='wide' else 18) or delta<=0:raise ValueError('Column relief outside protected band')
 column=cq.Workplane('XZ').polyline([(oi-.05,z0),(outer_target,z0+delta),(outer_target,z1-delta),(oi-.05,z1)]).close().revolve(360,(0,0),(0,1)).val()
 floor=cq.Workplane('XY').circle(oi-.2).circle(gi+.2).extrude(h['support_top']-p['floor_thickness']+.02).translate((0,0,p['floor_thickness'])).val()
 # Exact original cardinal bridge roots stay untouched; generous mask exceeds 1.2mm original bridge.
 keeps=[cq.Workplane('XY').box(oo+2,p['bridge_keep_width'],45,centered=(False,True,False)).val().rotate((0,0,0),(0,0,1),a) for a in [0,90,180,270]]
 if part=='wide':keeps.append(cq.Workplane('XY').box(5,8,9,centered=(True,True,False)).translate((0,-41,0)).val())
 cutter=guide.fuse(column,floor).cut(*keeps)
 out=s.cut(cutter).clean()
 if not out.isValid() or len(out.Solids())!=1:raise ValueError('Relieved body invalid/disconnected')
 return out
