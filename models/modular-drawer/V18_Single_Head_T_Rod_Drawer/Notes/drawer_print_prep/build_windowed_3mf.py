"""Build a windowed-drawer 3MF from drawer_windowed.stl with the same print settings.

The mesh is re-centred to the same print coordinates as the released project
(x/y centred on the plate, z=0 on the bed) before writing the 3MF.
"""

import json
import zipfile
from pathlib import Path

import trimesh

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC_3MF = ROOT / "Print" / "V18_H100_Single_Module_P1S_PETG_UNSLICED.3mf"
STL = HERE / "drawer_windowed.stl"
OUT = ROOT / "Print" / "V18_H100_Drawer_windowed_P1S_PETG.3mf"

mesh = trimesh.load(STL)
mesh.apply_translation([-mesh.bounds[0][0] - mesh.extents[0] / 2,
                        -mesh.bounds[0][1] - mesh.extents[1] / 2,
                        -mesh.bounds[0][2]])

verts = "\n".join(
    f'<vertex x="{v[0]:.6f}" y="{v[1]:.6f}" z="{v[2]:.6f}"/>' for v in mesh.vertices
)
tris = "\n".join(
    f'<triangle v1="{t[0]}" v2="{t[1]}" v3="{t[2]}"/>' for t in mesh.faces
)
OBJECT_MODEL = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
    'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
    'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">'
    f'<resources><object id="1" type="model"><mesh><vertices>{verts}</vertices>'
    f'<triangles>{tris}</triangles></mesh></object></resources><build/></model>'
)

CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
    '<Default Extension="config" ContentType="text/xml"/>'
    "</Types>"
)
ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
    'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
    "</Relationships>"
)
MODEL_RELS = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Target="/3D/Objects/object_1.model" Id="rel1" '
    'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
    "</Relationships>"
)
MODEL = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
    'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
    'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">'
    '<metadata name="Application">BambuStudio-02.09.01.70</metadata>'
    '<metadata name="BambuStudio:3mfVersion">1</metadata>'
    '<metadata name="Title">V18 H100 Drawer windowed - single part</metadata>'
    '<resources><object id="1" type="model" p:UUID="4214f26b-ef1a-4d8d-9214-1dfb6cb7a41f">'
    '<components><component p:path="/3D/Objects/object_1.model" objectid="1" '
    'p:UUID="29e43b37-be70-40a6-b8ba-11aaae9e939a"/></components></object></resources>'
    '<build><item objectid="1" p:UUID="4214f26b-ef1a-4d8d-9214-1dfb6cb7a41f" '
    'transform="1 0 0 0 1 0 0 0 1 128.0 128.0 0" printable="1"/></build></model>'
)
faces = len(mesh.faces)
MODEL_SETTINGS = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<config><object id="1"><metadata key="name" value="04_Drawer_windowed" />'
    f'<metadata face_count="{faces}" /><part id="1" subtype="normal_part">'
    '<metadata key="name" value="04_Drawer_windowed" />'
    '<metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1" />'
    f'<mesh_stat face_count="{faces}" edges_fixed="0" degenerate_facets="0" '
    'facets_removed="0" facets_reversed="0" backwards_edges="0" /></part></object>'
    '<plate><metadata key="plater_id" value="1" />'
    '<metadata key="plater_name" value="04 V18 DRAWER windowed" />'
    '<metadata key="locked" value="false" /><metadata key="gcode_file" value="" />'
    '<model_instance><metadata key="object_id" value="1" />'
    '<metadata key="instance_id" value="0" />'
    '<metadata key="identify_id" value="101" /></model_instance></plate>'
    '<assemble><assemble_item object_id="1" instance_id="0" '
    'transform="1 0 0 0 1 0 0 0 1 128.0 128.0 0" offset="0 0 0" />'
    '<assemble_item object_id="1" volume_id="0" transform="1 0 0 0 1 0 0 0 1 0 0 0" />'
    "</assemble></config>"
)

with zipfile.ZipFile(SRC_3MF) as src:
    settings = src.read("Metadata/project_settings.config")

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as out:
    out.writestr("[Content_Types].xml", CONTENT_TYPES)
    out.writestr("_rels/.rels", ROOT_RELS)
    out.writestr("3D/_rels/3dmodel.model.rels", MODEL_RELS)
    out.writestr("3D/3dmodel.model", MODEL)
    out.writestr("3D/Objects/object_1.model", OBJECT_MODEL)
    out.writestr("Metadata/model_settings.config", MODEL_SETTINGS)
    out.writestr("Metadata/project_settings.config", settings)

print(OUT)
print("faces", faces, "bbox", mesh.bounds.tolist())
