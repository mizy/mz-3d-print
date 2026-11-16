LV 30mm bowl, two-row original-vector FULL-SIDES edition — 2026-11-16

This is an actual CAD model with engraved geometry, not the flat design illustration.
Original third-party AI curves were converted directly to cubic Bezier CAD edges, retaining holes and islands. New two-row placement is intentionally NOT the original complete repeat tile. Front has 12 motifs (four types x3), 7mm tall; both sides now have 16 motifs plus 4 curved-transition motifs, 32 total. Curved front foreshortens symbols near edges versus flat design. Engravings are same-color cavities, not dark-colored inserts.

SIZE: nominal bowl footprint 160x145mm; bowl height 30mm; base4mm; wall3.2mm; nominal tangent engraving0.8mm (slightly shallower at symbol edges), approx2.4mm remaining wall. Integrated inverted-T tongue70x30x8.5mm; broad bar lies Z0 on build plate. Gap behind bowl3mm is provisional, not measured. Neck18mm, barheight8.5mm, attachment proportions also assumptions. Full bowl including clip bounds160x156.5x30mm.

PRINT: use parts/whole_bowl_AMS.stl for intact main bowl with height-based changes: ivory0-2mm, blue2-28mm, ivory28-30mm. Clip follows those same colors. Alternatively load three band STLs as one multipart object at original coordinates, NOT separate auto-arranged items. Print ivory_logo_print_flat.stl separately and glue. Do NOT print both assembly and duplicate constituent files. ivory_glue_logo is in assembly coordinates, not print orientation. Logo18mm high,2.5mm thick; flat back with nominal0.1mm central gap, larger side gaps against curved bowl; glue attachment not mechanically tested.

Seven STEP/STL pairs checked: valid single solids, closed positive-volume single-component meshes, zero degenerate faces. Band overlap0 and summed CAD volume matches whole within 0.000001mm3. True curves retained in STEP; STL necessarily tessellated0.02mm tolerance.

NOT YET VERIFIED: physical mating/locking/load, feeder dimensions, slicing on user's nozzle/profile, food contact/leak resistance. No ready-to-run printer Gcode included. A no-support orientation is intended, not yet slicer-certified. Thin pointed tips approach zero width; 7mm motifs have roughly0.8-1mm center features. Do not silently thicken curves to claim accuracy. Before full printing, a small engraved test patch is recommended (not included as a separate file); the clip fit coupon is included. Clip coupon included tests tongue envelope but not the complete installed root/gap.

PLA100%solid geometric equivalent at1.24g/cm3: bowl including clip171.21g + one logo0.40g =171.61g. Not a sliced consumption prediction; excludes support, purge, brim and samples.

SOURCE: https://www.titanui.com/35302-simple-louis-vuitton-logo-pattern-vector/ . Third-party/sccnn aggregation, NOT official LV vector. Personal-use claim on site is not independently verified authorization from the rights holder. No commercial rights claim.

REBUILD: Python3 with cadquery, svgpathtools, PyMuPDF and shapely; run lv/build.py from any cwd. lv/source.ai is the unmodified downloaded source. Blender render.py imports actual exported STLs. Source, original curves and prior releases kept intact.
