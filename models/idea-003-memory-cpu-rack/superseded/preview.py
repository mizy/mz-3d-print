#!/usr/bin/env python3
"""从 rack.scad 的参数生成等比正视图 + 侧视图 PNG（示意/自检用，不是内核渲染）。

参数全部从 rack.scad 解析，画法规则与 rack.scad 的模块一一对应：
  前端  = Y0 侧；槽位 = fin_x(i)+fin_t .. fin_x(i+1)；蜂窝孔跳过被隔片挡住的位置。
用法: python3 preview.py [输出路径, 默认同目录 preview.png]
"""
import math, re, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SCAD = HERE / 'rack.scad'
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / 'preview.png'
src = SCAD.read_text()

def num(name):
    m = re.search(r'^\s*%s\s*=\s*([-0-9.]+)\s*;' % name, src, re.M)
    assert m, 'rack.scad 里找不到参数 %s' % name
    return float(m.group(1))

def count(name):
    return int(num(name))

ram_c, cpu_c = count('ram_count'), count('cpu_count')
ram_w, cpu_w = num('ram_slot_w'), num('cpu_slot_w')
fin_t, fin_d, fin_h, cham = num('fin_t'), num('fin_d'), num('fin_h'), num('fin_chamfer')
base_t, base_d, base_r = num('base_t'), num('base_d'), num('base_r')
back_t, back_h = num('back_t'), num('back_h')
hex_r, hpx, hpz = num('hex_r'), num('hex_pitch_x'), num('hex_pitch_z')
hex_cols, hex_zmargin = int(num('hex_cols')), num('hex_zmargin')
foot_d = num('foot_d')
fin_hex_r, fin_hex_y, fin_hex_z = num('fin_hex_r'), num('fin_hex_y'), num('fin_hex_z')

slots = [ram_w] * ram_c + [cpu_w] * cpu_c
n = len(slots)
fin_x = [i * fin_t + sum(slots[:i]) for i in range(n + 1)]
comb_w = (n + 1) * fin_t + sum(slots)
RAM_T, RAM_H, RAM_D = 8, 133.35, 42   # 带马甲内存：厚 8 / 高 133.35 / 进深 42（马甲高）
CPU_T, CPU_H, CPU_D = 5, 40, 40      # LGA 裸板：厚 5 / 40x40


