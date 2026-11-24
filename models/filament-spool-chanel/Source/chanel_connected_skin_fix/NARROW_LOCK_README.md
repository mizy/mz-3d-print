# Official narrow lock analytic reconstruction

Source: official Wiki narrow STL, SHA256 f02ad60233f9287a4396d55307e9bc30470eceb8c20366610cf27b5776a81ba6.
Coordinates are right-handed: x=sourceY, y=sourceZ, z=sourceX+33.70000076293945.

`narrow_lock.py` is standalone CadQuery source. It does not load a mesh, cached BRep, section point cloud, or sampled loft at runtime. Geometry uses revolved profiles, circular arcs, planar sector boundaries, a rounded 2D bump sketch, extrusion and a conical intersection. Runtime dimensional parameters are in DEFAULTS.

`build_narrow_lock(p)` returns a compound containing four main teeth and four small retention bumps. Fuse each solid to the parent inner tube. The 0.02mm overlap into the base radius is internal only, not an external fit allowance. The caller must use the same base outer radius, total height and radial/axial scales for both module and tube.

The four main-tooth side angles are -16,24.5 / 85,107.5 degrees and their +180 copies. Small bumps repeat at 0,83.1,180,263.1 degrees relative to the first bump; 83.1 is deliberately not 83.0. The latter discrepancy was found by independent boundary comparison and fixed. Bump boundary circular tangencies are fitted from source mesh vertices, not official dimension annotations. A nominal R1.2 blend is used after fitted circle radii 1.200003 and 1.200188.

Default validation: additions alone are eight valid solids, 72 faces. When joined with the analytic inner tube segment z30..34.1, the result is one valid solid, 53 faces, also valid after STEP roundtrip. Sixteen independent section heights spanning31.27..34.08 were compared against the official source mesh-plane boundary within r<32. The largest sampled/discrete boundary Hausdorff value is0.0111249011mm at z31.99. CAD curves were sampled at <=0.01mm nominal edge length spacing. Most other sections are below0.005mm. This is sampled cross-section evidence, not a continuous full-surface error bound, fitted manufacturing tolerance, or assembly/strength certification.

Four nondefault tests change scales, tooth radius, bump radius and sector angle independently. All produced valid eight-solid additions and changed volumes/bounds as appropriate. They do not validate every parameter combination or assembled fit.

Files: narrow_lock_validation.json, narrow_lock_parameter_tests.json, check_narrow_lock.py, test_narrow_lock_parameters.py. Intermediate probe and locate_error scripts/logs are research only. Final exports narrow_lock_with_pipe.step/.brep are a partial lock-with-tube research sample, not a complete spool deliverable.
