#!/usr/bin/env python3
"""rack.scad 自检：尺寸派生量全取自 model.py（和 preview.py 同一份），逐条按物理约束算。

只读 rack.scad / model.py / 台账 print-ideas.json，不改任何文件；全过才有意义开打。
用法: python3 check.py     # 退出码 0 = 全过
"""
import json, math, sys
from pathlib import Path
from model import *   # noqa: F401,F403 —— 派生尺寸与重心只在 model.py 算一份

LEDGER = Path.home() / '.cah-data/skills/shared/3d-print-ideas/runtime/print-ideas.json'

fails, total = [], 0
def check(ok, label, detail):
    global total
    total += 1
    print(('  ok  ' if ok else ' FAIL ') + label + '  ' + detail)
    if not ok: fails.append(label)

# 1) 外廓 / 可打印性
check(W <= 250 and base_d <= 250 and H <= 250, '单件外廓 ≤250³', '%.1f x %.1f x %.1f mm' % (W, base_d, H))
check(math.degrees(tilt) <= 20, '后仰角不超 20°', '%.0f°（斜面远离 45° 悬垂线，免支撑）' % math.degrees(tilt))

# 2) 物件的落位与间隙
check(ram_cw - P['ram_w'] >= 1.5, '内存位留间隙（不夹）', '净宽 %.1f - 内存 %.1f = %.1f mm' % (ram_cw, P['ram_w'], ram_cw - P['ram_w']))
check(cpu_cw - P['cpu_w'] >= 1.5, 'CPU 位留间隙', '净宽 %.1f - CPU %.1f = %.1f mm' % (cpu_cw, P['cpu_w'], cpu_cw - P['cpu_w']))
check(P['ram_tine_d'] > P['ram_thick'], '内存牙比内存厚，能把住', '牙伸出 %.0f > 内存厚 %.0f' % (P['ram_tine_d'], P['ram_thick']))
check(P['cpu_tine_d'] > P['cpu_thick'], 'CPU 牙比 CPU 厚', '牙伸出 %.0f > CPU 厚 %.0f' % (P['cpu_tine_d'], P['cpu_thick']))
check(wall_top_z - ram_top_z >= 10, '背板高过内存顶，兜得住', '背板顶 %.1f - 内存顶 %.1f = %.1f mm' % (wall_top_z, ram_top_z, wall_top_z - ram_top_z))

# 3) 落位：物件坐进「靠板前表面 + 台面/底板」的角里
ram_butt = (wall_y_at_Zp, P['Zp'])                      # 内存底边棱落点
check(abs(wall_front_y(P['Zp']) - P['Zp'] * 0 - wall_y_at_Zp) < 1e-9,
      '内存底边棱正好落在背板前表面', '落点 Y %.2f = 背板前表面 Y(Zp) %.2f' % (ram_butt[0], wall_y_at_Zp))
check(P['plat_y0'] < ram_butt[0] and ram_butt[0] < P['plat_y0'] + P['plat_d'],
      '内存底边棱落在台面进深内', '落点 Y %.2f ∈ 台面 [%.0f, %.0f]' % (ram_butt[0], P['plat_y0'], P['plat_y0'] + P['plat_d']))
check(abs(cpu_plate_y0 - cpu_plate_front_y(cpu_plate_z0)) < 1e-9 and cpu_plate_front_y(0) < P['plat_y0'],
      'CPU 底边棱落在底板与 CPU 靠板交角上', '交角 Y %.2f，在台面前缘 %.0f 之前' % (cpu_plate_front_y(0), P['plat_y0']))

# 4) 前缘挡边（不靠摩擦独扛） + 摩擦余量
check(math.tan(tilt) < 0.3, '斜靠角在摩擦能自持范围内', 'tan%.0f° = %.3f < μ≈0.30（挡边仍保留兜底）' % (math.degrees(tilt), math.tan(tilt)))
check(P['lip_h'] >= 5, '每级都有前缘挡边', '挡边高 %.0f mm' % P['lip_h'])
ram_front_bottom_y = wall_y_at_Zp + fwd(P['ram_thick'])[0]
ram_lip_back_y = P['plat_y0'] + P['lip_t'] * math.cos(tilt)
gap = ram_front_bottom_y - ram_lip_back_y
check(0 <= gap <= 4, '内存挡边贴着内存前下角', '间隙 %.2f mm' % gap)
check(cpu_lip_y0 > base_front + 3, 'CPU 挡边在底板范围内', '挡边前下角 Y %.2f > 底板前缘 %.0f + 3' % (cpu_lip_y0, base_front))

# 5) 底板兜得住
check(wall_back_top_y <= base_back - 3, '背板后仰后仍在底板内', '板顶后沿 Y %.1f ≤ 底板后缘 %.1f - 3' % (wall_back_top_y, base_back))
check(cpu_lip_y0 - base_front >= 15, '底板前伸出基座（抗前倾）', '前伸 %.1f mm' % (cpu_lip_y0 - base_front))
check(P['plate_t'] >= 3, '斜靠板有厚度', '板厚 %.0f mm' % P['plate_t'])
check(P['plat_d'] >= P['ram_thick'] + 4, '台面进深容得下内存厚', '台面 %.0f ≥ 内存厚 %.0f + 4' % (P['plat_d'], P['ram_thick']))

