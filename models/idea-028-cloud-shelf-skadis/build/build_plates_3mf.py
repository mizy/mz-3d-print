#!/usr/bin/env python3
"""Build the 4-plate Bambu Studio project for the cloud shelf.

Input : ../model/plate-stl/0N-*.stl  (one merged mesh per colour)
Output: ../3mf/cloud-shelf-skadis-4plates.3mf

Each plate holds exactly one printed colour.  Plate order mirrors the real
print: 1 cream PETG main body, 2 grey PETG panels, 3 white PETG clouds,
4 yellow PLA arc/stars/moon.  The merged plate meshes are split back into
individual parts so every piece can be moved in Bambu Studio; the original
layout inside each plate is preserved.

Bambu separates virtual plates by 308 mm in X; plate membership itself is
declared in Metadata/model_settings.config.

Usage: python3 build_plates_3mf.py
"""
from __future__ import annotations

import json
import uuid
import zipfile
from pathlib import Path

import trimesh

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PLATE_STL = ROOT / "model" / "plate-stl"
OUT = ROOT / "3mf" / "cloud-shelf-skadis-4plates.3mf"
TEMPLATE = HERE / "template-project_settings.json"

PLATE_STEP = 307.2   # Bambu virtual plate pitch (bed + gap)
PLATE_COLS = 2        # Bambu lays virtual plates out 3 per row
BED_CENTER = 128.0

PLATES = [
    {
        "plate": 1,
        "stl": "01-主体.stl",
        "name": "01 主体 · 奶油白 PETG",
        "extruder": 1,
        "parts": ["cloud-shelf-main"],
    },
    {
        "plate": 2,
        "stl": "02-背板+前挡板.stl",
        "name": "02 背板+前挡板 · 灰 PETG",
        "extruder": 2,
        "parts": ["back-panel", "front-panel"],
    },
    {
        "plate": 3,
        "stl": "03-云朵x2.stl",
        "name": "03 云朵×2 · 白 PETG",
        "extruder": 1,
        "parts": ["cloud-a", "cloud-b"],
    },
    {
        "plate": 4,
        "stl": "04-拱条+星月.stl",
        "name": "04 拱条+星月 · 黄 PLA",
        "extruder": 3,
        "parts": ["rainbow-arc", "moon", "star-large", "star-medium", "star-small"],
    },
]

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
 <Default Extension="png" ContentType="image/png"/>
</Types>
"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
"""

MODEL_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
{rels}
</Relationships>
"""


def clean_json(d: dict) -> dict:
    """Trim the 8-filament template down to our 3 filaments."""
    out = {}
    for key, value in d.items():
        if isinstance(value, list):
            if len(value) == 16:          # 8 filaments × 2 nozzle variants
                value = value[:6]
            elif len(value) == 8:         # per filament
                value = value[:3]
        out[key] = value

    # 3×3 flush matrix (diagonal zero)
    out["flush_volumes_matrix"] = [
        "0", "300", "300",
        "300", "0", "300",
        "300", "300", "0",
    ]
    out["filament_self_index"] = ["1", "2", "3"]
    out["filament_nozzle_map"] = ["0", "0", "0"]

    out["filament_colour"] = ["#FABBCB", "#898989", "#F7D117"]
    out["filament_type"] = ["PETG", "PETG", "PLA"]
    out["filament_settings_id"] = [
        "Bambu PETG Matte @BBL P1S 0.4 nozzle",
        "Generic PETG @BBL P1S 0.4 nozzle",
        "Bambu PLA Basic @BBL P1S 0.4 nozzle",
    ]
    out["filament_ids"] = ["GFG03", "GFG99", "GFA00"]
    out["filament_vendor"] = ["Bambu Lab", "Bambu Lab", "Bambu Lab"]
    out["filament_density"] = ["1.37", "1.37", "1.24"]
    out["filament_cost"] = ["17.99", "13.99", "17.99"]

    # PLA (filament 3) lives at variant indices 4,5 in 16-length arrays.
    out["nozzle_temperature"] = ["250", "250", "250", "250", "220", "220"]
    out["nozzle_temperature_initial_layer"] = ["245", "245", "245", "245", "220", "220"]
    out["filament_max_volumetric_speed"] = ["15", "15", "12", "12", "21", "21"]

    # Bed temperatures are per filament (3 entries).
    out["hot_plate_temp"] = ["70", "70", "60"]
    out["hot_plate_temp_initial_layer"] = ["70", "70", "60"]
    out["textured_plate_temp"] = ["70", "70", "60"]
    out["textured_plate_temp_initial_layer"] = ["70", "70", "60"]

    # One process for every plate: decorative 0.20 mm, 2 walls, 8% gyroid.
    out["print_settings_id"] = "0.20mm Standard @BBL P1S"
    out["layer_height"] = "0.2"
    out["initial_layer_print_height"] = "0.2"
    out["wall_loops"] = "2"
    out["sparse_infill_density"] = "8%"
    out["sparse_infill_pattern"] = "gyroid"
    out["enable_support"] = "1"
    out["support_type"] = "tree(auto)"
    out["support_threshold_angle"] = "20"
    out["support_interface_top_layers"] = "3"
    out["support_interface_spacing"] = "0.2"
    out["support_filament"] = "0"
    out["support_interface_filament"] = "0"
    out["print_sequence"] = "by layer"
    out["enable_prime_tower"] = "0"
    out["brim_type"] = "outer_only"
    out["brim_width"] = "5"
    return out


