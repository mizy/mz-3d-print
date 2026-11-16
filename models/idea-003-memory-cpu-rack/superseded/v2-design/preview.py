#!/usr/bin/env python3
"""从 rack.scad 的参数生成等比正视图 + 侧剖视图 PNG（示意图/自检用，不是内核渲染）。

画法规则与 rack.scad 的模块一一对应：斜靠板 / 台面 / 分隔牙 / 挡边 / 蜂窝，
物件（内存、CPU）按参数画成半透明 ghost，用来核对落位与间隙。
用法: python3 preview.py [输出路径, 默认同目录 preview.png]
"""
import math, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from model import *   # 派生尺寸/重心与 check.py 共用一份，两边不会画歪

HERE = Path(__file__).resolve().parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / 'preview.png'

S = 3
BG, INK, GREY = (255, 255, 255), (38, 38, 38), (120, 120, 120)
PLATE, SLAB, BASE = (216, 221, 228), (176, 184, 196), (140, 148, 162)
RAM, CPU, FAINT = (70, 140, 225), (95, 185, 120), (205, 208, 214)
try:
    F = ImageFont.truetype('/System/Library/Fonts/PingFang.ttc', 17)
    Fs = ImageFont.truetype('/System/Library/Fonts/PingFang.ttc', 13)
except OSError:
    F = Fs = ImageFont.load_default()

def hexpts(cx, cz, r, squash=1.0):
    return [(cx + r * math.cos(a), cz + r * squash * math.sin(a)) for a in [k * math.pi / 3 for k in range(6)]]

# 画布：左正视图 / 右侧剖视图，共用同一条 z 基线
base_y = 70 + int(H) * S
f_ox = 60
s_ox = f_ox + int(W) * S + 90
canvas = Image.new('RGB', (s_ox + int(base_d) * S + 70, base_y + int(P['base_t']) * S + 112), BG)
d = ImageDraw.Draw(canvas)
FX = lambda x: f_ox + x * S
SZ = lambda z: base_y - z * S
SX = lambda y: s_ox + y * S

d.text((f_ox, 16), 'idea-003 内存条+CPU 展示架 v2 · 后仰斜靠式，正面朝外（等比示意 %d px/mm）' % S, font=F, fill=INK)
d.text((f_ox, 42), '外廓 %.0f × %.0f × %.0f mm  一体打印 / 免支撑 / 斜面 %d° / 估重 %.0f g' % (W, base_d, H, round(math.degrees(tilt)), tot_kg * 1000), font=Fs, fill=GREY)

