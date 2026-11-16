狗碗项目索引：按品牌，不按日期

LV/Models/FullSides_OriginalClip
  当前完整侧面纹样、原倒T接口。lv/parts 内为打印件及 STEP，含独立Logo与接口小样。
LV/Models/FullSides_HollowRaisedClip_Candidate
  当前完整侧面纹样、两翼加高与中柱镂空候选。配合改变，先验证独立接口小样，未实物确认。
Chanel/Models/LowBowl_30mm
  香奈儿现有完整30mm碗。parts 内含分件及接口小样。

每个品牌的 DesignProcess 保存不同设计、初稿、实验、失败尝试及相关源码/图片/日志，不是要求打印的版本列表。
LV/Design 保存认可设计图。Documentation 保存说明与原始交付记录。
Shared/DesignProcess 保存无法合理拆成单品牌的原始双款场景、公共脚本。
Shared/FitSamples/OutlineFrames/models 保存省料空心边框小样。
Shared/Documentation/OrganizationHistory 保存整理、恢复、哈希及去重审计记录。

模型文件只有在 SHA-256 字节完全一致时才合并为一份实体文件；历史位置保留相对符号链接。
不同几何、不同接口、不同格式均保留。复制单个历史资料目录时请同时保留链接目标或让复制工具解析链接。
原始 ZIP 作为交付/过程证据保持原样，因此包内可能有已解压模型副本，不作为另一个日常维护模型。
混合实验目录通过引用链接保留原相对文件关系；没有重新运行历史脚本，部分原脚本绝对路径仍可能需要调整。

重要限制
候选卡扣母槽余量、实际安装与承重尚未验证；原70×30×8.5mm包络不代表候选加高后配合不变。
已有切片诊断不等于温度/材料/AMS配置已验收。没有启动打印。
未永久删除任何内容，字节相同模型副本位于 macOS 废纸篓的 _IdenticalModelCopies_Recoverable。
今后模型未改变只维护一份；设计图、文档、过程和试错资料继续保留，不再按日期分类。
