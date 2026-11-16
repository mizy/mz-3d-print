// =============================================================================
// idea-003 内存条 + CPU 展示架 —— v8 后仰斜靠式（正面朝外，全靠重力）+ 浮雕直接长在底板前部
//
// v8 相对 v7 的一处改动（主人 9/29「直接浮雕刻在这个架子上」）：
//   浮雕不再另出一件 + 开槽，直接长在底板上：把 make_depth3d.py 出的高度场件 import 进来，
//   件底沉到 Z=-anime_bury（2.65 = 件底板 2.60 + 0.05 防共面），union 进底板。
//   件下沿那 2.65mm 落在底板内部，露出来的只有起伏那 2.31mm —— 看起来就是「底板上刻出来的人」。
//   换掉 v7 的「嵌槽 + 嵌片」：少了 0.15 装配间隙、少了拼装、也不用担心嵌片色差；
//   代价是不能再单独换色/换件（一件打完），浮雕的层高跟架子一致。
//   高度场件用 0.5mm 采样版（--sample-mm 0.5）：0.4 喷嘴看不出差别，
//   而 CGAL 布尔量从 19 万面降到 9.4 万面（0.35 版 union 要跑 1 分 40 秒，0.5 版几秒）。
//
// v7 相对 v6 的两处改动（主人 9/29「嵌片可以换成深度图版」）：
//   1) 嵌片换成深度图版：豆包正面深度图（2.5:1 横构图）→ make_depth3d.py 灰度直接拉高度，
//      成品 120 x 48 x 4.97mm（v6 那版是 120x61 的剪影浮雕，源图侧躺构图、看着「不是正对的」）。
//      底板前缘跟着从 -85 收到 -72；「名牌凹位→嵌槽」留边 3.35、「嵌槽→底板前缘」留边 8.35 都不变。
//   2) 嵌槽补上几何：v5/v6 只在参数区写了 anime_* 并画进 preview/check，但 rack() 里从没开过槽
//      —— 编译出的 STL 底板前部一直是整片平面。v7 新增 anime_pocket() 并挂进 rack()。
//      （v7 的嵌槽版文件仍留在目录里当备选；v8 起浮雕是长在底板上的，没有嵌片。）
//
// v5 相对 v3 的一处改动（主人 9/29 提）：
//   4) 底板往前伸出一块「浮雕嵌槽」：120x61 的浅槽开在底板面上（深 2.7），
//      嵌一块单独的二次元浮雕片（背板厚 2.6，单边留 0.15 装配间隙，片顶比底板面低 0.1）。
//      为什么放这里：底板前部是整个架子唯一「正面一直看得见 + 能平躺打印 + 不挡内存条」的面。
//      背板背面虽然更大（191x190）但朝后看不见、下半段还被加强筋占着；
//      带倾角的前立板会把内存条下沿挡掉。浮雕片单独一件 → 能单独用最细层高/另一种颜色，
//      也能粘死当一体件。底板前缘 Y 从 -20 伸到 -100（外廓 200 x 183 x 187）。
//
// v3 相对 v2 的三处改动（主人 9/28 提的三条）：
//   1) CPU 挪到内存条上面：内存条坐底板（下层），CPU 坐 Zp 高的台面（上层）；
//      正面朝外 + 后仰 15° 斜靠的受力方式不变，只是两级上下对调。
//   2) 背部加两道加强筋：贴背板背面从底板一直到 rib_h 高，底部往后伸 rib_reach_bot、
//      往上收到 rib_reach_top —— 把「物件→靠板→底板」这条链在背部连成一体，
//      背板不再是一块从上到下悬空的薄板。
//   3) 两侧隔板收短：内存分隔牙从 v2 的 18x50 收到 ram_tine_d x ram_tine_h，
//      只比内存前表面凸出一点、高度也压到只够分开相邻内存条；CPU 牙同步收短。
//
// 结构（一句）：一块底板 + 一块后仰 15° 的背板；背板前面上下两级斜靠面：
//   下层（底板面 Z=0）：ram_n 根内存竖着斜靠，标签面朝外；底棱坐底板、前缘有挡边、
//                        两侧短牙把相邻两根分开
//   上层（Z=Zp 台面）  ：cpu_n 颗 CPU 同样斜靠，IHS 面朝外；台面从背板前面往前伸
//                        （plat_d-4），后 4mm 埋进背板当根部
// 受力：每件背整面贴靠板、底棱压水平面 → 坐进直角角，重力把它压进板里，不吃摩擦；
//       背板根部埋进底板，两道加强筋把背板中上段的弯矩传回底板 → 全回到同一块底板。
//
// 硬约束：单件外廓 ≤250x250x250mm（主人：打印机长宽高都在 25cm 以内）
// 打印注意：最斜面 15°（远小于 45° 悬垂线）；加强筋是竖直薄片（两片大面垂直于平台），
//          蜂窝孔只在背板内开、不啃前表面 → 全局免支撑。
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
tine_t     = 3;      // 分隔牙厚

