# 共享基础料盘

Chanel 与 LV 的共同基础构型只有此处一份实际源码，两个品牌通过仓库内相对符号链接引用，不再各自维护复制件。修改这里会影响两款的下一次生成，**不会自动改动已经导出的 STEP**。

## 文件职责
- `Source/parameters.json`：共用官方参考尺寸、轴孔、筒、卡扣与定位键参数。
- `Source/official_hub.py`、`narrow_lock.py`、`wide_lock.py`、`wide_marker.py`：筒和配合结构。
- `Source/official_key.py`、`official_flange.py`：定位键、官方基准盘面。
- `Source/parking_slot.py`：A 方案线材收纳槽算法，配置仍由品牌指定。
- `Source/wide_*.json`：卡扣原生曲面建模数据。
- `Source/build_official.py`：官方参考基准生成器。
- `Models/OfficialBaseline/`：唯一官方基准 STEP 实际存储。

## 品牌入口
- 香奈儿：`../filament-spool-chanel/Source/chanel_reinforced_connected_fix/build_light.py`
- LV 最新错位厚壁版：`../filament-spool-lv/Source/StaggeredThickWall/lv_staggered_source/build_light.py`
- 各品牌保留 logo、盘面、开窗算法与 `light_parameters.json`。这次只抽取相同构型，不把 LV 新开窗强行套给香奈儿。

## 再生成
在安装对应品牌 `requirements.txt` 的 Python 环境执行：
```sh
python models/filament-spool-base/Source/build_official.py --output /tmp/spool-base-check
python models/filament-spool-chanel/Source/chanel_reinforced_connected_fix/build_light.py --output /tmp/chanel-check
python models/filament-spool-lv/Source/StaggeredThickWall/lv_staggered_source/build_light.py --output /tmp/lv-check
```
共享基准 `Source/requirements.txt` 使用与原香奈儿基准一致的 CadQuery 2.8.0；LV 原交付依赖仍保留 2.7.0，验证记录注明实际使用版本。快速检查共享引用可运行 `python models/filament-spool-base/Source/check_shared.py`。

品牌默认配置相对品牌脚本解析，不会错误加载共享目录的配置。请保留整个仓库的相对目录关系，不要单独复制品牌源码文件夹；Git 原生支持这些相对符号链接。历史源码 ZIP 是迁移前的独立快照，不是当前维护入口。

## 验证边界
本次不改变成品 STEP、不切片、不修改 3MF、不进行仿真、不作实物强度或锁合保证。共享重构记录见 `Notes/shared-source-migration.json`，验证见 `Notes/validation.json`。

### 本次验证结果
75 处兼容链接与品牌默认配置检查通过。两款均在 CadQuery 2.8.0 临时环境再生成并回读为 2 个有效实体。LV 原依赖为 2.7.0；2.8.0 再生成的 wide 体积比原报告少约 40.19 mm³（约 0.04%），因此**不宣称跨版本几何完全一致**，临时生成件没有替换交付 STEP。两款原交付 STEP 哈希保持不变。网页索引需待新增文件纳入 Git 后重建，本次未暂存、提交或推送。

## 当前 STEP 分件（2026-11-19）

- [BAMBU_OFFICIAL_REFERENCE_NATIVE_BASELINE_wide.step](Models/OfficialBaseline/BAMBU_OFFICIAL_REFERENCE_NATIVE_BASELINE_wide.step)
- [BAMBU_OFFICIAL_REFERENCE_NATIVE_BASELINE_narrow.step](Models/OfficialBaseline/BAMBU_OFFICIAL_REFERENCE_NATIVE_BASELINE_narrow.step)

wide 为宽半盘、narrow 为窄半盘。旧合并基准已移入可恢复废纸篓，历史文档的合并文件路径不再是当前入口。此次仅分离原实体，没有重新建模。生成器保留原行为；可用 `python Source/split_step.py <合并STEP>` 生成两件。
