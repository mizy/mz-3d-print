#!/usr/bin/env python3
"""从 rack.scad 的参数生成等比三视图 PNG（正视图 / 侧剖视图 / 俯视图）。

示意图/自检用，不是内核渲染：画法规则与 rack.scad 的模块一一对应
（斜靠板 / 台面 / 分隔牙 / 挡边 / 加强筋 / 蜂窝），物件（内存、CPU）按参数画成
半透明 ghost，用来核对上下两级落位、间隙、加强筋位置与重心。
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
PLATE, SLAB, BASE, RIB = (216, 221, 228), (176, 184, 196), (140, 148, 162), (232, 236, 240)
RAM, CPU, FAINT, RED = (70, 140, 225), (95, 185, 120), (208, 211, 217), (198, 60, 60)
ANIME = (150, 90, 180)
sys.path.insert(0, str(Path.home() / '.cah-data/skills/shared/3d-print-ideas/scripts'))
from cjk_font import load_cjk_font   # PingFang.ttc 在 macOS 上不存在，照抄会静默退成方框字体
F = load_cjk_font(18)
Fs = load_cjk_font(13)

hex_rows = int((P['wall_len'] - 2 * P['hex_zmargin']) // P['hex_pitch']) + 1
hex_x0 = (W - (P['hex_cols'] - 1) * P['hex_pitch']) / 2
s_plat0 = (Zp - P['plat_t'] - P['wall_z0']) / math.cos(tilt)
s_plat1 = (Zp - P['wall_z0']) / math.cos(tilt)
hex_kept = [(P['hex_zmargin'] + r * P['hex_pitch'], r)
            for r in range(hex_rows)
            if (P['hex_zmargin'] + r * P['hex_pitch'] + P['hex_r'] < s_plat0 - P['hex_skip']
                or P['hex_zmargin'] + r * P['hex_pitch'] - P['hex_r'] > s_plat1 + P['hex_skip'])]

# ---- 画布与各视图原点 ----
base_y = 74 + int(H) * S + 16                      # 正视图/侧剖视图共用的 Z=0 基线
f_ox = 62                                          # 正视图 X=0
s_ox = f_ox + int(W) * S + 92                      # 侧剖视图 Y=0
t_oy = base_y + 92 + base_back * S                 # 俯视图 Y=0（在正视图下方）
canvas = Image.new('RGB', (int(s_ox + base_back * S + 90), int(t_oy + 20 * S + 74)), BG)
d = ImageDraw.Draw(canvas)
FX = lambda x: f_ox + x * S
FZ = lambda z: base_y - z * S
SX = lambda y: s_ox + y * S
TX = lambda x: f_ox + x * S
TY = lambda y: t_oy - y * S

def box(*args, **kw):
    """按屏幕坐标画矩形，自动规整左上/右下顺序（可传 4 个数或一个列表）。"""
    px0, py0, px1, py1 = args[0] if len(args) == 1 else args
    d.rectangle([min(px0, px1), min(py0, py1), max(px0, px1), max(py0, py1)], **kw)

def hexpts(cx, cy, r, squash=1.0):
    return [(cx + r * math.cos(a), cy + r * squash * math.sin(a)) for a in [k * math.pi / 3 for k in range(6)]]

d.text((f_ox, 14), 'idea-003 内存条+CPU 展示架 v7 · 内存下层 / CPU 上层，正面朝外后仰斜靠（等比示意 %d px/mm）' % S, font=F, fill=INK)
d.text((f_ox, 40), '外廓 %.0f × %.0f × %.0f mm   一体打印 / 免支撑 / 斜面 %d° / 估重 %.0f g（满打）   '
       '内存 %d 根（%.0fmm 位）· CPU %d 颗（%.0f 位）' % (W, base_d, H, round(math.degrees(tilt)), tot_kg * 1000,
                                                          ram_n, ram_cw, cpu_n, cpu_cw), font=Fs, fill=GREY)

# ============================ 1) 正视图 ============================
d.text((f_ox, FZ(wall_top_z) - 30), '正视图（观众侧 · 透视叠加，物件画成轮廓）', font=F, fill=INK)
box([FX(0), FZ(wall_top_z), FX(W), FZ(wall_z0)], outline=INK)
for s, r in hex_kept:                                  # 背板蜂窝：被物件挡住的画虚
    z = wall_z0 + s * math.cos(tilt)
    off = 0 if r % 2 == 0 else P['hex_pitch'] / 2
    cols = int(P['hex_cols']) if r % 2 == 0 else int(P['hex_cols']) - 1
    col = INK if z > cpu_top_z - 12 else FAINT
    for c in range(cols):
        d.polygon(hexpts(FX(hex_x0 + off + c * P['hex_pitch']), FZ(z), P['hex_r'] * S, math.cos(tilt)),
                  fill=BG, outline=col)
box([FX(0), FZ(Zp), FX(W), FZ(Zp - P['plat_t'])], fill=SLAB, outline=INK)      # CPU 台面
box([FX(base_x0), FZ(0), FX(base_x0 + P['base_w']), FZ(-P['base_t'])], fill=BASE, outline=INK)  # 底板
for i in range(ram_tines):                             # 内存分隔牙（短牙）
    xc = ram_tine_x(i) - P['tine_t'] / 2
    box([FX(xc), FZ(0), FX(xc + P['tine_t']), FZ(P['ram_tine_h'] * math.cos(tilt))], fill=SLAB, outline=INK)
for i in range(cpu_tines):                             # CPU 分隔牙
    xc = cpu_tine_x(i) - P['tine_t'] / 2
    box([FX(xc), FZ(Zp), FX(xc + P['tine_t']), FZ(Zp + P['cpu_tine_h'] * math.cos(tilt))], fill=SLAB, outline=INK)
for i in range(ram_n):                                 # 物件 ghost：内存（下层）
    xc = ram_slot_x(i)
    box([FX(xc - P['ram_w'] / 2), FZ(ram_top_z), FX(xc + P['ram_w'] / 2), FZ(0)], outline=RAM, width=2)
    d.line([FX(xc - P['ram_w'] / 2 + 3), FZ(ram_top_z - 12), FX(xc + P['ram_w'] / 2 - 3), FZ(ram_top_z - 12)], fill=RAM, width=1)
    d.text((FX(xc - P['ram_w'] / 2 + 2), FZ(ram_top_z) + 4), '内存%d' % (i + 1), font=Fs, fill=RAM)
for i in range(cpu_n):                                 # 物件 ghost：CPU（上层）
    xc = cpu_slot_x(i)
    box([FX(xc - P['cpu_w'] / 2), FZ(cpu_top_z), FX(xc + P['cpu_w'] / 2), FZ(Zp)], outline=CPU, width=2)
    d.text((FX(xc - P['cpu_w'] / 2 + 2), FZ(cpu_top_z) + 4), 'CPU%d' % (i + 1), font=Fs, fill=CPU)
for i in range(ram_n):                                 # 前缘挡边（在物件前面，最后画）
    xc = ram_slot_x(i)
    box([FX(xc - ram_cw / 2), FZ(0), FX(xc + ram_cw / 2), FZ(P['lip_h'] * math.cos(tilt))], fill=SLAB, outline=INK)
for i in range(cpu_n):
    xc = cpu_slot_x(i)
    box([FX(xc - cpu_cw / 2), FZ(Zp), FX(xc + cpu_cw / 2), FZ(Zp + P['lip_h'] * math.cos(tilt))], fill=SLAB, outline=INK)
d.text((f_ox, FZ(-P['base_t']) + 8), '下层：内存 %d 根，底棱坐底板 Z=0，标签面朝外；分隔牙 %d 片只凸出 %.0fmm、高 %.0fmm 分开相邻两根'
       % (ram_n, ram_tines, P['ram_tine_d'] - P['ram_thick'], P['ram_tine_h']), font=Fs, fill=GREY)
d.text((f_ox, FZ(-P['base_t']) + 28), '上层：CPU %d 颗坐 Z=%.0fmm 台面，IHS 面朝外，台面从背板前面往前伸 %.0fmm（后 %.1fmm 埋进背板）'
       % (cpu_n, Zp, plat_d - P['plat_embed'], P['plat_embed']), font=Fs, fill=GREY)
d.text((f_ox, FZ(-P['base_t']) + 48), '总宽 %.0fmm；底座 %.0f×%.0f（比物件区每边宽 %.1fmm）；前缘挡边高 %.0fmm；'
       '蜂窝 %d 孔（台面根部留实心带）' % (W, P['base_w'], base_d, (P['base_w'] - W) / 2, P['lip_h'], hex_rows - (hex_rows - len(hex_kept))),
       font=Fs, fill=GREY)

# ============================ 2) 侧剖视图 ============================
d.text((s_ox - 70, FZ(wall_top_z) - 30), '侧剖视图（左 = 观众；内存/CPU blue-green 为 ghost）', font=F, fill=INK)
def quad(pts, fill, outline=INK, width=1):
    d.polygon([(SX(y), FZ(z)) for y, z in pts], fill=fill, outline=outline, width=width)

quad([(base_front, -P['base_t']), (base_back, -P['base_t']), (base_back, 0), (base_front, 0)], BASE)   # 底板
quad([(P['label_y'] - P['label_d'] / 2, -P['label_deep']), (P['label_y'] + P['label_d'] / 2, -P['label_deep']),
      (P['label_y'] + P['label_d'] / 2, 0), (P['label_y'] - P['label_d'] / 2, 0)], BASE, GREY)          # 名牌凹位
if P['anime_on']:                                                                       # 浮雕剖面（长在底板上）
    ay0, ay1 = P['anime_y'] - P['anime_d'] / 2, P['anime_y'] + P['anime_d'] / 2
    tp = P['anime_top']                                                                     # 起伏剖面（示意）
    mid = P['anime_y']
    quad([(ay0, -0.5), (ay0, 0), (ay0 + 5, tp * 0.55), (mid - 8, tp * 0.95), (mid, tp),
          (mid + 8, tp * 0.9), (ay1 - 5, tp * 0.5), (ay1, 0), (ay1, -0.5)],
         (233, 224, 243), ANIME)
    d.text((SX(ay1) + 6, FZ(tp * 0.5)), '浮雕（长在底板上，最高 %.2f）' % tp, font=Fs, fill=ANIME)
# 加强筋剖面（不在剖切面上，浅色示意）
quad([(wall_back_y(0), 0), (wall_back_y(0) + P['rib_reach_bot'] * math.cos(tilt), -P['rib_reach_bot'] * math.sin(tilt)),
      (wall_back_y(P['rib_h']) + P['rib_reach_top'] * math.cos(tilt), P['rib_h'] - P['rib_reach_top'] * math.sin(tilt)),
      (wall_back_y(P['rib_h']), P['rib_h'])], RIB, GREY)
# 背板剖面
quad([(wall_front_y(wall_z0), wall_z0), (wall_front_y(wall_top_z), wall_top_z),
      (wall_back_y(wall_top_z), wall_top_z), (wall_back_y(wall_z0), wall_z0)], PLATE)
quad([(plat_y0, Zp - P['plat_t']), (plat_y1, Zp - P['plat_t']), (plat_y1, Zp), (plat_y0, Zp)], SLAB)   # CPU 台面
# 分隔牙剖面（浅色：内存牙在 Z=0 一级、CPU 牙在 Zp 一级）
quad([(ram_butt_y, 0), (ram_butt_y + fwd(P['ram_tine_d'])[0], fwd(P['ram_tine_d'])[1]),
      (ram_butt_y + fwd(P['ram_tine_d'])[0], fwd(P['ram_tine_d'])[1] + P['ram_tine_h'] * math.cos(tilt)),
      (ram_butt_y, P['ram_tine_h'] * math.cos(tilt))], (238, 240, 243), (170, 174, 182))
quad([(cpu_butt_y, Zp), (cpu_butt_y + fwd(P['cpu_tine_d'])[0], Zp + fwd(P['cpu_tine_d'])[1]),
      (cpu_butt_y + fwd(P['cpu_tine_d'])[0], Zp + fwd(P['cpu_tine_d'])[1] + P['cpu_tine_h'] * math.cos(tilt)),
      (cpu_butt_y, Zp + P['cpu_tine_h'] * math.cos(tilt))], (238, 240, 243), (170, 174, 182))
for y0, z0 in [(ram_lip_y0, 0), (cpu_lip_y0, Zp)]:                     # 前缘挡边
    quad([(y0, z0), (y0 + up(P['lip_h'])[0], z0 + up(P['lip_h'])[1]),
          (y0 + up(P['lip_h'])[0] + P['lip_t'] * math.cos(tilt), z0 + up(P['lip_h'])[1] - P['lip_t'] * math.sin(tilt)),
          (y0 + P['lip_t'] * math.cos(tilt), z0 - P['lip_t'] * math.sin(tilt))], SLAB)

def lean_ghost(depth, length, y_butt, z_butt, color, label):
    p0 = (y_butt, z_butt)
    p1 = (y_butt + fwd(depth)[0], z_butt + fwd(depth)[1])
    p2 = (p1[0] + up(length)[0], p1[1] + up(length)[1])
    p3 = (p0[0] + up(length)[0], p0[1] + up(length)[1])
    d.polygon([(SX(y), FZ(z)) for y, z in [p0, p1, p2, p3]], outline=color, width=2)
    for t in (0.04, 0.09):                                             # 金手指那一段
        a = (p0[0] + t * (p3[0] - p0[0]), p0[1] + t * (p3[1] - p0[1]))
        b = (p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]))
        d.line([SX(a[0]), FZ(a[1]), SX(b[0]), FZ(b[1])], fill=color, width=1)
    d.text((SX(p2[0]) + 4, FZ(p2[1])), label, font=Fs, fill=color)

lean_ghost(P['ram_thick'], P['ram_len'], ram_butt_y, 0, RAM, '内存 %d 根：底棱坐底板，标签面朝外' % ram_n)
lean_ghost(P['cpu_thick'], P['cpu_w'], cpu_butt_y, Zp, CPU, 'CPU %d 颗：坐 %.0fmm 台面，IHS 面朝外' % (cpu_n, Zp))
d.text((s_ox - 70, FZ(-P['base_t']) + 8), '两级上下对调：内存 Z=0 → 顶 %.1f；CPU 台面 %.0f → 顶 %.1f（台面底离内存顶 %.1fmm）'
       % (ram_top_z, Zp, cpu_top_z, Zp - P['plat_t'] - ram_top_z), font=Fs, fill=GREY)
d.text((s_ox - 70, FZ(-P['base_t']) + 28), '加强筋 %.0f 厚 × 高 %.0f：底伸 %.0fmm → 顶收 %.0fmm；筋底埋在底板里（筋最低 Z %.1f）'
       % (P['rib_t'], P['rib_h'], P['rib_reach_bot'], P['rib_reach_top'], -P['rib_reach_bot'] * math.sin(tilt)), font=Fs, fill=GREY)
d.text((s_ox - 70, FZ(-P['base_t']) + 48), '物件背整面贴靠板、底棱压水平面 → 坐进直角角；重力把它压进板里，前缘挡边兜底',
       font=Fs, fill=GREY)

# ---- 受力标注 ----
d.line([SX(com_y), FZ(com_z), SX(com_y), FZ(-P['base_t'])], fill=RED, width=1)
for zz in range(int(FZ(-P['base_t'])), int(FZ(com_z)), 8):
    d.line([SX(com_y) - 3, zz, SX(com_y) + 3, zz], fill=RED, width=1)
d.ellipse([SX(com_y) - 5, FZ(com_z) - 5, SX(com_y) + 5, FZ(com_z) + 5], outline=RED, width=2)
d.line([SX(com_y) - 9, FZ(com_z), SX(com_y) + 9, FZ(com_z)], fill=RED, width=2)
d.line([SX(com_y), FZ(com_z) - 9, SX(com_y), FZ(com_z) + 9], fill=RED, width=2)
d.text((SX(com_y) + 8, FZ(com_z) - 10), '重心（估重 %.0f g）' % (tot_kg * 1000), font=Fs, fill=RED)
d.text((SX(com_y) + 8, FZ(com_z) + 6), '离前缘 %.0f / 离后缘 %.0f mm，重心高 %.0f' % (com_y - base_front, base_back - com_y, com_z),
       font=Fs, fill=RED)
for ey, name in [(base_front, '底板前缘'), (base_back, '底板后缘')]:
    d.line([SX(ey), FZ(0), SX(ey), FZ(-P['base_t'] - 14)], fill=RED, width=2)
    d.text((SX(ey) - 18, FZ(-P['base_t'] - 32)), name, font=Fs, fill=RED)
for by, bz in [(ram_butt_y, 0), (cpu_butt_y, Zp)]:
    d.ellipse([SX(by) - 7, FZ(bz) - 7, SX(by) + 7, FZ(bz) + 7], outline=RED, width=2)
d.text((SX(ram_butt_y) + 10, FZ(0) + 6), '两个坐角：面贴板 + 棱压水平面', font=Fs, fill=RED)
d.text((s_ox - 70, FZ(-P['base_t']) + 68), '顶部横推门槛：前倾 %.2f N（≈%.0f 克力）/ 后倾 %.2f N / 侧翻 %.2f N；力臂算到整机最高处 %.1fmm'
       % (tip_front_N, tip_front_N / 9.8 * 1000, tip_back_N, tip_side_N, H), font=Fs, fill=RED)

# ============================ 3) 俯视图 ============================
d.text((f_ox, TY(base_back) - 34), '俯视图（下 = 观众侧）', font=F, fill=INK)
d.rounded_rectangle([TX(base_x0), TY(base_back), TX(base_x0 + P['base_w']), TY(base_front)],
                    radius=P['base_r'] * S, fill=BASE, outline=INK)                       # 底板
box([TX(W / 2 - P['label_w'] / 2), TY(P['label_y'] + P['label_d'] / 2),
             TX(W / 2 + P['label_w'] / 2), TY(P['label_y'] - P['label_d'] / 2)], fill=BG, outline=GREY)  # 名牌凹位
if P['anime_on']:                                                                          # 浮雕（长在底板上）
    ax0, ax1 = (W - P['anime_w']) / 2, (W + P['anime_w']) / 2
    ay0, ay1 = P['anime_y'] - P['anime_d'] / 2, P['anime_y'] + P['anime_d'] / 2
    box([TX(ax0), TY(ay1), TX(ax1), TY(ay0)], fill=(233, 224, 243), outline=ANIME, width=2)
    d.text((TX(ax0) + 6, TY(ay1) + 6), '二次元浮雕 %.0f×%.0f，最高 %.2f（长在底板上，不另出件）'
           % (P['anime_w'], P['anime_d'], P['anime_top']), font=Fs, fill=ANIME)
for x in (W / 2 - 70, W / 2 + 70):                                                        # 脚垫坑
    for y in (base_front + 9, base_back - 9):
        r = P['foot_d'] / 2 * S
        d.ellipse([TX(x) - r, TY(y) - r, TX(x) + r, TY(y) + r], outline=GREY)
box([TX(0), TY(wall_front_y(0) + (wall_len + plate_t) * math.sin(tilt)), TX(W), TY(wall_front_y(0))],
            fill=PLATE, outline=INK)                                                       # 背板（后仰后的投影）
for i in range(ram_n):                                                                     # 内存条footprint
    xc = ram_slot_x(i)
    box([TX(xc - P['ram_w'] / 2), TY(ram_butt_y + P['ram_len'] * math.sin(tilt)),
                 TX(xc + P['ram_w'] / 2), TY(ram_butt_y + fwd(P['ram_thick'])[0])], outline=RAM, width=2)
for i in range(cpu_n):
    xc = cpu_slot_x(i)
    box([TX(xc - P['cpu_w'] / 2), TY(cpu_butt_y + P['cpu_w'] * math.sin(tilt)),
                 TX(xc + P['cpu_w'] / 2), TY(cpu_butt_y + fwd(P['cpu_thick'])[0])], outline=CPU, width=2)
for xc in (W / 2 - P['rib_x_off'], W / 2 + P['rib_x_off']):                                 # 两道加强筋
    box([TX(xc - P['rib_t'] / 2), TY(wall_back_y(0) + P['rib_reach_bot'] * math.cos(tilt)),
                 TX(xc + P['rib_t'] / 2), TY(wall_back_y(0))], fill=RIB, outline=GREY)
d.text((TX(base_x0 + P['base_w']) + 10, TY(base_back)), '底板 %.0f × %.0f，四角 R%.0f' % (P['base_w'], base_d, P['base_r']), font=Fs, fill=INK)
d.text((TX(base_x0 + P['base_w']) + 10, TY(base_back) + 20), '背板后仰后的投影（后缘 Y=%.1f）' % (wall_front_y(0) + (wall_len + plate_t) * math.sin(tilt)), font=Fs, fill=INK)
d.text((TX(base_x0 + P['base_w']) + 10, TY(base_back) + 40), '两道加强筋 @X=%.0f / %.0f，伸出 %.0f→%.0fmm' % (W / 2 - P['rib_x_off'], W / 2 + P['rib_x_off'], P['rib_reach_bot'], P['rib_reach_top']), font=Fs, fill=INK)
d.text((TX(base_x0 + P['base_w']) + 10, TY(base_back) + 60), '内存 footprint（蓝）· CPU footprint（绿）—— 上下两级错开，才塞得进 %.0f 宽度' % W, font=Fs, fill=GREY)
d.text((TX(base_x0 + P['base_w']) + 10, TY(base_back) + 82), '台面 Y %.1f..%.1f（后 %.1fmm 埋进背板）' % (plat_y0, plat_y1, plat_y1 - cpu_butt_y), font=Fs, fill=GREY)

canvas.save(OUT)
print('已输出 %s (%dx%d)' % (OUT, canvas.size[0], canvas.size[1]))
print('三视图：正视图(左上) / 侧剖视图(右上) / 俯视图(下)')
print('侧剖视：内存底棱 (y=%.2f, z=0)，CPU 底棱 (y=%.2f, z=%.0f)，底板 Y %.0f..%.1f，重心 (y=%.1f, z=%.1f)'
      % (ram_butt_y, cpu_butt_y, Zp, base_front, base_back, com_y, com_z))
