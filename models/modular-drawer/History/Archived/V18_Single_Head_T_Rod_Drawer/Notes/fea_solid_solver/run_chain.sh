#!/bin/zsh
# 等依赖与 Rust 原生求解器就绪后，跑两个实体算例：
# 1) 抽屉底板（与已有薄板模型交叉验证）
# 2) 整个抽屉实体（检验薄壁件可网格性）
set -u
NOTES=/Users/mizy/projects/mz-3d-print/models/modular-drawer/V18_Single_Head_T_Rod_Drawer/Notes
OUT=$NOTES/fea_solid_solver
PY=/Users/mizy/projects/cad-surface-mesher/.venv/bin/python
BIN=/Users/mizy/projects/cad-surface-mesher/.agents/skills/structural-solver/native/target/release/structural_solver_native
cd $OUT || exit 1

echo "[chain] wait python deps"
for i in {1..120}; do
  $PY -c "import numpy,scipy,trimesh,gmsh,pyvista" >/dev/null 2>&1 && break
  sleep 10
done
$PY -c "import numpy,scipy,trimesh,gmsh,pyvista" || { echo "[chain] DEPS FAILED"; exit 1; }

echo "[chain] wait native solver"
for i in {1..90}; do
  [ -x "$BIN" ] && break
  sleep 10
done
[ -x "$BIN" ] || { echo "[chain] NATIVE BIN MISSING"; exit 1; }
echo "[chain] ready $(date +%H:%M:%S)"

echo "[chain] case 1: bottom panel 2.0mm"
$PY run_solid_case.py \
  --stl $NOTES/fea_drawer_infill/bottom_panel.stl \
  --mesh-size 2.0 --young-mpa 1400 --poisson 0.35 \
  --fixes x_min,x_max,y_min,y_max --loads "z_min: fz=-19.6" \
  --out $OUT/fea_solid_bottom_2kg --backend auto \
  || echo "[chain] bottom case failed"

echo "[chain] case 2: full drawer mesh test 3.0mm"
$PY run_solid_case.py \
  --stl $NOTES/fea_drawer_infill/drawer_printed.stl \
  --mesh-size 3.0 --young-mpa 1400 --poisson 0.35 \
  --fixes x_min,x_max,y_min,y_max --loads "z_min: fz=-19.6" \
  --out $OUT/fea_solid_drawer_2kg --backend auto \
  || echo "[chain] drawer case failed"

echo "[chain] done $(date +%H:%M:%S)"
