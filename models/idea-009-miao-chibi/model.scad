// =============================================================================
// idea-009 苗白菜 Q 版手办（单件 / FDM 试水版）
//
// 正面朝 -Y，底座贴床 z=0，X 轴左右对称（白菜叶按 90°/90±34° 摆，整体镜像对称）。
// 设计约束（FDM，主人 10/2 定：不用树脂机）：
//   * 外廓 <= 250x250x250（主人给的打印机硬上限），实测 60 x 60 x 138.7
//   * 免手工支撑：形体一律「上收下放」；只剩手底/头根/胯下三处 <=6mm 的球面小帽
//     与平底桥接，切片器自己过，check.py 用「陡下向面积占比」量化
//   * 最薄实体件 = 白菜叶 2.6mm（>= 0.4 喷嘴 6 条线）
//   * 所有件两两「真交叉」，不写共面/相切（共面会出非流形边，check.py 会 FAIL）
//
// 编译：python3 ../../scripts/scad_build.py model.scad --out-dir . --name miao-chibi --3mf
// 自检：python3 check.py
// 预览：python3 ../../scripts/stl_preview.py miao-chibi.stl
// =============================================================================

// ---------- 参数（唯一数字来源；scad_params.py 只认「一行一个 name = 数字;」） ----------
// 底座
base_r = 30;
base_h = 5;

// 鞋
shoe_x = 10;
shoe_z = 9.7;
shoe_r = 9.6;  // z 半高 = shoe_r * shoe_zsq，鞋底要沉进底座 >=1mm
shoe_zsq = 0.62;

// 腿
leg_x = 10;
leg_z0 = 13;
leg_r0 = 7;
leg_z1 = 34;
leg_r1 = 8;

// 躯干（扁平胶囊 + 平底）
torso_z0 = 44;
torso_r0 = 16;
torso_z1 = 62;
torso_r1 = 15;
torso_ysq = 0.74;
torso_fz = 30;
torso_fr = 14.5;

// 开衫披肩（上收，免支撑）
cape_z = 56;
cape_h = 10;
cape_r1 = 16;
cape_r2 = 10;
cape_ysq = 0.85;

// 手臂
arm_x0 = 13.5;
arm_z0 = 64;
arm_r0 = 5.6;
arm_x1 = 19;
arm_z1 = 45;
arm_r1 = 4.6;

// 脖子（刻意做粗：把头部下缘的球面悬垂压到 <=6mm 环）
neck_z = 66;
neck_h = 18;
neck_r = 12;

// 头
head_z = 95;
head_r = 25;

// 头发
hair_r = 28;
cone_z0 = 60;
cone_r0 = 12;
cone_z1 = 99;
cone_r1 = 25.6;

// 侧发
lock_x = 23;
lock_z0 = 92;
lock_r0 = 6.2;
lock_z1 = 66;
lock_r1 = 5.4;

// 眼（浅浮雕 ~1mm，可打磨掉改手绘）
eye_x = 10.5;
eye_y = -20.8;
eye_z = 100;
eye_r = 6;

// 头顶白菜叶
stem_z = 108;
stem_h = 14;
stem_r = 3;
collar_z = 114;
collar_h = 5;
collar_r = 5;
leaf_z = 116;
leaf_len = 26;
leaf_elev0 = 80;
leaf_elev1 = 68;
leaf_w = 13;
leaf_t = 2.6;
vein_h = 1.3;

// 人脸开口球（从发壳里挖出脸）
face_cut_y = -18;
face_cut_z = 88;
face_cut_r = 20.5;

// 齿数
F_BIG = 96;
F_MID = 64;
F_SM = 40;

// ---------- 几何 ----------
module base_plate() {
  cylinder(r = base_r, h = base_h - 1.2, $fn = F_BIG);
  // 倒角段与主体重叠 0.6mm，避免两段圆柱在 z 上共面
  translate([0, 0, base_h - 1.8])
    cylinder(r1 = base_r, r2 = base_r - 2, h = 1.8, $fn = F_BIG);
}

module shoes() {
  for (s = [-1, 1])
    hull() {
      translate([s * shoe_x, -6, shoe_z]) scale([1, 1.15, shoe_zsq]) sphere(shoe_r, $fn = F_SM);
      translate([s * shoe_x,  5, shoe_z]) scale([1, 1.00, shoe_zsq]) sphere(shoe_r - 1, $fn = F_SM);
    }
}

module legs() {
  for (s = [-1, 1])
    hull() {
      translate([s * leg_x, 0, leg_z0]) sphere(leg_r0, $fn = F_SM);
      translate([s * leg_x, 0, leg_z1]) sphere(leg_r1, $fn = F_SM);
    }
}

