"""V18 style C, editable parametric planar window in one signed production tray.

FreeCAD 1.x Python:
  python3 build_c_front_window.py V18/Print_Parts/04_Drawer.step C_parameters.json OUT
The shape and checks use real analytic CAD faces, never a tessellated production STEP.
"""
from pathlib import Path
import hashlib,json,math,sys
import FreeCAD as App, Part, Import
V=App.Vector
SIGNED='4fab31b0c8a9abac78bae99e9d4ee4634a2a545abd49272ac800f2d9df6a380b'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bbox(s):
    b=s.optimalBoundingBox(False,False)
    return [round(getattr(b,k),6) for k in ('XMin','XMax','YMin','YMax','ZMin','ZMax')]
def build(seed: Path, config: Path, dest: Path):
    assert sha(seed)==SIGNED,'Exact signed V18 single drawer STEP required'
    d=json.loads(config.read_bytes())
    expected={'window_width_mm','window_height_mm','corner_radius_mm','window_center_z_mm'}
    assert set(d)==expected
    assert all(type(d[k]) in (int,float) and math.isfinite(d[k]) for k in expected)
    w,h,r,zc=(float(d[k]) for k in ('window_width_mm','window_height_mm','corner_radius_mm','window_center_z_mm'))
    X,Z=72.05,zc
    a,b=X-w*.5,X+w*.5
    c,f=Z-h*.5,Z+h*.5
    assert min(w,h)>0 and 1<=r<min(w,h)*.5,'Corner radius must be ≥1 and less than either half-size'
    assert 15<=a<b<=129.10,'Keep at least 15mm lateral structural band to unchanged body corner'
    assert 18<=c<f<=63,'Keep bottom sill and minimum 13.05mm below front pull-notch floor'
    old=Part.read(str(seed))
    assert old.isValid() and len(old.Solids)==1 and bbox(old)==[0,144.1,0,230,0,86]
    y0=-.8
    # XZ planar wire slides only in Y. The cutter stops before the open interior sidewall.
    q=r/math.sqrt(2)
    v=lambda x,z:V(x,y0,z)
    line=lambda p,q:Part.makeLine(v(*p),v(*q))
    arc=lambda p,q,s:Part.Arc(v(*p),v(*q),v(*s)).toShape()
    edges=[
        line((a+r,c),(b-r,c)),
        arc((b-r,c),(b-r+q,c+r-q),(b,c+r)),
        line((b,c+r),(b,f-r)),
        arc((b,f-r),(b-r+q,f-r+q),(b-r,f)),
        line((b-r,f),(a+r,f)),
        arc((a+r,f),(a+r-q,f-r+q),(a,f-r)),
        line((a,f-r),(a,c+r)),
        arc((a,c+r),(a+r-q,c+r-q),(a+r,c)),
    ]
    profile=Part.Face(Part.Wire(edges))
    tool=profile.extrude(V(0,4.1,0))
    new=old.cut(tool).removeSplitter()
    loss=old.Volume-new.Volume
    area=w*h-(4-math.pi)*r*r
    assert abs(profile.Area-area)<1e-6
    assert new.isValid() and len(new.Solids)==1 and bbox(new)==bbox(old)
    assert abs(loss-area*2.7)<.01,(loss,area)
    assert abs(tool.common(new).Volume)<.000001
    # Geometric proof of preserved fit: the only changed material is a subtractive window inside y=0..2.7.
    old_vs_new=old.cut(new)
    new_vs_old=new.cut(old)
    assert len(old_vs_new.Solids)==1 and abs(old_vs_new.Volume-loss)<.005
    assert new_vs_old.Volume<.000001
    region=bbox(old_vs_new)
    want=[a,b,0,2.7,c,f]
    assert max(abs(x-y) for x,y in zip(region,want))<.0005,(region,want)
    unit=(0,144.1,0,230,0,86)
    fronts=[x for x in new.Faces if type(x.Surface).__name__=='Plane' and abs(x.BoundBox.YMin)<1e-6 and abs(x.BoundBox.YMax)<1e-6]
    assert len(max(fronts,key=lambda x:x.Area).Wires)==2
    dest.mkdir(parents=True,exist_ok=True)
    out=dest/'C_Front_Picture_Window.step'
    doc=App.newDocument('V18_C_Front_Window')
    try:
        feature=doc.addObject('Part::Feature','C_Front_Picture_Window')
        feature.Label='V18 C front picture window'
        feature.Shape=new;doc.recompute();Import.export([feature],str(out))
    finally:App.closeDocument(doc.Name)
    raw=out.read_bytes()
    wrong=b'LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT($,.METRE.)'
    right=b'LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.)'
    if wrong in raw:
        assert right not in raw
        out.write_bytes(raw.replace(wrong,right))
    assert right in out.read_bytes()
    exact=Part.read(str(out))
    assert exact.isValid() and len(exact.Solids)==1 and bbox(exact)==list(unit)
    assert abs(new.Volume-exact.Volume)<.001
    assert exact.cut(new).Volume<.000001 and new.cut(exact).Volume<.000001
    result=dict(variant='V18 C Front Picture Window',seed_sha256=sha(seed),step=out.name,step_sha256=sha(out),
      unit='mm',valid_brep_solids=1,readback_bbox_XYZ_mm=[144.1,230,86],original_bbox_XYZ_mm=[144.1,230,86],
      exact_removed_region_Xmin_Xmax_Ymin_Ymax_Zmin_Zmax_mm=region,
      scheme='one XZ rounded rectangle, four analytic tangential arcs, tool spans full original wall; removal only',
      parameters=d,front_thickness_mm=2.7,notch_nominal_bottom_mm=76.05,
      notch_floor_to_window_top_nominal_mm=round(76.05-f,6),outer_side_reserve_each_mm=round(a,6),
      bottom_sill_nominal_height_mm=c,front_window_area_mm2=round(area,6),
      old_volume_mm3=round(old.Volume,6),new_volume_mm3=round(exact.Volume,6),
      material_volume_removed_mm3=round(loss,6),removed_CAD_volume_percentage=round(loss/old.Volume*100,6),
      added_material_mm3=0,open_to_inside=True,retained_nominal_envelope_and_interfaces_by_subtraction=True,
      no_slicing_or_physical_tests=True,separate_clear_lens_or_retention_not_included=True,
      note='No modification to grip, lower face, rails, interior fillets, sidewalls, back wall, or stopper. Long horizontal crown not assessed for bridging, no claim of support-free printing.')
    (dest/'C_CAD_Validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return exact,result
if __name__=='__main__':
    if len(sys.argv)!=4:raise SystemExit(__doc__)
    build(*(Path(x) for x in sys.argv[1:4]))