# ============ 正视图 ============
d.text((f_ox, SZ(wall_top_z) - 24), '正视图（观众侧）', font=F, fill=INK)
# 背板蜂窝：可见的顶排画实，其余画虚（被内存挡住）
hex_rows = int((P['wall_len'] - 2 * P['hex_zmargin']) // P['hex_pitch']) + 1
hex_x0 = (W - (P['hex_cols'] - 1) * P['hex_pitch']) / 2
for r in range(hex_rows):
    s = P['hex_zmargin'] + r * P['hex_pitch']
    z = wall_z0 + s * math.cos(tilt)
    cols = int(P['hex_cols']) if r % 2 == 0 else int(P['hex_cols']) - 1
    off = 0 if r % 2 == 0 else P['hex_pitch'] / 2
    for c in range(cols):
        x = hex_x0 + off + c * P['hex_pitch']
        pts = hexpts(FX(x), SZ(z), P['hex_r'] * S, math.cos(tilt))
        col = INK if z - P['hex_r'] > ram_top_z else FAINT
        d.polygon(pts, fill=BG, outline=col)
# 台面 / 底板轮廓
d.rectangle([FX(0), SZ(Zp), FX(W), SZ(Zp - P['plat_t'])], fill=SLAB, outline=INK)
d.rectangle([FX(0), SZ(0), FX(W), SZ(-P['base_t'])], fill=BASE, outline=INK)
# 分隔牙（每片是一根竖直细条，顶面随斜面）
for i in range(ram_tines):
    xc = i * (ram_cw + P['tine_t'])
    d.polygon([(FX(xc), SZ(Zp)), (FX(xc + P['tine_t']), SZ(Zp)), (FX(xc + P['tine_t']), SZ(Zp + P['ram_tine_h'] * math.cos(tilt))),
               (FX(xc), SZ(Zp + P['ram_tine_h'] * math.cos(tilt)))], fill=SLAB, outline=INK)
for i in range(cpu_tines):
    xc = cpu_row_x0 + i * (cpu_cw + P['tine_t'])
    d.polygon([(FX(xc), SZ(0)), (FX(xc + P['tine_t']), SZ(0)), (FX(xc + P['tine_t']), SZ(P['cpu_tine_h'] * math.cos(tilt))),
               (FX(xc), SZ(P['cpu_tine_h'] * math.cos(tilt)))], fill=SLAB, outline=INK)
# 物件 ghost
for i in range(ram_n):
    xc = ram_slot_x(i)
    zb, zt = Zp + 0.5, ram_top_z
    d.rectangle([FX(xc - P['ram_w'] / 2), SZ(zt), FX(xc + P['ram_w'] / 2), SZ(zb)], outline=RAM, width=2)
    d.line([FX(xc - P['ram_w'] / 2 + 3), SZ(zt - 12), FX(xc + P['ram_w'] / 2 - 3), SZ(zt - 12)], fill=RAM, width=1)
    d.text((FX(xc - P['ram_w'] / 2 + 2), SZ(zt) + 4), 'RAM%d' % (i + 1), font=Fs, fill=RAM)
for i in range(cpu_n):
    xc = cpu_slot_x(i)
    zt = P['cpu_w'] * math.cos(tilt) + P['cpu_thick'] * math.sin(tilt)
    d.rectangle([FX(xc - P['cpu_w'] / 2), SZ(zt), FX(xc + P['cpu_w'] / 2), SZ(0)], outline=CPU, width=2)
    d.text((FX(xc - P['cpu_w'] / 2 + 2), SZ(zt) + 4), 'CPU%d' % (i + 1), font=Fs, fill=CPU)
d.text((f_ox, SZ(-P['base_t']) + 8), '内存 %d 根（%dmm 位）朝外 / CPU %d 颗（%dmm 位）朝外，前排低一级' % (ram_n, ram_cw, cpu_n, cpu_cw), font=Fs, fill=GREY)
d.text((f_ox, SZ(-P['base_t']) + 28), '总宽 %.0f mm；分隔牙 %d 片把每件框住，前缘挡边高 %.0f mm' % (W, ram_tines + cpu_tines, P['lip_h']), font=Fs, fill=GREY)

# ============ 侧剖视图 ============
d.text((s_ox, SZ(wall_top_z) - 24), '侧剖视图（左=观众）', font=F, fill=INK)
def quad(pts, fill, outline=INK):
    d.polygon([(SX(y), SZ(z)) for y, z in pts], fill=fill, outline=outline)

# 底板（正视图外再画一次完整矩形）
quad([(base_front, -P['base_t']), (base_back, -P['base_t']), (base_back, 0), (base_front, 0)], BASE)
# 名牌凹位
quad([(P['label_y'] - P['label_d'] / 2, -P['label_deep']), (P['label_y'] + P['label_d'] / 2, -P['label_deep']),
      (P['label_y'] + P['label_d'] / 2, 0), (P['label_y'] - P['label_d'] / 2, 0)], BASE, GREY)
# 背板
fy, fz = wall_y0, wall_z0
quad([(fy, fz), (fy + up(P['wall_len'])[0], fz + up(P['wall_len'])[1]),
      (fy + up(P['wall_len'])[0] + P['plate_t'] * math.cos(tilt), fz + up(P['wall_len'])[1] - P['plate_t'] * math.sin(tilt)),
      (fy + P['plate_t'] * math.cos(tilt), fz - P['plate_t'] * math.sin(tilt))], PLATE)
# 台面
quad([(plat_y0, Zp - P['plat_t']), (plat_y0 + plat_d, Zp - P['plat_t']), (plat_y0 + plat_d, Zp), (plat_y0, Zp)], SLAB)
# CPU 斜靠板
quad([(cpu_plate_y0, cpu_plate_z0), (cpu_plate_y0 + up(cpu_plate_len)[0], cpu_plate_z0 + up(cpu_plate_len)[1]),
      (cpu_plate_y0 + up(cpu_plate_len)[0] + P['plate_t'] * math.cos(tilt), cpu_plate_z0 + up(cpu_plate_len)[1] - P['plate_t'] * math.sin(tilt)),
      (cpu_plate_y0 + P['plate_t'] * math.cos(tilt), cpu_plate_z0 - P['plate_t'] * math.sin(tilt))], PLATE)
# 内存挡边 / CPU 挡边
for y0, z0 in [(plat_y0, Zp), (cpu_plate_y0 + fwd(P['cpu_thick'] + P['lip_gap'] + P['lip_t'])[0], 0)]:
    quad([(y0, z0), (y0 + up(P['lip_h'])[0], z0 + up(P['lip_h'])[1]),
          (y0 + up(P['lip_h'])[0] + P['lip_t'] * math.cos(tilt), z0 + up(P['lip_h'])[1] - P['lip_t'] * math.sin(tilt)),
          (y0 + P['lip_t'] * math.cos(tilt), z0 - P['lip_t'] * math.sin(tilt))], SLAB)
# 分隔牙（剖面在旁边 24.5mm，用浅色表示）
dy = ram_slot_x(0) + ram_cw / 2 + 1.5
quad([(wall_y_at_Zp, Zp), (wall_y_at_Zp + fwd(P['ram_tine_d'])[0], Zp + fwd(P['ram_tine_d'])[1]),
      (wall_y_at_Zp + fwd(P['ram_tine_d'])[0], Zp + fwd(P['ram_tine_d'])[1] + P['ram_tine_h'] * math.cos(tilt)),
      (wall_y_at_Zp, Zp + P['ram_tine_h'] * math.cos(tilt))], (238, 240, 243), (170, 174, 182))
# 物件 ghost：内存（底面后角坐在台面上、背靠背板）/ CPU（底面后角坐底板、背靠 CPU 板）
def lean_ghost(depth, length, y_butt, z_butt, color, label, dash_z=10):
    p0 = (y_butt, z_butt)
    p1 = (y_butt + fwd(depth)[0], z_butt + fwd(depth)[1])
    p2 = (p1[0] + up(length)[0], p1[1] + up(length)[1])
    p3 = (p0[0] + up(length)[0], p0[1] + up(length)[1])
    quad([p0, p1, p2, p3], None, color)
    d.polygon([(SX(y), SZ(z)) for y, z in [p0, p1, p2, p3]], outline=color, width=2)
    if dash_z:  # 金手指那一段（离底面 10mm 内、两侧大面上）
        for t in (0.03, 0.07):
            a = (p0[0] + t * (p3[0] - p0[0]), p0[1] + t * (p3[1] - p0[1]))
            b = (p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]))
            d.line([SX(a[0]), SZ(a[1]), SX(b[0]), SZ(b[1])], fill=color, width=1)
    d.text((SX(p3[0]) + 4, SZ(p3[1])), label, font=Fs, fill=color)

