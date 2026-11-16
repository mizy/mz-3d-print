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
    'ram_n', 'ram_w', 'ram_thick', 'ram_len', 'cpu_n', 'cpu_w', 'cpu_thick',
    'tilt', 'base_t', 'base_front', 'base_back_margin', 'base_r', 'plate_t',
    'Zp', 'plat_y0', 'plat_d', 'plat_t', 'tine_t',
    'ram_tine_d', 'ram_tine_h', 'cpu_tine_d', 'cpu_tine_h',
    'lip_t', 'lip_h', 'lip_gap', 'hex_r', 'hex_pitch', 'hex_cols', 'hex_zmargin',
    'wall_len', 'foot_d', 'foot_deep', 'label_w', 'label_d', 'label_deep', 'label_y']}
tilt = math.radians(P['tilt'])
ram_n, cpu_n = int(P['ram_n']), int(P['cpu_n'])
ram_cw, cpu_cw = P['ram_w'] + 2, P['cpu_w'] + 2
ram_tines, cpu_tines = ram_n + 1, cpu_n + 1
W = ram_n * ram_cw + ram_tines * P['tine_t']          # 架宽
cpu_row_w = cpu_n * cpu_cw + cpu_tines * P['tine_t']
cpu_row_x0 = (W - cpu_row_w) / 2
# 常被引用的尺寸给个短名字（rack.scad 里也是这几个名字）
Zp, plat_y0, plat_d, plat_t = P['Zp'], P['plat_y0'], P['plat_d'], P['plat_t']
base_t = P['base_t']
wall_z0   = P['Zp'] - 3
wall_y_at_Zp = P['plat_y0'] + P['plat_d'] - 4          # 背板前表面在台面高度处的 Y

def up(d):   return ( d * math.sin(tilt),  d * math.cos(tilt))   # 沿斜面往上
def fwd(d):  return (-d * math.cos(tilt),  d * math.sin(tilt))   # 垂直板面往观众方向

wall_y0   = wall_y_at_Zp - (P['Zp'] - wall_z0) * math.tan(tilt)
wall_top_z = wall_z0 + P['wall_len'] * math.cos(tilt)
wall_back_top_y = wall_y0 + (P['wall_len'] + P['plate_t']) * math.sin(tilt)
ram_top_z = P['Zp'] + P['ram_len'] * math.cos(tilt)
H = P['base_t'] + wall_top_z

cpu_plate_z0  = -2
cpu_plate_len = (P['Zp'] - cpu_plate_z0) / math.cos(tilt)
cpu_plate_y0  = P['plat_y0'] - cpu_plate_len * math.sin(tilt)

base_front = P['base_front']
base_back  = wall_back_top_y + P['base_back_margin']
base_d     = base_back - base_front

ram_slot_x  = lambda i: (i + 1) * P['tine_t'] + i * ram_cw + ram_cw / 2
cpu_slot_x  = lambda i: cpu_row_x0 + (i + 1) * P['tine_t'] + i * cpu_cw + cpu_cw / 2
cpu_plate_point = lambda s: (cpu_plate_y0 + up(s)[0], cpu_plate_z0 + up(s)[1])
wall_front_y    = lambda z: wall_y0 + (z - wall_z0) * math.tan(tilt)      # 背板前表面
cpu_plate_front_y = lambda z: cpu_plate_y0 + (z - cpu_plate_z0) * math.tan(tilt)
cpu_lip_y0 = cpu_plate_y0 + fwd(P['cpu_thick'] + P['lip_gap'] + P['lip_t'])[0]

# ---------- 估重 / 重心（PLA 1.24 g/cm3；内存 35g、CPU 30g 为估值） ----------
density, ram_m, cpu_m = 1.24, 35.0, 30.0
parts = []   # (名字, 体积 mm3, 重心 y, 重心 z, 附加质量 g)
parts.append(('底板', W * base_d * P['base_t'], (base_front + base_back) / 2, -P['base_t'] / 2, 0))
wy, wz = up(P['wall_len'] / 2)
parts.append(('背板', W * P['plate_t'] * P['wall_len'],
              wall_y0 + wy + fwd(P['plate_t'] / 2)[0], wall_z0 + wz + fwd(P['plate_t'] / 2)[1], 0))
