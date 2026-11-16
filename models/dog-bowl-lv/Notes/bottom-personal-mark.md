# 碗底个人署名

用户要求：给源 STEP 的外碗底加个人 logo 和名字，不改变现有碗、花纹、前方榫卯 logo 或切片配置。

- 个人标志来源：`models/mark-miaozhuang-three-variants/miaozhuang-logo.svg`。其 README 记录为主人于 2026-11-12 上传的三版本资产，图形是「芽 + 立方体」。不是 LV 商标，也不是另一枚「苗壯」篆章。
- 姓名依据：同一 SVG title 和资产 README 均写「苗壮」。采用 STHeiti Medium，字高参数 9 mm，实际字符总范围约 16.97 × 8.09 mm。
- 原始 SVG 轮廓逐顶点保留，包含叶片内部镂空，没有平滑简化。标志宽 24 mm，高约 32.08 mm。
- 外底面凹刻 0.4 mm，原底厚 2 mm，刻痕上方保留 1.6 mm。无凸起，不影响底面平放。朝外观看文字正向。
- 只改变象牙色底板，仍为四个可独立选择的实体：底板、浅蓝碗身、象牙色口沿、单独摆放的前榫卯 logo。共两种颜色。
- 未操作 Bambu Studio，未切片、发送或开始打印。小刻字与原矢量极细边缘尚未实打验证；切片可能不会解析全部亚喷嘴细节。底面凹刻应检查首层桥接效果。

## 文件与复现

仅维护 `Models/LV_bowl_and_logo.step`，未新增第二个 STEP。
底视图为 `Design/bottom-personal-mark.png`；几何检查为 `Notes/bottom-personal-mark-validation.json`。

未刻字源件保存在 Git 历史提交 `e020f3269c6ef4dc838c83d3f071a1b6d6c9d32b`，不在工作树保留旧版本。

```sh
git show e020f3269c6ef4dc838c83d3f071a1b6d6c9d32b:models/dog-bowl-lv/Models/LV_bowl_and_logo.step | git lfs smudge > /tmp/LV-before-mark.step
python models/dog-bowl-lv/Source/add-bottom-personal-mark.py --input /tmp/LV-before-mark.step --output-dir /tmp/LV-mark-build
```

环境：CadQuery 2.x，macOS STHeiti Medium 字体。底视图从真实切割后的 B-rep 正投影生成，不是概念示意。