lean_ghost(P['ram_thick'], P['ram_len'], wall_y_at_Zp, Zp, RAM, '内存：竖着斜靠，标签面朝外')
lean_ghost(P['cpu_thick'], P['cpu_w'], cpu_plate_front_y(0), 0, CPU, 'CPU：IHS 面朝外')
d.text((s_ox, SZ(-P['base_t']) + 8), '后排内存坐在 %.0fmm 高的台面上，前排 CPU 坐底板 —— 错开一级省宽度' % Zp, font=Fs, fill=GREY)
d.text((s_ox, SZ(-P['base_t']) + 28), '斜面 %d°，靠重力贴板；底面后角落在板面上，前缘挡边防滑' % round(math.degrees(tilt)), font=Fs, fill=GREY)

# ---- 受力标注：重心投影 / 前后棱 / 坐角 ----
RED = (198, 60, 60)
d.line([SX(com_y), SZ(com_z), SX(com_y), SZ(-P['base_t'])], fill=RED, width=1)
for zz in range(int(SZ(-P['base_t'])), int(SZ(com_z)), 8):
    d.line([SX(com_y) - 3, zz, SX(com_y) + 3, zz], fill=RED, width=1)
d.ellipse([SX(com_y) - 5, SZ(com_z) - 5, SX(com_y) + 5, SZ(com_z) + 5], outline=RED, width=2)
d.line([SX(com_y) - 9, SZ(com_z), SX(com_y) + 9, SZ(com_z)], fill=RED, width=2)
d.line([SX(com_y), SZ(com_z) - 9, SX(com_y), SZ(com_z) + 9], fill=RED, width=2)
d.text((SX(com_y) + 8, SZ(com_z) - 8), '重心（估重 %.0f g）' % (tot_kg * 1000), font=Fs, fill=RED)
d.text((SX(com_y) + 8, SZ(com_z) + 8), '离前缘 %.0f / 离后缘 %.0f mm' % (com_y - base_front, base_back - com_y), font=Fs, fill=RED)
for ey, name in [(base_front, '底板前缘'), (base_back, '底板后缘')]:
    d.line([SX(ey), SZ(0), SX(ey), SZ(-P['base_t'] - 14)], fill=RED, width=2)
    d.text((SX(ey) - 18, SZ(-P['base_t'] - 30)), name, font=Fs, fill=RED)
# 坐角：内存底棱 + CPU 底棱，圈一下并说明重力把它压进角里
for by, bz in [(wall_y_at_Zp, Zp), (cpu_plate_front_y(0), 0)]:
    d.ellipse([SX(by) - 7, SZ(bz) - 7, SX(by) + 7, SZ(bz) + 7], outline=RED, width=2)
d.text((SX(wall_y_at_Zp) + 6, SZ(Zp) + 6), '坐进直角角里：面贴板 + 棱压台面', font=Fs, fill=RED)
d.text((s_ox, SZ(-P['base_t']) + 50), '受力：重力→台面/底板受压；后仰的水平推力→靠板根部→底板受剪，全回到同一块底板',
       font=Fs, fill=RED)
d.text((s_ox, SZ(-P['base_t']) + 68), '倾覆门槛：前推 %.2f N（≈%.0f 克力）/ 后推 %.2f N / 侧推 %.2f N'
       % (tip_front_N, tip_front_N / 9.8 * 1000, tip_back_N, tip_side_N), font=Fs, fill=RED)

canvas.save(OUT)
print('已输出 %s (%dx%d)' % (OUT, canvas.size[0], canvas.size[1]))
print('侧剖视：内存底棱 (y=%.2f, z=%.0f)，CPU 底棱 (y=%.2f, z=0)，底板 Y %.0f..%.1f，重心 (y=%.1f, z=%.1f)'
      % (wall_y_at_Zp, Zp, cpu_plate_front_y(0), base_front, base_back, com_y, com_z))
