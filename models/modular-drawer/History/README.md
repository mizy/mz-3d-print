# 历史版本：复现资料，不是打印入口

当前请用 [V18 说明书](../V18_Single_Head_T_Rod_Drawer/index.html)。历史目录只收录能解释设计来源与重建的源、参数和必要种子，不保存旧打印盘、旧总装、渲染图或安装包。不要把历史输入的 STEP 当作当前打印件。

## V10、V14、V15

旧成品及原始文档仍保留在 Git 提交 [d8f05e0](https://github.com/mizy/mz-3d-print/tree/d8f05e05495b43a4299faea8d646993c5c3c92c6/models/tv-cabinet-modular-drawer)。需要原封不动的旧成品，从旧提交导出到工作目录，不还原到当前项目：

```sh
mkdir -p ./drawer-legacy-snapshot
git archive d8f05e05495b43a4299faea8d646993c5c3c92c6 models/tv-cabinet-modular-drawer | tar -xf - -C ./drawer-legacy-snapshot
```

从当前核心源进行工程重建，请先复制整个 `History/` 到单独的目录，再在能导入 FreeCAD 1.x、Part 和 Import 的 Python 里运行。不要在本项目目录下产生旧 STEP：

- V10 标准高：`python3 V10_Prototype/Source/build_v10.py --out rebuilt-v10`。固定输入为随源码保留的 BRep。
- V10 双倍高：先把上一步生成的 `rebuilt-v10/STEP` 复制到临时副本的 `V10_Prototype/STEP`，再运行 `python3 V10_2X_Height/Source/build_double_height.py --out rebuilt-v10-2x`。其余旧排盘配置如需逐字节一致，取上述固定 Git 版本。
- V14 / V15：将 `Inputs/V13` 的两个固定种子复制为所选版本目录下的 `Seed`，运行相应版本的 `Run_V14_Template.command` 或 `Run_V15_Template.command`（macOS），传原始 `dimensions.json` 和一个新输出目录，也可直接用该目录的 Python 构建脚本。各目录保留参数、宏和核验源码。默认尺寸以原历史归档为准，未重新运行历史全套。

## V16、V17

下列是历史 H100 默认尺寸的工程重建，不保证旧文件头时间戳、说明书包和排盘工程逐字节一致。两版共用 [76 实体输入](Inputs/H100_True_Shared_10mm_Center_2x2_Closed.step)，另一份固定 [H100 单格输入](../V18_Single_Head_T_Rod_Drawer/Source/Seed/H100_Original_Single_Module.step) 与 V18 共享，不再复制一份。当前 V18 还保留 [签名 V17 闭合 STEP 种子](../V18_Single_Head_T_Rod_Drawer/Source/Seed/V17_H100_2x2_Universal_Closed.step)，只供 V18 再生。以本目录做起点时：

```sh
seed=Inputs/H100_True_Shared_10mm_Center_2x2_Closed.step
single=../V18_Single_Head_T_Rod_Drawer/Source/Seed/H100_Original_Single_Module.step
python3 V16/build_universal.py "$seed" "$single" /absolute/path/to/new-v16-output
python3 V17/build_v17.py "$seed" "$single" /absolute/path/to/new-v17-output 2.00
```

历史打印件如仅为复核：旧版重建会生成各自侧板，并保留与 V18 字节相同的 17 类共用打印 STEP。V18 已移除的 07 / 08 双头杆只保留一份 [历史小输入](Inputs/Former_Double_Rods/)，不用于 V18。旧版 3MF 的板材排布和设置只见历史归档，不承诺从 CAD 自动生成。

V16 的原批准 ZIP、历史自定义 W/D/H 实验，以及 V17 旧版网页和完整排盘归入本机历史归档，不在当前版本分发。V11–V13 的未跟踪草稿同样保留在本机历史归档，不纳入此仓库版本；未验证其全部能从当前目录重建。