# 背板蜂窝：偶数行 hex_cols 个，奇数行少一个并错半格，整排左右居中（与 rack.scad 同一套算式）
hexes = []
hex_x0 = (comb_w - (hex_cols - 1) * hpx) / 2
hex_rows = int((back_h - 2 * hex_zmargin) // hpz) + 1
for r in range(hex_rows):
    z = hex_zmargin + r * hpz
    cols = hex_cols if r % 2 == 0 else hex_cols - 1
    off = 0 if r % 2 == 0 else hpx / 2
    for c in range(cols):
        hexes.append((hex_x0 + off + c * hpx, z))

S = 4
BG, INK = (255, 255, 255), (40, 40, 40)
PANEL, FIN, BASE = (222, 226, 232), (176, 184, 196), (140, 148, 162)
RAM, CPU = (90, 150, 230), (110, 190, 130)
try:
    F = ImageFont.truetype('/System/Library/Fonts/PingFang.ttc', 17)
    Fs = ImageFont.truetype('/System/Library/Fonts/PingFang.ttc', 14)
except OSError:
    F = Fs = ImageFont.load_default()

H = int(back_h + base_t) * S
W = int(comb_w) * S
f_ox, s_ox = 60, 60 + W + 110
base_y = 60 + H          # z = 0 的像素行
canvas = Image.new('RGB', (s_ox + int(base_d) * S + 70, base_y + int(base_t) * S + 90), BG)
d = ImageDraw.Draw(canvas)
fx = lambda x: f_ox + x * S
fz = lambda z: base_y - z * S
sx = lambda y: s_ox + y * S

d.text((f_ox, 18), 'idea-003 内存条+CPU 展示架 · 竖直单排梳齿式（等比示意 %d px/mm）' % S, font=F, fill=INK)
d.text((f_ox, 44), '外廓 %.1f × %.1f × %.1f mm  单件打印 / 免支撑 / 免打墙' % (comb_w, base_d, back_h + base_t), font=Fs, fill=(90, 90, 90))

# ---- 正视图 ----
d.text((f_ox, fz(back_h) - 26), '正视图', font=F, fill=INK)
d.rectangle([fx(0), fz(back_h), fx(comb_w), fz(0)], fill=PANEL, outline=INK)
for hx, hz in hexes:
    pts = [(fx(hx + hex_r * math.cos(a)), fz(hz + hex_r * math.sin(a))) for a in [i * math.pi / 3 for i in range(6)]]
    d.polygon(pts, fill=BG)
for i in range(n + 1):
    d.rectangle([fx(fin_x[i]), fz(fin_h), fx(fin_x[i] + fin_t), fz(0)], fill=FIN, outline=INK)
    d.rectangle([fx(fin_x[i]), fz(fin_h), fx(fin_x[i] + fin_t), fz(fin_h - cham)], fill=(205, 210, 218), outline=INK)
    hx0 = fin_x[i] + fin_t / 2
    d.polygon([(fx(hx0 + fin_hex_r * math.cos(a)), fz(fin_hex_z + fin_hex_r * math.sin(a)))
               for a in [k * math.pi / 3 for k in range(6)]], fill=BG, outline=INK)
for i, w in enumerate(slots):
    cx = fin_x[i] + fin_t + w / 2
    if i < ram_c:
        d.rectangle([fx(cx - RAM_T / 2), fz(RAM_H), fx(cx + RAM_T / 2), fz(0)], outline=RAM, width=2)
    else:
        d.rectangle([fx(cx - CPU_T / 2), fz(CPU_H), fx(cx + CPU_T / 2), fz(0)], outline=CPU, width=2)
d.rectangle([fx(0), fz(0), fx(comb_w), fz(-base_t)], fill=BASE, outline=INK)
d.text((fx(0), fz(-base_t) + 8), '%d 槽：前 4 根内存（蓝, 高133） / 后 3 颗 CPU（绿, 高40）' % n, font=Fs, fill=(90, 90, 90))
d.text((fx(0), fz(-base_t) + 30), '总宽 %.1f mm' % comb_w, font=Fs, fill=(90, 90, 90))

# ---- 侧视图 ----
d.text((s_ox, fz(back_h) - 26), '侧视图（右为背板）', font=F, fill=INK)
d.polygon([(sx(0), fz(0)), (sx(fin_d), fz(0)), (sx(fin_d), fz(fin_h)),
           (sx(cham), fz(fin_h)), (sx(0), fz(fin_h - cham))], fill=FIN, outline=INK)
d.rectangle([sx(base_d - back_t), fz(back_h), sx(base_d), fz(0)], fill=PANEL, outline=INK)
d.rectangle([sx(0), fz(0), sx(base_d), fz(-base_t)], fill=BASE, outline=INK)
d.rectangle([sx(0), fz(RAM_H), sx(RAM_D), fz(0)], outline=RAM, width=2)
d.line([sx(0), fz(10), sx(42), fz(10)], fill=RAM, width=1)
d.rectangle([sx((base_d - fin_d) + 2), fz(CPU_H), sx(base_d - fin_d + 2 + CPU_D), fz(0)], outline=CPU, width=2)
d.text((sx(0), fz(-base_t) + 8), '底板进深 %.0f（重心靠后抗倒）' % base_d, font=Fs, fill=(90, 90, 90))
d.text((sx(0), fz(-base_t) + 30), '隔片高 %.0f / 斜切 %.0f / 槽深 %.0f' % (fin_h, cham, fin_d), font=Fs, fill=(90, 90, 90))
canvas.save(OUT)
print('已输出 %s  (%dx%d)' % (OUT, canvas.size[0], canvas.size[1]))
print('背板蜂窝孔 %d 个（%d 行）+ %d 片隔片各 1 个减重孔' % (len(hexes), hex_rows, n + 1))
print('蜂窝孔列 X: 偶数行 %s / 奇数行 %s' % (
    [round(hex_x0 + c * hpx, 2) for c in range(hex_cols)],
    [round(hex_x0 + hpx / 2 + c * hpx, 2) for c in range(hex_cols - 1)]))
print('蜂窝孔列 Z: %s ... %s' % (hex_zmargin, hex_zmargin + (hex_rows - 1) * hpz))
