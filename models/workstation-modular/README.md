# 3D 打印工作站 · 模块化桌面初版

状态：**CAD 初版，已做几何/STEP 回读检查，未切片、未打印、未验证工具实配**。

## 打开哪个文件
- 总览：`preview.png`
- 装配查看：`Models/ASSEMBLY_REFERENCE_NOT_FOR_SINGLE_PART_PRINT.step`（查看布局，不要作为一个实体打印）
- 分件打印：`Models/01_base.step` 至 `07_precision_tools.step`，各自独立文件。
- 参数：`Source/parameters.json`；建模源：`Source/build.py`。STEP 是解析 BREP，不是三角网格转换；参数与生成逻辑保留在源文件中，STEP 本身不保留特征历史。

## 初版布局
底座 237.6 × 127.2 × 6.4 mm，可置于 P1S 的标称 256 × 256 mm 平面内；实际可用区、摆盘与边缘仍由用户检查。
3 × 2 个直壁定位槽，单槽 76 × 60 mm，模块外框 75.2 × 59.2 mm，单边设计间隙 0.4 mm。模块可直接向上取出，无卡扣、磁铁或螺丝要求。不是经过标准验证的 Gridfinity 兼容接口。

前排：22 mm 高双格小零件盘；12 mm 高喷嘴/小附件孔盒；22 mm 高开放托盘。
后排：65 mm 高双格工具杯；50 mm 高胶水杯；58 mm 高四格精密工具杯。

喷嘴孔默认直径 8.5 mm，深 9.6 mm，共 15 孔。**只作为尺寸待确认的小附件收纳孔，不代表适配拓竹一体式热端**。需收纳完整热端时，应按其外形换专用模块；不要放热喷嘴。

## 建模取向与待确认项
- 开口全部朝上、平底独立分件，避免封闭顶板跨接；不据此声称已验证无支撑打印。
- 杯壁默认 3.2 mm、底板 2.4 mm；保留用户以两侧墙线+内部稀疏填充组织结构的空间，但是否实际产生稀疏区域由切片器决定。
- 工具杯不是精确卡位，尚未量取用户铲刀、剪钳、胶水及游标卡尺；卡尺横向长度超出单格，暂不声称能收纳。可后续替换为跨三格长托。
- 先确认桌面占地、工具清单和工具宽/厚尺寸。建议先打印一个小模块检验配合，再打印全套；用户自行切片。
- 未进行强度仿真、承载测试、稳定性实测；高工具重心需要实物确认。

## 来源与设计
从零构建本项目几何，没有下载或改造第三方模型。参考 MakerWorld 社区桌面分区、可换工具杯的设计方向：
- Rugged Maker Station： https://makerworld.com/en/models/1929250-rugged-maker-station-gridfinity
- Modular Screwdriver Organizer： https://makerworld.com/en/models/1131369-modular-screwdriver-gridfinity-organizer

检索可发现这些作品，但官方页面获取失败，未核实当前下载量/热度排名，不应称为已证实的热门榜单。

## 重建
```sh
uv run --with cadquery-ocp==7.9.3.1.1 python Source/build.py
uv run --with cadquery-ocp==7.9.3.1.1 --with matplotlib python Source/render.py
```
`assembly_validation.json` 记录全部组件两两求交体积最大为 0 mm³，模型状态无体积干涉；不等于实物配合验证。`Source/check_assembly.py` 可重跑。

`validation.json` 记录每个打印件单一实体、内核有效、STEP 写出/回读有效和外形尺寸；不是切片验收。没有覆盖其他模型、没有提交或 push。
