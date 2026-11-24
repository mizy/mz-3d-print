# 香奈儿 · 加厚连通盘面

## 当前模型（2026-11-19）

- [CHANEL_REINFORCED_CONNECTED_SELF_SUPPORT_A_wide.step](Models/ChanelLight/CHANEL_REINFORCED_CONNECTED_SELF_SUPPORT_A_wide.step)：宽半盘，一个有效 BRep 实体。
- [CHANEL_REINFORCED_CONNECTED_SELF_SUPPORT_A_narrow.step](Models/ChanelLight/CHANEL_REINFORCED_CONNECTED_SELF_SUPPORT_A_narrow.step)：窄半盘，一个有效 BRep 实体。

参数化源码：`Source/chanel_reinforced_connected_fix/build_light.py`。共享筒、卡扣、定位键、基础尺寸与 A 收纳槽引用 [filament-spool-base](../filament-spool-base/README.md)。品牌盘面、logo 与开窗参数独立。STEP 为几何交换文件，参数通过源码修改。

本次仅按现有实体分文件，不裁切实体、不改变装配接口或坐标。旧合并 STEP 和过时模型已移入可恢复废纸篓；只使用上面这对文件。现有 3MF 和源码未改；未切片、未新做强度或实物装配验证。

拆分核验与清理清单见共享项目 `Notes/split-step-validation.json` 和 `Notes/split-step-cleanup.json`。旧 README 在 `Notes/README_before_split_2026-11-19.md`，仅作历史，不作为当前文件/重量入口。

源码生成器仍会在指定输出目录产出合并 STEP，可用共享项目 `Source/split_step.py` 转为宽窄两文件；不要将历史临时输出误当当前成品。

用户原打印工程 `Models/ChanelLight/PARKING_A_WINDOW_TRIAL.3mf` 保留未动，不代表已替换为本次 STEP。
