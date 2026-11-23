#!/bin/bash
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
F="${FREECAD_RESOURCES:-/Applications/FreeCAD.app/Contents/Resources}"
PY="$F/bin/python"
if [ ! -x "$PY" ]; then
  printf '\n未找到 FreeCAD。请把 FreeCAD 放进 Applications，或设置 FREECAD_RESOURCES。\n'
  exit 1
fi
export PYTHONPATH="$F/lib" PYTHONDONTWRITEBYTECODE=1
if [ "$#" -gt 0 ]; then
  exec "$PY" "$HERE/build_v14_wdh.py" "$@"
fi
read -r OW OD OH < <("$PY" -c 'import json,sys;c=json.load(open(sys.argv[1]));print(c["outer_width_mm"],c["outer_depth_mm"],c["outer_height_mm"])' "$HERE/dimensions.json")
printf '\nV14 参数化抽屉｜毫米｜2 mm 档\n可直接输入；回车保留上次值。\n\n'
read -r -p "外宽 W 180–240 [$OW]：" W
read -r -p "外深 D 180–240 [$OD]：" D
read -r -p "外高 H 48–80   [$OH]：" H
W="${W:-$OW}"; D="${D:-$OD}"; H="${H:-$OH}"
CFG="$(mktemp "${TMPDIR:-/tmp}/v13-dimensions.XXXXXXXX")"
trap 'rm -f -- "$CFG"' EXIT
"$PY" - "$CFG" "$W" "$D" "$H" <<'PY'
import json,sys
open(sys.argv[1],'w').write(json.dumps(dict(zip(('outer_width_mm','outer_depth_mm','outer_height_mm'),map(int,sys.argv[2:]))),indent=2)+'\n')
PY
OO="$HERE/Results/W${W}_D${D}_H${H}_$(date '+%Y%m%d_%H%M%S')"
if "$PY" "$HERE/build_v14_wdh.py" --config "$CFG" --out "$OO"; then
 cp "$CFG" "$HERE/dimensions.json"
 printf '\n成品：%s\n' "$OO"
 read -r -p '按回车结束。' TEMP
else
 printf '\n没有导出通过的成品，请检查报错；没有修改上次参数。\n'
 read -r -p '按回车结束。' TEMP
 exit 1
fi