cy, cz = up(cpu_plate_len / 2)
parts.append(('CPU 靠板', W * P['plate_t'] * cpu_plate_len,
              cpu_plate_y0 + cy + fwd(P['plate_t'] / 2)[0], cpu_plate_z0 + cz + fwd(P['plate_t'] / 2)[1], 0))
parts.append(('台面', W * P['plat_d'] * P['plat_t'], P['plat_y0'] + P['plat_d'] / 2, P['Zp'] - P['plat_t'] / 2, 0))
for i in range(ram_tines):
    parts.append(('内存牙%d' % i, P['tine_t'] * P['ram_tine_d'] * P['ram_tine_h'],
                  wall_y_at_Zp + fwd(P['ram_tine_d'] / 2)[0] + up(P['ram_tine_h'] / 2)[0],
                  P['Zp'] + fwd(P['ram_tine_d'] / 2)[1] + up(P['ram_tine_h'] / 2)[1], 0))
for i in range(cpu_tines):
    parts.append(('CPU 牙%d' % i, P['tine_t'] * P['cpu_tine_d'] * P['cpu_tine_h'],
                  cpu_plate_y0 + fwd(P['cpu_tine_d'] / 2)[0] + up(P['cpu_tine_h'] / 2)[0],
                  cpu_plate_z0 + fwd(P['cpu_tine_d'] / 2)[1] + up(P['cpu_tine_h'] / 2)[1], 0))
for i in range(ram_n):
    parts.append(('内存%d' % i, 0, wall_y_at_Zp + fwd(P['ram_thick'] / 2)[0] + up(P['ram_len'] / 2)[0],
                  P['Zp'] + fwd(P['ram_thick'] / 2)[1] + up(P['ram_len'] / 2)[1], ram_m))
for i in range(cpu_n):
    parts.append(('CPU%d' % i, 0, cpu_plate_front_y(0) + fwd(P['cpu_thick'] / 2)[0] + up(P['cpu_w'] / 2)[0],
                  0 + fwd(P['cpu_thick'] / 2)[1] + up(P['cpu_w'] / 2)[1], cpu_m))

part_kg = [(n, v / 1e6 * density + g / 1000, y, z) for n, v, y, z, g in parts]
tot_kg = sum(k for _, k, _, _, in part_kg)
com_y = sum(k * y for _, k, y, _ in part_kg) / tot_kg
com_z = sum(k * z for _, k, _, z in part_kg) / tot_kg
mg = tot_kg * 9.8
arm = (ram_top_z + P['base_t']) / 1000          # 顶部横推的力臂（m）

def tip_force(edge_y):
    """在顶边横推多大力才绕着 edge_y 这条棱翻倒（N）"""
    return abs(com_y - edge_y) / 1000 * mg / arm

tip_front_N = tip_force(base_front)
tip_back_N  = tip_force(base_back)
tip_side_N  = tip_force(W / 2) * 0    # 侧向用 X 方向的臂，单独算
tip_side_N  = (W / 2) / 1000 * mg / arm
# 单件重心相对「底边棱」的偏移（朝靠板一侧为正 = 力矩把件压进板里，不靠摩擦）
ram_com_off = P['ram_thick'] / 2 * math.cos(tilt) + P['ram_len'] / 2 * math.sin(tilt)
cpu_com_off = P['cpu_thick'] / 2 * math.cos(tilt) + P['cpu_w'] / 2 * math.sin(tilt)
# 靠板根部弯曲应力（保守把水平推力按 2 倍估）
root_force_N = (ram_n * ram_m + cpu_n * cpu_m) / 1000 * 9.8 * math.sin(tilt) * 2
root_sigma_MPa = root_force_N * (wall_top_z - P['Zp']) / 1000 * 1000 / (W * P['plate_t'] ** 2 / 6)