def mesh_xml(vertices, faces, object_id: int = 1, object_uuid: str | None = None) -> str:
    v = "\n".join(
        f'     <vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>'
        for x, y, z in vertices
    )
    f = "\n".join(
        f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in faces
    )
    uuid_attr = f' p:UUID="{object_uuid}"' if object_uuid else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
        'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
        'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" '
        'requiredextensions="p">\n'
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
        " <resources>\n"
        f'  <object id="{object_id}"{uuid_attr} type="model">\n'
        "   <mesh>\n"
        "    <vertices>\n"
        f"{v}\n"
        "    </vertices>\n"
        "    <triangles>\n"
        f"{f}\n"
        "    </triangles>\n"
        "   </mesh>\n"
        "  </object>\n"
        " </resources>\n"
        " <build/>\n"
        "</model>\n"
    )


def main() -> None:
    objects = []
    object_rels = []
    model_objects = []
    build_items = []
    settings_objects = []
    settings_plates = []
    next_id = 1

    for spec in PLATES:
        plate_mesh = trimesh.load(PLATE_STL / spec["stl"], force="mesh")
        parts = plate_mesh.split(only_watertight=False)
        if len(parts) != len(spec["parts"]):
            raise RuntimeError(
                f"{spec['stl']}: expected {len(spec['parts'])} parts, got {len(parts)}"
            )

        # Keep the real print layout inside the plate; centre the whole group on the bed.
        cx = (plate_mesh.bounds[0][0] + plate_mesh.bounds[1][0]) / 2
        cy = (plate_mesh.bounds[0][1] + plate_mesh.bounds[1][1]) / 2
        min_z = plate_mesh.bounds[0][2]
        col = (spec["plate"] - 1) % PLATE_COLS
        row = (spec["plate"] - 1) // PLATE_COLS
        tx = BED_CENTER + col * PLATE_STEP
        ty = BED_CENTER - row * PLATE_STEP

        plate_object_ids = []
        for component, part_name in zip(parts, spec["parts"]):
            verts = component.vertices.copy()
            verts[:, 0] -= cx
            verts[:, 1] -= cy
            verts[:, 2] -= min_z
            faces = component.faces
            i = next_id
            next_id += 1
            plate_object_ids.append(i)

            xml_name = f"object_{i}.model"
            file_uuid = f"000{i:02d}0000-b206-40ff-9872-83e8017abed1"
            objects.append((xml_name, mesh_xml(verts, faces, i, file_uuid)))
            object_rels.append(
                f' <Relationship Target="/3D/Objects/{xml_name}" Id="rel-{i}" '
                'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
            )

            uid = f"000000{i:02d}-b206-40ff-9872-83e8017abed1"
            model_objects.append(
                f'  <object id="{i}" p:UUID="{uid}" type="model">\n'
                "   <components>\n"
                f'    <component p:path="/3D/Objects/{xml_name}" objectid="{i}" '
                f'p:UUID="000{i:02d}0000-b206-40ff-9872-83e8017abed1" '
                'transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
                "   </components>\n"
                "  </object>"
            )
            build_items.append(
                f'  <item objectid="{i}" p:UUID="{uid}" '
                f'transform="1 0 0 0 1 0 0 0 1 {tx:.2f} {ty:.2f} 0" printable="1"/>'
            )

            settings_objects.append(
                f'  <object id="{i}">\n'
                f'    <metadata key="name" value="{part_name}"/>\n'
                f'    <metadata key="extruder" value="{spec["extruder"]}"/>\n'
                f'    <metadata face_count="{len(faces)}"/>\n'
                f'    <part id="{i}" subtype="normal_part" uuid="{uuid.uuid4()}">\n'
                f'      <metadata key="name" value="{part_name}"/>\n'
                '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
                '      <mesh_stat face_count="%d" edges_fixed="0" degenerate_facets="0" '
                'facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n'
                "    </part>\n"
                "  </object>" % len(faces)
            )

        instances = "\n".join(
            "    <model_instance>\n"
            f'      <metadata key="object_id" value="{oid}"/>\n'
            '      <metadata key="instance_id" value="0"/>\n'
            f'      <metadata key="identify_id" value="{100 + oid}"/>\n'
            "    </model_instance>"
            for oid in plate_object_ids
        )
        settings_plates.append(
            "  <plate>\n"
            f'    <metadata key="plater_id" value="{spec["plate"]}"/>\n'
            f'    <metadata key="plater_name" value="{spec["name"]}"/>\n'
            '    <metadata key="locked" value="false"/>\n'
            '    <metadata key="filament_map_mode" value="Auto For Flush"/>\n'
            '    <metadata key="filament_maps" value="1 1 1"/>\n'
            '    <metadata key="filament_volume_maps" value="0 0 0"/>\n'
            '    <metadata key="gcode_file" value=""/>\n'
            + instances
            + "\n  </plate>"
        )

    model_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
        'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" '
        'requiredextensions="p">\n'
        ' <metadata name="Application">BambuStudio-02.09.01.70</metadata>\n'
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
        ' <metadata name="Title">云朵托架 SKADIS · 四色分盘</metadata>\n'
        ' <metadata name="Designer">苗白菜</metadata>\n'
        ' <metadata name="License">CC BY-NC-SA 4.0</metadata>\n'
        " <resources>\n"
        + "\n".join(model_objects)
        + "\n </resources>\n"
        " <build>\n"
        + "\n".join(build_items)
        + "\n </build>\n"
        "</model>\n"
    )

    settings_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<config>\n"
        + "\n".join(settings_objects)
        + "\n"
        + "\n".join(settings_plates)
        + "\n  <assemble>\n  </assemble>\n</config>\n"
    )

    project_settings = clean_json(json.loads(TEMPLATE.read_text()))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", ROOT_RELS)
        z.writestr("3D/3dmodel.model", model_xml)
        z.writestr("3D/_rels/3dmodel.model.rels", MODEL_RELS.format(rels="\n".join(object_rels)))
        for name, xml in objects:
            z.writestr(f"3D/Objects/{name}", xml)
        z.writestr("Metadata/model_settings.config", settings_xml)
        z.writestr(
            "Metadata/project_settings.config",
            json.dumps(project_settings, ensure_ascii=False, indent=1),
        )

    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
    for spec in PLATES:
        print(f"  plate {spec['plate']}: {spec['stl']} -> {spec['name']} (extruder {spec['extruder']})")


if __name__ == "__main__":
    main()
