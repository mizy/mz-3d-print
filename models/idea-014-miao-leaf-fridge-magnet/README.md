# 参数化模型模板（本目录：idea-014 白菜叶冰箱贴）

> **本件的实际构建方式**：本机（macOS 27 / arm64）已无 Rosetta 2，`~/.cah-data/tools/OpenSCAD-2021.01.app`
> 是 x86_64 单架构二进制，内核直接拒绝执行（`Bad CPU type in executable`），下面第 2 步的
> `scripts/scad_build.py` 调不动它。所以 STL/3MF 改由同目录的 `build_mesh.py` 生成
> —— 走 skill 里另一条已文档化的离线路线（uv 缓存里的 cadgen + build123d / OpenCASCADE），
> **参数仍全部来自 `model.scad`**：
>
> ```bash
> cd models/idea-014-miao-leaf-fridge-magnet
> uv run --offline --python 3.13 --with cadgen==0.7.26 python build_mesh.py   # -> leaf-fridge-magnet.stl + .3mf
> python3 check.py
> python3 ../../scripts/stl_preview.py leaf-fridge-magnet.stl
> node ../../scripts/cost.mjs leaf-fridge-magnet.stl --material PLA
> ```
>
> 「先量磁铁」：`pocket_d = magnet_d + fit_clear`、`pocket_depth = magnet_t` 都在 `model.scad`
> 参数段；主人量出手头磁铁的真实直径/厚度后只改 `magnet_d`/`magnet_t` 重跑即可。

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