ram_tine_d = 12;     // 内存牙从背板前表面向前伸出的深度（内存厚 8 → 只凸出 4）
ram_tine_h = 16;     // 内存牙沿斜面的高度（只够分开相邻两根，不再当隔墙）
cpu_tine_d = 6;      // CPU 牙伸出深度（CPU 厚 5 → 只凸出 1）
cpu_tine_h = 22;     // CPU 牙沿斜面的高度

lip_t      = 3;      // 前缘挡边厚
lip_h      = 8;      // 前缘挡边高（沿斜面）
lip_gap    = 1;      // 挡边与物件前表面的间隙

wall_y0    = 14;     // 背板前表面在底板顶面（Z=0）处的 Y
wall_z0    = -3;     // 背板下端埋进底板 3mm（保证根部是实心连接）
wall_len   = 190;    // 背板沿斜面长度（上端高出 CPU 最高点 ~2.6mm）
plate_t    = 4;      // 背板/台面厚（垂直板面量）

Zp         = 138;    // CPU 一级台面高度（内存最高点 130.9 之上 3.1mm）
plat_d     = 16;     // 台面进深
plat_embed = 2.5;    // 台面后缘埋进背板的深度（必须整条落在背板后表面之内）
plat_t     = 4;      // 台面厚

base_t     = 6;      // 底板厚
base_w     = 196;    // 底板宽（比物件区 191 每边宽 2.5mm，抗侧翻；v6 从 200 收到 196 省料）
base_front = -72;    // 底板前缘 Y（0 = 内存挡边附近；负值 = 往观众方向伸一段当基座）
                     // v5 -100 → v6 -85 → v7 -72（嵌片缩到 120x48，前缘跟着收）
base_back_margin = 18; // 底板后缘比后仰的背板顶端再留的余量（抗后翻）
base_r     = 8;      // 底板四角圆角
label_w    = 120;    // 基座上的名牌凹位宽（贴型号标签用）
label_d    = 12;     // 名牌凹位进深
label_deep = 1;      // 名牌凹位深度（凹进底板面）
label_y    = -6;     // 名牌凹位中心 Y（放在内存挡边之前的空基座上）

// ---------- 参数：底板前部的二次元浮雕（浮雕直接长在底板上，v8） ----------
anime_on    = 1;     // 是否把浮雕做进底板（0 = 光板；用数字，model.py 只解析数字）
anime_w     = 120;   // 浮雕幅面宽 X（= 深度图件成品宽 120.00；源图 2.5:1）
anime_d     = 48;    // 浮雕幅面进深 Y
anime_y     = -39.5; // 浮雕中心 Y（后沿距名牌凹位 3.5mm、前沿距底板前缘 8.5mm）
anime_bury  = 2.65;  // 高度场件沉进底板的深度 = 件自身底板 2.60 + 0.05（防共面布尔）
anime_top   = 2.3122;// 参考：浮雕最高点露出底板面多高（= 件最厚 4.9622 - 沉入 2.65）
anime_stl   = "anime-relief/miao-anime-depth-120x48-emboss.stl";  // make_depth3d.py 出的高度场件（相对本目录）

