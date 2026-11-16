#!/usr/bin/env python3
"""idea-009 苗白菜 Q 版手办：派生量。尺寸只在 model.scad 写一遍，这里只做算术。

check.py 与预览共用这一份，避免「验过的」和「画出来的」不是同一套尺寸。
不解表达式——scad_params.py 只认「一行一个 name = 数字;」。
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(Path.home() / ".cah-data/skills/shared/3d-print-ideas/scripts"))
from scad_params import read_params  # noqa: E402

P = read_params(HERE / "model.scad")


def g(k):
    if k not in P:
        raise SystemExit(f"model.scad 缺参数 {k}（scad_params 只认「一行一个 name = 数字;」）")
    return P[k]


# 白菜叶：绕 Z 转到方位角，再绕 Y 抬到仰角。派生量必须跟着仰角一起换。
ELEV0, ELEV1 = math.radians(g("leaf_elev0")), math.radians(g("leaf_elev1"))

# 部件表：(名字, z 下界, z 上界, 必须重叠的上游件)
# 「必须重叠」是给 check.py 判悬浮用的——两件 z 区间不交叉就是断的。
PARTS = [
    ("底座",   0.0,                       g("base_h"),                                  None),
    ("鞋",     g("shoe_z") - g("shoe_r") * g("shoe_zsq"),
               g("shoe_z") + g("shoe_r") * g("shoe_zsq"),                              "底座"),
    ("腿",     g("leg_z0") - g("leg_r0"), g("leg_z1") + g("leg_r1"),                    "鞋"),
    ("躯干",   g("torso_fz"),             g("torso_z1") + g("torso_r1"),                "腿"),
    ("开衫披肩", g("cape_z"),             g("cape_z") + g("cape_h"),                    "躯干"),
    ("手臂",   g("arm_z1") - g("arm_r1") - 0.4, g("arm_z0") + g("arm_r0"),              "躯干"),
    ("脖子",   g("neck_z"),               g("neck_z") + g("neck_h"),                    "躯干"),
    ("头",     g("head_z") - g("head_r"), g("head_z") + g("head_r"),                    "脖子"),
    ("头发",   min(g("cone_z0"), g("lock_z1") - g("lock_r1")),
               g("head_z") + g("hair_r"),                                               "头"),
    ("白菜叶", g("leaf_z") - 3 * math.sin(ELEV0),
               g("leaf_z") + (g("leaf_len") - 3) * math.sin(ELEV0) + g("leaf_t") * math.cos(ELEV0), "头发"),
]

# 期望包围盒：X 由底座定，Y 后侧由后脑发量定，Z 顶由叶尖定
BBOX_X = 2 * g("base_r")
BBOX_Y = g("base_r") + max(g("base_r"), 10 + 22)     # 后脑发量球心 y=10 r=22
# 中叶最立，最高点是叶尖上棱（叶厚在 z 上的投影也算）
BBOX_Z = g("leaf_z") + (g("leaf_len") - 3) * math.sin(ELEV0) + g("leaf_t") * math.cos(ELEV0)

# 最薄实体特征
MIN_FEATURE_MM = g("leaf_t")
