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
check(size_x <= 250 and base_d <= 250 and H <= 250, '单件外廓 ≤250³（按真实包围盒）',
      '%.1f x %.1f x %.1f mm（物件区宽 %.0f / 底板宽 %.0f）' % (size_x, base_d, H, W, P['base_w']))
check(math.degrees(tilt) <= 20, '后仰角不超 20°', '%.0f°（斜面远离 45° 悬垂线，免支撑）' % math.degrees(tilt))

# 2) 上下两级：内存在下、CPU 在上，两级之间不打架
check(Zp - P['plat_t'] - ram_top_z >= 2, 'CPU 台面下沿高过内存最高点',
      '台面底 %.1f - 内存顶 %.2f = %.2f mm' % (Zp - P['plat_t'], ram_top_z, Zp - P['plat_t'] - ram_top_z))
check(ram_butt_y < cpu_butt_y and ram_top_z < cpu_top_z, 'CPU 一级整体高过内存一级',
      '内存 底棱 Y%.1f/顶 Z%.1f；CPU 底棱 Y%.1f/顶 Z%.1f' % (ram_butt_y, ram_top_z, cpu_butt_y, cpu_top_z))
check(wall_top_z - cpu_top_z >= 2, '背板高过 CPU 最高点，兜得住',
      '背板顶 %.1f - CPU 顶 %.2f = %.2f mm' % (wall_top_z, cpu_top_z, wall_top_z - cpu_top_z))

# 3) 物件的落位与间隙
check(ram_cw - P['ram_w'] >= 1.5, '内存位留间隙（不夹）', '净宽 %.1f - 内存 %.1f = %.1f mm' % (ram_cw, P['ram_w'], ram_cw - P['ram_w']))
check(cpu_cw - P['cpu_w'] >= 1.5, 'CPU 位留间隙', '净宽 %.1f - CPU %.1f = %.1f mm' % (cpu_cw, P['cpu_w'], cpu_cw - P['cpu_w']))
check(P['ram_tine_d'] > P['ram_thick'], '内存牙比内存厚，能把住', '牙伸出 %.0f > 内存厚 %.0f' % (P['ram_tine_d'], P['ram_thick']))
check(P['cpu_tine_d'] > P['cpu_thick'], 'CPU 牙比 CPU 厚', '牙伸出 %.0f > CPU 厚 %.0f' % (P['cpu_tine_d'], P['cpu_thick']))

# 3b) 隔板「只凸出一点」——主人 9/28 要求：收短到只分开相邻件，不做隔墙
ram_proud = P['ram_tine_d'] - P['ram_thick']
cpu_proud = P['cpu_tine_d'] - P['cpu_thick']
check(0 < ram_proud <= 6 and P['ram_tine_h'] <= P['ram_len'] / 6,
      '内存隔板只凸出一点点（不是隔墙）',
      '凸出 %.0f mm ≤ 6；牙高 %.0f ≤ 内存长/6 = %.1f' % (ram_proud, P['ram_tine_h'], P['ram_len'] / 6))
check(0 < cpu_proud <= 6 and P['cpu_tine_h'] <= P['cpu_w'] * 0.6,
      'CPU 隔板同样只凸出一点点', '凸出 %.0f mm；牙高 %.0f ≤ %.0f' % (cpu_proud, P['cpu_tine_h'], P['cpu_w'] * 0.6))

# 4) 落位：物件坐进「靠板前表面 + 水平面」的角里
check(abs(wall_front_y(0) - ram_butt_y) < 1e-9 and base_front < ram_butt_y < base_back,
      '内存底棱落在底板面上、背贴背板前表面', '落点 (Y %.2f, Z 0) ∈ 底板 [%.0f, %.1f]' % (ram_butt_y, base_front, base_back))
