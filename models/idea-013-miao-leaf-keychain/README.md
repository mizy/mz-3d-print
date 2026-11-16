# 参数化模型模板（本目录：idea-013 白菜叶钥匙扣）

> **本件的实际构建方式**：本机（macOS 27 / arm64）已无 Rosetta 2，`~/.cah-data/tools/OpenSCAD-2021.01.app`
> 是 x86_64 单架构二进制，内核直接拒绝执行（`Bad CPU type in executable`），下面第 2 步的
> `scripts/scad_build.py` 调不动它。所以 STL/3MF 改由同目录的 `build_mesh.py` 生成
> —— 走 skill 里另一条已文档化的离线路线（uv 缓存里的 cadgen + build123d / OpenCASCADE，
> 与 `scripts/cad_model.sh` 同一套工具链），**参数仍全部来自 `model.scad`**：
>
> ```bash
> cd models/idea-013-miao-leaf-keychain
> uv run --offline --python 3.13 --with cadgen==0.7.26 python build_mesh.py   # -> leaf-keychain.stl + .3mf
> python3 check.py                                                           # 逐条自检，全过才开打
> python3 ../../scripts/stl_preview.py leaf-keychain.stl                     # 四联预览
> node ../../scripts/cost.mjs leaf-keychain.stl --material PLA               # 克数/材料费
> ```
>
> 等哪天这台机器能跑 OpenSCAD（或换 arm64 版）时，下面这套原生流程同样适用：`model.scad`
> 与 `build_mesh.py` 描述的是同一套几何（`check.py` 会拿 STL 的包围盒/体积/剖面与参数对账）。

复制整个目录起手：

```bash
S=~/.cah-data/skills/shared/3d-print-ideas
cp -r $S/templates/parametric-model $S/models/idea-00X-我的件
cd $S/models/idea-00X-我的件
# 1) 只改 model.scad 的「参数」段与两张表
# 2) 编译 + 自检（出 STL/3MF）
python3 $S/scripts/scad_build.py model.scad --out-dir . --name 我的件 --3mf
# 3) 逐条算「能不能打」（底盘/壁厚/槽深/材料预算/实测对账）
python3 check.py
# 4) 出四联预览图发给主人看
python3 $S/scripts/stl_preview.py 我的件.stl
```

- `model.py` / `check.py` 是通用的，**一般不用改**；要加新的检查项就加在 `check.py` 的
  「B 可打印性」段，照现有 `check(条件, 名称, 明细)` 的写法。
- 只改 `model.scad` 时，`model.py` 的派生量与 `check.py` 的断言会跟着重算——数字一处一改。
- 表格列数固定，改列会在 `model.py` 里直接报错，不会静默少读一行。
