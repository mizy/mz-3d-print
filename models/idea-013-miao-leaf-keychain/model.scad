// =============================================================================
// idea-013 苗白菜 · 白菜叶钥匙扣（φ4 挂孔 / 平放免支撑 / 默认单色）
//
// 坐标：叶片长边沿 +X（叶柄在 x=0 端，叶尖在 x=leaf_len 端），宽度沿 ±Y，
//       厚度沿 +Z：z=0 是贴床的平整背面，z 越大越靠正面（叶脉朝上）。
// 打印朝向：背面平贴热床，正面（叶脉）朝上 —— 所有侧壁都是竖直面，
//       叶脉是凸起的竖直棱，全程无悬垂、无支撑。
//
// 造型：叶片轮廓 = 一条半宽函数 hw(u) 的上下对称闭曲线
//       hw(u) = stem_hw + (half_w - stem_hw) * sin(180°·u^shape_p)^shape_q
//               * (1 + wave_amp·sin(360°·wave_n·u))
//       · u=0 端 = 叶柄（收窄到 stem_hw，为挂孔留料）
//       · u→1 端 = 叶尖（收窄）
//       · sin(...) 幂律把最宽处推到 u≈0.65（叶身偏后段鼓），
//         wave_* 项在两边上压出波边（波峰互相错开，像白菜叶的皱边）
//
// 颜色分区（只标参数，默认出单色单件；AMS 双色时按 x=stem_zone_x 切）：
//   x <  stem_zone_x  → 叶柄区（浅色）
//   x >= stem_zone_x  → 叶面区（叶身 + 叶脉）
// =============================================================================

// ---------- 参数（唯一数字来源；scad_params.py 只认「一行一个 name = 数字;」） ----------
// 轮廓
leaf_len   = 55;      // 叶片长度（X 外廓）
half_w     = 16.6;    // 名义半宽（叠加波边后最大半宽 = 17.52 -> Y 外廓 35.0）
stem_hw    = 2.6;     // 两端最小半宽（叶柄端 / 叶尖端，各自 5.2mm 宽）
shape_p    = 1.9;     // 幂律指数：越大叶柄越长、最宽处越靠叶尖
shape_q    = 0.55;    // 半宽曲线指数：<1 让叶身更饱满
wave_amp   = 0.075;   // 波边幅度（相对半宽）
wave_n     = 3.5;     // 波边周期数（沿长度方向）
samples    = 600;     // 轮廓采样段数（每侧）

// 厚度
leaf_t     = 3;       // 叶片板厚（贴床的那层）
vein_sink  = 0.6;     // 叶脉沉进叶面的深度（防共面，也保证真的熔在一起）
vein_h     = 1.6;     // 叶脉挤出高度 -> 露出叶面 vein_h - vein_sink = 1.0mm

// 挂孔
hole_d     = 4;       // 挂孔直径（钥匙圈 φ4）
hole_x     = 6.5;     // 挂孔圆心 X（落在叶柄段里）
min_wall   = 2.4;     // 挂孔到轮廓的最小净壁厚（0.4 喷嘴 6 条线）

// 分色
stem_zone_x = 11.2;   // 叶柄/叶面分色边界（x < 此值算叶柄区）

F_CYL      = 64;      // 圆孔分段

// ---------- 数据：叶脉 [名字, 起点x, 与X轴夹角(°), 长度, 起点宽, 终点宽] ----------
vein_rows = [
  ["主脉",    12.0,   0,  37.0, 2.2, 1.2],
  ["侧脉1",   19.0,  35,  10.0, 1.4, 0.9],
  ["侧脉1b",  19.0, -35,  10.0, 1.4, 0.9],
  ["侧脉2",   27.0,  32,  11.0, 1.4, 0.9],
  ["侧脉2b",  27.0, -32,  11.0, 1.4, 0.9],
  ["侧脉3",   35.5,  28,  10.0, 1.3, 0.9],
  ["侧脉3b",  35.5, -28,  10.0, 1.3, 0.9],
];

// ---------- 几何 ----------
function hw(u) =
  stem_hw + (half_w - stem_hw) * pow(sin(180 * pow(u, shape_p)), shape_q)
            * (1 + wave_amp * sin(360 * wave_n * u));

leaf_pts = concat(
  [for (i = [0 : samples]) [leaf_len * i / samples,  hw(i / samples)]],
  [for (i = [samples - 1 : -1 : 1]) [leaf_len * i / samples, -hw(i / samples)]]
);

module leaf_plate() {
  linear_extrude(leaf_t) polygon(leaf_pts);
}

module veins() {
  for (row = vein_rows)
    translate([row[1], 0, leaf_t - vein_sink])
      linear_extrude(vein_h)
        rotate([0, 0, row[2]])
          polygon([[0, -row[4] / 2], [row[3], -row[5] / 2],
                   [row[3], row[5] / 2], [0, row[4] / 2]]);
}

module mount_hole() {
  translate([hole_x, 0, -1]) cylinder(d = hole_d, h = leaf_t + 2, $fn = F_CYL);
}

difference() {
  union() {
    leaf_plate();
    veins();
  }
  mount_hole();
}
