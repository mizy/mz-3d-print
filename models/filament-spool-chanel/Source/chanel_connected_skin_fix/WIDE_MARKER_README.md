# Wide internal triangular marks: fitted native cutters

Official source wide STL SHA256 e5c88dcfd9b1c615925581b2165fbe3f970b17ea29b4cfc3810cd530e600c492.
Right-handed normalized coordinates (source Y, -source Z, 33.70000076293945-source X).

`wide_marker.py` creates two cutters at42 and222degrees. Parameters genuinely control bore radius, depth, bottom and apex heights, angular slope, bevel ratio, angular positions and radial/axial scale. No STL or sampled mesh is loaded at runtime.

The internal mark is not well described by a flat triangular prism: its sloped sides wrap around the bore. A small, smooth native loft provides the fitted wrapped-triangle ceiling; it is clipped by an exact R31.75 cylinder and a45degree cone beginning at z17.7/R31.4. This is a tolerance-based reconstruction with fitted shape parameters, not proof of the original feature recipe or an exact purely analytic-surface reconstruction. Default loft stations7per half; it does not recreate every mesh facet or generate a dense staircase of per-layer lofts.

`build_wide_markers(p)` returns two cutters. Use tube.cut(*cutters.Solids()). Default standalone tube cut and STEP roundtrip yielded one valid solid,12faces.

Independent actual STEP readback comparison of inner boundary with official mesh-plane sections:
- z17.75:0.0286008mm
- z18.00:0.0234944mm
- z18.50:0.0204635mm
- z19.00:0.0138567mm
- z20.00:0.0077963mm
- z21.00:0.0048740mm
- z21.70:0.0048245mm

This is sampled/discrete boundary Hausdorff comparison, not a global full-surface bound. The shallow lower-chamfer region has the largest deviation. Reference tessellation may contribute, but that contribution has not been separately quantified. No strength or physical fit claim is made.

Source: check_wide_marker.py; measurements:wide_marker_validation.json; nondefault tests:wide_marker_parameter_tests.json. Temporary wide_markers_with_pipe.step is a partial research sample, not a complete spool.