hex_r      = 10;     // 背板蜂窝孔外接圆半径（v6：6→10，孔大了料少了）
hex_pitch  = 26;     // 蜂窝间距（孔间留 6mm 料）
hex_cols   = 7;      // 偶数行孔数；奇数行 6 个错半格，整排仍居中（v6：9→7）
hex_zmargin = 14;    // 蜂窝离背板下端的留边（≥ r + 3/cos(tilt)，最低那个孔不许啃到底板上表面）
hex_skip   = 3;      // 与台面根部重叠的行跳过（台面根部留一条实心带）

rib_t        = 4;    // 加强筋厚（竖直薄片，两片大面垂直于平台）
rib_x_off    = 70;   // 加强筋中心离板中（两道对称）
rib_reach_bot = 20;  // 加强筋底部往后伸出的深度
rib_reach_top = 8;   // 加强筋顶部往后伸出的深度
rib_h        = 118;  // 加强筋沿竖直方向的高度
rib_overlap  = 1;    // 加强筋前端压进背板的深度（避免共面布尔）

foot_d     = 12;     // 防滑脚垫坑直径
foot_deep  = 1.5;    // 脚垫坑深

// ---------- derive：尺寸全从上面算，别手改 ----------
ram_cw     = ram_w + 2;                       // 内存位净宽 44
cpu_cw     = cpu_w + 2;                       // CPU 位净宽 42
ram_tines  = ram_n + 1;                        // 5
cpu_tines  = cpu_n + 1;                        // 4
W          = ram_n * ram_cw + ram_tines * tine_t;   // 架宽 191
cpu_row_w  = cpu_n * cpu_cw + cpu_tines * tine_t;   // 138
cpu_row_x0 = (W - cpu_row_w) / 2;                    // CPU 一排整体居中
base_x0    = (W - base_w) / 2;                       // 底板比物件区每边宽出来

// 沿斜面/法线的位移分量
function up_y(d)  =  d * sin(tilt);           // 沿斜面往上
function up_z(d)  =  d * cos(tilt);
function fwd_y(d) = -d * cos(tilt);           // 垂直板面往观众方向
function fwd_z(d) =  d * sin(tilt);

// 背板前/后表面（后表面 = 前表面沿法线推 plate_t）
function wall_front_y(z) = wall_y0 + (z - wall_z0) * tan(tilt);
function wall_back_y(z)  = wall_front_y(z) + plate_t / cos(tilt);

ram_butt_y = wall_front_y(0);                 // 内存底棱落点（背板前表面 Z=0 处）
cpu_butt_y = wall_front_y(Zp);                // CPU 底棱落点（背板前表面 Z=Zp 处）
plat_y0    = cpu_butt_y - (plat_d - plat_embed);  // 台面前缘（后缘埋进背板 plat_embed）
base_back  = wall_front_y(0) + (wall_len + plate_t) * sin(tilt) + base_back_margin;
base_d     = base_back - base_front;
wall_top_z = wall_z0 + wall_len * cos(tilt);

ram_top_z  = ram_len * cos(tilt) + ram_thick * sin(tilt);   // 内存最高点（前上角）
cpu_top_z  = Zp + cpu_w * cos(tilt) + cpu_thick * sin(tilt); // CPU 最高点（前上角）
ram_lip_y0 = ram_butt_y + fwd_y(ram_thick) - lip_gap - lip_t * cos(tilt);
cpu_lip_y0 = cpu_butt_y + fwd_y(cpu_thick) - lip_gap - lip_t * cos(tilt);
foot_in    = 9;                               // 脚垫坑心离底板边缘

