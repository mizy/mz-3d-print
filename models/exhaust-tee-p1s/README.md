<!-- generated-by: scripts/archive_design.py -->
# p1s-exhaust-tee P1S 排风三通 V3（对开两瓣）

原创设计归档（我们自己建模，不是外部模型改造）。

- 建模来源：自建参数化几何（build_tee.py / build_tee_split.py），V1→V3 迭代；按 P1S 实测排风口尺寸设计
- 打印记录：2026-11-01 实切：91.9 g / 3 h 01 min / 574 层（含开机序列）
- 备注：V2 60 口径与 V7 早期迭代已按 2026-11-10 清理删除；本目录为 V3 对开两瓣定稿（唯一保留版本）
- 归档时间：2026-11-09
- 文件清单 / SHA-256 / 几何尺寸：`ARCHIVE.json`

## 原始建模

| 文件 | 尺寸 mm | 面数 | 体积 cm³ |
|---|---|---|---|
| `exhaust-tee-split-assembled.stl` | 102.8 × 68 × 115.2 | 9856 | - |
| `exhaust-tee.stl` | 79.869 × 66.4 × 80 | 9108 | 30.615 |
| `tee-test-fit-assembled.stl` | 68 × 68 × 32 | 2696 | - |
| `tee_split_A.stl` | 102.8 × 48.658 × 115.2 | 5772 | - |
| `tee_split_A_repaired.stl` | 91.672 × 50.617 × 109.4 | 5730 | - |
| `tee_split_B.stl` | 101.941 × 35.467 × 115.2 | 4084 | - |
| `test-fit-half-A.stl` | 68 × 34 × 32 | 1348 | 7.509 |
| `test-fit-half-B.stl` | 68 × 34 × 32 | 1348 | 7.509 |

参数化脚本（`.scad` / `.py`）也在本目录，改动后按原命令重跑即可。

## 打印工程（3MF）

| 文件 | 切片重量 | 预计时长 |
|---|---|---|
| `coupon/wall-coupling-pair_sliced.3mf` | 4.37 g | 23m27s |
| `exhaust-tee-split.3mf` | 未切片 | - |
| `exhaust-tee-split_print.3mf` | 80.98 g | 2h33m |
| `exhaust-tee-split_print_support.3mf` | 91.9 g | 3h01m |
| `tee-test-fit.3mf` | 未切片 | - |

## 文档 / 自检报告

- `coupon/print-params.md`
- `coupon/打印说明.txt`
- `print-params.md`

## 重跑与自检

```bash
cd exhaust-tee-p1s
python3 build_tee.py        # 一体版
python3 build_tee_split.py  # 对开两瓣打印版
```
