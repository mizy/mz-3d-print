V17 SKADIS接口目标＋六角贯穿孔/深凹槽 · 试制版
1. 接口：长圆孔5×15mm（直段10mm、两端R2.5），同组40×40mm，两组偏移20×20mm；托架两挂头间距40mm。
尺寸依据是配件制造者和公开参数化项目的测量/实现，非宜家官方工程公差图：
https://www.justhangingpegboards.com/pages/pegboard-system
https://github.com/sebasdv/skadisgen
https://github.com/franpoli/OpenSCADutil/blob/master/libraries/ikea_skadis_pegboard_accessories/ikea_skadis.scad
2. 板：240×242mm；挂孔局部5mm厚，非挂接区域2.4mm薄壁。宽背座配件可能需要完整平面支承，不能直接承诺所有宜家附件兼容。
3. 减料：立板非挂接区78个最大跨度9mm六角贯穿孔；浮雕前板5个六角贯穿孔，以及51个1.2mm深的底部六角凹槽，浮雕下方保留至少1.8mm名义底厚。六角孔名义间距12mm、最小名义孔间料宽3mm；避开挂孔保护区、脚座支撑及定位孔。
4. 独立零件：board 1、universal_tray 7、desk_foot 2、relief_badge 1。四根内存因40mm接口间距错层20mm，三颗CPU在上层；原120×48浮雕保留在完整前板。
5. 挂接：托架抬高5.5mm，让两后挂头穿入长孔，再下落。缺少独立防抬锁止，取物时按住托架。打印头底部需切片检查局部支撑。
6. 装配、名义物件占位和挂头穿入/下落轨迹没有检测到干涉；四种零件均闭合、零退化面、零非流形顶点。未做宜家实物兼容、承载、抗倾倒或打印试验。
7. 省料对比：同尺寸、同接口、没有六角减料的几何约247.25cm³；当前233.40cm³，减少13.86cm³（5.6%）。这不是切片耗材节省率；它也比旧V14更大、接口更厚，总体用料仍高于V14。
8. print-plates含两个整盘和可选小样3MF。第一盘240×242mm板占据大部分250mm平台；务必核对设备禁打区、裙边。建议先小样再整盘。
9. 源码：design.py为几何生成入口；arrange_plates.py为分盘入口，依赖manifold3d、numpy、trimesh、pyvista。原浮雕文件在assets中。
10. MakerWorld 发布包：makerworld-export/skadis-tray-makerworld/（单件 STL/3MF、预览图、上传文案）。这是该发布包的唯一副本。
