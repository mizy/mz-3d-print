# Independent rigid assembly check of the original official STL files

This check uses only the downloaded official STL meshes, not the reconstructed CAD. It therefore tests whether observed rigid interference was already present in the reference. The source hashes are recorded in the official source audit.

Right-handed normalization:
- wide:(sourceY,-sourceZ,33.70000076293945-sourceX)
- narrow:(sourceY,sourceZ,sourceX+33.70000076293945)
- assembly:narrow Rx180,then Rz(theta),then translateZ(H).

Method: intersect each mesh with horizontal planes; round intersection coordinates to8decimals only for planar connectivity; polygonize and classify material by ray-crossing parity. Transform narrow section polygons and compute2Dmaterial intersection area. Integrate using midpoint sections spanning the full shared axial range. All sampled cross-sections had closed degree2connectivity. No3Dmesh Boolean and no source modification were used.

| H mm | theta deg | <=0.1mm step volume mm³ | <=0.05mm step volume mm³ |
|---|---|---|---|
|66.4|0|0.364510|0.364201|
|66.4|3|4.200398|4.196764|
|66.4|8|0|0|
|66.4|48|0|0|
|70|45|2.503186|2.500324|
|70|48|0.477002|0.476036|
|70|50|0|0|
|68|45|0.115855|0.115203|
|68|48|0|0|

The independent reconstructed CAD reported H66.4 theta0/3/8 volumes0.368554/4.204519/0mm³, and H70 theta45 approximately2.497mm³. The official STL results are close and establish that these sampled rigid interferences are not unique to the reconstruction.

At H66.4 theta3, the maximum-area sampled section is z33.666863. Its four intersection components have centroid angles−26.2634,70.7094,153.7366,−109.2906degrees and radial extent approximately29.896..30.350mm. These locations correspond to the transformed narrow retention bumps and wide R29.9retaining edges.

Limits: midpoint integration and reference mesh tessellation are approximate. The difference between step sizes is convergence evidence, not a guaranteed error bound. Zero at sampled sections is not proof of zero interference along a continuous path. The result does not determine elastic deflection, fatigue, required torque, print tolerances, or physical assembly safety. It would be incorrect to claim that reference interference certifies a safe snap-fit.

Reproducible scripts and full section data:
- official_assembly_overlap.py/.json
- official_assembly_overlap_extra.py/.json
