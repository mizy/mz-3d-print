// =============================================================================
// idea-016 吉他拨片盒（装 8-10 片标准 351 形拨片，插拔式上盖、无铰链）
//
// 两件套，一次打完：
//   ① 盒身：贴床平底 + 竖壁 + 上方开口的内腔（拨片平放堆叠，内腔高 = 10 片×1.5）;
//   ② 上盖：盖板 + 一圈外扣裙边（套在盒口外侧，插拔不用铰链，也就没有薄壁铰链
//      的断裂点和悬垂）。盖板正面朝下贴床打印，朝外那面最光。
//
// 打印姿态：两件都「平底贴床、竖壁朝上」→ 没有陡悬垂、也不用桥接；件与件之间留
//   6mm 间距排开（同一个 STL 里两块互不相连的实体，check.py 会验连通块数 = 2）。
// 全部尺寸 ≤ 90 x 45 x 20（含两件排开），单件更小；无铰链、无螺丝、无磁铁。
//
// 尺寸链（唯一数字来源；model.py 用同一套式子算派生量）：
//   内腔长宽 = 拨片长宽 + 2×edge_clear      内腔高 = 拨片数×厚 + stack_clear
//   盒身外廓 = 内腔 + 2×wall_t              盒身高 = floor_t + 内腔高
//   盖内 = 盒外 + 2×lid_fit（插拔间隙）      盖外 = 盖内 + 2×skirt_t
//   组装总高 = 盒身高 + lid_t ≤ 20
// =============================================================================

// ---------- 参数：拨片（标准 351 形，待主人按实物校） ----------
pick_l     = 31;      // 拨片长
pick_w     = 26;      // 拨片宽
pick_t     = 1.5;     // 单片刻厚
pick_count = 10;      // 一次装几片（8-10 片区间）

// ---------- 参数：盒身 ----------
edge_clear = 0.75;    // 拨片到内腔壁的单边间隙（好放好取）
stack_clear= 0.5;     // 堆叠顶部余量
floor_t    = 2;       // 盒底厚
wall_t     = 2.4;     // 盒壁厚
corner_r   = 4;       // 盒身外圆角
cavity_r   = 1.6;     // 内腔圆角 = corner_r - wall_t（同心，四角壁厚与直壁一致）

// ---------- 参数：上盖（插拔式，无铰链） ----------
lid_t      = 2.2;     // 盖板厚
skirt_h    = 4;       // 裙边高（套住盒口）
skirt_t    = 2.2;     // 裙边壁厚
lid_fit    = 0.25;    // 盖内壁与盒外壁的单边间隙（FDM 装配 0.2-0.3）

// ---------- 参数：排布 ----------
pack_gap   = 6;       // 两件之间的间距
F_CYL      = 64;

// ---------- 派生（只读，别手改；model.py 同步重算） ----------
cavity_l  = pick_l + 2 * edge_clear;
cavity_d  = pick_w + 2 * edge_clear;
cavity_h  = pick_count * pick_t + stack_clear;
tray_w    = cavity_l + 2 * wall_t;
tray_d    = cavity_d + 2 * wall_t;
tray_h    = floor_t + cavity_h;
lid_iw    = tray_w + 2 * lid_fit;
lid_id    = tray_d + 2 * lid_fit;
lid_ir    = corner_r + lid_fit;
lid_ow    = lid_iw + 2 * skirt_t;
lid_od    = lid_id + 2 * skirt_t;
lid_or    = lid_ir + skirt_t;
assembled_h = tray_h + lid_t;

// ---------- 几何 ----------
module rounded_rect(w, d, r) {
  hull() {
    for (sx = [-1, 1], sy = [-1, 1])
      translate([sx * (w / 2 - r), sy * (d / 2 - r)]) circle(r = r, $fn = F_CYL);
  }
}

module tray() {
  difference() {
    linear_extrude(tray_h) rounded_rect(tray_w, tray_d, corner_r);
    translate([0, 0, floor_t]) linear_extrude(cavity_h + 1) rounded_rect(cavity_l, cavity_d, cavity_r);
  }
}

module lid() {
  // 打印姿态：盖板贴床（朝外那面朝下），裙边朝上
  linear_extrude(lid_t) rounded_rect(lid_ow, lid_od, lid_or);
  translate([0, 0, lid_t])
    linear_extrude(skirt_h)
      difference() {
        rounded_rect(lid_ow, lid_od, lid_or);
        rounded_rect(lid_iw, lid_id, lid_ir);
      }
}

translate([tray_w / 2, tray_d / 2, 0]) tray();
translate([tray_w + pack_gap + lid_ow / 2, lid_od / 2, 0]) lid();
