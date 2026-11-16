#!/usr/bin/env python3
"""rack.scad 的参数自检：把文件里的数字抽出来，按物理约束逐条算一遍。

只读 rack.scad（+ 台账 print-ideas.json），不改任何文件；全部断言通过才有意义开打。
用法: python3 check.py     # 退出码 0 = 全过
"""
import json, math, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
src = (HERE / 'rack.scad').read_text()
LEDGER = Path.home() / '.cah-data/skills/shared/3d-print-ideas/runtime/print-ideas.json'

def num(name):
    m = re.search(r'^\s*%s\s*=\s*([-0-9.]+)\s*;' % name, src, re.M)
    assert m, 'rack.scad 缺参数 ' + name
    return float(m.group(1))

fails, total = [], 0
def check(ok, label, detail):
    global total
    total += 1
    print(('  ok  ' if ok else ' FAIL ') + label + '  ' + detail)
    if not ok: fails.append(label)

ram_c, cpu_c = int(num('ram_count')), int(num('cpu_count'))
ram_w, cpu_w = num('ram_slot_w'), num('cpu_slot_w')
fin_t, fin_d, fin_h, cham = num('fin_t'), num('fin_d'), num('fin_h'), num('fin_chamfer')
base_t, base_d, base_r = num('base_t'), num('base_d'), num('base_r')
back_t, back_h = num('back_t'), num('back_h')
hex_r, hpx, hpz = num('hex_r'), num('hex_pitch_x'), num('hex_pitch_z')
hex_cols, hex_zmargin = int(num('hex_cols')), num('hex_zmargin')
fh_r, fh_y, fh_z = num('fin_hex_r'), num('fin_hex_y'), num('fin_hex_z')
foot_d, foot_deep = num('foot_d'), num('foot_deep')

slots = [ram_w] * ram_c + [cpu_w] * cpu_c
n = len(slots)
fin_x = [i * fin_t + sum(slots[:i]) for i in range(n + 1)]
comb_w = (n + 1) * fin_t + sum(slots)
W, D, H = comb_w, base_d, back_h + base_t

# 1) 被展示物（带马甲内存 / LGA 裸板，最大的那种）能不能放进去
RAM_L, RAM_H_S, RAM_T = 133.35, 42, 8
CPU_S, CPU_T = 40, 5
check(W <= 250 and D <= 250 and H <= 250, '单件外廓 ≤250³', '%.1f x %.1f x %.1f mm' % (W, D, H))
check(back_h > RAM_L, '内存竖着不露头', '背板 %.0f > 内存 %.2f（富余 %.1f）' % (back_h, RAM_L, back_h - RAM_L))
check(ram_w - RAM_T >= 1.0 and ram_w - RAM_T <= 2.5, '内存槽有间隙但不晃', '槽 %.1f - 厚 %.1f = %.1f mm' % (ram_w, RAM_T, ram_w - RAM_T))
check(cpu_w - CPU_T >= 1.0 and cpu_w - CPU_T <= 2.5, 'CPU 槽有间隙但不晃', '槽 %.1f - 厚 %.1f = %.1f mm' % (cpu_w, CPU_T, cpu_w - CPU_T))
check(fin_d >= RAM_H_S and fin_d >= CPU_S, '槽深容得下物件进深', '槽深 %.0f ≥ max(内存 %.0f, CPU %.0f)' % (fin_d, RAM_H_S, CPU_S))
check(fin_h >= CPU_S, 'CPU 全高被隔片框住', '隔片 %.0f ≥ CPU %.0f' % (fin_h, CPU_S))

# 2) 镂空
lig_x, lig_z = hpx - 2 * hex_r, hpz - 2 * hex_r * math.cos(math.pi / 6)
check(lig_x >= 3 and lig_z >= 3, '背板蜂窝孔间留料 ≥3mm', '横向 %.1f / 纵向 %.1f mm' % (lig_x, lig_z))
hex_x0 = (comb_w - (hex_cols - 1) * hpx) / 2
hex_rows = int((back_h - 2 * hex_zmargin) // hpz) + 1
row_x = [hex_x0 + c * hpx for c in range(hex_cols)]                       # 偶数行孔心
row_x_odd = [hex_x0 + hpx / 2 + c * hpx for c in range(hex_cols - 1)]     # 奇数行孔心
xmin, xmax = min(row_x[0], row_x_odd[0]) - hex_r, max(row_x[-1], row_x_odd[-1]) + hex_r
zmax = hex_zmargin + (hex_rows - 1) * hpz + hex_r
check(xmin >= 3 and xmax <= comb_w - 3, '蜂窝不啃边', '最左 %.1f 最右 %.1f（板宽 %.1f）' % (xmin, xmax, comb_w))
check(zmax <= back_h - 3, '蜂窝不啃顶', '最高 %.1f ≤ %.1f' % (zmax, back_h - 3))
check(abs(((row_x[0] + row_x[-1]) / 2) - comb_w / 2) < 0.01 and abs(((row_x_odd[0] + row_x_odd[-1]) / 2) - comb_w / 2) < 0.01,
      '蜂窝整排居中', '偶数行中心 %.2f / 奇数行中心 %.2f / 板中 %.2f' % ((row_x[0] + row_x[-1]) / 2, (row_x_odd[0] + row_x_odd[-1]) / 2, comb_w / 2))
check(fh_z - fh_r > 0 and fh_y - fh_r > 0 and fh_y + fh_r < fin_d, '隔片减重孔在料里',
      'y %.0f±%.0f ⊆ (0, %.0f)，z %.0f±%.0f > 0' % (fh_y, fh_r, fin_d, fh_z, fh_r))
check(fh_z + fh_r < fin_h - cham, '隔片减重孔避开斜切区', 'z 顶 %.1f < 斜切起点 %.1f' % (fh_z + fh_r, fin_h - cham))

# 3) 自立 / 打印
inset = foot_d / 2 + 5
check(inset - base_r > 0, '脚垫坑在圆角料内', 'inset %.1f - 圆角 %.1f = %.1f mm' % (inset, base_r, inset - base_r))
check(base_d >= H * 0.45, '抗倾倒进深', '底板进深 %.0f / 总高 %.0f = %.2f' % (base_d, H, base_d / H))
check(base_t >= 6, '底板够厚压重心', '底板厚 %.0f mm' % base_t)

# 4) 台账同步
led = json.loads(LEDGER.read_text())
idea = next(i for i in led['ideas'] if i['id'] == 'idea-003')
size = idea['dimensions'] or ''
check('%g x %g x %g' % (W, D, H) in size, '台账 dimensions 与模型一致', size)
check(idea['openQuestions'] == [], '台账没有僵尸待确认项', str(idea['openQuestions']))

print('\n%s（共 %d 项）' % ('全部通过' if not fails else '有 %d 项不过: %s' % (len(fails), fails), total))
sys.exit(1 if fails else 0)