// 第 i 条内存位 / CPU 位的中心 X（位 = 牙与牙之间）
function ram_slot_x(i) = (i + 1) * tine_t + i * ram_cw + ram_cw / 2;
function cpu_slot_x(i) = cpu_row_x0 + (i + 1) * tine_t + i * cpu_cw + cpu_cw / 2;

// ---------- 几何 ----------
// 斜靠板/牙/挡边：局部 X = 宽，局部 y = 板厚方向（+y 垂直板面往板里），局部 z = 沿斜面
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

module cpu_platform() {
  translate([0, plat_y0, Zp - plat_t]) cube([W, plat_d, plat_t]);
}

module ram_tines() {
  for (i = [0 : ram_tines - 1]) {
    xc = i * (ram_cw + tine_t) + tine_t / 2;
    tine(xc, tine_t, ram_tine_d, ram_tine_h, ram_butt_y, 0, -2);
  }
}

module cpu_tines() {
  for (i = [0 : cpu_tines - 1]) {
    xc = cpu_row_x0 + i * (cpu_cw + tine_t) + tine_t / 2;
    tine(xc, tine_t, cpu_tine_d, cpu_tine_h, cpu_butt_y, Zp, Zp - 2);
  }
}

module ram_lips() {
  for (i = [0 : ram_n - 1]) {
    xc = ram_slot_x(i);
    translate([xc - ram_cw / 2, 0, 0]) leaning_slab(ram_cw, lip_t, lip_h, ram_lip_y0, 0);
  }
}

module cpu_lips() {
  for (i = [0 : cpu_n - 1]) {
    xc = cpu_slot_x(i);
    translate([xc - cpu_cw / 2, 0, 0]) leaning_slab(cpu_cw, lip_t, lip_h, cpu_lip_y0, Zp);
  }
}

// 两道加强筋：贴背板背面，底部伸 rib_reach_bot、顶部收到 rib_reach_top
module ribs() {
  // 筋的前端往背板里压 rib_overlap，避免与背板背面共面（共面布尔会出非流形边）
  for (xc = [W / 2 - rib_x_off, W / 2 + rib_x_off]) {
    hull() {
      translate([xc - rib_t / 2, wall_back_y(0) + fwd_y(rib_overlap), fwd_z(rib_overlap)])
        rotate([-tilt, 0, 0]) cube([rib_t, rib_reach_bot + rib_overlap, 1]);
      translate([xc - rib_t / 2, wall_back_y(rib_h) + fwd_y(rib_overlap), rib_h + fwd_z(rib_overlap)])
        rotate([-tilt, 0, 0]) cube([rib_t, rib_reach_top + rib_overlap, 1]);
    }
  }
}