check(abs(wall_front_y(Zp) - cpu_butt_y) < 1e-9 and plat_y0 < cpu_butt_y < plat_y1,
      'CPU 底棱落在台面顶面上、背贴背板前表面', '落点 (Y %.2f, Z %.0f) ∈ 台面 [%.2f, %.2f]' % (cpu_butt_y, Zp, plat_y0, plat_y1))
check(plat_y1 - cpu_butt_y >= 2, '台面后缘埋进背板（根部是实心）', '埋进 %.1f mm' % (plat_y1 - cpu_butt_y))
check(plat_y1 <= wall_back_y(Zp - plat_t) - 0.3, '台面后缘整条落在背板后表面之内（不戳出背面出薄片）',
      '台面后缘 Y %.2f ≤ 背板底面处后表面 %.2f - 0.3（板厚/cos%.0f° = %.2f）'
      % (plat_y1, wall_back_y(Zp - plat_t), math.degrees(tilt), P['plate_t'] / math.cos(tilt)))

# 5) 前缘挡边（不靠摩擦独扛） + 摩擦余量
check(math.tan(tilt) < 0.3, '斜靠角在摩擦能自持范围内', 'tan%.0f° = %.3f < μ≈0.30（挡边仍保留兜底）' % (math.degrees(tilt), math.tan(tilt)))
check(P['lip_h'] >= 5, '每级都有前缘挡边', '挡边高 %.0f mm' % P['lip_h'])
ram_front_bottom_y = ram_butt_y + fwd(P['ram_thick'])[0]
gap = ram_front_bottom_y - (ram_lip_y0 + P['lip_t'] * math.cos(tilt))
check(0 <= gap <= 4, '内存挡边贴着内存前下角', '间隙 %.2f mm' % gap)
cpu_front_bottom_y = cpu_butt_y + fwd(P['cpu_thick'])[0]
gap_c = cpu_front_bottom_y - (cpu_lip_y0 + P['lip_t'] * math.cos(tilt))
check(0 <= gap_c <= 4, 'CPU 挡边贴着 CPU 前下角', '间隙 %.2f mm' % gap_c)
check(ram_lip_y0 > base_front + 3, '内存挡边在底板范围内', '挡边前下角 Y %.2f > 底板前缘 %.0f + 3' % (ram_lip_y0, base_front))
check(cpu_lip_y0 > plat_y0 + 1, 'CPU 挡边整条坐在台面上', '挡边前下角 Y %.2f > 台面前缘 %.2f + 1' % (cpu_lip_y0, plat_y0))

# 6) 底板 / 加强筋兜得住
check(wall_front_y(0) + (wall_len + plate_t) * math.sin(tilt) <= base_back - 3, '背板后仰后仍在底板内',
      '板顶后沿 Y %.1f ≤ 底板后缘 %.1f - 3' % (wall_front_y(0) + (wall_len + plate_t) * math.sin(tilt), base_back))
rib_back_y = wall_back_y(0) + P['rib_reach_bot'] * math.cos(tilt)
check(rib_back_y <= base_back - 3, '加强筋后伸也在底板内', '筋底后沿 Y %.1f ≤ %.1f - 3' % (rib_back_y, base_back))
check(-P['rib_reach_bot'] * math.sin(tilt) >= -P['base_t'] + 0.5, '加强筋底不戳穿底板底面',
      '筋最低 Z %.2f ≥ 底板底 %.0f + 0.5' % (-P['rib_reach_bot'] * math.sin(tilt), -P['base_t']))
check(P['rib_reach_bot'] > P['rib_reach_top'] and P['rib_reach_top'] >= P['rib_t'],
      '加强筋根粗梢细、梢部还有料', '底部伸 %.0f → 顶部 %.0f，筋厚 %.0f' % (P['rib_reach_bot'], P['rib_reach_top'], P['rib_t']))
