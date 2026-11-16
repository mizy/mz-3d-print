// =============================================================================
// idea-015 桌面理线夹（夹持线径 4 / 6 / 8mm 三规格，一次打三颗）
//
// 一颗夹子 = 贴胶面平贴热床的长方块 + 沿 X 穿过的圆孔（走线）+ 从顶部开进去的
// 窄卡入口（槽宽 = 0.9×线径，比线细才有卡持），入口顶部做 30° 喇叭好塞线。
//
// 打印朝向：贴胶面（z=0）平贴热床 —— 侧壁全竖直；入口是竖直窄槽（不封顶，
//   所以圆孔顶部不需要桥接）；只有入口喇叭那两面是 30°（< 45°）的坡，免支撑。
// 双面胶：整块贴胶面（clip_w × dd）都是平的，胶带贴在 z=0 这一面。
// 单件外廓 <= 25 x 25 x 20（check.py 逐规格对账）；三颗沿 X 排开一次打完。
//
// 三规格共用一套参数，只按 d_line 算 r / 孔中心高 / 总高 / 总宽（model.py 同式重算）。
// =============================================================================

// ---------- 参数（唯一数字来源） ----------
clip_w      = 12;     // 沿走线方向（X）的宽度
tape_base   = 2.5;    // 贴胶面到穿线孔最低点的实心厚度（胶带粘贴面）
side_wall   = 2.4;    // 穿线孔两侧壁厚
top_wall    = 2.0;    // 穿线孔顶到件顶的壁厚
slot_ratio  = 0.9;    // 卡入口宽 / 线径（<1 才有卡持；>=1 就是敞口托）
flare_h     = 1;      // 入口喇叭高度
flare_ang   = 30;     // 喇叭张角（离竖直方向；< 45 免支撑）
pack_gap    = 6;      // 一次打多颗时的间距
min_wall    = 2.4;    // 最薄实心壁厚下限（0.4 喷嘴 6 条线）
single_max  = 25;     // 单件外廓上限（主人要求 <=25x25x20）
single_max_h = 20;
arc_facets  = 48;     // 孔壁圆弧分段（剖面用；0.01mm 弦差量级）
F_CYL       = 64;

// ---------- 数据：三规格 [名字, 线径 d, 排布起点 x] ----------
clip_rows = [
  ["夹 φ4", 4,  0],
  ["夹 φ6", 6, 18],
  ["夹 φ8", 8, 36],
];

// ---------- 几何 ----------
function z_axis_of(d) = tape_base + d / 2;            // 孔中心高
function h_of(d)      = tape_base + d + top_wall;      // 件总高
function dd_of(d)     = d + 2 * side_wall;             // 件总宽（Y）

module clip(d, x0) {
  w = clip_w;
  za = z_axis_of(d);
  h = h_of(d);
  dd = dd_of(d);
  flare_w2 = slot_ratio * d + 2 * (flare_h + 0.5) * tan(flare_ang);
  translate([x0, 0, 0])
    difference() {
      translate([w / 2, 0, h / 2]) cube([w, dd, h], center = true);
      // 走线孔：沿 X 穿过
      translate([w / 2, 0, za])
        rotate([0, 90, 0]) cylinder(d = d, h = w + 2, center = true, $fn = F_CYL);
      // 卡入口窄槽：从孔顶一路开到件顶
      translate([w / 2, 0, (za + h + 2) / 2])
        cube([w + 2, slot_ratio * d, h + 2 - za], center = true);
      // 入口喇叭：30° 外扩（< 45° 免支撑）
      translate([w / 2, 0, 0])
        hull() {
          translate([0, 0, h - flare_h]) cube([w + 2, slot_ratio * d, 0.02], center = true);
          translate([0, 0, h + 0.5]) cube([w + 2, flare_w2, 0.02], center = true);
        }
    }
}

union() {
  for (row = clip_rows) clip(row[1], row[2]);
}
