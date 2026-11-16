"""Render front / back / back-oblique preview of the kaka back-name tag (pure software)."""
import sys
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw

sys.path.insert(0, '/Users/mizy/.cah-data/skills/shared/3d-print-ideas/scripts')
from cjk_font import load_cjk_font  # noqa: E402

D = Path('/Users/mizy/projects/claude-agent-hub/outputs/dog-tag-kaka')
OUT = D / 'kaka-circle-preview.png'
BG = (206, 212, 217)
COLORS = {
    'white': np.array([248, 248, 246], dtype=float),
    'gray': np.array([146, 148, 152], dtype=float),
    'black': np.array([30, 30, 34], dtype=float),
}
LIGHT = np.array([-0.52, 0.46, 0.86])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def groove_floor_mask(m):
    """Faces lying on the engraved floor (z ~= 0.6) inside the name area."""
    tris = m.vertices[m.faces]
    z = tris[:, :, 2]
    return ((np.abs(z.mean(axis=1) - 0.6) < 0.02)
            & (tris[:, :, 0].min(axis=1) > -12) & (tris[:, :, 0].max(axis=1) < 12)
            & (tris[:, :, 1].min(axis=1) > -39) & (tris[:, :, 1].max(axis=1) < -25))


def load_parts():
    parts = []
    for name in ('white', 'gray', 'black'):
        m = trimesh.load(D / f'kaka-circle-{name}.stl')
        color = np.repeat(COLORS[name][None, :], len(m.faces), axis=0)
        if name == 'white':
            color[groove_floor_mask(m)] *= 0.76
        parts.append((m, color))
    return parts


def view_basis(direction):
    direction = np.asarray(direction, dtype=float)
    direction = direction / np.linalg.norm(direction)
    f = -direction
    up = np.array([0.0, 1.0, 0.0]) if abs(f[2]) > 0.9 else np.array([0.0, 0.0, 1.0])
    r = np.cross(f, up)
    r = r / np.linalg.norm(r)
    u = np.cross(r, f)
    return r, u, -f


def render(parts, direction, size, focus=None, supersample=2):
    r, u, to_cam = view_basis(direction)
    tri_list, col_list = [], []
    for mesh, color in parts:
        v = mesh.vertices
        f = mesh.faces
        tri_list.append(v[f])
        col_list.append(np.repeat(color[None, :], len(f), axis=0)
                        if color.ndim == 1 else color[:len(f)])
    tris = np.concatenate(tri_list)
    cols = np.concatenate(col_list)

    v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
    normal = np.cross(v1 - v0, v2 - v0)
    ln = np.linalg.norm(normal, axis=1, keepdims=True)
    ln[ln == 0] = 1.0
    normal = normal / ln
    keep = normal @ to_cam > 0
    tris, cols, normal = tris[keep], cols[keep], normal[keep]

    X = tris @ r
    Y = tris @ u
    depth = tris @ (-to_cam)

    if focus is None:
        x0, x1, y0, y1 = X.min(), X.max(), Y.min(), Y.max()
    else:
        fx0, fy0, fx1, fy1 = focus
        corners = np.array([[x, y, z] for x in (fx0, fx1) for y in (fy0, fy1) for z in (0.0, 0.6)])
        cx, cy = corners @ r, corners @ u
        x0, x1, y0, y1 = cx.min(), cx.max(), cy.min(), cy.max()
        pad = 0.10 * max(x1 - x0, y1 - y0)
        x0, x1, y0, y1 = x0 - pad, x1 + pad, y0 - pad, y1 + pad

    W = size * supersample
    scale = (W - 24) / max(x1 - x0, y1 - y0)
    ox = W / 2 - (x0 + x1) / 2 * scale
    oy = W / 2 + (y0 + y1) / 2 * scale

    img = Image.new('RGB', (W, W), BG)
    draw = ImageDraw.Draw(img)

    nview = np.stack([normal @ r, normal @ u, normal @ to_cam], axis=1)
    shade = 0.70 + 0.30 * np.clip(nview @ LIGHT, 0.0, 1.0)
    rgb = np.clip(cols * shade[:, None], 0, 255).astype(np.uint8)

    order = np.argsort(depth.mean(axis=1))[::-1]
    px = X * scale + ox
    py = oy - Y * scale
    px_l, py_l = px.tolist(), py.tolist()
    rgb_l = rgb.tolist()
    for i in order.tolist():
        draw.polygon([(px_l[i][0], py_l[i][0]), (px_l[i][1], py_l[i][1]), (px_l[i][2], py_l[i][2])],
                     fill=tuple(rgb_l[i]))
    return img.resize((size, size), Image.LANCZOS)


def panel(size, title, sub):
    return Image.new('RGB', (size, size + 74), BG)


def label(img, title, sub, font_title, font_sub):
    d = ImageDraw.Draw(img)
    w = img.width
    d.text((w / 2, img.height - 62), title, font=font_title, fill=(40, 44, 50), anchor='mm')
    d.text((w / 2, img.height - 28), sub, font=font_sub, fill=(96, 104, 112), anchor='mm')


def main():
    parts = load_parts()
    size = 560
    front = render(parts, (0, 0, 1), size)
    white_only = parts[:1]  # from the back only the base is visible; keep the front art out
    back = render(white_only, (0, 0, -1), size)
    # focus on the bottom banner (name area) for the oblique depth shot
    back_obl = render(white_only, (-0.16, 0.10, -1.0), size, focus=(-11.5, -14.5, 11.5, -1.5))

    ft = load_cjk_font(30)
    fs = load_cjk_font(19)
    head = load_cjk_font(38)
    note = load_cjk_font(18)

    gap = 30
    W = size * 3 + gap * 2 + 80
    H = size + 74 + 150
    canvas = Image.new('RGB', (W, H), BG)
    for i, (im, t, s) in enumerate([
        (front, '正面 · 不再印名字', '纯圆盘 + 挂孔，狗头与包边保留'),
        (back, '背面 · 凹槽名字', '0.6 mm 深，从背面读是正的'),
        (back_obl, '背面斜视 · 凹槽细节', '槽壁有清晰台阶，单色即可打印'),
    ]):
        x = 40 + i * (size + gap)
        block = Image.new('RGB', (size, size + 74), BG)
        block.paste(im, (0, 0))
        label(block, t, s, ft, fs)
        canvas.paste(block, (x, 110))

    d = ImageDraw.Draw(canvas)
    d.text((40, 34), '卡卡吊牌 · 圆形版（直径 45.7 × 60 mm）', font=head, fill=(28, 32, 38))
    d.text((40, 80), '圆盘直径 45.7 · 去掉下方横幅 · 背面凹槽 0.6 mm，单色不换料', font=note,
           fill=(96, 104, 112))
    canvas.save(OUT)
    print('wrote', OUT, canvas.size)


if __name__ == '__main__':
    main()