check(P['rib_h'] >= 0.5 * wall_top_z, '加强筋够高（撑到背板中上段）', '筋高 %.0f ≥ 背板高的一半 %.1f' % (P['rib_h'], 0.5 * wall_top_z))
check(P['plate_t'] >= 3, '斜靠板有厚度', '板厚 %.0f mm' % P['plate_t'])
check(P['base_w'] >= W, '底板不比物件区窄', '底板 %.0f ≥ 架宽 %.0f' % (P['base_w'], W))
check(-base_front + ram_lip_y0 >= 15, '底板前伸出基座（抗前倾）', '前伸 %.1f mm' % (-base_front + ram_lip_y0))
check(base_back - (wall_front_y(0) + (wall_len + plate_t) * math.sin(tilt)) >= 10,
      '底板后缘有富余（抗后倾）', '余量 %.1f mm' % (base_back - (wall_front_y(0) + (wall_len + plate_t) * math.sin(tilt))))

# 7) 镂空
lig_x = P['hex_pitch'] - 2 * P['hex_r']
lig_z = P['hex_pitch'] - 2 * P['hex_r'] * math.cos(math.pi / 6)
hex_x0 = (W - (P['hex_cols'] - 1) * P['hex_pitch']) / 2
hex_rows = int((wall_len - 2 * P['hex_zmargin']) // P['hex_pitch']) + 1
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
s_plat0 = (Zp - P['plat_t'] - P['wall_z0']) / math.cos(tilt)
s_plat1 = (Zp - P['wall_z0']) / math.cos(tilt)
rows_s = [P['hex_zmargin'] + r * P['hex_pitch'] for r in range(hex_rows)]
keep = lambda s: (s + P['hex_r'] < s_plat0 - P['hex_skip']) or (s - P['hex_r'] > s_plat1 + P['hex_skip'])
skipped = [s for s in rows_s if not keep(s)]
overlap = [s for s in rows_s if not (s - P['hex_r'] > s_plat1 + P['hex_skip'] or s + P['hex_r'] < s_plat0 - P['hex_skip'])]
check(skipped == overlap and len(skipped) >= 1 and len(skipped) < hex_rows,
      '台面根部那一条留实心带（不开蜂窝）',
      '台面占斜面 %.1f..%.1f，跳过行 %s，其余 %d 行照开'
      % (s_plat0, s_plat1, [round(s, 1) for s in skipped], hex_rows - len(skipped)))
z_hex_min = P['wall_z0'] + (P['hex_zmargin'] - P['hex_r']) * math.cos(tilt)
check(z_hex_min >= 0, '最低那个蜂窝孔不啃到底板上表面（啃了会在底板里掏出一段内腔）',
      '孔下沿 Z=%.2f ≥ 0（留边 %.0f ≥ 半径 %.0f + %.2f）'
      % (z_hex_min, P['hex_zmargin'], P['hex_r'], -P['wall_z0'] / math.cos(tilt)))
lig_frac = lig_x / P['hex_pitch']
check(root_sigma_MPa / lig_frac < 5, '按蜂窝净截面打折后靠板根部应力仍富余',
      '名义 %.2f ÷ 净料比 %.2f（%.1f/%.0f）= %.2f MPa（PLA 抗弯 ~40MPa；最保守的一刀切在孔心线上）'
      % (root_sigma_MPa, lig_frac, lig_x, P['hex_pitch'], root_sigma_MPa / lig_frac))

# 8) 脚垫 / 名牌位
pads = [(W / 2 - 70, base_front + 9), (W / 2 + 70, base_front + 9),
        (W / 2 - 70, base_back - 9), (W / 2 + 70, base_back - 9)]
edge_min = min(min(x - base_x0, y - base_front, base_x0 + P['base_w'] - x, base_back - y) for x, y in pads)
check(edge_min >= P['foot_d'] / 2 + 1, '四个脚垫坑都在料内（避开圆角）', '坑心最靠边 %.1f ≥ 半径 %.0f + 1' % (edge_min, P['foot_d'] / 2))
check(P['label_d'] + 2 * 4 <= base_d and W - P['label_w'] >= 2 * 6, '名牌凹位放得下', '%.0f x %.0f 凹位，四周留边够' % (P['label_w'], P['label_d']))
label_y0, label_y1 = P['label_y'] - P['label_d'] / 2, P['label_y'] + P['label_d'] / 2
lx0, lx1 = W / 2 - P['label_w'] / 2, W / 2 + P['label_w'] / 2
check(label_y1 <= ram_lip_y0 - 2, '名牌凹位在内存挡边之前（不被挡边压住）',
      '凹位后沿 Y %.1f ≤ 挡边前下角 %.2f - 2' % (label_y1, ram_lip_y0))
check(not any(lx0 < x + P['foot_d'] / 2 and lx1 > x - P['foot_d'] / 2 and
              label_y0 < y + P['foot_d'] / 2 and label_y1 > y - P['foot_d'] / 2 for x, y in pads),
      '名牌凹位不与脚垫坑打架', '凹位 X %.1f..%.1f / Y %.1f..%.1f' % (lx0, lx1, label_y0, label_y1))
check(label_y0 >= base_front + 4, '名牌凹位在底板范围内', '凹位前沿 Y %.1f ≥ 底板前缘 %.0f + 4' % (label_y0, base_front))

# 8b) 底板前部的二次元浮雕（v8：高度场件 import 进底板 union，不是另件嵌槽）
an_w, an_d, an_y, an_bury = P['anime_w'], P['anime_d'], P['anime_y'], P['anime_bury']
an_slab = 2.60                      # 高度场件自带底板厚 = make_depth3d.py --base-mm（件局部 0..2.6 是实心板）
an_max = 4.9622                     # 件最厚处（实测：120x48 深度图件 0.5mm 采样版，最大 Z）
an_x0, an_x1 = (W - an_w) / 2, (W + an_w) / 2
an_y0, an_y1 = an_y - an_d / 2, an_y + an_d / 2
check(P['anime_on'] == 0 or (an_x0 >= base_x0 and an_x1 <= base_x0 + P['base_w']
                             and an_y0 >= base_front and an_y1 <= base_back),
      '浮雕幅面整块落在底板内（并进去的那块在底板范围内）',
      '幅面 X %.2f..%.2f / Y %.2f..%.2f（底板 X %.1f..%.1f / Y %.0f..%.1f）'
      % (an_x0, an_x1, an_y0, an_y1, base_x0, base_x0 + P['base_w'], base_front, base_back))
check(an_w <= W, '浮雕幅面不比架宽宽（不抢架子的戏）', '幅面宽 %.0f ≤ 架宽 %.0f' % (an_w, W))
check(an_bury >= an_slab + 0.02, '件下沿整段埋进底板（不跟底板顶面共面）',
      '沉入 %.2f ≥ 件自带底板 %.2f + 0.02（多埋 %.2f mm 躲开共面布尔）'
      % (an_bury, an_slab, an_bury - an_slab))
check(P['base_t'] - an_bury >= 1.5, '浮雕底下还有实心料（不打穿底板）',
      '底板 %.0f - 沉入 %.2f = %.2f mm ≥ 1.5' % (P['base_t'], an_bury, P['base_t'] - an_bury))
check(P['base_t'] - an_bury - P['foot_deep'] >= 0.6, '浮雕底与脚垫坑之间的余料够（不在同一平面上）',
      '底板 %.0f - 沉入 %.2f - 坑深 %.1f = %.2f mm（脚垫坑 X 在浮雕两侧）'
      % (P['base_t'], an_bury, P['foot_deep'], P['base_t'] - an_bury - P['foot_deep']))
check(abs((an_max - an_bury) - P['anime_top']) < 0.05, '浮雕露出底板面的高度与参数一致',
      '件最厚 %.4f - 沉入 %.2f = %.4f mm（参数 anime_top %.4f）'
      % (an_max, an_bury, an_max - an_bury, P['anime_top']))
check(0.5 <= an_max - an_bury <= 3, '浮雕起伏够看得见、又不算高塔',
      '起伏 %.2f mm（0.1 层高约 %.0f 层；高度场每层截面只缩不涨 → 天然免支撑）'
      % (an_max - an_bury, (an_max - an_bury) / 0.1))
check(an_y1 < ram_lip_y0, '浮雕整片在内存挡边之前（不顶到内存条）',
      '浮雕后沿 Y %.1f < 内存挡边前下角 Y %.1f' % (an_y1, ram_lip_y0))
apron_l, apron_r, apron_f = an_x0 - base_x0, base_x0 + P['base_w'] - an_x1, an_y0 - base_front
check(min(apron_l, apron_r, apron_f) >= 3.5, '浮雕四周留边 ≥3.5mm（边框有料）',
      '左 %.2f / 右 %.2f / 前 %.2f mm' % (apron_l, apron_r, apron_f))
check(label_y0 - an_y1 >= 2, '浮雕不与名牌凹位打架', '浮雕后沿 Y %.2f ≤ 名牌前沿 %.1f - 2' % (an_y1, label_y0))
check(not any(an_x0 < x + P['foot_d'] / 2 and an_x1 > x - P['foot_d'] / 2
              and an_y0 < y + P['foot_d'] / 2 and an_y1 > y - P['foot_d'] / 2 for x, y in pads),
      '浮雕不与脚垫坑打架（脚垫坑在幅面两侧）',
      '幅面 X %.1f..%.1f / Y %.1f..%.1f，坑心 X %s' % (an_x0, an_x1, an_y0, an_y1, [p[0] for p in pads]))

# 9) 受力：重心 / 倾覆门槛 / 强度
check(base_front <= com_y <= base_back and base_x0 <= com_x <= base_x0 + P['base_w'],
      '整机重心投影落在底板内（静置不倒）',
      '重心 (x=%.1f, y=%.1f) ∈ 底板 X[%.1f, %.1f] Y[%.0f, %.1f]，重心高 %.1f mm，估重 %.0f g'
      % (com_x, com_y, base_x0, base_x0 + P['base_w'], base_front, base_back, com_z, tot_kg * 1000))
check(tip_front_N > 1.2, '顶部前推才前倾的门槛够高', '%.2f N（≈%.0f 克力）' % (tip_front_N, tip_front_N / 9.8 * 1000))
check(tip_back_N > 1.2, '后倾门槛也不虚', '%.2f N（≈%.0f 克力）' % (tip_back_N, tip_back_N / 9.8 * 1000))
check(tip_side_N > 3, '侧向最稳（宽底）', '%.2f N 才侧翻' % tip_side_N)
check(ram_com_off > 3 and cpu_com_off > 3, '物件自身不会前翻（重力把件压进靠板）',
      '内存重心比底棱靠后 %.1f mm / CPU %.1f mm —— 力矩朝板里，不吃摩擦' % (ram_com_off, cpu_com_off))
check(root_sigma_MPa < 5, '靠板根部强度富余（PLA 抗弯 ~40MPa）', '根部应力 %.2f MPa，安全系数 >%.0f' % (root_sigma_MPa, 40 / root_sigma_MPa))
check(rib_sigma_MPa < 5, '加强筋强度富余（PLA 抗弯 ~40MPa）', '单筋应力 %.3f MPa，安全系数 >%.0f' % (rib_sigma_MPa, 40 / rib_sigma_MPa))

# 10) 台账同步
led = json.loads(LEDGER.read_text())
idea = next(i for i in led['ideas'] if i['id'] == 'idea-003')
size = idea['dimensions'] or ''
check('%g x %g x %g' % (round(size_x), round(base_d), round(H)) in size, '台账 dimensions 与模型一致', size)
check(idea['openQuestions'] == [], '台账没有僵尸待确认项', str(idea['openQuestions']))

print('\n%s（共 %d 项）' % ('全部通过' if not fails else '有 %d 项不过: %s' % (len(fails), fails), total))
sys.exit(1 if fails else 0)
