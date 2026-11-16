// 由 scripts/make_text3d.py 生成 —— 改完可直接 scad_build.py 重编译
// 文字只在这里写一遍；底板尺寸是脚本量出文字包围盒后算好的明确数字
// 模式：立式（能放桌面）+底脚
text_str  = "苗白菜";
font_name = "Hiragino Sans GB";
size_mm   = 34.0;
height_mm = 8.0;
base_mm   = 0.0;
pad_mm    = 4.0;
hole_mm   = 0.0;
base_w    = 134.4950;
base_h    = 43.0668;

difference() {
  union() {
  translate([0, 0, 21.5334])
    rotate([90, 0, 0])
      union() {
  translate([0, 0, 0])
    linear_extrude(8.0)
      text(text_str, size = size_mm, font = font_name, halign = "center", valign = "center");
      }
  translate([0, -6.0000, 2.0000])
    cube([134.4950, 16.0000, 4.0000], center = true);
  }
}
