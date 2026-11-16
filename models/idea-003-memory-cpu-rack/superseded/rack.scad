// =============================================================================
// idea-003 内存条 + CPU 展示架 —— 竖直单排梳齿式自立架（单件打印，不靠墙）
//
// 结构：一块底板 + 一排竖直隔片（梳齿，7 个槽）+ 后缘背板当脊。
//       每片隔片中间贯穿一个六边形减重孔，背板做蜂窝孔阵列 —— 这就是装饰性镂空。
//       4 根内存条竖着插进前 4 个槽，3 颗 CPU 竖着插进后 3 个槽，
//       物件是被两侧隔片「框」住的，不夹、不压金手指（槽宽留 1.5mm 总间隙）。
//       背板与底板做蜂窝镂空减重，其余实心保证自立稳定。
//
// 硬约束：单件外廓 ≤ 250 x 250 x 250mm（主人：打印机长宽高都在 25cm 以内）
//         外廓 = 89.5 x 80 x 163mm（见下方 derive 段，脚本复算过）
// 打印注意：全部竖直面，无需支撑；层高 0.2；PLA/PETG 均可；
//           墙厚 ≥3 层；填充 15~20%（底板实心更好压重心）。
//
// 改动入口：只改下面「参数」段的数字，derive 段与几何全部跟着走。
// =============================================================================

// ---------- 参数：被展示物（当前 4 内存 + 3 CPU，要加位改这两个数） ----------
ram_count  = 4;
cpu_count  = 3;
ram_slot_w = 9.5;   // 兼容带金属马甲的内存（板厚约 8mm，总间隙 1.5mm）
cpu_slot_w = 6.5;   // LGA/PGA 裸板厚约 5mm，总间隙 1.5mm

slots = concat([for (i = [0 : ram_count - 1]) ram_slot_w],
               [for (i = [0 : cpu_count - 1]) cpu_slot_w]);

// ---------- 参数：结构 ----------
fin_t       = 4;    // 隔片厚（首尾两片同时充当外侧壁）
fin_d       = 75;   // 隔片进深（= 底板进深 - 背板厚，直接熔接进背板）
fin_h       = 60;   // 隔片高（撑住内存下段 60mm，CPU 40mm 全高被完全框住）
fin_chamfer = 10;   // 隔片前上角斜切，方便竖着往下插物件
base_t      = 8;    // 底板厚
base_d      = 80;   // 底板进深（重心靠后，向后倒的力臂 = 80mm）
base_r      = 8;    // 底板四角圆角
back_t      = 5;    // 背板厚
back_h      = 155;  // 背板高（底板面以上；内存高 133mm，上方留 22mm）
hex_r       = 6;    // 背板蜂窝孔外接圆半径
hex_pitch_x = 15;   // 蜂窝横向间距（孔间剩 3mm 料）
hex_pitch_z = 15;   // 蜂窝纵向行距（孔间剩 4.6mm 料）
hex_cols    = 5;    // 偶数行孔数；奇数行 4 个 + 半格错开，整排始终居中
hex_zmargin = 15;   // 蜂窝孔离背板上下边缘留边
fin_hex_r   = 7;    // 隔片减重孔外接圆半径（六边形，穿 fin_t 厚度）
fin_hex_y   = 22;   // 隔片减重孔中心：离前缘 22mm
fin_hex_z   = 28;   // 隔片减重孔中心：离底板面 28mm
foot_d      = 12;   // 防滑脚垫坑直径（贴 3M 硅胶垫）
foot_deep   = 1.5;  // 脚垫坑深

// ---------- derive：全部尺寸从上面推，别手改 ----------
n = len(slots);

function sum_first(list, cnt, i = 0, acc = 0) =
    i >= cnt ? acc : sum_first(list, cnt, i + 1, acc + list[i]);

slot_sum = sum_first(slots, n);
comb_w   = (n + 1) * fin_t + slot_sum;          // 梳齿总宽 = 底板宽 = 背板宽
fin_x(i) = i * fin_t + sum_first(slots, i);     // 第 i 片隔片左边缘 X（i 取 0..n）

hex_x0   = (comb_w - (hex_cols - 1) * hex_pitch_x) / 2;   // 偶数行首孔中心 X（整排左右居中）
hex_rows = floor((back_h - 2 * hex_zmargin) / hex_pitch_z) + 1;   // 偶数行行数 = 总行数一半（取整）
hex_count = ceil(hex_rows / 2) * hex_cols + floor(hex_rows / 2) * (hex_cols - 1);

// ---------- 几何 ----------
module base_plate() {
  translate([0, 0, -base_t])
    linear_extrude(base_t)
      offset(r = base_r) square([comb_w - 2 * base_r, base_d - 2 * base_r]);
}

module foot_pockets() {
  inset = foot_d / 2 + 5;
  for (p = [[inset, inset], [comb_w - inset, inset],
            [inset, base_d - inset], [comb_w - inset, base_d - inset]])
    translate([p[0], p[1], -base_t - 0.01])
      cylinder(d = foot_d, h = foot_deep + 0.01, $fn = 32);
}

module fin(i) {
  translate([fin_x(i) + fin_t, 0, 0])
    difference() {
      // 轮廓画在 XY（X = 进深, Y = 高度），挤出 fin_t 当厚度，再摆到 X = 厚度 / Z = 高度
      rotate([0, 0, 90])
        rotate([-90, 0, 0])
          linear_extrude(fin_t)
            polygon([[0, -base_t], [fin_d, -base_t],
                     [fin_d, fin_h], [fin_chamfer, fin_h], [0, fin_h - fin_chamfer]]);
      // 隔片减重孔：六边形沿 X 贯穿 fin_t
      translate([-fin_t - 1, fin_hex_y, fin_hex_z])
        rotate([0, 90, 0]) cylinder(r = fin_hex_r, h = fin_t + 2, $fn = 6);
    }
}

module back_panel() {
  translate([0, base_d - back_t, -base_t]) cube([comb_w, back_t, back_h + base_t]);
}

module hex_cutouts() {
  for (r = [0 : hex_rows - 1]) {
    z = hex_zmargin + r * hex_pitch_z;
    cols = (r % 2 == 0) ? hex_cols : hex_cols - 1;   // 奇数行少一个 + 错半格 → 整排仍居中
    xoff = (r % 2 == 0) ? 0 : hex_pitch_x / 2;
    for (c = [0 : cols - 1]) {
      x = hex_x0 + xoff + c * hex_pitch_x;
      translate([x, base_d - back_t - 1, z])
        rotate([-90, 0, 0]) cylinder(r = hex_r, h = back_t + 2, $fn = 6);
    }
  }
}

module display_rack() {
  difference() {
    union() {
      base_plate();
      back_panel();
      for (i = [0 : n]) fin(i);
    }
    foot_pockets();
    hex_cutouts();
  }
}

display_rack();

// ---------- 自检输出（openscad -o /dev/null 后在控制台看） ----------
echo(str("槽位数 = ", n, "（内存 ", ram_count, " + CPU ", cpu_count, "）"));
echo(str("外廓 = ", comb_w, " x ", base_d, " x ", back_h + base_t, " mm"));
echo(str("隔片 X 起点 = ", [for (i = [0 : n]) fin_x(i)]));
echo(str("蜂窝孔 = ", hex_count, " 个（", hex_rows, " 行：偶数行 ", hex_cols, " 个，奇数行 ", hex_cols - 1, " 个）"));
echo(str("隔片减重孔 = ", n + 1, " 个（每片隔片 1 个，r=", fin_hex_r, "）"));
