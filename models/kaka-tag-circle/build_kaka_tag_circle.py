"""Kaka tag v3: circular body (no bottom banner), front name removed, name engraved on back.

Source: the morning parametric version (55 x 81.8, circle + bottom banner).
Only the shape and the name move:
  * body clipped to the circle + hanging tab  -> no "chin"
  * front name removed (it lived on the banner, which is gone)
  * back name engraved 0.6 mm, mirrored, single colour
  * whole part scaled to 60 mm tall in XY (thickness untouched)
"""
import json
from pathlib import Path

import manifold3d
import numpy as np
import shapely
import trimesh
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from matplotlib.path import Path as MplPath
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

D = Path('/Users/mizy/projects/claude-agent-hub/outputs/dog-tag-kaka')
FONT = '/System/Library/Fonts/Hiragino Sans GB.ttc'
FONT_INDEX = 1
TEXT = '卡卡'
TEXT_W, TEXT_H = 24.0, 10.5
DEPTH = 0.6
EDGE = 0.9
STRIPES = ((1.5, 2.1), (2.7, 3.3))
TARGET_H = 60.0


def section(name, z):
    m = trimesh.load(D / f'parametric-{name}.stl')
    sec = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    flat, to3d = sec.to_planar()
    a, b = to3d[0, 0], to3d[0, 1]
    c, d = to3d[1, 0], to3d[1, 1]
    ox, oy = to3d[0, 3], to3d[1, 3]

    def lift(coords):
        return [(float(a * x + b * y + ox), float(c * x + d * y + oy)) for x, y in coords]

    polys = [Polygon(lift(p.exterior.coords), [lift(r.coords) for r in p.interiors])
             for p in flat.polygons_full]
    return unary_union(polys)


def glyph_polygons(text, font_path, index, target_w, target_h):
    tt = TTFont(font_path, fontNumber=index)
    glyphs = tt.getGlyphSet()
    cmap = tt.getBestCmap()
    pen = RecordingPen()
    x = 0.0
    for ch in text:
        g = glyphs[cmap[ord(ch)]]
        g.draw(TransformPen(pen, (1, 0, 0, 1, x, 0)))
        x += g.width
    verts, codes = [], []
    cur = None
    for op, args in pen.value:
        if op == 'moveTo':
            if cur is not None:
                codes.append(MplPath.CLOSEPOLY)
                verts.append(cur)
            cur = args[0]
            verts.append(cur)
            codes.append(MplPath.MOVETO)
        elif op == 'lineTo':
            verts.append(args[0])
            codes.append(MplPath.LINETO)
        elif op == 'qCurveTo':
            pts = list(args)
            start = verts[-1]
            offs, end = pts[:-1], pts[-1]
            for i, off in enumerate(offs):
                if end is None and i == len(offs) - 1:
                    end = ((offs[0][0] + offs[-1][0]) / 2, (offs[0][1] + offs[-1][1]) / 2)
                for t in (0.25, 0.5, 0.75):
                    mt = 1 - t
                    verts.append((mt * mt * start[0] + 2 * mt * t * off[0] + t * t * end[0],
                                  mt * mt * start[1] + 2 * mt * t * off[1] + t * t * end[1]))
                    codes.append(MplPath.LINETO)
                start = end
            verts.append(end)
            codes.append(MplPath.LINETO)
        elif op == 'curveTo':
            p1, p2, p3 = args
            start = verts[-1]
            for t in np.linspace(0.2, 1.0, 5):
                mt = 1 - t
                verts.append((mt ** 3 * start[0] + 3 * mt * mt * t * p1[0]
                              + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
                              mt ** 3 * start[1] + 3 * mt * mt * t * p1[1]
                              + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]))
                codes.append(MplPath.LINETO)
            start = p3
        elif op == 'closePath':
            verts.append((0, 0))
            codes.append(MplPath.CLOSEPOLY)
            cur = None
    if cur is not None:
        verts.append(cur)
        codes.append(MplPath.CLOSEPOLY)
    path = MplPath(verts, codes)
    rings = [Polygon(r) for r in path.to_polygons() if len(r) >= 3]
    geom = unary_union(rings)
    minx, miny, maxx, maxy = geom.bounds
    s = min(target_w / (maxx - minx), target_h / (maxy - miny))
    return shapely.affinity.scale(geom, s, s, origin='center')


