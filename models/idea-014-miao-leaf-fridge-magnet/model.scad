// =============================================================================
// idea-014 苗白菜 · 白菜叶冰箱贴（背面 2 个 φ10x2 磁铁压入槽 / 正面免支撑）
//
// 与 idea-013 同款叶形（同一套 hw() 轮廓公式），尺寸放大到 60 x 40，板厚加到 4mm
// 好给背面留 2 个磁铁槽；正面仍是「叶尖朝 +X、叶脉朝上」。
//
// 坐标：x=0 端 = 叶柄，x=leaf_len 端 = 叶尖；z=0 是背面（贴床、开磁铁槽），
//       z 越大越靠正面（叶脉朝上）。
// 打印朝向：背面平贴热床 —— 侧壁全竖直、叶脉是竖直凸棱 => 无陡悬垂；
//       唯一的水平面是 2 个磁铁槽的顶盖（φ10 圆盘，FDM 直接桥接，不用支撑）。
//
// 磁铁（φ10x2 圆片）从背面压入再点胶；槽径/槽深是参数，磁铁的实际规格见台账 openQuestions。
// =============================================================================

// ---------- 参数（唯一数字来源） ----------
// 轮廓（同 idea-013 的公式，只是放大）
leaf_len   = 60;      // 叶片长度（X 外廓）
half_w     = 18.95;   // 名义半宽（叠加波边后最大半宽 20.00 -> Y 外廓 40.0）
stem_hw    = 2.6;     // 两端最小半宽
shape_p    = 1.9;
shape_q    = 0.55;
wave_amp   = 0.075;
wave_n     = 3.5;
samples    = 700;

// 厚度
leaf_t     = 4;       // 板厚（背面到叶面）
vein_sink  = 0.6;     // 叶脉沉进叶面
vein_h     = 1.6;     // 叶脉挤出高度 -> 露出 1.0mm（总厚 5.0）

// 磁铁槽（磁铁规格是「假定值」，真实尺寸待主人拿卡尺量，见台账 openQuestions）
magnet_d     = 10;     // 假定磁铁直径（φ10 圆片）
magnet_t     = 2;      // 假定磁铁厚度
fit_clear    = 0.25;   // 压入单边间隙（FDM 装配 0.2-0.3 起步；孔打了会缩，别做零间隙）
pocket_d     = 10.25;  // 槽径 = magnet_d + fit_clear
pocket_depth = 2;      // 槽深 = 磁铁厚（压入后与背面齐平，点胶固定）
min_wall     = 2.4;    // 槽壁/叶面净料下限（0.4 喷嘴 6 条线）
min_edge     = 2.0;    // 槽圆周到轮廓最小净壁厚
bridge_max   = 15;     // 背面贴床时槽顶那片圆桥的跨距上限（FDM 桥接经验值）

F_CYL      = 64;

// ---------- 数据：磁铁槽 [名字, 圆心x, 圆心y] ----------
pocket_rows = [
  ["磁铁A", 34,  8],
  ["磁铁B", 34, -8],
];

// ---------- 数据：叶脉 [名字, 起点x, 与X轴夹角(°), 长度, 起点宽, 终点宽] ----------
vein_rows = [
  ["主脉",    13.0,   0,  40.0, 2.4, 1.2],
  ["侧脉1",   21.0,  35,  11.0, 1.5, 0.9],
  ["侧脉1b",  21.0, -35,  11.0, 1.5, 0.9],
  ["侧脉2",   29.5,  32,  12.0, 1.5, 0.9],
  ["侧脉2b",  29.5, -32,  12.0, 1.5, 0.9],
  ["侧脉3",   38.5,  28,  11.0, 1.4, 0.9],
  ["侧脉3b",  38.5, -28,  11.0, 1.4, 0.9],
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

module magnet_pockets() {
  // 从 z=-1 起切到 z=pocket_depth：背面开出平底圆槽，槽顶就是桥接面
  for (row = pocket_rows)
    translate([row[1], row[2], (pocket_depth - 1) / 2])
      cylinder(d = pocket_d, h = pocket_depth + 1, $fn = F_CYL);
}

difference() {
  union() {
    leaf_plate();
    veins();
  }
  magnet_pockets();
}
