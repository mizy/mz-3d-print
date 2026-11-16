#!/usr/bin/env python3
"""idea-006 工具收纳盘的参数解析 + 派生量 —— check.py 与成本估算共用这一份。

数字只从 model.scad 来（结构参数走 scad_params，两张表走固定列格式），
派生量在这里算一次：任何「以 scad 为准」的判断都基于同一套值，不会两边打架。

用法:
  python3 model.py            # 打印派生摘要
  python3 model.py --json     # 出完整 JSON（含两张表的解析结果）
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCAD = HERE / "model.scad"
sys.path.insert(0, str(Path.home() / ".cah-data/skills/shared/3d-print-ideas/scripts"))
from scad_params import read_params  # noqa: E402 —— .scad 参数解析只写一份

RECT_COLS = ["name", "cx", "cy", "tool_l", "tool_w", "tool_t", "pocket_l", "pocket_w", "depth"]
BORE_COLS = ["name", "cx", "cy", "tool_d", "tool_t", "pocket_d", "depth"]


def read_table(text, table_name, cols):
    """读 `table_name = [ ["名字", 数字...], ... ];` 这张表，按固定列名转成 dict 列表。

    行格式不合规（列数不对 / 数字解不出）就抛错——宁可炸在这儿，也不要悄悄少读一行。
    """
    block = re.search(rf"^\s*{table_name}\s*=\s*\[(.*?)^\s*\];", text, re.M | re.S)
    if not block:
        raise SystemExit(f"model.scad 里找不到表 {table_name}")
    rows = []
    for raw in block.group(1).splitlines():
        line = raw.split("//", 1)[0].strip().rstrip(",")
        if not line:
            continue
        m = re.match(r'^\[\s*"([^"]+)"\s*,(.*)\]$', line)
        if not m:
            raise SystemExit(f"{table_name} 里有解析不了的行: {raw.strip()}")
        name, rest = m.group(1), m.group(2)
        try:
            nums = [float(v) for v in rest.split(",") if v.strip() != ""]
        except ValueError as exc:
            raise SystemExit(f"{table_name} 行「{name}」有非数字字段: {exc}")
        if len(nums) != len(cols) - 1:
            raise SystemExit(f"{table_name} 行「{name}」列数 {len(nums)+1} != 规定 {len(cols)}")
        rows.append(dict(zip(cols, [name] + nums)))
    return rows


def box(row):
    """方槽的 (x0, y0, x1, y1)。"""
    return (row["cx"] - row["pocket_l"] / 2, row["cy"] - row["pocket_w"] / 2,
            row["cx"] + row["pocket_l"] / 2, row["cy"] + row["pocket_w"] / 2)


def load():
    text = SCAD.read_text()
    p = read_params(SCAD)
    rects = read_table(text, "rect_rows", RECT_COLS)
    bores = read_table(text, "bore_rows", BORE_COLS)
    depths = [r["depth"] for r in rects] + [r["depth"] for r in bores]
    p.update({
        "rect_pockets": rects,
        "bore_pockets": bores,
        "max_depth": max(depths),
        "pocket_count": len(rects) + len(bores),
        "tool_count": len(rects) + len(bores),
    })
    return p


def main(argv):
    ap = argparse.ArgumentParser(add_help=True, description="idea-006 派生量")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    p = load()
    if a.out:
        Path(a.out).write_text(json.dumps(p, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    if a.json:
        print(json.dumps(p, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"外廓 {p['tray_w']:.0f} x {p['tray_d']:.0f} x {p['tray_h']:.0f} mm，"
              f"底盘 {p['floor_t']:.0f}mm，槽 {p['pocket_count']} 个（最深 {p['max_depth']:.0f}mm），"
              f"间隙 {p['gap']}mm/边")
        for r in p["rect_pockets"]:
            print(f"  方槽 {r['name']:8s} {r['pocket_l']:.0f}x{r['pocket_w']:.0f}x深{r['depth']:.0f}"
                  f"  工具 {r['tool_l']:.0f}x{r['tool_w']:.0f}x{r['tool_t']:.0f}")
        for r in p["bore_pockets"]:
            print(f"  圆槽 {r['name']:8s} φ{r['pocket_d']:.0f}x深{r['depth']:.0f}"
                  f"  工具 φ{r['tool_d']:.0f}x{r['tool_t']:.0f}")
        if a.out:
            print(f"派生量 -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
