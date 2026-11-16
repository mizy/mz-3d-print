#!/usr/bin/env python3
"""rack.scad 的参数解析 + 派生尺寸 + 估重/重心 —— check.py 与 preview.py 共用这一份。

两个脚本必须看到同一套数字（否则「验过的」和「画出来的」会不一样），所以派生量和
质量模型只在这里算一次。改尺寸只改 rack.scad 顶部的参数。
"""
import math, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = (HERE / 'rack.scad').read_text()

def num(name):
    m = re.search(r'^\s*%s\s*=\s*([-0-9.]+)\s*;' % name, RAW, re.M)
    assert m, 'rack.scad 里找不到参数 ' + name
    return float(m.group(1))

P = {k: num(k) for k in [
    'ram_n', 'ram_w', 'ram_thick', 'ram_len', 'cpu_n', 'cpu_w', 'cpu_thick', 'tilt', 'tine_t',
    'ram_tine_d', 'ram_tine_h', 'cpu_tine_d', 'cpu_tine_h', 'lip_t', 'lip_h', 'lip_gap',
    'wall_y0', 'wall_z0', 'wall_len', 'plate_t', 'Zp', 'plat_d', 'plat_t', 'plat_embed',
    'base_t', 'base_w', 'base_front', 'base_back_margin', 'base_r',
    'label_w', 'label_d', 'label_deep', 'label_y',
    'anime_on', 'anime_w', 'anime_d', 'anime_y', 'anime_bury', 'anime_top',
    'hex_r', 'hex_pitch', 'hex_cols', 'hex_zmargin', 'hex_skip',
    'rib_t', 'rib_x_off', 'rib_reach_bot', 'rib_reach_top', 'rib_h', 'foot_d', 'foot_deep']}
tilt = math.radians(P['tilt'])
ram_n, cpu_n = int(P['ram_n']), int(P['cpu_n'])
ram_cw, cpu_cw = P['ram_w'] + 2, P['cpu_w'] + 2
ram_tines, cpu_tines = ram_n + 1, cpu_n + 1
W = ram_n * ram_cw + ram_tines * P['tine_t']
cpu_row_w = cpu_n * cpu_cw + cpu_tines * P['tine_t']
cpu_row_x0 = (W - cpu_row_w) / 2
base_x0 = (W - P['base_w']) / 2
size_x  = max(W, P['base_w'])              # 真实外廓 X（底板比物件区宽时以底板为准）

def up(d):   return ( d * math.sin(tilt),  d * math.cos(tilt))   # 沿斜面往上 (Δy, Δz)
def fwd(d):  return (-d * math.cos(tilt),  d * math.sin(tilt))   # 垂直板面往观众方向

def wall_front_y(z): return P['wall_y0'] + (z - P['wall_z0']) * math.tan(tilt)
def wall_back_y(z):  return wall_front_y(z) + P['plate_t'] / math.cos(tilt)

Zp, plat_d, plat_t = P['Zp'], P['plat_d'], P['plat_t']
wall_z0, wall_len, plate_t = P['wall_z0'], P['wall_len'], P['plate_t']
base_t, base_front, base_back = P['base_t'], P['base_front'], 0  # base_back 下面覆盖
ram_butt_y = wall_front_y(0)                      # 内存底棱落点
cpu_butt_y = wall_front_y(Zp)                     # CPU 底棱落点
plat_y0    = cpu_butt_y - (plat_d - P['plat_embed'])  # 台面前缘（后缘埋进背板 plat_embed）
plat_y1    = plat_y0 + plat_d
base_back  = wall_front_y(0) + (wall_len + plate_t) * math.sin(tilt) + P['base_back_margin']
base_d     = base_back - base_front
wall_top_z = wall_z0 + wall_len * math.cos(tilt)
H          = base_t + wall_top_z
ram_top_z  = P['ram_len'] * math.cos(tilt) + P['ram_thick'] * math.sin(tilt)
cpu_top_z  = Zp + P['cpu_w'] * math.cos(tilt) + P['cpu_thick'] * math.sin(tilt)
lip_y0     = lambda butt, thick: butt + fwd(thick)[0] - P['lip_gap'] - P['lip_t'] * math.cos(tilt)
ram_lip_y0, cpu_lip_y0 = lip_y0(ram_butt_y, P['ram_thick']), lip_y0(cpu_butt_y, P['cpu_thick'])
ram_slot_x  = lambda i: (i + 1) * P['tine_t'] + i * ram_cw + ram_cw / 2
cpu_slot_x  = lambda i: cpu_row_x0 + (i + 1) * P['tine_t'] + i * cpu_cw + cpu_cw / 2
ram_tine_x  = lambda i: i * (ram_cw + P['tine_t']) + P['tine_t'] / 2
cpu_tine_x  = lambda i: cpu_row_x0 + i * (cpu_cw + P['tine_t']) + P['tine_t'] / 2

# ---------- 估重 / 重心（PLA 1.24 g/cm3；内存 35g、CPU 30g 为估值） ----------
# parts: (名字, 体积 mm3, 重心 x, 重心 y, 重心 z, 附加质量 g)
density, ram_m, cpu_m = 1.24, 35.0, 30.0
parts = [('底板', P['base_w'] * base_d * base_t,
          base_x0 + P['base_w'] / 2, (base_front + base_back) / 2, -base_t / 2, 0),
         ('背板', W * plate_t * wall_len,
          W / 2, wall_front_y(wall_z0) + up(wall_len / 2)[0] + (plate_t / 2) * math.cos(tilt),
          wall_z0 + up(wall_len / 2)[1] - (plate_t / 2) * math.sin(tilt), 0),
         ('CPU 台面', W * plat_d * plat_t, W / 2, plat_y0 + plat_d / 2, Zp - plat_t / 2, 0)]