module base_plate() {
  translate([base_x0 + base_r, base_front + base_r, -base_t])
    linear_extrude(base_t)
      offset(r = base_r) square([base_w - 2 * base_r, base_d - 2 * base_r]);
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

module anime_relief() {
  // 浮雕直接长在底板上：高度场件（局部 Z=0 是它自己的底）沉到 Z=-anime_bury
  // 件下沿 2.65mm 落在底板内部 → 铸成一整块；露出来的只有起伏（0 .. anime_top）
  // 不做嵌槽、不留装配间隙：没有缝、没有拼装，也不能单独换色（一件打完）
  translate([(W - anime_w) / 2, anime_y - anime_d / 2, -anime_bury])
    import(anime_stl, convexity = 10);
}

// 蜂窝孔：只在背板内开（从背板前表面往后切），不碰台面根部那一条实心带
module wall_hexes() {
  hex_rows = floor((wall_len - 2 * hex_zmargin) / hex_pitch) + 1;
  hex_x0   = (W - (hex_cols - 1) * hex_pitch) / 2;
  s_plat0  = (Zp - plat_t - wall_z0) / cos(tilt);      // 台面下沿在斜面上的位置
  s_plat1  = (Zp - wall_z0) / cos(tilt);               // 台面上沿
  for (r = [0 : hex_rows - 1]) {
    s = hex_zmargin + r * hex_pitch;
    if (s + hex_r < s_plat0 - hex_skip || s - hex_r > s_plat1 + hex_skip) {
      cols = (r % 2 == 0) ? hex_cols : hex_cols - 1;
      xoff = (r % 2 == 0) ? 0 : hex_pitch / 2;
      for (c = [0 : cols - 1]) {
        x = hex_x0 + xoff + c * hex_pitch;
        translate([x, wall_y0, wall_z0]) rotate([-tilt, 0, 0])
          translate([0, 0, s]) rotate([-90, 0, 0])
            cylinder(r = hex_r, h = plate_t + 2, $fn = 6);
      }
    }
  }
}

module rack() {
  difference() {
    union() {
      base_plate();
      back_wall();
      cpu_platform();
      ribs();
      ram_tines();
      cpu_tines();
      ram_lips();
      cpu_lips();
      if (anime_on) anime_relief();
    }
    foot_pockets();
    label_pocket();
    wall_hexes();
  }
}

rack();

// ---------- 自检输出（openscad -o /dev/null 后在控制台看） ----------
hex_rows_total = floor((wall_len - 2 * hex_zmargin) / hex_pitch) + 1;
echo(str("外廓 = ", W, " x ", base_d, " x ", base_t + wall_top_z,
         " mm（底板 X ", base_x0, "..", base_x0 + base_w, " / Y ", base_front, "..", base_back, "）"));
echo(str("两级高度：内存底棱 Z=0（净宽 ", ram_cw, "，余 ", ram_cw - ram_w,
         "）→ 内存最高点 Z=", ram_top_z, "；CPU 台面 Z=", Zp, "（净宽 ", cpu_cw, "，余 ", cpu_cw - cpu_w,
         "）→ CPU 最高点 Z=", cpu_top_z));
echo(str("台面前缘 Y=", plat_y0, "，背板前表面 Z=Zp 处 Y=", cpu_butt_y, "（后缘埋进 ", plat_embed, "mm）"));
echo(str("内存牙 ", ram_tine_d, "x", ram_tine_h, "（比内存厚 ", ram_thick, " 凸出 ", ram_tine_d - ram_thick,
         "mm）/ CPU 牙 ", cpu_tine_d, "x", cpu_tine_h, "（凸出 ", cpu_tine_d - cpu_thick, "mm）"));
echo(str("背板前表面底端 Y=", wall_y0, "，板顶 Z=", wall_top_z, "（高出 CPU 顶 ", wall_top_z - cpu_top_z, "）"));
echo(str("加强筋 2 道 @X=", [W / 2 - rib_x_off, W / 2 + rib_x_off], "，高 ", rib_h,
         "，伸出 ", rib_reach_bot, "→", rib_reach_top, "（筋底 Z=", -rib_reach_bot * sin(tilt), " 埋在底板里）"));
echo(str("蜂窝孔 = ", ceil(hex_rows_total / 2) * hex_cols + floor(hex_rows_total / 2) * (hex_cols - 1),
         " 个（", hex_rows_total, " 行，跳过台面根部的行）"));
echo(str("浮雕（直接长在底板上）= ", anime_w, " x ", anime_d, " x ", anime_top + anime_bury,
         " mm 高度场件，X ", (W - anime_w) / 2, "..", (W + anime_w) / 2,
         " / Y ", anime_y - anime_d / 2, "..", anime_y + anime_d / 2,
         "；件底沉到 Z=", -anime_bury, "（件下沿埋进底板，底板顶面往下剩 ", base_t - anime_bury, " mm 料）"));
echo(str("浮雕留边：前 ", anime_y - anime_d / 2 - base_front,
         " / 后 ", (label_y - label_d / 2) - (anime_y + anime_d / 2),
         " / 左右 ", base_x0 + base_w - (W + anime_w) / 2,
         " mm（两侧都留这么多）；浮雕顶面 Z=", anime_top, "（从底板面长出来，无悬垂）"));
