// =============================================================================
// idea-003 内存条 + CPU 展示架 —— 后仰斜靠式（正面朝外，全靠重力）
//
// 受力结构（为什么不会被推倒、东西也不会翻）：
//   1) 每件东西是坐进「靠板前表面 + 台面/底板」的直角角里 —— 背面整面贴着靠板，
//      底边那条棱压在水平的台面上。不是悬空靠摩擦。
//   2) 重力：物件重量 → 台面/底板（受压），物件的重心投影落在底边棱的「靠板一侧」，
//      所以力矩是把物件往靠板里压，不可能往前翻。
//   3) 水平推力：物件压靠板 → 靠板根部（埋在台面/底板里）→ 底板受剪，力回到同一块底板。
//   4) 整机抗前倾：底板前缘再往观众方向伸出 base_front(负值) 当基座，重心投影离前缘
//      还有 60mm 以上，比只有物件区时抗推一倍多。
//
// 一句结构：一块底板 + 两级「斜靠面」，东西往里一放、自己靠着不倒：
//   后排高一级：4 根内存竖着斜靠，正面（标签那面）朝外；底面坐在台面上，
//               前缘有挡边，两侧 5 片分隔牙把 4 根分开，牙的背面贴着背板所以不晃
//   前排低一级：3 颗 CPU 同样斜靠，IHS（印字那面）朝外，直接坐在底板上
//   背板开蜂窝孔减重兼装饰（背面、侧上方看得见）
//
// 为什么分两级：一根内存竖着正面朝外要占 ~42mm 宽，4 根 ≈ 183mm；3 颗 CPU 再要
//   138mm —— 平铺一排 330mm 装不进 250mm 的机器，所以后排内存、前排 CPU 错开一层，
//   整体 191 x 84 x 198mm，单件成型。
//
// 硬约束：单件外廓 ≤250x250x250mm（主人：打印机长宽高都在 25cm 以内）
// 打印注意：所有斜面最斜只到 15°（远小于 45°），全局免支撑；层高 0.2，PLA/PETG 均可。
// 改动入口：只改下面「参数」，derive 段与几何全跟着走。
// =============================================================================

// ---------- 参数：要架的东西（按手头实物改） ----------
ram_n      = 4;      // 内存条数
ram_w      = 42;     // 内存宽度（竖放时占的横向宽度）：带金属马甲 42 / 裸条 31
ram_thick  = 8;      // 内存厚度：带马甲 8 / 裸条 2
ram_len    = 133.35; // 内存长度（竖起来的高度）
cpu_n      = 3;      // CPU 颗数
cpu_w      = 40;     // CPU 边长
cpu_thick  = 5;      // CPU 厚度（含 IHS）

// ---------- 参数：结构 ----------
tilt       = 15;     // 后仰角（与竖直方向夹角）。tan15=0.27 接近 PCB/PLA 摩擦系数，
                     // 所以每级都有前缘挡边兜底，不靠摩擦独扛
W          = ram_n * (ram_w + 2) + (ram_n + 1) * 3;  // 架宽（内存位净宽 = ram_w + 2）
base_t     = 6;      // 底板厚
base_front = -20;    // 底板前缘 Y（0 = 物件区前界；负值 = 再往观众方向伸一段当基座）
base_back_margin = 5;// 底板后缘比后仰的背板顶端再留的余量
base_r     = 8;      // 底板四角圆角
label_w    = 120;    // 基座上的名牌凹位宽（贴型号标签用）
label_d    = 12;     // 名牌凹位进深
label_deep = 1;      // 名牌凹位深度（凹进底板面）
label_y    = 8;      // 名牌凹位中心 Y
plate_t    = 4;      // 斜靠板厚（垂直板面量）
Zp         = 45;     // 内存那一级的台面高度
plat_y0    = 23;     // 台面前缘 Y
plat_d     = 16;     // 台面进深
plat_t     = 4;      // 台面厚
tine_t     = 3;      // 分隔牙厚
ram_tine_d = 18;     // 内存牙从背板前表面向前伸出的深度
ram_tine_h = 50;     // 内存牙沿斜面高度
cpu_tine_d = 7;      // CPU 牙伸出深度
cpu_tine_h = 32;     // CPU 牙高度
lip_t      = 3;      // 前缘挡边厚
lip_h      = 8;      // 前缘挡边高（沿斜面）
lip_gap    = 1;      // 挡边与物件前表面的间隙
hex_r      = 6;      // 背板蜂窝孔外接圆半径
hex_pitch  = 18;     // 蜂窝间距（孔间留 6mm 料）
hex_cols   = 9;      // 偶数行孔数；奇数行 8 个错半格，整排仍居中
hex_zmargin = 15;    // 蜂窝离背板上下端留边
wall_len   = 155;    // 背板沿斜面长度（内存 133.35 上端还富余 15+）
foot_d     = 12;     // 防滑脚垫坑直径
foot_deep  = 1.5;    // 脚垫坑深

