# 最新 LV 版：官方配合、四老花、自支撑与 A 收线槽

新文件：[LV_OFFICIAL_SELF_SUPPORT_A.step](Models/OfficialSelfSupport/LV_OFFICIAL_SELF_SUPPORT_A.step)

[完整验证与限制](Notes/lv_official_selfsupport_A/FINAL_REPORT.md) · [参数源码](Source/lv_official_selfsupport_A/README.md)

保持两墙，用户工艺实切两半 **118.45g**；低料工艺对照 **109.85g**。未达100g，强度优先不继续削筋或改一墙。真实BRep两实体、源可再生，官方关键表面差集已核，**没有实物承载认证**。原始STEP三角化可能出现零面积退化面提示，验证切片对此作透明清理，见报告。

旧原型仅保留历史，不要与新接口、重量或验证混用。

---

# LV 镂空轻量料盘 A：当前 v2 工程原型

> **未验证，禁止装料。不是可直接投入使用的成品。** 当前无独立防反转锁止，拓竹纸芯和旋锁接口尺寸尚未核实，未切片、未打印、未空载试配或承重试验。不要根据分析结果在 AMS 内满载使用。

## 最新修订要求（2026-11-17）

用户要求双孔与拓竹官方料盘一致。**当前自拟的 Ø2.4 mm、r93 mm、切向偏移 ±2.8 mm 孔位不是定稿，也未经官方模型核验。** 当前文件仅作为待修订原型保留，必须取得可验证官方孔位与走线方向后再修改、重新做网格及受力检查。不得称为官方同款孔位。

## 当前文件

仅保留当前两半的 STEP 与 STL。STEP 用于编辑，STL 用于网格检查和后续小样规划，不含打印设置；没有假造 3MF 或 G-code。未收录 ZIP、重复装配 STEP、旧迭代和可重建的有限元网格。完整装配 STEP 可从源脚本重建。

- `Models/`：两半模型，标称外径 200 mm、组装宽度 67 mm；芯筒接口是待验证的自建假设，不宣称官方兼容。
- `Design/`：实际 CAD 预览，不是 AI 效果图。
- `Notes/engineering_report.md`：完整载荷假设、官方材料数据来源、模型局限及试验步骤。
- `Source/`：几何生成、网格检查、有限元筛查脚本与依赖。
- `Notes/import_checksums.json`：入库源文件 SHA-256，记录此次归档校验；SVG 仅统一换行，其余导入文件字节一致。

每片 4 对 Ø2.4 mm 直通卡线孔。并非参考模型的 45°斜孔，也未做实际夹持验证。按拓竹 PETG Matte 密度 1.37 g/cm³，模型实体体积质量约 110.6 g，不是切片质量，略高于 100 g 目标。

## 验证边界

两半 CAD 各单实体且有效，STL 边界边/非流形边为 0；没有自交测试。既有有限元在云端实际运行，但只是各向同性线性简化筛查。1 kg 重力不能决定线圈轴向侧压力；轴向 1/5/10 N 为独立敏感性工况。大挠度、层间破坏、蠕变、接触、锁止脱开未模拟，不能推出安全承载。

## 来源与许可

分类为 derived，避免对 LV 品牌图形主张原创：料盘几何与脚本自建，LV 矢量沿用本项目既有狗碗设计；商标权不属于本项目。卡线思路参考公开料盘说明，未复制第三方 CAD。官方模型未取得，许可也未核实，不宣称使用或继承官方模型许可。参考链接见工程报告。仅作为个人设计研究，不暗示品牌授权。

## 复现（在独立临时目录，不覆盖当前档案）

依赖版本见 Source/requirements.txt；需自行配置相容的 Python 环境。当前记录是原环境的结果，未在 Mac 重跑 CAD/FEA。

```sh
work=$(mktemp -d)
cp Source/* "$work/"
# 在隔离 Python 环境安装 requirements.txt，然后：
cd "$work"
python build.py
python check_mesh.py
python analyze.py
python axial_plate.py
```

脚本都以自身目录为输入/输出；analyze.py 会生成 fea_mesh.npz，供 axial_plate.py 使用。仅比较或审阅临时输出，不自动覆盖本目录结果。装配 STEP 为生成输出，不另行入库。

## AMS 工况三维筛查（2026-11-17）

新增 [完整报告](Notes/ams_3d/REPORT.md)、两档网格的结果JSON/云图及 `Source/ams_3d/` 复现脚本。工况改为中心筒载重、外缘滚轮承托，接触只承压；不再把面内二维结果当作整盘变形证明。

理想连续对称芯筒模型最大位移为0.01417/0.01459mm，峰值等效应力为1.109/1.422MPa。**应力增加28.26%，未网格收敛；真实旋锁、滚轮尺寸/间隙和FDM各向异性未验证，不批准满载使用。** 禁止装料状态不变。

复现时先在独立环境安装 `Source/ams_3d/requirements.txt`，再运行其中的 `mesh.py 2`、`solve.py 2 30`；细网格改为1.4。默认临时输出在同目录被Git忽略的 `work/`，可通过 `AMS_OUTPUT` 指向新的独立目录，`AMS_CAD` 指定STEP。`plot.py` 根据计算输出生成云图。模型没有在本轮改动，双孔仍待官方资料核实。

## 共享基础构型（2026-11-19）

筒、官方配合、定位键、基础尺寸及 A 槽算法统一引用 [共享基础料盘](../filament-spool-base/README.md)。当前品牌生成入口为 `Source/StaggeredThickWall/lv_staggered_source/build_light.py`；品牌盘面、logo、开窗和轻量化配置仍独立。旧路径通过相对符号链接兼容，更新公共基础时只编辑 `filament-spool-base/Source/`。此次整理没有改变已经导出的 STEP。
