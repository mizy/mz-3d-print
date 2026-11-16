# 通用素材 Assets

这里只维护当前可复用资产，不复制项目的历史版本或打印盘配置。

## LV 矢量

来源：https://www.titanui.com/35302-simple-louis-vuitton-logo-pattern-vector/ （页面归因 sccnn）。从项目已选定的第三方 AI/SVG 分离四种图形，保留贝塞尔路径，不重新描摹或简化。四种图形可独立缩放、旋转和排布；lv-repeat.svg 是完整重复单元，不是限定两排的碗设计。

这些不是经认证的官方原稿。来源页不等于权利人授权，未核实商业复制、转售或再分发许可。品牌商标及图案权利归原权利人。

## Chanel 双 C

直接取自现有碗项目的独立平放 STEP，重新导出以移除路径和文件元数据。早期几何来源未核实；不是官方矢量，也不是新描摹的替代版本。预览为真实实体的正投影。

## 星星与月亮

parametric_shapes.py 是新的通用参数化源文件，不依赖其他项目。需要 CadQuery 2.x。默认直径 30 mm、厚度 3 mm。每种只保留一个最新 STEP，SVG 是同参数轮廓。

```sh
python parametric_shapes.py --shape star --diameter 30 --thickness 3 --points 5 --inner-ratio 0.46
python parametric_shapes.py --shape moon --diameter 30 --thickness 3 --cut-ratio 0.92 --offset-ratio 0.42
```

尺寸单位 mm。实体已检查有效且单实体，但未做实际打印验证，尖端受喷嘴宽度影响。素材预览是矢量轮廓/几何投影，不是实物照片。