// ---------- derive：尺寸全从上面算，别手改 ----------
ram_cw     = ram_w + 2;                       // 内存位净宽
cpu_cw     = cpu_w + 2;                       // CPU 位净宽
ram_tines  = ram_n + 1;                       // 5
cpu_tines  = cpu_n + 1;                       // 4
ram_row_w  = ram_n * ram_cw + ram_tines * tine_t;   // = W
cpu_row_w  = cpu_n * cpu_cw + cpu_tines * tine_t;   // 138
cpu_row_x0 = (W - cpu_row_w) / 2;                   // 前排整体居中
ram_row_x0 = 0;

wall_z0    = Zp - 3;                          // 背板下端埋进台面 3mm
wall_y_at_Zp = plat_y0 + plat_d - 4;          // 背板前表面在台面高度处的 Y
wall_y0    = wall_y_at_Zp - (Zp - wall_z0) * tan(tilt);

cpu_plate_z0  = -2;                           // CPU 斜靠板下端埋进底板 2mm
cpu_plate_len = (Zp - cpu_plate_z0) / cos(tilt);
cpu_plate_y0  = plat_y0 - cpu_plate_len * sin(tilt);  // 上端正好落在台面前缘

// 底板前后缘由背板位置倒推：后缘盖住后仰的背板顶，前缘留一段基座（抗前倾 + 放名牌）
base_back = wall_y0 + (wall_len + plate_t) * sin(tilt) + base_back_margin;
base_d    = base_back - base_front;
foot_in   = 9;                                // 脚垫坑心离底板边缘

// 沿斜面/法线的位移分量
function up_y(d)  =  d * sin(tilt);           // 沿斜面往上
function up_z(d)  =  d * cos(tilt);
function fwd_y(d) = -d * cos(tilt);           // 垂直板面往观众方向
function fwd_z(d) =  d * sin(tilt);

// 第 i 条内存位 / CPU 位的中心 X（位 = 牙与牙之间）
function ram_slot_x(i) = (i + 1) * tine_t + i * ram_cw + ram_cw / 2;
function cpu_slot_x(i) = cpu_row_x0 + (i + 1) * tine_t + i * cpu_cw + cpu_cw / 2;

// CPU 斜靠板前表面上的点：s = 沿斜面从下端起的长度
function cpu_plate_point(s) = [cpu_plate_y0 + up_y(s), cpu_plate_z0 + up_z(s)];

// ---------- 几何 ----------
// 斜靠板/牙/挡边：局部 X = 宽，局部 y = 板厚方向（0 = 前表面），局部 z = 沿斜面
module leaning_slab(w, depth, len, y0, z0) {
  translate([0, y0, z0]) rotate([-tilt, 0, 0]) cube([w, depth, len]);
}

// 分隔牙：背面贴靠板前表面（点 y_back/z_back 在靠板前表面上），向前伸 depth、向上高 len
module tine(x_center, wid, depth, len, y_back, z_back, floor_z) {
  extend = 12;                                  // 沿斜面往下的富余，供底面切平
  y_edge = y_back + fwd_y(depth);               // 牙的前下角落点
  z_edge = z_back + fwd_z(depth);
  translate([x_center - wid / 2, 0, 0])
    difference() {
      leaning_slab(wid, depth, len + extend,
                   y_edge - up_y(extend), z_edge - up_z(extend));
      translate([-5, -250, floor_z - 0.5 - 250]) cube([wid + 10, 500, 250]);
    }
}

module back_wall() {
  leaning_slab(W, plate_t, wall_len, wall_y0, wall_z0);
}

module cpu_plate() {
  leaning_slab(W, plate_t, cpu_plate_len, cpu_plate_y0, cpu_plate_z0);
}

module ram_platform() {
  translate([0, plat_y0, Zp - plat_t]) cube([W, plat_d, plat_t]);
}

module ram_tines() {
  for (i = [0 : ram_tines - 1]) {
    xc = ram_row_x0 + i * (ram_cw + tine_t) + tine_t / 2;
    tine(xc, tine_t, ram_tine_d, ram_tine_h, wall_y_at_Zp, Zp, Zp);
  }
}