module torso() {
  // 平底段与胶囊同比例压扁，腰线不出现横向凸台
  scale([1, torso_ysq, 1]) {
    translate([0, 0, torso_fz])
      cylinder(r1 = torso_fr, r2 = torso_fr + 1, h = torso_z0 - torso_fz, $fn = F_MID);
    hull() {
      translate([0, 0, torso_z0]) sphere(torso_r0, $fn = F_MID);
      translate([0, 0, torso_z1]) sphere(torso_r1, $fn = F_MID);
    }
  }
}

module cape() {
  scale([1, cape_ysq, 1])
    translate([0, 0, cape_z]) cylinder(r1 = cape_r1, r2 = cape_r2, h = cape_h, $fn = F_MID);
}

module arms() {
  for (s = [-1, 1]) {
    hull() {
      translate([s * arm_x0, 0, arm_z0]) sphere(arm_r0, $fn = F_SM);
      translate([s * arm_x1, -1, arm_z1]) sphere(arm_r1, $fn = F_SM);
    }
    translate([s * arm_x1, -1, arm_z1]) sphere(arm_r1 + 0.4, $fn = F_SM);
  }
}

module neck() {
  translate([0, 0, neck_z]) cylinder(r = neck_r, h = neck_h, $fn = F_MID);
}

module head() {
  translate([0, 0, head_z]) sphere(head_r, $fn = F_BIG);
}

module eyes() {
  for (s = [-1, 1])
    translate([s * eye_x, eye_y, eye_z]) scale([1, 0.42, 1.18]) sphere(eye_r, $fn = F_SM);
}

module hair_mass() {
  // 后发锥：上收（12 -> 25.6），坡度约 20° 离竖直，免支撑
  translate([0, 0, cone_z0]) cylinder(r1 = cone_r0, r2 = cone_r1, h = cone_z1 - cone_z0, $fn = F_BIG);
  // 后脑发量 + 长发垂到肩
  translate([0, 10, 88]) sphere(22, $fn = F_MID);
  hull() {
    translate([0,  8, 90]) sphere(20, $fn = F_MID);
    translate([0, 13, 62]) sphere(14, $fn = F_MID);
  }
  // 侧发
  for (s = [-1, 1])
    hull() {
      translate([s * lock_x, 1, lock_z0]) sphere(lock_r0, $fn = F_SM);
      translate([s * lock_x, 3, lock_z1]) sphere(lock_r1, $fn = F_SM);
    }
}

module hair_cap() {
  // 发壳 = 比头大 3mm 的球，挖掉正面开口当脸
  difference() {
    translate([0, 0, head_z]) sphere(hair_r, $fn = F_BIG);
    translate([0, face_cut_y, face_cut_z]) sphere(face_cut_r, $fn = F_BIG);
  }
}

// ---------- 白菜叶 ----------
function leaf_hw(u) = leaf_w * pow(sin(180 * u), 0.65) * (1 + 0.13 * sin(1080 * u));

leaf_n = 24;
leaf_pts = concat(
  [[-leaf_len / 2, 0]],
  [for (i = [1 : leaf_n - 1]) let(u = i / leaf_n) [-leaf_len / 2 + leaf_len * u,  leaf_hw(u)]],
  [[leaf_len / 2, 0]],
  [for (i = [leaf_n - 1 : -1 : 1]) let(u = i / leaf_n) [-leaf_len / 2 + leaf_len * u, -leaf_hw(u)]]
);

module leaf() {
  linear_extrude(leaf_t) polygon(leaf_pts);
  // 叶脉：底面沉进叶片 0.6mm，避免与叶面共面
  translate([0, 0, leaf_t - 0.6]) linear_extrude(vein_h) square([leaf_len * 0.72, 1.8], center = true);
}

// 中叶比侧叶立 12 度：三片叶的薄板若仰角全同，相交面会退化成非流形边
// （check_model 报「有向边重复」）。错开仰角后是干净的真交叉，左右仍严格镜像。
function leaf_elev(az) = az == 90 ? leaf_elev0 : leaf_elev1;

module sprout() {
  translate([0, 0, stem_z]) cylinder(r = stem_r, h = stem_h, $fn = F_SM);
  translate([0, 0, collar_z]) cylinder(r1 = collar_r + 1, r2 = collar_r, h = collar_h, $fn = F_SM);
  translate([0, 0, leaf_z])
    for (az = [90 - 34, 90, 90 + 34])
      rotate([0, 0, az])
        rotate([0, -leaf_elev(az), 0])
          translate([leaf_len / 2 - 3, 0, 0])
            leaf();
}

// ---------- 总装 ----------
union() {
  base_plate();
  shoes();
  legs();
  torso();
  cape();
  arms();
  neck();
  head();
  eyes();
  hair_mass();
  hair_cap();
  sprout();
}
