#!/usr/bin/env python3
"""idea-026 参数读取 + 派生量。数字只从 model.scad 来，build_mesh.py / check.py 共用这一份。

两种字（行楷 / 魏碑）字号相同但字面宽高不同，所以牌面尺寸是「量出字包围盒 + pad」，
实测值写进各变体的 *-report.json；这里只给参数与判据门槛。

用法:
  python3 model.py            # 打印摘要
  python3 model.py --json     # 完整 JSON
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

# 这台机器实测能出汉字的艺术字体（macOS AssetsV2 里的字库，路径固定带哈希目录）
FONTS = {
    "xingkai": "/System/Library/AssetsV2/com_apple_MobileAsset_Font8/"
               "13b8ce423f920875b28b551f9406bf1014e0a656.asset/AssetData/Xingkai.ttc",
    "weibei": "/System/Library/AssetsV2/com_apple_MobileAsset_Font8/"
              "c745f84f5eb15b1f594d3769dc86146fccee61ff.asset/AssetData/WeibeiSC-Bold.otf",
    "baoli": "/System/Library/AssetsV2/com_apple_MobileAsset_Font8/"
             "70875a1270987c17cfd6f40cd3d755ec04d03b33.asset/AssetData/Baoli.ttc",
    "libian": "/System/Library/AssetsV2/com_apple_MobileAsset_Font8/"
              "a304e3396d019087ab67af77f5e398977529007d.asset/AssetData/Libian.ttc",
}

# 纯立体字（无底座）用的参数
SOLID = {
    "font_size": 78,     # 字号（约等于一个字高）
    "thick": 10,         # 挤出厚度（平放打印，厚 = 立在桌上的深度）
    "bar_h": 8,          # 底部连体梁高度
    "bar_overlap": 1.2,  # 连体梁插进每个字的深度
    "chamfer": 0.8,      # 正面棱边倒角（45°，免支撑）
    "gap_mm": -4.0,      # 两字包围盒的重叠量（负数=略压一点，笔画才咬得上，像连体字）
}


def read_text(scad_path=SCAD):
    m = re.search(r'^\s*text_label\s*=\s*"([^"]*)"\s*;', Path(scad_path).read_text(), re.M)
    if not m:
        raise SystemExit("model.scad 里找不到 text_label")
    return m.group(1)


def load():
    p = read_params(SCAD)
    p["text"] = read_text()
    return p


def main(argv=None):
    ap = argparse.ArgumentParser(description="idea-026 参数摘要")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    p = load()
    if args.json:
        print(json.dumps(p, ensure_ascii=False, indent=2))
        return
    print(f"字: {p['text']}  字号 {p['font_size']}mm  立体字高 {p['letter_h']}mm  牌面厚 {p['plate_t']}mm")
    print(f"立式: 底座 {p['base_h']}mm 高 / 前伸 {p['base_front']} 后伸 {p['base_back']}；"
          f"斜筋 {p['rib_w']}×{p['rib_reach']}×{p['rib_h']} @ 25°")
    print(f"门槛: 笔画 ≥{p['min_stroke_mm']}  壁厚 ≥{p['min_wall_mm']}  外廓 ≤{p['bed_max_mm']}")


if __name__ == "__main__":
    main()
