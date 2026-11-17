# 苗壮的 3D 打印模型库

打印机：**Bambu Lab P1S**（AMS 四槽）。这里放我实际打过、改过、或为打印而设计的东西，提供 STL / 3MF / STEP 下载，具体可打印状态以项目说明为准。
部分 3MF 包含打印设置（层高、支撑、摆盘），是否可直接切片须以各项目说明和验证状态为准，不能仅凭扩展名判断。LV / Chanel 狗碗目前属于设计阶段，尚未完成切片、卡扣实配与承重验收；历史实验和旧 G-code 不应直接打印。

双 C 料盘当前为外滚环、主筋与筒壁加厚的 STEP 审查实验版，无新增内部承力环。全实体估重 168.06 g（非稀疏填充切片重量）；STEP 坐标核对通过，但 CAD 内核回读未完成、兼容性未知，尚未验证 1 kg 承载、AMS 动态及实物锁合。

**索引页（手机直接开）：https://mizy.github.io/mz-3d-print/**

---

## ⚠️ 来源说明：不是全部原创

这个库里只有一部分是**我们自己从零建模**的。为了不给别人的劳动成果乱贴原创标签，每个模型目录的 `MODEL.json` 里都标了来源类别，索引页上的小标签就是它：

| 标签 | 含义 | 我们做了什么 |
|---|---|---|
| **原创（original）** | 自建几何或参数化脚本，从零建模 | 全部：设计、建模、切片参数、打样改版 |
| **改造（derived）** | 母版来自第三方（MakerWorld / Thingiverse / 他人分享件）或 AI 生成网格 | 切割、分件、加销钉、重算包边、开凹槽、支撑与朝向、摆盘、层高工艺；**几何主体不是我们画的** |
| **样片（tool）** | 脚本试验样片（图片转浮雕、深度图转网格等） | 只有管线是我们写的，产物用于验证脚本 |

- **第三方母版**：改造件的原始版权仍归原作者，本库只记录「我们改了哪一步」，不主张原创。
- **AI 生成网格**：如 deepfish 玩偶，轮廓来自生成模型，我们做的是可打印化处理（分盘、支撑、朝向、首层工艺）。
- **许可证**：本库**未采用开源许可证**。原创件可自由用于个人非商业用途，转载/使用请注明出处；商业用途请先开 issue 联系。若你是某个母版的作者且不希望它出现在这里，开 issue 我会立刻移除。

原创新旧对照见 `models/ORIGINAL-ARCHIVE.md` 的上一级技能库归档规则（哪些算原创、哪些只算改造）。

---

## 目录结构

所有项目统一位于 `models/`，不再与 `projects/` 并列。共享狗碗设计资料在 [`models/dog-bowl-shared/`](models/dog-bowl-shared/README.md)，不是另一套可打印模型。

```
.
├── index.html              # GitHub Pages 索引页（自动生成，别手改）
├── models.json            # 索引数据（自动生成）
├── models/
│   └── <模型目录>/
│       ├── MODEL.json     # 元数据：id / 标题 / 分类 / 来源类别 / 一句话说明
│       └── ...           # stl / 3mf / preview png / 建模脚本 / 设计说明 md
└── tools/
    └── build-site.mjs     # 扫描 models/*/MODEL.json → 生成 index.html + models.json
```

## 什么进库、什么不进（2026-11-16 清理后的规则）

- **进库**：可直接下载去打的成品（**3mf 优先**，内含打印设置）、一份预览图、建模脚本 / `MODEL.json` / 设计说明。
- **不进库**：中间迭代版本（`-v2`…`-vN`、`superseded/`）、`.sliced.3mf` / `.gcode.3mf` 切片副本、与 3mf 同名的重复 STL、打包 zip、原始上传压缩包、大体积中间产物。
- 目前按这条规则清掉了 **178 MB / 55 项**冗余（重复 STL、旧版本、切片副本、重复浮雕副本、上传 zip）。
- 需要大 STL 或历史版本时，看 git 历史（`git log --follow <file>`）或 Release。

### 狗碗设计档案例外

按项目要求，`models/dog-bowl-lv/`、`models/dog-bowl-chanel/` 与共享档案 `models/dog-bowl-shared/` 保留设计图、文档和试错记录。品牌内 `Models/` 仅保留当前模型，`Design/`、`Notes/`、`Source/` 分别存放图片、说明及源脚本/矢量；旧模型仅在 Git 历史。大二进制通过 Git LFS 保存。LV 当前只维护一个 STEP，不要将历史记录误当当前交付。

## 下载方式

1. **手机**：打开 <https://mizy.github.io/mz-3d-print/>，点模型卡片里的文件名即可下载。
2. **桌面**：安装 Git LFS 后运行 `git clone` 和 `git lfs pull`，再使用 `models/` 里的文件；或点索引页链接。未拉取 LFS 时看到的小文本是指针，不是模型。
3. **大工程**：既有项目可使用 [Releases](../../releases)；狗碗大文件使用 Git LFS，索引页链接直接下载真实内容。40 MB 是既有项目的维护策略，不是 GitHub 的文件硬限制。

## 加一个新模型（维护流程）

```bash
mkdir -p models/my-new-part && cd models/my-new-part
# 放文件：xxx.stl / xxx.3mf / preview.png / DESIGN.md（切片参数写进 DESIGN.md）
cat > MODEL.json <<'JSON'
{ "id": "idea-0XX", "title": "名字", "category": "桌面收纳",
  "status": "design", "cls": "original",
  "summary": "一句话说明它是干什么的、关键尺寸" }
JSON
cd ../.. && bun tools/build-site.mjs     # 重新生成索引
git add -A && git commit -m "feat: 加入 xxx" && git push
```

`cls` 只允许 `original` / `derived` / `tool` 三种，选错等于给别人乱贴原创标签，别糊弄。

## 打印基线（P1S 走过坑之后的取值）

- **层高按可见性分档**：可见面 ≥ 0.12 mm；脸/头 0.08 mm；隐藏结构 / 底面 / 装配位 0.16–0.20 mm。
- **竖纹还是顺纹**：头发平躺顺发丝、衣服竖打顺织纹；**纹路 > 竖打**。
- **浅斜率是硬伤**：台阶宽度 `w = h / tanα`。α < 20° 的朝上面，降层高只是线性缓解（0.08→0.05 在 10° 处仍有 0.28 mm），只能靠**分件竖打**、**改造型做棱面**，或**只对该段加高度范围修改器**。量法见 `3d-print-ideas` 技能的 `scripts/slope_audit.py`。
- **支撑**：`tree(auto)`、45°、`critical_regions_only=1`、`top_z` 0.32、`XY` 0.35、界面 2 层 / 间距 0.5、8 mm brim。
- **首层脱盘是炒面的根因**：温水+洗洁精洗板、首层 0.20 mm / 线宽 0.5 / 25–30 mm/s、热床 75 ℃、前 3 层辅助风扇关、PETG 打印时别开外排风（穿堂风会让腔温掉到 5 ℃）。
- 完整的踩坑台账在 `3d-print-ideas` 技能的 `docs/print-pitfalls.md`（29 条），不在这里重复。