def extrude(geom, z0, z1):
    rings = []
    for p in getattr(geom, 'geoms', [geom]):
        if p.geom_type != 'Polygon' or p.area < 0.02:
            continue
        rings.append([[float(x), float(y)] for x, y in p.exterior.coords])
        for r in p.interiors:
            rings.append([[float(x), float(y)] for x, y in r.coords])
    cs = manifold3d.CrossSection(rings, manifold3d.FillRule.EvenOdd)
    mesh = cs.extrude(z1 - z0).to_mesh()
    tri = trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3],
                          faces=np.asarray(mesh.tri_verts), process=True)
    tri.apply_translation([0, 0, z0])
    return tri


outline = section('white', 1.6)
outer = Polygon(outline.exterior, [r.coords for r in outline.interiors])
hole = Polygon(outline.interiors[0])
print('old bbox', [round(v, 1) for v in outline.bounds])

# circle body + the hanging tab above y=23
disk = Point(0.1, -3.6).buffer(27.4, resolution=256)
tab = outer.intersection(box(-40, 23, 40, 60))
shape = unary_union([disk, tab]).intersection(outer).buffer(0)
print('circle bbox', [round(v, 1) for v in shape.bounds])
new_outer = Polygon(shape.exterior)
new_hole = Polygon(shape.interiors[0])

edge = new_outer.difference(new_outer.buffer(-EDGE)).difference(new_hole.buffer(0.2))
stripes = []
for a, b in STRIPES:
    band = new_outer.buffer(-a).difference(new_outer.buffer(-b)).difference(new_hole.buffer(0.2))
    stripes.append(band)
stripes = unary_union(stripes).difference(edge)

gray_art = section('gray', 3.4)
black_art = section('black', 3.4)
inner = new_outer.buffer(-STRIPES[-1][1] - 0.02).difference(new_hole.buffer(0.2))
gray_art = gray_art.intersection(inner)
black_art = black_art.intersection(inner)

name_mesh = trimesh.load(D / 'name.stl')
nb = name_mesh.bounds
text_zone = box(nb[0, 0], nb[0, 1], nb[1, 0], nb[1, 1]).buffer(1.0)
gray_art = gray_art.difference(text_zone)
black_art = black_art.difference(text_zone)

gray_final = unary_union([gray_art, stripes]).difference(edge).difference(new_hole.buffer(0.2))
black_final = unary_union([black_art, edge]).difference(stripes).difference(new_hole.buffer(0.2))
print('gray area', round(gray_final.area, 1), 'black area', round(black_final.area, 1))

base = extrude(new_outer.difference(new_hole.buffer(0.05)), 0.0, 3.2)
gray_mesh = extrude(gray_final, 3.1, 3.7)
black_mesh = extrude(black_final, 3.1, 4.0)

# back name, mirrored so it reads correctly from the back
txt = glyph_polygons(TEXT, FONT, FONT_INDEX, TEXT_W, TEXT_H)
cx, cy = 0.1, -10.0
txt = shapely.affinity.translate(txt, cx - (txt.bounds[0] + txt.bounds[2]) / 2,
                                 cy - (txt.bounds[1] + txt.bounds[3]) / 2)
back_txt = shapely.affinity.scale(txt, xfact=-1, yfact=1, origin=(cx, cy))
cut = extrude(back_txt, -0.1, DEPTH)
base = trimesh.boolean.difference([base, cut], engine='manifold')

# scale XY so the whole tag is 60 mm tall; keep thickness and layer heights
ymin, ymax = base.bounds[0, 1], base.bounds[1, 1]
s = TARGET_H / (ymax - ymin)
meshes = {'white': base, 'gray': gray_mesh, 'black': black_mesh}
for m in meshes.values():
    m.vertices[:, :2] *= s
    m.vertices[:, 0] -= (m.bounds[0, 0] + m.bounds[1, 0]) / 2
    m.vertices[:, 1] -= (m.bounds[0, 1] + m.bounds[1, 1]) / 2

for k, m in meshes.items():
    m.export(D / f'kaka-circle-{k}.stl')
trimesh.util.concatenate(list(meshes.values())).export(D / 'kaka-circle.stl')

meta = {
    'front_name_removed': True,
    'body': 'circle + hanging tab (no bottom banner)',
    'scale_xy': round(s, 4),
    'size_mm': [round(float(meshes['white'].bounds[1, 0] - meshes['white'].bounds[0, 0]), 1),
                round(float(meshes['white'].bounds[1, 1] - meshes['white'].bounds[0, 1]), 1),
                round(float(meshes['white'].bounds[1, 2] - meshes['white'].bounds[0, 2]), 1)],
    'engrave_depth_mm': DEPTH,
    'watertight': {k: bool(m.is_watertight) for k, m in meshes.items()},
}
(D / 'kaka-circle.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2))
print(json.dumps(meta, ensure_ascii=False))
