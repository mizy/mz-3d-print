// 由 scripts/make_text3d.py 生成 —— 改完可直接 scad_build.py 重编译
// 文字只在这里写一遍；底板尺寸是脚本量出文字包围盒后算好的明确数字
// 模式：平放
text_str  = "苗白菜";
font_name = "Hiragino Sans GB";
size_mm   = 30.0;
height_mm = 8.0;
base_mm   = 3.0;
pad_mm    = 5.0;
hole_mm   = 5.0;
base_w    = 128.6721;
base_h    = 48.0001;

difference() {
  union() {
  linear_extrude(3.0)
    offset(r = 3) square([122.6721, 42.0001], center = true);
  translate([0, 0, 3.0])
    linear_extrude(8.0)
      text(text_str, size = size_mm, font = font_name, halign = "center", valign = "center");
  }
  translate([58.8360, 0, -1])
    cylinder(d = 5.0, h = 5.0, $fn = 64);
}