reach_avg = (P['rib_reach_bot'] + P['rib_reach_top']) / 2 * math.cos(tilt)
for xc in (W / 2 - P['rib_x_off'], W / 2 + P['rib_x_off']):
    parts.append(('加强筋@%.0f' % xc, P['rib_t'] * P['rib_h'] * reach_avg,
                  xc, wall_back_y(P['rib_h'] / 2) + reach_avg / 2,
                  P['rib_h'] / 2 - reach_avg / 2 * math.tan(tilt), 0))
for i in range(ram_tines):
    parts.append(('内存牙%d' % i, P['tine_t'] * P['ram_tine_d'] * P['ram_tine_h'],
                  ram_tine_x(i), ram_butt_y + fwd(P['ram_tine_d'] / 2)[0] + up(P['ram_tine_h'] / 2)[0],
                  fwd(P['ram_tine_d'] / 2)[1] + up(P['ram_tine_h'] / 2)[1], 0))
for i in range(cpu_tines):
    parts.append(('CPU 牙%d' % i, P['tine_t'] * P['cpu_tine_d'] * P['cpu_tine_h'],
                  cpu_tine_x(i), cpu_butt_y + fwd(P['cpu_tine_d'] / 2)[0] + up(P['cpu_tine_h'] / 2)[0],
                  Zp + fwd(P['cpu_tine_d'] / 2)[1] + up(P['cpu_tine_h'] / 2)[1], 0))
for i in range(ram_n):
    parts.append(('内存挡边%d' % i, ram_cw * P['lip_t'] * P['lip_h'],
                  ram_slot_x(i), ram_lip_y0 + fwd(P['lip_t'] / 2)[0] + up(P['lip_h'] / 2)[0],
                  fwd(P['lip_t'] / 2)[1] + up(P['lip_h'] / 2)[1], 0))
for i in range(cpu_n):
    parts.append(('CPU 挡边%d' % i, cpu_cw * P['lip_t'] * P['lip_h'],
                  cpu_slot_x(i), cpu_lip_y0 + fwd(P['lip_t'] / 2)[0] + up(P['lip_h'] / 2)[0],
                  Zp + fwd(P['lip_t'] / 2)[1] + up(P['lip_h'] / 2)[1], 0))
for i in range(ram_n):
    parts.append(('内存%d' % i, 0, ram_slot_x(i),
                  ram_butt_y + fwd(P['ram_thick'] / 2)[0] + up(P['ram_len'] / 2)[0],
                  fwd(P['ram_thick'] / 2)[1] + up(P['ram_len'] / 2)[1], ram_m))
for i in range(cpu_n):
    parts.append(('CPU%d' % i, 0, cpu_slot_x(i),
                  cpu_butt_y + fwd(P['cpu_thick'] / 2)[0] + up(P['cpu_w'] / 2)[0],
                  Zp + fwd(P['cpu_thick'] / 2)[1] + up(P['cpu_w'] / 2)[1], cpu_m))

part_kg = [(n, v / 1e6 * density + g / 1000, x, y, z) for n, v, x, y, z, g in parts]
tot_kg = sum(k for _, k, _, _, _ in part_kg)
com_x = sum(k * x for _, k, x, _, _ in part_kg) / tot_kg
com_y = sum(k * y for _, k, _, y, _ in part_kg) / tot_kg
com_z = sum(k * z for _, k, _, _, z in part_kg) / tot_kg
mg = tot_kg * 9.8
arm = H / 1000          # 顶部横推的力臂（m）：算到整机最高处，取保守值

def tip_force(edge_y):
    """在顶边横推多大力才绕着 edge_y 这条棱翻倒（N）"""
    return abs(com_y - edge_y) / 1000 * mg / arm

tip_front_N = tip_force(base_front)
tip_back_N  = tip_force(base_back)
tip_side_N  = min(com_x - base_x0, base_x0 + P['base_w'] - com_x) / 1000 * mg / arm
# 单件重心相对「底边棱」的偏移（朝靠板一侧为正 = 力矩把件压进板里，不靠摩擦）
ram_com_off = P['ram_thick'] / 2 * math.cos(tilt) + P['ram_len'] / 2 * math.sin(tilt)
cpu_com_off = P['cpu_thick'] / 2 * math.cos(tilt) + P['cpu_w'] / 2 * math.sin(tilt)
# 靠板根部弯曲应力（保守把水平推力按 2 倍估）；加强筋把板中上段弯矩传回底板
root_force_N = (ram_n * ram_m + cpu_n * cpu_m) / 1000 * 9.8 * math.sin(tilt) * 2
root_sigma_MPa = root_force_N * (wall_top_z - 0) / 1000 * 1000 / (W * plate_t ** 2 / 6)
# 单道加强筋的截面惯性矩与抗弯模量（b=肋厚, h=肋高），用来核「筋够不够硬」
rib_S = P['rib_t'] * P['rib_h'] ** 2 / 6                      # mm3（按肋高当悬臂高）
rib_sigma_MPa = root_force_N / 2 * (P['rib_h']) / 1000 * 1000 / rib_S
