# LV · OPEN ARCH 大面积错位长窗

## 当前唯一成品（2026-11-19）
- [宽半盘 LV_OPEN_ARCH_A_wide.step](Models/StaggeredThickWall/LV_OPEN_ARCH_A_wide.step)
- [窄半盘 LV_OPEN_ARCH_A_narrow.step](Models/StaggeredThickWall/LV_OPEN_ARCH_A_narrow.step)
- [内外筒 CAD 剖切预览](Models/StaggeredThickWall/LV_OPEN_ARCH_CUTAWAY.png)

两文件各为一个有效原生BRep，各自居中，不是组合摆放位姿。已替代8小窗版，旧版移至可恢复废纸篓；现有3MF没有替换，打印时请自行换成新模型。

每层8个均匀长窗，内外错位22.5°。50°尖拱顶替代遮挡孔的宽斜膜；宽外窗延伸至z36、窄外窗23.2、内窗28。保留实际插接/卡扣段，不再把所有z26以上一律封死。最大开窗角宽20°，两层不径向对穿。

参数/完整边界说明：[源码 README](Source/StaggeredThickWall/lv_staggered_source/README.md)。共享基线11条相对链接保持不变。生成器默认识别当前项目输出目录，直接产出宽/窄STEP。

从本项目目录执行：
```sh
python Source/StaggeredThickWall/lv_staggered_source/build_light.py
```

CAD：保护区域差分0，16处/半的窗口及对侧壁探针通过；44°/50°名义组装无干涉。前提为两外盘面相距67.4mm、窄半先绕X180°再绕Z旋转。不是实物装配或强度合格证明。

名义孔径55mm，整件Ø54.9mm通孔体无碰撞；筒径81.7/81.3mm，定位键局部R43.7需纸芯对应缺口；主筋间轴向包络60.2mm。纸芯实际尺寸未测，不能保证任意耗材挂载。

本次未切片、未做FEA或实物测试；原径向桥在开窗高度的外壁连接改变，不因加厚或单实体而承诺强度。检查数据在当前Models目录，源码可调整尺寸后再验证。