module cpu_tines() {
  p = cpu_plate_point(0);
  for (i = [0 : cpu_tines - 1]) {
    xc = cpu_row_x0 + i * (cpu_cw + tine_t) + tine_t / 2;
    tine(xc, tine_t, cpu_tine_d, cpu_tine_h, p[0], p[1], 0);
  }
}

module ram_lips() {
  for (i = [0 : ram_n - 1]) {
    xc = ram_slot_x(i);
    translate([xc - ram_cw / 2, 0, 0]) leaning_slab(ram_cw, lip_t, lip_h, plat_y0, Zp);
  }
}

module cpu_lips() {
  y0 = cpu_plate_y0 + fwd_y(cpu_thick + lip_gap + lip_t);   // 挡边前下角
  for (i = [0 : cpu_n - 1]) {
    xc = cpu_slot_x(i);
    translate([xc - cpu_cw / 2, 0, 0]) leaning_slab(cpu_cw, lip_t, lip_h, y0, 0);
  }
}

module base_plate() {
  translate([base_r, base_front + base_r, -base_t])
    linear_extrude(base_t)
      offset(r = base_r) square([W - 2 * base_r, base_d - 2 * base_r]);
}

module foot_pockets() {
  for (x = [W / 2 - 70, W / 2 + 70])
    for (y = [base_front + foot_in, base_back - foot_in])
      translate([x, y, -base_t - 0.01]) cylinder(d = foot_d, h = foot_deep + 0.01, $fn = 32);
}

module label_pocket() {
  // 基座面上 1mm 浅凹：贴「DDR4 3200 16G / i5-12400」这类名牌
  translate([W / 2 - label_w / 2, label_y - label_d / 2, -label_deep])
    cube([label_w, label_d, label_deep]);
}

module wall_hexes() {
  hex_rows = floor((wall_len - 2 * hex_zmargin) / hex_pitch) + 1;
  hex_x0   = (W - (hex_cols - 1) * hex_pitch) / 2;
  for (r = [0 : hex_rows - 1]) {
    s = hex_zmargin + r * hex_pitch;
    cols = (r % 2 == 0) ? hex_cols : hex_cols - 1;
    xoff = (r % 2 == 0) ? 0 : hex_pitch / 2;
    for (c = [0 : cols - 1]) {
      x = hex_x0 + xoff + c * hex_pitch;
      translate([x, wall_y0, wall_z0]) rotate([-tilt, 0, 0])
        translate([0, -1, s]) rotate([-90, 0, 0])
          cylinder(r = hex_r, h = plate_t + 2, $fn = 6);
    }
  }
}

module rack() {
  difference() {
    union() {
      base_plate();
      back_wall();
      cpu_plate();
      ram_platform();
      ram_tines();
      cpu_tines();
      ram_lips();
      cpu_lips();
    }
    foot_pockets();
    label_pocket();
    wall_hexes();
  }
}

rack();

// ---------- 自检输出（openscad -o /dev/null 后在控制台看） ----------
hex_rows_total = floor((wall_len - 2 * hex_zmargin) / hex_pitch) + 1;
ram_top_z  = Zp + ram_len * cos(tilt);
wall_top_z = wall_z0 + wall_len * cos(tilt);
echo(str("外廓 = ", W, " x ", base_d, " x ", base_t + wall_top_z, " mm（底板 Y ", base_front, " .. ", base_back, "）"));
echo(str("内存位净宽 = ", ram_cw, "（架宽 ", ram_w, "，余 ", ram_cw - ram_w, "）; CPU 位净宽 = ", cpu_cw, "（余 ", cpu_cw - cpu_w, "）"));
echo(str("前排 X 起点 = ", cpu_row_x0, "，内存位中心 = ", [for (i = [0 : ram_n - 1]) ram_slot_x(i)]));
echo(str("背板前表面底端 Y = ", wall_y0, "，板顶 Y = ", wall_y0 + (wall_len + plate_t) * sin(tilt)));
echo(str("内存顶 Z = ", ram_top_z, "，背板顶 Z = ", wall_top_z, "（高出内存 ", wall_top_z - ram_top_z, "）"));
echo(str("蜂窝孔 = ", ceil(hex_rows_total / 2) * hex_cols + floor(hex_rows_total / 2) * (hex_cols - 1), " 个（", hex_rows_total, " 行）"));