# 6) 镂空
lig_x = P['hex_pitch'] - 2 * P['hex_r']
lig_z = P['hex_pitch'] - 2 * P['hex_r'] * math.cos(math.pi / 6)
hex_x0 = (W - (P['hex_cols'] - 1) * P['hex_pitch']) / 2
hex_rows = int((P['wall_len'] - 2 * P['hex_zmargin']) // P['hex_pitch']) + 1
row_x = [hex_x0 + c * P['hex_pitch'] for c in range(int(P['hex_cols']))]
row_x_odd = [hex_x0 + P['hex_pitch'] / 2 + c * P['hex_pitch'] for c in range(int(P['hex_cols']) - 1)]
xmin = min(row_x[0], row_x_odd[0]) - P['hex_r']
xmax = max(row_x[-1], row_x_odd[-1]) + P['hex_r']
smax = P['hex_zmargin'] + (hex_rows - 1) * P['hex_pitch'] + P['hex_r']
check(lig_x >= 3 and lig_z >= 3, '蜂窝孔间留料 ≥3mm', '横向 %.1f / 纵向 %.1f mm' % (lig_x, lig_z))
check(xmin >= 4 and xmax <= W - 4, '蜂窝不啃边', '最左 %.1f 最右 %.1f（板宽 %.0f）' % (xmin, xmax, W))
check(abs((row_x[0] + row_x[-1]) / 2 - W / 2) < 0.01 and abs((row_x_odd[0] + row_x_odd[-1]) / 2 - W / 2) < 0.01,
      '蜂窝整排居中', '偶数行 %.2f / 奇数行 %.2f / 板中 %.2f' % ((row_x[0] + row_x[-1]) / 2, (row_x_odd[0] + row_x_odd[-1]) / 2, W / 2))
check(smax <= P['wall_len'] - 4, '蜂窝不啃板顶', '沿斜面最远 %.1f ≤ %.0f' % (smax, P['wall_len'] - 4))

# 7) 脚垫 / 名牌位
pads = [(W / 2 - 70, base_front + 9), (W / 2 + 70, base_front + 9),
        (W / 2 - 70, base_back - 9), (W / 2 + 70, base_back - 9)]
edge_min = min(min(x, y - base_front, W - x, base_back - y) for x, y in pads)
check(edge_min >= P['foot_d'] / 2 + 1, '四个脚垫坑都在料内（避开圆角）', '坑心最靠边 %.1f ≥ 半径 %.0f + 1' % (edge_min, P['foot_d'] / 2))
check(P['label_d'] + 2 * 4 <= base_d and W - P['label_w'] >= 2 * 6, '名牌凹位放得下', '%.0f x %.0f 凹位，四周留边够' % (P['label_w'], P['label_d']))

# 8) 受力：重心 / 倾覆门槛 / 强度
check(base_front <= com_y <= base_back, '整机重心投影落在底板内（静置不倒）',
      '重心 y=%.1f ∈ [%.0f, %.1f]，离前缘 %.1f / 离后缘 %.1f mm，重心高 %.1f mm，估重 %.0f g'
      % (com_y, base_front, base_back, com_y - base_front, base_back - com_y, com_z, tot_kg * 1000))
check(tip_front_N > 1.2, '顶部前推才前倾的门槛够高', '%.2f N（≈%.0f 克力）' % (tip_front_N, tip_front_N / 9.8 * 1000))
check(tip_back_N > 1.2, '后倾门槛也不虚', '%.2f N（≈%.0f 克力）' % (tip_back_N, tip_back_N / 9.8 * 1000))
check(tip_side_N > 3, '侧向最稳（宽底）', '%.2f N 才侧翻' % tip_side_N)
check(ram_com_off > 3 and cpu_com_off > 3, '物件自身不会前翻（重力把件压进靠板）',
      '内存重心比底棱靠后 %.1f mm / CPU %.1f mm —— 力矩朝板里，不吃摩擦' % (ram_com_off, cpu_com_off))
check(root_sigma_MPa < 5, '靠板强度富余（PLA 抗弯 ~40MPa）', '根部应力 %.2f MPa，安全系数 >%.0f' % (root_sigma_MPa, 40 / root_sigma_MPa))

# 9) 台账同步
led = json.loads(LEDGER.read_text())
idea = next(i for i in led['ideas'] if i['id'] == 'idea-003')
size = idea['dimensions'] or ''
check('%g x %g x %g' % (round(W), round(base_d), round(H)) in size, '台账 dimensions 与模型一致', size)
check(idea['openQuestions'] == [], '台账没有僵尸待确认项', str(idea['openQuestions']))

print('\n%s（共 %d 项）' % ('全部通过' if not fails else '有 %d 项不过: %s' % (len(fails), fails), total))
sys.exit(1 if fails else 0)
